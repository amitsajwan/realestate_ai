"""Agent promo v2: the real product screens (sample data) in a phone frame, so agents SEE the leads, not just read about them.

  cd backend && PYTHONPATH=. python scripts/promo_agents_v2.py [--out uploads/promo]

Slides (4:5): your day (who to call first) · a buyer you understand · buyers who match · posts made for you · join (QR).
Plus one group image (4:5) with the two lead screens side by side. Screens come from frontend/public/landing (sample data,
labelled). Every slide passes the creative layout checks.
"""
import argparse
import sys
from pathlib import Path
from typing import List

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from PIL import Image, ImageOps  # noqa: E402

from app.modules.agentprojects.cards import check, save_all  # noqa: E402
from app.modules.creative.layouts.base import Canvas, Rendered  # noqa: E402
from app.modules.creative.layouts.palette import get as palette  # noqa: E402
from scripts.promo_agents import JOIN_URL, SITE, _qr, join  # noqa: E402

SIZE = (1080, 1350)
SHOTS = BACKEND.parent / "frontend" / "public" / "landing"
DARK = (8, 14, 28)


def _screen(name: str, w: int, h: int, top: float = 0.0) -> Image.Image:
    """The screenshot scaled to width w, cropped to height h starting `top` (0..1) down the screen."""
    with Image.open(SHOTS / name) as im:
        im = im.convert("RGB")
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    y = int((im.height - h) * top) if im.height > h else 0
    return im.crop((0, y, w, y + h)) if im.height >= h else ImageOps.pad(im, (w, h), color=(255, 255, 255))


def _phone(c: Canvas, name: str, x: int, y: int, w: int, h: int, top: float = 0.0) -> None:
    bez = 16
    c.shadow((x, y, x + w, y + h), 54, blur=36, dy=24, alpha=0.55)
    c.rrect((x, y, x + w, y + h), 54, DARK, outline=(70, 86, 118), width=3, log=False)
    c.rrect((x + bez, y + bez, x + w - bez, y + h - bez), 40, fill_img=_screen(name, w - 2 * bez, h - 2 * bez, top), log=False)
    c.shapes.append((x, y, x + w, y + h))


def _footer(c: Canvas, n: int, i: int) -> None:
    c.brand_bar(right="Sample data")
    if n > 1:
        c.dots(n, i, c.W // 2, c.bottom - 104)


def screen_slide(i: int, n: int, kicker: str, title: str, accent: str, shot: str, top: float = 0.0) -> Rendered:
    c = Canvas(SIZE, palette("navy_gold"), f"promo2_{i}", i)
    y = c.text(kicker.upper(), c.left, c.top + 6, c.right - c.left, 26, "bold", c.pal.accent, 1, role="kicker", balance=False) + 24
    y = c.text(title, c.left, y, c.right - c.left, 58, "bold", c.pal.ink, 2, min_size=44, role="headline") + 8
    y = c.text(accent, c.left, y, c.right - c.left, 40, "semibold", c.pal.accent, 2, min_size=30, role="support") + 30
    w = 560
    h = c.bottom - 140 - y
    _phone(c, shot, (c.W - w) // 2, y, w, h, top)
    _footer(c, n, i)
    return c.finish()


def carousel() -> List[Rendered]:
    n = 5
    slides = [
        screen_slide(0, n, "For Pune property agents", "Every morning: who to call first.", "Your leads, sorted for you.",
                     "30-home-actions.jpg"),
        screen_slide(1, n, "Every enquiry", "A buyer you understand.", "Budget, area, timing. Hot or warm.", "19-lead-detail.jpg"),
        screen_slide(2, n, "New property?", "See which buyers match.", "Send it on WhatsApp in one tap.", "27-buyers-match.jpg"),
        screen_slide(3, n, "Your marketing", "Posts made for you.", "English, Hindi and Marathi. Your website too.",
                     "22-marketing-ready.jpg"),
        join(n),
    ]
    check(slides)
    return slides


def group_image(url: str = JOIN_URL) -> Rendered:
    """One image for groups: the headline, two real lead screens side by side, and the join box with the QR."""
    c = Canvas(SIZE, palette("navy_gold"), "promo2_group", 0)
    c.chip("Free pilot for Pune property agents", c.left, c.top, icon="star", size=26)
    y = c.text("Stop chasing “Price?” comments.", c.left, c.top + 70, c.right - c.left, 60, "bold", c.pal.ink, 2, min_size=44,
               role="headline") + 6
    y = c.text("Get buyers you can call.", c.left, y, c.right - c.left, 44, "bold", c.pal.accent, 1, min_size=34, role="headline",
               balance=False) + 26
    w, gap = 420, 40
    h = 620
    x0 = (c.W - 2 * w - gap) // 2
    _phone(c, "30-home-actions.jpg", x0, y, w, h)
    _phone(c, "19-lead-detail.jpg", x0 + w + gap, y, w, h)
    y += h + 26
    qr = 150
    c.rrect((c.left, y, c.right, y + qr + 36), 24, c.pal.accent_fill)
    c.rrect((c.left + 14, y + 10, c.left + 26 + qr, y + qr + 26), 10, (255, 255, 255))
    c.img.paste(_qr(url, qr), (c.left + 20, y + 18))
    tx = c.left + 56 + qr
    c.text("Free during the pilot. Low-cost after.", tx, y + 26, c.right - 24 - tx, 30, "bold", c.pal.accent_ink, 2, min_size=22,
           role="body", bg_hint=c.pal.accent_fill)
    c.text("Scan or open " + SITE + "/pilot", tx, y + qr - 22, c.right - 24 - tx, 30, "bold", c.pal.accent_ink, 1, min_size=22,
           role="body", balance=False, bg_hint=c.pal.accent_fill)
    c.brand_bar(right="Screens: sample data")
    r = c.finish()
    check([r])
    return r


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="uploads/promo")
    out = Path(ap.parse_args().out)
    files = save_all(carousel(), out, "v2")
    save_all([group_image()], out, "v2-group")
    print("wrote", [f.name for f in files], "and v2-group-1.jpg to", out)


if __name__ == "__main__":
    main()
