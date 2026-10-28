#!/usr/bin/env python3
"""Verify the lean model-adaptive public CLI from brief through draft build."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PRESENT = ROOT / "scripts" / "present.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(PRESENT), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"present.py {' '.join(args)} failed:\n{completed.stdout}")
    return completed


def main() -> int:
    prompt = (
        "A concise civic infrastructure deck with heat-risk evidence, "
        "service tradeoffs, implementation owners, and sources"
    )
    candidate_counts = {"luna": 1, "terra": 2, "sol": 3}
    brief_bytes: dict[str, int] = {}
    for profile, expected_count in candidate_counts.items():
        completed = _run(
            "brief",
            "--topic",
            "How city libraries become climate refuges",
            "--prompt",
            prompt,
            "--profile",
            profile,
            "--slides",
            "7",
        )
        brief = json.loads(completed.stdout)
        actual = len(brief.get("route_candidates") or [])
        if actual != expected_count:
            raise AssertionError(f"{profile} candidate count={actual}, expected={expected_count}")
        brief_bytes[profile] = len(completed.stdout.encode("utf-8"))
        if brief_bytes[profile] > 9000:
            raise AssertionError(f"{profile} brief exceeded 9 KB: {brief_bytes[profile]}")

    with tempfile.TemporaryDirectory(prefix="presentation-skill-present-") as tmp:
        workspace = Path(tmp) / "workspace"
        _run(
            "init",
            "--workspace",
            str(workspace),
            "--title",
            "How city libraries become climate refuges",
            "--prompt",
            prompt,
            "--profile",
            "luna",
            "--overwrite",
        )
        if (workspace / "deck_start_packet.json").exists():
            raise AssertionError("default public init unexpectedly persisted the full audit packet")
        source_files = [
            path
            for path in workspace.iterdir()
            if path.is_file() and path.suffix.lower() in {".json", ".md"}
        ]
        source_bytes = sum(path.stat().st_size for path in source_files)
        if source_bytes > 350_000:
            raise AssertionError(f"lean workspace exceeded 350 KB: {source_bytes}")
        _run("build", "--workspace", str(workspace), "--draft")
        report = json.loads(
            (workspace / "build" / "build_workspace_report.json").read_text(encoding="utf-8")
        )
        run = report.get("run") if isinstance(report.get("run"), dict) else {}
        if run.get("status") != "succeeded" or int(run.get("returncode", 1) or 0) != 0:
            raise AssertionError(f"draft build report did not pass: {report}")
        qa = json.loads((workspace / "build" / "qa" / "report.json").read_text(encoding="utf-8"))
        counts = {
            key: int(qa.get(key, 0) or 0)
            for key in (
                "overflow_count",
                "overlap_count",
                "geometry_warning_count",
                "whitespace_warning_count",
                "design_warning_count",
            )
        }
        if any(counts.values()):
            raise AssertionError(f"draft QA was not clean: {counts}")

    print(
        json.dumps(
            {
                "passed": True,
                "brief_bytes": brief_bytes,
                "candidate_counts": candidate_counts,
                "workspace_source_bytes": source_bytes,
                "draft_qa_counts": counts,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
