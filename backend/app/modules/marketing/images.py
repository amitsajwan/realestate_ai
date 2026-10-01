"""Server-side share cards (Pillow + bundled Poppins). 1080x1080 carousel cards + one 1080x1920 status card.

Background photo: ONLY the listing's first image when it is one of our own uploads (`/uploads/images/<file>` that exists
under the backend uploads dir). Remote URLs, `..`, absolute paths and anything else are never opened or fetched.
Image text is English/numerals (Devanagari on images is out of scope), always inside safe margins over a dark overlay.
"""
import hashlib
import io
import random
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFile, ImageFont, ImageOps

from app.core import brand

from .facts import T, Facts

SQUARE = (1080, 1080)
STORY = (1080, 1920)
PORTRAIT = (1080, 1350)  # 4:5, what Instagram shows best; its profile grid crops to 3:4, which trims only about 34 px per side of this
MARGIN = 84
STORY_TOP, STORY_BOTTOM = 240, 300  # keep clear of the story app chrome
MAX_BYTES = 380 * 1024
MAX_SOURCE_BYTES = 20 * 1024 * 1024
WHITE, SOFT, ACCENT = (255, 255, 255), (214, 218, 228), (255, 214, 140)
GOLD = (240, 180, 64)  # the gold of the brand tagline (the Avasetu mark itself is #F0B13B)
FONT_DIR = Path(__file__).parent / "fonts"
FONT_FILES = {"regular": "Poppins-Regular.ttf", "medium": "Poppins-Medium.ttf",
              "semibold": "Poppins-SemiBold.ttf", "bold": "Poppins-Bold.ttf"}
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
UPLOAD_PATH_RE = re.compile(r"^/uploads/images/([A-Za-z0-9][A-Za-z0-9._-]{0,200})$")
PALETTES = [((16, 35, 64), (24, 55, 93)), ((14, 32, 60), (26, 60, 100)), ((18, 38, 70), (30, 62, 104))]  # brand navy
SILHOUETTE = (9, 21, 44)
LOGO_PATH = brand.MARK_PNG  # the Avasetu mark: gold disc, navy roof over a bridge arch (docs/brand/avasetu/mark.svg)
ImageFile.LOAD_TRUNCATED_IMAGES = False


# ---- safe source lookup ----------------------------------------------------------------------------
def local_upload_path(url: Optional[str], uploads_dir: Path) -> Optional[Path]:
    """Map a media url to a file under <uploads>/images, or None. Never touches any other path or URL."""
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None
    m = UPLOAD_PATH_RE.match(parsed.path or "")
    if not m or ".." in m.group(1):
        return None
    images = (Path(uploads_dir) / "images").resolve()
    cand = (images / m.group(1)).resolve()
    if cand.parent != images or not cand.is_file():
        return None
    return cand


def first_photo_url(media: List[dict]) -> Optional[str]:
    imgs = [(m.get("order") or 0, i, m) for i, m in enumerate(media or []) if (m.get("kind") or "image") == "image"]
    return min(imgs, key=lambda t: (t[0], t[1]))[2].get("url") if imgs else None


def _load_source(path: Optional[Path]) -> Optional[Image.Image]:
    """The listing photo as an RGB image (EXIF-rotated, capped in size), or None if missing/unreadable/oversized."""
    if path is None:
        return None
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            return None
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((2400, 2400), Image.LANCZOS)
            return im
    except Exception:
        return None


def _open_background(path: Optional[Path], size: Tuple[int, int]) -> Optional[Image.Image]:
    if path is None:
        return None
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            return None
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            return ImageOps.fit(im, size, Image.LANCZOS)
    except Exception:
        return None


# ---- backgrounds -----------------------------------------------------------------------------------
def palette_for(seed: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    return PALETTES[hashlib.md5(seed.encode("utf8")).digest()[0] % len(PALETTES)]


def gradient_card(size: Tuple[int, int], seed: str) -> Image.Image:
    top, bottom = palette_for(seed)
    mask = Image.linear_gradient("L").resize(size)
    return ImageOps.colorize(mask, black=top, white=bottom)


def dark_overlay(img: Image.Image) -> Image.Image:
    """Uniform-ish dark scrim, heavier toward the bottom, so white text is legible on any photo."""
    grad = Image.linear_gradient("L").resize(img.size).point(lambda v: 130 + int(v * 0.42))
    return Image.composite(Image.new("RGB", img.size, (8, 10, 16)), img, grad)


# ---- text measuring / fitting ----------------------------------------------------------------------
PITCH = 1.25  # line pitch = PITCH x font size (Poppins has generous natural spacing)


@lru_cache(maxsize=96)
def load_font(size: int, weight: str = "regular"):
    """Poppins (bundled, SIL Open Font License) in regular/medium/semibold/bold; the built-in font if the file is missing."""
    try:
        return ImageFont.truetype(str(FONT_DIR / FONT_FILES.get(weight, FONT_FILES["regular"])), size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:  # very old Pillow: no scalable default font
            return ImageFont.load_default()


def latin(s: Optional[str]) -> str:
    """Card text is Latin letters, digits and the rupee sign: drop anything else rather than draw tofu boxes."""
    return "".join(c for c in (s or "") if ord(c) < 0x250 or c in "–—’₹").strip()


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> List[str]:
    lines: List[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            while draw.textlength(word, font=font) > max_w:  # a single over-wide word: break by characters
                k = len(word)
                while k > 1 and draw.textlength(word[:k], font=font) > max_w:
                    k -= 1
                if cur:
                    lines.append(cur)
                    cur = ""
                lines.append(word[:k])
                word = word[k:]
            trial = f"{cur} {word}".strip()
            if cur and draw.textlength(trial, font=font) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def _ellipsize(draw, line: str, font, max_w: int) -> str:
    while line and draw.textlength(line + "…", font=font) > max_w:
        line = line[:-1]
    return line.rstrip() + "…"


def fit_text(draw, text: str, max_w: int, max_lines: int, start: int, min_size: int = 22, weight: str = "regular"):
    """Largest font size (start..min_size) whose wrapped text fits max_w within max_lines; at min size the last
    line is ellipsized. Returns (font, lines). Guarantees every returned line is <= max_w wide."""
    size = start
    while True:
        font = load_font(size, weight)
        lines = wrap(draw, text, font, max_w)
        if len(lines) <= max_lines:
            return font, lines
        if size <= min_size:
            lines = lines[:max_lines]
            lines[-1] = _ellipsize(draw, lines[-1] + " " + " ".join(wrap(draw, text, font, max_w)[max_lines:]), font, max_w)
            return font, lines
        size = max(min_size, size - 4)


class Card:
    """A canvas plus a log of every text box drawn (used to verify nothing leaves the safe margins) and of the text itself
    (used to verify no phone number ever appears on a card)."""

    def __init__(self, size: Tuple[int, int], img: Image.Image, top: int = MARGIN, bottom: int = MARGIN):
        self.size, self.img = size, img
        self.draw = ImageDraw.Draw(img)
        self.left, self.right = MARGIN, size[0] - MARGIN
        self.top, self.bottom = top, size[1] - bottom
        self.boxes: List[Tuple[int, int, int, int]] = []
        self.texts: List[str] = []

    def block(self, text: str, y: int, size: int, fill=WHITE, lines: int = 1, min_size: int = 24, x: Optional[int] = None,
              weight: str = "regular"):
        """Draw wrapped text at y; returns the y below it (line pitch = PITCH x font size)."""
        x = self.left if x is None else x
        font, ls = fit_text(self.draw, text, self.right - x, lines, size, min_size, weight)
        pitch = int(font.size * PITCH)
        for i, line in enumerate(ls):
            self.draw.text((x, y + i * pitch), line, font=font, fill=fill)
            self.boxes.append(self.draw.textbbox((x, y + i * pitch), line, font=font))
            self.texts.append(line)
        return y + len(ls) * pitch

    def height_of(self, text: str, size: int, lines: int = 1, min_size: int = 24, x: Optional[int] = None, weight: str = "regular") -> int:
        x = self.left if x is None else x
        font, ls = fit_text(self.draw, text, self.right - x, lines, size, min_size, weight)
        return len(ls) * int(font.size * PITCH)

    def stack(self, items: List[dict], anchor: str = "bottom", gap: int = 22, y0: Optional[int] = None) -> int:
        """Lay items (dicts: text,size,fill,lines,min_size,weight) top-down inside the safe area.
        anchor: bottom | top | center (centred between y0 (default: top) and the bottom margin)."""
        items = [i for i in items if i.get("text")]
        total = sum(self.height_of(i["text"], i["size"], i.get("lines", 1), i.get("min_size", 24), weight=i.get("weight", "regular")) + gap
                    for i in items) - gap
        start = self.top if y0 is None else max(self.top, y0)
        if anchor == "bottom":
            y = self.bottom - total
        elif anchor == "center":
            y = start + max(0, (self.bottom - start - total) // 2)
        else:
            y = start
        y = max(start, y)
        for i in items:
            y = self.block(i["text"], y, i["size"], i.get("fill", WHITE), i.get("lines", 1), i.get("min_size", 24),
                           weight=i.get("weight", "regular")) + gap
        return y


# ---- card layouts ----------------------------------------------------------------------------------
# Design: photo cards show the photo brightly with a scrim only behind the text; without a photo the card is a designed
# brand panel (gradient + skyline) so it never looks like an empty placeholder. Info cards keep the photo as a header strip.
# Calls to action are BUTTONS ("Comment INTERESTED"), never a phone number: the agent's tools answer the buyer.
HEADER_H = 330
FADE = 120
SCRIM_COLOR = (8, 10, 16)
DARK_INK = (24, 30, 44)
CTA_WORD = "INTERESTED"


def _fit(src: Image.Image, size: Tuple[int, int]) -> Image.Image:
    return ImageOps.fit(src, size, Image.LANCZOS, centering=(0.5, 0.45))


def _scrim_bottom(img: Image.Image, start: float = 0.4, strength: float = 0.9) -> Image.Image:
    """Dark gradient over the lower part only (0 above `start` of the height, `strength` at the bottom)."""
    s0 = int(255 * start)
    lut = [0 if v < s0 else int((v - s0) / max(1, 255 - s0) * 255 * strength) for v in range(256)]
    mask = Image.linear_gradient("L").resize(img.size).point(lut)
    return Image.composite(Image.new("RGB", img.size, SCRIM_COLOR), img, mask)


def _skyline(size: Tuple[int, int], seed: str, floor_y: int, tallest: int, windows_above: Optional[int] = None) -> Image.Image:
    """Dark apartment-tower silhouettes with lit gold windows (the Page cover's skyline), deterministic per seed (RGBA overlay)."""
    rnd = random.Random(int(hashlib.md5(seed.encode("utf8")).hexdigest()[:8], 16))
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x = -30
    while x < size[0]:
        bw, bh = rnd.randint(80, 170), rnd.randint(int(tallest * 0.4), tallest)
        top = floor_y - bh
        d.rectangle([x, top, x + bw, size[1]], fill=SILHOUETTE + (235,))
        for wy in range(top + 26, floor_y - 20, 48):
            for wx in range(x + 16, x + bw - 26, 34):
                if rnd.random() > 0.62 and (windows_above is None or wy + 22 < windows_above):
                    d.rectangle([wx, wy, wx + 15, wy + 22], fill=GOLD + (150,))
        x += bw + rnd.randint(8, 26)
    return overlay


def brand_background(size: Tuple[int, int], seed: str, skyline: bool = True, floor: float = 0.80, tall: float = 0.42,
                     windows_above: Optional[int] = None) -> Image.Image:
    """Brand gradient; with `skyline`, faint towers rise from the lower part. `floor`/`tall` (fractions of the height) place them,
    so a card with content in the middle can keep the towers below it."""
    img = gradient_card(size, seed)
    if not skyline:
        return img
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, _skyline(size, seed, floor_y=int(size[1] * floor), tallest=int(size[1] * tall), windows_above=windows_above))
    return base.convert("RGB")


@lru_cache(maxsize=8)
def _logo(diameter: int) -> Optional[Image.Image]:
    """The Avasetu mark (bundled PNG of the round gold disc), RGBA at diameter x diameter, or None if the file is missing."""
    try:
        with Image.open(LOGO_PATH) as im:
            return im.convert("RGBA").resize((diameter, diameter), Image.LANCZOS)
    except Exception:
        return None


def _stamp_logo(c: "Card", x: int, y: int, diameter: int = 96) -> None:
    """Paste the badge with its top-left at (x, y) and log its box for the margin checks."""
    badge = _logo(diameter)
    if badge is None:
        return
    c.img.paste(badge, (x, y), badge)
    c.boxes.append((x, y, x + diameter, y + diameter))


def _panel_with_header(size: Tuple[int, int], src: Optional[Image.Image], seed: str, header_h: int) -> Image.Image:
    """Brand gradient panel; the photo (if any) sits at the top and fades smoothly into the panel."""
    panel = gradient_card(size, seed)
    if src is None:
        return panel
    w = size[0]
    strip = _fit(src, (w, header_h))
    lut = []
    for v in range(256):
        y = v / 255 * header_h
        lut.append(255 if y < header_h - FADE else int(255 * max(0.0, (header_h - y) / FADE)))
    mask = Image.linear_gradient("L").resize((w, header_h)).point(lut)
    panel.paste(strip, (0, 0), mask)
    return panel


def _pill(c: "Card", text: str, y: int) -> int:
    """'Listed by ...' label on a translucent dark pill so it stays readable on any photo. Returns y below it."""
    font = load_font(32, "medium")
    w = int(c.draw.textlength(text, font=font)) + 56
    h = 68
    if c.left + w > c.right:
        w = c.right - c.left
    ov = Image.new("RGB", (w, h), SCRIM_COLOR)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=185)
    c.img.paste(ov, (c.left, y), mask)
    c.block(text, y + 14, 32, WHITE, 1, 22, x=c.left + 28, weight="medium")
    return y + h


def _chip(c: "Card", text: str, x: int, y: int, fill=GOLD, ink=DARK_INK, size: int = 28, outline=None) -> Tuple[int, int]:
    """A rounded label ('FOR SALE'). Returns (right edge, bottom edge); logs its box for the margin checks."""
    font = load_font(size, "semibold")
    w = int(c.draw.textlength(text, font=font)) + 2 * 24
    h = int(size * 1.9)
    c.draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=fill, outline=outline, width=3 if outline else 0)
    c.draw.text((x + 24, y + h // 2), text, font=font, fill=ink, anchor="lm")
    c.boxes.append((x, y, x + w, y + h))
    c.texts.append(text)
    return x + w, y + h


def _button(c: "Card", text: str, y: int, size: int, filled: bool) -> int:
    """A full-width button (filled gold or white outline) with centred text. Returns the y below it."""
    font = load_font(size, "bold" if filled else "semibold")
    h = int(size * 1.25) + 44
    box = [c.left, y, c.right, y + h]
    c.draw.rounded_rectangle(box, radius=h // 2, fill=GOLD if filled else None, outline=None if filled else WHITE, width=0 if filled else 4)
    c.draw.text(((c.left + c.right) // 2, y + h // 2), text, font=font, fill=DARK_INK if filled else WHITE, anchor="mm")
    c.boxes.append(tuple(box))
    c.texts.append(text)
    return y + h


def _button_height(size: int) -> int:
    return int(size * 1.25) + 44


def _facts_rows(f: Facts) -> List[Tuple[str, str]]:
    rows = [("PRICE", f.price_text), ("CONFIGURATION", " ".join(x for x in (f.bhk_text, f.type_text("en").title()) if x)),
            ("AREA", f"{f.area_text} ({f.area_kind})" if f.area_text else None), ("FLOOR", f.floor_text("en")),
            ("POSSESSION", f.possession_text("en")), ("FURNISHING", T["en"]["furn"].get(f.furnishing or "")),
            ("RERA", f.rera)]
    return [(k, v) for k, v in rows if v]


def _agent_line(f: Facts) -> str:
    return latin(f.agent_name)


def _listed_by(f: Facts) -> str:
    """'Listed by <business> · RERA <no>' when the agent has set them (never a phone number); empty otherwise."""
    biz = latin(f.agent_business)
    if not biz:
        return ""
    return f"Listed by {biz}" + (f" · RERA {f.agent_rera_no}" if f.agent_rera_no else "")


def _headline_parts(f: Facts) -> Tuple[str, str]:
    """('2 BHK Apartment', 'Kharadi, Pune') - the two lines that name the property on the cover and story."""
    what = " ".join(x for x in (f.bhk_text, f.type_text("en").title()) if x)
    return latin(what), latin(f.loc)


def _fact_bits(f: Facts) -> str:
    bits = [f.area_text, f.floor_text("en"), T["en"]["furn"].get(f.furnishing or "")]
    if f.possession and f.possession_text("en"):
        bits.insert(1, f.possession_text("en"))
    return "  |  ".join(latin(b) for b in bits if b)


def _tag_chips(c: "Card", f: Facts, y: int) -> int:
    """'FOR SALE' (gold) and 'READY TO MOVE' (outline) chips. Returns the y below them."""
    if f.sample:
        return _chip(c, "SAMPLE LISTING", c.left, y)[1]
    x, bottom = _chip(c, "FOR RENT" if f.rent else "FOR SALE", c.left, y)
    if f.possession == "ready" and x + 14 < c.right - 200:
        _, b2 = _chip(c, "READY TO MOVE", x + 14, y, fill=None, ink=WHITE, outline=WHITE)
        bottom = max(bottom, b2)
    return bottom


def _cover_footer(c: "Card", f: Facts) -> int:
    """'Listed by ...' on the left, a 'Comment INTERESTED' button-pill on the right. Returns the y where the footer starts."""
    size = 30
    label = f"Comment {CTA_WORD}"
    font = load_font(size, "semibold")
    pill_w = int(c.draw.textlength(label, font=font)) + 2 * 26
    h = int(size * 1.9)
    y = c.bottom - h
    px = c.right - pill_w
    c.draw.rounded_rectangle([px, y, c.right, y + h], radius=h // 2, outline=GOLD, width=3)
    c.draw.text((px + 26, y + h // 2), label, font=font, fill=GOLD, anchor="lm")
    c.boxes.append((px, y, c.right, y + h))
    c.texts.append(label)
    agent = _agent_line(f)
    if agent:
        saved = c.right
        c.right = px - 24
        if c.right - c.left > 120:
            c.block(_listed_by(f) or f"Listed by {agent}", y + (h - int(30 * PITCH)) // 2, 30, SOFT, 1, 20, weight="medium")
        c.right = saved
    return y


def render(kind: str, f: Facts, src: Optional[Image.Image]) -> Card:
    """`src` is the (already safely loaded) listing photo or None; layouts fit it themselves."""
    seed = f"{f.agent_name}|{f.locality}"
    story = kind == "status"
    size = STORY if story else SQUARE
    top, bottom = (STORY_TOP, STORY_BOTTOM) if story else (MARGIN, MARGIN)
    title = latin(f.title_line("en"))
    agent = _agent_line(f)
    what, where = _headline_parts(f)

    if kind == "cover":
        img = _scrim_bottom(_fit(src, size), 0.34, 0.94) if src is not None else brand_background(size, seed, windows_above=int(size[1] * 0.5))
        c = Card(size, img, top, bottom)
        _tag_chips(c, f, c.top)
        _stamp_logo(c, c.right - 96, c.top)
        footer_y = _cover_footer(c, f)
        c.bottom = footer_y - 34
        c.stack([{"text": f.price_text, "size": 124, "fill": GOLD, "min_size": 60, "weight": "bold"},
                 {"text": what, "size": 56, "min_size": 34, "lines": 2, "weight": "semibold"},
                 {"text": where, "size": 42, "fill": SOFT, "min_size": 26, "lines": 2, "weight": "medium"},
                 {"text": latin(f.project), "size": 34, "fill": SOFT, "min_size": 24},
                 {"text": _fact_bits(f), "size": 32, "fill": SOFT, "lines": 2, "min_size": 22}], gap=12)
        c.bottom = size[1] - bottom  # restore the real bottom (the stack above stopped at the footer)
        return c

    if story:
        items = [{"text": f.price_text, "size": 136, "fill": GOLD, "min_size": 70, "weight": "bold"},
                 {"text": what, "size": 62, "min_size": 36, "lines": 2, "weight": "semibold"},
                 {"text": where, "size": 46, "fill": SOFT, "min_size": 28, "lines": 2, "weight": "medium"},
                 {"text": latin(f.project), "size": 36, "fill": SOFT, "min_size": 24},
                 {"text": _fact_bits(f), "size": 34, "fill": SOFT, "lines": 3, "min_size": 24}]
        gap = 16
        btn = 54
        probe = Card(size, Image.new("RGB", size), top, bottom)
        total = sum(probe.height_of(i["text"], i["size"], i.get("lines", 1), i.get("min_size", 24), weight=i.get("weight", "regular")) + gap
                    for i in items if i.get("text")) + 30 + _button_height(btn) + 20 + int(34 * PITCH)
        start = max(top + 160, probe.bottom - total)
        head = min(1300, start + 60)
        img = _panel_with_header(size, src, seed, head) if src is not None else brand_background(size, seed, windows_above=int(size[1] * 0.45))
        c = Card(size, img, top, bottom)
        _stamp_logo(c, c.right - 96, c.top)
        if agent:
            _pill(c, _listed_by(f) or f"Listed by {agent}", c.top)
        y = c.stack(items, anchor="top", gap=gap, y0=start) + 30 - gap
        y = _button(c, f"Reply {CTA_WORD}", y, btn, True) + 20
        c.block("to get the details and plan a site visit", y, 34, SOFT, 1, 22, weight="medium")
        return c

    # header height adapts to how much content the card has: short cards get a bigger photo, dense ones a slimmer strip
    if kind == "facts":
        header_h = 250 if len(_facts_rows(f)) >= 6 else HEADER_H
    elif kind == "amenities":
        header_h = 470 if len(f.amenities[:8]) <= 4 else HEADER_H
    else:
        header_h = 420

    who = f"{agent} will share the details and plan a site visit." if agent else "We will share the details and plan a site visit."

    def cta_layout(c: "Card", y: int) -> int:
        """Draws (or, on a probe card, just measures) the closing card's content from y; returns the y below it."""
        y = c.block("Interested?", y, 108, GOLD, 1, 60, weight="bold") + 14
        y = _button(c, f"Comment {CTA_WORD}", y, 54, True) + 22
        y = _button(c, "Send us a message", y, 46, False) + 30
        y = c.block(who, y, 38, WHITE, 3, 26, weight="medium") + 10
        y = c.block(title, y, 32, SOFT, 2, 22) + 6
        if _listed_by(f):
            y = c.block(_listed_by(f), y, 26, SOFT, 1, 18, weight="medium") + 6
        if f.rera:
            y = c.block(f"RERA: {f.rera}", y, 28, SOFT, 1, 20)
        return y

    if kind == "cta":  # size the photo to the content: it must never push the content past the bottom margin
        probe = Card(size, Image.new("RGB", size), top, bottom)
        total = cta_layout(probe, 0)
        header_h = max(200, min(420, probe.bottom - total - 50))
    header = header_h if src is not None else 0
    img = _panel_with_header(size, src, seed, header_h) if src is not None else (
        brand_background(size, seed, floor=1.0, tall=0.2) if kind == "cta" else gradient_card(size, seed))
    c = Card(size, img, top, bottom)
    y0 = header + 10 if header else c.top

    if kind == "facts":
        y = c.block("Key details", y0, 62, GOLD, 1, 30, weight="bold") + 18
        rows = _facts_rows(f)
        pitch = max(66, min(150, (c.bottom - y) // max(1, len(rows))))  # rows always fit above the bottom margin
        ls = 22 if pitch < 100 else 26
        vs = max(30, min(52, pitch - 56))
        for label, value in rows:
            c.draw.line([(c.left, y), (c.right, y)], fill=(96, 118, 158), width=2)
            c.block(label, y + 8, ls, SOFT, 1, 18, weight="medium")
            c.block(latin(value), y + 8 + int(ls * PITCH), vs, WHITE, 1, 24, weight="semibold")
            y += pitch
    elif kind == "amenities":
        y = c.block("Amenities", y0, 64, GOLD, 1, 30, weight="bold") + 36
        items = [latin(a) for a in f.amenities[:8]]
        col_w = (c.right - c.left - 40) // 2
        rows_n = (len(items) + 1) // 2
        pitch = max(84, min(128, (c.bottom - y) // max(1, rows_n)))
        sz = 42 if pitch >= 100 else 36
        y += max(0, (c.bottom - y - rows_n * pitch) // 2)  # few items: centre the grid in the free space
        saved_right = c.right
        for idx, a in enumerate(items):
            col, row = idx % 2, idx // 2
            x = c.left + col * (col_w + 40)
            yy = y + row * pitch
            cy = yy + int(sz * PITCH) // 2 + 6
            c.draw.ellipse((x, cy - 15, x + 30, cy + 15), fill=GOLD)  # a tick in a gold disc
            c.draw.line([(x + 8, cy), (x + 13, cy + 6), (x + 23, cy - 7)], fill=DARK_INK, width=4)
            c.right = x + col_w
            c.block(a, yy, sz, WHITE, 2, 26, x=x + 46, weight="medium")
        c.right = saved_right
    elif kind == "cta":
        _stamp_logo(c, c.right - 96, c.top)
        total = cta_layout(Card(size, Image.new("RGB", size), top, bottom), 0)
        cta_layout(c, y0 + max(0, (c.bottom - y0 - total) // 2))
    else:
        raise ValueError(f"unknown card kind {kind}")
    return c


def _encode(img: Image.Image, qualities) -> Tuple[bytes, bool]:
    data = b""
    for q in qualities:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, optimize=True)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES:
            return data, True
    return data, False


def save_jpeg(img: Image.Image, path: Path) -> int:
    """Save with quality 85, stepping down until the file is under MAX_BYTES. Pathological, very noisy photos that
    still do not fit are softened slightly (a hard size guarantee beats sharpness there). Returns bytes written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data, ok = _encode(img, (85, 80, 74, 68, 60, 50, 40, 32))
    if not ok:
        from PIL import ImageFilter
        for radius in (1.0, 1.6, 2.4):
            data, ok = _encode(img.filter(ImageFilter.GaussianBlur(radius)), (60, 50, 40, 32, 25))
            if ok:
                break
    path.write_bytes(data)
    return len(data)


def render_all(f: Facts, media: List[dict], uploads_dir: Path, listing_id: str) -> Dict[str, dict]:
    """Render + write all cards. Returns {kind: {path (relative under /uploads), width, height}}."""
    if not ID_RE.match(listing_id or ""):
        raise ValueError("unsafe listing id")
    uploads_dir = Path(uploads_dir)
    out_dir = uploads_dir / "marketing" / listing_id
    src = _load_source(local_upload_path(first_photo_url(media), uploads_dir))
    kinds = ["cover", "facts"] + (["amenities"] if f.amenities else []) + ["cta", "status"]
    result: Dict[str, dict] = {}
    for kind in kinds:
        size = STORY if kind == "status" else SQUARE
        card = render(kind, f, src)
        save_jpeg(card.img, out_dir / f"{kind}.jpg")
        result[kind] = {"path": f"/uploads/marketing/{listing_id}/{kind}.jpg", "width": size[0], "height": size[1]}
    if not f.amenities:
        stale = out_dir / "amenities.jpg"
        if stale.exists():
            stale.unlink()
    return result
