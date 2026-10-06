"""Layout 3, checklist / carousel: a cover with a huge hook and a swipe cue, one idea per slide with a big numeral and progress
dots, and a closing save-this slide."""
from typing import List

from PIL import Image, ImageDraw

from app.modules.marketing.images import load_font

from ..models import Copy, Design
from .base import Canvas, Rendered, brand_name, mix
from .palette import get


def _cue(c: Canvas, n: int, active: int, last: bool) -> None:
    """Progress dots on the left, a 'Swipe' cue on the right (none on the last slide)."""
    y = c.bottom - 40
    pal = c.pal
    x0 = c.left + 10
    for i in range(n):
        if i == active:
            c.rrect((x0, y - 8, x0 + 44, y + 8), 8, pal.accent_fill)
            x0 += 44 + 14
        else:
            c.circle((x0 + 8, y), 8, mix(pal.ink, pal.bg_bottom, 0.7 if not pal.light else 0.55))
            x0 += 16 + 14
    if not last:
        w = 214
        c.rrect((c.right - w, y - 34, c.right, y + 34), 34, pal.accent_fill, shadow=True)
        c.text("Swipe", c.right - w + 34, y - 13, 110, 28, "bold", pal.accent_ink, 1, balance=False, role="chip", bg_hint=pal.accent_fill)
        c.icon("chevrons", (c.right - 46, y), 34, pal.accent_ink, 5)


def _cover(copy: Copy, design: Design, n: int) -> Rendered:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "checklist", 0, pattern="dots", glow_at=(0.9, 0.05))
    w = c.right - c.left
    c.logo(c.left, c.top, 64)
    c.text(brand_name(), c.left + 82, c.top + 14, 420, 30, "semibold", pal.ink, 1, balance=False, role="brand")
    c.chip(str(copy.payload.get("kicker", "SAVE THIS")), c.right, c.top + 4, icon="bookmark", align_right=True, size=24)
    top, cue_top = c.top + 130, c.bottom - 40 - 34 - 40
    skel_h = 250 if tall else 150
    hook_size = 122 if tall else 104
    hook_h = c.measure(copy.hook, w, hook_size, "bold", 3, pitch=1.06, min_size=64)
    sub = copy.support or f"{len(copy.slides)} things, one per slide"
    sub_h = c.measure(sub, w, 40, "medium", 2, pitch=1.3)
    total = hook_h + 34 + sub_h
    y = top + max(0, (cue_top - skel_h - 40 - top - total) // 2)
    c.rrect((c.left, y, c.left + 110, y + 10), 5, pal.accent_fill)
    y = c.text(copy.hook, c.left, y + 34, w, hook_size, "bold", pal.ink, 3, pitch=1.06, min_size=64, emph=design.emphasis, role="hook") + 34
    c.text(sub, c.left, y, w, 40, "medium", pal.muted, 2, pitch=1.3, balance=False, role="support")
    # Checklist skeleton: three rows, each a check disc and a bar, so the cover already reads as "a list inside".
    rows = 3
    rh = skel_h // rows
    for i in range(rows):
        ry = cue_top - skel_h + i * rh + rh // 2
        c.circle((c.left + 30, ry), 26, pal.accent_fill if i == 0 else pal.card)
        if i == 0:
            c.icon("check", (c.left + 30, ry), 28, pal.accent_ink, 5)
        bw = int(w * (0.78, 0.62, 0.7)[i])
        c.rrect((c.left + 82, ry - 15, c.left + 82 + bw, ry + 15), 15, pal.card if not pal.light else (226, 214, 190))
    _cue(c, n, 0, False)
    return c.finish()


def _slide(copy: Copy, design: Design, idx: int, n: int, text: str) -> Rendered:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "checklist", idx, pattern=("grid", "rings", "dots")[idx % 3], glow_at=((0.1, 0.12), (0.92, 0.2), (0.5, 0.9))[idx % 3])
    w = c.right - c.left
    ghost = Image.new("L", c.size, 0)
    ImageDraw.Draw(ghost).text((c.W - 30, c.H - 120), str(idx), font=load_font(820 if tall else 640, "bold"), fill=46 if not pal.light else 60, anchor="rs")
    c.img.paste(pal.accent_fill, (0, 0), ghost)
    c.text(f"{idx:02d} / {n - 2:02d}", c.left, c.top + 16, 300, 30, "semibold", pal.muted, 1, balance=False, role="meta")
    c.logo(c.right - 56, c.top + 4, 56)
    # numeral in a big accent disc, then the idea
    r = 92 if tall else 70
    cy = c.top + 130 + r
    c.circle((c.left + r, cy), r, pal.accent_fill, shadow=True)
    c.text(f"{idx}", c.left, cy - int(0.35 * r * 1.45), 2 * r, int(r * 1.45), "bold", pal.accent_ink, 1, align="center", balance=False, role="numeral",
           bg_hint=pal.accent_fill)
    top = cy + r + 60
    bottom = c.bottom - 120
    size = 100 if tall else 78
    h = c.measure(text, w, size, "bold", 6, pitch=1.14, min_size=46)
    y = top + max(0, (bottom - top - h) // 2)
    c.text(text, c.left, y, w, size, "bold", pal.ink, 6, pitch=1.14, min_size=46, h=bottom - y, role="slide")
    _cue(c, n, idx, False)
    return c.finish()


def _closing(copy: Copy, design: Design, n: int) -> Rendered:
    pal, (W, H) = get(design.palette), design.size
    tall = H > W
    c = Canvas(design.size, pal, "checklist", n - 1, pattern="rings", glow_at=(0.5, 0.45))
    w = c.right - c.left
    c.icon("bookmark", (c.left + 80, c.top + (190 if tall else 130)), 170 if tall else 120, pal.accent, 6)
    y = c.top + (330 if tall else 250)
    y = c.text("Save this" if copy.card_cta in ("Swipe", "") else copy.card_cta, c.left, y, w, 150 if tall else 110, "bold", pal.ink, 2, pitch=1.06, role="hook")
    y = c.text(copy.cta_question, c.left, y + 40, w, 56 if tall else 44, "medium", pal.muted, 4, pitch=1.3, balance=False, role="support")
    c.brand_bar(y=c.bottom - 130, dark_bg=not pal.light)
    _cue(c, n, n - 1, True)
    return c.finish()


def render(copy: Copy, design: Design) -> List[Rendered]:
    slides = copy.slides[:5]
    n = len(slides) + 2
    out = [_cover(copy, design, n)]
    out += [_slide(copy, design, i + 1, n, s) for i, s in enumerate(slides)]
    out.append(_closing(copy, design, n))
    return out
