"""
Build the NEM 2026 workshop deck — "From Procedural to SOLID".

Builds on top of the Beckhoff SPT template (`../SPT Framework_03_16_23.pptx`),
inheriting its slide masters, layouts, theme colors ("Test_Beckhoff_2020_v2"),
and chrome.

Audience-vs-instructor split:
  • Slides carry only what should be projected — short headlines, code,
    diff stats, the audience-takeaway pushback Q&A cards, the scoreboard.
  • Speaker notes carry the live-narration script — what to say, what to
    do (set timer, walk the room, switch branch), anticipated discussion
    answers, pacing levers, and any context that used to be crowded onto
    the slide. Notes use [BRACKET] section labels so an instructor can
    scan them mid-talk.

Run:
    .venv/bin/python build_deck.py

Output:
    NEM2026_workshop.pptx (sibling of this file)

Source of truth for content: docs/instructor.md on `Release`.

----------------------------------------------------------------------
WARNING — script and committed .pptx have DIVERGED as of 2026-05-21.

The committed NEM2026_workshop.pptx (7.91 MB) contains hand-edits made
directly in PowerPoint/Impress by a collaborator (Lauren). The version
this script would currently generate (~2.58 MB before Lauren's edits)
does NOT match what's committed.

Branch references in this script have been updated to the new layout
(`Release` baseline, `cr1-applied` / `cr2-applied` / `cr3-applied` /
`complete` CR branches; three side-by-side PLC projects per branch).
But running build_deck.py right now would OVERWRITE Lauren's hand-edited
.pptx with a stale, mostly-blank-by-comparison regenerated version.

Before regenerating:
  1. Read the committed .pptx slide-by-slide (e.g. via python-pptx) to
     identify what Lauren added or changed.
  2. Port those changes back into this script's add_*_slide() calls.
  3. Diff the regenerated .pptx against Lauren's version slide-by-slide.
  4. Only then run build_deck.py to overwrite the committed .pptx.

Until that reconciliation lands, treat this script as a structural
reference + presenter-notes archive — not a regenerator.
----------------------------------------------------------------------
"""

from __future__ import annotations

import copy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt


TEMPLATE_PATH = Path(__file__).parent.parent / "SPT Framework_03_16_23.pptx"
OUTPUT_PATH = Path(__file__).parent / "NEM2026_workshop.pptx"


# ---------------------------------------------------------------------------
# Theme — Beckhoff "Test_Beckhoff_2020_v2" palette
# ---------------------------------------------------------------------------

class Theme:
    SLIDE_W = Inches(13.333)
    SLIDE_H = Inches(7.5)

    BODY_X = Inches(0.0)
    BODY_Y = Inches(1.19)
    BODY_W = Inches(11.09)
    BODY_H = Inches(5.83)
    SAFE_X = Inches(0.40)
    SAFE_W = Inches(10.30)

    BECKHOFF_BLUE = RGBColor(0x2D, 0x76, 0xAD)
    BECKHOFF_RED  = RGBColor(0xEF, 0x00, 0x00)
    DARK_RED      = RGBColor(0x77, 0x00, 0x00)
    SLATE_DARK    = RGBColor(0x41, 0x4D, 0x5C)
    SLATE         = RGBColor(0x62, 0x71, 0x86)
    SLATE_LIGHT   = RGBColor(0xB3, 0xBC, 0xC8)
    LIGHT_PANEL   = RGBColor(0xE5, 0xE8, 0xEC)
    PALE_BLUE     = RGBColor(0xB5, 0xD4, 0xEC)
    BLACK         = RGBColor(0x00, 0x00, 0x00)
    WHITE         = RGBColor(0xFF, 0xFF, 0xFF)

    CODE_PANEL_BG = RGBColor(0x1B, 0x1F, 0x23)
    CODE_FG       = RGBColor(0xE6, 0xE8, 0xEB)
    BODY_INK      = RGBColor(0x24, 0x2A, 0x33)
    MUTED_INK     = RGBColor(0x62, 0x71, 0x86)
    RULE_GRAY     = RGBColor(0xC8, 0xCE, 0xD6)

    # Semantic stage accents — preserved for back-compat with build_slides()
    # Stage progression climbs warm → neutral → brand: dark red → slate → blue.
    AMBER   = DARK_RED       # Stage 1 — procedural ("the legacy that hurts")
    TEAL    = SLATE          # Stage 2 — inheritance (the bridge)
    VIOLET  = BECKHOFF_BLUE  # Stage 3 — composition (brand climax)
    NAVY    = BLACK          # Block 0/4 + section framing
    CRIMSON = BECKHOFF_RED   # Pre-emptive pushback warnings (brighter red)

    SANS         = "Arial"
    MONO         = "Consolas"
    SERIF_ACCENT = "Georgia"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _set_solid_fill(fill, color):
    fill.solid()
    fill.fore_color.rgb = color


def set_slide_bg(slide, color):
    bg = slide.background
    _set_solid_fill(bg.fill, color)


def add_rect(slide, x, y, w, h, fill_color, line_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    _set_solid_fill(shape.fill, fill_color)
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(0.75)
    shape.shadow.inherit = False
    return shape


def add_text(
    slide,
    x, y, w, h,
    text,
    *,
    font=None,
    size=18,
    bold=False,
    italic=False,
    color=None,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    line_spacing=1.15,
):
    font = font or Theme.SANS
    color = color or Theme.BODY_INK

    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor

    lines = text.split("\n") if isinstance(text, str) else list(text)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
    return tb


def add_bullets(
    slide,
    x, y, w, h,
    items,
    *,
    size=18,
    color=None,
    bullet_color=None,
    line_spacing=1.30,
    para_space_before=4,
    bold_first_token=False,
):
    color = color or Theme.BODY_INK
    bullet_color = bullet_color or Theme.BECKHOFF_BLUE

    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = line_spacing
        if i > 0:
            p.space_before = Pt(para_space_before)

        b = p.add_run()
        b.text = "▸  "
        b.font.name = Theme.SANS
        b.font.size = Pt(size)
        b.font.bold = True
        b.font.color.rgb = bullet_color

        if bold_first_token and "—" in item:
            head, tail = item.split("—", 1)
            r1 = p.add_run()
            r1.text = head.rstrip() + " "
            r1.font.name = Theme.SANS
            r1.font.size = Pt(size)
            r1.font.bold = True
            r1.font.color.rgb = color
            r2 = p.add_run()
            r2.text = "— " + tail.lstrip()
            r2.font.name = Theme.SANS
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
        else:
            r = p.add_run()
            r.text = item
            r.font.name = Theme.SANS
            r.font.size = Pt(size)
            r.font.color.rgb = color
    return tb


def add_speaker_notes(slide, notes_text):
    nf = slide.notes_slide.notes_text_frame
    nf.clear()
    paragraphs = notes_text.strip().split("\n\n")
    for i, para in enumerate(paragraphs):
        p = nf.paragraphs[0] if i == 0 else nf.add_paragraph()
        run = p.add_run()
        run.text = para
        run.font.name = Theme.SANS
        run.font.size = Pt(12)


# ---------------------------------------------------------------------------
# Layout lookup + slide creation
# ---------------------------------------------------------------------------

_LAYOUTS = {}


def _index_layouts(prs):
    _LAYOUTS.clear()
    for layout in prs.slide_masters[0].slide_layouts:
        _LAYOUTS[layout.name.strip()] = layout


def _layout(name):
    if name not in _LAYOUTS:
        raise KeyError(f"Layout {name!r} not in template. Available: {sorted(_LAYOUTS)}")
    return _LAYOUTS[name]


def _new(prs, layout_name):
    return prs.slides.add_slide(_layout(layout_name))


def _set_placeholder_text(slide, ph_idx, text):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == ph_idx:
            ph.text_frame.text = text
            return ph
    return None


def _remove_placeholder(slide, ph_idx):
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx == ph_idx:
            sp = ph._element
            sp.getparent().remove(sp)
            return


def _set_title(slide, title):
    return _set_placeholder_text(slide, 0, title)


def _set_body(slide, items, *, bullet_color=None, size=18, bold_first_token=True):
    body = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 15:
            body = ph
            break
    if body is None:
        return None

    bullet_color = bullet_color or Theme.BECKHOFF_BLUE
    tf = body.text_frame
    tf.clear()
    tf.word_wrap = True

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = 1.30
        if i > 0:
            p.space_before = Pt(4)

        b = p.add_run()
        b.text = "▸  "
        b.font.name = Theme.SANS
        b.font.size = Pt(size)
        b.font.bold = True
        b.font.color.rgb = bullet_color

        if bold_first_token and "—" in item:
            head, tail = item.split("—", 1)
            r1 = p.add_run()
            r1.text = head.rstrip() + " "
            r1.font.name = Theme.SANS
            r1.font.size = Pt(size)
            r1.font.bold = True
            r1.font.color.rgb = Theme.BODY_INK
            r2 = p.add_run()
            r2.text = "— " + tail.lstrip()
            r2.font.name = Theme.SANS
            r2.font.size = Pt(size)
            r2.font.color.rgb = Theme.BODY_INK
        else:
            r = p.add_run()
            r.text = item
            r.font.name = Theme.SANS
            r.font.size = Pt(size)
            r.font.color.rgb = Theme.BODY_INK
    return body


# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------

def add_title_slide(prs, title, subtitle, tagline, *, accent=None, notes=""):
    accent = accent or Theme.BECKHOFF_BLUE
    slide = _new(prs, "Title with picture")
    _set_title(slide, title)

    add_text(
        slide,
        Inches(0.0), Inches(2.20), Inches(11.09), Inches(0.5),
        "NEM 2026  ·  4-hour workshop",
        size=14, bold=True, color=accent, align=PP_ALIGN.LEFT,
    )
    add_text(
        slide,
        Inches(0.0), Inches(2.85), Inches(11.09), Inches(1.1),
        subtitle,
        size=22, color=Theme.SLATE, align=PP_ALIGN.LEFT, line_spacing=1.2,
    )
    add_text(
        slide,
        Inches(0.0), Inches(6.50), Inches(11.09), Inches(0.5),
        tagline,
        size=12, color=Theme.MUTED_INK, italic=True, align=PP_ALIGN.LEFT,
    )

    add_speaker_notes(slide, notes)
    return slide


def add_section_divider(prs, block_label, title, time_budget, summary, *, accent, notes=""):
    slide = _new(prs, "Contents")
    _set_title(slide, block_label)
    _remove_placeholder(slide, 15)

    add_rect(slide, Inches(0.0), Inches(1.30), Inches(0.18), Inches(5.6), accent)

    add_text(
        slide,
        Inches(0.45), Inches(1.40), Inches(10.5), Inches(1.7),
        title,
        size=46, bold=True, color=Theme.SLATE_DARK, line_spacing=1.05,
    )

    add_text(
        slide,
        Inches(0.45), Inches(3.20), Inches(10.5), Inches(0.5),
        time_budget,
        size=18, bold=True, color=accent,
    )

    if summary:
        add_text(
            slide,
            Inches(0.45), Inches(4.10), Inches(10.5), Inches(2.5),
            summary,
            size=20, color=Theme.BODY_INK, italic=True, line_spacing=1.4,
        )

    add_speaker_notes(slide, notes)
    return slide


def add_content_slide(prs, title, bullets, *, accent, eyebrow=None, page=0, notes="", body_size=20):
    slide = _new(prs, "Text")
    _set_title(slide, title)

    if eyebrow:
        add_text(
            slide,
            Inches(0.0), Inches(0.18), Inches(11.09), Inches(0.32),
            eyebrow.upper(),
            size=10, bold=True, color=accent,
        )

    _set_body(slide, bullets, bullet_color=accent, size=body_size)

    add_speaker_notes(slide, notes)
    return slide


def add_two_col_slide(
    prs, title,
    left_title, left_items,
    right_title, right_items,
    *, accent, left_accent=None, right_accent=None, eyebrow=None, page=0, notes="",
    body_size=15,
):
    slide = _new(prs, "Empty")
    _set_title(slide, title)
    if eyebrow:
        add_text(
            slide, Inches(0.0), Inches(0.18), Inches(11.09), Inches(0.32),
            eyebrow.upper(), size=10, bold=True, color=accent,
        )

    left_accent = left_accent or accent
    right_accent = right_accent or accent

    col_w = 5.30
    gap = 0.30
    x_left = 0.0
    x_right = x_left + col_w + gap

    add_rect(slide, Inches(x_left + col_w + gap / 2 - 0.005), Inches(1.5),
             Inches(0.01), Inches(5.3), Theme.RULE_GRAY)

    add_text(
        slide, Inches(x_left), Inches(1.30), Inches(col_w), Inches(0.4),
        left_title.upper(), size=12, bold=True, color=left_accent,
    )
    add_bullets(
        slide, Inches(x_left), Inches(1.80), Inches(col_w), Inches(5.0),
        left_items, size=body_size, color=Theme.BODY_INK, bullet_color=left_accent,
        bold_first_token=True,
    )

    add_text(
        slide, Inches(x_right), Inches(1.30), Inches(col_w), Inches(0.4),
        right_title.upper(), size=12, bold=True, color=right_accent,
    )
    add_bullets(
        slide, Inches(x_right), Inches(1.80), Inches(col_w), Inches(5.0),
        right_items, size=body_size, color=Theme.BODY_INK, bullet_color=right_accent,
        bold_first_token=True,
    )

    add_speaker_notes(slide, notes)
    return slide


def add_three_col_slide(prs, title, columns, *, accent, eyebrow=None, page=0, notes=""):
    slide = _new(prs, "Empty")
    _set_title(slide, title)
    if eyebrow:
        add_text(
            slide, Inches(0.0), Inches(0.18), Inches(11.09), Inches(0.32),
            eyebrow.upper(), size=10, bold=True, color=accent,
        )

    col_w = 3.55
    gap = 0.13
    x0 = 0.0
    for i, (ctitle, citems, caccent) in enumerate(columns):
        x = x0 + i * (col_w + gap)
        add_rect(slide, Inches(x), Inches(1.30), Inches(col_w), Inches(0.45), caccent)
        add_text(
            slide, Inches(x + 0.15), Inches(1.35), Inches(col_w - 0.3), Inches(0.4),
            ctitle, size=12, bold=True, color=Theme.WHITE,
        )
        add_bullets(
            slide, Inches(x + 0.05), Inches(1.95), Inches(col_w - 0.1), Inches(4.9),
            citems, size=14, color=Theme.BODY_INK, bullet_color=caccent,
            line_spacing=1.30, para_space_before=4,
        )
        if i < len(columns) - 1:
            rule_x = x + col_w + gap / 2
            add_rect(slide, Inches(rule_x - 0.005), Inches(1.5),
                     Inches(0.01), Inches(5.3), Theme.RULE_GRAY)

    add_speaker_notes(slide, notes)
    return slide


def add_code_slide(
    prs, title, code_text, *, language="ST", accent=None, eyebrow=None, page=0, notes="", caption=None,
):
    accent = accent or Theme.BECKHOFF_BLUE
    slide = _new(prs, "Empty")
    _set_title(slide, title)
    if eyebrow:
        add_text(
            slide, Inches(0.0), Inches(0.18), Inches(11.09), Inches(0.32),
            eyebrow.upper(), size=10, bold=True, color=accent,
        )

    panel_x, panel_y = Inches(0.0), Inches(1.35)
    panel_w = Inches(10.95)
    panel_h = Inches(5.05 if caption else 5.35)
    add_rect(slide, panel_x, panel_y, panel_w, panel_h, Theme.CODE_PANEL_BG)

    add_text(
        slide, panel_x + Inches(0.20), panel_y + Inches(0.10),
        Inches(3.0), Inches(0.3),
        language.upper(),
        size=10, bold=True, color=accent,
    )

    code_lines = code_text.rstrip("\n").split("\n")
    n = len(code_lines)
    if n <= 14:
        cs = 16
    elif n <= 20:
        cs = 13
    elif n <= 26:
        cs = 12
    else:
        cs = 11

    add_text(
        slide,
        panel_x + Inches(0.30), panel_y + Inches(0.50),
        panel_w - Inches(0.55), panel_h - Inches(0.65),
        code_lines,
        font=Theme.MONO, size=cs, color=Theme.CODE_FG,
        line_spacing=1.25,
    )

    if caption:
        add_text(
            slide,
            Inches(0.0), Inches(6.50), Inches(11.09), Inches(0.4),
            caption, size=11, color=Theme.MUTED_INK, italic=True,
        )

    add_speaker_notes(slide, notes)
    return slide


def add_quote_slide(
    prs, kicker, quote, attribution, *, accent=None, page=0, notes="", on_dark=False,
):
    accent = accent or Theme.BECKHOFF_BLUE
    slide = _new(prs, "Empty")

    if on_dark:
        add_rect(slide, Inches(0.0), Inches(1.19), Inches(11.09), Inches(5.83), Theme.SLATE_DARK)
        text_color = Theme.WHITE
        sub_color = Theme.LIGHT_PANEL
        mark_color = Theme.BECKHOFF_BLUE
    else:
        add_rect(slide, Inches(0.0), Inches(1.19), Inches(11.09), Inches(5.83), Theme.LIGHT_PANEL)
        text_color = Theme.SLATE_DARK
        sub_color = Theme.SLATE
        mark_color = accent

    _set_title(slide, kicker)

    add_text(
        slide, Inches(0.10), Inches(1.20), Inches(2.0), Inches(2.2),
        "“", font=Theme.SERIF_ACCENT, size=160, color=mark_color, align=PP_ALIGN.LEFT,
    )

    add_text(
        slide, Inches(1.50), Inches(1.80), Inches(9.30), Inches(4.0),
        quote, size=28, color=text_color, italic=True, line_spacing=1.30,
    )

    if attribution:
        add_text(
            slide, Inches(1.50), Inches(6.30), Inches(9.30), Inches(0.55),
            f"— {attribution}",
            size=14, color=sub_color, align=PP_ALIGN.LEFT,
        )

    add_speaker_notes(slide, notes)
    return slide


def add_diff_slide(
    prs, title, branch_compare, headline_stat, takeaways, *, accent, eyebrow="result", page=0, notes="",
):
    slide = _new(prs, "Empty")
    _set_title(slide, title)
    if eyebrow:
        add_text(
            slide, Inches(0.0), Inches(0.18), Inches(11.09), Inches(0.32),
            eyebrow.upper(), size=10, bold=True, color=accent,
        )

    add_text(
        slide, Inches(0.0), Inches(1.30), Inches(10.95), Inches(0.40),
        f"git diff  {branch_compare}",
        font=Theme.MONO, size=12, color=Theme.MUTED_INK,
    )

    add_text(
        slide, Inches(0.0), Inches(1.85), Inches(10.95), Inches(1.4),
        headline_stat, size=64, bold=True, color=accent, line_spacing=1.0,
    )

    add_rect(slide, Inches(0.0), Inches(3.45), Inches(1.2), Inches(0.05), accent)

    add_bullets(
        slide, Inches(0.0), Inches(3.80), Inches(10.95), Inches(2.9),
        takeaways, size=18, color=Theme.BODY_INK, bullet_color=accent,
        bold_first_token=True,
    )

    add_speaker_notes(slide, notes)
    return slide


def add_pushback_slide(prs, kicker, customer_q, fae_a, *, accent=None, page=0, notes=""):
    accent = accent or Theme.BECKHOFF_RED
    slide = _new(prs, "Empty")
    _set_title(slide, "Pre-emptive pushback")
    add_text(
        slide, Inches(0.0), Inches(0.18), Inches(11.09), Inches(0.32),
        kicker.upper(), size=10, bold=True, color=accent,
    )

    cust_y = Inches(1.30)
    cust_h = Inches(2.05)
    add_rect(slide, Inches(0.0), cust_y, Inches(10.95), cust_h, Theme.LIGHT_PANEL)
    add_rect(slide, Inches(0.0), cust_y, Inches(0.10), cust_h, accent)
    add_text(
        slide, Inches(0.30), cust_y + Inches(0.15), Inches(10.5), Inches(0.35),
        "CUSTOMER", size=11, bold=True, color=accent,
    )
    add_text(
        slide, Inches(0.30), cust_y + Inches(0.55), Inches(10.5), Inches(1.45),
        customer_q, size=18, italic=True, color=Theme.SLATE_DARK, line_spacing=1.30,
    )

    fae_y = Inches(3.55)
    fae_h = Inches(3.35)
    add_rect(slide, Inches(0.0), fae_y, Inches(10.95), fae_h, Theme.SLATE_DARK)
    add_rect(slide, Inches(0.0), fae_y, Inches(0.10), fae_h, Theme.BECKHOFF_BLUE)
    add_text(
        slide, Inches(0.30), fae_y + Inches(0.15), Inches(10.5), Inches(0.35),
        "FAE ANSWER", size=11, bold=True, color=Theme.BECKHOFF_BLUE,
    )
    add_text(
        slide, Inches(0.30), fae_y + Inches(0.55), Inches(10.5), Inches(2.70),
        fae_a, size=17, color=Theme.WHITE, line_spacing=1.35,
    )

    add_speaker_notes(slide, notes)
    return slide


def add_scoreboard_slide(prs, *, page=0, notes=""):
    slide = _new(prs, "Empty")
    _set_title(slide, "The scoreboard")
    add_text(
        slide, Inches(0.0), Inches(0.18), Inches(11.09), Inches(0.32),
        "BLOCK 4 · 4A", size=10, bold=True, color=Theme.BLACK,
    )

    headers = [
        ("", Theme.MUTED_INK),
        ("Stage 1 — Procedural", Theme.SLATE_DARK),
        ("Stage 2 — Inheritance", Theme.SLATE),
        ("Stage 3 — Composition", Theme.BECKHOFF_BLUE),
    ]
    rows = [
        ("CR-1  Pause mode",
         "5 files\n+50  −13",
         "3 files\n+65  −48",
         "2 files\n+19  −6"),
        ("CR-2  Inspect quality + parallel",
         "2 files\n+92  −55",
         "2 files\n+121  −48",
         "1 line in MAIN\n+ ~3 internal"),
        ("CR-3  Selective logging",
         "2 files\n+13  −3",
         "3 files\n+64  −25",
         "3 files\n+32  −11"),
    ]

    x0 = 0.0
    y0 = 1.40
    col_widths = [3.05, 2.65, 2.65, 2.60]
    row_heights = [0.55, 1.15, 1.30, 1.15]

    cx = x0
    for (htext, hcol), cw in zip(headers, col_widths):
        if htext:
            add_rect(slide, Inches(cx), Inches(y0), Inches(cw), Inches(row_heights[0]), hcol)
            add_text(
                slide, Inches(cx + 0.15), Inches(y0 + 0.13),
                Inches(cw - 0.3), Inches(row_heights[0] - 0.2),
                htext, size=13, bold=True, color=Theme.WHITE,
            )
        cx += cw

    cy = y0 + row_heights[0]
    for r, (label, *cells) in enumerate(rows):
        rh = row_heights[r + 1]
        add_rect(slide, Inches(x0), Inches(cy), Inches(col_widths[0]), Inches(rh),
                 Theme.LIGHT_PANEL, line_color=Theme.RULE_GRAY)
        add_text(
            slide, Inches(x0 + 0.20), Inches(cy + 0.18),
            Inches(col_widths[0] - 0.4), Inches(rh - 0.2),
            label, size=14, bold=True, color=Theme.SLATE_DARK,
        )
        cx = x0 + col_widths[0]
        for j, cell in enumerate(cells):
            cw = col_widths[j + 1]
            add_rect(slide, Inches(cx), Inches(cy), Inches(cw), Inches(rh),
                     Theme.WHITE, line_color=Theme.RULE_GRAY)
            cell_color = Theme.BECKHOFF_BLUE if j == 2 else Theme.SLATE_DARK
            cell_bold = j == 2
            add_text(
                slide, Inches(cx + 0.15), Inches(cy + 0.18),
                Inches(cw - 0.3), Inches(rh - 0.2),
                cell, font=Theme.MONO, size=13, bold=cell_bold, color=cell_color,
                line_spacing=1.20,
            )
            cx += cw
        cy += rh

    add_text(
        slide, Inches(0.0), Inches(6.55), Inches(10.95), Inches(0.5),
        "Stage 3 wins on every CR. The shape of the win matters more than the line count.",
        size=14, italic=True, color=Theme.MUTED_INK,
    )

    add_speaker_notes(slide, notes)
    return slide


def add_break_slide(prs, label, duration, message, *, accent=None, page=0, notes=""):
    accent = accent or Theme.BECKHOFF_BLUE
    slide = _new(prs, "Empty")
    add_rect(slide, Inches(0.0), Inches(1.19), Inches(11.09), Inches(5.83), Theme.SLATE_DARK)
    _set_title(slide, label)

    add_text(
        slide, Inches(0.0), Inches(1.50), Inches(10.95), Inches(0.50),
        "BREAK", size=14, bold=True, color=accent,
    )
    add_text(
        slide, Inches(0.0), Inches(2.20), Inches(10.95), Inches(1.7),
        duration, size=96, bold=True, color=Theme.WHITE, line_spacing=1.0,
    )
    add_text(
        slide, Inches(0.0), Inches(4.50), Inches(10.95), Inches(2.0),
        message, size=20, italic=True, color=Theme.LIGHT_PANEL, line_spacing=1.4,
    )
    add_speaker_notes(slide, notes)
    return slide


def add_closing_slide(prs, title, body, contact, *, accent=None, page=0, notes=""):
    accent = accent or Theme.BECKHOFF_BLUE
    slide = _new(prs, "Empty")
    add_rect(slide, Inches(0.0), Inches(1.19), Inches(11.09), Inches(5.83), Theme.SLATE_DARK)
    _set_title(slide, "Wrap")

    add_text(
        slide, Inches(0.0), Inches(1.50), Inches(10.95), Inches(0.50),
        "FROM PROCEDURAL TO SOLID  ·  CLOSING",
        size=13, bold=True, color=accent,
    )
    add_text(
        slide, Inches(0.0), Inches(2.10), Inches(10.95), Inches(1.4),
        title, size=44, bold=True, color=Theme.WHITE, line_spacing=1.0,
    )
    add_text(
        slide, Inches(0.0), Inches(3.80), Inches(10.95), Inches(2.7),
        body, size=18, color=Theme.LIGHT_PANEL, line_spacing=1.4, italic=True,
    )
    add_text(
        slide, Inches(0.0), Inches(6.60), Inches(10.95), Inches(0.4),
        contact, size=12, color=Theme.SLATE_LIGHT,
    )
    add_speaker_notes(slide, notes)
    return slide


# ---------------------------------------------------------------------------
# Template prep — strip the 20 example slides
# ---------------------------------------------------------------------------

def _strip_example_slides(prs):
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)


# ---------------------------------------------------------------------------
# Content
#
# Slide content = audience-facing only.
# Speaker notes = facilitator's live script. Notes use [BRACKET] section
# labels: [BEFORE], [SAY], [DO], [CONTEXT], [DISCUSSION], [PACING], [NEXT].
# ---------------------------------------------------------------------------

def build_slides(prs):
    page = 0
    def n():
        nonlocal page
        page += 1
        return page

    # ===== BLOCK 0 — Welcome ===============================================

    add_title_slide(
        prs,
        title="From Procedural to SOLID",
        subtitle="Object-Oriented PLC Design in TwinCAT 3",
        tagline="A 4-hour workshop  ·  NEM 2026",
        accent=Theme.BECKHOFF_BLUE,
        notes="""
[BEFORE] Up while attendees settle. Don't speak to it.

[CHECK — first action of the day] Confirm everyone has the repo cloned and a working XAE. Hands up. Anyone who can't build, surface NOW — there's a 5-minute Block 0 budget for env triage.

[SAY — 30-second frame, when you click forward]
"You'll build the same filling line three different ways. Same requirements at every stage. The diffs tell the story."
""".strip(),
    )

    add_content_slide(
        prs,
        title="The next 4 hours",
        bullets=[
            "Same machine — three architectures.",
            "Same three change requests, every stage.",
            "One running scoreboard — nine cells.",
            "When does each architecture pay off?",
        ],
        accent=Theme.BECKHOFF_BLUE,
        eyebrow="Block 0 · the frame",
        page=n(),
        body_size=24,
        notes="""
[SAY] Read the four lines slowly. The framing controls the whole day.

[KEY PHRASE] "The diffs tell the story." We are not lecturing about SOLID. We are running a controlled experiment — same inputs, three different blast radii.

[DO] Coax discussion early so the precedent is set. If they sit silent, the workshop fails.

[NEXT] Branch tree comes after the schedule slide — don't dive in yet.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The schedule",
        bullets=[
            "Block 0  ·  Welcome  ·  5 min",
            "Block 1  ·  Stage 1 — Procedural  ·  85 min",
            "Break  ·  10 min",
            "Block 2  ·  Stage 2 — Inheritance  ·  70 min",
            "Break  ·  10 min",
            "Block 3  ·  Stage 3 — Composition  ·  70 min",
            "Block 4  ·  Scoreboard + take-home  ·  20 min",
        ],
        accent=Theme.BECKHOFF_BLUE,
        eyebrow="Block 0",
        page=n(),
        body_size=18,
        notes="""
[DO] Walk this in 60 seconds. Don't dwell.

[SAY] "We'll be done by hour 4. Breaks are real."

[STRETCH ZONES — flag verbally]
- Block 1 — "Who copied from Fill?" reveal can run +10 min.
- Block 2 — CR-2 'SUPER-can't-be-called' is the workshop's hardest 25 min. Plan to slow down.
- Block 3 — CR-2 swap demo lands in 90 seconds; let the silence happen.
- Block 4 — plan to overshoot; that's where FAEs cement what they'll teach.

[BUDGET] On paper 4:30 — plan to land in 4:00.

[BONUS] If asked about the testing demo: "Bonus content if we finish ahead. Don't count on it."
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 0  ·  opening discussion",
        quote="Who here has shipped a 4-station-or-larger machine in the last year?",
        attribution="Then this workshop is calibrated for you.",
        accent=Theme.BECKHOFF_BLUE,
        page=n(),
        notes="""
[ASK] The question. Wait for hands. You should see most of the room.

[SAY — follow-up that lands the framing]
"Then this workshop is calibrated for you. The pain we're going to surface is pain you've already felt — but you've probably never named it. Today we name it, score it, and rehearse what to say when a customer pushes back."

[REPEAT EXPECTATIONS] "We move at FAE pace. But I want lots of discussion. If something feels wrong or you've seen it work differently, say so."
""".strip(),
    )

    # ===== BLOCK 1 — Stage 1 — Procedural ==================================

    add_section_divider(
        prs,
        block_label="Block 1",
        title="Stage 1 — Procedural",
        time_budget="85 min",
        summary="The architecture you've been writing for 20 years.",
        accent=Theme.AMBER,
        notes="""
[BEFORE] Switch presenter to `Release`. In XAE, expand `FillingLine_Procedural` → POUs and open all four station FBs side by side: FB_StationFill, FB_StationCap, FB_StationLabel, FB_StationInspect. (Legacy single-PLC alternative: `git switch stage-1-procedural`.)

[SAY — when you click forward]
"This is the architecture you've been writing for 20 years. IEC 61131-3 was designed for it. There's nothing wrong with it. Today we feel where it stops scaling."

[STRUCTURE] 1A walkthrough → CR-1 → CR-2 → CR-3 → debrief. Stretch zone is the CR-1 'who copied from Fill?' reveal.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The procedural paradigm",
        bullets=[
            "Origin — IEC 61131-3 (1993).",
            "Mental model — FB owns its state, runs once per cycle.",
            "Good at — small machines, short lifespan.",
            "Bad at — cross-cutting changes across N stations.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1A walkthrough",
        page=n(),
        body_size=22,
        notes="""
[SAY — don't read aloud, summarize]
"This is the architecture you've been writing for 20 years. Nothing wrong with it. We're going to feel where it stops scaling."

[CONTEXT — only if asked]
- 1970s structured programming + 1980s industrial controls; codified by IEC 61131-3 in 1993.
- Why it dominates TwinCAT: runtime, libraries, training, customer expectations all assume it. Path of least resistance.
- "Good at" examples: panel shops, single-machine integrators, code that won't outlive the contract.

[SEGUE] Spend more time on "Bad at" — that's the bridge to the drift demo on the next slide.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Every station has the same five sections",
        bullets=[
            "Mode block — read ModeAuto / ModeManual / ModeStop.",
            "Alarm-ack block — clear latched alarms.",
            "Reset block — return state to 0.",
            "State machine — the actual sequence (CASE).",
            "HMI mapping — copy state to HMI tags.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1A walkthrough",
        page=n(),
        body_size=20,
        notes="""
[DO] Pull up Fill and Cap side by side. Walk the five sections in order.

[SAY] "Sections 1, 2, 3, 5 are nearly identical between stations. Section 4 — the state machine — is the only meaningfully different part. Section 4 is what makes the station the station."

[FOUNDATION] This is the setup for the next three slides on drift. Don't editorialize on drift yet — the audience will see it themselves.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Three deliberate drifts",
        bullets=[
            "Drift #1 — alarm-ack: edge vs level.",
            "Drift #2 — step numbering: 0/100/200/300 vs 0/10/20/30.",
            "Drift #3 — dead variable: ManualStep in Inspect, never used.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1A walkthrough",
        page=n(),
        body_size=22,
        notes="""
[SAY — only the names. The next three slides have the code.]
"Three drifts, all between stations that should look the same. Pedagogical, not bugs — they're the setup for CR-1's reveal moment."

[DO] Do NOT editorialize on the drift yet. Just show the three names. The discussion happens after CR-1 when attendees discover they've inherited the drift by copy-paste.

[CONTEXT — DO NOT TIDY UP IN THE REPO] These drifts are deliberate. If you "clean them up" before the workshop, you destroy the CR-1 reveal.

[WATCH FOR] If anyone in the room laughs or groans during a drift reveal — that's the workshop working. Note who; ask them later if they have a specific story.
""".strip(),
    )

    add_code_slide(
        prs,
        title="Drift #1 — alarm-ack: edge vs level",
        code_text="""// FB_StationFill — uses R_TRIG (edge-triggered)
fbAckTrig(CLK := AlarmAck);
IF fbAckTrig.Q AND AlarmActive THEN
    AlarmActive := FALSE;
    AlarmCode   := 0;
END_IF

// FB_StationCap — uses level (held-high)
IF AlarmAck AND AlarmActive THEN
    AlarmActive := FALSE;
    AlarmCode   := 0;
END_IF

// They look identical. They behave differently the moment AlarmAck is wired
// to a maintained switch instead of a pushbutton.""",
        language="Structured Text",
        accent=Theme.AMBER,
        eyebrow="Block 1 · drift #1",
        page=n(),
        notes="""
[SAY] "Both implementations look reasonable in isolation. Side-by-side they're a maintenance trap."

[KEY POINT] Nobody wrote buggy code. Both stations work. The system itself failed to enforce consistency — there's no way for the procedural architecture to say 'all stations ack the same way.'

[SETUP FOR CR-1] This is the drift that catches people on CR-1. They copy the Pause guard from Fill (R_TRIG style) into Label (level style) and the inconsistency compounds.
""".strip(),
    )

    add_code_slide(
        prs,
        title="Drift #2 — step numbering",
        code_text="""// FB_StationFill, Cap, Inspect — clean 0/10/20/30
CASE State OF
    0:   // idle
    10:  // run
    20:  // complete
    30:  // fault
END_CASE

// FB_StationLabel — copy-pasted from a different machine years ago
CASE State OF
    0:    // idle
    100:  // run
    200:  // complete
    300:  // fault
END_CASE""",
        language="Structured Text",
        accent=Theme.AMBER,
        eyebrow="Block 1 · drift #2",
        page=n(),
        notes="""
[SAY] "Both work. Neither is wrong. They diverge for no reason."

[CONTEXT] Someone clearly copied Label from a different project where 100/200/300 was the convention, and never normalized it.

[LESSON] The architecture has no opinion on naming. Conventions are tribal — they live in your head, not the compiler.

[FORESHADOW] Stage 2's base class will normalize this for free. You'll see it in Block 2.
""".strip(),
    )

    add_code_slide(
        prs,
        title="Drift #3 — dead variable",
        code_text="""// FB_StationInspect — declared, never read, never written
VAR
    State           : INT;
    AlarmActive     : BOOL;
    AlarmCode       : INT;
    ManualStep      : INT;   // <-- nothing in this FB references it
    PartPresent     : BOOL;
    Result          : BOOL;
END_VAR

// Probably copied from a different station's draft 18 months ago.
// Nobody removed it because nobody knew it was safe to remove.""",
        language="Structured Text",
        accent=Theme.AMBER,
        eyebrow="Block 1 · drift #3",
        page=n(),
        notes="""
[DO] Don't dwell — show it and move on.

[LESSON] In procedural code, dead state lingers because removing it requires reading every reference everywhere. Nobody owns the cleanup.

[FORESHADOW] In Stage 2 the base class won't carry ManualStep, so it can't propagate. In Stage 3 the FB has explicit dependencies; an unused field is loud.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 1 · 1A discussion",
        quote="Anyone here written something that looks like this in the last six months?",
        attribution="Hold on to that feeling — we're about to make it worse.",
        accent=Theme.AMBER,
        page=n(),
        notes="""
[ASK — three-step audience hands-up]
1. "Anyone written something that looks like this in the last six months?" → most hands.
2. "Anyone written EXACTLY five files like this?" → some hands stay up.
3. "Anyone copied station 5 from station 4 and then had to fix four things?" → more hands.

[CLOSE] "Good. Hold on to that feeling. We're about to make it worse with CR-1."

[DO] Don't rush past this slide — earn the audience commitment before starting the timer. The first reveal is coming.
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 1 · 1A pre-emptive pushback",
        customer_q="This is fine. We've shipped 50 machines like this. Why are we changing it?",
        fae_a="You're right — it's fine for one machine. We're going to look at what happens when the same change has to land in four files instead of one. If that's never happened to you, this workshop won't change your mind. If it has, you'll recognize the pain.",
        page=n(),
        notes="""
[ABOUT THE PUSHBACK SLIDES] First of ~10 in the deck. Format is the same throughout: customer's actual objection on top, rehearsed FAE answer below. Run THIS one explicitly so the format is established. Later ones can be flashed quickly unless the room wants to dwell.

[WHY THIS ONE MATTERS] Most common objection FAEs get from senior controls engineers.

[CUSTOMER-CONVERSATION PATTERN] Note the structure: respect the customer ("you're right") before pivoting to the cost ("what happens when…"). Flag this as a template for any pushback rebuttal.
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-1  ·  Add a Pause mode",
        bullets=[
            "Global ModePause input. Every station holds when TRUE.",
            "Exception — Fill must ignore Pause mid-cycle.",
            "Cross-cutting + has an exception + feels small.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1B  ·  CR-1 hands-on (20 min)",
        page=n(),
        body_size=22,
        notes="""
[SAY — read CR-1 verbatim]
"Add a global Pause input. When ModePause is TRUE, every station should hold. Exception: the Fill station must ignore Pause mid-cycle — pausing a half-filled bottle ruins the product."

[THE TRAP] Most attendees miss the Fill exception on first read and write a uniform Pause guard.

[DO]
1. Switch presenter to `stage-1-broken` (this demo uses the legacy single-PLC branch — the broken state was deliberately preserved there). Show the compile error in MAIN.
2. "30 seconds to read the broken state, then 15 minutes to fix it."
3. Set the timer. Walk the room. DON'T HELP. Wait until people are ~10 minutes in before you interrupt for the reveal slide.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 1 · CR-1 the reveal moment",
        quote="Quick check — how many of you copied Pause logic into Label from Cap? From Fill? From Inspect?  Now: who has level-based AlarmAck and who has R_TRIG?",
        attribution="That's the procedural maintenance trap. Drift you didn't even know was there.",
        accent=Theme.AMBER,
        page=n(),
        on_dark=True,
        notes="""
[WHEN] After ~10 minutes, when most attendees are mid-fix. INTERRUPT.

[ASK — two questions, in sequence]
1. "How many of you copied your Pause logic into Label from Cap? From Fill? From Inspect?" → mixed hands.
2. "Now: who has a level-based AlarmAck and who has an R_TRIG?" → the room goes quiet because some attendees realize they copied from a station with one ack style and pasted into one with the other.

[DELIVER THE LESSON]
"That's the procedural maintenance trap. Drift you didn't know was there. The system itself failed to enforce consistency. You weren't writing buggy code — the architecture failed to help you."

[DO] Let the silence sit for 5 seconds before moving on. The realization IS the lesson; don't trample it.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-1 result",
        branch_compare="Release...cr1-applied --stat -- NEM2026/FillingLine_Procedural/",
        headline_stat="5 files  ·  +50  −13",
        takeaways=[
            "Same 25 lines of guard logic, paid four times.",
            "Fill's exception — easy to miss, easy to copy wrong.",
            "Tomorrow's CR pays this cost too. And the next.",
        ],
        accent=Theme.AMBER,
        page=n(),
        notes="""
[BEFORE] After attendees finish (or you call time): `git switch cr1-applied` and `git diff Release --stat -- NEM2026/FillingLine_Procedural/` on screen.

[DO] Write the 5 / +50 / −13 number on the physical scoreboard whiteboard.

[SAY] "This is what your codebase looks like after one CR."

[ASK] "Show of hands — who got Fill's mid-cycle exception right on the first try?" Most won't.

[FOLLOW-UP] "That's not a comment on you; it's a comment on the design. The exception is buried in the same Pause-guard logic every other station uses. You couldn't write it once and apply it correctly four ways."
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 1 · CR-1 pre-emptive pushback",
        customer_q="My team's careful. We use code review. Drift won't happen.",
        fae_a="Code review against duplicated logic catches drift sometimes. Drift you don't catch is the kind that ships. The architecture either enforces consistency or it doesn't — and code review is your last line of defense, not your first.",
        page=n(),
        notes="""
[FRAME] Acknowledge that process catches some drift — then sharpen the point: process catches drift you notice; architecture catches the drift you don't.

[CALLBACK] Pair this with the line "Discipline is bounded; architecture is unbounded." You'll use it again in Block 2.
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-2  ·  Inspect: non-faulting alarm + parallel",
        bullets=[
            "Inspect must flag visual defects — without stopping the line.",
            "Camera and reject pre-arm — at the same time, not sequentially.",
            "Only Inspect changes. The other three stations stay as-is.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1C  ·  CR-2 hands-on (20 min)",
        page=n(),
        body_size=20,
        notes="""
[SAY — read CR-2 aloud, emphasize the phrase]
"Two axes of variation at once. Alarm policy AND sequencer topology. Only one station, but the patterns have to coexist with the others."

[DO] Set 15-minute timer. Walk the room.

[WATCH FOR] The attempt: rewriting Inspect's CASE machine end-to-end with QualityFlag/QualityCode/QualityText outputs and CameraDone/RejectDone parallel coordination inside step 10.

[STRETCH WHEN DONE]
"How many of you ended up with a 60+ line rewrite of one CASE machine?" (Most.) "Now: think about the next station that needs parallel branches. How much of what you just wrote can the next person reuse?" (Almost none — the parallel coordination is buried in Inspect's CASE.)
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-2 result",
        branch_compare="Release...cr2-applied --stat -- NEM2026/FillingLine_Procedural/",
        headline_stat="2 files  ·  +92  −55",
        takeaways=[
            "Inspect's CASE machine rewritten end-to-end.",
            "Parallel coordination buried in CASE — nothing reusable.",
            "The next station that needs parallel pays this cost again.",
        ],
        accent=Theme.AMBER,
        page=n(),
        notes="""
[SAY] "This isn't just duplication of the base — it's duplication of NEW patterns each time they appear. Stage 2 will help with this. Stage 3 will help even more."

[PUSHBACK if asked] "Why do I care that the parallel logic isn't reusable? I only have one Inspect station." → "Today, you do. Two years from now, you might have an Inspect AND a Test station that both need parallel branches. The procedural cost of CR-2 is a tax you pay every time a new station needs the same pattern."
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-3  ·  Selective cycle logging",
        bullets=[
            "Log cycle data for Fill and Inspect. Cap and Label don't need it.",
            "Looks trivial. The temptation: paste 13 lines into both.",
            "Logger implementation will probably change later.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1D  ·  CR-3 hands-on (15 min)",
        page=n(),
        body_size=20,
        notes="""
[DO] Read it, set a 10-minute timer, let them go. Most attendees finish in 7-8 minutes.

[THE TRAP] It looks small. They'll write 13 lines and feel done. The cost — duplication that will be paid every time the logging requirement evolves — is invisible until it bites.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-3 result — small, but defend it as fine?",
        branch_compare="Release...cr3-applied --stat -- NEM2026/FillingLine_Procedural/",
        headline_stat="2 files  ·  +13  −3",
        takeaways=[
            "Identical buffer code in two places.",
            "Logger evolves in 6 months — two places to change. Forget one? Drift.",
            "Smallest line count. Loses on every other dimension.",
        ],
        accent=Theme.AMBER,
        page=n(),
        notes="""
[ASK] "That looked small. Anyone want to defend it as 'fine'?" Some attendees will defend it. Let them — then sharpen.

[FOLLOW-UP] "Now imagine the logging requirements change in six months — say we want to write to a file instead of an in-memory buffer. Where do you change the code?" (Two places.) "And if you forget one of them?" (Drift.)

[PUSHBACK if asked] "It's literally 13 lines. Stop making it a big deal." → "It's 13 lines today. The cost isn't the lines; it's the duplication. Every future change to that logic happens twice. Stage 3 — same lines, but only one place to change."
""".strip(),
    )

    add_content_slide(
        prs,
        title="Block 1 debrief — why are we moving on?",
        bullets=[
            "Total Stage 1 diff — 5 files, +152, −66.",
            "Drift between files.",
            "Can't enforce consistency.",
            "Duplication compounds.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1E debrief (15 min)",
        page=n(),
        body_size=22,
        notes="""
[BEFORE] Switch presenter to `complete`. Show `git diff Release --stat -- NEM2026/FillingLine_Procedural/` live.

[SAY] "That's what your codebase looks like after a year of cross-cutting CRs. Five files modified, growth concentrated in Inspect, duplication on every cross-cutting concern."

[ASK — the bridge to Block 2] "Stage 1 isn't broken. It works. So why are we moving on?"

[ANTICIPATED ANSWERS — capture on whiteboard]
- "Drift between files."
- "Can't enforce consistency."
- "Duplication compounds."

[CLOSE] "Right. Now we'll see what happens when we try to fix all of that with a base class. Spoiler: we'll fix some of it. We'll create new problems too."

[PACING] If behind, cut CR-3 hands-on (smallest CR, easiest to walk declaratively). If ahead, extend the CR-1 reveal into a longer drift discussion.
""".strip(),
    )

    add_break_slide(
        prs,
        label="Block 1 → Block 2 break",
        duration="10 min",
        message="Coffee, bathroom, social conversation. The next block has the densest concept load.",
        accent=Theme.AMBER,
        page=n(),
        notes="""
[DO NOT SHORTEN] Don't compress to 5 minutes — you'll pay for it in Block 2's CR-2 attention crash.

[USE THE BREAK] Make sure presenter is on `Release` (or stay there from Block 1). In XAE, expand `FillingLine_Inheritance` → POUs and open FB_StationBase and FB_StationFill in side-by-side tabs.
""".strip(),
    )

    # ===== BLOCK 2 — Stage 2 — Inheritance =================================

    add_section_divider(
        prs,
        block_label="Block 2",
        title="Stage 2 — Inheritance",
        time_budget="70 min",
        summary="The duplication evaporates.\nThen the base class becomes the constraint.",
        accent=Theme.TEAL,
        notes="""
[BEFORE] Presenter on `Release`, `FillingLine_Inheritance` expanded. FB_StationBase and FB_StationFill side by side.

[FRAMING] Block 2 is the trickiest to facilitate. Inheritance has real wins; don't dismiss them. But the audience has to FEEL where it stops working, not just be told. Pace the CR-2 reveal carefully — that's the workshop's hardest moment (25 min).
""".strip(),
    )

    add_content_slide(
        prs,
        title="The inheritance paradigm",
        bullets=[
            "Origin — Simula 67, Smalltalk 1972; mainstream via C++ / Java.",
            "Mental model — base encodes shared; children override to specialize.",
            "TwinCAT — EXTENDS, virtual METHOD, THIS^ / SUPER^, FB_init.",
            "Promise — write the common path once.",
            "Catch — the common path becomes a constraint.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2A walkthrough",
        page=n(),
        body_size=20,
        notes="""
[DON'T LECTURE] Read the bullets, gesture at the FB_StationBase tab, move on.

[SEED] "The common path becomes a constraint when ANY child needs to opt out." Plant it now — water it on the CR-2 slides.

[CONTEXT — only if asked] FB_init is TwinCAT's constructor: runs once at instantiation, takes parameters that never change. Use it for names, sizes, references the FB will hold for its lifetime.

[FRAMEWORK] Stage 2 builds on Beckhoff USA's SPT-Libraries (FB_ComponentBase). Production-grade, not academic.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Same code, same behavior, different architecture",
        bullets=[
            "FB_StationFill — ~110 lines → ~65. Shrinkage moved into the base.",
            "Drift #1 fixed — base normalizes alarm-ack to R_TRIG.",
            "Drift #2 fixed — Label normalized to 0/10/20/30.",
            "Drift #3 fixed — dead ManualStep doesn't propagate.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2A walkthrough",
        page=n(),
        body_size=20,
        notes="""
[DO] Open FB_StationFill, walk the shrinkage. Then open FB_StationBase and show where each section moved.

[EARN THE WIN] The drift fixes are the headline win for Stage 2. Walk through them slowly — earn the win before you puncture it.

[ASK] "What did this refactor cost?" Take answers. First answers will be: nothing visible, lower line count, etc.

[PUSH TO THE RIGHT ANSWER] "It cost an extra concept. Now you have to understand 'base class' and 'override' and 'THIS vs SUPER' to read this code. That's the real cost. Be honest about it."
""".strip(),
    )

    add_code_slide(
        prs,
        title="Inheritance mechanics — four things to recognize",
        code_text="""// 1. EXTENDS — child declares parent
FUNCTION_BLOCK FB_StationFill EXTENDS FB_StationBase

// 2. SUPER^ — explicit base call
METHOD PROTECTED CyclicLogic
    SUPER^.CyclicLogic();    // run the base's mode/ack/reset
    THIS^.ExecuteSequence(); // then run my sequence

// 3. Method override — child's version replaces base's
METHOD PROTECTED ExecuteSequence
    CASE State OF
        0:  IF Mode.AllowRun THEN State := 10; END_IF
        10: // ... fill logic
        20: State := 0;
    END_CASE

// 4. FB_init — construction-time parameters
METHOD FB_init : BOOL
VAR_INPUT
    bInitRetains : BOOL;
    bInCopyCode  : BOOL;
    Name         : STRING(20);
END_VAR
SUPER^.FB_init(bInitRetains, bInCopyCode);
THIS^.Name := Name;""",
        language="Structured Text",
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2A walkthrough",
        page=n(),
        notes="""
[DO] Walk all four constructs by name (EXTENDS, SUPER^, override, FB_init).

[FAE-SPECIFIC] For FAEs this is review at the conceptual level. The reason you're naming them: they'll have to TEACH this to controls engineers who haven't used inheritance, and the vocabulary matters.

[SAY] "If you're going to teach Stage 2 to your customers, this slide is what you'll spend 5 minutes on. The audience needs to recognize all four constructs by sight before CR-1."
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 2 · 2A pre-emptive pushback",
        customer_q="My junior engineers don't know inheritance. Now they can't read my code.",
        fae_a="That's a valid concern. Inheritance has a learning cost. The win is consistency enforcement — once your team learns it, drift goes away. The trade-off is real; you pick whichever fits your team's experience curve.",
        page=n(),
        notes="""
[DON'T DISMISS] The customer is correct that inheritance has a learning cost. The honest framing is the trade-off, not the dismissal.

[VARIANT — common follow-up] "We don't have time to train the team." → "Then Stage 1 is your right answer for now. The workshop's value isn't 'always pick Stage 3.' It's 'know which stage fits your situation.'"
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-1 — the inheritance way",
        bullets=[
            "Same Pause requirement.",
            "Option A — virtual AllowPause() on the base; Fill overrides.",
            "Option B — Fill overrides Monitoring entirely.",
            "Both legitimate. Both ugly in the same way.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2B  ·  CR-1 hands-on (15 min)",
        page=n(),
        body_size=20,
        notes="""
[DO] Read the requirement. Set 10-minute timer. Walk the room. Most attendees start with Option A — feels more "inheritance-y."

[ASK MID-EXERCISE] When attendees are stuck, walk and ask: "How are you handling the exception?" Both options will surface.

[SAY OUT LOUD WHEN BOTH SURFACE]
"Option A — AllowPause exists for ONE child's exception, but Cap, Label, Inspect inherit it forever. Pollution. Option B — duplicates base mode logic in Fill. Drift risk. Pick your poison."

[REVEAL #2] This is the workshop's second reveal: inheritance trades one cost for another. Stage 1 had per-station pollution; Stage 2 puts the pollution on the base.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-1 result — base-class pollution",
        branch_compare="Release...cr1-applied --stat -- NEM2026/FillingLine_Inheritance/",
        headline_stat="3 files  ·  +65  −48",
        takeaways=[
            "Pollution lives on the base — every reader, every child pays.",
            "vs Stage 1: fewer files, more lines.",
            "Inheritance didn't eliminate the cost. It relocated it.",
        ],
        accent=Theme.TEAL,
        page=n(),
        notes="""
[SHOW] Live diff vs Stage 1 (5 files / +50 / −13) → Stage 2 (3 files / +65 / −48).

[ASK — discussion] "Which is worse — scattered pollution paid by 4 stations, or centralized pollution paid by every reader of the base?"

[POINT] There's no right answer. That's the point. Inheritance didn't eliminate the cost; it relocated it.

[BRIDGE] This sets up CR-2, where the relocation becomes a trap.
""".strip(),
    )

    add_section_divider(
        prs,
        block_label="Block 2 · 2C",
        title="CR-2 — the breaking point",
        time_budget="25 min  ·  the workshop's hardest moment",
        summary="Same as Stage 1, applied via inheritance.\nWatch the override fight the base.",
        accent=Theme.TEAL,
        notes="""
[PLAN TO SLOW DOWN] This block is the workshop's hardest moment.

[DO]
1. Read CR-2 again — same requirement as Stage 1.
2. Set 15-minute timer. "I'll be available — this one's harder."
3. Walk the room.

[WATCH FOR] Most attendees start by overriding Monitoring and adding their quality-flag logic AFTER calling SUPER^.Monitoring(). This produces broken behavior — the base latches the alarm before their override can flag it as quality.

[NEXT SLIDE] The leading-questions slide is for when they're stuck. Use it to walk them to the realization.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The realization — you can't call SUPER",
        bullets=[
            "When does SUPER^.Monitoring() latch the alarm?",
            "What does the quality-flag policy say should happen?",
            "So what does that imply about calling SUPER?",
            "But if you don't call SUPER, you lose the base's mode + ack.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2C  ·  the breaking point",
        page=n(),
        body_size=20,
        notes="""
[DO] Walk the room while attendees are stuck. Use these four leading questions IN ORDER. Let them arrive at the realization themselves.

[ANTICIPATED ANSWERS]
1. "Every time RaiseStationAlarm is called."
2. "Don't latch."
3. "You can't call SUPER."
4. "You have to duplicate them in your override."

[GATHER ATTENTION AND DELIVER]
"There's no way to say 'inherit everything except the alarm policy.' Inheritance is all-or-nothing. Whatever the base does, every child gets — unless the child reimplements that behavior in an override."

[DO] Show stage-2-broken (legacy single-PLC branch — the half-finished override was preserved there): "This is what mid-fix looks like in real life — a partially overridden Monitoring with TODO comments." Leave the TODOs visible; they're the visual evidence of the design fight.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 2 · CR-2 the breaking-point reveal",
        quote="The base class that helped you in Stage 1 → Stage 2 has now become the constraint. Inspect can't extend the base. It has to fight the base.",
        attribution="This isn't your fault. It's a property of the design. Single inheritance is all-or-nothing.",
        accent=Theme.TEAL,
        page=n(),
        on_dark=True,
        notes="""
[REVEAL #3] Workshop's third reveal. Climax of Block 2.

[DO] Read the quote slowly. Wait. Let it land. The room should be uncomfortable — that's the lesson working.

[DO NOT FILL THE SILENCE] Senior controls engineers in the room are recognizing this pattern from their own codebases right now.

[CALLBACK SETUP] Mark this in your head: in Block 3 we'll call back to this exact moment when the CR-2 swap is one line.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-2 result — the override fight",
        branch_compare="Release...cr2-applied --stat -- NEM2026/FillingLine_Inheritance/",
        headline_stat="2 files  ·  +121  −48",
        takeaways=[
            "Inspect overrides Monitoring without calling SUPER.",
            "~80 lines reimplement mode + ack from scratch.",
            "Every future base change is now \"did we update Inspect?\"",
        ],
        accent=Theme.TEAL,
        page=n(),
        notes="""
[DO] Show the diff. Highlight the ~80-line override on the projector if you have time.

[SAY] "The visible cost is the line count. The invisible cost is the future-change burden every time the base evolves."

[COMPARE] Stage 1 CR-2 was 92 lines of inline rewrite. Stage 2 CR-2 is 121 lines of override fight. The architecture made it WORSE on lines, not better.

[NEXT SLIDE] The most important pushback in the workshop. Don't skip it.
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 2 · CR-2 the most important pushback",
        customer_q="This is fine — I just need to remember to mirror base changes into Inspect's override.",
        fae_a="That's a code-review burden you'll carry forever. Every base change is now a question of 'did we update Inspect?' Sometimes you'll forget. The architecture isn't enforcing the consistency anymore — your team's discipline is. Discipline is bounded; architecture is unbounded.",
        page=n(),
        notes="""
[MOST IMPORTANT PUSHBACK] If only one customer-conversation Q&A sticks, this is the one you want.

[KEY LINE] "Discipline is bounded; architecture is unbounded." The workshop's central thesis in seven words. Mark it. Repeat it in Block 3 and Block 4. Make it the line attendees go home quoting.

[VARIANT — if asked] "Use multiple inheritance, then." → "TwinCAT doesn't support multiple inheritance, and most languages that do (C++, Python) have ugly issues with it (the diamond problem). The composition pattern in Stage 3 solves the same need without those issues. We'll get there."
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-3 result — dead weight in unrelated children",
        branch_compare="Release...cr3-applied --stat -- NEM2026/FillingLine_Inheritance/",
        headline_stat="3 files  ·  +64  −25",
        takeaways=[
            "LogBuffer + LoggingEnabled added to the base.",
            "Cap and Label inherit storage they never use.",
            "Cognitive cost compounds even when memory cost doesn't.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2D  ·  CR-3 hands-on (10 min)",
        page=n(),
        notes="""
[DO] Read the requirement. 5-minute timer. The attempt: LogBuffer + LoggingEnabled virtual on the base; Fill and Inspect override to TRUE.

[ASK] "Where does Cap's LogBuffer storage live in memory?" → in every Cap and Label instance, even though they never write to it. "Is that a problem?" → in 4 stations, no. In a 50-station factory, yes.

[PUSHBACK if asked] "100 strings × 120 chars × 2 unused stations = 24KB. Why are we obsessing about this?" → "You're right — for this scale, the memory cost is academic. The bigger problem is COGNITIVE. Every reader of FB_StationBase has to understand why LogBuffer exists when half the children don't use it. As your codebase grows, that noise compounds."

[PACING] If behind, cut this hands-on entirely (just show the diff). The CR-2 breakdown is the lesson; CR-3 is supplementary.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Block 2 debrief — the base became a junk drawer",
        bullets=[
            "Total Stage 2 diff — 4 files, +224, −65.",
            "Wins — drift fixed, consistency enforced.",
            "New problems — base pollution, SUPER fragility, dead weight.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2E debrief (5 min)",
        page=n(),
        body_size=22,
        notes="""
[DO] Switch presenter to `complete`. Show `git diff Release --stat -- NEM2026/FillingLine_Inheritance/` live. Walk the FillingLine_Inheritance/POUs/FB_StationBase tab — point to each new accumulation: ModePause field, AllowPause virtual, LogBuffer, LoggingEnabled virtual, LogCycleData helper.

[SAY] "It started clean. Now it's a junk drawer. Every CR added another carve-out the base wasn't designed for."

[ASK] "Stage 2 fixed real Stage 1 problems. What new problems did it create?"

[ANTICIPATED ANSWERS — capture on whiteboard]
- "Base-class pollution."
- "SUPER-can't-be-called fragility."
- "Dead weight in unrelated children."

[BRIDGE] "Stage 3 will keep what's good — clean abstractions, consistency enforcement — and fix what's wrong. Let's go."
""".strip(),
    )

    add_break_slide(
        prs,
        label="Block 2 → Block 3 break",
        duration="10 min",
        message="The longer of the two breaks if you can swing it. Block 3's payoff lands harder if the room comes back fresh.",
        accent=Theme.TEAL,
        page=n(),
        notes="""
[USE THE BREAK] Stay on `Release` for the presenter machine. In XAE, expand `FillingLine_Composition` and open its I_AlarmHandler.TcPOU and FB_AlarmHandler_LineFault.TcPOU side by side.

[SECOND LAPTOP] If you have one: open MAIN.TcPOU on it. The MAIN swap demo in Block 3 is the workshop's emotional climax — preparing it now saves a switching delay later.
""".strip(),
    )

    # ===== BLOCK 3 — Stage 3 — Composition =================================

    add_section_divider(
        prs,
        block_label="Block 3",
        title="Stage 3 — Composition",
        time_budget="70 min",
        summary="Build the line from interface-typed building blocks.\nCR-2 — the killer requirement — becomes a one-line swap.",
        accent=Theme.VIOLET,
        notes="""
[BEFORE] Presenter on `Release`, `FillingLine_Composition` expanded. File tree visible — 18 source files in three directories (Interfaces/, BuildingBlocks/, Stations/).

[FRAMING] This block is the EMOTIONAL PAYOFF of the workshop. Pace it so the room has time to FEEL the win, not just observe it. Don't rush past CR-2.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The composition paradigm",
        bullets=[
            "Origin — Gang of Four 1994; SOLID 2000s.",
            "Mental model — small focused FBs talk through interfaces.",
            "TwinCAT — INTERFACE, IMPLEMENTS, FB references typed by interface, FB_init for DI.",
            "Promise — variation by injection.",
            "Catch — more files, more concepts, more vocabulary.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        body_size=20,
        notes="""
[DON'T LECTURE] Read the bullets, gesture at the file tree, move on.

[SEED] "Variation by injection." That's the seed of CR-2's swap demo. Plant it now — they'll see it in 30 minutes.

[FRAMEWORK] Beckhoff USA's Core / CoreComponents / MechatronicsCore libraries. I_Cyclic, I_Diagnostic component pattern. Production code.

[IF ASKED] "Is this just dependency injection?" → "Yes. DI is one of the patterns. We'll name them all in Block 4."
""".strip(),
    )

    add_content_slide(
        prs,
        title="The file tree — 18 files. Hold the judgment.",
        bullets=[
            "5 interfaces — I_AlarmHandler, I_DataLogger, I_HmiReportable, I_Sequenceable, I_StationCore.",
            "7 building blocks — alarm handlers, loggers, mode manager, sequencers.",
            "4 stations — each composes building blocks.",
            "MAIN — wires the dependency graph.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        body_size=20,
        notes="""
[DO] Open the file tree. Walk top to bottom.

[PRE-EMPT] "This is more files than Stage 1 had." Acknowledge it explicitly.

[SAY] "Hold that judgment for one slide. The architecture's payback comes in the next 40 minutes. Don't defend it now; let CR-2 defend it."
""".strip(),
    )

    add_code_slide(
        prs,
        title="The contract — I_AlarmHandler",
        code_text="""// I_AlarmHandler.TcPOU — a contract. No implementation.

INTERFACE I_AlarmHandler

PROPERTY IsActive : BOOL    // is an alarm currently latched?
PROPERTY StopsLine : BOOL   // should this alarm stop the line?
                            // (TRUE for line faults, FALSE for quality flags)

METHOD Raise
VAR_INPUT
    Code   : INT;
    Text   : STRING(80);
END_VAR

METHOD Acknowledge
END_METHOD

// Anyone who implements this satisfies the contract.
// Stations depend on I_AlarmHandler — they never know which implementation
// they have. That's the seam where CR-2's swap will happen.""",
        language="TwinCAT INTERFACE",
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
[DO] Open I_AlarmHandler.TcPOU on the projector. Walk the four members.

[KEY LINE] "Stations depend on I_AlarmHandler — they never know which implementation they have. That's the seam where CR-2's swap will happen."

[FORESHADOW] Don't explain the swap yet. Just plant the seam. Reveal in 25 minutes.
""".strip(),
    )

    add_two_col_slide(
        prs,
        title="Two implementations — same shape, opposite policy",
        left_title="FB_AlarmHandler_LineFault",
        left_items=[
            "StopsLine — TRUE.",
            "Raise() — latches, blocks downstream.",
            "Use for — real faults that should stop the line.",
            "Tells the station — \"halt.\"",
        ],
        right_title="FB_AlarmHandler_QualityFlag",
        right_items=[
            "StopsLine — FALSE.",
            "Raise() — sets Code/Text, does NOT latch.",
            "Use for — quality defects that feed sortation.",
            "Tells the station — \"note this part; keep running.\"",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        body_size=17,
        notes="""
[DO] Open both files side by side on the projector. Walk the symmetry.

[KEY LINE] "Same contract, opposite behavior. The station code can't tell them apart. The behavior change happens in MAIN, not in the station."

[FORESHADOW] "In 25 minutes, CR-2 is going to ask 'change Inspect's alarm policy.' We'll do it by changing one line in MAIN."
""".strip(),
    )

    add_code_slide(
        prs,
        title="A composed station — FB_StationFill",
        code_text="""FUNCTION_BLOCK FB_StationFill IMPLEMENTS I_HmiReportable, I_Sequenceable

VAR
    Mode    : REFERENCE TO FB_ModeManager;
    Alarm   : I_AlarmHandler;        // <-- depends on the INTERFACE
    Logger  : I_DataLogger;          // <-- same
    Seq     : FB_StepSequencer;
END_VAR

METHOD FB_init : BOOL
VAR_INPUT
    bInitRetains  : BOOL;
    bInCopyCode   : BOOL;
    ModeRef       : REFERENCE TO FB_ModeManager;
    AlarmHandler  : I_AlarmHandler;     // <-- injected at construction
    DataLogger    : I_DataLogger;       // <-- injected at construction
END_VAR
THIS^.Mode  REF= ModeRef;
THIS^.Alarm := AlarmHandler;
THIS^.Logger := DataLogger;

// The station never constructs its dependencies. It receives them.
// That's dependency injection — the seam that makes CR-2 trivial.""",
        language="Structured Text",
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
[DO] Open FB_StationFill on the projector. Walk the VAR block first — point at I_AlarmHandler / I_DataLogger fields. Then walk FB_init — point at AlarmHandler / DataLogger parameters.

[KEY LINE] "The station never constructs its dependencies. It receives them. That's dependency injection — the seam that makes CR-2 trivial."

[IF ASKED] "What's REFERENCE TO?" → "TwinCAT's pointer-with-syntax-sugar. Use REF= to bind, then dereference with .field syntax. We use it for FB_ModeManager because there's exactly one shared instance."
""".strip(),
    )

    add_code_slide(
        prs,
        title="MAIN — the construction is the architecture",
        code_text="""PROGRAM MAIN
VAR
    Mode          : FB_ModeManager;
    LineFault     : FB_AlarmHandler_LineFault;
    QualityFlag   : FB_AlarmHandler_QualityFlag;   // <-- both available
    CycleLogger   : FB_CycleDataLogger;

    Fill          : FB_StationFill(
                        ModeRef       := Mode,
                        AlarmHandler  := LineFault,        // <-- swap point
                        DataLogger    := CycleLogger);
    Cap           : FB_StationCap(
                        ModeRef       := Mode,
                        AlarmHandler  := LineFault);
    Label         : FB_StationLabel(
                        ModeRef       := Mode,
                        AlarmHandler  := LineFault);
    Inspect       : FB_StationInspect(
                        ModeRef       := Mode,
                        AlarmHandler  := LineFault);       // <-- this line
END_VAR
// Read MAIN top-to-bottom: it IS the wiring diagram for the line.""",
        language="Structured Text",
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
[DO] Open MAIN on the projector. Walk the construction calls. Highlight `AlarmHandler := LineFault` on Inspect — call it the "swap point."

[KEY LINE] "Read MAIN top-to-bottom — it IS the wiring diagram for the line. In Stage 1, MAIN was 'instantiate stations.' In Stage 3, MAIN is 'wire the dependency graph.' The architecture is realized at construction."

[SETUP] This sets up CR-2 directly. The audience should be ready to predict what the swap looks like.
""".strip(),
    )

    add_content_slide(
        prs,
        title="SOLID — concretely, in this codebase",
        bullets=[
            "S — Single Responsibility — one job per FB.",
            "O — Open/Closed — add new alarm strategy, existing code untouched.",
            "L — Liskov Substitution — any I_AlarmHandler works anywhere.",
            "I — Interface Segregation — HMI sees I_HmiReportable only.",
            "D — Dependency Inversion — stations depend on I_AlarmHandler.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        body_size=20,
        notes="""
[DO] Walk SOLID once, slowly, with the codebase as the example. This is the vocabulary attendees take to customer conversations.

[FAE-FRAMING] For an FAE audience, SOLID is review at the conceptual level. What's new is mapping each principle to a SPECIFIC TwinCAT file they just walked through.

[ASK — if you have time] "Which SOLID principle is doing the heavy lifting in this codebase?" Best answer is D (Dependency Inversion) — that's the seam that makes CR-2 trivial. L (Liskov) is the property that makes D safe.
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 3 · 3A pre-emptive pushback",
        customer_q="Eighteen files for a 4-station machine? You've got to be kidding.",
        fae_a="You're right — for 4 stations, this is overkill. The architecture pays back when the codebase grows. If you're shipping one machine and walking away, Stage 1 is the right answer. If you're building a product family, Stage 3 is the prerequisite for sane long-term maintenance.",
        page=n(),
        notes="""
[ACKNOWLEDGE] Critical to acknowledge — for the workshop's 4-station example, the customer is RIGHT. Stage 3 IS overkill at this scale.

[FRAMING] Stage 3's payoff is at scale and over time. For a one-off machine, Stage 1 is correct. For a product family that ships 50 variants over 5 years, Stage 3 is the only sane answer.

[DON'T OVERSELL] The workshop's value is the trade-off vocabulary, not religion.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-1 — the composition way (Fill's exception comes free)",
        branch_compare="Release...cr1-applied --stat -- NEM2026/FillingLine_Composition/",
        headline_stat="2 files  ·  +19  −6",
        takeaways=[
            "Just modify FB_ModeManager. Stations are not touched.",
            "Fill's mid-cycle exception — automatic.",
            "The abstraction already encoded the right behavior.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3B  ·  CR-1 hands-on (10 min)",
        page=n(),
        notes="""
[DO] Read the requirement: same Pause requirement as Stage 1. 5-minute timer. The realization comes fast: just modify FB_ModeManager.

[ASK] "Why is the Fill mid-cycle exception automatic in this architecture?"

[ANTICIPATED ANSWER] Fill's state-10 logic gates on `Accumulated >= TargetVolume`, not on `AllowRun`. The right gating point was already in place. CR-1 didn't have to add new gating logic anywhere because the abstraction encoded the right behavior already.

[PUSHBACK if asked] "Sure, this works for Pause because Pause maps cleanly to a mode. What about a feature that doesn't?" → "Then you do the work to find the right abstraction. Composition isn't magic — it requires careful design. Stage 1 + 2 pay per-CR. Stage 3 pays up front and reaps savings."
""".strip(),
    )

    add_section_divider(
        prs,
        block_label="Block 3 · 3C",
        title="CR-2 — the headline swap demo",
        time_budget="20 min  ·  the workshop's emotional payoff",
        summary="One line in MAIN. Watch.\nThen pause. Don't fill the silence.",
        accent=Theme.VIOLET,
        notes="""
[PACE CAREFULLY] This is the workshop's emotional payoff.

[SAY] Read CR-2 again: "Inspect: non-faulting alarm AND parallel state-10. Same as Stage 1 (60 inline lines) and Stage 2 (the override mess). Apply it the composition way."

[DEMO FIRST] On the presenter machine, before they try. Next slide is the swap script.
""".strip(),
    )

    add_code_slide(
        prs,
        title="The swap — one line in MAIN",
        code_text="""// MAIN.TcPOU — find this line:

Inspect       : FB_StationInspect(
                    ModeRef       := Mode,
                    AlarmHandler  := LineFault);     // <-- this

// Change to:

Inspect       : FB_StationInspect(
                    ModeRef       := Mode,
                    AlarmHandler  := QualityFlag);   // <-- this

// Save. Build.
//
// Inspect's behavior just changed: alarms are now non-latching,
// the line keeps running on defect. NO INSPECT CODE WAS MODIFIED.""",
        language="Structured Text",
        accent=Theme.VIOLET,
        eyebrow="Block 3 · CR-2 the headline swap",
        page=n(),
        notes="""
[DEMO LIVE] The slide is the script — the demo is the lesson.

[SEQUENCE]
1. Open MAIN. Find the line.
2. Change LineFault to QualityFlag.
3. Save. Build.
4. PAUSE. Don't speak. Let the implication land. Count to 10 silently.

[AFTER THE SILENCE]
- ASK: "Did Inspect's behavior just change?" (Yes — alarms are non-latching, line keeps running.)
- ASK: "Did we modify any Inspect code?" (No.)
- ASK: "How is this possible?" (Because the alarm strategy is INJECTED, not hardcoded. Inspect depends on I_AlarmHandler — anything implementing that interface plugs in.)

[THE SILENCE IS THE LESSON.] Don't fill it.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 3 · the workshop's central claim",
        quote="Stage 1 CR-2: 92 lines of inline rewrite.\nStage 2 CR-2: 121 lines of override fight.\nStage 3 CR-2: ONE LINE.",
        attribution="Same requirements, three architectures, different blast radius.",
        accent=Theme.VIOLET,
        page=n(),
        on_dark=True,
        notes="""
[HEADLINE] Workshop's central claim. Read it slowly. Repeat it. This is the line attendees take home.

[SAY] "If only one slide of the workshop sticks, this is it. The 92 → 121 → 1 progression is the receipt for the entire 4 hours."

[PUSHBACK — the customer-facing version] "You're cherry-picking the example. CR-2 is designed to make composition look good." → "It's designed to be REALISTIC, not to make composition look good. Real customers ask for non-faulting alarms and parallel coordination on specific stations all the time. The point isn't that Stage 3 looks good in this CR — it's that CR-1, CR-2, AND CR-3 all look good in Stage 3. Three different shapes of cross-cutting requirement, three different costs, every one cheaper. That's pattern recognition, not cherry-picking."
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-2 hands-on — the parallel sequencer",
        bullets=[
            "Compose FB_ParallelSequencer alongside FB_StepSequencer.",
            "Configure for 2 branches in FB_init. Rework state 10.",
            "Composition, not rewriting.",
            "Final diff — 2 files, ~30 lines added.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · CR-2 hands-on (10 min)",
        page=n(),
        body_size=20,
        notes="""
[DO] After the swap demo, hand them the parallel-sequencer half. 10-minute timer.

[PATTERN] What they're applying: COMPOSE a new building block (FB_ParallelSequencer) alongside an existing one (FB_StepSequencer). Not rewriting; composing.

[WHEN DONE] `git switch cr2-applied` and show `git diff Release --stat -- NEM2026/FillingLine_Composition/`. ~30 lines added in 2 files.

[PACING] If behind, skip this hands-on. The reveal moment is the swap on the presenter screen — that's the lesson. The parallel sequencer is supplementary.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-3 — DI all the way",
        branch_compare="Release...cr3-applied --stat -- NEM2026/FillingLine_Composition/",
        headline_stat="3 files  ·  +32  −11",
        takeaways=[
            "Add I_DataLogger field + FB_init param to Fill and Inspect only.",
            "Cap and Label keep their 4-arg signature — DON'T touch them.",
            "Logger swap (in-memory → file → DB) — replace one FB. Stations don't change.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3D  ·  CR-3 hands-on (10 min)",
        page=n(),
        notes="""
[DO] Read the requirement. 5-minute timer. The path: add I_DataLogger field + FB_init param to Fill and Inspect only.

[ASK] "Where does Cap's logger storage live now?" → nowhere. Cap doesn't have the field.

[ASK] "What changes if we swap from in-memory buffer to file-based logger?" → only FB_CycleDataLogger is replaced. Stations don't change. MAIN doesn't change.

[COMPARE] Stage 2's logger refactor cost: base + every override + LogCycleData helper. Stage 3: just the building block.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Even composition can be applied poorly",
        bullets=[
            "git switch stage-3-broken — Pause via per-station guards (legacy demo branch).",
            "Compiles. Runs. Halts Fill mid-cycle.",
            "The right architecture nudges, doesn't force.",
            "Right answer: 1-file diff. Wrong answer: 5-file diff.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3E  ·  the wrong-way branch (5 min)",
        page=n(),
        body_size=20,
        notes="""
[DO] Show stage-3-broken on the projector (this demo uses the legacy single-PLC branch — the wrong-way state was preserved there). Walk the per-station guards. Then switch back to `cr1-applied` and show FillingLine_Composition's FB_ModeManager-only change.

[LESSON] The right architecture makes the right thing easy and the wrong thing visible. Right answer is loud and small; wrong answer is loud and large.

[PUSHBACK] "So composition can be done wrong too. What's the point?" → "Every paradigm can be done wrong. The point is which one MAKES THE RIGHT THING EASY AND THE WRONG THING VISIBLE. Stage 1's right answer is 'modify every station' — easy to do, easy to drift. Stage 3's right answer is 'modify the shared service' — also easy, and the wrong-way alternative is loud (5-file diff) instead of quiet (1-file diff)."
""".strip(),
    )

    # ===== BLOCK 4 — Scoreboard, discussion, take-home =====================

    add_section_divider(
        prs,
        block_label="Block 4",
        title="Scoreboard, discussion, take-home",
        time_budget="20 min  ·  plan to overshoot",
        summary="The numbers from the diffs go on the board.\nWhen does each stage fit your real workload?",
        accent=Theme.NAVY,
        notes="""
[FRAMING] This is where the workshop cements. Plan to overshoot the 20-minute budget if discussion is gold — that's the workshop's value.

[BEFORE] Pull up the scoreboard page on the projector OR reveal the whiteboard with cells pre-drawn.
""".strip(),
    )

    add_scoreboard_slide(
        prs,
        page=n(),
        notes="""
[DO] Walk the matrix cell-by-cell. The audience has DONE every cell — this is consolidation, not introduction.

[READ ALOUD]
- "CR-1 hits 5 files in procedural; 3 in inheritance; 2 in composition."
- "CR-2 in procedural is a 92-line inline rewrite. In inheritance it's a 121-line override fight. In composition it's a 1-line swap."
- "CR-3 looks small in procedural (13 lines) but the duplication is permanent. Inheritance fixes the duplication but adds dead weight. Composition has both proportional cost AND zero dead weight."

[NEXT SLIDE] The deeper lessons.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Reading the numbers — blast radius, not lines",
        bullets=[
            "Stage 1 — every CR touches every station.",
            "Stage 2 — base + affected children. Until pollution.",
            "Stage 3 — building block touched. Others untouched.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4A scoreboard (10 min)",
        page=n(),
        body_size=22,
        notes="""
[KEY LINE] "Lines are the visible cost. BLAST RADIUS is the real cost."

[CONTEXT — examples to work in]
- Stage 1 wins on raw lines for CR-3 (13). But those 13 lines are duplicated identically. The duplicate is permanent.
- Stage 2 CR-2 only adds ~80 lines of override, but those 80 lines re-implement mode resolution and alarm-ack from scratch. The 'lines' are cheap; the FRAGILITY is expensive.

[FAE TAKEAWAY] The blast-radius framing is the language attendees take to customer conversations. Mark it. Repeat it.

[VISUAL ANCHOR] If you have a whiteboard: write "BLAST RADIUS" in big letters next to the scoreboard matrix.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The quiet long-tail value — testability",
        bullets=[
            "Stage 1 / 2 stations — entangled with I/O. Hard to test.",
            "Stage 3 stations — accept dependencies at construction.",
            "Today — PlcTestSuite + DI + mocks → deterministic tests.",
            "Coming — Beckhoff-native framework. TcUnit also exists. Both heavier lifts than PlcTestSuite.",
            "If your shop wants CI for PLC code, this is the prerequisite.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4A scoreboard",
        page=n(),
        body_size=18,
        notes="""
[FRAMING] The testability argument is the workshop's quiet long-tail value. Some attendees will care about this MORE than the blast-radius argument.

[CONTEXT — to weave in]
"In a PlcTestSuite test you can construct FB_StationFill with mocks: MockMode, MockAlarm (QualityFlag — never latches), Logger (inspect buffer after each cycle). Drive MockMode.ModeAuto := TRUE, set PartPresent := TRUE, call Execute() repeatedly, assert against Logger._Buffer. No real I/O. No real alarms. Deterministic."

[FRAMEWORK LANDSCAPE — be ready, FAEs will ask]
- PlcTestSuite (SimmelFlo, OSS) — what we use today. Lightest install, fastest to demo.
- TcUnit (community, OSS) — the older / better-known option. More setup, more ceremony.
- Beckhoff-native — first-party framework on the way. Like TcUnit, expect a heavier lift than PlcTestSuite. Worth tracking for shops standardizing later.
- The architectural lesson is framework-independent: composition + DI is what makes ANY of them testable. Stage 1 / Stage 2 stations don't have the seam regardless of which framework you pick.

[IF AHEAD] Springboard into the bonus PlcTestSuite demo (see backup slides).

[IF ON TIME] Deliver as one sentence and move on. Next slide is the discussion that earns the workshop.
""".strip(),
    )

    add_three_col_slide(
        prs,
        title="Which stage for which shop?",
        columns=[
            ("Stage 1 — Procedural is right for", [
                "Single-machine integrators",
                "Panel shops",
                "One-engineer teams",
                "Short-lifespan code",
                "Ship-and-walk-away contracts",
            ], Theme.AMBER),
            ("Stage 2 — Inheritance is right for", [
                "Homogeneous machine families",
                "Mid-sized teams",
                "Long-lifespan, medium variation",
                "Teams comfortable with EXTENDS / SUPER",
            ], Theme.TEAL),
            ("Stage 3 — Composition is right for", [
                "OEMs building product families",
                "Multi-engineer teams",
                "Multi-customer variation",
                "Long-lifespan codebases",
                "Shops moving toward CI / TDD for PLC",
            ], Theme.VIOLET),
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4A discussion (the most important one)",
        page=n(),
        notes="""
[MOST IMPORTANT DISCUSSION OF THE WORKSHOP]

[ASK] "Walk back to your shop. What machine, codebase, or customer is each stage right for? Be specific. Name names if you can."

[DO] Take answers. Encourage debate. The slide is the framing — the workshop value is the customer-specific application.

[IF ROOM IS SHY — prime with]
- "Anyone here own a single-machine codebase that Stage 1 is fine for?" → hands.
- "Anyone working on a product family where Stage 3 is the prerequisite?" → hands.
- "Anyone in the messy middle where Stage 2 is what you're already doing and you're feeling the limits?" → most hands.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Customer-conversation rehearsal",
        bullets=[
            "You'll go back. Someone will say \"this is overkill\" or \"just give me the procedural version.\"",
            "Pick three pushbacks. Roleplay.",
            "The answer isn't \"composition is always right.\"",
            "Discipline is bounded; architecture is unbounded.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4B (5 min)",
        page=n(),
        body_size=20,
        notes="""
[DO] Pick three of the deck's pushback Q&A pairs. Roleplay them with the room. Let attendees take the FAE side; you take the customer side.

[POINT] The customer-conversation rehearsal is the workshop's transferable skill. They've heard the pushbacks all day; now they practice the answers.

[PUSHBACKS WORTH PICKING — depending on audience composition]
- "This is fine. We've shipped 50 machines like this." (most universal)
- "I just need to remember to mirror base changes into Inspect's override." (the most important Q&A)
- "Eighteen files for a 4-station machine?" (the overkill objection)
- "Use multiple inheritance, then." (the technically-knowledgeable customer)

[CLOSE] "Discipline is bounded; architecture is unbounded." Repeat the line. Make sure they walk out quoting it.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Continuation kit",
        bullets=[
            "Self-paced refresher — ./serve-docs.sh, walk the stages.",
            "Teaching mode — run a 1-2 hour version for your team.",
            "Deep end — PlcTestSuite on Stage 3 vs Stage 1. Visceral.",
            "Send me one specific machine this material applies to.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4C (5 min)",
        page=n(),
        body_size=20,
        notes="""
[DO] Walk the four bullets in order.

[REAL ASK] "Send me one specific machine, project, or customer this material applies to. I want to know what you'll teach it for. That's how I make this workshop better."

[FRAMING] Senior FAEs who attend are the workshop's distribution channel — they need to teach it. Knowing what they'll teach it FOR makes the next iteration better.

[NEXT SLIDE] The personal-recommendation pattern — what makes the workshop stick.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Personal recommendations — what makes it stick",
        bullets=[
            "Send each attendee a brief follow-up — one specific recommendation tied to their team.",
            "Sarah — motion controllers. Try the I_AlarmHandler swap on test rigs.",
            "Bob — single-machine codebase. Stage 1 is fine. Try the CR-2 swap exercise on your next vendor swap.",
            "Generic advice fades. Specific advice sticks.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4C continuation",
        page=n(),
        body_size=18,
        notes="""
[FRAMING] The personal-recommendation pattern is what makes the workshop transferable. Generic advice ('use composition more') fades within a week; specific advice ('try the I_AlarmHandler swap on your test rigs next month') sticks.

[USE THIS SLIDE AS A TEMPLATE] Copy the structure: name, observed situation, specific recommended action.

[AUDIENCE-SIZE NOTE] If your audience is > 20: the personal-recommendation pattern doesn't scale. Skip the per-attendee follow-up; send a group note instead.
""".strip(),
    )

    add_closing_slide(
        prs,
        title="Become believers, then teachers",
        body="The believer part comes from doing the workshop. You did that today.\n\nThe teacher part requires three more things: run a shorter version yourself within a month; adapt the script to your audience; track customer pushback you hear that isn't in this material — send it back.\n\nThe deepest measure of this workshop's success is when an FAE who attended teaches it, and their attendees recognize themselves in Stage 1's drift the way you recognized yourselves today.",
        contact="github.com/Mark-Code-Cowboys/NEM_Workshop  ·  ./serve-docs.sh  ·  Questions welcome.",
        accent=Theme.NAVY,
        page=n(),
        notes="""
[DO] Read the body slowly.

[BOOKEND] The "recognize themselves in Stage 1's drift" line is the emotional bookend to the CR-1 reveal in Block 1. Pull the thread explicitly:

"Remember the silence in the room when half of you realized you'd copied from a station with one ack style? When you teach this, your attendees will have that same silence. That's the workshop working."

[Q&A] Immediately after. The workshop is technically over but the discussion is half the value — let it run.
""".strip(),
    )

    # ===== Backup / facilitator reference ==================================

    add_section_divider(
        prs,
        block_label="Backup",
        title="Facilitator reference (skip in live presentation)",
        time_budget="reference  ·  not for projection",
        summary="Pacing levers. PlcTestSuite demo script. Materials. Shorter versions.",
        accent=Theme.NAVY,
        notes="""
[NOT FOR LIVE] Backup slides are reference material for the FAE running the workshop. Do NOT advance through them during the live class. Hide from the slide order if presenting from a printed agenda.

[STILL IN THE DECK BECAUSE] The deck doubles as a teaching kit for FAEs reusing the material later. Backup section serves them.
""".strip(),
    )

    add_two_col_slide(
        prs,
        title="Pacing levers — what to cut, what to add",
        left_title="If you're 15+ min behind",
        left_items=[
            "Block 2 CR-3 — cut hands-on. Just show the diff.",
            "Block 1 debrief — tighten. Show matrix; let audience scan.",
            "Block 3 CR-2 — demo the swap, skip the parallel sequencer.",
            "Block 4 4A — compress to a 2-min walk-through.",
        ],
        right_title="If you're ahead",
        right_items=[
            "Block 4 4B — extend customer-conversation rehearsal.",
            "Show patterns.md — name Strategy / Template Method / DI.",
            "Demo stage-3-broken (legacy branch) — why wrong even though it compiles.",
            "PlcTestSuite demo — most powerful extension. See next slide.",
        ],
        accent=Theme.NAVY,
        left_accent=Theme.CRIMSON,
        right_accent=Theme.NAVY,
        eyebrow="Backup  ·  facilitator reference",
        page=n(),
        body_size=15,
        notes="""
[USE DURING BREAKS] Recalibrate against the schedule.

[MOST COMMON MISTAKE] Trying to cover all 9 scoreboard cells in equal depth. CR-2 in every stage is the spine; CR-1 and CR-3 are illustrations. If you're behind, compress CR-3 first.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Bonus — PlcTestSuite demo (only if class finishes early)",
        bullets=[
            "When — 20+ min ahead at Block 4, runtime available, room is engaged.",
            "Branch — stage-3-complete-tests. Library — PlcTestSuite (separate install).",
            "2 min — read 'Why composition is testable' from testing.md.",
            "5 min — show Test_QualityFlag_StopsLineIsFalse. Six lines = Liskov.",
            "5 min — show Test_FillStation_HappyPath_CompletesCycle. The DI seam IS the testing seam.",
            "5 min — if you have a runtime: build, login, RunTests := TRUE, show TEST_Result.xml.",
            "Why PlcTestSuite — TcUnit and the upcoming Beckhoff-native framework are heavier installs.",
        ],
        accent=Theme.NAVY,
        eyebrow="Backup  ·  bonus content",
        page=n(),
        body_size=14,
        notes="""
[WHY PLCTESTSUITE, NOT TCUNIT, NOT THE BECKHOFF FRAMEWORK]
- PlcTestSuite is the lightest install — single .library file. Demoable in a workshop slot.
- TcUnit works fine but is a heavier setup; you spend the workshop installing it instead of teaching it.
- The first-party Beckhoff framework is in flight — when it ships, it'll likely be the recommendation for shops standardizing on Beckhoff tooling. Until then, PlcTestSuite is the path of least resistance.
- Whichever framework attendees pick later, the architectural lesson stays the same: only Stage 3 has the DI seam that any of them needs.

[WHY BONUS, NOT CORE]
1. PlcTestSuite is a separate library install (5+ min per machine if attendees don't have it).
2. Only works on Stage 3 code. Demonstrating WHY it doesn't work on Stage 1 or 2 takes extra time.
3. Needs a running TwinCAT runtime. Review-only attendees can't actually execute.

[FRAME AS] "This is what the rest of software engineering takes for granted. Stage 3 makes it available to control code. Composition isn't optional architecture if your shop wants CI for PLC — it's the prerequisite."

[LESSON IT SURFACES NATURALLY] "What would it take to test a Stage 1 station? A Stage 2 station? Why is this only possible on Stage 3?" → Stage 1 and 2 stations don't have the dependency-injection seam, so there's nowhere to plug in mocks.

[IF YOU DON'T GET TO IT] Send testing.md link in post-workshop follow-up. The architectural lesson lands fully without the testing demo.
""".strip(),
    )

    add_two_col_slide(
        prs,
        title="Materials checklist",
        left_title="Day-of",
        left_items=[
            "Repo cloned, all branches fetched.",
            "TwinCAT XAE 3.1.4026+, two instances open.",
            "Browser with the scoreboard bookmarked.",
            "Local docs site (./serve-docs.sh) — wifi backup.",
            "Whiteboard or large sticky notes for the physical scoreboard.",
            "Timer for the timed exercises.",
        ],
        right_title="Day-after",
        right_items=[
            "Send each attendee a personal recommendation.",
            "Send the repo URL and scoreboard compare links.",
            "Solicit feedback in the workshop's chat / channel.",
            "Optional — only if you ran testing demo: PlcTestSuite link.",
        ],
        accent=Theme.NAVY,
        eyebrow="Backup  ·  facilitator checklist",
        page=n(),
        body_size=15,
        notes="""
[PRINT AND TAPE] Reference card for day-of and day-after. Print it; tape it next to your laptop.

[PHYSICAL SCOREBOARD MATTERS] Watching the cells get filled in on a whiteboard as exercises complete creates a different kind of engagement than a static slide.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Shorter versions — when 4 hours isn't on the table",
        bullets=[
            "30 min — \"the one demo.\" Stage 3 CR-2 swap only.",
            "1 hr — \"the methodology compare.\" Stage 1 + Stage 3 CR-1; skip Stage 2.",
            "2 hr — \"the workshop, compressed.\" Cut CR-3 in every stage.",
            "4 hr — \"the full workshop.\" This deck.",
        ],
        accent=Theme.NAVY,
        eyebrow="Backup  ·  facilitator reference",
        page=n(),
        body_size=20,
        notes="""
[USE CASE]
- 30 min — customer pitches. Plant a single seed: runtime-swappable strategies are real and useful in TwinCAT.
- 1 hr — internal team training. Same requirement, three different costs.
- 2 hr — intermediate audience that doesn't need every cell of the scoreboard.

[NONE INCLUDE THE TESTING DEMO] Reserved for the 4-hour version, only when ahead of schedule.

[IF AN FAE ASKS] "Which version should I run?" → ask back: "What's your audience and what time do you have?" Then pick from this list.
""".strip(),
    )

    return page


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Template not found: {TEMPLATE_PATH}")

    prs = Presentation(str(TEMPLATE_PATH))
    _index_layouts(prs)
    _strip_example_slides(prs)

    total = build_slides(prs)

    prs.save(str(OUTPUT_PATH))
    print(f"Wrote {OUTPUT_PATH}  ·  {total} slides  ·  {OUTPUT_PATH.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
