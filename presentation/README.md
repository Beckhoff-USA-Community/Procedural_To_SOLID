# Presentation deck — NEM 2026 workshop

The committed `NEM2026_workshop.pptx` (7.91 MB) is the deck used to deliver the workshop. As of 2026-05-21 it has been **hand-edited in PowerPoint / LibreOffice Impress** and DOES NOT match what `build_deck.py` would regenerate.

## Current state — DO NOT regenerate without reconciling first

`build_deck.py` was originally the source-of-truth (the deck was generated from the script). A collaborator (Lauren) subsequently edited the `.pptx` directly to add substantial new content; the script has since had its branch references updated to the new `Release` layout but has NOT been brought into line with the hand-edited slides.

Running `build_deck.py` right now would **overwrite the committed 7.91 MB deck** with a stale ~2.58 MB regeneration.

The reconciliation work (read Lauren's slides, port the diff back into `build_deck.py`, then regenerate) hasn't been done. Until it has, treat:

- **The committed `.pptx`** as the source-of-truth for what gets projected.
- **`build_deck.py`** as a structural reference + presenter-notes archive that needs reconciliation work before the next regenerate.

## Hand-edit workflow (current)

1. Open `NEM2026_workshop.pptx` in PowerPoint, Keynote, LibreOffice Impress, or Google Slides.
2. Edit slides directly.
3. Save and commit the .pptx as a binary blob.

Caveat: binary `.pptx` files don't diff or merge usefully in git. Coordinate edits among collaborators so two people don't edit the same deck in parallel. The `.~lock.*#` editor lock files are now gitignored (added 2026-05-21) so they no longer leak into commits.

## Script-driven workflow (paused)

Originally documented as:

```fish
cd presentation
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build_deck.py    # regenerates NEM2026_workshop.pptx
```

The script builds on top of the Beckhoff SPT template at `../SPT Framework_03_16_23.pptx`, inheriting its slide masters, layouts, theme colors ("Test_Beckhoff_2020_v2"), and chrome. Slide content is authored as `add_*_slide()` calls inside `build_slides()`; the `Theme` block at the top holds colors / fonts.

When reconciliation lands, the script's branch references (already updated 2026-05-21 to `Release` / `cr1-applied` / `cr2-applied` / `cr3-applied` / `complete` and the per-PLC `git diff Release...crN-applied -- NEM2026/FillingLine_<Stage>/` form) will be the right starting point.

## Source material for the deck content

Slide content and speaker notes were originally condensed from these docs (still the right reference today for context, even if individual slides have drifted in Lauren's hand-edited version):

- `docs/instructor.md` — live tour script (primary source)
- `docs/workshop/change-requests.md` — CR specs and per-PLC handling
- `docs/workshop/scoreboard.md` — diff numbers
- `docs/workshop/overview.md` — schedule and audience framing

These live on the `Release` branch; the presentation tooling lives alongside on whichever branch you build from.

## Reconciliation plan (when picked up)

1. Use `python-pptx` to enumerate Lauren's slides — title, body text, notes, layout — and dump to a structured intermediate form (JSON or YAML).
2. Diff against what `build_deck.py`'s `build_slides()` would produce.
3. For each meaningful change Lauren made:
   - New slide → add an `add_*_slide()` call in the right block.
   - Edited content → update the matching `add_*_slide()` arguments.
   - Reordered slides → reorder the calls.
   - Theme/layout overrides → port into the `Theme` block or layout helpers.
4. Run `build_deck.py` against a temp output (`--output some_other.pptx`) and diff slide-by-slide against Lauren's.
5. Once they match, replace the committed `.pptx`.

This is a multi-hour task. Track it as a separate engagement.
