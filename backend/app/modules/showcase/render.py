"""Showcase renderers (Pillow + bundled Poppins): 5-slide Instagram carousel 1080x1350, Facebook card 1200x630, story scenes 1080x1920.

Every image carries the 'Sample listing' label in text. Margins: text stays >= MARGIN from the left/right edges, so nothing is
lost by Instagram's 3:4 profile-grid crop (centre 1012x1350 of 1080x1350 trims 34 px per side).
"""
from app.core import brand
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from app.modules.marketing.images import GOLD, SOFT, WHITE, brand_background, load_font, save_jpeg, wrap, _logo

from .icons import check_tile, icon_tile
from .samples import (AGENTS_CTA, BRAND, ICON_LABELS, RERA_LINE, SAMPLE_LABEL, SAMPLE_NOTE, SAMPLE_RIBBON, Home, Photo, area_lines)

PORTRAIT = (1080, 1350)
FACEBOOK = (1200, 630)
STORY = (1080, 1920)
MARGIN = 84
GRID_SAFE_X = 34            # Instagram's 3:4 grid crop trims this much from each side of a 1080x1350 post
INK = (24, 30, 44)
NAVY = (16, 35, 64)
SCRIM = (8, 10, 16)
FOOTER_TEXT = f"{SAMPLE_LABEL}  |  Illustrative home, not for sale"


# ---- primitives ---------------------------------------------------------------------------------------------
def load_photo(p: Photo) -> Image.Image:
    with Image.open(p.path) as im:
        return ImageOps.exif_transpose(im).convert("RGB")


def cover_fit(im: Image.Image, size: Tuple[int, int], focus: Tuple[float, float] = (0.5, 0.5), zoom: float = 1.0) -> Image.Image:
    """Fill `size` with the photo, cropping around the `focus` point (fractions of the photo) and optionally zooming in."""
    w, h = im.size
    tw, th = size
    scale = max(tw / w, th / h) * zoom
    cw, ch = min(w, tw / scale), min(h, th / scale)
    cx, cy = focus[0] * w, focus[1] * h
    left = min(max(cx - cw / 2, 0), w - cw)
    top = min(max(cy - ch / 2, 0), h - ch)
    out = im.crop((int(left), int(top), int(left + cw), int(top + ch))).resize(size, Image.LANCZOS)
    out = ImageEnhance.Contrast(out).enhance(1.05)
    return ImageEnhance.Color(out).enhance(1.06)


def vscrim(img: Image.Image, y0: int, y1: int, a0: float, a1: float, color=SCRIM) -> None:
    """Blend `color` over rows y0..y1 with opacity going a0 -> a1 (eased so the edge is invisible), in place."""
    y0, y1 = max(0, y0), min(img.height, y1)
    if y1 <= y0:
        return
    h = y1 - y0
    ramp = Image.linear_gradient("L").resize((img.width, h))
    lo, hi = int(a0 * 255), int(a1 * 255)
    mask = ramp.point(lambda v: int(lo + (hi - lo) * ((v / 255.0) ** 1.5 if hi > lo else 1 - ((1 - v / 255.0) ** 1.5))))
    img.paste(Image.new("RGB", (img.width, h), color), (0, y0), mask)


def hscrim(img: Image.Image, x1: int, a0: float, a1: float, color=SCRIM) -> None:
    """Left-to-right scrim over columns 0..x1, opacity a0 at the left edge, a1 at x1."""
    ramp = Image.linear_gradient("L").rotate(90).resize((x1, img.height))  # rotate gives 255 -> 0 left to right
    lo, hi = int(a0 * 255), int(a1 * 255)
    mask = ramp.point(lambda v: int(lo + (hi - lo) * (v / 255.0)))
    img.paste(Image.new("RGB", (x1, img.height), color), (0, 0), mask)


class Canvas:
    """An image plus a log of every text box (for margin checks) and every string (for label/phone checks)."""

    def __init__(self, img: Image.Image, top: int = MARGIN, bottom: Optional[int] = None):
        self.img = img
        self.draw = ImageDraw.Draw(img)
        self.w, self.h = img.size
        self.left, self.right = MARGIN, self.w - MARGIN
        self.top = top
        self.bottom = self.h - MARGIN if bottom is None else bottom
        self.boxes: List[Tuple[int, int, int, int]] = []
        self.texts: List[str] = []

    # --- text ---
    def font(self, size: int, weight: str = "regular"):
        return load_font(size, weight)

    def tw(self, s: str, size: int, weight: str = "regular") -> int:
        return int(self.draw.textlength(s, font=self.font(size, weight)))

    def text(self, x: int, y: int, s: str, size: int, weight: str = "regular", fill=WHITE, anchor: str = "la") -> int:
        font = self.font(size, weight)
        self.draw.text((x, y), s, font=font, fill=fill, anchor=anchor)
        self.boxes.append(tuple(int(v) for v in self.draw.textbbox((x, y), s, font=font, anchor=anchor)))
        self.texts.append(s)
        return y + int(size * 1.25)

    def para(self, x: int, y: int, s: str, size: int, weight: str = "regular", fill=WHITE, max_w: Optional[int] = None,
             max_lines: int = 6, pitch: float = 1.3, center: bool = False) -> int:
        """Wrapped paragraph; shrinks the font (down to 70%) until it fits max_lines. Returns y below it."""
        max_w = max_w or (self.right - x)
        sz = size
        while True:
            lines = wrap(self.draw, s, self.font(sz, weight), max_w)
            if len(lines) <= max_lines or sz <= int(size * 0.7):
                break
            sz -= 2
        for i, line in enumerate(lines[:max_lines]):
            yy = y + int(i * sz * pitch)
            if center:
                self.text(x + max_w // 2, yy, line, sz, weight, fill, "ma")
            else:
                self.text(x, yy, line, sz, weight, fill)
        return y + int(min(len(lines), max_lines) * sz * pitch)

    def para_h(self, s: str, size: int, weight: str, max_w: int, max_lines: int, pitch: float = 1.3) -> int:
        sz = size
        while True:
            lines = wrap(self.draw, s, self.font(sz, weight), max_w)
            if len(lines) <= max_lines or sz <= int(size * 0.7):
                return int(min(len(lines), max_lines) * sz * pitch)
            sz -= 2

    # --- shapes ---
    def panel(self, box, radius: int, color=SCRIM, alpha: float = 0.6, outline=None, width: int = 2) -> None:
        x0, y0, x1, y1 = [int(v) for v in box]
        w, h = x1 - x0, y1 - y0
        mask = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], radius=radius * 2, fill=int(alpha * 255))
        self.img.paste(Image.new("RGB", (w, h), color), (x0, y0), mask.resize((w, h), Image.LANCZOS))
        if outline:
            self.draw.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=radius, outline=outline, width=width)
        self.boxes.append((x0, y0, x1, y1))

    def chip(self, x: int, y: int, s: str, size: int = 28, fill=GOLD, ink=INK, weight: str = "semibold", pad: int = 26,
             outline=None, anchor_right: bool = False) -> Tuple[int, int, int, int]:
        font = self.font(size, weight)
        w = int(self.draw.textlength(s, font=font)) + 2 * pad
        h = int(size * 1.9)
        if anchor_right:
            x = x - w
        self.draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=fill, outline=outline, width=3 if outline else 0)
        self.draw.text((x + w // 2, y + h // 2 + 1), s, font=font, fill=ink, anchor="mm")
        self.boxes.append((x, y, x + w, y + h))
        self.texts.append(s)
        return x, y, x + w, y + h

    def paste_rgba(self, tile: Image.Image, x: int, y: int) -> None:
        self.img.paste(tile, (x, y), tile)
        self.boxes.append((x, y, x + tile.width, y + tile.height))

    def logo(self, x: int, y: int, d: int = 80) -> None:
        badge = _logo(d)
        if badge is not None:
            self.paste_rgba(badge, x, y)

    def brandbar(self, y: int, ribbon: bool = True) -> None:
        """Logo + wordmark at the left, the 'SAMPLE HOME' ribbon at the right."""
        self.logo(self.left, y, 76)
        self.text(self.left + 92, y + 19, BRAND, 32, "semibold", WHITE)
        if ribbon:
            self.chip(self.right, y + 6, SAMPLE_RIBBON, 26, GOLD, INK, "bold", anchor_right=True)

    def footer(self, y: int, swipe: bool = False, plate: bool = False) -> None:
        """The persistent honesty label, on every image. `plate` puts a dark strip behind it (for busy backgrounds)."""
        if plate:
            self.panel((0, y - 22, self.w, y + 54), 0, NAVY, 0.92)
        self.text(self.left, y, FOOTER_TEXT, 25, "medium", (232, 236, 244))
        if swipe:
            self.text(self.right, y, "Swipe  >", 25, "semibold", GOLD, "ra")


# ---- layouts -------------------------------------------------------------------------------------------------
@dataclass
class Frame:
    """Vertical safe zone of a canvas: content lives between `top` and `bottom`."""
    size: Tuple[int, int]
    top: int
    bottom: int

    @property
    def extra(self) -> int:   # extra vertical room compared with the 1080x1350 post
        return (self.bottom - self.top) - (PORTRAIT[1] - 2 * MARGIN)


def frame_for(size: Tuple[int, int]) -> Frame:
    if size == STORY:
        return Frame(size, 250, 1920 - 320)   # clear of story app chrome
    return Frame(size, MARGIN, size[1] - MARGIN)


def _new(size, fr: Frame) -> Canvas:
    return Canvas(Image.new("RGB", size, NAVY), fr.top, fr.bottom)


def slide_cover(h: Home, size=PORTRAIT) -> Canvas:
    fr = frame_for(size)
    ph = h.exterior
    img = cover_fit(load_photo(ph), size, ph.focus, zoom=1.0)
    H = size[1]
    vscrim(img, 0, int(H * 0.2) + fr.top, 0.8, 0.0)
    vscrim(img, int(H * 0.45), H, 0.0, 0.9)
    c = Canvas(img, fr.top, fr.bottom)
    c.brandbar(fr.top - (MARGIN - 60) if size == PORTRAIT else fr.top)
    y_footer = fr.bottom - 26
    c.footer(y_footer, swipe=True)
    # text block, anchored above the footer
    y = y_footer - 48
    status = f"{h.possession.split(',')[0]}  |  {h.floor_text}"
    y -= int(34 * 1.25)
    c.text(c.left, y, status, 34, "medium", (232, 236, 244))
    y -= 30
    carpet = f"{h.carpet_text} carpet area"
    y -= int(56 * 1.25)
    c.text(c.left, y, carpet, 56, "semibold", WHITE)
    y -= 12
    big = f"{h.bhk} BHK"
    y -= int(196 * 1.12)
    c.text(c.left, y, big, 196, "bold", WHITE)
    y -= 26
    y -= 62
    c.chip(c.left, y, f"{h.locality.upper()}, PUNE", 30, GOLD, INK, "bold")
    return c


def slide_inside(h: Home, size=PORTRAIT) -> Canvas:
    fr = frame_for(size)
    ph = h.interiors[0]
    H = size[1]
    photo_h = 800 + fr.extra // 2
    img = Image.new("RGB", size, NAVY)
    img.paste(cover_fit(load_photo(ph), (size[0], photo_h + 100), ph.focus), (0, 0))
    vscrim(img, 0, 260, 0.55, 0.0)
    # navy sheet with rounded top corners rising over the photo
    sheet_top = photo_h - 40
    sheet = brand_background((size[0], H - sheet_top), "showcase-" + h.slug, skyline=False)
    m = Image.new("L", (size[0] * 2, (H - sheet_top) * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] * 2, (H - sheet_top) * 2 + 120], radius=90, fill=255)
    img.paste(sheet, (0, sheet_top), m.resize((size[0], H - sheet_top), Image.LANCZOS))
    c = Canvas(img, fr.top, fr.bottom)
    c.draw.rounded_rectangle([size[0] // 2 - 44, sheet_top + 18, size[0] // 2 + 44, sheet_top + 24], radius=3, fill=(255, 255, 255, 90))
    c.chip(c.left, fr.top, "INSIDE THE HOME", 26, (16, 35, 64), WHITE, "bold", outline=GOLD)
    c.chip(c.right, fr.top, SAMPLE_RIBBON, 26, GOLD, INK, "bold", anchor_right=True)
    y = sheet_top + 62
    c.text(c.left, y, "Highlights", 42, "bold", WHITE)
    y += 74
    row_h, gap = 90, 14
    tick = check_tile(52)
    for s in h.highlights:
        c.panel((c.left, y, c.right, y + row_h), row_h // 2, (255, 255, 255), 0.10, outline=(255, 255, 255), width=2)
        c.paste_rgba(tick, c.left + 20, y + (row_h - 52) // 2)
        c.text(c.left + 98, y + row_h // 2, s, 38, "medium", WHITE, "lm")
        y += row_h + gap
    c.footer(fr.bottom - 26)
    return c


def _tile(c: Canvas, x: int, y: int, w: int, h: int, label: str, value: str, vsize: int = 54) -> None:
    c.panel((x, y, x + w, y + h), 28, (255, 255, 255), 0.08, outline=(255, 255, 255), width=2)
    c.text(x + 30, y + 26, label.upper(), 24, "semibold", GOLD)
    sz = vsize
    while c.tw(value, sz, "bold") > w - 60 and sz > 28:
        sz -= 2
    c.text(x + 30, y + 26 + 46, value, sz, "bold", WHITE)


def slide_glance(h: Home, size=PORTRAIT) -> Canvas:
    fr = frame_for(size)
    img = brand_background(size, "showcase-glance-" + h.slug, skyline=True, floor=0.985, tall=0.16)
    c = Canvas(img, fr.top, fr.bottom)
    e = fr.extra // 6
    c.logo(c.left, fr.top, 64)
    c.text(c.left + 80, fr.top + 14, "AT A GLANCE", 28, "bold", GOLD)
    c.chip(c.right, fr.top + 2, SAMPLE_RIBBON, 24, GOLD, INK, "bold", anchor_right=True)
    y = fr.top + 100 + e
    c.para(c.left, y, h.title, 70, "bold", WHITE, max_lines=1)
    y += 108 + e
    gap = 24
    tw_ = (c.right - c.left - gap) // 2
    th = 160 + e // 2
    poss_value = "Ready" if h.ready else h.possession.split("possession ")[-1]
    tiles = [("Bedrooms", f"{h.bhk} BHK"), ("Carpet area", h.carpet_text), ("Floor", f"{h.floor} of {h.total_floors}"),
             ("Possession", poss_value), ("Furnishing", h.furnishing), ("Sample price", h.price_text)]
    for i, (lab, val) in enumerate(tiles):
        _tile(c, c.left + (i % 2) * (tw_ + gap), y + (i // 2) * (th + gap), tw_, th, lab, val)
    y += 3 * (th + gap) + 6 + e
    c.text(c.left, y, "AMENITIES", 26, "bold", GOLD)
    y += 50
    keys = list(h.amenities)[:6]
    colw = (c.right - c.left) // 6
    for i, k in enumerate(keys):
        cx = c.left + i * colw + colw // 2
        c.paste_rgba(icon_tile(k, 96), cx - 48, y)
        label = ICON_LABELS.get(k, k.title())
        ly = y + 108
        for ln in wrap(c.draw, label, c.font(22, "medium"), colw - 6)[:2]:
            c.text(cx, ly, ln, 23, "medium", WHITE, "ma")
            ly += 29
    y += 108 + 66 + e
    c.text(c.left, y, RERA_LINE, 25, "medium", SOFT)
    c.footer(fr.bottom - 26, plate=True)
    return c


def slide_area(h: Home, size=PORTRAIT) -> Canvas:
    fr = frame_for(size)
    ph = h.photos[-1]
    img = cover_fit(load_photo(ph), size, ph.focus, zoom=1.1).filter(ImageFilter.GaussianBlur(5))
    img = Image.blend(img, Image.new("RGB", size, NAVY), 0.6)
    c = Canvas(img, fr.top, fr.bottom)
    c.logo(c.left, fr.top, 64)
    c.text(c.left + 80, fr.top + 14, "WHY THIS AREA", 28, "bold", GOLD)
    c.chip(c.right, fr.top + 2, SAMPLE_RIBBON, 24, GOLD, INK, "bold", anchor_right=True)
    e = fr.extra // 5
    y = fr.top + 110 + e
    name_size = 124
    while c.tw(h.locality, name_size, "bold") > c.right - c.left and name_size > 70:
        name_size -= 4
    y = c.text(c.left, y, h.locality, name_size, "bold", WHITE) + 0
    c.text(c.left, y + 2, "Pune", 38, "medium", GOLD)
    y += 96 + e
    for i, line in enumerate(area_lines(h), 1):
        inner_w = c.right - c.left - 150
        ph_ = c.para_h(line, 40, "medium", inner_w, 4)
        ch = ph_ + 64
        c.panel((c.left, y, c.right, y + ch), 34, (8, 10, 16), 0.55, outline=(255, 255, 255), width=2)
        c.draw.ellipse([c.left + 28, y + 30, c.left + 92, y + 94], fill=GOLD)
        c.text(c.left + 60, y + 62, str(i), 34, "bold", INK, "mm")
        c.para(c.left + 122, y + 32, line, 40, "medium", WHITE, max_w=inner_w, max_lines=4)
        y += ch + 26
    # the sample home this area line is shown with: thumbnail + facts
    cy = fr.bottom - 26 - 40 - 130
    c.panel((c.left, cy, c.right, cy + 130), 34, (255, 255, 255), 0.10, outline=GOLD, width=2)
    th_ = cover_fit(load_photo(h.exterior), (98, 98), h.exterior.focus)
    tm = Image.new("L", (392, 392), 0)
    ImageDraw.Draw(tm).rounded_rectangle([0, 0, 391, 391], radius=80, fill=255)
    c.img.paste(th_, (c.left + 16, cy + 16), tm.resize((98, 98), Image.LANCZOS))
    c.text(c.left + 136, cy + 22, "SAMPLE HOME IN THIS AREA", 21, "bold", GOLD)
    c.text(c.left + 136, cy + 52, f"{h.title}, {h.carpet_text}", 32, "semibold", WHITE)
    c.text(c.left + 136, cy + 92, f"Sample price {h.price_text}", 24, "medium", SOFT)
    c.footer(fr.bottom - 26)
    return c


def slide_cta(h: Home, size=PORTRAIT) -> Canvas:
    fr = frame_for(size)
    img = brand_background(size, "showcase-cta-" + h.slug, skyline=True, floor=0.985, tall=0.24)
    c = Canvas(img, fr.top, fr.bottom)
    e = fr.extra // 4
    cx = size[0] // 2
    c.logo(cx - 50, fr.top + 10, 100)
    c.chip(c.right, fr.top + 2, SAMPLE_RIBBON, 24, GOLD, INK, "bold", anchor_right=True)
    y = fr.top + 160 + e
    c.text(cx, y, "Like this home?", 88, "bold", WHITE, "ma")
    y += 112
    c.para(c.left, y, "This is a sample home, shown to give you a feel for how listings look on " + brand.NAME + ".", 32, "regular",
           SOFT, max_lines=3, center=True)
    y += 140 + e
    bh = 112
    c.draw.rounded_rectangle([c.left, y, c.right, y + bh], radius=bh // 2, fill=GOLD)
    c.draw.text((cx, y + bh // 2 + 2), "Comment INTERESTED for details", font=c.font(38, "bold"), fill=INK, anchor="mm")
    c.boxes.append((c.left, y, c.right, y + bh))
    c.texts.append("Comment INTERESTED for details")
    y += bh + 22
    c.text(cx, y, "on this sample home", 28, "medium", SOFT, "ma")
    y += 88 + e
    c.draw.line([c.left + 120, y, c.right - 120, y], fill=(255, 255, 255), width=2)
    y += 42
    c.text(cx, y, "For agents", 24, "bold", GOLD, "ma")
    y += 46
    c.draw.rounded_rectangle([c.left, y, c.right, y + 100], radius=50, outline=WHITE, width=4)
    c.draw.text((cx, y + 52), "Agents: list your homes free", font=c.font(36, "semibold"), fill=WHITE, anchor="mm")
    c.boxes.append((c.left, y, c.right, y + 100))
    c.texts.append(AGENTS_CTA)
    y += 100 + 18
    c.text(cx, y, "Link in bio", 30, "semibold", GOLD, "ma")
    c.footer(fr.bottom - 26, plate=True)
    return c


SLIDES = (slide_cover, slide_inside, slide_glance, slide_area, slide_cta)


def render_carousel(h: Home) -> List[Canvas]:
    return [fn(h, PORTRAIT) for fn in SLIDES]


def render_story(h: Home) -> List[Canvas]:
    return [fn(h, STORY) for fn in SLIDES]


def render_facebook(h: Home) -> Canvas:
    """1200x630 photo-led card: photo, left scrim, locality chip, BHK and carpet in big type, ribbon and label."""
    size = FACEBOOK
    ph = h.exterior
    img = cover_fit(load_photo(ph), size, ph.focus, zoom=1.0)
    hscrim(img, 820, 0.88, 0.0)
    vscrim(img, 420, 630, 0.0, 0.55)
    c = Canvas(img, 56, 630 - 56)
    m = 64
    c.left = m
    c.logo(m, 44, 64)
    c.text(m + 80, 57, BRAND, 28, "semibold", WHITE)
    c.chip(size[0] - m, 50, SAMPLE_RIBBON, 24, GOLD, INK, "bold", anchor_right=True)
    c.chip(m, 200, f"{h.locality.upper()}, PUNE", 26, GOLD, INK, "bold")
    c.text(m, 262, f"{h.bhk} BHK", 132, "bold", WHITE)
    c.text(m, 424, f"{h.carpet_text} carpet area", 40, "semibold", WHITE)
    c.text(m, 476, h.possession.split(",")[0], 28, "medium", (232, 236, 244))
    c.text(m, 630 - 56, FOOTER_TEXT, 22, "medium", (232, 236, 244), "ls")
    return c


# ---- output --------------------------------------------------------------------------------------------------
def contact_sheet(images: Sequence[Image.Image], cols: int, thumb_w: int = 360, gap: int = 14, bg=(235, 237, 242)) -> Image.Image:
    thumbs = []
    for im in images:
        r = thumb_w / im.width
        thumbs.append(im.resize((thumb_w, int(im.height * r)), Image.LANCZOS))
    rows = [thumbs[i:i + cols] for i in range(0, len(thumbs), cols)]
    heights = [max(t.height for t in r) for r in rows]
    W = cols * thumb_w + (cols + 1) * gap
    Hh = sum(heights) + (len(rows) + 1) * gap
    sheet = Image.new("RGB", (W, Hh), bg)
    y = gap
    for r, hh in zip(rows, heights):
        for i, t in enumerate(r):
            sheet.paste(t, (gap + i * (thumb_w + gap), y))
        y += hh + gap
    return sheet


def write_home(h: Home, out_dir: Path, scenes: bool = True) -> Dict[str, List[Path]]:
    """Render everything for one home under out_dir/<slug>/: 1..5.jpg, facebook.jpg and scenes/1..5.jpg."""
    base = Path(out_dir) / h.slug
    result: Dict[str, List[Path]] = {"carousel": [], "facebook": [], "scenes": []}
    for i, cv in enumerate(render_carousel(h), 1):
        p = base / f"{i}.jpg"
        save_jpeg(cv.img, p)
        result["carousel"].append(p)
    p = base / "facebook.jpg"
    save_jpeg(render_facebook(h).img, p)
    result["facebook"].append(p)
    if scenes:
        for i, cv in enumerate(render_story(h), 1):
            p = base / "scenes" / f"{i}.jpg"
            save_jpeg(cv.img, p)
            result["scenes"].append(p)
    return result
