"""Server-side share cards (Pillow only). 1080x1080 carousel cards + one 1080x1920 status card.

Background photo: ONLY the listing's first image when it is one of our own uploads (`/uploads/images/<file>` that exists
under the backend uploads dir). Remote URLs, `..`, absolute paths and anything else are never opened or fetched.
Image text is English/numerals (Devanagari on images is out of scope), always inside safe margins over a dark overlay.
"""
import hashlib
import io
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFile, ImageFont, ImageOps

from .facts import T, Facts

SQUARE = (1080, 1080)
STORY = (1080, 1920)
MARGIN = 84
STORY_TOP, STORY_BOTTOM = 240, 300  # keep clear of the story app chrome
MAX_BYTES = 380 * 1024
MAX_SOURCE_BYTES = 20 * 1024 * 1024
WHITE, SOFT, ACCENT = (255, 255, 255), (214, 218, 228), (255, 214, 140)
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
UPLOAD_PATH_RE = re.compile(r"^/uploads/images/([A-Za-z0-9][A-Za-z0-9._-]{0,200})$")
PALETTES = [((22, 50, 92), (60, 110, 160)), ((30, 64, 58), (70, 128, 112)), ((70, 36, 66), (140, 80, 120)),
            ((52, 48, 90), (100, 96, 170)), ((84, 48, 30), (170, 110, 70)), ((34, 44, 60), (84, 100, 120))]
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
def load_font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow: no scalable default font
        return ImageFont.load_default()


def latin(s: Optional[str]) -> str:
    """Default font is Latin only: drop anything else rather than draw tofu boxes."""
    return "".join(c for c in (s or "") if ord(c) < 0x250 or c in "–—’").strip()


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


def fit_text(draw, text: str, max_w: int, max_lines: int, start: int, min_size: int = 22):
    """Largest font size (start..min_size) whose wrapped text fits max_w within max_lines; at min size the last
    line is ellipsized. Returns (font, lines). Guarantees every returned line is <= max_w wide."""
    size = start
    while True:
        font = load_font(size)
        lines = wrap(draw, text, font, max_w)
        if len(lines) <= max_lines:
            return font, lines
        if size <= min_size:
            lines = lines[:max_lines]
            lines[-1] = _ellipsize(draw, lines[-1] + " " + " ".join(wrap(draw, text, font, max_w)[max_lines:]), font, max_w)
            return font, lines
        size = max(min_size, size - 4)


class Card:
    """A canvas plus a log of every text box drawn (used to verify nothing leaves the safe margins)."""

    def __init__(self, size: Tuple[int, int], img: Image.Image, top: int = MARGIN, bottom: int = MARGIN):
        self.size, self.img = size, img
        self.draw = ImageDraw.Draw(img)
        self.left, self.right = MARGIN, size[0] - MARGIN
        self.top, self.bottom = top, size[1] - bottom
        self.boxes: List[Tuple[int, int, int, int]] = []

    def block(self, text: str, y: int, size: int, fill=WHITE, lines: int = 1, min_size: int = 24, x: Optional[int] = None):
        """Draw wrapped text at y; returns the y below it (line pitch = 1.3 x font size)."""
        x = self.left if x is None else x
        font, ls = fit_text(self.draw, text, self.right - x, lines, size, min_size)
        pitch = int(font.size * 1.3) if hasattr(font, "size") else int(size * 1.3)
        for i, line in enumerate(ls):
            self.draw.text((x, y + i * pitch), line, font=font, fill=fill)
            self.boxes.append(self.draw.textbbox((x, y + i * pitch), line, font=font))
        return y + len(ls) * pitch

    def height_of(self, text: str, size: int, lines: int = 1, min_size: int = 24, x: Optional[int] = None) -> int:
        x = self.left if x is None else x
        font, ls = fit_text(self.draw, text, self.right - x, lines, size, min_size)
        return len(ls) * (int(font.size * 1.3) if hasattr(font, "size") else int(size * 1.3))

    def stack(self, items: List[dict], anchor: str = "bottom", gap: int = 22, y0: Optional[int] = None) -> int:
        """Lay items (dicts: text,size,fill,lines,min_size) top-down inside the safe area.
        anchor: bottom | top | center (centred between y0 (default: top) and the bottom margin)."""
        items = [i for i in items if i.get("text")]
        total = sum(self.height_of(i["text"], i["size"], i.get("lines", 1), i.get("min_size", 24)) + gap for i in items) - gap
        start = self.top if y0 is None else max(self.top, y0)
        if anchor == "bottom":
            y = self.bottom - total
        elif anchor == "center":
            y = start + max(0, (self.bottom - start - total) // 2)
        else:
            y = start
        y = max(start, y)
        for i in items:
            y = self.block(i["text"], y, i["size"], i.get("fill", WHITE), i.get("lines", 1), i.get("min_size", 24)) + gap
        return y


# ---- card layouts ----------------------------------------------------------------------------------
# Design: photo cards show the photo brightly with a scrim only behind the text; info cards are a calm brand panel
# with the photo as a header strip (so the property is always visible and text never fights a busy image).
HEADER_H = 330
FADE = 120
SCRIM_COLOR = (8, 10, 16)


def _fit(src: Image.Image, size: Tuple[int, int]) -> Image.Image:
    return ImageOps.fit(src, size, Image.LANCZOS, centering=(0.5, 0.45))


def _scrim_bottom(img: Image.Image, start: float = 0.4, strength: float = 0.9) -> Image.Image:
    """Dark gradient over the lower part only (0 above `start` of the height, `strength` at the bottom)."""
    s0 = int(255 * start)
    lut = [0 if v < s0 else int((v - s0) / max(1, 255 - s0) * 255 * strength) for v in range(256)]
    mask = Image.linear_gradient("L").resize(img.size).point(lut)
    return Image.composite(Image.new("RGB", img.size, SCRIM_COLOR), img, mask)


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
    font = load_font(34)
    w = int(c.draw.textlength(text, font=font)) + 56
    h = 68
    if c.left + w > c.right:
        w = c.right - c.left
    ov = Image.new("RGB", (w, h), SCRIM_COLOR)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=185)
    c.img.paste(ov, (c.left, y), mask)
    c.block(text, y + 15, 34, WHITE, 1, 22, x=c.left + 28)
    return y + h


def _facts_rows(f: Facts) -> List[Tuple[str, str]]:
    rows = [("PRICE", f.price_text), ("CONFIGURATION", " ".join(x for x in (f.bhk_text, f.type_text("en")) if x)),
            ("AREA", f"{f.area_text} ({f.area_kind})" if f.area_text else None), ("FLOOR", f.floor_text("en")),
            ("POSSESSION", f.possession_text("en")), ("FURNISHING", T["en"]["furn"].get(f.furnishing or "")),
            ("RERA", f.rera)]
    return [(k, v) for k, v in rows if v]


def _agent_line(f: Facts) -> str:
    return latin(f.agent_name)


def render(kind: str, f: Facts, src: Optional[Image.Image]) -> Card:
    """`src` is the (already safely loaded) listing photo or None; layouts fit it themselves."""
    seed = f"{f.agent_name}|{f.locality}"
    story = kind == "status"
    size = STORY if story else SQUARE
    top, bottom = (STORY_TOP, STORY_BOTTOM) if story else (MARGIN, MARGIN)
    title = latin(f.title_line("en"))
    agent = _agent_line(f)

    if kind == "cover":
        img = _scrim_bottom(_fit(src, size), 0.36, 0.92) if src is not None else gradient_card(size, seed)
        c = Card(size, img, top, bottom)
        if agent:
            _pill(c, f"Listed by {agent}", c.top)
        c.stack([{"text": f.price_text, "size": 124, "fill": ACCENT, "min_size": 60},
                 {"text": title, "size": 56, "lines": 3, "min_size": 34},
                 {"text": latin(f.project), "size": 40, "fill": SOFT, "min_size": 26},
                 {"text": " | ".join(x for x in (f.area_text, f.possession_text("en")) if x), "size": 40, "fill": SOFT, "lines": 2}])
        return c

    if story:
        items = [{"text": f.price_text, "size": 140, "fill": ACCENT, "min_size": 70},
                 {"text": title, "size": 60, "lines": 3, "min_size": 34},
                 {"text": latin(f.project), "size": 42, "fill": SOFT, "min_size": 26},
                 {"text": " | ".join(x for x in (f.area_text, f.possession_text("en")) if x), "size": 42, "fill": SOFT, "lines": 2},
                 {"text": "Message for details", "size": 48, "fill": ACCENT}]
        gap = 26
        # measure the text first: it always ends at the bottom safe margin and the photo takes all the room above it
        probe = Card(size, Image.new("RGB", size), top, bottom)
        total = sum(probe.height_of(i["text"], i["size"], i.get("lines", 1), i.get("min_size", 24)) + gap
                    for i in items if i.get("text")) - gap
        start = max(top + 160, probe.bottom - total)
        head = min(1300, start + 60)
        img = _panel_with_header(size, src, seed, head)
        c = Card(size, img, top, bottom)
        if agent:
            _pill(c, f"Listed by {agent}", c.top)
        c.stack(items, anchor="top", gap=gap, y0=start)
        return c

    # header height adapts to how much content the card has: short cards get a bigger photo, dense ones a slimmer strip
    if kind == "facts":
        header_h = 250 if len(_facts_rows(f)) >= 6 else HEADER_H
    elif kind == "amenities":
        header_h = 470 if len(f.amenities[:8]) <= 4 else HEADER_H
    else:
        header_h = 420
    cta_items = [{"text": "Interested?", "size": 104, "fill": ACCENT},
                 {"text": f"Message {agent} for a site visit" if agent else "Message us for a site visit", "size": 58, "lines": 3},
                 {"text": f"Call {latin(f.agent_phone)}" if f.agent_phone else "", "size": 64, "fill": ACCENT},
                 {"text": title, "size": 40, "fill": SOFT, "lines": 2},
                 {"text": f"RERA: {f.rera}" if f.rera else "", "size": 30, "fill": SOFT}]
    if kind == "cta":  # size the photo to the text: it must never push the text past the bottom margin
        probe = Card(size, Image.new("RGB", size), top, bottom)
        total = sum(probe.height_of(i["text"], i["size"], i.get("lines", 1), i.get("min_size", 24)) + 32
                    for i in cta_items if i.get("text")) - 32
        header_h = max(200, min(420, probe.bottom - total - 50))
    header = header_h if src is not None else 0
    img = _panel_with_header(size, src, seed, header_h) if src is not None else gradient_card(size, seed)
    c = Card(size, img, top, bottom)
    y0 = header + 10 if header else c.top

    if kind == "facts":
        y = c.block("Key details", y0, 64, ACCENT) + 20
        rows = _facts_rows(f)
        pitch = max(66, min(150, (c.bottom - y) // max(1, len(rows))))  # rows always fit above the bottom margin
        ls = 22 if pitch < 100 else 26
        vs = max(30, min(54, pitch - 52))
        for label, value in rows:
            c.draw.line([(c.left, y), (c.right, y)], fill=(96, 118, 158), width=2)
            c.block(label, y + 10, ls, SOFT, 1, 18)
            c.block(latin(value), y + 10 + ls + 10, vs, WHITE, 1, 24)
            y += pitch
    elif kind == "amenities":
        y = c.block("Amenities", y0, 68, ACCENT) + 40
        items = [latin(a) for a in f.amenities[:8]]
        col_w = (c.right - c.left - 40) // 2
        rows_n = (len(items) + 1) // 2
        pitch = max(84, min(128, (c.bottom - y) // max(1, rows_n)))
        sz = 44 if pitch >= 100 else 38
        y += max(0, (c.bottom - y - rows_n * pitch) // 2)  # few items: centre the grid in the free space
        saved_right = c.right
        for idx, a in enumerate(items):
            col, row = idx % 2, idx // 2
            x = c.left + col * (col_w + 40)
            yy = y + row * pitch
            c.draw.ellipse((x, yy + sz // 2 - 5, x + 14, yy + sz // 2 + 9), fill=ACCENT)
            c.right = x + col_w
            c.block(a, yy, sz, WHITE, 2, 26, x=x + 40)
        c.right = saved_right
    elif kind == "cta":
        c.stack(cta_items, anchor="center", gap=32, y0=y0)
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
