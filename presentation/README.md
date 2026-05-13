# Presentation deck — NEM 2026 workshop

Source-of-truth for the 4-hour workshop slide deck. Built programmatically with
`python-pptx` so the deck stays in sync with `docs/instructor.md`.

## Build

```fish
cd presentation
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build_deck.py
```

Output: `NEM2026_workshop.pptx` in this directory. Open in PowerPoint, Keynote,
LibreOffice Impress, or upload to Google Slides.

## Editing

Edit `build_deck.py` and re-run. Slide content is authored as a list of
slide-builder calls in `build_slides()`. Theme colors / fonts are in the
`Theme` block at the top of the file.

The deck is regenerated from scratch on every run — do not edit the `.pptx`
directly if you want changes to survive a rebuild.

## Source material

Slide content and speaker notes are condensed from:

- `docs/instructor.md` — live tour script (primary source)
- `docs/workshop/change-requests.md` — CR specs and per-stage handling
- `docs/workshop/scoreboard.md` — diff numbers
- `docs/workshop/overview.md` — schedule and audience framing

These live on the `main` branch; the presentation tooling is on whichever
branch you build from. To regenerate against the latest instructor script,
pull `main` first.
