"""Layout 8, quote / tip card: a large typographic treatment with a giant quote mark and marker-highlighted key words."""
from typing import List

from PIL import Image, ImageDraw

from app.modules.marketing.images import load_font

from ..models import Copy, Design
from .base import Canvas, Rendered
from .palette import get


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "quote_tip", pattern=None, glow_at=(0.15, 0.85))
    w = c.right - c.left
    # giant quote mark, a decoration behind the text
    mask = Image.new("L", c.size, 0)
    ImageDraw.Draw(mask).text((c.left - 14, c.top + (150 if tall else 90)), "“", font=load_font(620 if tall else 480, "bold"), fill=70 if pal.light else 60, anchor="ls")
    c.img.paste(pal.accent_fill, (0, 0), mask)
    c.chip(str(copy.payload.get("kicker", "QUICK TIP")), c.left, c.top, icon="bolt")
    c.brand_bar(dark_bg=not pal.light)
    top, bottom = c.top + (270 if tall else 200), c.bottom - 64 - 40
    sup = copy.support or str(copy.payload.get("tip") or "")
    size = 100 if tall else 84
    hh = c.measure(copy.hook, w, size, "bold", 3, pitch=1.1, min_size=56)
    sup_h = c.measure(sup, w, 40, "medium", 3, pitch=1.3, balance=False) if sup else 0
    total = hh + (44 + 6 + 34 + sup_h if sup else 0)
    y = top + max(0, (bottom - top - total) // 2)
    y = c.text(copy.hook, c.left, y, w, size, "bold", pal.ink, 3, pitch=1.1, min_size=56, emph=design.emphasis, marker=True, role="hook")
    if sup:
        c.rrect((c.left, y + 44, c.left + 110, y + 50), 3, pal.accent_fill)
        c.text(sup, c.left, y + 44 + 6 + 34, w, 40, "medium", pal.muted, 3, pitch=1.3, balance=False, role="support")
    return [c.finish()]
