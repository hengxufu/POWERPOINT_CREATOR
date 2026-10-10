#!/usr/bin/env python3
"""Offline self-test for PPT session initialization and element composition."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from pptx import Presentation


HERE = Path(__file__).resolve().parent


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run(*args: object, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(arg) for arg in args], text=True, capture_output=True, encoding="utf-8", errors="replace"
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    if not expect_success and result.returncode == 0:
        raise AssertionError("Command unexpectedly succeeded")
    return result


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="research-ppt-skill-", dir=HERE.parent, ignore_cleanup_errors=True) as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        run(
            sys.executable,
            HERE / "init_ppt_session.py",
            "--out", workspace,
            "--title", "测试汇报",
            "--project-root", root,
        )
        session = json.loads((workspace / "session.json").read_text(encoding="utf-8"))
        assert session["planning_owner"] == "chatgpt-web:gpt-6-astra"
        assert (workspace / "planning" / "gpt6_task_packet.md").is_file()

        source = root / "source.pptx"
        prs = Presentation()
        prs.slides.add_slide(prs.slide_layouts[6])
        prs.save(source)

        asset = root / "asset.png"
        image = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
        ImageDraw.Draw(image).ellipse((60, 60, 540, 540), fill=(16, 114, 108, 255))
        image.save(asset)
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()

        job = root / "job"
        job.mkdir()
        dump(job / "job.json", {
            "status": "accepted",
            "spec": {"kind": "icon", "slide_id": "slide-01", "object_id": "sensor"},
            "asset_file": asset.name,
            "sha256": digest,
        })
        dump(job / "placement.json", {
            "schema": "single_element_placement_v1",
            "asset_file": str(asset),
            "asset_sha256": digest,
            "image_box_inches": [1.0, 1.0, 2.0, 2.0],
        })
        manifest = root / "manifest.json"
        dump(manifest, {
            "schema": "ppt_element_manifest_v1",
            "max_generated_asset_area_fraction": 0.55,
            "elements": [{"kind": "icon", "slide_number": 1, "job_dir": str(job)}],
        })
        output = root / "output.pptx"
        report = root / "report.json"
        run(sys.executable, HERE / "compose_elements.py", "--pptx", source, "--manifest", manifest, "--out", output, "--report", report)
        result = Presentation(output)
        pictures = [shape for shape in result.slides[0].shapes if shape.name == "slide-01/sensor"]
        assert len(pictures) == 1
        assert hashlib.sha256(pictures[0].image.blob).hexdigest() == digest
        assert json.loads(report.read_text(encoding="utf-8"))["whole_slide_generation_used"] is False

        bad_manifest = root / "bad-manifest.json"
        dump(bad_manifest, {
            "schema": "ppt_element_manifest_v1",
            "elements": [{"kind": "full_slide", "slide_number": 1, "job_dir": str(job)}],
        })
        run(
            sys.executable, HERE / "compose_elements.py",
            "--pptx", source,
            "--manifest", bad_manifest,
            "--out", root / "forbidden.pptx",
            "--report", root / "forbidden.json",
            expect_success=False,
        )
    print("offline pipeline self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
