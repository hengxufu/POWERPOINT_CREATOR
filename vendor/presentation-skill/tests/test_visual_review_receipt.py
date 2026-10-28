from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from visual_review_receipt import create_receipt, validate_receipt  # noqa: E402


class VisualReviewReceiptTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, Path]:
        pptx = root / "deck.pptx"
        with zipfile.ZipFile(pptx, "w") as package:
            package.writestr("[Content_Types].xml", "<Types/>")
            package.writestr("ppt/presentation.xml", "<presentation/>")
        renders = root / "renders"
        renders.mkdir()
        (renders / "slide-1.png").write_bytes(b"render-one")
        (renders / "slide-2.png").write_bytes(b"render-two")
        review = root / "review.json"
        review.write_text(
            json.dumps(
                {
                    "schema_version": "visual_judgment_v1",
                    "reviewer": {"type": "model", "name": "visual-review-agent"},
                    "verdict": "pass",
                    "findings": [
                        {"slide": 1, "severity": "info", "message": "Reading order is clear."}
                    ],
                }
            ),
            encoding="utf-8",
        )
        return pptx, renders, review

    def test_receipt_validates_exact_deck_and_renders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pptx, renders, review = self._fixture(root)
            receipt = create_receipt(pptx_path=pptx, renders_dir=renders, review_path=review)
            receipt_path = root / "receipt.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            result = validate_receipt(receipt_path=receipt_path, pptx_path=pptx, renders_dir=renders)
            self.assertTrue(result["passed"], result["failures"])

    def test_stale_render_invalidates_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pptx, renders, review = self._fixture(root)
            receipt = create_receipt(pptx_path=pptx, renders_dir=renders, review_path=review)
            receipt_path = root / "receipt.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            (renders / "slide-2.png").write_bytes(b"changed-render")
            result = validate_receipt(receipt_path=receipt_path, pptx_path=pptx, renders_dir=renders)
            self.assertFalse(result["passed"])
            self.assertTrue(any("Rendered-slide hashes" in item for item in result["failures"]))

    def test_passing_review_rejects_unresolved_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pptx, renders, review = self._fixture(root)
            payload = json.loads(review.read_text(encoding="utf-8"))
            payload["findings"] = [{"slide": 2, "severity": "error", "message": "Text overlaps chart."}]
            review.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unresolved"):
                create_receipt(pptx_path=pptx, renders_dir=renders, review_path=review)


if __name__ == "__main__":
    unittest.main()
