# v0.2.0 Release Notes

## Summary

This release adds a descriptor-first style-reference layer for richer,
reproducible PowerPoint generation. The skill now gives agents a browseable
design-memory path instead of relying only on preset colors, headings, and
borders.

## What Changed

- Added a descriptor-only inspiration corpus for public design systems,
  presentation tooling, template indexes, and slide-design heuristics.
- Added corpus validation with rights posture, allowed extraction modes,
  forbidden materials, preset routes, and subagent safety rules.
- Extended the style/content router prompt so a scout can use corpus routes,
  selected source descriptors, and preset contact-sheet use cases before
  locking a design contract.
- Added per-preset contact-sheet collections for all 13 presets:
  `overview`, `data_evidence`, and `decision_sources`.
- Extended release evidence so rendered gallery checks fail if a preset is
  missing its contact-sheet collection or expected treatment thumbnails.
- Added compact release evidence for browseable style comparison without
  bundling external decks, screenshots, logos, proprietary text, or copied
  slide geometry.

## Evidence

- Presets covered: 13
- Per-preset contact sheets: 39
- Global/treatment contact sheets: 11
- Required per-preset use cases: `overview`, `data_evidence`,
  `decision_sources`
- Release evidence gate: passed
- Render-free QA totals: 0 overflow, 0 overlap, 0 design warnings,
  0 visual warnings, 0 placeholder hits

## Validation

- `python3 scripts/style_inspiration_corpus.py --validate`
- `npm run check:style-corpus`
- `npm run check:style-router`
- `npm run check:style-reference-gallery`
- `npm run check:style-reference-release`
- `npm run check:python`
- `npm run check:focused -- --jobs 4`
- `git diff --check`
