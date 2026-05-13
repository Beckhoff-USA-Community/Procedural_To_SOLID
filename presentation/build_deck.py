"""
Build the NEM 2026 workshop deck — "From Procedural to SOLID".

Builds on top of the Beckhoff SPT template (`../SPT Framework_03_16_23.pptx`),
inheriting its slide masters, layouts, theme colors ("Test_Beckhoff_2020_v2"),
and chrome. Custom overlays (code panels, diff stats, pushback Q&A panels,
scoreboard) sit inside the template's body area and use the Beckhoff palette.

Run:
    .venv/bin/python build_deck.py

Output:
    NEM2026_workshop.pptx (sibling of this file)

Source of truth for content: docs/instructor.md on `main`.
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

    # Content area carved out by the template (Title at y=0.49 h=0.69;
    # Body at y=1.19 w=11.09 h=5.83; chrome occupies right column 11.09→13.33
    # and footer band 7.02→7.50).
    BODY_X      = Inches(0.0)
    BODY_Y      = Inches(1.19)
    BODY_W      = Inches(11.09)
    BODY_H      = Inches(5.83)
    SAFE_X      = Inches(0.40)
    SAFE_W      = Inches(10.30)

    # Beckhoff palette (extracted from theme1.xml)
    BECKHOFF_BLUE  = RGBColor(0x2D, 0x76, 0xAD)   # accent2 — primary brand
    BECKHOFF_RED   = RGBColor(0xEF, 0x00, 0x00)   # accent4 — emphasis / warning
    DARK_RED       = RGBColor(0x77, 0x00, 0x00)   # accent6
    SLATE_DARK     = RGBColor(0x41, 0x4D, 0x5C)   # accent3
    SLATE          = RGBColor(0x62, 0x71, 0x86)   # dk2
    SLATE_LIGHT    = RGBColor(0xB3, 0xBC, 0xC8)   # accent1
    LIGHT_PANEL    = RGBColor(0xE5, 0xE8, 0xEC)   # lt2
    PALE_BLUE      = RGBColor(0xB5, 0xD4, 0xEC)   # accent5
    BLACK          = RGBColor(0x00, 0x00, 0x00)
    WHITE          = RGBColor(0xFF, 0xFF, 0xFF)

    # Custom neutrals for overlays
    CODE_PANEL_BG  = RGBColor(0x1B, 0x1F, 0x23)   # near-black for code blocks
    CODE_FG        = RGBColor(0xE6, 0xE8, 0xEB)
    BODY_INK       = RGBColor(0x24, 0x2A, 0x33)
    MUTED_INK      = RGBColor(0x62, 0x71, 0x86)
    RULE_GRAY      = RGBColor(0xC8, 0xCE, 0xD6)

    # Semantic aliases used in build_slides() — preserve old call sites
    AMBER   = SLATE_DARK     # Stage 1 — procedural (the legacy)
    TEAL    = SLATE          # Stage 2 — inheritance (the bridge)
    VIOLET  = BECKHOFF_BLUE  # Stage 3 — composition (the brand climax)
    NAVY    = BLACK          # Block 0/4 + section framing
    CRIMSON = BECKHOFF_RED   # Pre-emptive pushback warnings

    # Type — match template's Arial
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
    size=17,
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
    """Index layouts by name from master 0, called once per build."""
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
    """Set placeholder text and let the layout style it (font, color, size)."""
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == ph_idx:
            ph.text_frame.text = text
            return ph
    return None


def _remove_placeholder(slide, ph_idx):
    """Remove a placeholder by idx so it doesn't render its default text."""
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx == ph_idx:
            sp = ph._element
            sp.getparent().remove(sp)
            return


def _set_title(slide, title):
    """Title placeholder is always idx=0 in this template."""
    return _set_placeholder_text(slide, 0, title)


def _set_body(slide, items, *, bullet_color=None, size=17, bold_first_token=True):
    """Populate the BODY placeholder (idx=15) with bullets, styled by template
    but with run-level overrides for bullet color and bold-first-token."""
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

    # Add subtitle + tagline beneath the title placeholder
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
    """Section dividers use the 'Contents' layout — full template chrome,
    title at top, custom big-typography block in the body area."""
    slide = _new(prs, "Contents")
    _set_title(slide, block_label)

    # Remove the default body placeholder; we'll render our own large layout
    _remove_placeholder(slide, 15)

    # Accent stripe down the left of the body area
    add_rect(slide, Inches(0.0), Inches(1.30), Inches(0.18), Inches(5.6), accent)

    # Big title
    add_text(
        slide,
        Inches(0.45), Inches(1.40), Inches(10.5), Inches(1.7),
        title,
        size=44, bold=True, color=Theme.SLATE_DARK, line_spacing=1.05,
    )

    # Time budget line
    add_text(
        slide,
        Inches(0.45), Inches(3.20), Inches(10.5), Inches(0.5),
        time_budget,
        size=16, bold=True, color=accent,
    )

    # Summary
    if summary:
        add_text(
            slide,
            Inches(0.45), Inches(3.95), Inches(10.5), Inches(2.5),
            summary,
            size=16, color=Theme.BODY_INK, italic=True, line_spacing=1.4,
        )

    add_speaker_notes(slide, notes)
    return slide


def add_content_slide(prs, title, bullets, *, accent, eyebrow=None, page=0, notes="", body_size=17):
    slide = _new(prs, "Text")
    # Eyebrow + title combined into the title placeholder
    title_with_eyebrow = title
    if eyebrow:
        title_with_eyebrow = title  # template title is single-line; render eyebrow above as overlay
    _set_title(slide, title_with_eyebrow)

    # Eyebrow as a small overlay above the title placeholder area
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

    # Vertical rule
    add_rect(slide, Inches(x_left + col_w + gap / 2 - 0.005), Inches(1.5),
             Inches(0.01), Inches(5.3), Theme.RULE_GRAY)

    # Left column
    add_text(
        slide, Inches(x_left), Inches(1.30), Inches(col_w), Inches(0.4),
        left_title.upper(), size=12, bold=True, color=left_accent,
    )
    add_bullets(
        slide, Inches(x_left), Inches(1.80), Inches(col_w), Inches(5.0),
        left_items, size=14, color=Theme.BODY_INK, bullet_color=left_accent,
        bold_first_token=True,
    )

    # Right column
    add_text(
        slide, Inches(x_right), Inches(1.30), Inches(col_w), Inches(0.4),
        right_title.upper(), size=12, bold=True, color=right_accent,
    )
    add_bullets(
        slide, Inches(x_right), Inches(1.80), Inches(col_w), Inches(5.0),
        right_items, size=14, color=Theme.BODY_INK, bullet_color=right_accent,
        bold_first_token=True,
    )

    add_speaker_notes(slide, notes)
    return slide


def add_three_col_slide(prs, title, columns, *, accent, eyebrow=None, page=0, notes=""):
    """columns: list of (col_title, items, col_accent)."""
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
        # Header band
        add_rect(slide, Inches(x), Inches(1.30), Inches(col_w), Inches(0.45), caccent)
        add_text(
            slide, Inches(x + 0.15), Inches(1.35), Inches(col_w - 0.3), Inches(0.4),
            ctitle, size=12, bold=True, color=Theme.WHITE,
        )
        add_bullets(
            slide, Inches(x + 0.05), Inches(1.95), Inches(col_w - 0.1), Inches(4.9),
            citems, size=12, color=Theme.BODY_INK, bullet_color=caccent,
            line_spacing=1.25, para_space_before=3,
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
        # Dark panel covers the body area
        add_rect(slide, Inches(0.0), Inches(1.19), Inches(11.09), Inches(5.83), Theme.SLATE_DARK)
        text_color = Theme.WHITE
        sub_color = Theme.LIGHT_PANEL
        mark_color = Theme.BECKHOFF_BLUE
    else:
        add_rect(slide, Inches(0.0), Inches(1.19), Inches(11.09), Inches(5.83), Theme.LIGHT_PANEL)
        text_color = Theme.SLATE_DARK
        sub_color = Theme.SLATE
        mark_color = accent

    # Use the title placeholder for the kicker (template-styled at top)
    _set_title(slide, kicker)

    # Oversized opening quotation mark
    add_text(
        slide, Inches(0.10), Inches(1.20), Inches(2.0), Inches(2.2),
        "“", font=Theme.SERIF_ACCENT, size=160, color=mark_color, align=PP_ALIGN.LEFT,
    )

    add_text(
        slide, Inches(1.50), Inches(1.80), Inches(9.30), Inches(4.0),
        quote, size=26, color=text_color, italic=True, line_spacing=1.30,
    )

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

    # Branch compare (small monospace)
    add_text(
        slide, Inches(0.0), Inches(1.30), Inches(10.95), Inches(0.40),
        f"git diff  {branch_compare}",
        font=Theme.MONO, size=12, color=Theme.MUTED_INK,
    )

    # Headline stat
    add_text(
        slide, Inches(0.0), Inches(1.85), Inches(10.95), Inches(1.4),
        headline_stat, size=58, bold=True, color=accent, line_spacing=1.0,
    )

    # Thin accent rule under the stat
    add_rect(slide, Inches(0.0), Inches(3.40), Inches(1.2), Inches(0.05), accent)

    add_bullets(
        slide, Inches(0.0), Inches(3.70), Inches(10.95), Inches(3.0),
        takeaways, size=15, color=Theme.BODY_INK, bullet_color=accent,
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

    # Customer Q card
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
        customer_q, size=17, italic=True, color=Theme.SLATE_DARK, line_spacing=1.30,
    )

    # FAE answer card
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
        fae_a, size=16, color=Theme.WHITE, line_spacing=1.35,
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
    col_widths = [3.05, 2.65, 2.65, 2.60]   # total 10.95
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
        slide, Inches(0.0), Inches(6.50), Inches(10.95), Inches(0.5),
        "Stage 3 wins on every CR. The shape of the win matters more than the line count.",
        size=13, italic=True, color=Theme.MUTED_INK,
    )

    add_speaker_notes(slide, notes)
    return slide


def add_break_slide(prs, label, duration, message, *, accent=None, page=0, notes=""):
    accent = accent or Theme.BECKHOFF_BLUE
    slide = _new(prs, "Empty")
    # Dark panel covers the body area
    add_rect(slide, Inches(0.0), Inches(1.19), Inches(11.09), Inches(5.83), Theme.SLATE_DARK)
    _set_title(slide, label)

    add_text(
        slide, Inches(0.0), Inches(1.50), Inches(10.95), Inches(0.50),
        "BREAK", size=14, bold=True, color=accent,
    )
    add_text(
        slide, Inches(0.0), Inches(2.20), Inches(10.95), Inches(1.7),
        duration, size=88, bold=True, color=Theme.WHITE, line_spacing=1.0,
    )
    add_text(
        slide, Inches(0.0), Inches(4.50), Inches(10.95), Inches(2.0),
        message, size=18, italic=True, color=Theme.LIGHT_PANEL, line_spacing=1.4,
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
        body, size=16, color=Theme.LIGHT_PANEL, line_spacing=1.4, italic=True,
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
    """Remove all slides from the template so we start with an empty deck
    but keep the masters, layouts, and theme."""
    sldIdLst = prs.slides._sldIdLst
    # Iterate over a snapshot — we mutate during the loop
    for sldId in list(sldIdLst):
        rId = sldId.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)


# ---------------------------------------------------------------------------
# Content — unchanged from the prior build (only the rendering changes)
# ---------------------------------------------------------------------------

def build_slides(prs):
    page = 0
    def n():
        nonlocal page
        page += 1
        return page

    # ------ BLOCK 0 — Welcome ----------------------------------------------

    add_title_slide(
        prs,
        title="From Procedural to SOLID",
        subtitle="Object-Oriented PLC Design in TwinCAT 3",
        tagline="A 4-hour workshop for Beckhoff FAEs and customer-training staff  ·  NEM 2026",
        accent=Theme.BECKHOFF_BLUE,
        notes="""
Welcome them into the room. This title slide is on while attendees settle. Don't speak to it; the next slide is the real opener.

When ready: confirm everyone has the repo cloned and a working XAE. Hands up. Anyone who can't build, surface that NOW — there's a 5-min Block 0 budget for env triage.

Frame in 30 seconds: "You'll build the same filling line three different ways. Same requirements at every stage. The diffs tell the story."
""".strip(),
    )

    add_content_slide(
        prs,
        title="What we're going to do for the next 4 hours",
        bullets=[
            "Same machine, three architectures — a 4-station filling line built procedurally, with inheritance, then with composition.",
            "Same three change requests at every stage — Pause mode, Inspect quality + parallel, selective logging.",
            "One running scoreboard — files touched and lines changed for every (stage × CR) cell. Nine cells total.",
            "One question we keep coming back to — when does each architectural choice actually pay off?",
            "Discussion is the whole point — you're FAEs, you'll teach this. Half the workshop's value is what gets debated in the room.",
        ],
        accent=Theme.BECKHOFF_BLUE,
        eyebrow="Block 0 · the frame",
        page=n(),
        notes="""
Read this slide aloud, slowly. The framing controls the whole day.

Key phrase: "the diffs tell the story." We are not lecturing about SOLID. We are running a controlled experiment — same inputs, three different blast radii.

Discussion-first is non-negotiable. If they sit silent, the workshop fails. Coax discussion early so the precedent is set.

Don't dive into the branch tree yet — that's the next slide.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The schedule (be honest about the stretch zones)",
        bullets=[
            "Block 0  ·  Welcome  ·  5 min  — audience check, repo confirmation",
            "Block 1  ·  Stage 1 — Procedural  ·  85 min — walkthrough, CR-1, CR-2, CR-3, debrief.  Stretch: \"Who copied from Fill?\" reveal.",
            "Break  ·  10 min",
            "Block 2  ·  Stage 2 — Inheritance  ·  70 min — refactor, CR-1, CR-2, CR-3, debrief.  Stretch: SUPER-can't-be-called moment.",
            "Break  ·  10 min",
            "Block 3  ·  Stage 3 — Composition  ·  70 min — architecture, CR-1, CR-2 swap demo, CR-3.  Stretch: let the silence land after the swap.",
            "Block 4  ·  Scoreboard + take-home  ·  20 min — methodology fit discussion, customer-conversation rehearsal.",
        ],
        accent=Theme.BECKHOFF_BLUE,
        eyebrow="Block 0",
        page=n(),
        body_size=14,
        notes="""
Walk this in 60 seconds. Don't dwell. The point is to set expectations: "We'll be done by hour 4. Breaks are real. Stretch zones are where I'm planning to spend overflow."

If anyone asks "what about the testing demo?" — answer: "Bonus content if we finish ahead. Don't count on it."

Total budget on paper is 4:30 — plan to land in 4:00.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 0  ·  opening discussion prompt",
        quote="Before we start — quickly: who here has shipped a 4-station-or-larger machine in the last year?",
        attribution="Then this workshop is calibrated for you. The pain we're about to surface is pain you've already felt.",
        accent=Theme.BECKHOFF_BLUE,
        page=n(),
        notes="""
Ask the question. Wait for hands. You should see most of the room.

Follow-up that lands the framing: "Then this workshop is calibrated for you. The pain we're going to surface is pain you've already felt — but you've probably never named it. Today we name it, score it, and rehearse what to say when a customer pushes back."

Set expectations one more time: "We move at FAE pace. But I want lots of discussion. If something feels wrong or you've seen it work differently, say so."
""".strip(),
    )

    # ------ BLOCK 1 — Stage 1 — Procedural ---------------------------------

    add_section_divider(
        prs,
        block_label="Block 1",
        title="Stage 1 — Procedural",
        time_budget="85 min  ·  walkthrough · CR-1 · CR-2 · CR-3 · debrief",
        summary="The architecture you've been writing for 20 years.\nIEC 61131-3 was designed for it. There's nothing wrong with it.\nToday we feel where it stops scaling.",
        accent=Theme.AMBER,
        notes="""
Section break. Take a breath. Switch to `stage-1-procedural` on your presenter machine before clicking past this slide.

Open all four station FBs side by side: FB_StationFill, FB_StationCap, FB_StationLabel, FB_StationInspect. The visual side-by-side is the lesson.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The procedural paradigm in one slide",
        bullets=[
            "Origin — 1970s structured programming + 1980s industrial controls. IEC 61131-3 (1993) codified it for PLCs.",
            "Mental model — a station is a function block that runs once per cycle. It owns its state. It reads inputs, runs a CASE machine, writes outputs.",
            "Why it dominates TwinCAT — the runtime, libraries, training material, and customer expectations all assume it. It's the path of least resistance.",
            "What it's good at — small machines, single integrators, code that won't outlive the contract.",
            "What it's bad at — cross-cutting changes that have to land in N stations consistently. Today we'll feel exactly that.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1A walkthrough",
        page=n(),
        notes="""
Don't read this aloud. Summarize: "This is the architecture you've been writing for 20 years. Nothing wrong with it. We're going to feel where it stops scaling."

Skip the academic origin material if the room is engaged. Spend more time on the "what it's bad at" line — that's the segue into the drift demo.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Every station has the same five sections",
        bullets=[
            "Mode block — read ModeAuto/ModeManual/ModeStop, decide whether to advance.",
            "Alarm-ack block — clear latched alarms when AlarmAck is held or pulses.",
            "Reset block — return state to 0 when Reset is held.",
            "State machine — the actual sequence (CASE).  This is the only meaningfully different section between stations.",
            "HMI mapping — copy internal state to HMI tags.",
            "Look at any two stations side by side. Sections 1, 2, 3, 5 are nearly identical. Section 4 is the only thing that varies — and section 4 is what makes the station the station.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1A walkthrough",
        page=n(),
        notes="""
Pull up Fill and Cap side by side. Walk the five sections in order. Pause on section 4 — point out that it's the only meaningfully different section. The other four are duplication waiting to happen.

This is the foundation for the next three slides on drift. Don't editorialize yet — they'll see it themselves on the next click.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Three deliberate drifts (don't fix them)",
        bullets=[
            "Drift #1 — alarm-ack edge vs level. Fill uses R_TRIG; the others use level — or vice-versa.",
            "Drift #2 — step numbering. FB_StationLabel uses 0/100/200/300; the others use 0/10/20/30.",
            "Drift #3 — dead variable. FB_StationInspect declares ManualStep : INT; that nothing reads or writes.",
            "These are pedagogical, not bugs. They're the setup for CR-1's reveal moment. Don't tidy them up before the workshop.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1A walkthrough",
        page=n(),
        notes="""
Show the drifts one at a time. The next three slides have the code excerpts.

Don't editorialize on the drift yet. Just show them. The discussion comes after CR-1 when attendees discover they've inherited the drift by copy-paste.

If anyone in the room laughs or groans during the drift reveal — that's the workshop working. Note who it was; ask them later if they have a specific story.
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
This is the most insidious of the three drifts because both implementations look reasonable in isolation. Side-by-side they're a maintenance trap.

The pedagogical point: nobody wrote buggy code. Both stations work. The system itself failed to enforce consistency — there's no way for the procedural architecture to say "all stations ack the same way."

This is the drift that catches people on CR-1. They copy the Pause guard from Fill (R_TRIG style) into Label (level style) and the inconsistency compounds.
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
END_CASE

// Both work. Neither is wrong. They diverge for no reason.""",
        language="Structured Text",
        accent=Theme.AMBER,
        eyebrow="Block 1 · drift #2",
        page=n(),
        notes="""
This is the easiest drift to laugh about. Someone clearly copied Label from a different project where 100/200/300 was the convention, and never normalized it.

The lesson: the architecture has no opinion on naming. Conventions are tribal — they live in your head, not the compiler. Stage 2's base class will normalize this for free; you'll see it in Block 2.
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
The smallest drift, but the one that makes the point cleanest: in procedural code, dead state lingers because removing it requires reading every reference everywhere. Nobody owns the cleanup.

In Stage 2 the base class won't carry ManualStep, so it can't propagate. In Stage 3 the FB has explicit dependencies; an unused field is loud.

Don't dwell — just show it and move on.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 1 · 1A discussion prompt",
        quote="Look at this code. Anyone here written something that looks like this in the last six months?",
        attribution="Anyone copied station 5 from station 4 and then had to fix four things? Hold on to that feeling — we're about to make it worse.",
        accent=Theme.AMBER,
        page=n(),
        notes="""
Run this as a three-step audience hands-up:

1. "Anyone written something that looks like this in the last six months?" → most hands.
2. "Anyone written EXACTLY five files like this?" → some hands stay up.
3. "Anyone copied station 5 from station 4 and then had to fix four things?" → more hands.

Then close: "Good. Hold on to that feeling. We're about to make it worse with CR-1."

The first reveal in the workshop is coming. Don't rush past this slide — earn the audience commitment before starting the timer.
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 1 · 1A pre-emptive pushback",
        customer_q="This is fine. We've shipped 50 machines like this. Why are we changing it?",
        fae_a="You're right — it's fine for one machine. We're going to look at what happens when the same change has to land in four files instead of one. If that's never happened to you, this workshop won't change your mind. If it has, you'll recognize the pain.",
        page=n(),
        notes="""
This is the first of ~10 pre-emptive pushback slides. The format is the same throughout: the customer's actual objection on top, the rehearsed FAE answer below.

Run this slide ONCE explicitly. After that, attendees know the format. Later pushback slides can be flashed quickly unless the room wants to dwell.

Why this one matters: it's the most common objection FAEs get from senior controls engineers. The rehearsed answer respects the customer ("you're right") before pivoting to the cost ("what happens when…"). That sequence is the customer-conversation pattern; flag it as a template.
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-1  ·  Add a Pause mode",
        bullets=[
            "Requirement — Add a global Pause input. When ModePause is TRUE, every station should hold.",
            "Exception — the Fill station must ignore Pause mid-cycle. Pausing a half-filled bottle ruins the product.",
            "Why it hurts — cross-cutting (every station), has an exception (Fill is special), feels small (one English sentence).",
            "Half-applied state to start from — git switch stage-1-broken. Compile error in MAIN tells you what's missing.",
            "15-minute timer. Don't help. Walk the room.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1B  ·  CR-1 hands-on (20 min)",
        page=n(),
        notes="""
Read CR-1 aloud verbatim. The "Fill exception" line is the trap — most attendees will miss it on first read and write a uniform Pause guard, then realize Fill needs special handling.

Switch the presenter machine to `stage-1-broken`. Show the compile error in MAIN. "30 seconds to read the broken state, then 15 minutes to fix it."

Set the timer. Walk the room. Don't help. Wait until people are ~10 minutes in before you interrupt for the reveal.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 1 · CR-1 the reveal moment",
        quote="Quick check — how many of you copied your Pause logic into Label from Cap? From Fill? From Inspect?  Now: who has a level-based AlarmAck and who has an R_TRIG?",
        attribution="That's the procedural maintenance trap. Drift you didn't even know was there. The system itself failed to enforce consistency.",
        accent=Theme.AMBER,
        page=n(),
        on_dark=True,
        notes="""
This is the workshop's first reveal. Pace it.

After ~10 minutes (when most attendees are mid-fix), interrupt and run the two questions in sequence. Mixed hands on the first; the room goes quiet on the second because some attendees realize they copied from a station with one ack style and pasted into one with the other.

Then deliver the lesson exactly as written below the quote: drift you didn't know was there, system failed to enforce consistency, you weren't being sloppy — the architecture didn't help.

Let the silence sit for 5 seconds before moving on. The realization is the lesson; don't trample it.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-1 result — the procedural blast radius",
        branch_compare="stage-1-procedural...stage-1-cr1-applied --stat",
        headline_stat="5 files  ·  +50  −13",
        takeaways=[
            "Five files modified — every station gets a ModePause input and the same Pause guard.",
            "Fill's exception — a State <> 10 check on the guard, easy to miss, easy to copy wrong.",
            "Same 25 lines of guard logic, paid four times — that's the procedural cost shape.",
            "Tomorrow's task — the next CR also pays this cost. And the next. Forever.",
        ],
        accent=Theme.AMBER,
        page=n(),
        notes="""
After attendees finish (or you call time), `git switch stage-1-cr1-applied` and `git diff stage-1-procedural --stat` on screen.

The 5 files / +50 / −13 number is what goes on the physical scoreboard whiteboard. Walk the audience to it: "this is what your codebase looks like after one CR."

Discussion prompt: "Show of hands — who got Fill's mid-cycle exception right on the first try?" Most won't. "That's not a comment on you; it's a comment on the design. The exception is buried in the same Pause-guard logic every other station uses. You couldn't write it once and apply it correctly four ways."
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 1 · CR-1 pre-emptive pushback",
        customer_q="My team's careful. We use code review. Drift won't happen.",
        fae_a="Code review against duplicated logic catches drift sometimes. Drift you don't catch is the kind that ships. The architecture either enforces consistency or it doesn't — and code review is your last line of defense, not your first.",
        page=n(),
        notes="""
The "we have process" objection. Acknowledge that process catches some drift — then sharpen the point: process catches the drift you notice. Architecture catches the drift you don't.

Pair this with the framing: "Discipline is bounded; architecture is unbounded." (You'll use that line again in Block 2.)
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-2  ·  Inspect: non-faulting alarm + parallel",
        bullets=[
            "Requirement — Inspect must flag visual defects without stopping the line. Defects feed downstream sortation, not a fault chain.",
            "AND — Inspect must trigger the camera at the same time as it pre-arms the reject pusher, not sequentially.",
            "Both changes apply only to Inspect. The other stations stay as-is.",
            "Why it hurts — two axes of variation at once. Alarm policy AND sequencer topology. Only one station, but the patterns have to coexist with the others.",
            "15-minute timer. The attempt will be: rewriting Inspect's CASE machine end-to-end.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1C  ·  CR-2 hands-on (20 min)",
        page=n(),
        notes="""
Read CR-2 aloud. Emphasize "two axes of variation at once" — this is the trickiest CR and most attendees will underestimate it.

Set the timer. Walk the room. The attempt to watch for: rewriting Inspect's CASE machine entirely, including QualityFlag/QualityCode/QualityText outputs and a CameraDone/RejectDone parallel coordination inside step 10.

When the room is wrapped: stretch the discussion. "How many of you ended up with a 60+ line rewrite of one CASE machine?" (Most.) "Now: think about the next station that needs parallel branches. How much of what you just wrote can the next person reuse?" (Almost none — the parallel coordination is buried in Inspect's CASE.)
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-2 result — the procedural inline rewrite",
        branch_compare="stage-1-procedural...stage-1-cr2-applied --stat",
        headline_stat="2 files  ·  +92  −55",
        takeaways=[
            "Inspect's CASE machine rewritten end-to-end — CameraDone / RejectDone flags inside step 10, plus a RejectDelay timer.",
            "New QualityFlag / QualityCode / QualityText outputs parallel the existing alarm fields.",
            "AlarmActive output now ORs two sources — the HMI now needs station-aware logic to interpret alarms.",
            "The parallel coordination logic is buried in Inspect's CASE. Nothing the next station can reuse.",
            "That's the second procedural cost — duplication of NEW patterns each time they appear.",
        ],
        accent=Theme.AMBER,
        page=n(),
        notes="""
Show the diff. Land the lesson on slide: this isn't just duplication of the base — it's duplication of new patterns each time they appear. Stage 2 will help with this. Stage 3 will help even more.

The pre-emptive pushback to rehearse if asked: "Why do I care that the parallel logic isn't reusable? I only have one Inspect station." → "Today, you do. Two years from now, you might have an Inspect AND a Test station that both need parallel branches. The procedural cost of CR-2 is a tax you pay every time a new station needs the same pattern."
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-3  ·  Selective cycle logging",
        bullets=[
            "Requirement — log cycle completion data (station name, step, cycle time) for Fill and Inspect only. Cap and Label don't need it.",
            "Why it hurts — feature affects some children but not all. Looks trivial. Logger implementation will probably change later.",
            "10-minute timer. The attempt will be: LogBuffer ARRAY[0..99] OF STRING(120) + LogIndex INT, identical code, copied into Fill and Inspect.",
            "It will compile. It will work. It will cost you forever.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1D  ·  CR-3 hands-on (15 min)",
        page=n(),
        notes="""
Easier CR. Read it, set the timer, let them go. Most attendees finish in 7-8 minutes.

The pedagogical trap: it looks small. They'll write 13 lines and feel done. The cost — duplication that will be paid every time the logging requirement evolves — is invisible until it bites.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-3 result — small, but defend it as fine?",
        branch_compare="stage-1-procedural...stage-1-cr3-applied --stat",
        headline_stat="2 files  ·  +13  −3",
        takeaways=[
            "Identical buffer code duplicated in Fill and Inspect. Two places to maintain.",
            "Defend it as 'fine'? Some will. Now imagine logging changes in 6 months — write to file instead of an in-memory buffer.",
            "Where do you change the code? — Two places. Forget one? — Drift.",
            "Stage 1 wins on raw line count for CR-3. Loses on every other dimension that matters.",
        ],
        accent=Theme.AMBER,
        page=n(),
        notes="""
Discussion prompt: "That looked small. Anyone want to defend it as 'fine'?" Some attendees will defend it. Let them — then sharpen.

"Now imagine the logging requirements change in six months — say we want to write to a file instead of an in-memory buffer. Where do you change the code?" (Two places.) "And if you forget one of them?" (Drift.)

Pre-emptive pushback if it comes up: "It's literally 13 lines. Stop making it a big deal." → "It's 13 lines today. The cost isn't the lines; it's the duplication. Every future change to that logic happens twice. We'll show you the same feature in Stage 3 — same lines, but only one place to change."
""".strip(),
    )

    add_content_slide(
        prs,
        title="Block 1 debrief — the year-from-now view",
        bullets=[
            "Total Stage 1 diff after all three CRs — git switch stage-1-complete && git diff stage-1-procedural --stat — 5 files, +152, −66.",
            "That's what your codebase looks like after a year of cross-cutting CRs. Five files modified, growth concentrated in Inspect, duplication on every cross-cutting concern.",
            "Stage 1 isn't broken. It works. So why are we moving on?",
            "Drift between files — you saw it on CR-1.",
            "Can't enforce consistency — the architecture has no opinion.",
            "Duplication compounds — every new CR pays the same per-station tax.",
            "Stage 2 fixes drift and consistency. We'll see what new problems it creates.",
        ],
        accent=Theme.AMBER,
        eyebrow="Block 1 · 1E debrief (15 min)",
        page=n(),
        notes="""
Switch presenter to stage-1-complete. Show the diff stat live.

The "Stage 1 isn't broken — so why are we moving on?" question is the bridge to Block 2. Take audience answers. The right ones surface naturally — capture them on the whiteboard if you have one.

Pacing lever: if you're behind, cut CR-3 hands-on (smallest CR, easiest to walk through declaratively). If you're ahead, extend the CR-1 reveal into a longer drift discussion.

Set up the next break: "10 minutes. Coffee, bathroom. Block 2 is denser — come back fresh."
""".strip(),
    )

    add_break_slide(
        prs,
        label="Block 1 → Block 2 break",
        duration="10 min",
        message="Don't shorten this. Coffee, bathroom, social conversation. The next block has the densest concept load.",
        accent=Theme.AMBER,
        page=n(),
        notes="""
Real break. Don't compress to 5 minutes — you'll pay for it in Block 2's CR-2 attention crash.

While they're out: pull `stage-2-inheritance` on the presenter machine. Open FB_StationBase and FB_StationFill in side-by-side tabs.
""".strip(),
    )

    # ------ BLOCK 2 — Stage 2 — Inheritance --------------------------------

    add_section_divider(
        prs,
        block_label="Block 2",
        title="Stage 2 — Inheritance",
        time_budget="70 min  ·  refactor walkthrough · CR-1 · CR-2 · CR-3 · debrief",
        summary="The duplication evaporates. You're a hero — for about 20 minutes.\nThen CR-2 lands and you discover the base class you just built is now the constraint.",
        accent=Theme.TEAL,
        notes="""
Section break. While reading, switch presenter to `stage-2-inheritance`. Open FB_StationBase first, then FB_StationFill alongside.

Block 2 is the trickiest to facilitate. Inheritance has real wins; don't dismiss them. But the audience has to feel where it stops working, not just be told. Pace the CR-2 reveal carefully — that's the workshop's hardest moment.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The inheritance paradigm in one slide",
        bullets=[
            "Origin — Simula 67, Smalltalk 1972, then C++/Java made it the dominant OO style for two decades.",
            "Mental model — a base class encodes shared behavior; children specialize by overriding virtual methods.",
            "TwinCAT support — EXTENDS keyword, virtual methods (METHOD on the base, override in child), THIS^ vs SUPER^ for explicit dispatch, FB_init for construction-time parameters.",
            "Framework grounding — Stage 2 builds on Beckhoff USA's SPT-Libraries (FB_ComponentBase pattern). Production-grade, not academic.",
            "The promise — write the common path once. The catch — the common path becomes a constraint when ANY child needs to opt out.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2A walkthrough",
        page=n(),
        notes="""
Don't lecture this. Read the bullets, gesture at the FB_StationBase tab, and move on.

The line that matters: "the common path becomes a constraint when any child needs to opt out." That's the seed of the CR-2 lesson — plant it now, water it later.

If anyone asks "why FB_init?" — short answer: it's TwinCAT's constructor, runs once at instantiation, takes parameters that never change. Use it for injecting names, sizes, references that the FB will hold for its lifetime.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Same code, same behavior, different architecture",
        bullets=[
            "FB_StationFill went from ~110 lines to ~65. The shrinkage moved into FB_StationBase.",
            "Mode block — gone from each child, now on the base. One implementation; every station gets it.",
            "Alarm-ack block — gone from each child. Base normalizes to R_TRIG for everyone — drift fixed.",
            "Reset block — gone from each child. One implementation.",
            "Step numbering — Label normalized to 0/10/20/30. Drift #2 fixed.",
            "Dead ManualStep — wasn't on the base. Doesn't propagate. Drift #3 fixed.",
            "What's left in the child — the actual sequence (the only thing that varies) and a couple of overrides.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2A walkthrough",
        page=n(),
        notes="""
Open FB_StationFill. Walk the audience through the shrinkage. Then open FB_StationBase and show where each section moved.

The "drift fixed" notes are the headline win for Stage 2. Walk through each fix slowly — earn the win before you puncture it.

Then ask: "What did this refactor cost?" Take answers. Likely first answers: nothing visible, lower line count, etc. Push to the right answer: "It cost an extra concept. Now you have to understand 'base class' and 'override' and 'THIS vs SUPER' to read this code. That's the real cost. Be honest about it."
""".strip(),
    )

    add_code_slide(
        prs,
        title="Inheritance mechanics — the four things to recognize",
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
FUNCTION_BLOCK FB_StationFill EXTENDS FB_StationBase
METHOD FB_init : BOOL
VAR_INPUT
    bInitRetains : BOOL;
    bInCopyCode  : BOOL;
    Name         : STRING(20);   // passed to base's name field at construction
END_VAR
SUPER^.FB_init(bInitRetains, bInCopyCode);
THIS^.Name := Name;""",
        language="Structured Text",
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2A walkthrough",
        page=n(),
        notes="""
This is the "TwinCAT inheritance has a learning cost" slide. Walk all four constructs.

For the FAE audience this is review — most have used inheritance in TwinCAT. But explicitly call them out by name (EXTENDS, SUPER^, override, FB_init) because they'll have to TEACH this to controls engineers who haven't used inheritance, and the vocabulary matters.

The line to deliver: "If you're going to teach Stage 2 to your customers, this slide is what you'll spend 5 minutes on. The audience needs to recognize all four constructs by sight before CR-1."
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 2 · 2A pre-emptive pushback",
        customer_q="My junior engineers don't know inheritance. Now they can't read my code.",
        fae_a="That's a valid concern. Inheritance has a learning cost. The win is consistency enforcement — once your team learns it, drift goes away. The trade-off is real; you pick whichever fits your team's experience curve.",
        page=n(),
        notes="""
Common controls-engineering objection. Don't dismiss it — the customer is correct that inheritance has a learning cost. The honest framing is the trade-off, not the dismissal.

Variant of this you might hear: "We don't have time to train the team." → "Then Stage 1 is your right answer for now. The workshop's value isn't 'always pick Stage 3.' It's 'know which stage fits your situation.'"
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-1 — the inheritance way",
        bullets=[
            "Same Pause requirement as Stage 1. Apply it via inheritance.",
            "10-minute timer. The attempt: most will add ModePause to the base's mode logic. Then they'll hit Fill's mid-cycle exception.",
            "The two answers — Option A: virtual AllowPause() on the base, override in Fill. Option B: Fill overrides Monitoring entirely.",
            "Both are legitimate. Both are ugly in the same way.",
            "Option A — AllowPause exists for ONE child's exception, but Cap, Label, Inspect inherit it forever. Pollution.",
            "Option B — duplicates base mode logic in Fill. Drift risk.",
            "Pick your poison. There's no clean way through.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2B  ·  CR-1 hands-on (15 min)",
        page=n(),
        notes="""
Read the requirement. Set the timer. Walk the room. Most attendees will start with Option A because it feels more "inheritance-y."

When attendees are stuck, walk the room and ask: "How are you handling the exception?" Both options will surface. Run the "both are ugly in the same way" line out loud — make sure the room hears it.

This is the workshop's second reveal: inheritance trades one cost for another. Stage 1 had per-station pollution; Stage 2 puts the pollution on the base, where every reader and every child pays.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-1 result — base-class pollution",
        branch_compare="stage-2-inheritance...stage-2-cr1-applied --stat",
        headline_stat="3 files  ·  +65  −48",
        takeaways=[
            "Base gets a virtual AllowPause() method (default TRUE). Fill overrides to return (State <> 10).",
            "Compared to Stage 1 (5 files / +50 / −13) — Stage 2 touches fewer files but adds more lines.",
            "The pollution is on the base — visible to every reader, paid by every child, even Cap/Label/Inspect that have no exception.",
            "Stage 1's pollution was scattered across stations. Stage 2's pollution is centralized. Which is worse?",
            "There's no clear answer. That's the point. Inheritance trades one cost for another.",
        ],
        accent=Theme.TEAL,
        page=n(),
        notes="""
Show the diff. Drive the comparison: 5 files / +50 / −13 (Stage 1) vs 3 files / +65 / −48 (Stage 2).

The discussion question: "Which is worse — scattered pollution paid by 4 stations, or centralized pollution paid by every reader of the base?" There's no right answer. The point is that inheritance didn't eliminate the cost; it relocated it.

This sets up CR-2, where the relocation becomes a trap.
""".strip(),
    )

    add_section_divider(
        prs,
        block_label="Block 2 · 2C",
        title="CR-2 — the breaking point",
        time_budget="25 min  ·  the workshop's hardest moment",
        summary="Inspect: non-faulting alarm AND parallel state-10. Same as Stage 1, applied via inheritance.\nMost attempts call SUPER^.Monitoring() and add quality logic after.\nThe base latches the alarm before the override gets a chance.",
        accent=Theme.TEAL,
        notes="""
This block is the workshop's hardest moment. Plan to slow down.

Read CR-2 again — same requirement as Stage 1. Set a 15-minute timer. Walk the room. Most attendees start by overriding Monitoring and adding their quality-flag logic AFTER calling SUPER^.Monitoring(). This produces broken behavior — the base latches the alarm before their override can flag it as quality.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The realization — you can't call SUPER",
        bullets=[
            "When does SUPER^.Monitoring() latch the alarm? — every time RaiseStationAlarm is called.",
            "What does the quality-flag policy say should happen? — don't latch.",
            "So what does that imply about calling SUPER? — you can't.",
            "But if you don't call SUPER, you lose the mode resolution and alarm-ack the base does — so you have to duplicate them in your override.",
            "The base class that helped you in Stage 1 → Stage 2 — that compressed five files into one base — has now become the constraint.",
            "This isn't your fault. It's a property of the design. Single inheritance is all-or-nothing.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2C  ·  the breaking point",
        page=n(),
        notes="""
Walk the room while attendees are stuck. Use the leading questions in order — let them arrive at the realization.

When the room is at the "you can't call SUPER" moment, gather attention and deliver the lesson: "There's no way to say 'inherit everything except the alarm policy.' Inheritance is all-or-nothing. Whatever the base does, every child gets — unless the child reimplements that behavior in an override."

Then show stage-2-broken: "This is what mid-fix looks like in real life — a partially overridden Monitoring with TODO comments." Leave the TODOs visible; they're the visual evidence of the design fight.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 2 · CR-2 the breaking-point reveal",
        quote="Notice this isn't your fault. It's a property of the design. Single inheritance gives you ONE base. Whatever the base does, every child gets — unless the child reimplements that behavior in an override. There's no way to say 'inherit everything except the alarm policy.'",
        attribution="The base class that helped Stage 1 → Stage 2 has now become the constraint. Inspect can't extend the base; it has to fight the base.",
        accent=Theme.TEAL,
        page=n(),
        on_dark=True,
        notes="""
Workshop's third reveal. This is the climax of Block 2.

Read the quote slowly. Wait. Let it land. The room should be uncomfortable — that's the lesson working.

If you're tempted to fill the silence: don't. The silence is the workshop. Senior controls engineers in the room are recognizing this pattern from their own codebases right now.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-2 result — the override fight",
        branch_compare="stage-2-inheritance...stage-2-cr2-applied --stat",
        headline_stat="2 files  ·  +121  −48",
        takeaways=[
            "Inspect overrides Monitoring WITHOUT calling SUPER — the base would latch the alarm and stop the line.",
            "The override is ~80 lines: re-implements mode resolution and alarm-ack from scratch in Inspect.",
            "Future additions to base Monitoring won't auto-propagate. Every base change is now a 'did we update Inspect?' code review burden.",
            "Compared to Stage 1 CR-2 (92 lines of inline rewrite) — Stage 2 is WORSE on lines. The architecture made it harder, not easier.",
            "Pre-emptive pushback: 'Use multiple inheritance.' — TwinCAT doesn't support it; languages that do (C++, Python) have ugly issues with it (the diamond problem). Composition is the answer.",
        ],
        accent=Theme.TEAL,
        page=n(),
        notes="""
Show the diff. Land the cost: 121 lines of override fight, including duplicated mode resolution.

Highlight the ~80-line override. Open it on the projector if you have time. The visible cost is the line count; the invisible cost is the future-change burden every time the base evolves.

The most important pushback rehearsal in the workshop is on the next slide. Don't skip it.
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 2 · CR-2 the most important pushback",
        customer_q="This is fine — I just need to remember to mirror base changes into Inspect's override.",
        fae_a="That's a code-review burden you'll carry forever. Every base change is now a question of 'did we update Inspect?' Sometimes you'll forget. The architecture isn't enforcing the consistency anymore — your team's discipline is. Discipline is bounded; architecture is unbounded.",
        page=n(),
        notes="""
The most important pushback in the workshop. Run it explicitly. If only one customer-conversation Q&A sticks, this is the one you want.

The line "discipline is bounded; architecture is unbounded" is the workshop's central thesis in seven words. Mark it. Repeat it in Block 3 and Block 4. Make it the line attendees go home quoting.

Variant — if asked: "Use multiple inheritance, then." → "TwinCAT doesn't support multiple inheritance, and most languages that do (C++, Python) have ugly issues with it (the diamond problem). The composition pattern in Stage 3 solves the same need without those issues. We'll get there."
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-3 result — dead weight in unrelated children",
        branch_compare="stage-2-inheritance...stage-2-cr3-applied --stat",
        headline_stat="3 files  ·  +64  −25",
        takeaways=[
            "FB_StationBase gets LogBuffer, LogIndex, LoggingEnabled virtual + LogCycleData helper.",
            "Fill and Inspect override LoggingEnabled to return TRUE.",
            "Cap and Label silently inherit the storage — pay for memory they never use.",
            "100 strings × 120 chars × 2 unused stations = 24KB. Academic at this scale; cognitive cost compounds.",
            "Every reader of FB_StationBase has to understand why LogBuffer exists when half the children don't use it. Noise on the abstraction.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2D  ·  CR-3 hands-on (10 min)",
        page=n(),
        notes="""
Read the requirement. 5-minute timer. The attempt: LogBuffer + LoggingEnabled virtual on the base; Fill and Inspect override to TRUE.

Show the diff. The discussion: "Where does Cap's LogBuffer storage live in memory?" → in every Cap and Label instance, even though they never write to it. "Is that a problem?" → in 4 stations, no. In a 50-station factory, yes.

Pre-emptive pushback: "100 strings × 120 chars × 2 unused stations = 24KB. Why are we obsessing about this?" → "You're right — for this scale, the memory cost is academic. The bigger problem is COGNITIVE. Every reader of FB_StationBase has to understand why LogBuffer exists when half the children don't use it. As your codebase grows, that noise compounds."

Pacing lever: if you're behind, cut this hands-on entirely (just show the diff). The CR-2 breakdown is the lesson; CR-3 is supplementary.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Block 2 debrief — the base became a junk drawer",
        bullets=[
            "Total Stage 2 diff after all three CRs — git switch stage-2-complete && git diff stage-2-inheritance --stat — 4 files, +224, −65.",
            "The base has accumulated ModePause, AllowPause virtual, LogBuffer, LogIndex, LoggingEnabled virtual, LogCycleData helper.",
            "It started clean. Now it's a junk drawer. Every CR added another carve-out the base wasn't designed for.",
            "Stage 2 fixed real Stage 1 problems — drift, consistency, line count.",
            "Stage 2 created new problems — base-class pollution, SUPER-can't-be-called fragility, dead weight in unrelated children.",
            "Stage 3 will keep what's good (clean abstractions, consistency enforcement) and fix what's wrong. Let's go.",
        ],
        accent=Theme.TEAL,
        eyebrow="Block 2 · 2E debrief (5 min)",
        page=n(),
        notes="""
Switch presenter to stage-2-complete. Show the diff stat live. Walk the FB_StationBase tab — point to each new accumulation: ModePause field, AllowPause virtual, LogBuffer, LoggingEnabled virtual, LogCycleData helper.

Ask the room: "Stage 2 fixed real problems Stage 1 had. What new problems did it create?" Take answers. The right ones: base-class pollution, SUPER-can't-be-called fragility, dead weight.

Then the bridge: "Stage 3 will keep what's good — clean abstractions, consistency enforcement — and fix what's wrong. Let's go."

Set up the break.
""".strip(),
    )

    add_break_slide(
        prs,
        label="Block 2 → Block 3 break",
        duration="10 min",
        message="The longer of the two breaks if you can swing it. Block 3's emotional payoff lands harder if the room comes back fresh.",
        accent=Theme.TEAL,
        page=n(),
        notes="""
Real break. While they're out: pull `stage-3-composition` on the presenter machine. Open the file tree, then I_AlarmHandler.TcPOU and FB_AlarmHandler_LineFault.TcPOU side by side.

If you have a second laptop: open MAIN.TcPOU on it. The MAIN swap demo in Block 3 is the workshop's emotional climax — preparing it now saves a switching delay later.
""".strip(),
    )

    # ------ BLOCK 3 — Stage 3 — Composition --------------------------------

    add_section_divider(
        prs,
        block_label="Block 3",
        title="Stage 3 — Composition",
        time_budget="70 min  ·  architecture · CR-1 · CR-2 swap demo · CR-3",
        summary="Build the line from interface-typed building blocks. CR-2 — the killer requirement that broke Stage 2 — becomes a one-line swap.\nThe patterns you just used get names: Strategy, Template Method, DI.",
        accent=Theme.VIOLET,
        notes="""
Section break. Switch presenter to `stage-3-composition`. The file tree should be visible — 18 files in three directories.

This block is the emotional payoff of the workshop. Pace it so the room has time to FEEL the win, not just observe it. Don't rush past CR-2.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The composition paradigm in one slide",
        bullets=[
            "Origin — Gang of Four 1994 ('favor composition over inheritance'); SOLID 2000s codified the design principles.",
            "Mental model — small focused FBs talk through interfaces. Stations COMPOSE building blocks instead of EXTENDING a base.",
            "TwinCAT support — INTERFACE keyword, IMPLEMENTS keyword, FB references typed by interface, FB_init for dependency injection.",
            "Framework grounding — Beckhoff USA's Core / CoreComponents / MechatronicsCore libraries. I_Cyclic, I_Diagnostic component pattern. Production code.",
            "The promise — variation by injection (different building block, same interface). The catch — more files, more concepts, more vocabulary.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
Don't lecture this. Read the bullets, gesture at the file tree, and move on.

The line that matters: "variation by injection." That's the seed of CR-2's swap demo. Plant it now — they'll see it in 30 minutes.

If anyone asks "is this just dependency injection?" — answer: "Yes. DI is one of the patterns. We'll name them all in Block 4."
""".strip(),
    )

    add_content_slide(
        prs,
        title="The file tree — 18 files. Hold the judgment.",
        bullets=[
            "Interfaces (5 files) — I_AlarmHandler, I_DataLogger, I_HmiReportable, I_Sequenceable, I_StationCore.",
            "Building blocks (~7 files) — FB_AlarmHandler_LineFault, FB_AlarmHandler_QualityFlag, FB_CycleDataLogger, FB_ModeManager, FB_StepSequencer, FB_ParallelSequencer, …",
            "Stations (4 files) — FB_StationFill, FB_StationCap, FB_StationLabel, FB_StationInspect — each composes building blocks.",
            "MAIN — wires the dependency graph. The construction calls ARE the architecture.",
            "This looks like more code. Hold that judgment for one slide.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
Open the file tree. Walk it from top to bottom. Pre-empt the objection — "this is more files than Stage 1 had" — by acknowledging it explicitly.

The "hold that judgment" framing is deliberate. The architecture's payback comes in the next 40 minutes. Don't defend it now; let CR-2 defend it.
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

// That's it. Anyone who implements this satisfies the contract.
// Stations depend on I_AlarmHandler — they never know which implementation
// they have. That's the seam where CR-2's swap will happen.""",
        language="TwinCAT INTERFACE",
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
Open I_AlarmHandler.TcPOU on the projector. Walk through the four members.

The line to deliver: "Stations depend on I_AlarmHandler — they never know which implementation they have. That's the seam where CR-2's swap will happen."

Don't explain the swap yet. Just plant the seam. Reveal in 25 minutes.
""".strip(),
    )

    add_two_col_slide(
        prs,
        title="Two implementations — same shape, opposite policy",
        left_title="FB_AlarmHandler_LineFault",
        left_items=[
            "StopsLine — returns TRUE.",
            "Raise() — latches Active flag, sets Code/Text, blocks downstream.",
            "Acknowledge() — clears the latch (operator action required).",
            "Use this for — real faults that should stop the line.",
            "What it tells the station — 'something is wrong; halt.'",
        ],
        right_title="FB_AlarmHandler_QualityFlag",
        right_items=[
            "StopsLine — returns FALSE.",
            "Raise() — sets Code/Text, does NOT latch, does NOT block.",
            "Acknowledge() — no-op (nothing to clear).",
            "Use this for — quality defects that feed downstream sortation.",
            "What it tells the station — 'note this part; keep running.'",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
Open both files side by side. Walk the symmetry: same shape, opposite policy. Both satisfy I_AlarmHandler.

The line to deliver: "Same contract, opposite behavior. The station code can't tell them apart — that's the point. The behavior change happens in MAIN, not in the station."

Foreshadow: "In 25 minutes, CR-2 is going to ask 'change Inspect's alarm policy.' We'll do it by changing one line in MAIN."
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
Open FB_StationFill on the projector. Walk the VAR block first — point at the I_AlarmHandler / I_DataLogger fields. Then walk FB_init — point at the AlarmHandler / DataLogger parameters.

The line to deliver: "The station never constructs its dependencies. It receives them. That's dependency injection — the seam that makes CR-2 trivial."

If anyone asks "what's REFERENCE TO?" — short answer: "TwinCAT's pointer-with-syntax-sugar. Use REF= to bind, then dereference with .field syntax. We use it for FB_ModeManager because there's exactly one shared instance."
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

    // Each station receives its dependencies via FB_init
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
Open MAIN on the projector. Walk the construction calls. Highlight the AlarmHandler := LineFault line on Inspect — call it the "swap point."

The line to deliver: "Read MAIN top-to-bottom — it IS the wiring diagram for the line. In Stage 1, MAIN was 'instantiate stations.' In Stage 3, MAIN is 'wire the dependency graph.' The architecture is realized at construction."

This sets up CR-2 directly. The audience should be ready to predict what the swap looks like.
""".strip(),
    )

    add_content_slide(
        prs,
        title="SOLID — concretely, in this codebase",
        bullets=[
            "S — Single Responsibility — every building block does ONE thing. FB_AlarmHandler latches. FB_CycleDataLogger logs. FB_StepSequencer sequences. None of them do two things.",
            "O — Open/Closed — open to new alarm strategies (add another I_AlarmHandler implementation), closed to modification of the existing ones. CR-2 will demonstrate this directly.",
            "L — Liskov Substitution — any I_AlarmHandler works anywhere I_AlarmHandler is expected. The station can't tell LineFault from QualityFlag.",
            "I — Interface Segregation — HMI sees I_HmiReportable. Sequencer sees I_Sequenceable. Nobody sees the kitchen sink.",
            "D — Dependency Inversion — stations depend on I_AlarmHandler (abstract), not on FB_AlarmHandler_LineFault (concrete). MAIN binds the concrete to the abstract.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3A architecture walkthrough",
        page=n(),
        notes="""
Walk SOLID once, slowly, with the codebase as the example. This is the vocabulary attendees will take to customer conversations — make sure each principle is named with a specific Stage 3 file as the example.

For an FAE audience, SOLID is review at the conceptual level — what's new is mapping each principle to a specific TwinCAT file they just walked through.

Discussion prompt if you have time: "Which SOLID principle is doing the heavy lifting in this codebase?" Best answer is D (Dependency Inversion) — that's the seam that makes CR-2 trivial. L (Liskov) is the property that makes D safe.
""".strip(),
    )

    add_pushback_slide(
        prs,
        kicker="Block 3 · 3A pre-emptive pushback",
        customer_q="Eighteen files for a 4-station machine? You've got to be kidding.",
        fae_a="You're right — for 4 stations, this is overkill. The architecture pays back when the codebase grows. If you're shipping one machine and walking away, Stage 1 is the right answer. If you're building a product family, Stage 3 is the prerequisite for sane long-term maintenance.",
        page=n(),
        notes="""
The "this is overkill" objection. Critical to acknowledge — for the workshop's 4-station example, the customer is RIGHT. Stage 3 is overkill at this scale.

The honest framing is the trade-off: Stage 3's payoff is at scale and over time. For a one-off machine, Stage 1 is correct. For a product family that ships 50 variants over 5 years, Stage 3 is the only sane answer.

Don't oversell composition. The workshop's value is the trade-off vocabulary, not the religion.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-1 — the composition way (and Fill's exception comes free)",
        branch_compare="stage-3-composition...stage-3-cr1-applied --stat",
        headline_stat="2 files  ·  +19  −6",
        takeaways=[
            "Just modify FB_ModeManager. Add ModePause input + Mode = 3 branch. Done.",
            "Stations are NOT touched — they consult Mode.AllowRun, which already returns FALSE when paused.",
            "Fill's mid-cycle exception — automatic. Fill's state-10 logic doesn't gate on AllowRun once started; it gates on Accumulated >= TargetVolume.",
            "The right gating point was already in place. CR-1 didn't have to add new gating logic anywhere because the abstraction encoded the right behavior already.",
            "Compare to Stage 1 (5 files / +50 / −13) and Stage 2 (3 files / +65 / −48). The shape of the change matters more than the lines.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3B  ·  CR-1 hands-on (10 min)",
        page=n(),
        notes="""
Read the requirement: same Pause requirement as Stage 1. 5-minute timer. The realization comes fast: just modify FB_ModeManager.

Discussion prompt: "Why is the Fill mid-cycle exception automatic in this architecture?" Walk the audience to the answer: Fill's state-10 logic gates on Accumulated >= TargetVolume, not on AllowRun. The abstraction already encoded the right behavior.

Pre-emptive pushback: "Sure, this works for Pause because Pause maps cleanly to a mode. What about a feature that doesn't?" → "Then you do the work to find the right abstraction. Composition isn't magic — it requires careful design. Stage 1 + 2 pay per-CR. Stage 3 pays up front and reaps savings."
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
This is the workshop's emotional payoff. Pace it carefully.

Read CR-2 again: "Inspect: non-faulting alarm AND parallel state-10. Same as Stage 1 (60 inline lines) and Stage 2 (the override mess). Apply it the composition way."

Demonstrate FIRST — on the presenter machine, before they try. The next slide is the one-line swap.
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
// the line keeps running on defect. NO INSPECT CODE WAS MODIFIED.
//
// How is this possible? Because the alarm strategy is INJECTED, not
// hardcoded. Inspect depends on I_AlarmHandler — anything implementing
// that interface plugs in.""",
        language="Structured Text",
        accent=Theme.VIOLET,
        eyebrow="Block 3 · CR-2 the headline swap",
        page=n(),
        notes="""
Demonstrate this LIVE on the presenter machine. The slide is the script — but the demo is the lesson.

1. Open MAIN. Find the line.
2. Change LineFault to QualityFlag.
3. Save. Build.
4. PAUSE. Don't speak. Let the implication land. Count to 10 silently.
5. After the silence, ask: "Did Inspect's behavior just change?" (Yes — alarms are non-latching, line keeps running.) "Did we modify any Inspect code?" (No.) "How is this possible?" (Because the alarm strategy is injected, not hardcoded.)

The silence is the lesson. Don't fill it.
""".strip(),
    )

    add_quote_slide(
        prs,
        kicker="Block 3 · the workshop's central claim",
        quote="Stage 1 CR-2: 92 lines of inline rewrite of one CASE machine.\nStage 2 CR-2: 121 lines of override that fights the base.\nStage 3 CR-2: ONE LINE.",
        attribution="Same requirements, three architectures, different blast radius. The diff is the proof.",
        accent=Theme.VIOLET,
        page=n(),
        on_dark=True,
        notes="""
This is the workshop's headline claim. Read it slowly. Repeat it. This is the line attendees will take home.

If only one slide of the workshop sticks, this is the one you want. The 92 → 121 → 1 progression is the receipt for the entire 4 hours.

Pre-emptive pushback (the customer-facing version): "You're cherry-picking the example. CR-2 is designed to make composition look good." → "It's designed to be REALISTIC, not to make composition look good. Real customers ask for non-faulting alarms and parallel coordination on specific stations all the time. The point isn't that Stage 3 looks good in this CR — it's that CR-1, CR-2, AND CR-3 all look good in Stage 3. Three different shapes of cross-cutting requirement, three different costs, every one cheaper. That's pattern recognition, not cherry-picking."
""".strip(),
    )

    add_content_slide(
        prs,
        title="CR-2 hands-on — the parallel sequencer",
        bullets=[
            "The swap was the headline. The hands-on completes the picture.",
            "Inspect also needs parallel state-10 (camera + reject pre-arm at the same time).",
            "Open FB_StationInspect.TcPOU. Compose FB_ParallelSequencer alongside FB_StepSequencer. Configure for 2 branches in FB_init. Rework state 10.",
            "10 minutes. Composition, not rewriting.",
            "Final diff — 2 files modified. ~30 lines added, ~10 removed. No other stations touched.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · CR-2 hands-on (10 min)",
        page=n(),
        notes="""
After the swap demo, hand them the parallel-sequencer half. 10-minute timer.

The pattern they're applying: COMPOSE a new building block (FB_ParallelSequencer) alongside an existing one (FB_StepSequencer). Not rewriting; composing.

When done: `git switch stage-3-cr2-applied` and show the diff. ~30 lines added in 2 files.

Pacing lever: if you're behind, skip this hands-on. The reveal moment is the swap on the presenter screen — that's the lesson. The parallel sequencer is supplementary.
""".strip(),
    )

    add_diff_slide(
        prs,
        title="CR-3 — DI all the way",
        branch_compare="stage-3-composition...stage-3-cr3-applied --stat",
        headline_stat="3 files  ·  +32  −11",
        takeaways=[
            "Add Logger : I_DataLogger field + DataLogger FB_init param to Fill and Inspect ONLY.",
            "MAIN constructs CycleLogger and passes it via DI.",
            "Cap and Label keep their original 4-arg FB_init signature — DON'T touch them.",
            "Cap's logger storage lives nowhere — Cap doesn't have a logger field.",
            "Swap from in-memory buffer to file-based logger? Replace FB_CycleDataLogger only. Stations don't change. MAIN doesn't change.",
            "Compare to Stage 2 (3 files / +64 / −25) — same file count, half the lines, zero dead weight.",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3D  ·  CR-3 hands-on (10 min)",
        page=n(),
        notes="""
Read the requirement. 5-minute timer. The path: add I_DataLogger field + FB_init param to Fill and Inspect only.

Discussion prompt: "Where does Cap's logger storage live now?" → nowhere. Cap doesn't have the field. "What changes if we swap from in-memory buffer to file-based logger?" → only FB_CycleDataLogger is replaced. Stations don't change. MAIN doesn't change.

Compare to Stage 2's logger refactor cost: base + every override + LogCycleData helper. Stage 3: just the building block.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Bonus — even composition can be applied poorly",
        bullets=[
            "git switch stage-3-broken — same CR-1 (Pause), but applied via per-station guard logic instead of via FB_ModeManager.",
            "Compiles. Runs. Halts Fill mid-cycle — the very failure mode CR-1 was designed to avoid.",
            "Architecture matters, but so does discipline. Composition gives you the tools to do it right. It doesn't force you to.",
            "The right architecture nudges you toward the right answer — and the wrong-way alternative is loud (5-file diff) instead of quiet (1-file diff).",
        ],
        accent=Theme.VIOLET,
        eyebrow="Block 3 · 3E  ·  the wrong-way branch (5 min)",
        page=n(),
        notes="""
Show stage-3-broken on the projector. Walk the per-station guards. Then compare to stage-3-cr1-applied (FB_ModeManager-only). The right answer is loud and small; the wrong answer is loud and large.

The lesson: the right architecture makes the right thing easy and the wrong thing visible.

Pre-emptive pushback: "So composition can be done wrong too. What's the point?" → "Every paradigm can be done wrong. The point is which one MAKES THE RIGHT THING EASY AND THE WRONG THING VISIBLE. Stage 1's right answer for cross-cutting concerns is 'modify every station' — easy to do, easy to drift. Stage 3's right answer is 'modify the shared service' — also easy, and the wrong-way alternative is loud (5-file diff) instead of quiet (1-file diff)."
""".strip(),
    )

    # ------ BLOCK 4 — Scoreboard, discussion, take-home --------------------

    add_section_divider(
        prs,
        block_label="Block 4",
        title="Scoreboard, discussion, take-home",
        time_budget="20 min  ·  plan to overshoot",
        summary="The numbers from the diffs go on the board.\nDiscussion: when does each stage fit your real workload?\nThe vocabulary they'll take to customer conversations starts here.",
        accent=Theme.NAVY,
        notes="""
Section break. This is where the workshop cements. Plan to overshoot the 20-minute budget if discussion is gold — that's the workshop's value.

Pull up the scoreboard page on the projector OR reveal the whiteboard with cells pre-drawn. Walk through the 9 cells.
""".strip(),
    )

    add_scoreboard_slide(
        prs,
        page=n(),
        notes="""
Walk the matrix cell-by-cell. The audience has now DONE every cell — this is consolidation, not introduction.

Read aloud:
- "CR-1 hits 5 files in procedural; 3 in inheritance; 2 in composition."
- "CR-2 in procedural is a 92-line inline rewrite. In inheritance it's a 121-line override fight. In composition it's a 1-line swap."
- "CR-3 looks small in procedural (13 lines) but the duplication is permanent. Inheritance fixes the duplication but adds dead weight. Composition has both proportional cost AND zero dead weight."

The deeper lessons are on the next slide.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Reading the numbers — blast radius, not lines",
        bullets=[
            "Stage 1 wins on raw lines for CR-3 (13). But those 13 lines are duplicated identically in Fill and Inspect. The duplicate is permanent.",
            "Stage 2 CR-2 only adds ~80 lines, but those 80 lines re-implement mode resolution and alarm-ack from scratch. The 'lines' are cheap; the FRAGILITY is expensive.",
            "Stage 1 blast radius — every change to a cross-cutting concern touches every station. CR-1 hit 5 files; the next 50 changes will hit ~5 files each.",
            "Stage 2 blast radius — common parts hit the base; station-specific parts hit one child. Until a child needs to opt out, in which case the base gets polluted.",
            "Stage 3 blast radius — building-block changes hit one file. Wiring changes hit MAIN. Stations themselves rarely change after initial composition.",
            "The right frame is BLAST RADIUS, not LINES.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4A scoreboard (10 min)",
        page=n(),
        body_size=14,
        notes="""
This is the slide that recasts the scoreboard. Lines are the visible cost; blast radius is the real cost.

The blast-radius framing is the language attendees will take to customer conversations. Mark it. Repeat it.

If you have a whiteboard: write "BLAST RADIUS" in big letters next to the scoreboard matrix. Visual anchor.
""".strip(),
    )

    add_content_slide(
        prs,
        title="The quiet long-tail value — testability",
        bullets=[
            "The scoreboard tracks the visible cost of CRs. The invisible cost the scoreboard CAN'T show is testability.",
            "Stage 1 and Stage 2 stations are entangled with their I/O — you can't unit-test them without spinning up the whole framework.",
            "Stage 3 stations accept their dependencies at construction. In a TcUnit test you can construct FB_StationFill with mocks: MockMode, MockAlarm (QualityFlag — never latches), Logger (inspect buffer after each cycle).",
            "Drive MockMode.ModeAuto := TRUE, set PartPresent := TRUE, call Execute() repeatedly, assert against Logger._Buffer. No real I/O. No real alarms. Deterministic.",
            "If your shop is moving toward CI for control code, this isn't optional anymore — it's the prerequisite.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4A scoreboard",
        page=n(),
        notes="""
The testability argument is the workshop's quiet long-tail value. Some attendees will care about this more than the blast-radius argument.

If you're running ahead and the room is technically engaged, this is the springboard into the bonus TcUnit demo (see backup slides).

If you're running on time: deliver this as a sentence and move on. The next slide is the discussion that earns the workshop.
""".strip(),
    )

    add_three_col_slide(
        prs,
        title="Which stage for which shop? — the honest answers",
        columns=[
            ("Stage 1 — Procedural is right for", [
                "Single-machine integrators",
                "Panel shops",
                "One-engineer teams",
                "Short-lifespan code",
                "Customers shipping a machine and walking away",
                "Teams with no inheritance/OOP background",
            ], Theme.AMBER),
            ("Stage 2 — Inheritance is right for", [
                "Homogeneous machine families",
                "Mid-sized teams",
                "Long-lifespan code with medium variation",
                "Teams already comfortable with EXTENDS / SUPER",
                "Codebases where most stations are 80% similar and 20% different",
            ], Theme.TEAL),
            ("Stage 3 — Composition is right for", [
                "OEMs building product families",
                "Multi-engineer teams",
                "Multi-customer variation",
                "Long-lifespan codebases",
                "Shops moving toward CI / TDD for PLC code",
                "Codebases where the same shape appears with different policy",
            ], Theme.VIOLET),
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4A discussion (the most important one)",
        page=n(),
        notes="""
The most important discussion of the workshop.

Ask: "Walk back to your shop. What machine, codebase, or customer is each stage right for? Be specific. Name names if you can."

Take answers. Encourage debate. The slide is the honest framing — the workshop value is the customer-specific application.

If the room is shy, prime with: "Anyone here own a single-machine codebase that Stage 1 is fine for?" → hands. "Anyone working on a product family where Stage 3 is the prerequisite?" → hands. "Anyone in the messy middle where Stage 2 is what you're already doing and you're feeling the limits?" → most hands.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Customer-conversation rehearsal",
        bullets=[
            "You'll go back to your customers. Someone will say 'this is overkill' or 'we don't have time for this' or 'just give me the procedural version.' Let's rehearse.",
            "Pick three of these — roleplay with the room — \"This is fine. We've shipped 50 machines like this.\" — \"My team's careful. We use code review. Drift won't happen.\" — \"My junior engineers don't know inheritance.\" — \"Eighteen files for a 4-station machine? You've got to be kidding.\" — \"I just need to remember to mirror base changes into Inspect's override.\" — \"You're cherry-picking the example.\"",
            "The answer isn't 'composition is always right.'  The answer is 'here's how to know which fits your situation.'",
            "Discipline is bounded; architecture is unbounded. Take that line home.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4B (5 min)",
        page=n(),
        notes="""
Pick three of the pushback questions. Roleplay them with the room. Let attendees take the FAE side; you take the customer side.

The point: the customer-conversation rehearsal is the workshop's transferable skill. They've heard the pushbacks all day; now they practice the answers.

If time is short: pick the ONE pushback most likely to come up in their next customer conversation. The "discipline is bounded; architecture is unbounded" line is the close.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Continuation kit — three modes for keeping this alive",
        bullets=[
            "Self-paced refresher — ./serve-docs.sh from the cloned repo. Walk the stages in order. Re-read the per-CR diffs against the scoreboard.",
            "Teaching mode — the docs site is structured so you can run a 1-2 hour version for your own team or customer. The Instructor's guide is the script; the Patterns reference is the cheat sheet.",
            "Deep end — TcUnit on a Stage 3 station, then the same on Stage 1. The testability difference is visceral. See the testing.md page for the working PlcTestSuite demo on stage-3-complete-tests.",
            "Send me one specific machine, project, or customer this material applies to. That's how I make this workshop better.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4C (5 min)",
        page=n(),
        notes="""
Three modes for keeping the material alive. Walk them in order.

The "send me one specific machine" ask is real. Senior FAEs who attend are the workshop's distribution channel — they need to teach it. Knowing what they'll teach it FOR makes the next iteration of the workshop better.

If you have time and the workshop is intimate enough (< 20 attendees), promise a personal recommendation per attendee in the post-workshop follow-up. The next slide.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Personal recommendations — what makes the workshop stick",
        bullets=[
            "If your shop is < 20 attendees and you have time, send each attendee a brief follow-up with a specific recommendation tied to their team's situation.",
            "Sarah — your shop ships motion controllers. The I_AlarmHandler swap is the most useful Stage 3 pattern for your test rigs. Try it on your next customer build.",
            "Bob — you're maintaining a single-machine codebase. Stage 1 is fine for you. Add the Stage 3 CR-2 swap exercise to your toolkit for the next motion vendor swap — that's where you'll feel the testability win.",
            "Maria — you do customer training. Run a 1-hour version of just Stage 1 → Stage 3 CR-2 (skip CR-1 and CR-3) for your next class. It's the most impactful single demo in the workshop.",
            "Generic advice fades. Specific advice sticks.",
        ],
        accent=Theme.NAVY,
        eyebrow="Block 4 · 4C continuation",
        page=n(),
        notes="""
The personal-recommendation pattern is what makes the workshop transferable. Generic advice ('use composition more') fades within a week; specific advice ('try the I_AlarmHandler swap on your test rigs next month') sticks.

This slide IS the template. Copy the structure: name, observed situation, specific recommended action.

If your audience is > 20: skip this slide. The personal-recommendation pattern doesn't scale past intimate workshops.
""".strip(),
    )

    add_closing_slide(
        prs,
        title="Become believers, then teachers",
        body="The bar for the FAE audience is to become believers and teachers.\n\nThe believer part comes from doing the workshop. You did that today.\n\nThe teacher part requires three more things: run a shorter version yourself within a month; adapt the script to your audience; track customer pushback you hear that isn't in this material — send it back so the next version is better.\n\nThe deepest measure of this workshop's success is when an FAE who attended teaches it, and their attendees recognize themselves in Stage 1's drift the way you recognized yourselves today.",
        contact="Repo: github.com/Mark-Code-Cowboys/NEM_Workshop  ·  Docs: ./serve-docs.sh  ·  Questions welcome.",
        accent=Theme.NAVY,
        page=n(),
        notes="""
Closing slide. Read the body slowly.

The "recognize themselves in Stage 1's drift" line is the emotional bookend to the CR-1 reveal in Block 1. Pull that thread explicitly: "Remember the silence in the room when half of you realized you'd copied from a station with one ack style? When you teach this, your attendees will have that same silence. That's the workshop working."

Q&A immediately after. The workshop is technically over but the discussion is half the value — let it run.
""".strip(),
    )

    # ------ Backup / pacing reference --------------------------------------

    add_section_divider(
        prs,
        block_label="Backup",
        title="Pacing levers, materials, bonus content",
        time_budget="reference  ·  not part of the live flow",
        summary="What to cut if you're behind. What to add if you're ahead.\nThe materials checklist for the day.\nThe TcUnit demo if the room earns it.",
        accent=Theme.NAVY,
        notes="""
Backup slides are reference material. NOT part of the live flow.

Hide these from the slide order if presenting from a printed agenda — but keep them in the deck file for your own reference and for FAEs who reuse the deck for shorter versions.
""".strip(),
    )

    add_two_col_slide(
        prs,
        title="Pacing levers — what to cut, what to add",
        left_title="If you're 15+ min behind",
        left_items=[
            "Block 2 CR-3 — cut hands-on entirely. Just show the diff. The Stage 2 lesson is CR-1 (pollution) and CR-2 (breaking point); CR-3's dead-weight problem is academic by comparison.",
            "Block 1 debrief — tighten. Don't walk every diff in detail; show the matrix on the scoreboard page and let the audience scan.",
            "Block 3 CR-2 — demo the swap, skip the parallel-sequencer hands-on. The reveal moment IS the swap.",
            "Block 4 4A — compress to a 2-minute walk-through of the scoreboard rather than per-cell discussion.",
        ],
        right_title="If you're ahead",
        right_items=[
            "Block 4 4B — extend customer-conversation rehearsal. 15+ minutes if the room is engaged.",
            "Patterns reference — show patterns.md and walk Strategy / Template Method / DI by name. Connect to the workshop they just did.",
            "Wrong-way branch — demo stage-3-broken and walk through WHY it's wrong even though it compiles.",
            "TcUnit demo — most powerful extension if the room is technically engaged. 15-25 min. See the next slide.",
        ],
        accent=Theme.NAVY,
        left_accent=Theme.CRIMSON,
        right_accent=Theme.NAVY,
        eyebrow="Backup",
        page=n(),
        notes="""
Quick reference card for facilitators. Use it during breaks to recalibrate.

The most common mistake: trying to cover all 9 scoreboard cells in equal depth. CR-2 in every stage is the spine; CR-1 and CR-3 are illustrations. If you're behind, compress CR-3 first.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Bonus — TcUnit demo (only if class finishes early)",
        bullets=[
            "When to run it — at least 20 min ahead at Block 4, most attendees have a runtime, room is leaning toward 'what would I actually do with this back at my shop?'",
            "Branch — stage-3-complete-tests. Library — PlcTestSuite (separate .library install; eats 5+ min if attendees don't have it).",
            "2 min — pull up the testing.md page. Read the 'Why composition is testable' section aloud. The architectural argument that hasn't been made explicit yet.",
            "3 min — open POUs/Tests/FB_TestRunner.TcPOU. Walk the file structure: 16 test methods organized into building-block tests + station integration tests.",
            "5 min — show one building-block test in detail. Test_QualityFlag_StopsLineIsFalse is the best one. Six lines, the entire Liskov substitution principle.",
            "5 min — show one station integration test. Test_FillStation_HappyPath_CompletesCycle. Highlight the VAR_INST block: local FB_ModeManager, FB_AlarmHandler_LineFault, FB_CycleDataLogger constructed and injected. THAT'S the testing seam.",
            "5 min — if you have a runtime: build, activate, login, start. Set RunTests := TRUE in MAIN. Show TEST_Result.xml.",
            "Frame as — 'this is what the rest of software engineering takes for granted. Stage 3 makes it available to control code. Composition isn't optional architecture if your shop wants CI for PLC — it's the prerequisite.'",
        ],
        accent=Theme.NAVY,
        eyebrow="Backup  ·  bonus content",
        page=n(),
        body_size=13,
        notes="""
The TcUnit demo is the most powerful single addition to the workshop — but it's deliberately bonus. Three reasons:

1. PlcTestSuite is a separate library install (5+ min per machine if attendees don't have it).
2. It only works on Stage 3 code. Demonstrating WHY it doesn't work on Stage 1 or 2 requires extra setup time the core workshop doesn't budget.
3. It needs a running TwinCAT runtime. Review-only attendees can't actually execute.

If you DO get to it: the lesson surfaces naturally — 'what would it take to test a Stage 1 station? A Stage 2 station? Why is this only possible on Stage 3?' Answer: Stage 1 and 2 stations don't have the dependency-injection seam, so there's nowhere to plug in mocks.

If you DON'T get to it: send the testing.md link in the post-workshop follow-up. The architectural lesson lands fully without the testing demo. Testing is the cherry on top, not the load-bearing beam.
""".strip(),
    )

    add_two_col_slide(
        prs,
        title="Materials checklist",
        left_title="Day-of",
        left_items=[
            "Presenter laptop, repo cloned, all branches fetched (git fetch --all).",
            "Working TwinCAT XAE 3.1.4026+.",
            "Two XAE instances open: stage-1-procedural and stage-3-composition.",
            "Browser with the scoreboard bookmarked.",
            "Local docs site running (./serve-docs.sh) — backup if wifi fails.",
            "Whiteboard or large sticky notes — physical scoreboard is more engaging than digital.",
            "Sticky notes for attendees to track files-touched and lines-changed.",
            "Timer for the timed exercises.",
        ],
        right_title="Day-after",
        right_items=[
            "Send each attendee the personal recommendation (see Block 4C).",
            "Send the repo URL and the scoreboard compare links — they'll forget where to find them.",
            "Solicit feedback in the workshop's chat / dedicated channel.",
            "Optional bonus material — only if you ran the testing demo: PlcTestSuite link, stage-3-complete-tests branch link, testing.md.",
        ],
        accent=Theme.NAVY,
        eyebrow="Backup  ·  facilitator checklist",
        page=n(),
        notes="""
Reference card for the day-of and day-after of running the workshop. Print it; tape it next to your laptop.

The physical scoreboard line matters more than it sounds. Watching the cells get filled in on a whiteboard as the exercises complete creates a different kind of engagement than a static slide.
""".strip(),
    )

    add_content_slide(
        prs,
        title="Shorter versions — when 4 hours isn't on the table",
        bullets=[
            "30 min — 'the one demo.' Show only the Stage 3 CR-2 swap demo. Three steps. Plant a single seed: runtime-swappable strategies are real and useful in TwinCAT.",
            "1 hr — 'the methodology compare.' Skip Stage 2. Run Stage 1 walkthrough + CR-1 hands-on, then Stage 3 walkthrough + CR-1 demonstration. Show only the CR-1 cells of the scoreboard. Lesson: same requirement, three different costs.",
            "2 hr — 'the workshop, compressed.' Run the full workshop's structure but cut CR-3 in every stage. CR-1 + CR-2 cover the key lessons; CR-3 is a pacing extender for the 4-hour version.",
            "4 hr — 'the full workshop.' This deck.",
            "None of the shortened versions include the testing demo. It's reserved for the 4-hour version, only when ahead of schedule.",
        ],
        accent=Theme.NAVY,
        eyebrow="Backup  ·  facilitator reference",
        page=n(),
        notes="""
FAEs running customer training or internal sessions often need 1-2 hour versions. These three pre-built shapes are battle-tested.

The 30-minute version is the most useful for customer pitches: one demo, one seed. The 1-hour version is the most useful for internal team training. The 2-hour version is the closest to the full experience without burning a half-day.

If an FAE asks "which version should I run?" — ask back: "What's your audience and what time do you have?" Then pick from this list.
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
