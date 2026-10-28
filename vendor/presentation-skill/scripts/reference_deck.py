#!/usr/bin/env python3
"""Inspect and safely patch editable objects in an existing PPTX."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from office_package_hash import office_package_normalized_sha256


MANIFEST_VERSION = "reference_deck_manifest_v1"
PATCH_VERSION = "reference_deck_patch_v1"


def _json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _shape_text(shape: Any) -> str:
    if not getattr(shape, "has_text_frame", False):
        return ""
    return "\n".join(paragraph.text for paragraph in shape.text_frame.paragraphs).strip()


def _shape_kind(shape: Any) -> str:
    shape_type = getattr(shape, "shape_type", None)
    names = {
        MSO_SHAPE_TYPE.AUTO_SHAPE: "shape",
        MSO_SHAPE_TYPE.CHART: "chart",
        MSO_SHAPE_TYPE.GROUP: "group",
        MSO_SHAPE_TYPE.LINE: "line",
        MSO_SHAPE_TYPE.PICTURE: "image",
        MSO_SHAPE_TYPE.PLACEHOLDER: "placeholder",
        MSO_SHAPE_TYPE.TABLE: "table",
        MSO_SHAPE_TYPE.TEXT_BOX: "text",
    }
    return names.get(shape_type, "object")


def _color_token(color: Any) -> str:
    try:
        if color.type is None:
            return ""
        if color.rgb is not None:
            return str(color.rgb)
        if color.theme_color is not None:
            return f"theme:{color.theme_color}"
    except (AttributeError, TypeError, ValueError):
        return ""
    return ""


def _style_record(shape: Any) -> dict[str, Any]:
    record: dict[str, Any] = {"kind": _shape_kind(shape), "name": str(getattr(shape, "name", ""))}
    try:
        record["fill"] = _color_token(shape.fill.fore_color)
    except (AttributeError, TypeError, ValueError):
        record["fill"] = ""
    try:
        record["line"] = _color_token(shape.line.color)
        record["line_width"] = int(shape.line.width or 0)
    except (AttributeError, ValueError):
        record["line"] = ""
        record["line_width"] = 0
    fonts: list[dict[str, Any]] = []
    if getattr(shape, "has_text_frame", False):
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                fonts.append(
                    {
                        "name": run.font.name or "",
                        "size": int(run.font.size or 0),
                        "bold": run.font.bold,
                        "italic": run.font.italic,
                    }
                )
    record["font_runs"] = fonts
    return record


def _alt_text(shape: Any) -> str:
    nodes = shape._element.xpath('.//*[local-name()="cNvPr"]')  # noqa: SLF001
    return str(nodes[0].get("descr") or "") if nodes else ""


def _set_alt_text(shape: Any, value: str) -> None:
    nodes = shape._element.xpath('.//*[local-name()="cNvPr"]')  # noqa: SLF001
    if not nodes:
        raise ValueError(f"Shape {shape.shape_id} has no cNvPr accessibility node")
    nodes[0].set("descr", value)


def _iter_shapes(shapes: Any) -> Iterator[Any]:
    for shape in shapes:
        yield shape
        if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
            yield from _iter_shapes(shape.shapes)


def _shape_record(shape: Any) -> dict[str, Any]:
    text = _shape_text(shape)
    geometry = {
        "x": int(shape.left),
        "y": int(shape.top),
        "w": int(shape.width),
        "h": int(shape.height),
        "rotation": float(getattr(shape, "rotation", 0) or 0),
    }
    style = _style_record(shape)
    return {
        "element_id": f"shape-{shape.shape_id}",
        "shape_id": int(shape.shape_id),
        "name": str(getattr(shape, "name", "")),
        "object_kind": _shape_kind(shape),
        "editable": bool(getattr(shape, "has_text_frame", False) or _shape_kind(shape) in {"image", "shape"}),
        "geometry": geometry,
        "geometry_sha256": _json_hash(geometry),
        "style_sha256": _json_hash(style),
        "text": text,
        "text_sha256": _text_hash(text),
        "alt_text": _alt_text(shape),
    }


def inspect_reference_deck(pptx_path: Path) -> dict[str, Any]:
    pptx_path = pptx_path.expanduser().resolve()
    if not pptx_path.is_file():
        raise FileNotFoundError(f"Reference PPTX not found: {pptx_path}")
    presentation = Presentation(str(pptx_path))
    slides: list[dict[str, Any]] = []
    for index, slide in enumerate(presentation.slides, start=1):
        elements = [_shape_record(shape) for shape in _iter_shapes(slide.shapes)]
        slides.append(
            {
                "slide_id": f"slide-{slide.slide_id}",
                "slide_index": index,
                "powerpoint_slide_id": int(slide.slide_id),
                "element_count": len(elements),
                "elements": elements,
            }
        )
    manifest_core = {
        "schema_version": MANIFEST_VERSION,
        "source": {
            "filename": pptx_path.name,
            "normalized_office_sha256": office_package_normalized_sha256(pptx_path),
        },
        "slide_size_emu": {
            "width": int(presentation.slide_width),
            "height": int(presentation.slide_height),
        },
        "slide_count": len(slides),
        "slides": slides,
    }
    manifest_core["manifest_sha256"] = _json_hash(manifest_core)
    return manifest_core


def _slide_by_id(presentation: Presentation, slide_id: str) -> Any:
    for slide in presentation.slides:
        if f"slide-{slide.slide_id}" == slide_id:
            return slide
    raise KeyError(f"Unknown slide_id: {slide_id}")


def _shape_by_id(slide: Any, element_id: str) -> Any:
    for shape in _iter_shapes(slide.shapes):
        if f"shape-{shape.shape_id}" == element_id:
            return shape
    raise KeyError(f"Unknown element_id {element_id} on slide-{slide.slide_id}")


def _replace_text_preserving_runs(shape: Any, text: str) -> None:
    if not getattr(shape, "has_text_frame", False):
        raise ValueError(f"{shape.name} is not an editable text object")
    paragraphs = list(shape.text_frame.paragraphs)
    runs = [run for paragraph in paragraphs for run in paragraph.runs]
    if runs:
        runs[0].text = text
        for run in runs[1:]:
            run.text = ""
        for paragraph in paragraphs[1:]:
            paragraph.text = ""
    else:
        paragraphs[0].text = text


def _load_patch_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != PATCH_VERSION:
        raise ValueError(f"Patch plan schema_version must be {PATCH_VERSION}")
    if not isinstance(payload.get("operations"), list):
        raise ValueError("Patch plan operations must be an array")
    return payload


def _element_index(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(slide["slide_id"]), str(element["element_id"])): element
        for slide in manifest.get("slides", [])
        for element in slide.get("elements", [])
    }


def patch_reference_deck(
    *,
    input_path: Path,
    patch_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if output_path == input_path:
        raise ValueError("Reference patch output must differ from the source PPTX")
    source_manifest = inspect_reference_deck(input_path)
    plan = _load_patch_plan(patch_path.expanduser().resolve())
    expected_manifest = str(plan.get("source_manifest_sha256") or "")
    if expected_manifest and expected_manifest != source_manifest["manifest_sha256"]:
        raise ValueError("Patch plan source_manifest_sha256 does not match the reference deck")
    presentation = Presentation(str(input_path))
    touched: set[tuple[str, str]] = set()
    operation_results: list[dict[str, Any]] = []
    source_index = _element_index(source_manifest)
    for index, operation in enumerate(plan["operations"]):
        if not isinstance(operation, dict):
            raise ValueError(f"operations[{index}] must be an object")
        action = str(operation.get("action") or "").strip()
        if action not in {"replace_text", "set_alt_text"}:
            raise ValueError(f"operations[{index}].action is not registered: {action!r}")
        slide_id = str(operation.get("slide_id") or "")
        element_id = str(operation.get("element_id") or "")
        key = (slide_id, element_id)
        source = source_index.get(key)
        if source is None:
            raise KeyError(f"operations[{index}] targets an unknown slide/element")
        slide = _slide_by_id(presentation, slide_id)
        shape = _shape_by_id(slide, element_id)
        if action == "replace_text":
            expected_text = str(operation.get("expected_text_sha256") or "")
            if not expected_text:
                raise ValueError(f"operations[{index}].expected_text_sha256 is required")
            if expected_text != source["text_sha256"]:
                raise ValueError(f"operations[{index}] text precondition failed")
            _replace_text_preserving_runs(shape, str(operation.get("text") or ""))
        else:
            expected_alt = str(operation.get("expected_alt_text") or "")
            if expected_alt != str(source.get("alt_text") or ""):
                raise ValueError(f"operations[{index}] alt-text precondition failed")
            _set_alt_text(shape, str(operation.get("alt_text") or ""))
        touched.add(key)
        operation_results.append({"index": index, "action": action, "slide_id": slide_id, "element_id": element_id})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(output_path))
    output_manifest = inspect_reference_deck(output_path)
    output_index = _element_index(output_manifest)
    preservation_failures: list[str] = []
    if set(source_index) != set(output_index):
        preservation_failures.append("slide/element identity set changed")
    for key, source in source_index.items():
        target = output_index.get(key)
        if target is None:
            continue
        if source["geometry_sha256"] != target["geometry_sha256"]:
            preservation_failures.append(f"{key[0]}/{key[1]} geometry changed")
        if source["style_sha256"] != target["style_sha256"]:
            preservation_failures.append(f"{key[0]}/{key[1]} style changed")
        if key not in touched and source["text_sha256"] != target["text_sha256"]:
            preservation_failures.append(f"{key[0]}/{key[1]} untouched text changed")
    return {
        "passed": not preservation_failures,
        "schema_version": PATCH_VERSION,
        "input": str(input_path),
        "output": str(output_path),
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "output_manifest_sha256": output_manifest["manifest_sha256"],
        "operation_count": len(operation_results),
        "operations": operation_results,
        "preservation_failures": preservation_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or safely patch an editable reference PPTX.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("--input", required=True)
    inspect.add_argument("--output", required=True)
    patch = subparsers.add_parser("patch")
    patch.add_argument("--input", required=True)
    patch.add_argument("--plan", required=True)
    patch.add_argument("--output", required=True)
    patch.add_argument("--report")
    args = parser.parse_args()
    if args.command == "inspect":
        payload = inspect_reference_deck(Path(args.input))
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"passed": True, "manifest": str(output), "slide_count": payload["slide_count"]}, indent=2))
        return 0
    result = patch_reference_deck(
        input_path=Path(args.input),
        patch_path=Path(args.plan),
        output_path=Path(args.output),
    )
    if args.report:
        report = Path(args.report).expanduser().resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
