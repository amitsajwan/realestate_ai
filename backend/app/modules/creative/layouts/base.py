"""Drawing kit for the creative layouts: a Canvas with anti-aliased shapes, soft shadows and glows, icon glyphs drawn from
shapes, and text that fits, balances its lines and logs what it drew (box, size, colour, background) so the critic and the
tests can prove that everything is inside the safe margins and readable. Built on marketing.images primitives."""
import contextvars
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Sequence, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

from app.core import brand
from app.modules.marketing.images import LOGO_PATH, MARGIN, load_font as _latin_font, wrap

from ..models import CardBrand
from .palette import Palette, contrast, luminance

RGB = Tuple[int, int, int]
Box = Tuple[int, int, int, int]
AA = 4  # supersampling factor for shapes
CAP = 0.70      # Poppins cap height / font size
DESC = 0.30     # descender allowance below the last baseline
CAP_DEVANAGARI = 0.92
TEXT_TOL = 4    # px a text's ink may overhang the safe area (glyph side bearings), invisible inside the margin
PHOTO_DIR = Path(__file__).resolve().parent.parent / "assets" / "photos"
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
DEVANAGARI_FONTS = {"regular": "Mukta-Regular.ttf", "medium": "Mukta-Medium.ttf", "semibold": "Mukta-SemiBold.ttf",
                    "bold": "Mukta-Bold.ttf"}  # Mukta (SIL OFL): Devanagari, Latin and ₹; Pillow shapes it with libraqm

# What the card being rendered needs: Devanagari fonts (a Marathi/Hindi post) and whose footer (an agent's or ours).
_CARD: contextvars.ContextVar = contextvars.ContextVar("creative_card", default=(False, None))


@contextmanager
def card(devanagari: bool = False, card_brand: Optional[CardBrand] = None) -> Iterator[None]:
    """Render inside this to draw Devanagari text and/or an agent's footer (layouts.render_layout does it)."""
    token = _CARD.set((devanagari, card_brand))
    try:
        yield
    finally:
        _CARD.reset(token)


def load_font(size: int, weight: str = "regular"):
    if _CARD.get()[0]:
        try:
            return ImageFont.truetype(str(FONT_DIR / DEVANAGARI_FONTS.get(weight, DEVANAGARI_FONTS["regular"])), size)
        except OSError:
            pass
    return _latin_font(size, weight)


def cap() -> float:
    """Height above the baseline the layout reserves for a line: Poppins' cap height, or Devanagari's taller letters with
    their vowel signs (measured 0.91 of the size in Mukta), so Marathi text never rises past the safe margin."""
    return CAP_DEVANAGARI if _CARD.get()[0] else CAP


def card_brand() -> Optional[CardBrand]:
    return _CARD.get()[1]


def brand_name() -> str:
    b = card_brand()
    return b.name if b else brand.NAME


@dataclass
class Item:
    text: str
    box: Box
    size: int
    fill: RGB
    bg_lum: float
    lines: int
    truncated: bool
    role: str
    contrast: float
    orphan: bool = False


@dataclass
class Rendered:
    img: Image.Image
    size: Tuple[int, int]
    layout: str
    items: List[Item] = field(default_factory=list)
    shapes: List[Box] = field(default_factory=list)
    index: int = 0

    @property
    def safe(self) -> Box:
        return (MARGIN, MARGIN, self.size[0] - MARGIN, self.size[1] - MARGIN)


def outside(box: Box, safe: Box, tol: int = 1) -> bool:
    return box[0] < safe[0] - tol or box[1] < safe[1] - tol or box[2] > safe[2] + tol or box[3] > safe[3] + tol


def violations(r: Rendered) -> List[str]:
    # text may overhang by a few pixels: some Devanagari letters' ink starts left of the pen (measured 2 px at 84 px margins)
    out = [f"text '{i.text[:30]}' box {i.box} outside safe area {r.safe}" for i in r.items if outside(i.box, r.safe, TEXT_TOL)]
    out += [f"shape {b} outside safe area" for b in r.shapes if outside(b, r.safe)]
    return out


def gradient(size: Tuple[int, int], top: RGB, bottom: RGB) -> Image.Image:
    mask = Image.linear_gradient("L").resize(size)
    return ImageOps.colorize(mask, black=top, white=bottom)


def mix(a: RGB, b: RGB, t: float) -> RGB:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _balanced(draw, text: str, font, max_w: int) -> List[str]:
    lines = wrap(draw, text, font, max_w)
    n = len(lines)
    if n < 2:
        return lines
    lo, hi = int(max_w * 0.45), max_w
    while lo < hi:
        mid = (lo + hi) // 2
        if len(wrap(draw, text, font, mid)) <= n:
            hi = mid
        else:
            lo = mid + 1
    return wrap(draw, text, font, hi)


class Canvas:
    def __init__(self, size: Tuple[int, int], pal: Palette, layout: str, index: int = 0, bg: Optional[Image.Image] = None,
                 pattern: Optional[str] = "dots", glow_at: Optional[Tuple[float, float]] = (0.85, 0.08)):
        self.size, self.pal, self.layout, self.index = size, pal, layout, index
        self.W, self.H = size
        self.left, self.top, self.right, self.bottom = MARGIN, MARGIN, self.W - MARGIN, self.H - MARGIN
        self.img = bg if bg is not None else gradient(size, pal.bg_top, pal.bg_bottom)
        self.d = ImageDraw.Draw(self.img)
        self.items: List[Item] = []
        self.shapes: List[Box] = []
        if bg is None:
            if glow_at:
                self.glow((int(self.W * glow_at[0]), int(self.H * glow_at[1])), int(self.W * 0.62), pal.glow, 0.22 if not pal.light else 0.35)
            if pattern:
                self.pattern(pattern)

    # ---- background decoration ------------------------------------------------------------------
    def glow(self, center: Tuple[int, int], radius: int, colour: RGB, strength: float = 0.3) -> None:
        mask = ImageOps.invert(Image.radial_gradient("L").resize((radius * 2, radius * 2)).point(lambda v: min(255, int(v * 1.45)))).point(lambda v: int(v * strength))
        self.img.paste(colour, (center[0] - radius, center[1] - radius), mask)

    def pattern(self, kind: str) -> None:
        mask = Image.new("L", (self.W * 2, self.H * 2), 0)
        m = ImageDraw.Draw(mask)
        ink = 26 if not self.pal.light else 34
        if kind == "dots":
            for y in range(40, self.H, 54):
                for x in range(40, self.W, 54):
                    m.ellipse([x * 2 - 3, y * 2 - 3, x * 2 + 3, y * 2 + 3], fill=ink)
        elif kind == "rings":
            cx, cy = int(self.W * 0.9) * 2, int(self.H * 0.06) * 2
            for i in range(1, 9):
                r = i * 150
                m.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ink + 10, width=3)
        elif kind == "grid":
            for x in range(0, self.W, 90):
                m.line([(x * 2, 0), (x * 2, self.H * 2)], fill=ink - 8, width=2)
            for y in range(0, self.H, 90):
                m.line([(0, y * 2), (self.W * 2, y * 2)], fill=ink - 8, width=2)
        mask = mask.resize(self.size, Image.LANCZOS)
        self.img.paste(self.pal.ink if not self.pal.light else self.pal.accent, (0, 0), mask)

    # ---- shapes ---------------------------------------------------------------------------------
    def _mask(self, w: int, h: int, draw_fn: Callable[[ImageDraw.ImageDraw, int], None]) -> Image.Image:
        m = Image.new("L", (w * AA, h * AA), 0)
        draw_fn(ImageDraw.Draw(m), AA)
        return m.resize((w, h), Image.LANCZOS)

    def shape(self, box: Box, draw_fn: Callable[[ImageDraw.ImageDraw, int], None], fill: RGB, alpha: float = 1.0) -> None:
        """Anti-aliased shape: draw_fn(draw, scale) draws in box-local coordinates multiplied by scale."""
        x0, y0, x1, y1 = box
        m = self._mask(x1 - x0, y1 - y0, draw_fn)
        if alpha < 1:
            m = m.point(lambda v: int(v * alpha))
        self.img.paste(fill, (x0, y0), m)

    def shadow(self, box: Box, r: int, blur: int = 26, dy: int = 18, alpha: float = 0.45, grow: int = 0) -> None:
        pad = blur * 3
        x0, y0, x1, y1 = box
        w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([pad - grow, pad - grow, w - pad + grow, h - pad + grow], radius=r + grow, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
        self.img.paste((0, 0, 0) if not self.pal.light else (40, 30, 10), (x0 - pad, y0 - pad + dy), m)

    def rrect(self, box: Box, r: int, fill: Optional[RGB] = None, outline: Optional[RGB] = None, width: int = 0, shadow: bool = False,
              alpha: float = 1.0, log: bool = True, fill_img: Optional[Image.Image] = None) -> None:
        x0, y0, x1, y1 = box
        if log:
            self.shapes.append(box)
        if shadow:
            self.shadow(box, r)
        w, h = x1 - x0, y1 - y0
        outer = self._mask(w, h, lambda d, s: d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r * s, fill=255))
        if fill is not None or fill_img is not None:
            m = outer.point(lambda v: int(v * alpha)) if alpha < 1 else outer
            if fill_img is not None:
                self.img.paste(fill_img.resize((w, h)), (x0, y0), m)
            else:
                self.img.paste(fill, (x0, y0), m)
        if outline is not None and width:
            inner = self._mask(w, h, lambda d, s: d.rounded_rectangle([width * s, width * s, (w - width) * s - 1, (h - width) * s - 1],
                                                                   radius=max(1, (r - width)) * s, fill=255))
            ring = ImageChops.subtract(outer, inner)
            self.img.paste(outline, (x0, y0), ring)

    def circle(self, c: Tuple[int, int], r: int, fill: Optional[RGB] = None, outline: Optional[RGB] = None, width: int = 0,
               shadow: bool = False, alpha: float = 1.0, log: bool = True) -> None:
        self.rrect((c[0] - r, c[1] - r, c[0] + r, c[1] + r), r, fill, outline, width, shadow, alpha, log)

    def line(self, pts: Sequence[Tuple[float, float]], width: int, fill: RGB, alpha: float = 1.0, round_caps: bool = True) -> None:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        pad = width
        box = (int(min(xs)) - pad, int(min(ys)) - pad, int(max(xs)) + pad + 1, int(max(ys)) + pad + 1)

        def fn(d: ImageDraw.ImageDraw, s: int) -> None:
            loc = [((x - box[0]) * s, (y - box[1]) * s) for x, y in pts]
            d.line(loc, fill=255, width=width * s, joint="curve")
            if round_caps:
                for p in (loc[0], loc[-1]):
                    d.ellipse([p[0] - width * s / 2, p[1] - width * s / 2, p[0] + width * s / 2, p[1] + width * s / 2], fill=255)
        self.shape(box, fn, fill, alpha)

    # ---- icon glyphs, drawn from shapes ----------------------------------------------------------
    def icon(self, name: str, c: Tuple[int, int], size: int, fill: RGB, width: Optional[int] = None) -> None:
        x, y, s = c[0] - size // 2, c[1] - size // 2, size
        w = width or max(3, size // 7)
        P = lambda fx, fy: (x + fx * s, y + fy * s)  # noqa: E731
        if name == "check":
            self.line([P(.18, .54), P(.42, .76), P(.84, .28)], w, fill)
        elif name == "cross":
            self.line([P(.22, .22), P(.78, .78)], w, fill)
            self.line([P(.78, .22), P(.22, .78)], w, fill)
        elif name == "arrow":
            self.line([P(.12, .5), P(.86, .5)], w, fill)
            self.line([P(.56, .2), P(.88, .5), P(.56, .8)], w, fill)
        elif name == "chevrons":
            self.line([P(.2, .18), P(.5, .5), P(.2, .82)], w, fill)
            self.line([P(.56, .18), P(.86, .5), P(.56, .82)], w, fill)
        elif name == "star":
            import math
            pts = []
            for i in range(10):
                ang = -math.pi / 2 + i * math.pi / 5
                rad = .5 if i % 2 == 0 else .21
                pts.append((.5 + rad * math.cos(ang), .5 + rad * math.sin(ang)))
            self.shape((x, y, x + s, y + s), lambda d, k: d.polygon([(px * s * k, py * s * k) for px, py in pts], fill=255), fill)
        elif name == "bubble":
            self.shape((x, y, x + s, y + s), lambda d, k: (d.rounded_rectangle([.06 * s * k, .1 * s * k, .94 * s * k, .72 * s * k], radius=.22 * s * k, fill=255),
                                                           d.polygon([(.24 * s * k, .66 * s * k), (.2 * s * k, .92 * s * k), (.5 * s * k, .68 * s * k)], fill=255)), fill)
        elif name == "home":
            self.shape((x, y, x + s, y + s), lambda d, k: (d.polygon([(.5 * s * k, .08 * s * k), (.94 * s * k, .48 * s * k), (.06 * s * k, .48 * s * k)], fill=255),
                                                           d.rectangle([.18 * s * k, .46 * s * k, .82 * s * k, .9 * s * k], fill=255)), fill)
        elif name == "pin":
            self.shape((x, y, x + s, y + s), lambda d, k: (d.ellipse([.2 * s * k, .06 * s * k, .8 * s * k, .66 * s * k], fill=255),
                                                           d.polygon([(.26 * s * k, .5 * s * k), (.5 * s * k, .96 * s * k), (.74 * s * k, .5 * s * k)], fill=255)), fill)
        elif name == "bookmark":
            self.shape((x, y, x + s, y + s), lambda d, k: d.polygon([(.22 * s * k, .06 * s * k), (.78 * s * k, .06 * s * k), (.78 * s * k, .94 * s * k),
                                                                     (.5 * s * k, .7 * s * k), (.22 * s * k, .94 * s * k)], fill=255), fill)
        elif name == "bolt":
            self.shape((x, y, x + s, y + s), lambda d, k: d.polygon([(.58 * s * k, .02 * s * k), (.2 * s * k, .56 * s * k), (.46 * s * k, .56 * s * k),
                                                                     (.38 * s * k, .98 * s * k), (.8 * s * k, .4 * s * k), (.54 * s * k, .4 * s * k)], fill=255), fill)

    # ---- text -----------------------------------------------------------------------------------
    def fit(self, s: str, w: int, size: int, weight: str = "bold", lines: int = 3, min_size: Optional[int] = None, pitch: float = 1.12,
            h: Optional[int] = None, balance: bool = True):
        """Largest size (<= size, >= min_size) whose wrapped text fits w x lines (and h). Returns (font size, lines, height, truncated)."""
        lo = min_size or max(18, int(size * 0.5))
        fs = size
        while True:
            font = load_font(fs, weight)
            ls = _balanced(self.d, s, font, w) if balance and lines > 1 else wrap(self.d, s, font, w)
            height = int(cap() * fs + (len(ls) - 1) * pitch * fs + DESC * fs)
            whole = set(s.split()) <= set(" ".join(ls).split())  # no word broken mid-way
            if whole and len(ls) <= lines and (h is None or height <= h):
                return fs, ls, height, False
            if fs <= lo:
                ls = ls[:lines]
                height = int(cap() * fs + (len(ls) - 1) * pitch * fs + DESC * fs)
                return fs, ls, height, True
            fs = max(lo, fs - 2)

    def measure(self, s: str, w: int, size: int, weight: str = "bold", lines: int = 3, min_size: Optional[int] = None,
                pitch: float = 1.12, h: Optional[int] = None, balance: bool = True) -> int:
        return self.fit(s, w, size, weight, lines, min_size, pitch, h, balance)[2]

    def text(self, s: str, x: int, y: int, w: int, size: int, weight: str = "bold", fill: Optional[RGB] = None, lines: int = 3,
             min_size: Optional[int] = None, align: str = "left", pitch: float = 1.12, h: Optional[int] = None, emph: Sequence[str] = (),
             emph_fill: Optional[RGB] = None, strike: Optional[RGB] = None, balance: bool = True, role: str = "body",
             bg_hint: Optional[RGB] = None, marker: bool = False) -> int:
        """Draw text whose cap-top sits at y inside x..x+w. Returns the y just below the block."""
        fill = fill or self.pal.ink
        fs, ls, height, trunc = self.fit(s, w, size, weight, lines, min_size, pitch, h, balance)
        font = load_font(fs, weight)
        if trunc and ls:
            last = ls[-1]
            while last and self.d.textlength(last + "…", font=font) > w:
                last = last[:-1]
            ls[-1] = last.rstrip() + "…"
        emph_set = {e.lower().strip(".,!?:;\"'“”—-") for e in emph}
        lx0, lx1, ly0, ly1 = self.W, 0, self.H, 0
        pos = []
        for i, line in enumerate(ls):
            base = y + cap() * fs + i * pitch * fs
            lw = self.d.textlength(line, font=font)
            lx = x if align == "left" else (x + (w - lw) / 2 if align == "center" else x + w - lw)
            bb = self.d.textbbox((lx, base), line, font=font, anchor="ls")
            lx0, lx1, ly0, ly1 = min(lx0, bb[0]), max(lx1, bb[2]), min(ly0, bb[1]), max(ly1, bb[3])
            pos.append((line, lx, base, lw))
        box = (int(lx0), int(ly0), int(lx1) + 1, int(ly1) + 1)
        crop = self.img.crop((max(0, box[0]), max(0, box[1]), min(self.W, box[2]), min(self.H, box[3])))
        if bg_hint is not None:
            bg_l = luminance(bg_hint)
        else:
            mean = ImageStat.Stat(crop).mean if crop.size[0] and crop.size[1] else [0, 0, 0]
            bg_l = luminance((int(mean[0]), int(mean[1]), int(mean[2])))
        for line, lx, base, lw in pos:
            if emph_set:
                cx = lx
                space = self.d.textlength(" ", font=font)
                for wd in line.split(" "):
                    hit = wd.lower().strip(".,!?:;\"'“”—-") in emph_set
                    col = (emph_fill or self.pal.accent) if hit else fill
                    if hit and marker:
                        ww = int(self.d.textlength(wd, font=font))
                        self.rrect((int(cx) - 10, int(base - cap() * fs - 0.12 * fs), int(cx) + ww + 10, int(base + 0.26 * fs)), int(fs * 0.16),
                                   self.pal.accent_fill, log=False)
                        col = self.pal.accent_ink
                    self.d.text((cx, base), wd, font=font, fill=col, anchor="ls")
                    cx += self.d.textlength(wd, font=font) + space
            else:
                self.d.text((lx, base), line, font=font, fill=fill, anchor="ls")
            if strike:
                yy = int(base - cap() * fs * 0.36)
                self.d.line([(lx - 6, yy), (lx + lw + 6, yy)], fill=strike, width=max(4, fs // 11))
        ink_l = luminance(fill)
        hi, lo = max(ink_l, bg_l), min(ink_l, bg_l)
        orphan = False
        if len(ls) > 1 and len(ls[-1].split()) == 1:
            last_w = self.d.textlength(ls[-1], font=font)
            orphan = len(ls[-1]) <= 4 or last_w < 0.2 * w
        item = Item(" ".join(ls), box, fs, fill, bg_l, len(ls), trunc, role, (hi + 0.05) / (lo + 0.05), orphan)
        self.items.append(item)
        return y + height

    # ---- brand chrome ---------------------------------------------------------------------------
    def logo(self, x: int, y: int, d: int) -> None:
        agent = card_brand()
        try:
            with Image.open(agent.logo if agent else LOGO_PATH) as im:
                im = ImageOps.fit(im.convert("RGBA"), (d, d), Image.LANCZOS)
        except Exception:
            self.circle((x + d // 2, y + d // 2), d // 2, self.pal.accent_fill)
            self.shapes.append((x, y, x + d, y + d))
            return
        if agent:  # an agent's logo is usually a square photo: draw it in a circle
            mask = Image.new("L", (d * AA, d * AA), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, d * AA - 1, d * AA - 1], fill=255)
            im.putalpha(ImageChops.multiply(im.getchannel("A"), mask.resize((d, d), Image.LANCZOS)))
        self.img.paste(im, (x, y), im)  # the Avasetu mark is a round disc; its own alpha is the mask
        self.shapes.append((x, y, x + d, y + d))

    def brand_bar(self, y: Optional[int] = None, right: Optional[str] = None, dark_bg: bool = True) -> None:
        """Logo + name + second line at the bottom margin (or at y); an optional cue on the right. Ours: the Avasetu mark,
        wordmark and tagline. An agent's: their logo, name and phone (CardBrand)."""
        d = 64
        y = self.bottom - d if y is None else y
        self.logo(self.left, y, d)
        agent = card_brand()
        ink = self.pal.ink if dark_bg else self.pal.card_ink
        self.text(agent.name if agent else brand.NAME, self.left + d + 18, y + 4, 420, 30, "semibold", ink, 1, role="brand",
                  balance=False)
        line = agent.line if agent else brand.TAGLINE
        if line:
            self.text(line, self.left + d + 18, y + 4 + 38, 460 if agent else 420, 24 if agent else 21, "semibold" if agent else "medium",
                      self.pal.accent if dark_bg else self.pal.muted, 1, role="brand", balance=False)
        if right:
            self.text(right, self.right - 360, y + 14, 360, 28, "semibold", self.pal.accent if dark_bg else self.pal.muted, 1, align="right",
                      role="brand", balance=False)

    def chip(self, label: str, x: int, y: int, fill: Optional[RGB] = None, ink: Optional[RGB] = None, size: int = 26,
             outline: Optional[RGB] = None, icon: Optional[str] = None, align_right: bool = False) -> Box:
        """A rounded label. Returns its box."""
        font = load_font(size, "semibold")
        tw = int(self.d.textlength(label, font=font))
        ic = int(size * 1.1) if icon else 0
        pad = int(size * 0.85)
        w = tw + 2 * pad + (ic + 10 if icon else 0)
        h = int(size * 1.95)
        if align_right:
            x = x - w
        fill = fill if fill is not None or outline else self.pal.accent_fill
        ink = ink or (self.pal.accent_ink if fill is not None and outline is None else self.pal.ink)
        self.rrect((x, y, x + w, y + h), h // 2, fill, outline, 3 if outline else 0)
        tx = x + pad
        if icon:
            self.icon(icon, (tx + ic // 2, y + h // 2), ic, ink)
            tx += ic + 10
        self.text(label, tx, y + (h - int(size * cap())) // 2 - 1, tw + 6, size, "semibold", ink, 1, balance=False, role="chip", min_size=size,
                  bg_hint=fill if fill is not None else None)
        return (x, y, x + w, y + h)

    def dots(self, n: int, active: int, cx: int, cy: int, r: int = 8, gap: int = 26, on: Optional[RGB] = None, off: Optional[RGB] = None) -> None:
        total = (n - 1) * gap
        for i in range(n):
            x = cx - total // 2 + i * gap
            if i == active:
                self.rrect((x - r * 2, cy - r, x + r * 2, cy + r), r, on or self.pal.accent_fill)
            else:
                self.circle((x, cy), r, off or mix(self.pal.ink, self.pal.bg_bottom, 0.65))

    def finish(self) -> Rendered:
        return Rendered(self.img, self.size, self.layout, self.items, self.shapes, self.index)


def photo(key: str, size: Tuple[int, int], centering: Tuple[float, float] = (0.5, 0.5)) -> Optional[Image.Image]:
    """A bundled stock photo (by key) or a real photo file (by path) cropped to fill `size`, or None if neither exists."""
    p = PHOTO_DIR / f"{key}.jpg"
    if not p.is_file() and key and Path(key).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        p = Path(key)
    if not p.is_file():
        return None
    with Image.open(p) as im:
        return ImageOps.fit(im.convert("RGB"), size, Image.LANCZOS, centering=centering)


def photo_keys() -> List[str]:
    return sorted(p.stem for p in PHOTO_DIR.glob("*.jpg"))


def scrim(img: Image.Image, start: float, strength: float, color: RGB = (6, 12, 26), top: bool = False) -> Image.Image:
    """Dark gradient over the lower part (or the upper part when top=True), for legible text on a photo."""
    s0 = int(255 * start)
    lut = [0 if v < s0 else int((v - s0) / max(1, 255 - s0) * 255 * strength) for v in range(256)]
    mask = Image.linear_gradient("L").resize(img.size).point(lut)
    if top:
        mask = ImageOps.flip(mask)
    return Image.composite(Image.new("RGB", img.size, color), img, mask)
