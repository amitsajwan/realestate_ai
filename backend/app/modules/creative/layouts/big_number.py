"""Layout 1, big-number hero: one huge number, a one-line meaning, a soft glow behind it."""
from typing import List

from ..models import Copy, Design
from .base import Canvas, Rendered, footer_h, known, mix
from .palette import get


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "big_number", pattern="rings", glow_at=(0.5, 0.36))
    p = copy.payload
    value, label = str(p.get("value", "")), str(p.get("label", ""))
    c.chip(str(p.get("kicker", "WORTH REMEMBERING")), c.left, c.top, icon="star")
    w = c.right - c.left
    top, bottom = c.top + 110, c.bottom - footer_h() - 110
    num_size = 470 if tall else 380
    num_fs, _, num_h, _ = c.fit(value, w, num_size, "bold", 1, int(num_size * 0.26), balance=False)
    lab_size = 68 if tall else 58
    lab_h = c.measure(label, w, lab_size, "bold", 3, pitch=1.14)
    sup_h = c.measure(copy.support, w, 36, "medium", 2, pitch=1.3) if copy.support else 0
    gap = 34
    total = num_h + 40 + 10 + gap + lab_h + (gap + sup_h if sup_h else 0)
    y = top + max(0, (bottom - top - total) // 2)
    c.glow((c.W // 2, y + num_h // 2), 480, pal.glow, 0.30 if not pal.light else 0.45)
    vy = c.text(value, c.left, y, w, num_fs, "bold", pal.accent, 1, balance=False, role="hero", min_size=int(num_size * 0.26))
    by = vy + 40
    c.rrect((c.left, by, c.left + 150, by + 10), 5, pal.accent_fill)
    y = by + 10 + gap
    y = c.text(label, c.left, y, w, lab_size, "bold", pal.ink, 3, pitch=1.14, role="label")
    if copy.support:
        c.text(copy.support, c.left, y + gap, w, 36, "medium", pal.muted, 2, pitch=1.3, balance=False, role="support")
    c.brand_bar(right=known(copy.card_cta or "Save this"), dark_bg=not pal.light)
    return [c.finish()]
