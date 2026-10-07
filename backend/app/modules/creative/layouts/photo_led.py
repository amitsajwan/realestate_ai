"""Layout 6, photo-led card: a full-bleed real photo, a dark gradient, the hook large over it."""
from pathlib import Path
from typing import List

from ..models import Copy, Design
from .base import Canvas, Rendered, footer_h, known, photo, photo_keys, scrim, ui
from .palette import get


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    if pal.light:
        pal = get("navy_gold")
    tall = H > W
    keys = photo_keys()
    key = design.photo if design.photo in keys or design.photo == "none" or Path(design.photo).is_file() else (keys[0] if keys else "")
    img = photo(key, design.size, centering=(0.5, 0.42)) if key and key != "none" else None
    if img is None:
        from .base import gradient
        img = gradient(design.size, pal.bg_top, pal.bg_bottom)
    img = scrim(img, 0.30, 0.94)
    img = scrim(img, 0.50, 0.55, top=True)
    c = Canvas(design.size, pal, "photo_led", bg=img)
    w = c.right - c.left
    c.chip(str(copy.payload.get("kicker", "BUYER NOTE")), c.left, c.top, icon="home")
    # bottom-up: brand bar, cta, then support and hook above it
    c.brand_bar(right=ui("illustrative") if key in keys else None, dark_bg=True)  # a real listing photo needs no label
    cta_y = c.bottom - footer_h() - 40 - int(30 * 1.95)
    cta = known(copy.card_cta or "Save this")
    c.chip(cta, c.left, cta_y, outline=pal.accent, ink=pal.accent, icon="bookmark", size=30)
    hook_size = 112 if tall else 92
    hh = c.measure(copy.hook, w, hook_size, "bold", 3, pitch=1.06, min_size=60)
    sup_h = c.measure(copy.support, w, 44, "medium", 2, pitch=1.3, balance=False) if copy.support else 0
    bottom = cta_y - 40
    y = bottom - (sup_h + 28 if sup_h else 0) - hh
    c.rrect((c.left, y - 34, c.left + 110, y - 24), 5, pal.accent_fill)
    y = c.text(copy.hook, c.left, y, w, hook_size, "bold", (255, 255, 255), 3, pitch=1.06, min_size=60, emph=design.emphasis, role="hook")
    if copy.support:
        c.text(copy.support, c.left, y + 28, w, 44, "medium", (222, 228, 240), 2, pitch=1.3, balance=False, role="support")
    return [c.finish()]
