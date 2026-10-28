#!/usr/bin/env python3
"""Build a frozen-content A/B proof for two monochrome scientific grammars."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUTDIR = REPO / "decks" / "v011-monochrome-lab-comparison-20260823"
STYLES = {
    "assay_notebook": {
        "style_preset": "lab-report",
        "composition_grammar": "scientific-evidence-plate",
        "palette_key": "lab_monochrome_v1",
        "style_seed": "rapid-lrgs-assay-notebook-20260823",
        "visual_density": "high",
    },
    "journal_appendix": {
        "style_preset": "paper-journal",
        "composition_grammar": "editorial-spread",
        "palette_key": "journal_monochrome_v1",
        "style_seed": "rapid-lrgs-journal-appendix-20260823",
        "visual_density": "medium",
    },
}
SELECTED_SLIDES = (1, 4, 6, 7, 9, 10)


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    path = Path("/System/Library/Fonts/Supplemental") / name
    if path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _run(command: list[str]) -> tuple[float, str]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {completed.returncode}: {' '.join(command)}\n"
            f"{completed.stdout.strip()}"
        )
    return round(time.perf_counter() - started, 3), completed.stdout.strip()


def _write_outline(base: dict, outdir: Path, name: str, style: dict) -> Path:
    payload = copy.deepcopy(base)
    payload["deck_style"].update(style)
    output = outdir / f"outline_{name}.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output


def _make_contact_sheet(outdir: Path) -> Path:
    thumb_w, thumb_h = 390, 219
    margin, label_h, gutter = 34, 54, 18
    canvas = Image.new("RGB", (4 * thumb_w + 5 * gutter, 3 * (thumb_h + label_h) + 4 * gutter), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)
    title_font = _font(24, bold=True)
    label_font = _font(18, bold=True)
    small_font = _font(15)
    styles = ("assay_notebook", "journal_appendix")
    display = {"assay_notebook": "ASSAY NOTEBOOK", "journal_appendix": "JOURNAL APPENDIX"}

    for pair_idx, slide_number in enumerate(SELECTED_SLIDES):
        row = pair_idx // 2
        pair_col = pair_idx % 2
        for style_idx, style in enumerate(styles):
            col = pair_col * 2 + style_idx
            x = gutter + col * (thumb_w + gutter)
            y = gutter + row * (thumb_h + label_h + gutter)
            render = outdir / f"qa_{style}" / "renders" / f"slide-{slide_number:02d}.jpg"
            image = Image.open(render).convert("RGB")
            image = ImageOps.fit(image, (thumb_w, thumb_h), method=Image.Resampling.LANCZOS)
            canvas.paste(image, (x, y + label_h))
            draw.text((x, y), display[style], fill="#171717", font=label_font)
            draw.text((x, y + 25), f"SLIDE {slide_number:02d}", fill="#666666", font=small_font)
            draw.rectangle((x, y + label_h, x + thumb_w - 1, y + label_h + thumb_h - 1), outline="#CFCFCF", width=1)

    output = outdir / "rapid_lrgs_monochrome_ab_contact_sheet.jpg"
    canvas.save(output, quality=92, optimize=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    args = parser.parse_args()
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    base = json.loads((outdir / "outline_content.json").read_text(encoding="utf-8"))
    manifest = {"schema_version": "lab_monochrome_comparison/v1", "same_content": True, "builds": {}}

    for name, style in STYLES.items():
        outline = _write_outline(base, outdir, name, style)
        pptx = outdir / f"rapid_lrgs_{name}.pptx"
        qa_dir = outdir / f"qa_{name}"
        duration, _stdout = _run(
            [
                sys.executable,
                str(REPO / "scripts" / "present.py"),
                "finalize",
                "--outline",
                str(outline),
                "--output",
                str(pptx),
                "--qa-dir",
                str(qa_dir),
            ]
        )
        receipt_path = qa_dir / "finalize_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        manifest["builds"][name] = {
            "outline": outline.name,
            "pptx": pptx.name,
            "duration_seconds": duration,
            "finalize_total_duration_seconds": receipt.get("total_duration_seconds"),
            "passed": receipt.get("passed"),
            "qa_counts": receipt.get("qa_counts"),
            "style": style,
        }

    manifest["contact_sheet"] = _make_contact_sheet(outdir).name
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
