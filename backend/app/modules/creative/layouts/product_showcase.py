"""Layout 7, product showcase for agent-attraction posts: a drawn phone with a mini agent-site listing card and an INTERESTED
comment, plus a floating lead card (looking for, budget, timing). Everything on the phone is an illustration, labelled as such."""
from typing import List

from ..models import Copy, Design
from .base import Canvas, Rendered, mix, photo
from .palette import get

DARK = (8, 14, 28)
SCREEN = (246, 247, 250)
INK = (16, 35, 64)
GREY = (104, 116, 138)


def _phone(c: Canvas, x0: int, y0: int, pw: int, ph: int, k: float, key: str) -> None:
    pal = c.pal
    c.glow((x0 + pw // 2, y0 + ph // 3), int(pw * 1.25), pal.glow, 0.28)
    c.shadow((x0, y0, x0 + pw, y0 + ph), int(58 * k), blur=40, dy=30, alpha=0.6)
    c.rrect((x0, y0, x0 + pw, y0 + ph), int(58 * k), DARK, outline=(66, 82, 112), width=3, log=False)
    bez = int(14 * k)
    sx0, sy0, sx1, sy1 = x0 + bez, y0 + bez, x0 + pw - bez, y0 + ph - bez
    c.rrect((sx0, sy0, sx1, sy1), int(46 * k), SCREEN, log=False)
    c.rrect((x0 + pw // 2 - int(54 * k), sy0 + int(10 * k), x0 + pw // 2 + int(54 * k), sy0 + int(10 * k) + int(26 * k)), int(13 * k), DARK, log=False)
    sw = sx1 - sx0
    m = int(22 * k)
    y = sy0 + int(54 * k)
    # app bar
    c.logo(sx0 + m, y, int(34 * k))
    c.text("PUNE Property", sx0 + m + int(44 * k), y + int(6 * k), sw // 2, int(21 * k), "bold", INK, 1, balance=False, role="mock", bg_hint=SCREEN, min_size=14)
    y += int(34 * k) + int(18 * k)
    # listing card with photo
    card_h = int(330 * k)
    c.rrect((sx0 + m, y, sx1 - m, y + card_h), int(22 * k), (255, 255, 255), outline=(222, 226, 236), width=2, shadow=True, log=False)
    ph_h = int(170 * k)
    img = photo(key, (sx1 - sx0 - 2 * m - 12, ph_h), centering=(0.5, 0.55)) if key else None
    if img is not None:
        c.rrect((sx0 + m + 6, y + 6, sx1 - m - 6, y + 6 + ph_h), int(17 * k), fill_img=img, log=False)
    else:
        c.rrect((sx0 + m + 6, y + 6, sx1 - m - 6, y + 6 + ph_h), int(17 * k), (196, 208, 226), log=False)
    chip_w = int(150 * k)
    c.rrect((sx0 + m + 16, y + 16, sx0 + m + 16 + chip_w, y + 16 + int(28 * k)), int(14 * k), (240, 180, 64), log=False)
    c.text("SAMPLE LISTING", sx0 + m + 16, y + 16 + int(6 * k), chip_w, int(14 * k), "bold", (24, 30, 44), 1, align="center", balance=False, role="mock", bg_hint=(240, 180, 64), min_size=10)
    ty = y + 6 + ph_h + int(16 * k)
    c.text("2 BHK Apartment", sx0 + m + 14, ty, sw - 2 * m - 28, int(26 * k), "bold", INK, 1, balance=False, role="mock", bg_hint=(255, 255, 255), min_size=14)
    c.text("Kharadi, Pune", sx0 + m + 14, ty + int(36 * k), sw - 2 * m - 28, int(20 * k), "medium", GREY, 1, balance=False, role="mock", bg_hint=(255, 255, 255), min_size=12)
    bw = int(150 * k)
    by = y + card_h - int(50 * k)
    c.rrect((sx1 - m - 14 - bw, by, sx1 - m - 14, by + int(34 * k)), int(17 * k), INK, log=False)
    c.text("Get details", sx1 - m - 14 - bw, by + int(8 * k), bw, int(17 * k), "bold", (255, 255, 255), 1, align="center", balance=False, role="mock", bg_hint=INK, min_size=11)
    y += card_h + int(22 * k)
    # comments
    c.text("Comments", sx0 + m, y, sw, int(20 * k), "bold", GREY, 1, balance=False, role="mock", bg_hint=SCREEN, min_size=12)
    y += int(34 * k)
    for txt, gold in (("INTERESTED", True), ("Is it still available?", False)):
        c.circle((sx0 + m + int(17 * k), y + int(17 * k)), int(17 * k), (184, 196, 216) if not gold else (240, 180, 64), log=False)
        bwid = int((176 if gold else 232) * k)
        c.rrect((sx0 + m + int(44 * k), y, sx0 + m + int(44 * k) + bwid, y + int(36 * k)), int(18 * k), (255, 243, 214) if gold else (232, 236, 244), log=False)
        c.text(txt, sx0 + m + int(56 * k), y + int(9 * k), bwid - int(24 * k), int(18 * k), "bold" if gold else "medium", INK, 1, balance=False,
               role="mock", bg_hint=(255, 243, 214) if gold else (232, 236, 244), min_size=11)
        y += int(48 * k)


def render(copy: Copy, design: Design) -> List[Rendered]:
    pal, (W, H) = get(design.palette), design.size
    if pal.light:
        pal = get("navy_gold")
    tall = H > W
    k = 1.0 if tall else 0.78
    c = Canvas(design.size, pal, "product_showcase", pattern="grid", glow_at=(0.85, 0.05))
    w = c.right - c.left
    c.chip(str(copy.payload.get("kicker", "FOR AGENTS")), c.left, c.top, icon="bolt")
    c.logo(c.right - 64, c.top, 64)
    hy = c.top + 100
    hsize = 92 if tall else 60
    hook_w = w
    hh = c.measure(copy.hook, hook_w, hsize, "bold", 3, pitch=1.06, min_size=54)
    y = c.text(copy.hook, c.left, hy, hook_w, hsize, "bold", pal.ink, 3, pitch=1.06, min_size=54, emph=design.emphasis, role="hook")
    if copy.support:
        y = c.text(copy.support, c.left, y + 22, w, 36 if tall else 30, "medium", pal.muted, 2, pitch=1.3, balance=False, role="support")
    top = y + 36
    k = max(0.6, min(1.0, (c.bottom - top - 12 - 38) / 608))
    pw = int(430 * k)
    ph = int(pw * 1.95)
    px = c.left + 10
    key = design.photo or "living-room"
    _phone(c, px, top, pw, ph, k, key)

    # floating "INTERESTED" comment
    rx0 = px + pw - int(40 * k)
    bub_w = min(c.right - rx0, int(430 * k) + 40)
    bx0 = c.right - bub_w
    by0 = top + int(30 * k)
    bh = int(104 * k)
    c.rrect((bx0, by0, c.right, by0 + bh), int(30 * k), (255, 255, 255), shadow=True)
    c.circle((bx0 + int(56 * k), by0 + bh // 2), int(30 * k), (240, 180, 64))
    c.text("INTERESTED", bx0 + int(104 * k), by0 + int(20 * k), bub_w - int(124 * k), int(38 * k), "bold", INK, 1, balance=False, role="ui", bg_hint=(255, 255, 255), min_size=22)
    c.text("New comment on your post", bx0 + int(104 * k), by0 + int(20 * k) + int(52 * k), bub_w - int(124 * k), int(21 * k), "medium", GREY, 1, balance=False,
           role="ui", bg_hint=(255, 255, 255), min_size=16)
    # arrow from comment to the lead card
    ax = bx0 + bub_w // 2
    c.line([(ax, by0 + bh + 10), (ax, by0 + bh + int(54 * k))], 5, pal.accent)
    c.line([(ax - 14, by0 + bh + int(54 * k) - 14), (ax, by0 + bh + int(54 * k)), (ax + 14, by0 + bh + int(54 * k) - 14)], 5, pal.accent)

    # floating lead card
    ly0 = by0 + bh + int(64 * k)
    lh = int(410 * k)
    lx0 = bx0
    c.rrect((lx0, ly0, c.right, ly0 + lh), int(34 * k), (255, 255, 255), shadow=True)
    lm = int(30 * k)
    c.circle((lx0 + lm + int(26 * k), ly0 + lm + int(26 * k)), int(26 * k), pal.accent_fill)
    c.icon("bolt", (lx0 + lm + int(26 * k), ly0 + lm + int(26 * k)), int(28 * k), pal.accent_ink)
    c.text("New lead", lx0 + lm + int(68 * k), ly0 + lm + int(6 * k), bub_w - 2 * lm - int(68 * k), int(32 * k), "bold", INK, 1, balance=False, role="ui", bg_hint=(255, 255, 255), min_size=20)
    c.text("Buyer summary", lx0 + lm + int(68 * k), ly0 + lm + int(6 * k) + int(40 * k), bub_w - 2 * lm - int(68 * k), int(20 * k), "medium", GREY, 1, balance=False,
           role="ui", bg_hint=(255, 255, 255), min_size=14)
    ry = ly0 + lm + int(52 * k) + int(34 * k)
    c.rrect((lx0 + lm, ry - int(14 * k), c.right - lm, ry - int(14 * k) + 2), 1, (226, 230, 240), log=False)
    rows = (("Looking for", "2 BHK"), ("Area", "Kharadi"), ("Budget", "Noted"), ("Timing", "Within 3 months"))
    rh = int(52 * k)
    for lab, val in rows:
        c.text(lab, lx0 + lm, ry + int(6 * k), int(150 * k), int(21 * k), "medium", GREY, 1, balance=False, role="ui", bg_hint=(255, 255, 255), min_size=14)
        c.text(val, lx0 + lm + int(160 * k), ry, bub_w - 2 * lm - int(160 * k), int(28 * k), "bold", INK, 1, align="left", balance=False, role="ui",
               bg_hint=(255, 255, 255), min_size=16)
        ry += rh
    bty = ly0 + lh - lm - int(58 * k)
    c.rrect((lx0 + lm, bty, c.right - lm, bty + int(58 * k)), int(29 * k), INK)
    c.text("Reply now", lx0 + lm, bty + int(14 * k), bub_w - 2 * lm, int(26 * k), "bold", (255, 255, 255), 1, align="center", balance=False, role="ui", bg_hint=INK, min_size=16)
    c.text("Illustration. Sample data.", bx0, ly0 + lh + 18, bub_w, 20, "medium", pal.muted, 1, align="right", balance=False, role="meta", min_size=16)
    return [c.finish()]
