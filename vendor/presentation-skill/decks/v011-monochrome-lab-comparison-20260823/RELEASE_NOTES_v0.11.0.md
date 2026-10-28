# v0.11.0 - Monochrome scientific range and a faster first pass

This release focuses on scientific decks that should feel designed without
looking decorated. It adds two opt-in white-page systems: a compact assay
notebook and a more open journal appendix. Both keep color subordinate to the
evidence and preserve editable charts, tables, text, and diagrams.

## What changed

- Added `lab_monochrome_v1` and `journal_monochrome_v1` palette systems.
- Made each model-selected route carry its own story sequence instead of
  inheriting the first candidate's sequence.
- Made the authoring prompt, preflight, and renderer share one v2 role/variant
  capability contract.
- Added a distinct 13 pt support/subtitle readability tier.
- Removed table readouts inferred from row order; analytical takeaways must be
  explicit in source.
- Removed empty title-stage panels unless the outline supplies content or an
  asset for them.
- Added stage timing to quick-deck receipts and a read-only plugin parity check.

## Release proof

The proof uses one frozen 12-slide synthesis of three recent primary studies on
rapid nanopore long-read genome sequencing in pediatric critical care. The
content, metrics, and sources are identical across both decks; only the design
system changes.

- `rapid_lrgs_assay_notebook.pptx`
- `rapid_lrgs_journal_appendix.pptx`
- `rapid_lrgs_monochrome_ab_contact_sheet.jpg`
- `outline_content.json` and the two resolved outlines

On the development machine, the complete build, render, and validation pass
took 4.9 seconds for the assay notebook and 3.9 seconds for the journal
appendix after the source outline was complete.
