#!/usr/bin/env python3
"""Offline, artifact-driven benchmark harness for presentation generators."""

from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import math
import random
import re
import shutil
import sys
import zipfile
from pathlib import Path
from statistics import fmean
from typing import Any, Mapping, Sequence


MANIFEST_VERSION = "deck-benchmark-manifest/v1"
SUBMISSION_VERSION = "deck-benchmark-submission/v1"
RUN_VERSION = "deck-benchmark-run/v1"
PACKET_VERSION = "deck-benchmark-review-packet/v1"
BLIND_KEY_VERSION = "deck-benchmark-blind-key/v1"
SCORE_SHEET_VERSION = "deck-benchmark-score-sheet/v1"
NORMALIZED_SCORES_VERSION = "deck-benchmark-normalized-scores/v1"
REPORT_VERSION = "deck-benchmark-report/v1"

ARM_IDS = ("codex_native", "claude_code", "presentation_skill")
GATE_IDS = (
    "layout",
    "readability",
    "placeholders",
    "editability",
    "reproducibility",
)
SCORE_DIMENSIONS = ("Content", "Aesthetics", "Editability")
BLIND_LABELS = ("Option A", "Option B", "Option C")

CLAIM_WIN_RATE = 0.60
CLAIM_CI_LOWER = 0.55
CLAIM_HARD_GATE_PASS_RATE = 0.95
NONINFERIORITY_MARGIN = 0.05

_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

FAILURE_KINDS = (
    "timeout",
    "no_artifact",
    "tool_error",
    "refused",
    "invalid_artifact",
    "other",
)
FAILURE_STAGES = ("generation", "render", "export", "validation", "unknown")


class BenchmarkError(ValueError):
    """Raised when benchmark input violates the frozen protocol."""


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise BenchmarkError(f"Value is not canonical JSON data: {exc}") from exc


def _payload_hash(value: Mapping[str, Any], hash_field: str | None = None) -> str:
    payload = dict(value)
    if hash_field is not None:
        payload.pop(hash_field, None)
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: str | Path) -> dict[str, Any]:
    input_path = Path(path)
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError(f"Could not read JSON from {input_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BenchmarkError(f"{input_path} must contain a JSON object")
    return payload


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    )
    output_path.write_text(rendered + "\n", encoding="utf-8")


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BenchmarkError(f"{path} must be an object")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise BenchmarkError(f"{path} must be an array")
    return value


def _check_keys(
    value: Mapping[str, Any],
    *,
    path: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required - optional)
    if missing:
        raise BenchmarkError(f"{path} is missing required fields: {', '.join(missing)}")
    if unknown:
        raise BenchmarkError(f"{path} has unknown fields: {', '.join(unknown)}")


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"{path} must be a non-empty string")
    return value


def _identifier(value: Any, path: str) -> str:
    text = _string(value, path)
    if len(text) > 96 or _ID_RE.fullmatch(text) is None:
        raise BenchmarkError(f"{path} must be a stable lowercase identifier")
    return text


def _sha256(value: Any, path: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise BenchmarkError(f"{path} must be a lowercase SHA-256 digest")
    return value


def _string_list(value: Any, path: str, *, require_nonempty: bool = True) -> list[str]:
    items = _list(value, path)
    if require_nonempty and not items:
        raise BenchmarkError(f"{path} must contain at least one explicit constraint")
    result: list[str] = []
    for index, item in enumerate(items):
        result.append(_string(item, f"{path}[{index}]"))
    if len(result) != len(set(result)):
        raise BenchmarkError(f"{path} must not contain duplicate entries")
    return result


def _hash_seed(*parts: Any) -> int:
    digest = hashlib.sha256(_canonical_json(list(parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _round(value: float) -> float:
    return round(float(value), 10)


def _manifest_body(document: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(document)
    body.pop("manifest_sha256", None)
    return body


def _validate_manifest_body(document: Mapping[str, Any]) -> None:
    _check_keys(
        document,
        path="manifest",
        required={
            "schema_version",
            "benchmark_id",
            "visibility",
            "frozen",
            "arms",
            "prompts",
        },
    )
    if document["schema_version"] != MANIFEST_VERSION:
        raise BenchmarkError(f"manifest.schema_version must be {MANIFEST_VERSION}")
    _identifier(document["benchmark_id"], "manifest.benchmark_id")
    if document["visibility"] != "hidden":
        raise BenchmarkError("manifest.visibility must be hidden")
    if document["frozen"] is not True:
        raise BenchmarkError("manifest.frozen must be true")

    arms = _list(document["arms"], "manifest.arms")
    if len(arms) != len(ARM_IDS):
        raise BenchmarkError("manifest.arms must contain exactly the three benchmark arms")
    arm_names: dict[str, str] = {}
    for index, raw_arm in enumerate(arms):
        arm = _mapping(raw_arm, f"manifest.arms[{index}]")
        _check_keys(
            arm,
            path=f"manifest.arms[{index}]",
            required={"arm_id", "display_name"},
        )
        arm_id = _identifier(arm["arm_id"], f"manifest.arms[{index}].arm_id")
        display_name = _string(
            arm["display_name"], f"manifest.arms[{index}].display_name"
        )
        if arm_id in arm_names:
            raise BenchmarkError(f"manifest.arms contains duplicate arm_id {arm_id}")
        arm_names[arm_id] = display_name
    if set(arm_names) != set(ARM_IDS):
        raise BenchmarkError(
            "manifest.arms must use codex_native, claude_code, and presentation_skill"
        )

    prompts = _list(document["prompts"], "manifest.prompts")
    if not prompts:
        raise BenchmarkError("manifest.prompts must contain at least one prompt")
    prompt_ids: set[str] = set()
    forbidden_markers = {
        marker.casefold()
        for marker in (*ARM_IDS, *arm_names.values())
        if len(marker.strip()) >= 4
    }
    for index, raw_prompt in enumerate(prompts):
        path = f"manifest.prompts[{index}]"
        prompt = _mapping(raw_prompt, path)
        _check_keys(
            prompt,
            path=path,
            required={"prompt_id", "topic", "content", "constraints", "seeds"},
        )
        prompt_id = _identifier(prompt["prompt_id"], f"{path}.prompt_id")
        if prompt_id in prompt_ids:
            raise BenchmarkError(f"manifest.prompts contains duplicate prompt_id {prompt_id}")
        prompt_ids.add(prompt_id)
        _string(prompt["topic"], f"{path}.topic")
        _string(prompt["content"], f"{path}.content")

        constraints = _mapping(prompt["constraints"], f"{path}.constraints")
        _check_keys(
            constraints,
            path=f"{path}.constraints",
            required={"content", "evidence", "assets"},
        )
        for constraint_type in ("content", "evidence", "assets"):
            _string_list(
                constraints[constraint_type],
                f"{path}.constraints.{constraint_type}",
            )

        seeds = _list(prompt["seeds"], f"{path}.seeds")
        if len(seeds) != 3:
            raise BenchmarkError(f"{path}.seeds must contain exactly 3 seeds")
        normalized_seeds: list[int] = []
        for seed_index, seed in enumerate(seeds):
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise BenchmarkError(f"{path}.seeds[{seed_index}] must be an integer")
            if seed < 0 or seed > 2**32 - 1:
                raise BenchmarkError(
                    f"{path}.seeds[{seed_index}] must be between 0 and 4294967295"
                )
            normalized_seeds.append(seed)
        if len(set(normalized_seeds)) != 3:
            raise BenchmarkError(f"{path}.seeds must contain 3 unique seeds")

        public_prompt_text = _canonical_json(
            {
                "topic": prompt["topic"],
                "content": prompt["content"],
                "constraints": prompt["constraints"],
            }
        ).casefold()
        leaked = sorted(marker for marker in forbidden_markers if marker in public_prompt_text)
        if leaked:
            raise BenchmarkError(
                f"{path} contains arm-identifying text and cannot be blinded: {leaked[0]}"
            )


def freeze_manifest(draft: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize, validate, and self-hash a hidden benchmark manifest."""

    allowed = {
        "schema_version",
        "benchmark_id",
        "visibility",
        "frozen",
        "arms",
        "prompts",
    }
    unknown = sorted(set(draft) - allowed)
    if unknown:
        raise BenchmarkError(f"manifest draft has unknown fields: {', '.join(unknown)}")
    required = {"schema_version", "benchmark_id", "arms", "prompts"}
    missing = sorted(required - set(draft))
    if missing:
        raise BenchmarkError(f"manifest draft is missing required fields: {', '.join(missing)}")
    if "visibility" in draft and draft["visibility"] != "hidden":
        raise BenchmarkError("manifest.visibility must be hidden")
    if "frozen" in draft and draft["frozen"] is not True:
        raise BenchmarkError("manifest.frozen must be true")

    body = json.loads(_canonical_json(draft))
    body["visibility"] = "hidden"
    body["frozen"] = True
    _validate_manifest_body(body)
    frozen = dict(body)
    frozen["manifest_sha256"] = _payload_hash(frozen, "manifest_sha256")
    return frozen


def validate_manifest(document: Mapping[str, Any]) -> None:
    """Validate a frozen manifest and its self-hash."""

    _check_keys(
        document,
        path="manifest",
        required={
            "schema_version",
            "benchmark_id",
            "visibility",
            "frozen",
            "arms",
            "prompts",
            "manifest_sha256",
        },
    )
    _validate_manifest_body(_manifest_body(document))
    supplied_hash = _sha256(document["manifest_sha256"], "manifest.manifest_sha256")
    expected_hash = _payload_hash(document, "manifest_sha256")
    if supplied_hash != expected_hash:
        raise BenchmarkError("manifest.manifest_sha256 does not match the frozen manifest")


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = _load_json(path)
    validate_manifest(manifest)
    return manifest


def _manifest_indexes(
    manifest: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    prompts = {prompt["prompt_id"]: prompt for prompt in manifest["prompts"]}
    arms = {arm["arm_id"]: arm for arm in manifest["arms"]}
    return prompts, arms


def _validate_hard_gates(value: Any, path: str) -> dict[str, Mapping[str, Any]]:
    gates = _mapping(value, path)
    _check_keys(gates, path=path, required=set(GATE_IDS))
    normalized: dict[str, Mapping[str, Any]] = {}
    for gate_id in GATE_IDS:
        gate_path = f"{path}.{gate_id}"
        gate = _mapping(gates[gate_id], gate_path)
        _check_keys(gate, path=gate_path, required={"status", "assessor", "evidence"})
        if gate["status"] not in {"pass", "fail"}:
            raise BenchmarkError(f"{gate_path}.status must be pass or fail")
        _string(gate["assessor"], f"{gate_path}.assessor")
        _string_list(gate["evidence"], f"{gate_path}.evidence")
        normalized[gate_id] = gate
    return normalized


def _validate_provenance(value: Any, path: str) -> Mapping[str, Any]:
    provenance = _mapping(value, path)
    _check_keys(
        provenance,
        path=path,
        required={
            "mode",
            "generator_executed_by_harness",
            "submitted_by",
            "source_run_id",
        },
    )
    if provenance["mode"] != "external-artifact-ingestion":
        raise BenchmarkError(f"{path}.mode must be external-artifact-ingestion")
    if provenance["generator_executed_by_harness"] is not False:
        raise BenchmarkError(
            f"{path}.generator_executed_by_harness must be false; this harness only ingests artifacts"
        )
    _string(provenance["submitted_by"], f"{path}.submitted_by")
    _string(provenance["source_run_id"], f"{path}.source_run_id")
    return provenance


def _validate_blinding_attestation(value: Any, path: str) -> Mapping[str, Any]:
    attestation = _mapping(value, path)
    _check_keys(
        attestation,
        path=path,
        required={"self_identifying_content", "assessor", "evidence"},
    )
    if attestation["self_identifying_content"] is not False:
        raise BenchmarkError(
            f"{path}.self_identifying_content must be false before review packet construction"
        )
    _string(attestation["assessor"], f"{path}.assessor")
    _string_list(attestation["evidence"], f"{path}.evidence")
    return attestation


def _validate_failure(value: Any, path: str) -> Mapping[str, Any]:
    failure = _mapping(value, path)
    _check_keys(
        failure,
        path=path,
        required={"kind", "stage", "summary", "evidence"},
    )
    kind = _string(failure["kind"], f"{path}.kind")
    if kind not in FAILURE_KINDS:
        raise BenchmarkError(f"{path}.kind must be one of {', '.join(FAILURE_KINDS)}")
    stage = _string(failure["stage"], f"{path}.stage")
    if stage not in FAILURE_STAGES:
        raise BenchmarkError(f"{path}.stage must be one of {', '.join(FAILURE_STAGES)}")
    _string(failure["summary"], f"{path}.summary")
    _string_list(failure["evidence"], f"{path}.evidence")
    return failure


def _validate_submission(
    submission: Mapping[str, Any], manifest: Mapping[str, Any]
) -> tuple[str, int, str, dict[str, Mapping[str, Any]], Mapping[str, Any] | None]:
    _check_keys(
        submission,
        path="submission",
        required={
            "schema_version",
            "manifest_sha256",
            "prompt_id",
            "seed",
            "arm_id",
            "provenance",
            "blinding_attestation",
            "hard_gates",
        },
        optional={"failure"},
    )
    if submission["schema_version"] != SUBMISSION_VERSION:
        raise BenchmarkError(f"submission.schema_version must be {SUBMISSION_VERSION}")
    supplied_manifest_hash = _sha256(
        submission["manifest_sha256"], "submission.manifest_sha256"
    )
    if supplied_manifest_hash != manifest["manifest_sha256"]:
        raise BenchmarkError("submission manifest does not match the frozen manifest")

    prompts, arms = _manifest_indexes(manifest)
    prompt_id = _identifier(submission["prompt_id"], "submission.prompt_id")
    if prompt_id not in prompts:
        raise BenchmarkError(f"submission.prompt_id {prompt_id} is not in the manifest")
    arm_id = _identifier(submission["arm_id"], "submission.arm_id")
    if arm_id not in arms:
        raise BenchmarkError(f"submission.arm_id {arm_id} is not in the manifest")
    seed = submission["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise BenchmarkError("submission.seed must be an integer")
    if seed not in prompts[prompt_id]["seeds"]:
        raise BenchmarkError(
            f"submission.seed {seed} is not registered for prompt {prompt_id}"
        )
    _validate_provenance(submission["provenance"], "submission.provenance")
    _validate_blinding_attestation(
        submission["blinding_attestation"], "submission.blinding_attestation"
    )
    hard_gates = _validate_hard_gates(submission["hard_gates"], "submission.hard_gates")
    failure = (
        _validate_failure(submission["failure"], "submission.failure")
        if "failure" in submission
        else None
    )
    return prompt_id, seed, arm_id, hard_gates, failure


def _validate_pptx(path: Path) -> None:
    if path.suffix.lower() != ".pptx":
        raise BenchmarkError(f"Artifact must be an editable .pptx file: {path}")
    if not path.is_file():
        raise BenchmarkError(f"Artifact does not exist: {path}")
    try:
        with zipfile.ZipFile(path) as package:
            names = set(package.namelist())
            if "ppt/presentation.xml" not in names:
                raise BenchmarkError(f"Artifact is not a valid PPTX package: {path}")
            corrupt_member = package.testzip()
            if corrupt_member is not None:
                raise BenchmarkError(
                    f"Artifact PPTX contains a corrupt member {corrupt_member}: {path}"
                )
    except zipfile.BadZipFile as exc:
        raise BenchmarkError(f"Artifact is not a readable PPTX package: {path}") from exc


def _record_path(store: Path, prompt_id: str, seed: int, arm_id: str) -> Path:
    return store / "records" / f"{prompt_id}--seed-{seed}--{arm_id}.json"


def _artifact_relative_path(prompt_id: str, seed: int, arm_id: str) -> Path:
    return Path("artifacts") / prompt_id / f"seed-{seed}" / f"{arm_id}.pptx"


def ingest_artifact(
    *,
    manifest: Mapping[str, Any],
    submission: Mapping[str, Any],
    artifact_path: str | Path,
    store: str | Path,
) -> dict[str, Any]:
    """Copy one external artifact into the benchmark store and emit a hashed run record."""

    validate_manifest(manifest)
    prompt_id, seed, arm_id, hard_gates, failure = _validate_submission(submission, manifest)
    if failure is not None:
        raise BenchmarkError("Failure submissions must use ingest_failure, not ingest_artifact")
    source = Path(artifact_path)
    _validate_pptx(source)
    artifact_hash = _file_sha256(source)
    artifact_bytes = source.stat().st_size
    store_path = Path(store)
    relative_artifact = _artifact_relative_path(prompt_id, seed, arm_id)
    destination = store_path / relative_artifact
    record_path = _record_path(store_path, prompt_id, seed, arm_id)

    hard_gate_pass = all(gate["status"] == "pass" for gate in hard_gates.values())
    record: dict[str, Any] = {
        "schema_version": RUN_VERSION,
        "run_id": f"{prompt_id}::seed-{seed}::{arm_id}",
        "manifest_sha256": manifest["manifest_sha256"],
        "benchmark_id": manifest["benchmark_id"],
        "prompt_id": prompt_id,
        "seed": seed,
        "arm_id": arm_id,
        "artifact": {
            "format": "pptx",
            "path": relative_artifact.as_posix(),
            "sha256": artifact_hash,
            "bytes": artifact_bytes,
        },
        "provenance": json.loads(_canonical_json(submission["provenance"])),
        "blinding_attestation": json.loads(
            _canonical_json(submission["blinding_attestation"])
        ),
        "hard_gates": json.loads(_canonical_json(submission["hard_gates"])),
        "hard_gate_pass": hard_gate_pass,
    }
    record["record_sha256"] = _payload_hash(record, "record_sha256")

    if record_path.exists():
        existing = _load_json(record_path)
        if existing != record:
            raise BenchmarkError(
                f"Conflicting run record already exists for {record['run_id']}"
            )
        if not destination.exists() or _file_sha256(destination) != artifact_hash:
            raise BenchmarkError(
                f"Stored artifact is missing or changed for existing run {record['run_id']}"
            )
        return record

    if destination.exists() and _file_sha256(destination) != artifact_hash:
        raise BenchmarkError(f"Conflicting artifact already exists at {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)
    if _file_sha256(destination) != artifact_hash:
        raise BenchmarkError(f"Copied artifact hash mismatch at {destination}")
    _write_json(record_path, record)
    return record


def ingest_failure(
    *,
    manifest: Mapping[str, Any],
    submission: Mapping[str, Any],
    store: str | Path,
) -> dict[str, Any]:
    """Record a generator run that produced no reviewable PPTX."""

    validate_manifest(manifest)
    prompt_id, seed, arm_id, hard_gates, failure = _validate_submission(submission, manifest)
    if failure is None:
        raise BenchmarkError("Failure submissions must include submission.failure")
    passing = [gate_id for gate_id, gate in hard_gates.items() if gate["status"] == "pass"]
    if passing:
        raise BenchmarkError(
            "A run with no reviewable PPTX must fail every hard gate; passing: "
            + ", ".join(passing)
        )

    store_path = Path(store)
    record_path = _record_path(store_path, prompt_id, seed, arm_id)
    record: dict[str, Any] = {
        "schema_version": RUN_VERSION,
        "run_id": f"{prompt_id}::seed-{seed}::{arm_id}",
        "manifest_sha256": manifest["manifest_sha256"],
        "benchmark_id": manifest["benchmark_id"],
        "prompt_id": prompt_id,
        "seed": seed,
        "arm_id": arm_id,
        "failure": json.loads(_canonical_json(failure)),
        "provenance": json.loads(_canonical_json(submission["provenance"])),
        "blinding_attestation": json.loads(
            _canonical_json(submission["blinding_attestation"])
        ),
        "hard_gates": json.loads(_canonical_json(submission["hard_gates"])),
        "hard_gate_pass": False,
    }
    record["record_sha256"] = _payload_hash(record, "record_sha256")

    if record_path.exists():
        existing = _load_json(record_path)
        if existing != record:
            raise BenchmarkError(
                f"Conflicting run record already exists for {record['run_id']}"
            )
        return record
    record_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(record_path, record)
    return record


def _safe_store_path(store: Path, relative_path: str) -> Path:
    candidate_relative = Path(relative_path)
    if candidate_relative.is_absolute():
        raise BenchmarkError("run artifact.path must be relative to the benchmark store")
    store_resolved = store.resolve()
    candidate = (store / candidate_relative).resolve()
    try:
        candidate.relative_to(store_resolved)
    except ValueError as exc:
        raise BenchmarkError("run artifact.path escapes the benchmark store") from exc
    return candidate


def _validate_run_record(
    record: Mapping[str, Any], manifest: Mapping[str, Any], store: Path
) -> tuple[str, int, str]:
    _check_keys(
        record,
        path="run",
        required={
            "schema_version",
            "run_id",
            "manifest_sha256",
            "benchmark_id",
            "prompt_id",
            "seed",
            "arm_id",
            "provenance",
            "blinding_attestation",
            "hard_gates",
            "hard_gate_pass",
            "record_sha256",
        },
        optional={"artifact", "failure"},
    )
    if record["schema_version"] != RUN_VERSION:
        raise BenchmarkError(f"run.schema_version must be {RUN_VERSION}")
    _sha256(record["manifest_sha256"], "run.manifest_sha256")
    if record["manifest_sha256"] != manifest["manifest_sha256"]:
        raise BenchmarkError("run record manifest does not match the frozen manifest")
    if record["benchmark_id"] != manifest["benchmark_id"]:
        raise BenchmarkError("run.benchmark_id does not match the frozen manifest")
    prompts, arms = _manifest_indexes(manifest)
    prompt_id = _identifier(record["prompt_id"], "run.prompt_id")
    arm_id = _identifier(record["arm_id"], "run.arm_id")
    if prompt_id not in prompts or arm_id not in arms:
        raise BenchmarkError("run coordinates are not registered in the frozen manifest")
    seed = record["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise BenchmarkError("run.seed must be an integer")
    if seed not in prompts[prompt_id]["seeds"]:
        raise BenchmarkError("run.seed is not registered for its prompt")
    expected_run_id = f"{prompt_id}::seed-{seed}::{arm_id}"
    if record["run_id"] != expected_run_id:
        raise BenchmarkError("run.run_id does not match its prompt, seed, and arm")

    _validate_provenance(record["provenance"], "run.provenance")
    _validate_blinding_attestation(
        record["blinding_attestation"], "run.blinding_attestation"
    )
    gates = _validate_hard_gates(record["hard_gates"], "run.hard_gates")
    expected_gate_pass = all(gate["status"] == "pass" for gate in gates.values())
    if record["hard_gate_pass"] is not expected_gate_pass:
        raise BenchmarkError("run.hard_gate_pass does not match its gate records")

    has_artifact = "artifact" in record
    has_failure = "failure" in record
    if has_artifact == has_failure:
        raise BenchmarkError("run must contain exactly one of artifact or failure")
    if has_artifact:
        artifact = _mapping(record["artifact"], "run.artifact")
        _check_keys(
            artifact,
            path="run.artifact",
            required={"format", "path", "sha256", "bytes"},
        )
        if artifact["format"] != "pptx":
            raise BenchmarkError("run.artifact.format must be pptx")
        relative_path = _string(artifact["path"], "run.artifact.path")
        artifact_hash = _sha256(artifact["sha256"], "run.artifact.sha256")
        if isinstance(artifact["bytes"], bool) or not isinstance(artifact["bytes"], int):
            raise BenchmarkError("run.artifact.bytes must be an integer")
        artifact_path = _safe_store_path(store, relative_path)
        _validate_pptx(artifact_path)
        if artifact_path.stat().st_size != artifact["bytes"]:
            raise BenchmarkError(f"Stored artifact byte count changed for {expected_run_id}")
        if _file_sha256(artifact_path) != artifact_hash:
            raise BenchmarkError(f"Stored artifact hash changed for {expected_run_id}")
    else:
        _validate_failure(record["failure"], "run.failure")
        if record["hard_gate_pass"] is not False or any(
            gate["status"] != "fail" for gate in gates.values()
        ):
            raise BenchmarkError("run failure records must fail every hard gate")

    record_hash = _sha256(record["record_sha256"], "run.record_sha256")
    if record_hash != _payload_hash(record, "record_sha256"):
        raise BenchmarkError(f"run.record_sha256 does not match {expected_run_id}")
    return prompt_id, seed, arm_id


def expected_run_keys(manifest: Mapping[str, Any]) -> set[tuple[str, int, str]]:
    """Return the frozen same-denominator prompt/seed/arm matrix."""

    validate_manifest(manifest)
    return {
        (prompt["prompt_id"], seed, arm_id)
        for prompt in manifest["prompts"]
        for seed in prompt["seeds"]
        for arm_id in ARM_IDS
    }


def load_run_records(
    *, manifest: Mapping[str, Any], store: str | Path, require_complete: bool = True
) -> dict[tuple[str, int, str], dict[str, Any]]:
    """Load, hash-check, and matrix-check all records in a benchmark store."""

    validate_manifest(manifest)
    store_path = Path(store)
    records_dir = store_path / "records"
    if not records_dir.is_dir():
        raise BenchmarkError(f"Benchmark record directory does not exist: {records_dir}")
    records: dict[tuple[str, int, str], dict[str, Any]] = {}
    for record_path in sorted(records_dir.glob("*.json")):
        record = _load_json(record_path)
        key = _validate_run_record(record, manifest, store_path)
        if key in records:
            raise BenchmarkError(f"Duplicate run record for {key}")
        records[key] = record

    expected = expected_run_keys(manifest)
    extra = sorted(set(records) - expected)
    if extra:
        raise BenchmarkError(f"Benchmark store contains unexpected run coordinates: {extra[0]}")
    if require_complete:
        missing = sorted(expected - set(records))
        if missing:
            raise BenchmarkError(
                f"Benchmark matrix is incomplete; missing {len(missing)} runs, first: {missing[0]}"
            )
    return records


def _path_is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _case_id(manifest_hash: str, prompt_id: str, seed: int) -> str:
    digest = hashlib.sha256(
        f"{manifest_hash}:{prompt_id}:{seed}".encode("utf-8")
    ).hexdigest()[:12]
    return f"case-{digest}"


def _packet_hash(packet: Mapping[str, Any]) -> str:
    return _payload_hash(packet, "packet_sha256")


def _blind_key_hash(key: Mapping[str, Any]) -> str:
    return _payload_hash(key, "key_sha256")


def _normalized_pptx_bytes(raw: bytes) -> bytes:
    source = io.BytesIO(raw)
    output = io.BytesIO()
    with zipfile.ZipFile(source) as package, zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as normalized:
        for name in sorted(package.namelist()):
            original = package.getinfo(name)
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = original.external_attr
            info.create_system = original.create_system
            normalized.writestr(info, package.read(name))
    return output.getvalue()


def _failure_placeholder_pptx() -> bytes:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches, Pt

    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = RGBColor(248, 250, 252)
    title = slide.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(11.33), Inches(0.7))
    title_frame = title.text_frame
    title_frame.text = "No presentation was produced"
    title_frame.paragraphs[0].font.name = "Arial"
    title_frame.paragraphs[0].font.size = Pt(28)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = RGBColor(15, 23, 42)
    title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    detail = slide.shapes.add_textbox(Inches(2.0), Inches(3.20), Inches(9.33), Inches(0.9))
    detail_frame = detail.text_frame
    detail_frame.text = (
        "This option failed before a reviewable PowerPoint deck was delivered. "
        "Score unavailable content, aesthetics, and editability as 0."
    )
    detail_frame.paragraphs[0].font.name = "Arial"
    detail_frame.paragraphs[0].font.size = Pt(15)
    detail_frame.paragraphs[0].font.color.rgb = RGBColor(71, 85, 105)
    detail_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    buffer = io.BytesIO()
    presentation.save(buffer)
    return _normalized_pptx_bytes(buffer.getvalue())


def validate_review_packet(packet: Mapping[str, Any]) -> None:
    """Validate the public packet structure and verify that it is blinded."""

    _check_keys(
        packet,
        path="packet",
        required={
            "schema_version",
            "packet_id",
            "manifest_sha256",
            "blinded",
            "rubric",
            "cases",
            "packet_sha256",
        },
    )
    if packet["schema_version"] != PACKET_VERSION:
        raise BenchmarkError(f"packet.schema_version must be {PACKET_VERSION}")
    _identifier(packet["packet_id"], "packet.packet_id")
    _sha256(packet["manifest_sha256"], "packet.manifest_sha256")
    if packet["blinded"] is not True:
        raise BenchmarkError("packet.blinded must be true")
    rubric = _mapping(packet["rubric"], "packet.rubric")
    _check_keys(
        rubric,
        path="packet.rubric",
        required={"dimensions", "scale", "aggregation", "hard_gate_status_visible"},
    )
    if rubric["dimensions"] != list(SCORE_DIMENSIONS):
        raise BenchmarkError("packet.rubric.dimensions must use the frozen dimensions")
    if rubric["scale"] != {"min": 0, "max": 100}:
        raise BenchmarkError("packet.rubric.scale must be 0 to 100")
    if rubric["aggregation"] != "equal-weight-mean":
        raise BenchmarkError("packet.rubric.aggregation must be equal-weight-mean")
    if rubric["hard_gate_status_visible"] is not False:
        raise BenchmarkError("packet hard-gate status must remain hidden from reviewers")

    cases = _list(packet["cases"], "packet.cases")
    if not cases:
        raise BenchmarkError("packet.cases must not be empty")
    case_ids: set[str] = set()
    artifact_pairs: set[tuple[str, str]] = set()
    for case_index, raw_case in enumerate(cases):
        path = f"packet.cases[{case_index}]"
        case = _mapping(raw_case, path)
        _check_keys(
            case,
            path=path,
            required={"case_id", "topic", "prompt_content", "constraints", "artifacts"},
        )
        case_id = _identifier(case["case_id"], f"{path}.case_id")
        if case_id in case_ids:
            raise BenchmarkError(f"packet contains duplicate case_id {case_id}")
        case_ids.add(case_id)
        _string(case["topic"], f"{path}.topic")
        _string(case["prompt_content"], f"{path}.prompt_content")
        constraints = _mapping(case["constraints"], f"{path}.constraints")
        _check_keys(
            constraints,
            path=f"{path}.constraints",
            required={"content", "evidence", "assets"},
        )
        for constraint_type in ("content", "evidence", "assets"):
            _string_list(
                constraints[constraint_type], f"{path}.constraints.{constraint_type}"
            )
        artifacts = _list(case["artifacts"], f"{path}.artifacts")
        if len(artifacts) != 3:
            raise BenchmarkError(f"{path}.artifacts must contain exactly 3 blinded decks")
        labels: set[str] = set()
        for artifact_index, raw_artifact in enumerate(artifacts):
            artifact_path = f"{path}.artifacts[{artifact_index}]"
            artifact = _mapping(raw_artifact, artifact_path)
            _check_keys(
                artifact,
                path=artifact_path,
                required={"blind_label", "path", "sha256"},
            )
            label = _string(artifact["blind_label"], f"{artifact_path}.blind_label")
            if label not in BLIND_LABELS:
                raise BenchmarkError(f"{artifact_path}.blind_label is not allowed")
            labels.add(label)
            relative = _string(artifact["path"], f"{artifact_path}.path")
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise BenchmarkError(f"{artifact_path}.path must be a safe relative path")
            _sha256(artifact["sha256"], f"{artifact_path}.sha256")
            artifact_pairs.add((case_id, label))
        if labels != set(BLIND_LABELS):
            raise BenchmarkError(f"{path}.artifacts must use each blind label exactly once")

    supplied_hash = _sha256(packet["packet_sha256"], "packet.packet_sha256")
    if supplied_hash != _packet_hash(packet):
        raise BenchmarkError("packet.packet_sha256 does not match the packet")


def _validate_blind_key(
    key: Mapping[str, Any], packet: Mapping[str, Any]
) -> dict[tuple[str, str], Mapping[str, Any]]:
    _check_keys(
        key,
        path="blind_key",
        required={
            "schema_version",
            "packet_sha256",
            "manifest_sha256",
            "benchmark_id",
            "randomization_seed",
            "mappings",
            "key_sha256",
        },
    )
    if key["schema_version"] != BLIND_KEY_VERSION:
        raise BenchmarkError(f"blind_key.schema_version must be {BLIND_KEY_VERSION}")
    if key["packet_sha256"] != packet["packet_sha256"]:
        raise BenchmarkError("blind key does not match the review packet")
    if key["manifest_sha256"] != packet["manifest_sha256"]:
        raise BenchmarkError("blind key manifest does not match the review packet")
    _identifier(key["benchmark_id"], "blind_key.benchmark_id")
    if isinstance(key["randomization_seed"], bool) or not isinstance(
        key["randomization_seed"], int
    ):
        raise BenchmarkError("blind_key.randomization_seed must be an integer")
    key_hash = _sha256(key["key_sha256"], "blind_key.key_sha256")
    if key_hash != _blind_key_hash(key):
        raise BenchmarkError("blind_key.key_sha256 does not match the key")

    packet_pairs = {
        (case["case_id"], artifact["blind_label"])
        for case in packet["cases"]
        for artifact in case["artifacts"]
    }
    mapping_index: dict[tuple[str, str], Mapping[str, Any]] = {}
    for case_index, raw_mapping in enumerate(_list(key["mappings"], "blind_key.mappings")):
        path = f"blind_key.mappings[{case_index}]"
        mapping = _mapping(raw_mapping, path)
        _check_keys(
            mapping,
            path=path,
            required={"case_id", "prompt_id", "seed", "options"},
        )
        case_id = _identifier(mapping["case_id"], f"{path}.case_id")
        _identifier(mapping["prompt_id"], f"{path}.prompt_id")
        seed = mapping["seed"]
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise BenchmarkError(f"{path}.seed must be an integer")
        options = _list(mapping["options"], f"{path}.options")
        if len(options) != 3:
            raise BenchmarkError(f"{path}.options must contain exactly 3 mappings")
        for option_index, raw_option in enumerate(options):
            option_path = f"{path}.options[{option_index}]"
            option = _mapping(raw_option, option_path)
            _check_keys(
                option,
                path=option_path,
                required={"blind_label", "arm_id", "run_id", "artifact_sha256"},
            )
            label = _string(option["blind_label"], f"{option_path}.blind_label")
            arm_id = _identifier(option["arm_id"], f"{option_path}.arm_id")
            if arm_id not in ARM_IDS:
                raise BenchmarkError(f"{option_path}.arm_id is not a benchmark arm")
            _string(option["run_id"], f"{option_path}.run_id")
            _sha256(option["artifact_sha256"], f"{option_path}.artifact_sha256")
            pair = (case_id, label)
            if pair in mapping_index:
                raise BenchmarkError(f"blind key contains duplicate mapping {pair}")
            mapping_index[pair] = {
                **option,
                "prompt_id": mapping["prompt_id"],
                "seed": seed,
            }
    if set(mapping_index) != packet_pairs:
        raise BenchmarkError("blind key mappings do not cover the review packet exactly")
    return mapping_index


def build_review_packet(
    *,
    manifest: Mapping[str, Any],
    store: str | Path,
    output_dir: str | Path,
    key_output: str | Path,
    randomization_seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a blinded public packet and a separate private arm-mapping key."""

    validate_manifest(manifest)
    if isinstance(randomization_seed, bool) or not isinstance(randomization_seed, int):
        raise BenchmarkError("randomization_seed must be an integer")
    store_path = Path(store)
    records = load_run_records(manifest=manifest, store=store_path, require_complete=True)
    output_path = Path(output_dir)
    key_path = Path(key_output)
    if _path_is_within(key_path, output_path):
        raise BenchmarkError("Private blind key must be outside the public packet directory")
    if output_path.exists() and any(output_path.iterdir()):
        raise BenchmarkError(f"Review packet directory must be empty: {output_path}")

    prompt_index, arm_index = _manifest_indexes(manifest)
    cases: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    copy_plan: list[tuple[Path, Path, str]] = []
    write_plan: list[tuple[bytes, Path, str]] = []
    failure_placeholder = _failure_placeholder_pptx()
    failure_placeholder_hash = hashlib.sha256(failure_placeholder).hexdigest()
    for prompt_id in sorted(prompt_index):
        prompt = prompt_index[prompt_id]
        for seed in sorted(prompt["seeds"]):
            case_id = _case_id(manifest["manifest_sha256"], prompt_id, seed)
            randomized_arms = list(ARM_IDS)
            rng = random.Random(
                _hash_seed(
                    "deck-benchmark-blinding",
                    manifest["manifest_sha256"],
                    randomization_seed,
                    case_id,
                )
            )
            rng.shuffle(randomized_arms)
            artifacts: list[dict[str, Any]] = []
            options: list[dict[str, Any]] = []
            for blind_label, arm_id in zip(BLIND_LABELS, randomized_arms):
                record = records[(prompt_id, seed, arm_id)]
                label_slug = blind_label.casefold().replace(" ", "-")
                relative_destination = Path("artifacts") / case_id / f"{label_slug}.pptx"
                destination = output_path / relative_destination
                if "artifact" in record:
                    source = _safe_store_path(store_path, record["artifact"]["path"])
                    artifact_hash = record["artifact"]["sha256"]
                    copy_plan.append((source, destination, artifact_hash))
                else:
                    artifact_hash = failure_placeholder_hash
                    write_plan.append((failure_placeholder, destination, artifact_hash))
                artifacts.append(
                    {
                        "blind_label": blind_label,
                        "path": relative_destination.as_posix(),
                        "sha256": artifact_hash,
                    }
                )
                options.append(
                    {
                        "blind_label": blind_label,
                        "arm_id": arm_id,
                        "run_id": record["run_id"],
                        "artifact_sha256": artifact_hash,
                    }
                )
            cases.append(
                {
                    "case_id": case_id,
                    "topic": prompt["topic"],
                    "prompt_content": prompt["content"],
                    "constraints": json.loads(_canonical_json(prompt["constraints"])),
                    "artifacts": artifacts,
                }
            )
            mappings.append(
                {
                    "case_id": case_id,
                    "prompt_id": prompt_id,
                    "seed": seed,
                    "options": options,
                }
            )

    packet_id_digest = hashlib.sha256(
        f"{manifest['manifest_sha256']}:{randomization_seed}".encode("utf-8")
    ).hexdigest()[:16]
    packet: dict[str, Any] = {
        "schema_version": PACKET_VERSION,
        "packet_id": f"packet-{packet_id_digest}",
        "manifest_sha256": manifest["manifest_sha256"],
        "blinded": True,
        "rubric": {
            "dimensions": list(SCORE_DIMENSIONS),
            "scale": {"min": 0, "max": 100},
            "aggregation": "equal-weight-mean",
            "hard_gate_status_visible": False,
        },
        "cases": cases,
    }
    packet["packet_sha256"] = _packet_hash(packet)
    validate_review_packet(packet)

    serialized_packet = _canonical_json(packet).casefold()
    forbidden_markers = [
        marker.casefold()
        for marker in (*ARM_IDS, *(arm["display_name"] for arm in arm_index.values()))
    ]
    leaked = sorted(marker for marker in forbidden_markers if marker in serialized_packet)
    if leaked:
        raise BenchmarkError(f"Public review packet leaks an arm identity: {leaked[0]}")

    blind_key: dict[str, Any] = {
        "schema_version": BLIND_KEY_VERSION,
        "packet_sha256": packet["packet_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "benchmark_id": manifest["benchmark_id"],
        "randomization_seed": randomization_seed,
        "mappings": mappings,
    }
    blind_key["key_sha256"] = _blind_key_hash(blind_key)
    _validate_blind_key(blind_key, packet)

    output_path.mkdir(parents=True, exist_ok=True)
    for source, destination, expected_hash in copy_plan:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if _file_sha256(destination) != expected_hash:
            raise BenchmarkError(f"Blinded artifact copy hash mismatch at {destination}")
    for payload, destination, expected_hash in write_plan:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        if _file_sha256(destination) != expected_hash:
            raise BenchmarkError(f"Failure placeholder hash mismatch at {destination}")
    _write_json(output_path / "packet.json", packet)
    _write_json(key_path, blind_key)
    return packet, blind_key


def _validate_score_sheet(
    sheet: Mapping[str, Any], packet: Mapping[str, Any]
) -> tuple[str, list[Mapping[str, Any]]]:
    _check_keys(
        sheet,
        path="score_sheet",
        required={"schema_version", "packet_sha256", "reviewer_id", "blinded", "scores"},
    )
    if sheet["schema_version"] != SCORE_SHEET_VERSION:
        raise BenchmarkError(f"score_sheet.schema_version must be {SCORE_SHEET_VERSION}")
    if sheet["packet_sha256"] != packet["packet_sha256"]:
        raise BenchmarkError("score sheet does not match the review packet")
    reviewer_id = _identifier(sheet["reviewer_id"], "score_sheet.reviewer_id")
    if sheet["blinded"] is not True:
        raise BenchmarkError("score_sheet.blinded must be true")
    expected_pairs = {
        (case["case_id"], artifact["blind_label"])
        for case in packet["cases"]
        for artifact in case["artifacts"]
    }
    scores = _list(sheet["scores"], "score_sheet.scores")
    observed_pairs: set[tuple[str, str]] = set()
    normalized_rows: list[Mapping[str, Any]] = []
    for index, raw_score in enumerate(scores):
        path = f"score_sheet.scores[{index}]"
        score = _mapping(raw_score, path)
        _check_keys(
            score,
            path=path,
            required={"case_id", "blind_label", "dimensions"},
            optional={"comment"},
        )
        case_id = _identifier(score["case_id"], f"{path}.case_id")
        blind_label = _string(score["blind_label"], f"{path}.blind_label")
        pair = (case_id, blind_label)
        if pair in observed_pairs:
            raise BenchmarkError(f"score sheet contains duplicate score for {pair}")
        observed_pairs.add(pair)
        dimensions = _mapping(score["dimensions"], f"{path}.dimensions")
        _check_keys(
            dimensions,
            path=f"{path}.dimensions",
            required=set(SCORE_DIMENSIONS),
        )
        normalized_dimensions: dict[str, float] = {}
        for dimension in SCORE_DIMENSIONS:
            value = dimensions[dimension]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise BenchmarkError(f"{path}.dimensions.{dimension} must be numeric")
            number = float(value)
            if not math.isfinite(number) or not 0 <= number <= 100:
                raise BenchmarkError(
                    f"{path}.dimensions.{dimension} must be between 0 and 100"
                )
            normalized_dimensions[dimension] = _round(number)
        if "comment" in score:
            _string(score["comment"], f"{path}.comment")
        normalized_rows.append(
            {
                "case_id": case_id,
                "blind_label": blind_label,
                "dimensions": normalized_dimensions,
            }
        )
    if observed_pairs != expected_pairs:
        missing = sorted(expected_pairs - observed_pairs)
        extra = sorted(observed_pairs - expected_pairs)
        detail = f"missing={len(missing)}, extra={len(extra)}"
        raise BenchmarkError(f"score sheet is incomplete or mismatched ({detail})")
    return reviewer_id, normalized_rows


def _scores_hash(scores: Mapping[str, Any]) -> str:
    return _payload_hash(scores, "scores_sha256")


def ingest_scores(
    *,
    packet: Mapping[str, Any],
    blind_key: Mapping[str, Any],
    score_sheets: Sequence[tuple[Mapping[str, Any], str]],
) -> dict[str, Any]:
    """Validate complete blinded score sheets and privately unblind their rows."""

    validate_review_packet(packet)
    mapping_index = _validate_blind_key(blind_key, packet)
    if not score_sheets:
        raise BenchmarkError("At least one score sheet is required")

    reviewers: list[dict[str, str]] = []
    normalized_scores: list[dict[str, Any]] = []
    reviewer_ids: set[str] = set()
    for sheet, source_hash in score_sheets:
        reviewer_id, rows = _validate_score_sheet(sheet, packet)
        if reviewer_id in reviewer_ids:
            raise BenchmarkError(f"Duplicate reviewer_id {reviewer_id}")
        reviewer_ids.add(reviewer_id)
        _sha256(source_hash, f"score_sheet[{reviewer_id}].source_sha256")
        reviewers.append(
            {"reviewer_id": reviewer_id, "score_sheet_sha256": source_hash}
        )
        for row in rows:
            mapping = mapping_index[(row["case_id"], row["blind_label"])]
            dimensions = dict(row["dimensions"])
            normalized_scores.append(
                {
                    "reviewer_id": reviewer_id,
                    "case_id": row["case_id"],
                    "blind_label": row["blind_label"],
                    "prompt_id": mapping["prompt_id"],
                    "seed": mapping["seed"],
                    "arm_id": mapping["arm_id"],
                    "dimensions": dimensions,
                    "composite": _round(fmean(dimensions.values())),
                }
            )

    reviewers.sort(key=lambda item: item["reviewer_id"])
    normalized_scores.sort(
        key=lambda item: (
            item["reviewer_id"],
            item["prompt_id"],
            item["seed"],
            item["arm_id"],
        )
    )
    result: dict[str, Any] = {
        "schema_version": NORMALIZED_SCORES_VERSION,
        "packet_sha256": packet["packet_sha256"],
        "manifest_sha256": packet["manifest_sha256"],
        "reviewers": reviewers,
        "scores": normalized_scores,
    }
    result["scores_sha256"] = _scores_hash(result)
    validate_normalized_scores(result)
    return result


def validate_normalized_scores(scores: Mapping[str, Any]) -> None:
    _check_keys(
        scores,
        path="normalized_scores",
        required={
            "schema_version",
            "packet_sha256",
            "manifest_sha256",
            "reviewers",
            "scores",
            "scores_sha256",
        },
    )
    if scores["schema_version"] != NORMALIZED_SCORES_VERSION:
        raise BenchmarkError(
            f"normalized_scores.schema_version must be {NORMALIZED_SCORES_VERSION}"
        )
    _sha256(scores["packet_sha256"], "normalized_scores.packet_sha256")
    _sha256(scores["manifest_sha256"], "normalized_scores.manifest_sha256")
    supplied_hash = _sha256(scores["scores_sha256"], "normalized_scores.scores_sha256")
    if supplied_hash != _scores_hash(scores):
        raise BenchmarkError("normalized_scores.scores_sha256 does not match the scores")

    reviewer_ids: set[str] = set()
    for index, raw_reviewer in enumerate(_list(scores["reviewers"], "normalized_scores.reviewers")):
        path = f"normalized_scores.reviewers[{index}]"
        reviewer = _mapping(raw_reviewer, path)
        _check_keys(
            reviewer,
            path=path,
            required={"reviewer_id", "score_sheet_sha256"},
        )
        reviewer_id = _identifier(reviewer["reviewer_id"], f"{path}.reviewer_id")
        if reviewer_id in reviewer_ids:
            raise BenchmarkError(f"normalized_scores contains duplicate reviewer {reviewer_id}")
        reviewer_ids.add(reviewer_id)
        _sha256(reviewer["score_sheet_sha256"], f"{path}.score_sheet_sha256")
    if not reviewer_ids:
        raise BenchmarkError("normalized_scores must contain at least one reviewer")

    seen: set[tuple[str, str, int, str]] = set()
    for index, raw_row in enumerate(_list(scores["scores"], "normalized_scores.scores")):
        path = f"normalized_scores.scores[{index}]"
        row = _mapping(raw_row, path)
        _check_keys(
            row,
            path=path,
            required={
                "reviewer_id",
                "case_id",
                "blind_label",
                "prompt_id",
                "seed",
                "arm_id",
                "dimensions",
                "composite",
            },
        )
        reviewer_id = _identifier(row["reviewer_id"], f"{path}.reviewer_id")
        if reviewer_id not in reviewer_ids:
            raise BenchmarkError(f"{path}.reviewer_id is not declared")
        _identifier(row["case_id"], f"{path}.case_id")
        _string(row["blind_label"], f"{path}.blind_label")
        prompt_id = _identifier(row["prompt_id"], f"{path}.prompt_id")
        seed = row["seed"]
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise BenchmarkError(f"{path}.seed must be an integer")
        arm_id = _identifier(row["arm_id"], f"{path}.arm_id")
        if arm_id not in ARM_IDS:
            raise BenchmarkError(f"{path}.arm_id is not a benchmark arm")
        dimensions = _mapping(row["dimensions"], f"{path}.dimensions")
        _check_keys(
            dimensions,
            path=f"{path}.dimensions",
            required=set(SCORE_DIMENSIONS),
        )
        for dimension in SCORE_DIMENSIONS:
            value = dimensions[dimension]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise BenchmarkError(f"{path}.dimensions.{dimension} must be numeric")
            if not math.isfinite(float(value)) or not 0 <= float(value) <= 100:
                raise BenchmarkError(f"{path}.dimensions.{dimension} is outside 0 to 100")
        expected_composite = _round(fmean(float(dimensions[name]) for name in SCORE_DIMENSIONS))
        if row["composite"] != expected_composite:
            raise BenchmarkError(f"{path}.composite does not match its dimensions")
        key = (reviewer_id, prompt_id, seed, arm_id)
        if key in seen:
            raise BenchmarkError(f"normalized_scores contains duplicate row {key}")
        seen.add(key)


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        raise BenchmarkError("Cannot calculate a percentile from no values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def _paired_win_rate(candidate: Sequence[float], comparator: Sequence[float]) -> float:
    wins = 0.0
    for candidate_score, comparator_score in zip(candidate, comparator):
        if candidate_score > comparator_score:
            wins += 1.0
        elif candidate_score == comparator_score:
            wins += 0.5
    return wins / len(candidate)


def bootstrap_pairwise(
    candidate: Sequence[float],
    comparator: Sequence[float],
    *,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    """Bootstrap paired prompt/seed units for win-rate and score-delta intervals."""

    if not candidate or len(candidate) != len(comparator):
        raise BenchmarkError("Pairwise bootstrap requires equal non-empty paired samples")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 100:
        raise BenchmarkError("bootstrap iterations must be an integer of at least 100")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise BenchmarkError("bootstrap seed must be an integer")
    rng = random.Random(seed)
    unit_count = len(candidate)
    win_rates: list[float] = []
    deltas: list[float] = []
    for _ in range(iterations):
        indices = [rng.randrange(unit_count) for _ in range(unit_count)]
        resampled_candidate = [candidate[index] for index in indices]
        resampled_comparator = [comparator[index] for index in indices]
        win_rates.append(_paired_win_rate(resampled_candidate, resampled_comparator))
        deltas.append(
            fmean(
                candidate_score - comparator_score
                for candidate_score, comparator_score in zip(
                    resampled_candidate, resampled_comparator
                )
            )
        )
    observed_delta = fmean(
        candidate_score - comparator_score
        for candidate_score, comparator_score in zip(candidate, comparator)
    )
    return {
        "unit_count": unit_count,
        "win_rate": _round(_paired_win_rate(candidate, comparator)),
        "win_rate_ci_95": {
            "lower": _round(_percentile(win_rates, 0.025)),
            "upper": _round(_percentile(win_rates, 0.975)),
        },
        "mean_composite_delta": _round(observed_delta),
        "mean_composite_delta_ci_95": {
            "lower": _round(_percentile(deltas, 0.025)),
            "upper": _round(_percentile(deltas, 0.975)),
        },
    }


def evaluate_superiority(
    *,
    win_rate: float,
    win_rate_ci_lower: float,
    candidate_hard_gate_pass_rate: float,
    candidate_editability: float,
    comparator_editability: float,
    candidate_failure_rate: float,
    comparator_failure_rate: float,
) -> dict[str, Any]:
    """Apply the frozen conjunctive superiority rule without relaxing boundaries."""

    editability_delta = candidate_editability - comparator_editability
    failure_rate_delta = candidate_failure_rate - comparator_failure_rate
    conditions = {
        "win_rate_gt_0_60": win_rate > CLAIM_WIN_RATE,
        "win_rate_ci_lower_gt_0_55": win_rate_ci_lower > CLAIM_CI_LOWER,
        "hard_gate_pass_rate_gte_0_95": (
            candidate_hard_gate_pass_rate >= CLAIM_HARD_GATE_PASS_RATE
        ),
        "editability_noninferior_within_0_05": (
            editability_delta >= -NONINFERIORITY_MARGIN
        ),
        "failure_noninferior_within_0_05": (
            failure_rate_delta <= NONINFERIORITY_MARGIN
        ),
    }
    return {
        "conditions": conditions,
        "editability_delta": _round(editability_delta),
        "failure_rate_delta": _round(failure_rate_delta),
        "superiority_claim": all(conditions.values()),
    }


def _reverse_bootstrap(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "unit_count": result["unit_count"],
        "win_rate": _round(1.0 - result["win_rate"]),
        "win_rate_ci_95": {
            "lower": _round(1.0 - result["win_rate_ci_95"]["upper"]),
            "upper": _round(1.0 - result["win_rate_ci_95"]["lower"]),
        },
        "mean_composite_delta": _round(-result["mean_composite_delta"]),
        "mean_composite_delta_ci_95": {
            "lower": _round(-result["mean_composite_delta_ci_95"]["upper"]),
            "upper": _round(-result["mean_composite_delta_ci_95"]["lower"]),
        },
    }


def analyze_benchmark(
    *,
    manifest: Mapping[str, Any],
    store: str | Path,
    normalized_scores: Mapping[str, Any],
    bootstrap_iterations: int = 10000,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    """Analyze complete paired records and emit threshold-gated pairwise claims."""

    validate_manifest(manifest)
    validate_normalized_scores(normalized_scores)
    if normalized_scores["manifest_sha256"] != manifest["manifest_sha256"]:
        raise BenchmarkError("normalized scores manifest does not match the frozen manifest")
    records = load_run_records(manifest=manifest, store=store, require_complete=True)
    expected_keys = expected_run_keys(manifest)
    reviewer_ids = [item["reviewer_id"] for item in normalized_scores["reviewers"]]
    expected_score_keys = {
        (reviewer_id, prompt_id, seed, arm_id)
        for reviewer_id in reviewer_ids
        for prompt_id, seed, arm_id in expected_keys
    }
    score_rows: dict[tuple[str, str, int, str], Mapping[str, Any]] = {}
    for row in normalized_scores["scores"]:
        key = (row["reviewer_id"], row["prompt_id"], row["seed"], row["arm_id"])
        if key not in expected_score_keys:
            raise BenchmarkError(f"normalized scores contain out-of-manifest row {key}")
        score_rows[key] = row
    missing_scores = sorted(expected_score_keys - set(score_rows))
    if missing_scores:
        raise BenchmarkError(
            f"normalized scores are incomplete; missing {len(missing_scores)} rows"
        )

    run_scores: dict[tuple[str, int, str], dict[str, float]] = {}
    for prompt_id, seed, arm_id in sorted(expected_keys):
        rows = [
            score_rows[(reviewer_id, prompt_id, seed, arm_id)]
            for reviewer_id in reviewer_ids
        ]
        dimension_means = {
            dimension: _round(fmean(row["dimensions"][dimension] for row in rows))
            for dimension in SCORE_DIMENSIONS
        }
        run_scores[(prompt_id, seed, arm_id)] = {
            **dimension_means,
            "composite": _round(fmean(row["composite"] for row in rows)),
        }

    arm_metrics: dict[str, dict[str, float]] = {}
    for arm_id in ARM_IDS:
        arm_runs = [key for key in sorted(expected_keys) if key[2] == arm_id]
        gate_pass_rate = fmean(
            1.0 if records[key]["hard_gate_pass"] else 0.0 for key in arm_runs
        )
        arm_metrics[arm_id] = {
            "Content": _round(fmean(run_scores[key]["Content"] for key in arm_runs) / 100),
            "Aesthetics": _round(
                fmean(run_scores[key]["Aesthetics"] for key in arm_runs) / 100
            ),
            "Editability": _round(
                fmean(run_scores[key]["Editability"] for key in arm_runs) / 100
            ),
            "composite": _round(
                fmean(run_scores[key]["composite"] for key in arm_runs) / 100
            ),
            "hard_gate_pass_rate": _round(gate_pass_rate),
            "failure_rate": _round(1.0 - gate_pass_rate),
        }

    paired_units = sorted({(prompt_id, seed) for prompt_id, seed, _ in expected_keys})
    pairwise: list[dict[str, Any]] = []
    for first_arm, second_arm in itertools.combinations(ARM_IDS, 2):
        first_scores = [
            run_scores[(prompt_id, seed, first_arm)]["composite"]
            for prompt_id, seed in paired_units
        ]
        second_scores = [
            run_scores[(prompt_id, seed, second_arm)]["composite"]
            for prompt_id, seed in paired_units
        ]
        pair_seed = _hash_seed(
            "deck-benchmark-bootstrap",
            manifest["manifest_sha256"],
            bootstrap_seed,
            first_arm,
            second_arm,
        )
        first_result = bootstrap_pairwise(
            first_scores,
            second_scores,
            iterations=bootstrap_iterations,
            seed=pair_seed,
        )
        directions = (
            (first_arm, second_arm, first_result),
            (second_arm, first_arm, _reverse_bootstrap(first_result)),
        )
        for candidate, comparator, bootstrap in directions:
            claim = evaluate_superiority(
                win_rate=bootstrap["win_rate"],
                win_rate_ci_lower=bootstrap["win_rate_ci_95"]["lower"],
                candidate_hard_gate_pass_rate=arm_metrics[candidate][
                    "hard_gate_pass_rate"
                ],
                candidate_editability=arm_metrics[candidate]["Editability"],
                comparator_editability=arm_metrics[comparator]["Editability"],
                candidate_failure_rate=arm_metrics[candidate]["failure_rate"],
                comparator_failure_rate=arm_metrics[comparator]["failure_rate"],
            )
            pairwise.append(
                {
                    "candidate": candidate,
                    "comparator": comparator,
                    **bootstrap,
                    **claim,
                }
            )
    pairwise.sort(key=lambda item: (item["candidate"], item["comparator"]))

    report: dict[str, Any] = {
        "schema_version": REPORT_VERSION,
        "manifest_sha256": manifest["manifest_sha256"],
        "scores_sha256": normalized_scores["scores_sha256"],
        "denominator": {
            "prompt_count": len(manifest["prompts"]),
            "seeds_per_prompt": 3,
            "paired_units": len(paired_units),
            "artifact_runs": len(records),
            "reviewer_count": len(reviewer_ids),
            "arms": list(ARM_IDS),
        },
        "bootstrap": {
            "iterations": bootstrap_iterations,
            "seed": bootstrap_seed,
            "resampling_unit": "prompt-seed",
            "confidence_level": 0.95,
        },
        "claim_rule": {
            "win_rate": ">0.60",
            "win_rate_ci_lower": ">0.55",
            "candidate_hard_gate_pass_rate": ">=0.95",
            "editability_noninferiority_margin": 0.05,
            "failure_noninferiority_margin": 0.05,
            "conjunctive": True,
        },
        "arm_metrics": arm_metrics,
        "pairwise": pairwise,
    }
    report["report_sha256"] = _payload_hash(report, "report_sha256")
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze_parser = subparsers.add_parser(
        "freeze-manifest", help="validate and hash a hidden prompt manifest"
    )
    freeze_parser.add_argument("input", help="draft manifest JSON")
    freeze_parser.add_argument("--output", "-o", required=True)

    validate_parser = subparsers.add_parser(
        "validate-manifest", help="validate a frozen hidden manifest"
    )
    validate_parser.add_argument("manifest")

    ingest_parser = subparsers.add_parser(
        "ingest-artifact", help="ingest one externally generated PPTX and gate record"
    )
    ingest_parser.add_argument("--manifest", required=True)
    ingest_parser.add_argument("--submission", required=True)
    ingest_parser.add_argument("--artifact", required=True)
    ingest_parser.add_argument("--store", required=True)

    failure_parser = subparsers.add_parser(
        "record-failure", help="record a run that produced no reviewable PPTX"
    )
    failure_parser.add_argument("--manifest", required=True)
    failure_parser.add_argument("--submission", required=True)
    failure_parser.add_argument("--store", required=True)

    packet_parser = subparsers.add_parser(
        "build-review-packet", help="build a blinded packet and separate private key"
    )
    packet_parser.add_argument("--manifest", required=True)
    packet_parser.add_argument("--store", required=True)
    packet_parser.add_argument("--output-dir", required=True)
    packet_parser.add_argument("--key-output", required=True)
    packet_parser.add_argument("--randomization-seed", required=True, type=int)

    scores_parser = subparsers.add_parser(
        "ingest-scores", help="validate complete blinded score sheets and unblind privately"
    )
    scores_parser.add_argument("--packet", required=True)
    scores_parser.add_argument("--key", required=True)
    scores_parser.add_argument("--score", action="append", required=True)
    scores_parser.add_argument("--output", "-o", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze", help="analyze paired scores with deterministic bootstrap intervals"
    )
    analyze_parser.add_argument("--manifest", required=True)
    analyze_parser.add_argument("--store", required=True)
    analyze_parser.add_argument("--scores", required=True)
    analyze_parser.add_argument("--output", "-o", required=True)
    analyze_parser.add_argument("--bootstrap-iterations", type=int, default=10000)
    analyze_parser.add_argument("--bootstrap-seed", type=int, default=0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "freeze-manifest":
            frozen = freeze_manifest(_load_json(args.input))
            _write_json(args.output, frozen)
            print(f"frozen {frozen['manifest_sha256']} {args.output}")
            return 0
        if args.command == "validate-manifest":
            manifest = load_manifest(args.manifest)
            print(f"valid {manifest['manifest_sha256']}")
            return 0
        if args.command == "ingest-artifact":
            record = ingest_artifact(
                manifest=load_manifest(args.manifest),
                submission=_load_json(args.submission),
                artifact_path=args.artifact,
                store=args.store,
            )
            print(f"ingested {record['run_id']} {record['record_sha256']}")
            return 0
        if args.command == "record-failure":
            record = ingest_failure(
                manifest=load_manifest(args.manifest),
                submission=_load_json(args.submission),
                store=args.store,
            )
            print(f"recorded-failure {record['run_id']} {record['record_sha256']}")
            return 0
        if args.command == "build-review-packet":
            packet, _ = build_review_packet(
                manifest=load_manifest(args.manifest),
                store=args.store,
                output_dir=args.output_dir,
                key_output=args.key_output,
                randomization_seed=args.randomization_seed,
            )
            print(f"packet {packet['packet_sha256']} {args.output_dir}")
            return 0
        if args.command == "ingest-scores":
            packet = _load_json(args.packet)
            blind_key = _load_json(args.key)
            sheets: list[tuple[Mapping[str, Any], str]] = []
            for score_path_text in args.score:
                score_path = Path(score_path_text)
                sheets.append((_load_json(score_path), _file_sha256(score_path)))
            normalized = ingest_scores(
                packet=packet,
                blind_key=blind_key,
                score_sheets=sheets,
            )
            _write_json(args.output, normalized)
            print(f"scores {normalized['scores_sha256']} {args.output}")
            return 0
        if args.command == "analyze":
            report = analyze_benchmark(
                manifest=load_manifest(args.manifest),
                store=args.store,
                normalized_scores=_load_json(args.scores),
                bootstrap_iterations=args.bootstrap_iterations,
                bootstrap_seed=args.bootstrap_seed,
            )
            _write_json(args.output, report)
            print(f"report {report['report_sha256']} {args.output}")
            return 0
    except (BenchmarkError, OSError) as exc:
        print(f"deck_benchmark: {exc}", file=sys.stderr)
        return 2
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
