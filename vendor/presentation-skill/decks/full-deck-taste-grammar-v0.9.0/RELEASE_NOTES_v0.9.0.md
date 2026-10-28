# presentation-skill v0.9.0

v0.9 moves composition grammar from title treatment into the full deck.
Evidence, comparison, chart, table, decision, and references slides now resolve
through the same grammar contract as covers and section turns.

## What changed

- Added `renderer_role_contracts_v2`: eight color-independent structural
  systems for each of eight slide roles.
- Added a declarative role-layout compiler with normalized semantic slots and
  bounded `primary`, `alternate`, and `dense` slide overrides.
- Kept text, charts, tables, figures, and diagrams editable in PowerPoint.
- Made new workspaces persist and apply v2 through deck start, design contract,
  style routing, outline authoring, and workspace build.
- Kept v1-only workspaces pinned until the explicit, idempotent migration
  command is run.
- Replaced readiness-report command execution with a typed action registry that
  validates operations, flags, and workspace-contained paths.

## See it

- [Narrative structures](https://github.com/siril9/presentation-skill/releases/download/v0.9.0/v0.9_narrative_structures.jpg)
- [Evidence and data structures](https://github.com/siril9/presentation-skill/releases/download/v0.9.0/v0.9_evidence_data_structures.jpg)
- [Decisions and sources](https://github.com/siril9/presentation-skill/releases/download/v0.9.0/v0.9_decisions_sources.jpg)
- [Editable 64-slide gallery](https://github.com/siril9/presentation-skill/releases/download/v0.9.0/v0.9_full_deck_taste_grammar_gallery.pptx)

The gallery uses one urban-heat topic across all eight grammar families so the
differences are visible without changing the subject.

## Upgrade an existing workspace

```bash
python3 scripts/upgrade_renderer_role_contracts_v2.py \
  --workspace decks/my-deck
```

Running the command again is a no-op. Workspaces without the v2 contract keep
their v1 rendering behavior.
