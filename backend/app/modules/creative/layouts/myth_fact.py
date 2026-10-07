"""Layout 2, myth vs fact: a dark MYTH card with the claim struck through, a bright FACT card with a check, a VS badge at the seam."""
from typing import List

from ..models import Copy, Design
from .base import Canvas, Rendered, footer_h, load_font, mix, ui
from .palette import FACT_GREEN, MYTH_RED, get


def _badge(c: Canvas, label: str, x: int, y: int, fill, icon: str) -> None:
    """The MYTH / FACT label: an icon and the word on a coloured pill as wide as the word needs."""
    tw = int(c.d.textlength(label, font=load_font(26, "bold")))
    c.rrect((x, y, x + 60 + tw + 26, y + 52), 26, fill)
    c.icon(icon, (x + 34, y + 26), 24 if icon == "cross" else 26, (255, 255, 255), 4)
    c.text(label, x + 60, y + 13, tw + 8, 26, "bold", (255, 255, 255), 1, balance=False, role="chip", bg_hint=fill)


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "myth_fact", pattern="grid", glow_at=(0.1, 0.9))
    p = copy.payload
    myth, truth = str(p.get("myth", "")), str(p.get("truth", ""))
    c.chip(str(p.get("kicker", "MYTH VS FACT")), c.left, c.top, icon="bolt")
    c.brand_bar(dark_bg=not pal.light)
    top = c.top + 100
    bottom = c.bottom - footer_h() - 30
    gap = 56
    avail = bottom - top - gap
    h_myth, h_fact = int(avail * 0.42), int(avail * 0.58)
    pad = 44
    w = c.right - c.left - 2 * pad
    dark = (20, 32, 58) if pal.light else mix(pal.card, (0, 0, 0), 0.45)
    light_card = (255, 253, 246)

    # MYTH card
    my0, my1 = top, top + h_myth
    c.rrect((c.left, my0, c.right, my1), 36, dark, outline=MYTH_RED, width=4, shadow=True)
    cx, cy = c.left + pad, my0 + pad
    _badge(c, ui("myth"), cx, cy, MYTH_RED, "cross")
    c.text(myth, cx, cy + 52 + 28, w, 82 if tall else 62, "bold", (236, 240, 248), 3, pitch=1.16, strike=(255, 110, 104), h=my1 - pad - (cy + 80), role="myth",
           bg_hint=dark)

    # FACT card
    fy0, fy1 = my1 + gap, bottom
    c.rrect((c.left, fy0, c.right, fy1), 36, light_card, outline=FACT_GREEN, width=5, shadow=True)
    cx, cy = c.left + pad, fy0 + pad
    _badge(c, ui("fact"), cx, cy, FACT_GREEN, "check")
    c.text(truth, cx, cy + 52 + 28, w, 76 if tall else 58, "bold", (16, 35, 64), 4, pitch=1.16, h=fy1 - pad - (cy + 80), role="fact", bg_hint=light_card)

    # VS badge on the seam
    bx, by = c.W // 2, my1 + gap // 2
    c.circle((bx, by), 46, pal.accent_fill, shadow=True)
    c.text(ui("vs"), bx - 40, by - 17, 80, 34, "bold", pal.accent_ink, 1, align="center", balance=False, role="chip", bg_hint=pal.accent_fill)
    return [c.finish()]
