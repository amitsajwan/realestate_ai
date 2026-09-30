"""Render the library's cards in the brand style.

Facebook keeps the 1080x1080 square:  <uploads>/calendar/<slug>.jpg
Instagram uses 4:5 portrait 1080x1350: <uploads>/calendar/ig/<slug>.jpg  (a square is cropped to 3:4 in the profile grid and loses its sides)
All text stays inside the 84 px margins (the grid trims about 34 px per side).
"""
import inspect
import shutil
from pathlib import Path
from typing import Iterable, Optional, Tuple

from PIL import Image

from app.modules.marketing import images as _images
from app.modules.marketing.brand_posts import render_brand_post
from app.modules.marketing.images import (GOLD, PITCH, SOFT, SQUARE, WHITE, DARK_INK, Card, _chip, _stamp_logo, brand_background, load_font, save_jpeg)

from .library import ENTRIES, Entry

PORTRAIT: Tuple[int, int] = getattr(_images, "PORTRAIT", (1080, 1350))
STATIC_DIR = Path(_images.__file__).parent / "static_cards"  # Hindi/Marathi cards pre-rendered in Chrome (Pillow cannot shape Devanagari)
SUBDIR = "calendar"
CHANNELS = ("facebook_page", "instagram")


def image_path(slug: str, channel: str = "facebook_page") -> str:
    """Path of the card relative to the uploads directory (stored in the calendar row)."""
    return f"{SUBDIR}/ig/{slug}.jpg" if channel == "instagram" else f"{SUBDIR}/{slug}.jpg"


def _card(kicker: str, title: str, points: list, size: Tuple[int, int]) -> Card:
    """The brand card at any size. Uses marketing's renderer when it accepts `size`, else the same layout drawn here."""
    if "size" in inspect.signature(render_brand_post).parameters:
        return render_brand_post(kicker, title, points, size=size)
    c = Card(size, brand_background(size, "pune-property", floor=1.0, tall=0.2))
    _, y = _chip(c, kicker, c.left, c.top)
    y += 34
    tall = size[1] > size[0]
    y = c.block(title, y, 74 if tall else 68, WHITE, 4 if tall else 3, 42, weight="bold") + (34 if tall else 26)
    avail = c.bottom - 110 - y
    for sz in ((44, 40, 36, 32, 28) if tall else (40, 36, 32, 28)):
        need = sum(c.height_of(p, sz, 2, 24, x=c.left + 64, weight="medium") + 20 for p in points)
        if need <= avail:
            break
    for i, p in enumerate(points):
        cy = y + int(sz * PITCH) // 2 + 4
        c.draw.ellipse((c.left, cy - 21, c.left + 42, cy + 21), fill=GOLD)
        c.draw.text((c.left + 21, cy), str(i + 1), font=load_font(26, "bold"), fill=DARK_INK, anchor="mm")
        y = c.block(p, y, sz, WHITE, 2, 24, x=c.left + 64, weight="medium") + (28 if tall else 20)
    _stamp_logo(c, c.left, c.bottom - 88, 88)
    c.block("PUNE Property", c.bottom - 88, 34, GOLD, 1, 20, x=c.left + 108, weight="semibold")
    c.block("Find. Compare. Decide.", c.bottom - 88 + int(34 * PITCH), 26, SOFT, 1, 18, x=c.left + 108, weight="medium")
    return c


def _to_portrait(square: Path, dest: Path) -> None:
    """A pre-rendered square card on a 1080x1350 canvas: the card sits in the middle and its top and bottom rows are stretched to fill
    the rest, so there is no seam. Its text stays inside the original margins."""
    with Image.open(square) as im:
        im = im.convert("RGB")
        if im.size != SQUARE:
            im = im.resize(SQUARE, Image.LANCZOS)
        canvas = Image.new("RGB", PORTRAIT)
        pad = (PORTRAIT[1] - SQUARE[1]) // 2
        canvas.paste(im.crop((0, 0, SQUARE[0], 1)).resize((SQUARE[0], pad)), (0, 0))
        canvas.paste(im.crop((0, SQUARE[1] - 1, SQUARE[0], SQUARE[1])).resize((SQUARE[0], PORTRAIT[1] - pad - SQUARE[1])), (0, pad + SQUARE[1]))
        canvas.paste(im, (0, pad))
        save_jpeg(canvas, dest)


def render_entry(entry: Entry, out_dir: Path, channel: str = "facebook_page") -> Path:
    """Render one card into out_dir (Instagram cards go to out_dir/ig/)."""
    ig = channel == "instagram"
    target = out_dir / "ig" if ig else out_dir
    target.mkdir(parents=True, exist_ok=True)
    dest = target / f"{entry.slug}.jpg"
    if entry.card_from:
        static = STATIC_DIR / f"{entry.card_from}.jpg"
        if not static.is_file():
            raise FileNotFoundError(f"pre-rendered card missing: {static.name}")
        if ig:
            _to_portrait(static, dest)
        else:
            shutil.copyfile(static, dest)
    else:
        save_jpeg(_card(entry.kicker, entry.title, list(entry.points), PORTRAIT if ig else SQUARE).img, dest)
    return dest


def render_all(out_dir: Path, entries: Optional[Iterable[Entry]] = None, only: Optional[Iterable[str]] = None) -> list:
    wanted = set(only) if only else None
    paths = []
    for e in (entries or ENTRIES):
        if wanted is None or e.slug in wanted:
            paths += [render_entry(e, out_dir, ch) for ch in CHANNELS]
    return paths


def ensure_card(entry: Entry, uploads: Path, channel: str = "facebook_page") -> Path:
    """The card file for an entry and channel under the uploads dir, rendering it the first time."""
    dest = uploads / image_path(entry.slug, channel)
    return dest if dest.is_file() else render_entry(entry, uploads / SUBDIR, channel)
