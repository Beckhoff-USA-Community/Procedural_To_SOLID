# Presentation deck — NEM 2026 workshop

The committed `NEM2026_workshop.pdf` (2.1 MB) is the deck that gets projected during the workshop. It's exported from a `.pptx` editing surface that is **not** tracked in git — see *Editing the deck* below.

## Why PDF is the committed deliverable

- **PowerPoint `.pptx`** is a zipped XML blob: doesn't diff, doesn't merge usefully, bloats git history (7+ MB per commit), and risks editor lock-file leakage.
- **PDF** is a stable rendering of the final slides — what auditors and attendees see — at ~30 % the size of the source `.pptx`.
- The PDF is the cross-platform projection artifact (PowerPoint, Keynote, Acrobat, browser PDF viewer all render it identically).

So the canonical workshop deck in this repo is the PDF. The editable PPTX lives outside git.

## Editing the deck

1. **Get the editable `.pptx`** from the person who last edited it (DM, shared drive, USB, etc.). The PPTX is intentionally not tracked — coordinate sharing out-of-band.
2. **Open in PowerPoint, Keynote, or LibreOffice Impress** and make your edits.
3. **Export to PDF** via `File → Export → Create PDF/XPS` (PowerPoint) or `File → Export As → PDF` (Keynote). Save as `presentation/NEM2026_workshop.pdf`, overwriting the committed file.
4. **Commit the PDF** alone. The local `.pptx` stays untracked (it matches the `*.pptx` rule in `presentation/.gitignore`).
5. **Hand the latest `.pptx` off** to the next editor — same out-of-band channel.

Caveat: binary `.pptx` files don't diff or merge usefully in git — that's why we kept them out. Coordinate edits so two people don't fork the deck in parallel; whoever holds the latest `.pptx` is the editing baseline.

## Regenerating from scratch (`build_deck.py`) — DIVERGED

`build_deck.py` was originally the source-of-truth: the deck was generated end-to-end from the Python script, which knew how to compose every slide, speaker note, branch reference, and Beckhoff theme color. A collaborator (Lauren) then **edited the `.pptx` directly** to add substantial new content; the script has had its branch references updated to the current `Release` layout but has not been brought into line with the hand-edited slides.

Running `build_deck.py` right now would produce a `.pptx` that's missing Lauren's hand-edits — projected, it would look like a stale, mostly-blank-by-comparison version of the real deck.

So:

- **If you have the latest editable `.pptx`** (from the previous editor) — ignore `build_deck.py`, edit the PPTX directly, export PDF, commit.
- **If you don't have the `.pptx` and need one urgently** — `build_deck.py` will produce a starting point you can layer Lauren's content into, but expect the divergence reconciliation to be a multi-hour task.

```fish
cd presentation
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build_deck.py    # writes NEM2026_workshop.pptx (gitignored)
```

The script builds on top of the Beckhoff SPT template at `../SPT Framework_03_16_23.pptx`, inheriting its slide masters, layouts, theme colors ("Test_Beckhoff_2020_v2"), and chrome. Slide content is authored as `add_*_slide()` calls inside `build_slides()`; the `Theme` block at the top holds colors / fonts.

## Source material for the deck content

Slide content and speaker notes were originally condensed from these docs (still the right reference today for context, even if individual slides have drifted in Lauren's hand-edited version):

- `docs/instructor.md` — live tour script (primary source)
- `docs/workshop/change-requests.md` — CR specs and per-PLC handling
- `docs/workshop/scoreboard.md` — diff numbers
- `docs/workshop/overview.md` — schedule and audience framing

These live on the `Release` branch; the presentation tooling lives alongside on whichever branch you build from.

## Reconciliation plan (when picked up)

If someone wants to bring `build_deck.py` back into line with Lauren's hand-edits so the script can regenerate the canonical deck:

1. Use `python-pptx` to enumerate Lauren's slides in the latest editable `.pptx` — title, body text, notes, layout — and dump to a structured intermediate form (JSON or YAML).
2. Diff against what `build_deck.py`'s `build_slides()` would produce.
3. For each meaningful change Lauren made:
   - New slide → add an `add_*_slide()` call in the right block.
   - Edited content → update the matching `add_*_slide()` arguments.
   - Reordered slides → reorder the calls.
   - Theme/layout overrides → port into the `Theme` block or layout helpers.
4. Run `build_deck.py` against a temp output (`--output some_other.pptx`) and diff slide-by-slide against Lauren's `.pptx`.
5. Once they match, export both to PDF and check parity. Then the script can be the regenerator again — its output becomes the committed PDF on each rebuild.

This is a multi-hour task. Track it as a separate engagement.
