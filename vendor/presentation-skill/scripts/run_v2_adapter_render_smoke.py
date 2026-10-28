#!/usr/bin/env python3
"""Render and validate the executable v2 role-layout adapter proof."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from office_package_hash import office_package_normalized_sha256
from pptx import Presentation


ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_RE = re.compile(
    r"\b(?:TODO|TBD|XXX|lorem|ipsum)\b|\[(?:insert|placeholder)[^\]]*\]",
    re.IGNORECASE,
)


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


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _attach_renders(manifest_path: Path, renders_dir: Path) -> None:
    manifest = _load(manifest_path)
    for deck in manifest.get("decks", []):
        for slide in deck.get("slides", []):
            slide_index = int(slide.get("index") or 0)
            slide["render"] = str((renders_dir / f"slide-{slide_index:02d}.jpg").resolve())
    _write(manifest_path, manifest)


def _adapter_receipt_summary(manifest_path: Path) -> dict[str, Any]:
    manifest = _load(manifest_path)
    failures: list[dict[str, Any]] = []
    applied = 0
    adapters: set[str] = set()
    roles: set[str] = set()
    policy_adaptations: set[str] = set()
    for deck in manifest.get("decks", []):
        grammar_id = str(deck.get("id") or "")
        for slide in deck.get("slides", []):
            receipt = slide.get("render_receipt")
            context = {
                "grammar_id": grammar_id,
                "slide": int(slide.get("index") or 0),
                "proof_role": str(slide.get("role") or ""),
            }
            if not isinstance(receipt, dict):
                failures.append({**context, "reason": "missing_render_receipt"})
                continue
            planned = str(receipt.get("planned_adapter") or "")
            executed = str(receipt.get("executed_adapter") or "")
            contract_applied = bool(receipt.get("contract_applied"))
            consumed_slots = receipt.get("consumed_slots")
            if receipt.get("planned_contract_source") != "v2":
                failures.append({**context, "reason": "not_planned_as_v2", "receipt": receipt})
            elif not contract_applied:
                failures.append({**context, "reason": "v2_contract_not_applied", "receipt": receipt})
            elif planned != executed:
                failures.append({**context, "reason": "planned_executed_adapter_mismatch", "receipt": receipt})
            elif not isinstance(consumed_slots, list) or not consumed_slots:
                failures.append({**context, "reason": "no_contract_slots_consumed", "receipt": receipt})
            elif str(receipt.get("grammar_id") or "") != grammar_id:
                failures.append({**context, "reason": "grammar_receipt_mismatch", "receipt": receipt})
            else:
                applied += 1
                adapters.add(executed)
                roles.add(str(receipt.get("canonical_role") or ""))
                if grammar_id == "policy-public-docket":
                    adaptation = str(receipt.get("adaptation") or "").strip()
                    if adaptation:
                        policy_adaptations.add(adaptation)
    if failures:
        raise RuntimeError(f"Executable v2 adapter proof failed: {failures[:5]}")
    expected_policy_adaptations = {
        "policy-title-stage",
        "policy-section-stage",
        "policy-public-record-open",
        "policy-option-docket-open",
        "policy-public-impact-open",
        "policy-option-table-open",
        "policy-decision-board-open",
        "policy-accountability-register-open",
    }
    missing_policy_adaptations = sorted(expected_policy_adaptations - policy_adaptations)
    if missing_policy_adaptations:
        raise RuntimeError(
            "Public Docket role adaptations were not executed: "
            + ", ".join(missing_policy_adaptations)
        )
    return {
        "receipt_count": applied,
        "distinct_adapters": len(adapters),
        "canonical_roles": sorted(role for role in roles if role),
        "policy_adaptations": sorted(policy_adaptations),
    }


def _policy_chrome_audit(pptx_path: Path, manifest_path: Path) -> dict[str, int]:
    manifest = _load(manifest_path)
    policy_slide_numbers = {
        int(slide.get("index") or 0)
        for deck in manifest.get("decks", [])
        if str(deck.get("id") or "") == "policy-public-docket"
        for slide in deck.get("slides", [])
    }
    presentation = Presentation(str(pptx_path))
    persistent_rails = 0
    for slide_number, slide in enumerate(presentation.slides, start=1):
        if slide_number not in policy_slide_numbers:
            continue
        for shape in slide.shapes:
            x = float(shape.left) / 914400.0
            width = float(shape.width) / 914400.0
            height = float(shape.height) / 914400.0
            if x < 0.20 and 0.30 <= width <= 0.50 and height >= 4.0:
                persistent_rails += 1
    if persistent_rails:
        raise RuntimeError(
            f"Public Docket content still contains {persistent_rails} persistent decorative rails"
        )
    return {
        "policy_slide_count": len(policy_slide_numbers),
        "persistent_rail_count": persistent_rails,
    }


def _placeholder_hits(pptx_path: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    presentation = Presentation(str(pptx_path))
    for slide_number, slide in enumerate(presentation.slides, start=1):
        for shape in slide.shapes:
            text = " ".join(str(getattr(shape, "text", "") or "").split())
            if text and PLACEHOLDER_RE.search(text):
                hits.append(
                    {
                        "slide": slide_number,
                        "shape": str(getattr(shape, "name", "")),
                        "text": text[:160],
                    }
                )
    return hits


def _editable_object_counts(pptx_path: Path) -> dict[str, int]:
    presentation = Presentation(str(pptx_path))
    charts = 0
    tables = 0
    text_shapes = 0
    for slide in presentation.slides:
        for shape in slide.shapes:
            charts += int(bool(getattr(shape, "has_chart", False)))
            tables += int(bool(getattr(shape, "has_table", False)))
            text_shapes += int(bool(getattr(shape, "has_text_frame", False) and shape.text.strip()))
    return {
        "slides": len(presentation.slides),
        "native_charts": charts,
        "native_tables": tables,
        "editable_text_shapes": text_shapes,
    }


def _build_once(node: str, output: Path, manifest: Path) -> None:
    _run(
        [
            node,
            str(ROOT / "scripts" / "build_role_contract_showcase.js"),
            "--adapter-proof",
            "--output",
            str(output),
            "--manifest",
            str(manifest),
        ]
    )


def run(output_dir: Path) -> dict[str, Any]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required for the rendered v2 adapter smoke")

    output_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = output_dir / "gallery.pptx"
    repeat_path = output_dir / "gallery-repeat.pptx"
    manifest_path = output_dir / "manifest.json"
    repeat_manifest_path = output_dir / "manifest-repeat.json"
    renders_dir = output_dir / "renders"
    visual_dir = output_dir / "visual"
    structural_dir = output_dir / "structural-artifacts"

    _build_once(node, pptx_path, manifest_path)
    _build_once(node, repeat_path, repeat_manifest_path)
    adapter_receipts = _adapter_receipt_summary(manifest_path)
    repeat_adapter_receipts = _adapter_receipt_summary(repeat_manifest_path)
    if adapter_receipts != repeat_adapter_receipts:
        raise RuntimeError("The executable v2 adapter receipts are not reproducible")
    first_hash = office_package_normalized_sha256(pptx_path)
    repeat_hash = office_package_normalized_sha256(repeat_path)
    if first_hash != repeat_hash:
        raise RuntimeError("The controlled v2 adapter proof is not reproducible")
    policy_chrome = _policy_chrome_audit(pptx_path, manifest_path)

    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_slides.py"),
            "--input",
            str(pptx_path),
            "--outdir",
            str(renders_dir),
            "--dpi",
            "120",
            "--format",
            "jpeg",
        ]
    )
    rendered = sorted(renders_dir.glob("slide-*.jpg"))
    if len(rendered) != 80:
        raise RuntimeError(f"Expected 80 rendered slides, found {len(rendered)}")
    _attach_renders(manifest_path, renders_dir)

    layout_report = output_dir / "layout.json"
    design_report = output_dir / "design.json"
    accessibility_report = output_dir / "accessibility.json"
    structural_report = output_dir / "structural.json"
    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "layout_lint.py"),
            "--input",
            str(pptx_path),
            "--output",
            str(layout_report),
            "--fail-on-error",
        ]
    )
    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "design_rules_qa.py"),
            "--input",
            str(pptx_path),
            "--report",
            str(design_report),
        ]
    )
    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "accessibility_qa.py"),
            "--input",
            str(pptx_path),
            "--report",
            str(accessibility_report),
            "--min-body-pt",
            "8",
            "--min-metadata-pt",
            "7",
            "--strict",
        ]
    )
    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "structural_diversity_v2.py"),
            "--manifest",
            str(manifest_path),
            "--report",
            str(structural_report),
            "--artifacts-dir",
            str(structural_dir),
        ]
    )
    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "visual_review.py"),
            "--input",
            str(pptx_path),
            "--outdir",
            str(visual_dir),
            "--renders-dir",
            str(renders_dir),
            "--fail-on-warnings",
        ]
    )

    placeholder_hits = _placeholder_hits(pptx_path)
    if placeholder_hits:
        raise RuntimeError(f"Placeholder text found: {placeholder_hits[:3]}")
    editable = _editable_object_counts(pptx_path)
    if editable["slides"] != 80 or editable["native_charts"] < 8 or editable["native_tables"] < 16:
        raise RuntimeError(f"Editable object coverage is incomplete: {editable}")

    design = _load(design_report)
    accessibility = _load(accessibility_report)
    structural = _load(structural_report)
    visual = _load(visual_dir / "visual_review.json")
    summary = {
        "passed": True,
        "output_dir": str(output_dir.resolve()),
        "normalized_sha256": first_hash,
        "reproducible": first_hash == repeat_hash,
        "rendered_slides": len(rendered),
        "structural_roles": {
            role: report.get("cluster_count")
            for role, report in structural.get("role_reports", {}).items()
        },
        "structural_failures": structural.get("failures", []),
        "design_warnings": design.get("warning_count", 0),
        "accessibility_findings": accessibility.get("finding_count", 0),
        "visual_warnings": visual.get("warning_count", 0),
        "placeholder_hits": placeholder_hits,
        "editable_objects": editable,
        "adapter_receipts": adapter_receipts,
        "policy_chrome": policy_chrome,
        "contact_sheet": visual.get("contact_sheet", ""),
    }
    _write(output_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.output_dir:
        summary = run(args.output_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="presentation-skill-v2-adapter-") as tmp:
            summary = run(Path(tmp))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
