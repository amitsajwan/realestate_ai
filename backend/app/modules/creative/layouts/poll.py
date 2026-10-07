"""Layout 4, question / poll card: a bold question and two big choice cards (A and B) with a VS badge, and a vote button."""
from typing import List

from ..models import Copy, Design
from .base import Canvas, Rendered, footer_h, ui
from .palette import get


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "poll", pattern="rings", glow_at=(0.5, 0.5))
    p = copy.payload
    question = str(p.get("question") or copy.hook)
    opts = [str(o) for o in (p.get("options") or ["", ""])][:2]
    w = c.right - c.left
    c.chip(str(p.get("kicker", "THIS OR THAT")), c.left, c.top, icon="bolt")
    qy = c.top + 100
    q_size = 104 if tall else 78
    qh = c.measure(question, w, q_size, "bold", 3, pitch=1.08, min_size=52)
    c.text(question, c.left, qy, w, q_size, "bold", pal.ink, 3, pitch=1.08, min_size=52, emph=design.emphasis, role="hook")
    btn_h = 104 if tall else 92
    btn_y = c.bottom - footer_h() - 34 - btn_h
    cards_top = qy + qh + 56
    _cap = 560 if tall else 420
    cards_bot = btn_y - 44
    if cards_bot - cards_top > _cap:  # compact cards; spare room goes above and below
        _spare = cards_bot - cards_top - _cap
        cards_top += _spare // 2
        cards_bot -= _spare // 2
    gap = 40
    cw = (w - gap) // 2
    sizes = [(pal.accent_fill, pal.accent_ink), ((255, 255, 255) if not pal.light else (16, 35, 64), (16, 35, 64) if not pal.light else (255, 255, 255))]
    for i, (opt, letter) in enumerate(zip(opts, "AB")):
        x0 = c.left + i * (cw + gap)
        box = (x0, cards_top, x0 + cw, cards_bot)
        c.rrect(box, 40, pal.card, outline=pal.accent_fill if i == 0 else pal.edge, width=4, shadow=True)
        r = 54
        cx, cy = x0 + 34 + r, cards_top + 34 + r
        fill, ink = sizes[i]
        c.circle((cx, cy), r, fill, shadow=True)
        c.text(letter, cx - r, cy - int(0.35 * 76), 2 * r, 76, "bold", ink, 1, align="center", balance=False, role="numeral", bg_hint=fill)
        ty = cy + r + 34
        c.text(opt, x0 + 34, ty, cw - 68, 68 if tall else 52, "bold", pal.card_ink, 5, pitch=1.14, min_size=30, h=cards_bot - 34 - ty, role="option", bg_hint=pal.card)
    # VS badge between the cards
    bx, by = c.W // 2, cards_top + (cards_bot - cards_top) // 2
    c.circle((bx, by), 44, pal.accent_fill if pal.light else (255, 255, 255), shadow=True)
    c.text(ui("vs"), bx - 40, by - 16, 80, 32, "bold", (24, 30, 44), 1, align="center", balance=False, role="chip",
           bg_hint=pal.accent_fill if pal.light else (255, 255, 255))
    # vote button
    c.rrect((c.left, btn_y, c.right, btn_y + btn_h), btn_h // 2, pal.accent_fill, shadow=True)
    c.icon("bubble", (c.left + 86, btn_y + btn_h // 2), 50, pal.accent_ink)
    c.text(ui("vote_ab"), c.left + 136, btn_y + (btn_h - int(0.7 * 36)) // 2, w - 170, 36,
           "bold", pal.accent_ink, 1, balance=False, role="chip", bg_hint=pal.accent_fill, min_size=26)
    c.brand_bar(dark_bg=not pal.light)
    return [c.finish()]
