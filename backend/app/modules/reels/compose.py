"""Compose a vertical MP4 from still images and text, with no video editor: every frame is drawn with Pillow (slow drift on the
photo, eased text animation, cross-fade or slide transitions, progress bar, a small brand mark on the last scene) and piped to ffmpeg.
No separate end card by default: a 'Follow for more' card is a dead end that breaks the loop (pass end_card=True to get one).

Output: H.264 (yuv420p, High profile), 1080x1920, 30 fps, AAC stereo audio (the Avasetu signature music unless `music` is given), faststart, < 30 s.
Text stays inside the Instagram safe zone: every text line and the CTA between 14% and 72% of the height (TEXT_TOP / TEXT_BOTTOM;
Instagram's caption, account row and the bottom bar cover roughly the last 20-28%) and left of the right 12% (TEXT_RIGHT: the like,
comment and share buttons). Only the thin progress bar sits above TEXT_TOP.
Text in Devanagari (a Hindi or Marathi reel) is drawn in Mukta, shaped by libraqm; Latin text stays in Poppins. Without libraqm
(`devanagari_ok()` False) Devanagari would not join, so callers keep the screen text Roman and the renderer drops Devanagari.
"""
from app.core import brand
import os
import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from functools import lru_cache
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, features

from app.modules.marketing.images import GOLD, STORY, _logo, brand_background, latin, load_font

from . import ffmpeg

W, H = STORY
FPS = 30
MAX_SECONDS = 29.0            # Reels may be longer; we stay under 30 s on purpose
MIN_SECONDS = 8.0             # shorter than this and a tour/tip reel feels like a flash; scenes are stretched up to it
MAX_BYTES = 20 * 1024 * 1024
SAFE_TOP = int(H * 0.10)      # 192: Instagram's top bar
SAFE_BOTTOM = int(H * 0.80)   # 1536: caption, account name, buttons
TEXT_TOP = -(-H * 14 // 100)   # 269: no text above (the top bar and its icons)
TEXT_BOTTOM = int(H * 0.72)   # 1382: no text below (caption, account row, audio line, bottom bar)
TEXT_RIGHT = int(W * 0.88)    # 950: no text right of this (like / comment / share / remix buttons)
SIDE = 72
TEXT_W = TEXT_RIGHT - SIDE                 # 878: left-aligned lines run from SIDE to TEXT_RIGHT
TEXT_W_CENTER = W - 2 * (W - TEXT_RIGHT)   # 820: centred lines keep the same margin on both sides
WHITE = (255, 255, 255)
SOFT = (226, 232, 243)
INK = (24, 30, 44)
NAVY_BLACK = (8, 10, 16)
BRAND = brand.NAME
TAGLINE = brand.TAGLINE
# a run of 9+ digits that does not start inside a word: 'A51800012345' (a MahaRERA agent number) is not a phone number
PHONE_RE = re.compile(r"(?<![A-Za-z0-9])(?:\+?\d[\s\-]?){9,}")
PAD = 28
# Which version of the look a reel was drawn with, kept in the calendar row's tags so results before and after a change of the
# look can be told apart. Bump it with every change viewers would notice (timing, transitions, text size).
RENDER_VERSION = "2026-10-11-devanagari"   # Hindi and Marathi screen text in Devanagari (Mukta); English reels look the same
TEXT_IN = 0.22         # a later scene's text is fully in this many seconds after its cut (no delay: never an empty screen)
PUNCH_SCALE = 0.035    # each new picture starts 3.5% zoomed in ...
PUNCH_SECONDS = 0.7    # ... and eases out over this long: a gentle push, not a jolt
TEXT_HANDOVER = (0.4, 0.6)   # during a blend the new text starts at 40% of it and the old text is gone by 60%: never two texts on top of each other
MAX_SCREEN_WORDS = 8   # on-screen text longer than this is split over quick screens (most people watch muted and read)
TAG_Y = TEXT_TOP               # the brand tag row (logo + name), under the progress bar
CONTENT_TOP = TAG_Y + 94       # 362: below the brand tag row
BADGE_ROW = 64 + 24            # the outlined badge (drawn at CONTENT_TOP - 4) and a gap under it


class ReelError(Exception):
    pass


# ---- content model ------------------------------------------------------------------------------------------
@dataclass
class TextLine:
    """One text line; `*word*` is drawn in brand gold. `size` None = default for its position (headline first)."""
    text: str
    size: Optional[int] = None
    weight: Optional[str] = None
    color: Optional[Tuple[int, int, int]] = None
    max_lines: Optional[int] = None


@dataclass
class Scene:
    image: Union[Image.Image, str, Path, None] = None   # photo; None = branded gradient with skyline
    lines: Sequence[Union[str, TextLine]] = ()
    kicker: Optional[str] = None                        # small gold label above the text, e.g. "TIP 1 OF 3"
    layout: str = "center"                              # center | lower | top (text just under the brand tag row)
    align: Optional[str] = None                         # left | center (default: left for "lower", center otherwise)
    badge: Optional[str] = None                         # static outlined label, e.g. "SAMPLE LISTING"
    seconds: Optional[float] = None
    seed: str = "reel"
    kind: str = "scene"                                 # scene | end
    brand_mark: bool = False                            # small logo + name above the text (set on the last scene by Renderer)
    screen: bool = False                                # `image` is a designed frame (a product screen in a phone): shown as it is,
                                                        # with no dark scrim, no parallax and only a gentle zoom
    reveal: Optional[Sequence[float]] = None            # a stacked list: seconds after the scene starts at which each line appears
                                                        # (one per line). The stack is laid out at its final size, so a line that
                                                        # joins never moves the ones already there; a line at 0 is there on frame one
    images: Sequence = ()                               # more photos behind the same text (a walkthrough under a stacked list): images[k]
    image_at: Sequence[float] = ()                      # takes over from the one before at image_at[k] seconds, with a short blend


def end_scene(seconds: float = 2.6) -> Scene:
    return Scene(kind="end", seconds=seconds, seed="pune-property-end")


# ---- timing maths (pure) ----------------------------------------------------------------------------------------
@dataclass
class Timeline:
    starts: List[float]
    durations: List[float]
    xfade: float
    total: float

    @property
    def frames(self) -> int:
        return max(1, round(self.total * FPS))


def plan(durations: Sequence[float], xfade: float, max_total: float = MAX_SECONDS) -> Timeline:
    """Scenes overlap by `xfade` seconds (the transition). Durations are scaled down together if the total exceeds `max_total`."""
    if not durations:
        raise ReelError("a reel needs at least one scene")
    durs = [float(d) for d in durations]
    xf = max(0.0, min(xfade, 0.4 * min(durs))) if len(durs) > 1 else 0.0

    def total_of(ds):
        return sum(ds) - xf * (len(ds) - 1)

    total = total_of(durs)
    if total > max_total:
        k = (max_total + xf * (len(durs) - 1)) / sum(durs)
        durs = [d * k for d in durs]
        total = total_of(durs)
    starts, t = [], 0.0
    for d in durs:
        starts.append(t)
        t += d - xf
    return Timeline(starts, durs, xf, total)


def distinct_photos(photos: Sequence) -> list:
    """The photos in order without repeats (paths compared as resolved strings, images by identity)."""
    seen, out = set(), []
    for p in photos or []:
        key = ("img", id(p)) if isinstance(p, Image.Image) else ("path", str(p))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def photo_plan(n_scenes: int, photos: Sequence, min_scenes: int = 1) -> list:
    """One photo per scene, no photo twice, for as many scenes as there are distinct photos (at most `n_scenes`, at least
    `min_scenes`). Only when there are fewer photos than `min_scenes` does a photo come back, never on the next scene: the
    closing scene reuses the opening photo, so the loop back to the hook is seamless."""
    uniq = distinct_photos(photos)
    if not uniq:
        return []
    n = max(min(n_scenes, len(uniq)), min(min_scenes, n_scenes))
    picks = uniq[:n]
    while len(picks) < n:
        picks.append(uniq[(len(picks) - len(uniq)) % len(uniq)])
    if len(picks) > len(uniq) and len(uniq) > 1 and picks[-1] is not picks[0]:
        picks[-1] = picks[0]
    return picks


def stretch(durations: Sequence[float], xfade: float, min_total: float = MIN_SECONDS) -> List[float]:
    """Scale scene durations up (together) so the reel lasts at least `min_total` seconds; longer reels are unchanged."""
    durs = [float(d) for d in durations]
    if not durs:
        return durs
    total = plan(durs, xfade).total
    if total >= min_total:
        return durs
    xf = plan(durs, xfade).xfade
    k = (min_total + xf * (len(durs) - 1)) / sum(durs)
    return [d * k for d in durs]


def split_screens(text: str, max_words: int = MAX_SCREEN_WORDS) -> List[str]:
    """Split on-screen text into screens of at most `max_words` words: at sentence ends first, then at commas, then near the
    middle. Never inside a *gold* span. 'Ask for the *RERA number*. Then look it up on the MahaRERA site.' -> two screens."""
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()] if text.strip() else []

    def open_gold(i):  # True when the cut after words[:i] would fall inside a *gold* span
        return " ".join(words[:i]).count("*") % 2 == 1

    cuts = [i for i in range(1, len(words)) if not open_gold(i)]
    if not cuts:
        return [text.strip()]
    mid = len(words) / 2
    for ends in ((".", "?", "!"), (",", ";", ":")):
        good = [i for i in cuts if words[i - 1].rstrip("*").endswith(ends)]
        if good:
            i = min(good, key=lambda k: abs(k - mid))
            break
    else:
        i = min(cuts, key=lambda k: abs(k - mid))
    return split_screens(" ".join(words[:i]), max_words) + split_screens(" ".join(words[i:]), max_words)


def read_seconds(text: str) -> float:
    """How long a screen of text stays up: enough to read it muted (about 3.5 words a second), never a long hold."""
    return max(1.5, min(3.0, 0.8 + 0.3 * len(text.split())))


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out_cubic(x: float) -> float:
    return 1 - (1 - clamp01(x)) ** 3


def ease_in_out_cubic(x: float) -> float:
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def active_scenes(tl: Timeline, t: float) -> List[Tuple[int, float]]:
    """[(scene index, weight)] at time t: one scene, or two during a transition (the second one's weight = transition progress)."""
    out = [i for i, (s, d) in enumerate(zip(tl.starts, tl.durations)) if s <= t < s + d]
    if len(out) >= 2:
        i, j = out[0], out[1]
        return [(i, 1.0), (j, clamp01((t - tl.starts[j]) / tl.xfade) if tl.xfade else 1.0)]
    return [(out[0] if out else len(tl.starts) - 1, 1.0)]


# ---- fonts: Poppins for Latin text, Mukta for Devanagari ---------------------------------------------------------------
# The creative cards' Mukta files (SIL OFL; Devanagari, Latin and the rupee sign): one copy in the repo.
DEVANAGARI_FONT_DIR = Path(__file__).resolve().parent.parent / "creative" / "assets" / "fonts"
DEVANAGARI_FONTS = {"regular": "Mukta-Regular.ttf", "medium": "Mukta-Medium.ttf", "semibold": "Mukta-SemiBold.ttf",
                    "bold": "Mukta-Bold.ttf"}
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
# Line step as a share of the font size. Poppins: 1.17. In Mukta, Devanagari ink runs from about 0.21 to 1.41 of the size below
# the line's top (vowel signs above the headline, conjuncts and the u / ri signs below it), so its lines step 1.30: about 0.1 of
# the size between one line's lowest sign and the next line's highest.
STEP = 1.17
STEP_DEVANAGARI = 1.30


def has_devanagari(text: Optional[str]) -> bool:
    return bool(DEVANAGARI_RE.search(text or ""))


@lru_cache(maxsize=1)
def devanagari_ok() -> bool:
    """True when Devanagari can be drawn properly here: Pillow has libraqm (it joins the letters and places the vowel signs)
    and the Mukta files are there. Without it the screen text stays Roman (as before) and no reel breaks."""
    try:
        if not features.check("raqm"):
            return False
        ImageFont.truetype(str(DEVANAGARI_FONT_DIR / DEVANAGARI_FONTS["bold"]), 20, layout_engine=ImageFont.Layout.RAQM)
        return True
    except Exception:
        return False


@lru_cache(maxsize=96)
def devanagari_font(size: int, weight: str = "regular"):
    """Mukta at `size`, laid out by libraqm. Only used when devanagari_ok()."""
    return ImageFont.truetype(str(DEVANAGARI_FONT_DIR / DEVANAGARI_FONTS.get(weight, DEVANAGARI_FONTS["regular"])), size,
                              layout_engine=ImageFont.Layout.RAQM)


def _devanagari_text(text: Optional[str]) -> bool:
    """Draw this text in Mukta: it has Devanagari and the shaper is here."""
    return has_devanagari(text) and devanagari_ok()


def text_font(size: int, weight: str = "regular", devanagari: bool = False):
    return devanagari_font(size, weight) if devanagari else load_font(size, weight)


def is_devanagari_font(font) -> bool:
    return Path(getattr(font, "path", "") or "").name in DEVANAGARI_FONTS.values()


def line_step(font) -> int:
    """Distance from one line's top to the next one's, for this font."""
    return int(font.size * (STEP_DEVANAGARI if is_devanagari_font(font) else STEP))


def devanagari_clean(s: Optional[str]) -> str:
    """Screen text drawn in Mukta: Devanagari, the Latin letters, digits and signs the cards use, and the joiners Devanagari
    needs (ZWNJ, ZWJ). Anything else (emoji, other scripts) is dropped rather than drawn as a box."""
    return "".join(c for c in (s or "") if ord(c) < 0x250 or "\u0900" <= c <= "\u097F" or c in "–—’₹\u200c\u200d").strip()


# ---- text layers ----------------------------------------------------------------------------------------------------
def _tokens(text: str, devanagari: bool = False) -> List[Tuple[str, bool, bool]]:
    """(word, gold, glued): `glued` = no space before it (punctuation right after a gold word stays attached).
    `devanagari`: the text is drawn in Mukta, so its Devanagari is kept (otherwise only Latin is: marketing.images.latin)."""
    out: List[Tuple[str, bool, bool]] = []
    prev_end_space = True
    for i, part in enumerate((devanagari_clean(text) if devanagari else latin(text)).split("*")):
        words = part.split()
        lead = part[:1].isspace() if part else True
        for k, w in enumerate(words):
            out.append((w, bool(i % 2), k == 0 and not lead and not prev_end_space and bool(out)))
        if part:
            prev_end_space = part[-1:].isspace()
    return out


def _advance(tokens, k: int, font, space: float) -> float:
    return _DRAW.textlength(tokens[k][0], font=font) + (space if k + 1 < len(tokens) and not tokens[k + 1][2] else 0)


_DRAW = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def _wrap(tokens, font, max_w: int) -> List[List[Tuple[str, bool]]]:
    space = _DRAW.textlength(" ", font=font)
    lines, cur, width = [], [], 0.0
    for w, g, glue in tokens:
        ww = _DRAW.textlength(w, font=font)
        if cur and not glue and width + space + ww > max_w:
            lines.append(cur)
            cur, width = [], 0.0
        width += (space if cur and not glue else 0) + ww
        cur.append((w, g, False if not cur else glue))
    if cur:
        lines.append(cur)
    return lines


def _wrap_balanced(tokens, font, max_w: int):
    """Wrap to the fewest lines, then narrow the measure while the line count stays the same, so the last line is not a lone word."""
    best = _wrap(tokens, font, max_w)
    if len(best) < 2:
        return best
    w = max_w
    while w > max_w * 0.55:
        w -= max_w * 0.03
        trial = _wrap(tokens, font, int(w))
        if len(trial) != len(best):
            break
        widest = max(sum(_advance(ln, k, font, _DRAW.textlength(" ", font=font)) for k in range(len(ln))) for ln in trial)
        if widest > max_w:
            break
        best = trial
    return best


@dataclass
class Item:
    img: Image.Image           # RGBA, includes PAD of padding for the shadow
    x: int
    y: int
    box: Tuple[int, int, int, int]  # the visible text/shape box in frame coordinates (used for safe-zone checks)
    block: int = 0             # which of the scene's lines it belongs to (Scene.reveal); the kicker goes with the first, the mark with the last


def _shadowed(w: int, h: int, draw_fn, strength: float = 0.55) -> Image.Image:
    """RGBA of size (w+2PAD, h+2PAD): the painted content over a soft dark shadow. draw_fn(draw, dx, dy, mode) mode: shadow|fill."""
    size = (w + 2 * PAD, h + 2 * PAD)
    sh = Image.new("L", size, 0)
    draw_fn(ImageDraw.Draw(sh), PAD, PAD + 4, "shadow")
    sh = sh.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(min(255, v * strength * 1.6)))
    layer = Image.new("RGBA", size, NAVY_BLACK + (0,))
    layer.putalpha(sh)
    top = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(top), PAD, PAD, "fill")
    return Image.alpha_composite(layer, top)


def _text_item(tokens, font, color, align: str, y: int) -> Item:
    space = _DRAW.textlength(" ", font=font)
    width = int(sum(_advance(tokens, k, font, space) for k in range(len(tokens))) - (space if False else 0))
    asc, desc = font.getmetrics()
    h = asc + desc
    x0 = SIDE if align == "left" else (W - width) // 2

    def paint(d, dx, dy, mode):
        x = dx
        for k, (w, g, _) in enumerate(tokens):
            d.text((x, dy), w, font=font, fill=255 if mode == "shadow" else ((*GOLD, 255) if g else (*color, 255)))
            x += _advance(tokens, k, font, space)

    return Item(_shadowed(width, h, paint), x0 - PAD, y - PAD, (x0, y, x0 + width, y + h))


def _pill(tw: int, h: int, fill, outline=None) -> Image.Image:
    s = 3
    big = Image.new("RGBA", (tw * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle([0, 0, tw * s - 1, h * s - 1], radius=h * s // 2, fill=fill, outline=outline, width=3 * s if outline else 0)
    return big.resize((tw, h), Image.LANCZOS)


def _chip_item(text: str, y: int, align: str, filled: bool = True) -> Item:
    h = 64
    ink = (*INK, 255) if filled else (255, 255, 255, 255)
    deva = _devanagari_text(text)
    if deva:   # a Devanagari label is one shaped run (letter spacing would break the joins), centred on its ink
        font = devanagari_font(34, "semibold")
        label = devanagari_clean(text)
        tw = int(_DRAW.textlength(label, font=font)) + 60
    else:
        font = load_font(34, "semibold")
        label = latin(text).upper()
        tw = int(sum(_DRAW.textlength(c, font=font) + 2 for c in label)) + 60
    x0 = SIDE if align == "left" else (W - tw) // 2
    img = Image.new("RGBA", (tw + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    pill = _pill(tw, h, (*GOLD, 255)) if filled else _pill(tw, h, (8, 10, 16, 150), (255, 255, 255, 235))
    img.alpha_composite(pill, (PAD, PAD))
    d = ImageDraw.Draw(img)
    x = PAD + 30
    if deva:
        top, bottom = font.getbbox(label)[1::2]
        d.text((x, PAD + (h - top - bottom) // 2), label, font=font, fill=ink)
        return Item(img, x0 - PAD, y - PAD, (x0, y, x0 + tw, y + h))
    for ch in label:
        d.text((x, PAD + 9), ch, font=font, fill=ink)
        x += d.textlength(ch, font=font) + 2
    return Item(img, x0 - PAD, y - PAD, (x0, y, x0 + tw, y + h))


def _default_spec(i: int, layout: str):
    """(size, weight, color, max_lines) for the i-th line: a big bold headline first, medium supporting lines after."""
    if i == 0:
        return (124 if layout == "center" else 108), "bold", WHITE, 4
    return 58, "medium", SOFT, 3


MARK_D = 84


def _mark_item(y: int, align: str) -> Item:
    """The brand mark on the last scene: the round logo with the name and tagline beside it."""
    name_f, tag_f = load_font(46, "bold"), load_font(30, "medium")
    tw = int(max(_DRAW.textlength(BRAND, font=name_f), _DRAW.textlength(TAGLINE, font=tag_f)))
    w, h = MARK_D + 22 + tw, MARK_D
    logo = _logo(MARK_D)

    def paint(d, dx, dy, mode):
        if mode == "shadow":
            d.ellipse([dx, dy, dx + MARK_D, dy + MARK_D], fill=255)
        tx = dx + MARK_D + 22
        d.text((tx, dy + 2), BRAND, font=name_f, fill=255 if mode == "shadow" else (*WHITE, 255))
        d.text((tx, dy + 52), TAGLINE, font=tag_f, fill=255 if mode == "shadow" else (*GOLD, 255))

    img = _shadowed(w, h, paint, strength=0.45)
    if logo is not None:
        img.alpha_composite(logo, (PAD, PAD))
    x0 = SIDE if align == "left" else (W - w) // 2
    return Item(img, x0 - PAD, y - PAD, (x0, y, x0 + w, y + h))


def layout_scene(scene: Scene) -> List[Item]:
    """All text items for a scene, positioned inside the safe zone (type shrinks if it would not fit)."""
    if scene.kind == "end":
        return _end_items()
    align = scene.align or ("left" if scene.layout == "lower" else "center")
    lines = [l if isinstance(l, TextLine) else TextLine(l) for l in scene.lines]
    if scene.reveal is not None and len(scene.reveal) != len(lines):
        raise ReelError("a stacked list needs one reveal time per line")
    lines = [l for l in lines if l.text]
    bottom = TEXT_BOTTOM
    top = CONTENT_TOP + (BADGE_ROW if scene.badge else 0)   # a full screen of text never runs into the badge
    avail = bottom - top
    max_w = TEXT_W if align == "left" else TEXT_W_CENTER
    shrink = 1.0
    for _ in range(10):
        blocks = []
        for i, tl in enumerate(lines):
            size, weight, color, mx = _default_spec(i, scene.layout)
            size = int((tl.size or size) * shrink)
            weight, color, mx = tl.weight or weight, tl.color or color, tl.max_lines or mx
            deva = _devanagari_text(tl.text)   # measured, wrapped and drawn with the same font and layout engine
            fnt = text_font(size, weight, deva)
            toks = _tokens(tl.text, deva)
            wr = _wrap_balanced(toks, fnt, max_w)
            while len(wr) > mx and size > 34:
                size -= 4
                fnt = text_font(size, weight, deva)
                wr = _wrap_balanced(toks, fnt, max_w)
            blocks.append([(ln, fnt, color) for ln in wr])
        chip_h = 64 + 36 if scene.kicker else 0
        mark_h = MARK_D + 40 if scene.brand_mark else 0
        total = mark_h + chip_h + sum(len(b) * line_step(b[0][1]) + 30 for b in blocks) - (30 if blocks else 0)
        if blocks:  # the last line's glyph box (ascent + descent) can reach below its line step
            last = blocks[-1][-1][1]
            total += max(0, sum(last.getmetrics()) - line_step(last))
        if total <= avail:
            break
        shrink *= 0.9
    if scene.layout == "lower":
        y = bottom - total
    elif scene.layout == "top":
        y = top
    else:
        y = min(top + (avail - total) // 2 + 20, bottom - total)   # the nudge down never pushes a full screen past the zone
    y = max(y, top)
    items: List[Item] = []
    if scene.brand_mark:
        items.append(replace(_mark_item(y, align), block=max(0, len(blocks) - 1)))
        y += mark_h
    if scene.kicker:
        items.append(_chip_item(scene.kicker, y, align))
        y += chip_h
    for i, b in enumerate(blocks):
        for ln, fnt, color in b:
            items.append(replace(_text_item(ln, fnt, color, align, y), block=i))
            y += line_step(fnt)
        y += 30
    return items


def _button_item(text: str, y: int) -> Item:
    font = load_font(50, "semibold")
    tw = int(_DRAW.textlength(text, font=font)) + 2 * 64
    h = 118
    img = Image.new("RGBA", (tw + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    img.alpha_composite(_pill(tw, h, (*GOLD, 255)), (PAD, PAD))
    asc, desc = font.getmetrics()
    ImageDraw.Draw(img).text((PAD + 64, PAD + (h - asc - desc) // 2 - 2), text, font=font, fill=(*INK, 255))
    x = (W - tw) // 2
    return Item(img, x - PAD, y - PAD, (x, y, x + tw, y + h))


def _end_items() -> List[Item]:
    """End card: badge, brand name, tagline, 'Follow for more' button. No phone numbers, by design."""
    items: List[Item] = []
    d = 250
    logo = _logo(d)
    if logo is not None:
        img = Image.new("RGBA", (d + 2 * PAD, d + 2 * PAD), (0, 0, 0, 0))
        img.alpha_composite(logo, (PAD, PAD))
        x, y = (W - d) // 2, 470
        items.append(Item(img, x - PAD, y - PAD, (x, y, x + d, y + d)))
    items.append(_text_item(_tokens(BRAND), load_font(96, "bold"), WHITE, "center", 770))
    items.append(_text_item(_tokens(TAGLINE), load_font(52, "medium"), GOLD, "center", 910))
    items.append(_button_item("Follow for more", 1110))
    return items


# ---- backgrounds and motion -------------------------------------------------------------------------------------
def _load(image) -> Optional[Image.Image]:
    if image is None:
        return None
    if isinstance(image, Image.Image):
        return ImageOps.exif_transpose(image).convert("RGB")
    try:
        with Image.open(image) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((3000, 3000), Image.LANCZOS)
            return im
    except Exception:
        raise ReelError("could not read a scene image")


IMAGE_BLEND = 0.35   # a photo change behind a stacked list: a quick blend, the text stays still


class _Backdrop:
    """One picture with its own slow motion (zoom, pan, 2.5D parallax), drawn at any point of its time on screen."""

    def __init__(self, image, scene: Scene, index: int):
        src = _load(image)
        self.has_photo = src is not None
        if src is None:
            tall = 0.2 if scene.kind == "end" else 0.24
            src = brand_background((W, H), scene.seed, skyline=True, floor=0.985, tall=tall)
        s = max(W / src.width, H / src.height)
        self.base = src.resize((max(W, round(src.width * s)), max(H, round(src.height * s))), Image.LANCZOS)
        self.index = index
        flip = index % 2
        self.z0, self.z1 = (1.0, 1.10) if not flip else (1.10, 1.0)
        if self.has_photo and self.base.width > W * 1.25:   # landscape photo in a portrait frame: pan across it
            self.fx0, self.fx1 = (0.34, 0.66) if not flip else (0.66, 0.34)
        else:
            self.fx0, self.fx1 = (0.47, 0.53) if not flip else (0.53, 0.47)
        self.fy0, self.fy1 = (0.52, 0.46) if not flip else (0.46, 0.52)
        if scene.screen:  # a designed frame: barely moves, so the screen stays readable
            self.z0, self.z1 = (1.0, 1.035)
            self.fx0, self.fx1, self.fy0, self.fy1 = 0.5, 0.5, 0.5, 0.5
        self.depth = None
        if self.has_photo and not scene.screen and os.environ.get("REEL_PARALLAX", "on").lower() != "off":
            try:
                from .depth import depth_map
                self.depth = depth_map(self.base)  # 2.5D: nearness per pixel, or None (plain zoom)
            except Exception:
                self.depth = None
        if self.depth is not None:  # with parallax the zoom stays gentle so the depth motion reads clearly
            self.z0, self.z1 = (1.02, 1.07) if not flip else (1.07, 1.02)

    def view(self, p: float, zoom: float = 1.0) -> Image.Image:
        z = (self.z0 + (self.z1 - self.z0) * p) * zoom
        bw, bh = self.base.size
        ww, wh = min(W / z, bw), min(H / z, bh)
        cx = (self.fx0 + (self.fx1 - self.fx0) * p) * bw
        cy = (self.fy0 + (self.fy1 - self.fy0) * p) * bh
        x0 = min(max(cx - ww / 2, 0), bw - ww)
        y0 = min(max(cy - wh / 2, 0), bh - wh)
        view = self.base.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + ww, y0 + wh))
        if self.depth is None:
            return view
        import cv2
        dcrop = self.depth[int(y0):int(y0 + wh), int(x0):int(x0 + ww)]
        d = cv2.resize(dcrop, (W, H), interpolation=cv2.INTER_LINEAR)
        swing = (p - 0.5) * 2 * (1 if self.index % 2 == 0 else -1)
        from .depth import parallax
        return parallax(view, d, shift_x=34 * swing, shift_y=-10 * swing)


class _Prepared:
    """A scene with its base image scaled once, its scrim and text items laid out, ready to draw at any time."""

    def __init__(self, scene: Scene, index: int, is_first: bool):
        self.scene, self.index = scene, index
        if len(scene.images) != len(scene.image_at):
            raise ReelError("each extra image needs the time it comes in")
        self.backdrops = [_Backdrop(scene.image, scene, index)] + [_Backdrop(im, scene, index + k + 1) for k, im in enumerate(scene.images)]
        self.backdrop_at = [0.0] + [float(t) for t in scene.image_at]
        self.has_photo = self.backdrops[0].has_photo
        self.mask = self._scrim_mask()
        self.solid = Image.new("RGB", (W, H), NAVY_BLACK)
        self.items = layout_scene(scene)
        self.reveal = [t for l, t in zip(scene.lines, scene.reveal) if (l.text if isinstance(l, TextLine) else l)] if scene.reveal else None
        self.is_first = is_first
        self.badge = _chip_item(scene.badge, CONTENT_TOP - 4, "left", filled=False) if scene.badge else None
        # The opening scene has no entrance animation: frame one already shows the whole hook, so it is readable before anyone
        # swipes away (and the cover image, a still of that frame, shows it too). Later scenes pop their text in from the cut:
        # a slow fade after a delay left the screen empty for about a second right after the hook (the moment viewers decide).
        self.animate = not is_first
        self.delay, self.fade, self.stagger = 0.0, TEXT_IN, 0.05
        self.punch = 0.0 if is_first or scene.screen else PUNCH_SCALE   # each cut lands slightly zoomed in and settles: motion on every cut

    def _scrim_mask(self) -> Image.Image:
        if self.scene.screen:
            return Image.new("L", (W, H), 0)
        grad = Image.linear_gradient("L").resize((W, H))
        if not self.has_photo:
            lut = [int(40 * min(1.0, v / 120)) for v in range(256)]
        elif self.scene.layout == "lower":
            lut = [int(255 * (0.12 + 0.80 * clamp01((v / 255 - 0.28) / 0.55))) for v in range(256)]
        else:
            lut = [int(255 * (0.52 + 0.28 * v / 255)) for v in range(256)]
        return grad.point(lut)

    def background(self, p: float, lt: float = 1.0) -> Image.Image:
        """The scene's picture at progress p. With several pictures each one moves over its own stretch of the scene, lands with
        the same gentle punch-in as a cut, and blends in over IMAGE_BLEND seconds."""
        punch = lambda t, amount: 1 + amount * (1 - ease_out_cubic(t / PUNCH_SECONDS))
        if len(self.backdrops) == 1:
            return self.backdrops[0].view(p, punch(lt, self.punch))
        dur = lt / p if p > 0 else (self.scene.seconds or 1.0)   # the scene's length as planned (plan() may have scaled it)
        ends = self.backdrop_at[1:] + [max(dur, self.backdrop_at[-1] + 1e-3)]
        k = max(i for i, t in enumerate(self.backdrop_at) if t <= lt)

        def draw(i):
            t0, t1 = self.backdrop_at[i], ends[i] + (IMAGE_BLEND if i < k else 0.0)
            amount = self.punch if i == 0 else PUNCH_SCALE
            return self.backdrops[i].view(clamp01((lt - t0) / max(1e-3, t1 - t0)), punch(lt - t0, amount))

        cur = draw(k)
        w = (lt - self.backdrop_at[k]) / IMAGE_BLEND
        if k == 0 or w >= 1:
            return cur
        return Image.blend(draw(k - 1), cur, ease_in_out_cubic(w))

    def badge_alpha(self, lt: float) -> float:
        return ease_out_cubic(lt / TEXT_IN) if self.animate else 1.0

    def item_alpha(self, k: int, lt: float) -> float:
        """Opacity (and so the rise offset) of the k-th text item at scene time lt: 1.0 means in its final place."""
        if self.reveal:  # a stacked list: each line pops in at its own time and stays; the opening scene's first line is there on frame one
            at = self.reveal[self.items[k].block]
            if at <= 0 and self.is_first:
                return 1.0
            return ease_out_cubic((lt - max(at, self.delay)) / self.fade)
        return ease_out_cubic((lt - self.delay - self.stagger * k) / self.fade) if self.animate else 1.0

    def frame(self, lt: float, p: float, text_a: float = 1.0) -> Image.Image:
        """`text_a` < 1 while this scene is on its way out: its text leaves before the next scene's text arrives (no overlap)."""
        img = Image.composite(self.solid, self.background(p, lt), self.mask)
        if self.badge:
            _blit(img, self.badge, self.badge_alpha(lt), rise=0)
        for k, it in enumerate(self.items):
            _blit(img, it, self.item_alpha(k, lt) * text_a, rise=24)
        return img


def _blit(img: Image.Image, it: Item, a: float, rise: int = 46) -> None:
    if a <= 0.004:
        return
    alpha = it.img.getchannel("A")
    if a < 0.999:
        alpha = alpha.point([int(v * a) for v in range(256)])
    img.paste(it.img, (it.x, it.y + int((1 - a) * rise)), alpha)


# ---- chrome: progress bar and brand tag ---------------------------------------------------------------------------
def _tag_item() -> Item:
    badge = _logo(64)
    font = load_font(32, "semibold")
    tw = int(_DRAW.textlength(BRAND, font=font))
    w, h = 64 + 18 + tw, 64
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    if badge is not None:
        img.alpha_composite(badge, (PAD, PAD))
    shadow = _shadowed(tw, 40, lambda d, dx, dy, m: d.text((dx, dy), BRAND, font=font, fill=255 if m == "shadow" else (*WHITE, 255)))
    img.alpha_composite(shadow, (64 + 18, PAD + 10 - PAD))
    y = TAG_Y
    return Item(img, SIDE - PAD, y - PAD, (SIDE, y, SIDE + w, y + h))


def _chrome(img: Image.Image, tag: Item, progress: float, alpha: float, bar: bool = True, tag_alpha: float = 1.0) -> None:
    """The brand tag (at `tag_alpha` of `alpha`) and the progress bar, drawn at `alpha` over the frame."""
    if alpha <= 0.004:
        return
    over = img.copy() if alpha < 0.999 else img
    if tag_alpha >= 0.999:
        _blit(over, tag, 1.0, rise=0)
    elif tag_alpha > 0.004:
        _blit(over, tag, tag_alpha, rise=0)
    if not bar:
        return
    d = ImageDraw.Draw(over)
    y, h = SAFE_TOP + 4, 7
    d.rounded_rectangle([SIDE, y, W - SIDE, y + h], radius=h // 2, fill=(92, 100, 118))
    fw = int((W - 2 * SIDE) * clamp01(progress))
    if fw > h:
        d.rounded_rectangle([SIDE, y, SIDE + fw, y + h], radius=h // 2, fill=GOLD)
    if over is not img:
        img.paste(Image.blend(img, over, alpha))


# ---- rendering --------------------------------------------------------------------------------------------------------
def _no_phone_numbers(scenes: Sequence[Scene]) -> None:
    """Brand rule: no phone numbers on reels (the agent's tools answer the buyer). Checked on everything that will be drawn."""
    for s in scenes:
        texts = [l.text if isinstance(l, TextLine) else l for l in s.lines] + [s.kicker or "", s.badge or ""]
        if any(PHONE_RE.search(t) for t in texts):
            raise ReelError("reel text must not contain a phone number")


def finish_scenes(scenes: Sequence[Scene], end_card: bool = False) -> List[Scene]:
    """The scenes as rendered: never two end cards in a row; with end_card=True exactly one end card closes the reel; otherwise
    the last content scene carries the brand mark (the reel loops straight back to the hook, no dead end)."""
    out: List[Scene] = []
    for s in scenes:
        if s.kind == "end" and out and out[-1].kind == "end":
            continue  # a duplicated end card
        out.append(s)
    if end_card and not (out and out[-1].kind == "end"):
        out.append(end_scene())
    if out and out[-1].kind != "end" and not end_card:
        out[-1] = replace(out[-1], brand_mark=True)
    return out


class Renderer:
    def __init__(self, scenes: Sequence[Scene], seconds_per_scene: float = 3.0, transition: str = "fade", xfade: float = 0.45,
                 progress: bool = True, end_card: bool = False, hook_tag: bool = True):
        """hook_tag=False: no brand tag while the hook (scene 1) is on screen; it fades in with scene 2. The first second belongs to the
        viewer's problem, not to our name."""
        scenes = finish_scenes(scenes, end_card)
        self.hook_tag = hook_tag
        _no_phone_numbers(scenes)
        if transition not in ("fade", "slide"):
            raise ReelError("transition must be 'fade' or 'slide'")
        self.transition, self.progress = transition, progress
        self.tl = plan([s.seconds if s.seconds else seconds_per_scene for s in scenes], xfade)
        self.prep = [_Prepared(s, i, i == 0) for i, s in enumerate(scenes)]
        for q in self.prep[1:]:   # the incoming text starts a little before the middle of the blend, as the outgoing text leaves
            q.delay = TEXT_HANDOVER[0] * self.tl.xfade
        for a, b in zip(self.prep, self.prep[1:]):  # the next screen of the same picture (a long line split in two): the background
            if b.scene.seed == a.scene.seed and b.scene.image is a.scene.image:   # carries on where it was (the zoom direction
                b.punch = 0.0                                                     # alternates, so it starts where the last ended)
        self.tag = _tag_item()

    def _scene_frame(self, i: int, t: float, text_a: float = 1.0) -> Image.Image:
        lt = t - self.tl.starts[i]
        return self.prep[i].frame(lt, clamp01(lt / self.tl.durations[i]), text_a)

    def frame_at(self, t: float) -> Image.Image:
        t = min(t, self.tl.total - 1e-6)
        act = active_scenes(self.tl, t)
        tag_a = 1.0
        if len(act) == 1:
            i = act[0][0]
            img = self._scene_frame(i, t)
            chrome_a = 0.0 if self.prep[i].scene.kind == "end" else 1.0
            if i == 0 and not self.hook_tag:
                tag_a = 0.0
        else:
            (i, _), (j, w) = act
            a = self._scene_frame(i, t, 1 - ease_out_cubic(w / TEXT_HANDOVER[1]))   # old text gone by 60% of the blend
            b = self._scene_frame(j, t)
            e = ease_in_out_cubic(w)
            if self.transition == "slide":
                img = Image.new("RGB", (W, H))
                off = int(W * e)
                img.paste(a, (-off, 0))
                img.paste(b, (W - off, 0))
            else:
                img = Image.blend(a, b, e)
            chrome_a = (1 - e) if self.prep[j].scene.kind == "end" else 1.0
            if i == 0 and not self.hook_tag:
                tag_a = e
        _chrome(img, self.tag, t / self.tl.total if self.progress else 0.0, chrome_a, tag_alpha=tag_a)
        return img

    def cover(self) -> Image.Image:
        """The cover: the hook scene as a still with all its text in place (no progress bar, it is not playing)."""
        img = self._scene_frame(0, 0.0)
        _chrome(img, self.tag, 0.0, 0.0 if self.prep[0].scene.kind == "end" else 1.0, bar=False, tag_alpha=1.0 if self.hook_tag else 0.0)
        return img

    def frames(self) -> Iterator[bytes]:
        for k in range(self.tl.frames):
            yield self.frame_at(k / FPS).tobytes()


def cover_path(video) -> Path:
    """Where the cover of `video` lives: next to it, same name + '-cover.jpg' (reel.mp4 -> reel-cover.jpg)."""
    v = Path(video)
    return v.with_name(f"{v.stem}-cover.jpg")


def write_cover(renderer: "Renderer", video) -> Path:
    out = cover_path(video)
    renderer.cover().save(out, "JPEG", quality=86, optimize=True, progressive=True)
    return out


def brand_music_on() -> bool:
    return os.environ.get("REEL_BRAND_MUSIC", "on").strip().lower() != "off"


def encode(frames: Iterable[bytes], total: float, out_path, music=None, timeout: float = 900.0) -> Path:
    """Encode raw 1080x1920 RGB frames lasting `total` seconds to an MP4 with an audio track: `music` when given, else the Avasetu
    signature music (reels.music; REEL_BRAND_MUSIC=off gives a silent track instead)."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    brand_bed = music is None and brand_music_on()
    with tempfile.TemporaryDirectory() as work:
        if brand_bed:
            from .music import write as write_music
            music = write_music(Path(work) / "brand.wav", seconds=total)
        args = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if music:
            if not Path(music).is_file():
                raise ReelError("music file not found")
            vol = 0.5 if brand_bed else 0.7   # the bed alone (no voice over it) sits quieter than a supplied mix
            args += ["-stream_loop", "-1", "-i", str(music), "-af", f"afade=t=in:d=0.6,afade=t=out:st={max(0.0, total - 1.4):.2f}:d=1.4,volume={vol}"]
        else:
            args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        args += ["-map", "0:v:0", "-map", "1:a:0", "-t", f"{total:.3f}",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
                 "-maxrate", "8M", "-bufsize", "16M", "-g", "60", "-r", str(FPS),
                 "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(out)]
        try:
            ffmpeg.run_with_frames(args, frames, timeout=timeout)
        except ffmpeg.FfmpegError as e:
            out.unlink(missing_ok=True)
            raise ReelError(str(e))
    if out.stat().st_size > MAX_BYTES:
        out.unlink(missing_ok=True)
        raise ReelError("the reel came out larger than 20 MB")
    return out


def make_reel(scenes: Sequence[Scene], out_path, seconds_per_scene: float = 3.0, music=None, transition: str = "fade",
              xfade: float = 0.45, progress: bool = True, end_card: bool = False, timeout: float = 900.0, hook_tag: bool = True) -> Path:
    """Render `scenes` (plus the brand end card only when end_card=True) to an MP4 at `out_path` and return the path. A 1080x1920 cover JPG (the hook
    scene as a still, see `cover_path`) is written next to it, for Instagram's `cover_url`.

    `music` is an optional path to an audio file that YOU have the rights to (a voice-over mixed with our bed, say); without it the reel
    carries the Avasetu signature music (see `encode`)."""
    if music and not Path(music).is_file():
        raise ReelError("music file not found")
    r = Renderer(scenes, seconds_per_scene, transition, xfade, progress, end_card, hook_tag)
    out = encode(r.frames(), r.tl.total, out_path, music=music, timeout=timeout)
    write_cover(r, out)
    return out


def contact_sheet(video, out_png, frames: int = 8, cols: int = 4, thumb_w: int = 360) -> Path:
    """A PNG grid of evenly spaced frames (for reviewing a reel at a glance)."""
    info = ffmpeg.probe(video)
    rate = max(0.05, frames / max(info.duration, 0.5))
    rows = -(-frames // cols)
    ffmpeg.run(["-y", "-i", str(video), "-vf", f"fps={rate:.4f},scale={thumb_w}:-1,tile={cols}x{rows}:padding=6:color=0x101828",
                "-frames:v", "1", str(out_png)])
    return Path(out_png)
