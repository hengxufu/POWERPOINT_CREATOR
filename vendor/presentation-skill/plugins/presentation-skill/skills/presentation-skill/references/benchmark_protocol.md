# Deck Benchmark Protocol

This protocol defines an offline, same-denominator foundation for comparing:

1. `codex_native`: native Codex presentation generation.
2. `claude_code`: Claude Code-style presentation generation.
3. `presentation_skill`: this repository's presentation skill.

The harness ingests artifacts. It does not execute, emulate, or claim to have executed any generator. Generator runs happen outside the harness and must be documented in each submission record.

## Integrity Model

The benchmark has four private/public boundaries:

- The frozen prompt manifest is private until all generation runs are complete.
- Run records and hard-gate evidence are private to the benchmark operator.
- The review packet is public to reviewers and contains only randomized `Option A`, `Option B`, and `Option C` labels.
- The blind key and normalized scores are private until review is locked.

Every prompt has exactly three unique integer seeds. The denominator is therefore:

`prompt count x 3 seeds x 3 arms`

No failed run is removed. A failed hard gate remains in the denominator and contributes to the arm's failure rate. Reviewers score every packet entry. If a deck cannot be opened or evaluated, the affected dimensions receive `0`; the run is not silently omitted.

## Frozen Manifest

Create a draft JSON with the following shape:

```json
{
  "schema_version": "deck-benchmark-manifest/v1",
  "benchmark_id": "deck-benchmark-2026q3",
  "arms": [
    {"arm_id": "codex_native", "display_name": "Native Codex"},
    {"arm_id": "claude_code", "display_name": "Claude Code style"},
    {"arm_id": "presentation_skill", "display_name": "Repository skill"}
  ],
  "prompts": [
    {
      "prompt_id": "clinic-capacity-brief",
      "topic": "Clinic capacity planning",
      "content": "Create an eight-slide decision deck for the operating committee.",
      "constraints": {
        "content": [
          "State the requested decision on slide one.",
          "Include owners, timing, risks, and next steps."
        ],
        "evidence": [
          "Use only the supplied capacity table.",
          "Cite every quantitative claim on-slide."
        ],
        "assets": [
          "Use the supplied floor-plan image once.",
          "Do not fetch replacement assets."
        ]
      },
      "seeds": [1041, 2077, 4099]
    }
  ]
}
```

Prompt content and constraints must be arm-neutral. The validator rejects canonical arm IDs or display names in reviewer-visible prompt material.

Freeze the manifest before any arm receives a prompt:

```bash
python3 scripts/deck_benchmark.py freeze-manifest \
  private/manifest-draft.json \
  --output private/manifest.json

python3 scripts/deck_benchmark.py validate-manifest private/manifest.json
```

Freezing adds `visibility: hidden`, `frozen: true`, and `manifest_sha256`. Any later change invalidates the hash. Do not publish the manifest before generation is locked.

## External Runs And Ingestion

Give every arm the same prompt content, evidence bundle, asset bundle, seed, attempt count, and resource/time policy. Record model/runtime versions and commands outside the harness. Seed support differs across systems; when a system cannot consume a seed directly, use the seed to deterministically select a predeclared run configuration and document that mapping before execution.

For each external run, create a submission record:

```json
{
  "schema_version": "deck-benchmark-submission/v1",
  "manifest_sha256": "<64 lowercase hex characters>",
  "prompt_id": "clinic-capacity-brief",
  "seed": 1041,
  "arm_id": "codex_native",
  "provenance": {
    "mode": "external-artifact-ingestion",
    "generator_executed_by_harness": false,
    "submitted_by": "benchmark-operator-01",
    "source_run_id": "native-2026q3-clinic-1041"
  },
  "blinding_attestation": {
    "self_identifying_content": false,
    "assessor": "blind-checker-01",
    "evidence": [
      "Visible slides, filenames, notes, and package metadata were checked for arm identity."
    ]
  },
  "hard_gates": {
    "layout": {
      "status": "pass",
      "assessor": "qa-01",
      "evidence": ["Rendered slide audit: private/evidence/native-clinic-1041-layout.json"]
    },
    "readability": {
      "status": "pass",
      "assessor": "qa-01",
      "evidence": ["Readability audit: private/evidence/native-clinic-1041-readability.json"]
    },
    "placeholders": {
      "status": "pass",
      "assessor": "qa-01",
      "evidence": ["Placeholder search returned zero unresolved items."]
    },
    "editability": {
      "status": "pass",
      "assessor": "qa-02",
      "evidence": ["Object edit audit: private/evidence/native-clinic-1041-editability.json"]
    },
    "reproducibility": {
      "status": "pass",
      "assessor": "qa-02",
      "evidence": ["Independent rerun receipt: private/evidence/native-clinic-1041-rerun.json"]
    }
  }
}
```

Gate records are mandatory and binary:

- **Layout:** rendered slides have no severe overlap, clipping, off-canvas content, or broken geometry.
- **Readability:** text is legible at the review size, contrast is adequate, and reading order is coherent.
- **Placeholders:** no unresolved template text, TODO markers, empty required frames, or fake citations remain.
- **Editability:** the PPTX opens and required text/data objects remain natively editable; flattening is limited to intentional image assets.
- **Reproducibility:** a second execution from the recorded inputs and environment completes and satisfies the artifact contract. Byte-identical PPTX output is not required unless preregistered.

Evidence strings should identify immutable local receipts or concrete observations. A bare assertion such as `looks good` is not adequate benchmark evidence even though the harness can only enforce that evidence is present.

Ingest the external PPTX:

```bash
python3 scripts/deck_benchmark.py ingest-artifact \
  --manifest private/manifest.json \
  --submission private/submissions/native-clinic-1041.json \
  --artifact external-runs/native-clinic-1041.pptx \
  --store private/benchmark-store
```

The harness validates the PPTX package, copies the exact bytes into the store, hashes the artifact, and writes a self-hashed run record. A conflicting re-ingestion is rejected. It never calls a generator or accesses the network.

If a run times out, refuses, crashes, exports an invalid package, or otherwise
produces no reviewable PPTX, record that outcome instead of omitting or
rerunning it. Add this typed object to the normal submission record and mark
all five hard gates `fail`:

```json
"failure": {
  "kind": "timeout",
  "stage": "generation",
  "summary": "The run exceeded the preregistered time limit.",
  "evidence": ["External receipt recorded exit status 124 after 900 seconds."]
}
```

Allowed kinds are `timeout`, `no_artifact`, `tool_error`, `refused`,
`invalid_artifact`, and `other`. Allowed stages are `generation`, `render`,
`export`, `validation`, and `unknown`.

```bash
python3 scripts/deck_benchmark.py record-failure \
  --manifest private/manifest.json \
  --submission private/submissions/native-clinic-1041.json \
  --store private/benchmark-store
```

Packet construction replaces a missing artifact with one deterministic,
arm-neutral slide stating that no deck was produced. The reviewer instruction
on that slide is to score unavailable dimensions as `0`; the private run
record retains the typed failure and all gate evidence.

## Blinded Review

Packet construction is allowed only when the full prompt/seed/arm matrix is present and hash-valid:

```bash
python3 scripts/deck_benchmark.py build-review-packet \
  --manifest private/manifest.json \
  --store private/benchmark-store \
  --output-dir review/public-packet \
  --key-output private/blind-key.json \
  --randomization-seed 55031
```

The randomization seed must be fixed before review. Arm-to-label assignment is independently shuffled for each prompt/seed case. The public directory contains `packet.json` and artifact copies named only by case and blind label. The private key must be outside that directory.

The harness does not rewrite PPTX internals because rewriting would change the evaluated artifact. The required blinding attestation covers visible branding, speaker notes, author/producer metadata, embedded filenames, and other self-identifying content.

Reviewers must not receive the manifest, run records, gate outcomes, or blind key. Each reviewer returns one complete score sheet:

```json
{
  "schema_version": "deck-benchmark-score-sheet/v1",
  "packet_sha256": "<packet hash from packet.json>",
  "reviewer_id": "reviewer-07",
  "blinded": true,
  "scores": [
    {
      "case_id": "case-0123456789ab",
      "blind_label": "Option A",
      "dimensions": {
        "Content": 82,
        "Aesthetics": 76,
        "Editability": 88
      },
      "comment": "Decision and evidence are clear; two dense slides reduce scanability."
    }
  ]
}
```

Scores use a `0` to `100` scale. The three frozen dimensions are exact and equally weighted:

- **Content:** task completion, correctness, evidence use, and narrative quality.
- **Aesthetics:** composition, hierarchy, visual coherence, and professional finish.
- **Editability:** practical ability to revise text, data, structure, and visual objects in the delivered PPTX.

Every score sheet must contain exactly one row for every case/label pair. Partial, duplicate, mismatched, or `blinded: false` sheets are rejected.

```bash
python3 scripts/deck_benchmark.py ingest-scores \
  --packet review/public-packet/packet.json \
  --key private/blind-key.json \
  --score private/scores/reviewer-01.json \
  --score private/scores/reviewer-02.json \
  --output private/normalized-scores.json
```

## Analysis And Claim Gate

```bash
python3 scripts/deck_benchmark.py analyze \
  --manifest private/manifest.json \
  --store private/benchmark-store \
  --scores private/normalized-scores.json \
  --bootstrap-iterations 10000 \
  --bootstrap-seed 8819 \
  --output private/report.json
```

Reviewer scores are averaged within each artifact first. The statistical unit is the paired `prompt + seed`, not an individual reviewer score. This prevents reviewer count from inflating the sample size.

For every ordered arm pair, the report includes:

- Composite win rate, with ties worth `0.5`.
- Paired bootstrap 95% confidence interval for win rate.
- Mean composite-score difference and paired bootstrap 95% confidence interval.
- Candidate hard-gate pass rate and failure rate.
- Editability and failure-rate noninferiority checks.

Bootstrap resampling is deterministic and samples complete prompt/seed units with replacement. Reverse pair directions are exact transformations of the same bootstrap draws.

`superiority_claim` is `true` only when all conditions hold:

1. Win rate is strictly greater than `0.60`.
2. The lower 95% win-rate confidence bound is strictly greater than `0.55`.
3. Candidate hard-gate pass rate is at least `0.95`.
4. Candidate mean Editability is no more than `0.05` below the comparator.
5. Candidate failure rate is no more than `0.05` above the comparator.

The rule is conjunctive and the strict boundaries are not rounded upward. Failure rate is `1 - hard_gate_pass_rate`, where a run passes only if all five hard gates pass.

The report emits six ordered pairwise results. Its intervals are not adjusted for multiple comparisons. Predeclare primary contrasts or apply an appropriate multiplicity procedure before inferential use beyond this benchmark. A `superiority_claim` field is an internal benchmark result, not a release, production, marketing, or general quality claim.

## Determinism Checklist

- Freeze the manifest and record its SHA-256 before generation.
- Use exactly three preregistered seeds per prompt and all three arms.
- Keep generator execution external and retain source-run receipts.
- Use the same evidence/assets and resource policy for every arm.
- Ingest exact PPTX bytes; never replace a failed artifact with a later attempt.
- Lock the packet randomization seed before review.
- Keep the blind key outside the public packet directory.
- Require complete score sheets from every included reviewer.
- Lock bootstrap seed and iteration count before analysis.
- Retain all failed hard gates in the denominator.
