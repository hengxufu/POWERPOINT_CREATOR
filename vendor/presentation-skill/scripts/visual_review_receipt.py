#!/usr/bin/env python3
"""Bind human/model visual judgment to an exact PPTX and render set."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from office_package_hash import office_package_normalized_sha256


RECEIPT_VERSION = "visual_review_receipt_v1"
REVIEW_VERSION = "visual_judgment_v1"
RENDER_SUFFIXES = {".jpg", ".jpeg", ".png"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _render_records(renders_dir: Path) -> list[dict[str, Any]]:
    if not renders_dir.is_dir():
        raise FileNotFoundError(f"Rendered-slide directory not found: {renders_dir}")
    paths = sorted(
        path for path in renders_dir.iterdir()
        if path.is_file() and path.suffix.lower() in RENDER_SUFFIXES and path.name.startswith("slide-")
    )
    if not paths:
        raise ValueError(f"No slide render images found in {renders_dir}")
    return [
        {"name": path.name, "sha256": _sha256(path), "size_bytes": path.stat().st_size}
        for path in paths
    ]


def _review_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Visual judgment must be a JSON object")
    if payload.get("schema_version") != REVIEW_VERSION:
        raise ValueError(f"Visual judgment schema_version must be {REVIEW_VERSION}")
    reviewer = payload.get("reviewer")
    if not isinstance(reviewer, dict) or reviewer.get("type") not in {"human", "model"}:
        raise ValueError("reviewer.type must be human or model")
    verdict = str(payload.get("verdict") or "").strip().lower()
    if verdict not in {"pass", "fail"}:
        raise ValueError("verdict must be pass or fail")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("findings must be an array")
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise ValueError(f"findings[{index}] must be an object")
        if str(finding.get("severity") or "").lower() not in {"info", "warning", "error", "critical"}:
            raise ValueError(f"findings[{index}].severity is invalid")
        if not str(finding.get("message") or "").strip():
            raise ValueError(f"findings[{index}].message is required")
    return payload


def create_receipt(
    *,
    pptx_path: Path,
    renders_dir: Path,
    review_path: Path,
) -> dict[str, Any]:
    pptx_path = pptx_path.expanduser().resolve()
    renders_dir = renders_dir.expanduser().resolve()
    review_path = review_path.expanduser().resolve()
    if not pptx_path.is_file():
        raise FileNotFoundError(f"PPTX not found: {pptx_path}")
    review = _review_payload(review_path)
    render_records = _render_records(renders_dir)
    unresolved_errors = [
        finding
        for finding in review["findings"]
        if str(finding.get("severity") or "").lower() in {"error", "critical"}
        and finding.get("resolved") is not True
    ]
    verdict = str(review["verdict"]).lower()
    if verdict == "pass" and unresolved_errors:
        raise ValueError("A passing visual judgment cannot contain unresolved error/critical findings")
    return {
        "schema_version": RECEIPT_VERSION,
        "review_schema_version": REVIEW_VERSION,
        "deck": {
            "filename": pptx_path.name,
            "sha256": _sha256(pptx_path),
            "normalized_office_sha256": office_package_normalized_sha256(pptx_path),
        },
        "renders": render_records,
        "render_count": len(render_records),
        "reviewer": review["reviewer"],
        "verdict": verdict,
        "findings": review["findings"],
        "reviewed_at": review.get("reviewed_at"),
        "review_context": review.get("review_context") or {},
    }


def validate_receipt(
    *,
    receipt_path: Path,
    pptx_path: Path,
    renders_dir: Path,
    fail_on_warnings: bool = False,
) -> dict[str, Any]:
    receipt_path = receipt_path.expanduser().resolve()
    pptx_path = pptx_path.expanduser().resolve()
    renders_dir = renders_dir.expanduser().resolve()
    failures: list[str] = []
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"passed": False, "schema_version": RECEIPT_VERSION, "failures": [str(exc)]}
    if not isinstance(receipt, dict) or receipt.get("schema_version") != RECEIPT_VERSION:
        failures.append(f"receipt schema_version must be {RECEIPT_VERSION}")
        receipt = receipt if isinstance(receipt, dict) else {}
    try:
        current_renders = _render_records(renders_dir)
    except (OSError, ValueError) as exc:
        current_renders = []
        failures.append(str(exc))
    deck = receipt.get("deck") if isinstance(receipt.get("deck"), dict) else {}
    if not pptx_path.is_file():
        failures.append(f"PPTX not found: {pptx_path}")
    else:
        if deck.get("sha256") != _sha256(pptx_path):
            failures.append("PPTX SHA-256 does not match the reviewed deck")
        if deck.get("normalized_office_sha256") != office_package_normalized_sha256(pptx_path):
            failures.append("Normalized Office hash does not match the reviewed deck")
    expected_renders = receipt.get("renders") if isinstance(receipt.get("renders"), list) else []
    if expected_renders != current_renders:
        failures.append("Rendered-slide hashes do not match the reviewed render set")
    verdict = str(receipt.get("verdict") or "").lower()
    if verdict != "pass":
        failures.append("Visual reviewer verdict is not pass")
    findings = receipt.get("findings") if isinstance(receipt.get("findings"), list) else []
    unresolved = [
        item for item in findings
        if isinstance(item, dict)
        and item.get("resolved") is not True
        and str(item.get("severity") or "").lower() in ({"warning", "error", "critical"} if fail_on_warnings else {"error", "critical"})
    ]
    if unresolved:
        failures.append(f"Visual receipt has {len(unresolved)} unresolved gated finding(s)")
    return {
        "passed": not failures,
        "schema_version": RECEIPT_VERSION,
        "receipt": str(receipt_path),
        "deck": str(pptx_path),
        "renders_dir": str(renders_dir),
        "render_count": len(current_renders),
        "reviewer": receipt.get("reviewer") or {},
        "verdict": verdict,
        "unresolved_gated_findings": len(unresolved),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or validate a hash-bound visual-review receipt.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--input", required=True, help="Reviewed PPTX")
    create.add_argument("--renders-dir", required=True)
    create.add_argument("--review", required=True, help=f"{REVIEW_VERSION} JSON judgment")
    create.add_argument("--output", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--input", required=True, help="Reviewed PPTX")
    validate.add_argument("--renders-dir", required=True)
    validate.add_argument("--receipt", required=True)
    validate.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()

    if args.command == "create":
        payload = create_receipt(
            pptx_path=Path(args.input),
            renders_dir=Path(args.renders_dir),
            review_path=Path(args.review),
        )
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"passed": True, "receipt": str(output), "render_count": payload["render_count"]}, indent=2))
        return 0

    result = validate_receipt(
        receipt_path=Path(args.receipt),
        pptx_path=Path(args.input),
        renders_dir=Path(args.renders_dir),
        fail_on_warnings=args.fail_on_warnings,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
