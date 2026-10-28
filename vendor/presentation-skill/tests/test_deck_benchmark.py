from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from deck_benchmark import (  # noqa: E402
    ARM_IDS,
    BLIND_LABELS,
    BenchmarkError,
    analyze_benchmark,
    bootstrap_pairwise,
    build_review_packet,
    evaluate_superiority,
    freeze_manifest,
    ingest_artifact,
    ingest_failure,
    ingest_scores,
    load_run_records,
    validate_manifest,
    validate_review_packet,
)


class DeckBenchmarkTests(unittest.TestCase):
    def _draft_manifest(self, *, benchmark_id: str = "deck-benchmark-fixture") -> dict:
        return {
            "schema_version": "deck-benchmark-manifest/v1",
            "benchmark_id": benchmark_id,
            "arms": [
                {"arm_id": "codex_native", "display_name": "Native generation"},
                {"arm_id": "claude_code", "display_name": "Code-style generation"},
                {"arm_id": "presentation_skill", "display_name": "Repository workflow"},
            ],
            "prompts": [
                {
                    "prompt_id": "urban-heat-plan",
                    "topic": "Urban heat adaptation",
                    "content": "Create a six-slide decision deck for a city resilience committee.",
                    "constraints": {
                        "content": [
                            "State the decision on slide one.",
                            "Include implementation owners and timing.",
                        ],
                        "evidence": [
                            "Use only the supplied temperature and budget table.",
                            "Cite every quantitative claim on-slide.",
                        ],
                        "assets": [
                            "Use the supplied ward map once.",
                            "Do not use network-fetched assets.",
                        ],
                    },
                    "seeds": [11, 22, 33],
                }
            ],
        }

    def _manifest(self, *, benchmark_id: str = "deck-benchmark-fixture") -> dict:
        return freeze_manifest(self._draft_manifest(benchmark_id=benchmark_id))

    def _write_pptx(self, root: Path, name: str, marker: str) -> Path:
        path = root / name
        with zipfile.ZipFile(path, "w") as package:
            package.writestr("[Content_Types].xml", "<Types/>")
            package.writestr("ppt/presentation.xml", f"<presentation>{marker}</presentation>")
        return path

    def _submission(
        self,
        manifest: dict,
        *,
        prompt_id: str,
        seed: int,
        arm_id: str,
        failed_gate: str | None = None,
    ) -> dict:
        hard_gates = {}
        for gate_id in (
            "layout",
            "readability",
            "placeholders",
            "editability",
            "reproducibility",
        ):
            hard_gates[gate_id] = {
                "status": "fail" if gate_id == failed_gate else "pass",
                "assessor": "fixture-assessor",
                "evidence": [f"fixture evidence for {gate_id}"],
            }
        return {
            "schema_version": "deck-benchmark-submission/v1",
            "manifest_sha256": manifest["manifest_sha256"],
            "prompt_id": prompt_id,
            "seed": seed,
            "arm_id": arm_id,
            "provenance": {
                "mode": "external-artifact-ingestion",
                "generator_executed_by_harness": False,
                "submitted_by": "fixture-operator",
                "source_run_id": f"external::{prompt_id}::{seed}::{arm_id}",
            },
            "blinding_attestation": {
                "self_identifying_content": False,
                "assessor": "fixture-blinding-reviewer",
                "evidence": ["Visible slides and package metadata were checked."],
            },
            "hard_gates": hard_gates,
        }

    def _failure_submission(
        self,
        manifest: dict,
        *,
        prompt_id: str,
        seed: int,
        arm_id: str,
    ) -> dict:
        submission = self._submission(
            manifest,
            prompt_id=prompt_id,
            seed=seed,
            arm_id=arm_id,
        )
        for gate in submission["hard_gates"].values():
            gate["status"] = "fail"
            gate["evidence"] = ["No reviewable PPTX was produced."]
        submission["failure"] = {
            "kind": "timeout",
            "stage": "generation",
            "summary": "The generator exceeded the preregistered time limit.",
            "evidence": ["External run receipt recorded exit status 124."],
        }
        return submission

    def _ingest_matrix(
        self,
        root: Path,
        manifest: dict,
        *,
        failed_coordinate: tuple[int, str] | None = None,
    ) -> Path:
        store = root / "store"
        prompt = manifest["prompts"][0]
        for seed in prompt["seeds"]:
            for arm_id in ARM_IDS:
                artifact = self._write_pptx(
                    root,
                    f"source-{seed}-{arm_id}.pptx",
                    f"{seed}-{arm_id}",
                )
                failed_gate = (
                    "layout" if failed_coordinate == (seed, arm_id) else None
                )
                ingest_artifact(
                    manifest=manifest,
                    submission=self._submission(
                        manifest,
                        prompt_id=prompt["prompt_id"],
                        seed=seed,
                        arm_id=arm_id,
                        failed_gate=failed_gate,
                    ),
                    artifact_path=artifact,
                    store=store,
                )
        return store

    def _packet_fixture(
        self, root: Path, manifest: dict
    ) -> tuple[Path, dict, dict]:
        store = self._ingest_matrix(root, manifest)
        packet, key = build_review_packet(
            manifest=manifest,
            store=store,
            output_dir=root / "public-packet",
            key_output=root / "private-blind-key.json",
            randomization_seed=719,
        )
        return store, packet, key

    def _score_sheet(self, packet: dict, *, reviewer_id: str = "reviewer-01") -> dict:
        return {
            "schema_version": "deck-benchmark-score-sheet/v1",
            "packet_sha256": packet["packet_sha256"],
            "reviewer_id": reviewer_id,
            "blinded": True,
            "scores": [
                {
                    "case_id": case["case_id"],
                    "blind_label": artifact["blind_label"],
                    "dimensions": {
                        "Content": 75,
                        "Aesthetics": 75,
                        "Editability": 75,
                    },
                }
                for case in packet["cases"]
                for artifact in case["artifacts"]
            ],
        }

    def _sheet_hash(self, sheet: dict) -> str:
        payload = json.dumps(sheet, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def test_manifest_rejects_incomplete_constraints_and_seed_denominator(self) -> None:
        missing_evidence = self._draft_manifest()
        missing_evidence["prompts"][0]["constraints"]["evidence"] = []
        with self.assertRaisesRegex(BenchmarkError, "at least one explicit constraint"):
            freeze_manifest(missing_evidence)

        two_seeds = self._draft_manifest()
        two_seeds["prompts"][0]["seeds"] = [11, 22]
        with self.assertRaisesRegex(BenchmarkError, "exactly 3 seeds"):
            freeze_manifest(two_seeds)

    def test_manifest_rejects_unblinded_or_mutated_documents(self) -> None:
        unblinded = self._draft_manifest()
        unblinded["visibility"] = "public"
        with self.assertRaisesRegex(BenchmarkError, "visibility must be hidden"):
            freeze_manifest(unblinded)

        frozen = self._manifest()
        frozen["prompts"][0]["topic"] = "Changed after freezing"
        with self.assertRaisesRegex(BenchmarkError, "does not match the frozen manifest"):
            validate_manifest(frozen)

    def test_artifact_ingestion_rejects_mismatched_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            artifact = self._write_pptx(root, "deck.pptx", "fixture")
            submission = self._submission(
                manifest,
                prompt_id="urban-heat-plan",
                seed=11,
                arm_id="codex_native",
            )
            submission["manifest_sha256"] = "0" * 64
            with self.assertRaisesRegex(BenchmarkError, "does not match the frozen manifest"):
                ingest_artifact(
                    manifest=manifest,
                    submission=submission,
                    artifact_path=artifact,
                    store=root / "store",
                )

    def test_incomplete_run_matrix_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            artifact = self._write_pptx(root, "deck.pptx", "fixture")
            ingest_artifact(
                manifest=manifest,
                submission=self._submission(
                    manifest,
                    prompt_id="urban-heat-plan",
                    seed=11,
                    arm_id="codex_native",
                ),
                artifact_path=artifact,
                store=root / "store",
            )
            with self.assertRaisesRegex(BenchmarkError, "matrix is incomplete"):
                load_run_records(
                    manifest=manifest,
                    store=root / "store",
                    require_complete=True,
                )

    def test_ingestion_requires_external_provenance_and_every_hard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            artifact = self._write_pptx(root, "deck.pptx", "fixture")
            submission = self._submission(
                manifest,
                prompt_id="urban-heat-plan",
                seed=11,
                arm_id="codex_native",
            )
            submission["provenance"]["generator_executed_by_harness"] = True
            with self.assertRaisesRegex(BenchmarkError, "only ingests artifacts"):
                ingest_artifact(
                    manifest=manifest,
                    submission=submission,
                    artifact_path=artifact,
                    store=root / "store",
                )

            submission = self._submission(
                manifest,
                prompt_id="urban-heat-plan",
                seed=11,
                arm_id="codex_native",
            )
            del submission["hard_gates"]["reproducibility"]
            with self.assertRaisesRegex(BenchmarkError, "reproducibility"):
                ingest_artifact(
                    manifest=manifest,
                    submission=submission,
                    artifact_path=artifact,
                    store=root / "store",
                )

    def test_failure_runs_remain_in_denominator_and_receive_blinded_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            store = root / "store"
            prompt = manifest["prompts"][0]
            failure_key = (prompt["prompt_id"], prompt["seeds"][0], "codex_native")
            for seed in prompt["seeds"]:
                for arm_id in ARM_IDS:
                    key = (prompt["prompt_id"], seed, arm_id)
                    if key == failure_key:
                        ingest_failure(
                            manifest=manifest,
                            submission=self._failure_submission(
                                manifest,
                                prompt_id=prompt["prompt_id"],
                                seed=seed,
                                arm_id=arm_id,
                            ),
                            store=store,
                        )
                    else:
                        artifact = self._write_pptx(
                            root,
                            f"source-{seed}-{arm_id}.pptx",
                            f"{seed}-{arm_id}",
                        )
                        ingest_artifact(
                            manifest=manifest,
                            submission=self._submission(
                                manifest,
                                prompt_id=prompt["prompt_id"],
                                seed=seed,
                                arm_id=arm_id,
                            ),
                            artifact_path=artifact,
                            store=store,
                        )

            records = load_run_records(manifest=manifest, store=store, require_complete=True)
            self.assertIn("failure", records[failure_key])
            self.assertFalse(records[failure_key]["hard_gate_pass"])
            packet, key = build_review_packet(
                manifest=manifest,
                store=store,
                output_dir=root / "packet",
                key_output=root / "private-key.json",
                randomization_seed=719,
            )
            failure_option = next(
                option
                for mapping in key["mappings"]
                if mapping["prompt_id"] == failure_key[0] and mapping["seed"] == failure_key[1]
                for option in mapping["options"]
                if option["arm_id"] == failure_key[2]
            )
            failure_case = next(
                case
                for case in packet["cases"]
                if any(
                    artifact["blind_label"] == failure_option["blind_label"]
                    for artifact in case["artifacts"]
                )
                and any(
                    mapping["case_id"] == case["case_id"]
                    and mapping["prompt_id"] == failure_key[0]
                    and mapping["seed"] == failure_key[1]
                    for mapping in key["mappings"]
                )
            )
            failure_artifact = next(
                artifact
                for artifact in failure_case["artifacts"]
                if artifact["blind_label"] == failure_option["blind_label"]
            )
            placeholder = root / "packet" / failure_artifact["path"]
            with zipfile.ZipFile(placeholder) as package:
                self.assertIn("ppt/presentation.xml", package.namelist())
            self.assertEqual(
                hashlib.sha256(placeholder.read_bytes()).hexdigest(),
                failure_artifact["sha256"],
            )

    def test_failure_submission_requires_all_hard_gates_to_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            submission = self._failure_submission(
                manifest,
                prompt_id="urban-heat-plan",
                seed=11,
                arm_id="codex_native",
            )
            submission["hard_gates"]["layout"]["status"] = "pass"
            with self.assertRaisesRegex(BenchmarkError, "must fail every hard gate"):
                ingest_failure(manifest=manifest, submission=submission, store=root / "store")

            artifact = self._write_pptx(root, "deck.pptx", "fixture")
            with self.assertRaisesRegex(BenchmarkError, "must use ingest_failure"):
                ingest_artifact(
                    manifest=manifest,
                    submission=self._failure_submission(
                        manifest,
                        prompt_id="urban-heat-plan",
                        seed=11,
                        arm_id="codex_native",
                    ),
                    artifact_path=artifact,
                    store=root / "store",
                )

    def test_review_packet_is_deterministic_blinded_and_randomized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            store = self._ingest_matrix(root, manifest)
            packet_one, key_one = build_review_packet(
                manifest=manifest,
                store=store,
                output_dir=root / "packet-one",
                key_output=root / "key-one.json",
                randomization_seed=719,
            )
            packet_two, key_two = build_review_packet(
                manifest=manifest,
                store=store,
                output_dir=root / "packet-two",
                key_output=root / "key-two.json",
                randomization_seed=719,
            )
            self.assertEqual(packet_one, packet_two)
            self.assertEqual(key_one, key_two)
            self.assertTrue(packet_one["blinded"])
            public_json = json.dumps(packet_one).casefold()
            for arm_id in ARM_IDS:
                self.assertNotIn(arm_id, public_json)
            for case in packet_one["cases"]:
                self.assertEqual(
                    {artifact["blind_label"] for artifact in case["artifacts"]},
                    set(BLIND_LABELS),
                )
                self.assertTrue(
                    all("option-" in artifact["path"] for artifact in case["artifacts"])
                )
            private_arms = {
                option["arm_id"]
                for mapping in key_one["mappings"]
                for option in mapping["options"]
            }
            self.assertEqual(private_arms, set(ARM_IDS))

            leaked = copy.deepcopy(packet_one)
            leaked["cases"][0]["artifacts"][0]["arm_id"] = "codex_native"
            with self.assertRaisesRegex(BenchmarkError, "unknown fields: arm_id"):
                validate_review_packet(leaked)

    def test_score_ingestion_rejects_incomplete_and_unblinded_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            _, packet, key = self._packet_fixture(root, manifest)

            incomplete = self._score_sheet(packet)
            incomplete["scores"].pop()
            with self.assertRaisesRegex(BenchmarkError, "incomplete or mismatched"):
                ingest_scores(
                    packet=packet,
                    blind_key=key,
                    score_sheets=[(incomplete, self._sheet_hash(incomplete))],
                )

            unblinded = self._score_sheet(packet)
            unblinded["blinded"] = False
            with self.assertRaisesRegex(BenchmarkError, "blinded must be true"):
                ingest_scores(
                    packet=packet,
                    blind_key=key,
                    score_sheets=[(unblinded, self._sheet_hash(unblinded))],
                )

    def test_analysis_is_deterministic_and_rejects_mismatched_scores(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            store, packet, key = self._packet_fixture(root, manifest)
            sheet = self._score_sheet(packet)
            normalized = ingest_scores(
                packet=packet,
                blind_key=key,
                score_sheets=[(sheet, self._sheet_hash(sheet))],
            )
            report_one = analyze_benchmark(
                manifest=manifest,
                store=store,
                normalized_scores=normalized,
                bootstrap_iterations=250,
                bootstrap_seed=17,
            )
            report_two = analyze_benchmark(
                manifest=manifest,
                store=store,
                normalized_scores=normalized,
                bootstrap_iterations=250,
                bootstrap_seed=17,
            )
            self.assertEqual(report_one, report_two)
            self.assertEqual(report_one["denominator"]["paired_units"], 3)
            self.assertEqual(len(report_one["pairwise"]), 6)
            self.assertTrue(
                all(not result["superiority_claim"] for result in report_one["pairwise"])
            )

            other_manifest = self._manifest(benchmark_id="other-benchmark-fixture")
            with self.assertRaisesRegex(BenchmarkError, "manifest does not match"):
                analyze_benchmark(
                    manifest=other_manifest,
                    store=store,
                    normalized_scores=normalized,
                    bootstrap_iterations=250,
                    bootstrap_seed=17,
                )

    def test_failed_hard_gate_remains_in_denominator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._manifest()
            store = self._ingest_matrix(
                root,
                manifest,
                failed_coordinate=(11, "presentation_skill"),
            )
            packet, key = build_review_packet(
                manifest=manifest,
                store=store,
                output_dir=root / "public-packet",
                key_output=root / "private-key.json",
                randomization_seed=719,
            )
            sheet = self._score_sheet(packet)
            normalized = ingest_scores(
                packet=packet,
                blind_key=key,
                score_sheets=[(sheet, self._sheet_hash(sheet))],
            )
            report = analyze_benchmark(
                manifest=manifest,
                store=store,
                normalized_scores=normalized,
                bootstrap_iterations=250,
                bootstrap_seed=17,
            )
            self.assertEqual(report["denominator"]["artifact_runs"], 9)
            skill_metrics = report["arm_metrics"]["presentation_skill"]
            self.assertAlmostEqual(skill_metrics["hard_gate_pass_rate"], 2 / 3)
            self.assertAlmostEqual(skill_metrics["failure_rate"], 1 / 3)
            self.assertTrue(
                all(
                    not result["superiority_claim"]
                    for result in report["pairwise"]
                    if result["candidate"] == "presentation_skill"
                )
            )

    def test_bootstrap_and_superiority_rule_use_strict_frozen_thresholds(self) -> None:
        bootstrap = bootstrap_pairwise(
            [90, 92, 94, 96, 98],
            [70, 72, 74, 76, 78],
            iterations=500,
            seed=101,
        )
        self.assertEqual(bootstrap["win_rate"], 1.0)
        self.assertEqual(bootstrap["win_rate_ci_95"], {"lower": 1.0, "upper": 1.0})

        passing = evaluate_superiority(
            win_rate=0.61,
            win_rate_ci_lower=0.56,
            candidate_hard_gate_pass_rate=0.95,
            candidate_editability=0.71,
            comparator_editability=0.75,
            candidate_failure_rate=0.09,
            comparator_failure_rate=0.05,
        )
        self.assertTrue(passing["superiority_claim"])

        for override in (
            {"win_rate": 0.60},
            {"win_rate_ci_lower": 0.55},
            {"candidate_hard_gate_pass_rate": 0.949},
            {"candidate_editability": 0.69},
            {"candidate_failure_rate": 0.11},
        ):
            arguments = {
                "win_rate": 0.61,
                "win_rate_ci_lower": 0.56,
                "candidate_hard_gate_pass_rate": 0.95,
                "candidate_editability": 0.71,
                "comparator_editability": 0.75,
                "candidate_failure_rate": 0.09,
                "comparator_failure_rate": 0.05,
            }
            arguments.update(override)
            with self.subTest(override=override):
                self.assertFalse(
                    evaluate_superiority(**arguments)["superiority_claim"]
                )

    def test_cli_help_lists_the_offline_pipeline(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "deck_benchmark.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in (
            "freeze-manifest",
            "ingest-artifact",
            "build-review-packet",
            "ingest-scores",
            "analyze",
        ):
            self.assertIn(command, result.stdout)


if __name__ == "__main__":
    unittest.main()
