#!/usr/bin/env python3
"""Exercise the one-command quick-deck build, render, and QA path."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from contextlib import nullcontext
from pathlib import Path

from pptx import Presentation

from run_high_readability_v2_smoke import _outline


ROOT = Path(__file__).resolve().parent.parent


def _metadata_text(package: zipfile.ZipFile) -> str:
    names = {"docProps/core.xml", "docProps/app.xml"}
    return "\n".join(
        package.read(name).decode("utf-8", errors="ignore")
        for name in names
        if name in package.namelist()
    )


def _off_canvas_shape_count(path: Path) -> int:
    deck = Presentation(path)
    slide_w = int(deck.slide_width)
    slide_h = int(deck.slide_height)
    tolerance = 1000
    return sum(
        1
        for slide in deck.slides
        for shape in slide.shapes
        if int(shape.left) < -tolerance
        or int(shape.top) < -tolerance
        or int(shape.left) + int(shape.width) > slide_w + tolerance
        or int(shape.top) + int(shape.height) > slide_h + tolerance
    )


def main() -> int:
    requested_outdir = os.environ.get("PRESENTATION_SKILL_SMOKE_OUTDIR", "").strip()
    context = nullcontext(requested_outdir) if requested_outdir else tempfile.TemporaryDirectory(
        prefix="presentation-skill-finalizer-"
    )
    with context as tmp:
        root = Path(tmp)
        root.mkdir(parents=True, exist_ok=True)
        outline_path = root / "outline.json"
        output_path = root / "output.pptx"
        qa_dir = root / "qa"
        outline = _outline()
        outline["slides"][0]["stakeholders"] = "This title sidecar must not render"
        outline["slides"][1]["facts"][0].update(
            {
                "label": "Highest two heat vulnerability indices",
                "detail": "Northgate and Eastbank priority pair",
            }
        )
        outline["slides"][2]["chart"]["facts"] = [
            {"value": "82", "label": "Highest mean neighborhood heat vulnerability"}
        ]
        outline["slides"][3]["table"] = {
            "headers": ["Criterion", "A · Targeted", "B · Citywide", "C · School-first"],
            "rows": [
                ["Scope", "North + East", "City vouchers", "12 schools"],
                ["Budget", "$620K · fits", "$1.35M · over", "$510K · fits"],
                ["Reach", "620 households", "1,280 households", "0 households"],
                ["Cooling", "4.6°C", "3.8°C", "2.7°C"],
                ["Delivery", "12 wk · medium", "18 wk · high", "10 wk · low"],
                ["Tradeoff", "Best cooling", "Broadest; over cap", "No residential reach"],
            ],
            "column_weights": [1.05, 1.55, 1.55, 1.55],
        }
        outline["slides"][6]["table"]["rows"] = outline["slides"][6]["table"]["rows"][:5]
        outline["slides"][6]["table"]["footnotes"] = [
            "SOURCE REGISTER",
            "S1 · Neighborhood evidence",
            "S2 · Decision evidence",
            "S3 · Operating evidence",
        ]
        outline_path.write_text(json.dumps(outline, indent=2) + "\n", encoding="utf-8")

        command = [
            sys.executable,
            str(ROOT / "scripts" / "finalize_quick_deck.py"),
            "--outline",
            str(outline_path),
            "--output",
            str(output_path),
            "--style-preset",
            "warm-terracotta",
            "--qa-dir",
            str(qa_dir),
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Quick-deck finalizer failed:\n{completed.stdout}")

        receipt = json.loads((qa_dir / "finalize_receipt.json").read_text(encoding="utf-8"))
        qa = json.loads((qa_dir / "qa_report.json").read_text(encoding="utf-8"))
        if not receipt.get("passed"):
            raise RuntimeError(f"Finalizer receipt did not pass: {receipt}")
        blocking_counts = {
            key: int(qa.get(key, 0) or 0)
            for key in (
                "overflow_count",
                "overlap_count",
                "geometry_error_count",
                "geometry_warning_count",
                "whitespace_warning_count",
                "visual_warning_count",
                "visual_review_warning_count",
                "design_error_count",
                "design_warning_count",
                "accessibility_error_count",
                "accessibility_warning_count",
            )
        }
        failures = {key: value for key, value in blocking_counts.items() if value}
        if failures:
            raise RuntimeError(f"Finalizer QA counts are not clean: {failures}")
        off_canvas_shape_count = _off_canvas_shape_count(output_path)
        if off_canvas_shape_count:
            raise RuntimeError(
                f"Finalizer output has {off_canvas_shape_count} off-canvas shape(s)"
            )

        with zipfile.ZipFile(output_path) as package:
            outer_metadata = _metadata_text(package)
            slide_one = package.read("ppt/slides/slide1.xml").decode("utf-8", errors="ignore")
            if "This title sidecar must not render" in slide_one:
                raise RuntimeError("The removed title stakeholder sidecar was rendered")
            if "PptxGenJS" in outer_metadata:
                raise RuntimeError("Outer package retained generator-identifying metadata")
            workbook_names = [
                name for name in package.namelist()
                if name.startswith("ppt/embeddings/") and name.lower().endswith(".xlsx")
            ]
            if not workbook_names:
                raise RuntimeError("Expected an editable chart workbook")
            for name in workbook_names:
                with zipfile.ZipFile(io.BytesIO(package.read(name))) as workbook:
                    if "PptxGenJS" in _metadata_text(workbook):
                        raise RuntimeError("Embedded workbook retained generator-identifying metadata")

        print(
            json.dumps(
                {
                    "passed": True,
                    "slide_count": 7,
                    "qa_counts": blocking_counts,
                    "metadata_sanitized": True,
                    "title_sidecar_removed": True,
                    "off_canvas_shape_count": off_canvas_shape_count,
                    "contact_sheet": receipt["contact_sheet"],
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
