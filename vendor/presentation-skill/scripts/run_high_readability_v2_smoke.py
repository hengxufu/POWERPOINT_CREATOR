#!/usr/bin/env python3
"""Exercise dense v2 role layouts at the documented 16/9 readability floor."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def _run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}"
        )


def _outline() -> dict[str, Any]:
    style = {
        "font_pair": "clean_modern_v1",
        "palette_key": "energy_sunset_v1",
        "style_seed": "high-readability-v2-smoke",
        "header_variant": "auto",
        "header_variants": ["split-rule", "title-rule", "left-accent", "plain"],
        "footer_mode": "source-line",
        "footer_page_numbers": True,
        "readability_contract": {
            "min_title_pt": 28,
            "min_body_pt": 16,
            "min_caption_pt": 9,
            "min_footer_pt": 9,
            "max_title_lines": 2,
        },
    }
    return {
        "title": "Cooling pilot decision",
        "deck_style": style,
        "slides": [
            {
                "type": "title",
                "role": "title",
                "variant": "title",
                "slide_intent": "public question",
                "title": "Fund a 120-day cooling pilot",
                "subtitle": "$620,000 for two priority districts and 620 households",
                "kicker": "FUNDING DECISION",
                "sources": ["S2", "S3"],
            },
            {
                "type": "content",
                "role": "evidence",
                "variant": "stats",
                "slide_intent": "affected groups",
                "title": "Exposure is concentrated and the target reaches 620 households",
                "sources": ["S1", "S2"],
                "facts": [
                    {"value": "58.1°C", "label": "Priority roof heat", "detail": "4.3°C vs control"},
                    {"value": "21pt", "label": "Vulnerability gap", "detail": "82 vs 61"},
                    {"value": "620", "label": "Households reached", "detail": "Across 340 roofs"},
                    {"value": "4.6°C", "label": "Modeled cooling", "detail": "12-week delivery"},
                ],
            },
            {
                "type": "content",
                "role": "chart",
                "variant": "chart",
                "slide_intent": "evidence",
                "role_layout_variant": "alternate",
                "title": "Two districts rank highest on heat vulnerability",
                "sources": ["S1"],
                "chart": {
                    "type": "bar",
                    "categories": ["Control", "Central", "South", "East", "North"],
                    "series": [{"name": "HVI", "values": [61, 69, 74, 77, 82]}],
                    "facts": [{"value": "82", "label": "Highest HVI"}],
                },
            },
            {
                "type": "content",
                "role": "table",
                "variant": "table",
                "slide_intent": "options",
                "role_layout_variant": "alternate",
                "title": "Option A is the only residential choice inside the appropriation",
                "sources": ["S2"],
                "table_treatment": "decision-matrix",
                "summary_callout": "Fund A: within the cap and strongest residential cooling.",
                "table": {
                    "headers": ["Option", "Budget", "Reach", "Cooling", "Delivery", "Tradeoff"],
                    "rows": [
                        ["A — two districts", "$620k", "340 roofs / 620 HH", "4.6°C", "12 wk / Medium", "Highest cooling per household"],
                        ["B — citywide", "$1.35M", "702 roofs / 1,280 HH", "3.8°C", "18 wk / High", "Broadest reach; above cap"],
                        ["C — schools", "$510k", "12 roofs / 0 HH", "2.7°C", "10 wk / Low", "Fast; no residential reach"],
                    ],
                    "column_weights": [0.22, 0.10, 0.14, 0.10, 0.13, 0.31],
                },
            },
            {
                "type": "content",
                "role": "decision",
                "variant": "matrix",
                "slide_intent": "recommendation",
                "title": "The recommendation is bounded by four measurable commitments",
                "sources": ["S2", "S3"],
                "quadrants": [
                    {"title": "Scope", "body": "Two districts; 340 roofs and 620 households; $620,000 hard cap."},
                    {"title": "Outcome", "body": "4.6°C modeled cooling; report accepted by day 120."},
                    {"title": "Uptake gate", "body": "At least 260 eligible roofs opt in by week 5; re-scope if missed."},
                    {"title": "Delivery gate", "body": "Permit-ready list by week 7 and 300 passed inspections by week 14."},
                ],
                "summary_callout": "Approve only with named owners and explicit stop rules.",
            },
            {
                "type": "content",
                "role": "evidence",
                "variant": "timeline",
                "slide_intent": "implementation",
                "role_layout_variant": "alternate",
                "title": "Five owned gates fit inside the 120-day window",
                "sources": ["S3"],
                "milestones": [
                    {"label": "Weeks 1–2", "title": "Approve", "body": "Resilience Office signs the framework."},
                    {"label": "Weeks 3–5", "title": "Recruit", "body": "Partners secure 260 eligible opt-ins."},
                    {"label": "Weeks 5–7", "title": "Verify", "body": "Building staff produce the roof list."},
                    {"label": "Weeks 8–14", "title": "Install", "body": "Contractors reach 300 passed inspections."},
                    {"label": "Weeks 15–17", "title": "Report", "body": "Analytics accepts the delivery report."},
                ],
            },
            {
                "type": "content",
                "role": "references",
                "variant": "table",
                "slide_intent": "accountability",
                "role_layout_variant": "dense",
                "title": "Each trigger maps to an owner and evidence source",
                "sources": ["S1", "S2", "S3"],
                "table": {
                    "table_style": "references",
                    "headers": ["Record", "Owner / basis", "Control or use", "Source"],
                    "rows": [
                        ["Procurement", "Resilience Office", "Framework by week 2", "S3"],
                        ["Response", "Neighborhood Partners", "260 opt-ins by week 5", "S3"],
                        ["Eligibility", "Building Department", "Roof list by week 7", "S3"],
                        ["Delivery", "Installer + Analytics", "300 passes; report by week 17", "S3"],
                        ["Neighborhood evidence", "S1 — neighborhoods.csv", "Heat, roofs, HVI, cooling", "Slides 2–3"],
                        ["Decision evidence", "S2 — options.csv", "Budget, reach, timing, risk", "Slides 1, 4–5"],
                        ["Operating evidence", "S3 — implementation.csv", "Owners, gates, principal risks", "Slides 1, 5–7"],
                    ],
                },
            },
        ],
    }


def run(outdir: Path) -> dict[str, Any]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required")
    outdir.mkdir(parents=True, exist_ok=True)
    outline = outdir / "outline.json"
    pptx = outdir / "deck.pptx"
    qa_dir = outdir / "qa"
    visual_dir = outdir / "visual"
    outline.write_text(json.dumps(_outline(), indent=2) + "\n", encoding="utf-8")
    _run([node, str(ROOT / "scripts" / "build_deck_pptxgenjs.js"), "--outline", str(outline), "--output", str(pptx), "--style-preset", "warm-terracotta"])
    _run([sys.executable, str(ROOT / "scripts" / "qa_gate.py"), "--input", str(pptx), "--outline", str(outline), "--outdir", str(qa_dir), "--style-preset", "warm-terracotta", "--allow-issues"])
    accessibility = qa_dir / "accessibility.json"
    _run([sys.executable, str(ROOT / "scripts" / "accessibility_qa.py"), "--input", str(pptx), "--report", str(accessibility), "--min-body-pt", "16", "--min-metadata-pt", "9", "--strict"])
    _run([sys.executable, str(ROOT / "scripts" / "visual_review.py"), "--input", str(pptx), "--outline", str(outline), "--renders-dir", str(qa_dir / "renders"), "--outdir", str(visual_dir), "--fail-on-warnings"])

    qa = json.loads((qa_dir / "qa_report.json").read_text(encoding="utf-8"))
    access = json.loads(accessibility.read_text(encoding="utf-8"))
    counts = {
        key: int(qa.get(key, 0) or 0)
        for key in (
            "overflow_count", "overlap_count", "geometry_error_count",
            "geometry_warning_count", "whitespace_warning_count",
            "visual_warning_count", "design_error_count", "design_warning_count",
        )
    }
    failures = {key: value for key, value in counts.items() if value}
    if failures or int(access.get("finding_count", 0) or 0):
        raise RuntimeError(f"High-readability v2 smoke failed: counts={failures}, accessibility={access.get('finding_count')}")
    summary = {
        "passed": True,
        "slide_count": 7,
        "counts": counts,
        "accessibility_findings": 0,
        "pptx": str(pptx.resolve()),
        "contact_sheet": str((visual_dir / "contact_sheet.jpg").resolve()),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path)
    args = parser.parse_args()
    if args.outdir:
        summary = run(args.outdir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="presentation-skill-readable-v2-") as tmp:
            summary = run(Path(tmp))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
