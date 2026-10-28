#!/usr/bin/env python3
"""Deterministic accessibility audit for PowerPoint presentations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER


SCHEMA = "pptx_accessibility_qa"
VERSION = 1
SCHEMA_VERSION = f"{SCHEMA}_v{VERSION}"

EXIT_PASS = 0
EXIT_FINDINGS = 1
EXIT_OPERATIONAL_ERROR = 2

DEFAULT_MIN_BODY_PT = 12.0
DEFAULT_MIN_SUPPORT_PT = 13.0
DEFAULT_MIN_METADATA_PT = 8.0
LARGE_VISUAL_AREA_RATIO = 0.20

_GENERIC_ALT_WORDS = {
    "alt text",
    "chart",
    "description",
    "diagram",
    "figure",
    "graphic",
    "image",
    "object",
    "photo",
    "picture",
    "screenshot",
    "smartart",
    "tbd",
    "todo",
}
_EXEMPT_METADATA_VALUES = {
    "allow",
    "artifact",
    "background",
    "decorative",
    "ignore accessibility",
    "a11y allow",
    "a11y decorative",
    "a11y ignore",
    "accessibility allow",
    "accessibility decorative",
    "accessibility ignore",
    "aria hidden true",
}
_EXEMPT_NAME_PREFIXES = (
    "a11y allow",
    "a11y decorative",
    "a11y ignore",
    "accessibility allow",
    "accessibility decorative",
    "accessibility ignore",
    "artifact",
    "background",
    "bg",
    "decoration",
    "decorative",
)
_METADATA_MARKERS = (
    "caption",
    "citation",
    "confidential",
    "copyright",
    "date",
    "footnote",
    "footer",
    "legal",
    "metadata",
    "note",
    "page number",
    "source",
)
_SUPPORT_MARKERS = (
    "slide subtitle",
    "slide-subtitle",
    "support",
    "subtitle",
)
_NUMBER_NAME_MARKERS = (
    "decorative number",
    "folio",
    "page number",
    "section number",
    "slide number",
)
_TITLE_NAME_MARKERS = ("headline", "slide title", "title")


def _normalize_signal(value: str) -> str:
    value = value.strip().lower().replace("aria-hidden", "aria hidden")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _c_nv_pr(shape: Any) -> Any | None:
    for element in shape._element.iter():
        if _local_name(element.tag) == "cNvPr":
            return element
    return None


def _shape_metadata(shape: Any) -> dict[str, str]:
    c_nv_pr = _c_nv_pr(shape)
    name = str(getattr(shape, "name", "") or "").strip()
    if c_nv_pr is None:
        return {"name": name, "title": "", "description": ""}
    return {
        "name": str(c_nv_pr.get("name") or name).strip(),
        "title": str(c_nv_pr.get("title") or "").strip(),
        "description": str(c_nv_pr.get("descr") or "").strip(),
    }


def _is_exempt(shape: Any) -> bool:
    metadata = _shape_metadata(shape)
    for key in ("title", "description"):
        normalized = _normalize_signal(metadata[key])
        if normalized in _EXEMPT_METADATA_VALUES:
            return True
        if normalized.startswith(("decorative ", "a11y allow ", "a11y ignore ")):
            return True

    normalized_name = _normalize_signal(metadata["name"])
    return any(
        normalized_name == prefix or normalized_name.startswith(f"{prefix} ")
        for prefix in _EXEMPT_NAME_PREFIXES
    )


def _shape_text(shape: Any) -> str:
    if not getattr(shape, "has_text_frame", False):
        return ""
    return " ".join(str(shape.text or "").split())


def _font_size_pt(font: Any) -> float | None:
    size = getattr(font, "size", None)
    return float(size.pt) if size is not None else None


def _text_frame_sizes(text_frame: Any) -> list[float]:
    sizes: list[float] = []
    for paragraph in text_frame.paragraphs:
        paragraph_size = _font_size_pt(paragraph.font)
        if paragraph.runs:
            for run in paragraph.runs:
                if not run.text.strip():
                    continue
                run_size = _font_size_pt(run.font)
                if run_size is not None:
                    sizes.append(run_size)
                elif paragraph_size is not None:
                    sizes.append(paragraph_size)
        elif paragraph.text.strip() and paragraph_size is not None:
            sizes.append(paragraph_size)
    return sizes


def _shape_text_sizes(shape: Any) -> list[float]:
    if getattr(shape, "has_text_frame", False):
        return _text_frame_sizes(shape.text_frame)
    if not getattr(shape, "has_table", False):
        return []

    sizes: list[float] = []
    seen_cells: set[int] = set()
    for row in shape.table.rows:
        for cell in row.cells:
            cell_key = id(cell._tc)
            if cell_key in seen_cells:
                continue
            seen_cells.add(cell_key)
            sizes.extend(_text_frame_sizes(cell.text_frame))
    return sizes


def _shape_sample_text(shape: Any) -> str:
    text = _shape_text(shape)
    if text:
        return text[:120]
    if getattr(shape, "has_table", False):
        values: list[str] = []
        seen_cells: set[int] = set()
        for row in shape.table.rows:
            for cell in row.cells:
                cell_key = id(cell._tc)
                if cell_key in seen_cells:
                    continue
                seen_cells.add(cell_key)
                value = " ".join(cell.text.split())
                if value:
                    values.append(value)
        return " | ".join(values)[:120]
    return ""


def _graphic_data_uris(shape: Any) -> tuple[str, ...]:
    uris = []
    for element in shape._element.iter():
        if _local_name(element.tag) == "graphicData":
            uri = str(element.get("uri") or "").strip()
            if uri:
                uris.append(uri)
    return tuple(uris)


def _visual_kind(shape: Any) -> str | None:
    if getattr(shape, "has_chart", False):
        return "chart"
    if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.PICTURE:
        return "image"

    uris = _graphic_data_uris(shape)
    if any("/diagram" in uri.lower() for uri in uris):
        return "diagram"
    if any("/chart" in uri.lower() for uri in uris):
        return "chart"
    if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
        return "diagram"
    return None


def _is_generic_alt_text(value: str) -> bool:
    if re.search(
        r"(?:^|[/\\])?[^/\\]+\.(?:bmp|emf|gif|jpe?g|png|svg|tiff?|webp|wmf)$",
        value.strip(),
        flags=re.IGNORECASE,
    ):
        return True
    normalized = _normalize_signal(value)
    if not normalized or normalized in _GENERIC_ALT_WORDS:
        return True
    generic_numbered = (
        r"(?:alt text|chart|diagram|figure|graphic|image|object|photo|picture|"
        r"screenshot|smartart) \d+"
    )
    if re.fullmatch(generic_numbered, normalized):
        return True
    if re.fullmatch(
        r"(?:img|image|picture|photo|screenshot)\d*(?: png| jpg| jpeg| gif| svg)?",
        normalized,
    ):
        return True
    return normalized.startswith(("alt text goes here", "description goes here"))


def _has_meaningful_object_metadata(shape: Any) -> bool:
    metadata = _shape_metadata(shape)
    values = [metadata["title"], metadata["description"]]
    return any(value and not _is_generic_alt_text(value) for value in values)


def _is_title_placeholder(shape: Any) -> bool:
    if not getattr(shape, "is_placeholder", False):
        return False
    try:
        return shape.placeholder_format.type in {
            PP_PLACEHOLDER.TITLE,
            PP_PLACEHOLDER.CENTER_TITLE,
        }
    except (AttributeError, ValueError):
        return False


def _max_explicit_font_size(shape: Any) -> float | None:
    sizes = _shape_text_sizes(shape)
    return max(sizes) if sizes else None


def _is_headline(shape: Any, slide_width: int, slide_height: int) -> bool:
    text = _shape_text(shape)
    if not text or _is_exempt(shape):
        return False
    if _is_title_placeholder(shape):
        return True

    metadata = _shape_metadata(shape)
    normalized_name = _normalize_signal(metadata["name"])
    if any(marker in normalized_name for marker in _TITLE_NAME_MARKERS):
        return True

    top = int(getattr(shape, "top", 0) or 0)
    width = int(getattr(shape, "width", 0) or 0)
    font_size = _max_explicit_font_size(shape)
    return (
        top <= slide_height * 0.30
        and width >= slide_width * 0.20
        and len(text) <= 200
        and font_size is not None
        and font_size >= 18.0
    )


def _slide_metadata_name(slide: Any) -> str:
    name = str(slide._element.cSld.get("name") or "").strip()
    normalized = _normalize_signal(name)
    if not normalized or normalized in {"slide", "untitled"}:
        return ""
    if re.fullmatch(r"slide \d+", normalized):
        return ""
    return name


def _horizontal_overlap_ratio(first: Any, second: Any) -> float:
    first_left = int(getattr(first, "left", 0) or 0)
    second_left = int(getattr(second, "left", 0) or 0)
    first_width = int(getattr(first, "width", 0) or 0)
    second_width = int(getattr(second, "width", 0) or 0)
    overlap = min(first_left + first_width, second_left + second_width) - max(
        first_left, second_left
    )
    denominator = min(first_width, second_width)
    if overlap <= 0 or denominator <= 0:
        return 0.0
    return overlap / denominator


def _has_nearby_table_label(table_shape: Any, shapes: Iterable[Any]) -> bool:
    table_top = int(getattr(table_shape, "top", 0) or 0)
    for candidate in shapes:
        if candidate is table_shape or _is_exempt(candidate):
            continue
        text = _shape_text(candidate)
        if not text or len(text) > 200 or _is_generic_alt_text(text):
            continue
        candidate_bottom = int(getattr(candidate, "top", 0) or 0) + int(
            getattr(candidate, "height", 0) or 0
        )
        gap_inches = (table_top - candidate_bottom) / 914400.0
        overlap_ratio = _horizontal_overlap_ratio(table_shape, candidate)
        if -0.05 <= gap_inches <= 0.75 and overlap_ratio >= 0.20:
            return True
    return False


def _is_decorative_number(shape: Any, text: str, slide_width: int, slide_height: int) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not re.fullmatch(r"(?:\d{1,4}|[IVXLCDM]{1,8})", compact, flags=re.IGNORECASE):
        return False

    normalized_name = _normalize_signal(_shape_metadata(shape)["name"])
    if any(marker in normalized_name for marker in _NUMBER_NAME_MARKERS):
        return True
    if _is_exempt(shape):
        return True

    top = int(getattr(shape, "top", 0) or 0)
    width = int(getattr(shape, "width", 0) or 0)
    return top >= slide_height * 0.88 and width <= slide_width * 0.20


def _text_role(shape: Any, text: str, slide_height: int) -> str:
    normalized_name = _normalize_signal(_shape_metadata(shape)["name"])
    normalized_text = _normalize_signal(text)
    if any(marker in normalized_name for marker in _SUPPORT_MARKERS):
        return "support"
    if any(marker in normalized_name for marker in _METADATA_MARKERS):
        return "metadata"
    if normalized_text.startswith(
        ("citation ", "confidential", "copyright ", "note ", "source ", "sources ")
    ):
        return "metadata"
    top = int(getattr(shape, "top", 0) or 0)
    compact_text = " ".join(text.split())
    if (
        top <= slide_height * 0.20
        and len(compact_text) <= 80
        and compact_text.upper() == compact_text
        and any(character.isalpha() for character in compact_text)
    ):
        return "metadata"
    if top >= slide_height * 0.82:
        return "metadata"
    return "body"


def _iter_shapes_with_order(
    shapes: Iterable[Any],
    prefix: tuple[int, ...] = (),
) -> Iterator[tuple[tuple[int, ...], Any, bool]]:
    for index, shape in enumerate(shapes, start=1):
        order = (*prefix, index)
        exempt = _is_exempt(shape)
        yield order, shape, exempt
        if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP and not exempt:
            yield from _iter_shapes_with_order(shape.shapes, order)


def _order_label(order: tuple[int, ...] | None) -> str | None:
    return ".".join(str(value) for value in order) if order else None


def _shape_details(shape: Any | None, order: tuple[int, ...] | None) -> dict[str, Any]:
    if shape is None:
        return {"shape_id": None, "shape_name": None, "xml_order": None}
    metadata = _shape_metadata(shape)
    return {
        "shape_id": int(getattr(shape, "shape_id", 0) or 0),
        "shape_name": metadata["name"],
        "xml_order": _order_label(order),
    }


def _finding(
    *,
    code: str,
    base_severity: str,
    strict: bool,
    slide_number: int | None,
    message: str,
    shape: Any | None = None,
    order: tuple[int, ...] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    severity = "error" if strict and base_severity == "warning" else base_severity
    return {
        "code": code,
        "severity": severity,
        "base_severity": base_severity,
        "slide_number": slide_number,
        **_shape_details(shape, order),
        "message": message,
        "details": details or {},
    }


def _finding_sort_key(finding: dict[str, Any]) -> tuple[Any, ...]:
    order = tuple(int(part) for part in str(finding.get("xml_order") or "").split(".") if part)
    return (
        int(finding.get("slide_number") or 0),
        order,
        str(finding.get("code") or ""),
        int(finding.get("shape_id") or 0),
    )


def audit_presentation(
    input_path: str | Path,
    *,
    min_body_pt: float = DEFAULT_MIN_BODY_PT,
    min_support_pt: float = DEFAULT_MIN_SUPPORT_PT,
    min_metadata_pt: float = DEFAULT_MIN_METADATA_PT,
    strict: bool = False,
) -> dict[str, Any]:
    """Audit ``input_path`` without modifying it and return a stable JSON-ready report."""

    if min_body_pt <= 0 or min_support_pt <= 0 or min_metadata_pt <= 0:
        raise ValueError("minimum font sizes must be greater than zero")

    pptx_path = Path(input_path).expanduser().resolve(strict=True)
    presentation = Presentation(str(pptx_path))
    slide_width = int(presentation.slide_width)
    slide_height = int(presentation.slide_height)
    slide_area = slide_width * slide_height
    findings: list[dict[str, Any]] = []

    for slide_number, slide in enumerate(presentation.slides, start=1):
        top_level_shapes = list(slide.shapes)
        headlines = [
            (order, shape)
            for order, shape in enumerate(top_level_shapes, start=1)
            if _is_headline(shape, slide_width, slide_height)
        ]
        if not headlines and not _slide_metadata_name(slide):
            findings.append(
                _finding(
                    code="missing_slide_title",
                    base_severity="error",
                    strict=strict,
                    slide_number=slide_number,
                    message="Slide has no title, headline, or explicit common-slide name.",
                )
            )

        for order_index, shape in enumerate(top_level_shapes, start=1):
            order = (order_index,)
            if _is_exempt(shape):
                continue

            visual_kind = _visual_kind(shape)
            if visual_kind:
                metadata = _shape_metadata(shape)
                alt_values = [
                    value for value in (metadata["title"], metadata["description"]) if value
                ]
                if not alt_values:
                    findings.append(
                        _finding(
                            code="missing_alt_text",
                            base_severity="error",
                            strict=strict,
                            slide_number=slide_number,
                            shape=shape,
                            order=order,
                            message=f"{visual_kind.title()} has no object title or description.",
                            details={"visual_kind": visual_kind},
                        )
                    )
                elif all(_is_generic_alt_text(value) for value in alt_values):
                    findings.append(
                        _finding(
                            code="generic_alt_text",
                            base_severity="warning",
                            strict=strict,
                            slide_number=slide_number,
                            shape=shape,
                            order=order,
                            message=f"{visual_kind.title()} alternative text appears generic.",
                            details={"visual_kind": visual_kind, "alt_text": alt_values},
                        )
                    )

            if getattr(shape, "has_table", False):
                if not _has_meaningful_object_metadata(shape) and not _has_nearby_table_label(
                    shape, top_level_shapes
                ):
                    findings.append(
                        _finding(
                            code="table_missing_accessible_context",
                            base_severity="warning",
                            strict=strict,
                            slide_number=slide_number,
                            shape=shape,
                            order=order,
                            message=(
                                "Table has no meaningful object title/description "
                                "or nearby label."
                            ),
                        )
                    )

        if headlines:
            headline_order, headline_shape = min(headlines, key=lambda item: item[0])
            headline_name = _shape_metadata(headline_shape)["name"]
            for order_index, shape in enumerate(top_level_shapes, start=1):
                if order_index >= headline_order or _is_exempt(shape):
                    continue
                visual_kind = _visual_kind(shape)
                if not visual_kind:
                    continue
                area = int(getattr(shape, "width", 0) or 0) * int(
                    getattr(shape, "height", 0) or 0
                )
                area_ratio = area / slide_area if slide_area else 0.0
                if area_ratio < LARGE_VISUAL_AREA_RATIO:
                    continue
                findings.append(
                    _finding(
                        code="reading_order_visual_before_headline",
                        base_severity="warning",
                        strict=strict,
                        slide_number=slide_number,
                        shape=shape,
                        order=(order_index,),
                        message="Large visual precedes the slide headline in XML/z-order.",
                        details={
                            "visual_kind": visual_kind,
                            "area_ratio": round(area_ratio, 4),
                            "headline_shape_id": int(headline_shape.shape_id),
                            "headline_shape_name": headline_name,
                            "headline_xml_order": str(headline_order),
                        },
                    )
                )

        for order, shape, exempt in _iter_shapes_with_order(top_level_shapes):
            if exempt:
                continue
            sizes = _shape_text_sizes(shape)
            if not sizes:
                continue
            text = _shape_sample_text(shape)
            if text and _is_decorative_number(shape, text, slide_width, slide_height):
                continue
            role = "body" if getattr(shape, "has_table", False) else _text_role(
                shape, text, slide_height
            )
            minimum = {
                "body": min_body_pt,
                "support": min_support_pt,
                "metadata": min_metadata_pt,
            }[role]
            observed = min(sizes)
            if observed >= minimum:
                continue
            findings.append(
                _finding(
                    code="text_below_minimum",
                    base_severity="warning",
                    strict=strict,
                    slide_number=slide_number,
                    shape=shape,
                    order=order,
                    message=f"{role.title()} text is below the configured minimum size.",
                    details={
                        "role": role,
                        "observed_min_pt": round(observed, 2),
                        "minimum_pt": round(minimum, 2),
                        "text_sample": text,
                    },
                )
            )

    findings.sort(key=_finding_sort_key)
    error_count = sum(1 for finding in findings if finding["severity"] == "error")
    warning_count = sum(1 for finding in findings if finding["severity"] == "warning")
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "input": str(pptx_path),
        "strict": bool(strict),
        "thresholds": {
            "min_body_pt": float(min_body_pt),
            "min_support_pt": float(min_support_pt),
            "min_metadata_pt": float(min_metadata_pt),
            "large_visual_area_ratio": LARGE_VISUAL_AREA_RATIO,
        },
        "slide_count": len(presentation.slides),
        "finding_count": len(findings),
        "error_count": error_count,
        "warning_count": warning_count,
        "passed": error_count == 0,
        "findings": findings,
    }


def _operational_error_report(
    input_path: str | Path,
    exc: Exception,
    strict: bool,
    min_body_pt: float,
    min_support_pt: float,
    min_metadata_pt: float,
) -> dict[str, Any]:
    path = str(Path(input_path).expanduser().resolve())
    finding = {
        "code": "audit_failed",
        "severity": "error",
        "base_severity": "error",
        "slide_number": None,
        "shape_id": None,
        "shape_name": None,
        "xml_order": None,
        "message": "Accessibility audit could not read the presentation.",
        "details": {"exception_type": type(exc).__name__, "reason": str(exc)},
    }
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "input": path,
        "strict": bool(strict),
        "thresholds": {
            "min_body_pt": float(min_body_pt),
            "min_support_pt": float(min_support_pt),
            "min_metadata_pt": float(min_metadata_pt),
            "large_visual_area_ratio": LARGE_VISUAL_AREA_RATIO,
        },
        "slide_count": 0,
        "finding_count": 1,
        "error_count": 1,
        "warning_count": 0,
        "passed": False,
        "findings": [finding],
    }


def _serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit PPTX accessibility without modifying the deck"
    )
    parser.add_argument("--input", required=True, help="Input PPTX path")
    parser.add_argument("--report", help="Optional path for the same JSON emitted to stdout")
    parser.add_argument(
        "--min-body-pt",
        type=float,
        default=DEFAULT_MIN_BODY_PT,
        help=f"Minimum body text size (default: {DEFAULT_MIN_BODY_PT:g})",
    )
    parser.add_argument(
        "--min-support-pt",
        type=float,
        default=DEFAULT_MIN_SUPPORT_PT,
        help=f"Minimum supporting/subtitle text size (default: {DEFAULT_MIN_SUPPORT_PT:g})",
    )
    parser.add_argument(
        "--min-metadata-pt",
        type=float,
        default=DEFAULT_MIN_METADATA_PT,
        help=f"Minimum metadata text size (default: {DEFAULT_MIN_METADATA_PT:g})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Upgrade audit warnings to errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = audit_presentation(
            args.input,
            min_body_pt=args.min_body_pt,
            min_support_pt=args.min_support_pt,
            min_metadata_pt=args.min_metadata_pt,
            strict=args.strict,
        )
        output = _serialize_report(report)
        if args.report:
            input_path = Path(args.input).expanduser().resolve()
            report_path = Path(args.report).expanduser().resolve()
            if report_path == input_path:
                raise ValueError("report path must not overwrite the input PPTX")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(output, encoding="utf-8")
    except Exception as exc:  # CLI boundary: always return machine-readable failure JSON.
        report = _operational_error_report(
            args.input,
            exc,
            args.strict,
            args.min_body_pt,
            args.min_support_pt,
            args.min_metadata_pt,
        )
        output = _serialize_report(report)
        sys.stdout.write(output)
        return EXIT_OPERATIONAL_ERROR

    sys.stdout.write(output)
    return EXIT_PASS if report["passed"] else EXIT_FINDINGS


if __name__ == "__main__":
    raise SystemExit(main())
