"""Layout 5, before / after ("messy vs clean"): two columns with small drawn illustrations, crosses on the left, ticks on the right."""
import math
from typing import List

from ..models import Copy, Design
from .base import Canvas, Rendered, mix, footer_h
from .palette import FACT_GREEN, MYTH_RED, get


def _messy_art(c: Canvas, box, dark: bool) -> None:
    """Three tilted sheets and a scribble: paperwork in a heap."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    for ang, dx, dy, col in ((-14, -46, 6, (214, 204, 186)), (9, 38, -4, (232, 224, 208)), (-3, 0, 14, (246, 240, 228))):
        w, h = 120, 150
        a = math.radians(ang)
        pts = []
        for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            pts.append((cx + dx + px * math.cos(a) - py * math.sin(a), cy + dy + py * math.cos(a) + px * math.sin(a)))
        bx0, by0 = int(min(p[0] for p in pts)) - 4, int(min(p[1] for p in pts)) - 4
        bx1, by1 = int(max(p[0] for p in pts)) + 4, int(max(p[1] for p in pts)) + 4
        c.shadow((bx0 + 14, by0 + 14, bx1 - 14, by1 - 14), 8, 12, 8, 0.4)
        c.shape((bx0, by0, bx1, by1), lambda d, s, pts=pts, bx0=bx0, by0=by0: d.polygon([((px - bx0) * s, (py - by0) * s) for px, py in pts], fill=255), col)
    c.line([(cx - 40, cy - 10), (cx - 10, cy + 12), (cx + 14, cy - 14), (cx + 40, cy + 14)], 6, MYTH_RED)


def _clean_art(c: Canvas, box) -> None:
    """A tidy stack: three aligned cards with a tick."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    for i in range(3):
        top = cy - 62 + i * 42
        c.rrect((cx - 92, top, cx + 92, top + 34), 10, (255, 255, 255), outline=(200, 214, 206), width=2, shadow=(i == 0), log=False)
        c.rrect((cx - 76, top + 11, cx + 10 - i * 14, top + 23), 6, (196, 208, 226), log=False)
    c.circle((cx + 70, cy - 46), 26, FACT_GREEN, shadow=True, log=False)
    c.icon("check", (cx + 70, cy - 46), 28, (255, 255, 255), 5)


def _column(c: Canvas, box, items: List[str], good: bool, tall: bool) -> None:
    x0, y0, x1, y1 = box
    pal = c.pal
    fill = (255, 253, 246) if good else (22, 34, 58)
    ink = (16, 35, 64) if good else (226, 232, 244)
    c.rrect(box, 34, fill, outline=FACT_GREEN if good else MYTH_RED, width=4, shadow=True)
    art_h = 190 if tall else 140
    art = (x0, y0 + 14, x1, y0 + 14 + art_h)
    (_clean_art(c, art) if good else _messy_art(c, art, True))
    label = "CLEAN" if good else "MESSY"
    tag = FACT_GREEN if good else MYTH_RED
    lw = 150
    c.rrect((x0 + (x1 - x0 - lw) // 2, y0 + 14 + art_h, x0 + (x1 - x0 - lw) // 2 + lw, y0 + 14 + art_h + 46), 23, tag)
    c.text(label, x0 + (x1 - x0 - lw) // 2, y0 + 14 + art_h + 11, lw, 24, "bold", (255, 255, 255), 1, align="center", balance=False, role="chip", bg_hint=tag)
    y = y0 + 14 + art_h + 46 + 26
    n = min(3, len(items))
    rows_h = (y1 - 26 - y)
    row_h = rows_h // max(1, n)
    tx = x0 + 26 + 46
    for i, it in enumerate(items[:n]):
        ry = y + i * row_h
        c.circle((x0 + 26 + 20, ry + 20), 20, tag, log=False)
        c.icon("check" if good else "cross", (x0 + 26 + 20, ry + 20), 20, (255, 255, 255), 4)
        c.text(it, tx, ry + 4, x1 - 22 - tx, 34 if tall else 28, "semibold", ink, 4, pitch=1.22, min_size=22, h=row_h - 14, balance=False,
               role="item", bg_hint=fill)


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "before_after", pattern="dots", glow_at=(0.9, 0.1))
    p = copy.payload
    w = c.right - c.left
    c.chip(str(p.get("kicker", "SIDE BY SIDE")), c.left, c.top, icon="bolt")
    hy = c.top + 100
    hsize = 84 if tall else 68
    hh = c.measure(copy.hook, w, hsize, "bold", 2, pitch=1.08, min_size=50)
    c.text(copy.hook, c.left, hy, w, hsize, "bold", pal.ink, 2, pitch=1.08, min_size=50, emph=design.emphasis, role="hook")
    top, bottom = hy + hh + 40, c.bottom - footer_h() - 34
    gap = 28
    cw = (w - gap) // 2
    _column(c, (c.left, top, c.left + cw, bottom), [str(x) for x in p.get("messy", [])], False, tall)
    _column(c, (c.left + cw + gap, top, c.right, bottom), [str(x) for x in p.get("clean", [])], True, tall)
    c.brand_bar(dark_bg=not pal.light)
    return [c.finish()]
