"""Compose a vertical MP4 from still images and text, with no video editor: every frame is drawn with Pillow (slow drift on the
photo, eased text animation, cross-fade or slide transitions, progress bar, brand end card) and piped to ffmpeg.

Output: H.264 (yuv420p, High profile), 1080x1920, 30 fps, AAC stereo audio (silent unless `music` is given), faststart, < 30 s.
Text stays inside the Instagram safe zone: nothing in the top 10% or bottom 20% of the frame (see SAFE_TOP / SAFE_BOTTOM).
"""
from app.core import brand
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from app.modules.marketing.images import GOLD, STORY, _logo, brand_background, latin, load_font

from . import ffmpeg

W, H = STORY
FPS = 30
MAX_SECONDS = 29.0            # Reels may be longer; we stay under 30 s on purpose
MAX_BYTES = 20 * 1024 * 1024
SAFE_TOP = int(H * 0.10)      # 192: Instagram's top bar
SAFE_BOTTOM = int(H * 0.80)   # 1536: caption, account name, buttons
SIDE = 72
TEXT_W = W - 2 * SIDE
WHITE = (255, 255, 255)
SOFT = (226, 232, 243)
INK = (24, 30, 44)
NAVY_BLACK = (8, 10, 16)
BRAND = brand.NAME
TAGLINE = brand.TAGLINE
PHONE_RE = re.compile(r"(?:\+?\d[\s\-]?){9,}")
PAD = 28
CONTENT_TOP = SAFE_TOP + 150   # below the brand tag row


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
    layout: str = "center"                              # center | lower
    align: Optional[str] = None                         # left | center (default: center for "center", left for "lower")
    badge: Optional[str] = None                         # static outlined label, e.g. "SAMPLE LISTING"
    seconds: Optional[float] = None
    seed: str = "reel"
    kind: str = "scene"                                 # scene | end


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


# ---- text layers ----------------------------------------------------------------------------------------------------
def _tokens(text: str) -> List[Tuple[str, bool, bool]]:
    """(word, gold, glued): `glued` = no space before it (punctuation right after a gold word stays attached)."""
    out: List[Tuple[str, bool, bool]] = []
    prev_end_space = True
    for i, part in enumerate(latin(text).split("*")):
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
    font = load_font(34, "semibold")
    label = latin(text).upper()
    tw = int(sum(_DRAW.textlength(c, font=font) + 2 for c in label)) + 60
    h = 64
    x0 = SIDE if align == "left" else (W - tw) // 2
    img = Image.new("RGBA", (tw + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    pill = _pill(tw, h, (*GOLD, 255)) if filled else _pill(tw, h, (8, 10, 16, 150), (255, 255, 255, 235))
    img.alpha_composite(pill, (PAD, PAD))
    d = ImageDraw.Draw(img)
    x = PAD + 30
    for ch in label:
        d.text((x, PAD + 9), ch, font=font, fill=(*INK, 255) if filled else (255, 255, 255, 255))
        x += d.textlength(ch, font=font) + 2
    return Item(img, x0 - PAD, y - PAD, (x0, y, x0 + tw, y + h))


def _default_spec(i: int, layout: str):
    """(size, weight, color, max_lines) for the i-th line: a big bold headline first, medium supporting lines after."""
    if i == 0:
        return (124 if layout == "center" else 108), "bold", WHITE, 4
    return 58, "medium", SOFT, 3


def layout_scene(scene: Scene) -> List[Item]:
    """All text items for a scene, positioned inside the safe zone (type shrinks if it would not fit)."""
    if scene.kind == "end":
        return _end_items()
    align = scene.align or ("center" if scene.layout == "center" else "left")
    lines = [l if isinstance(l, TextLine) else TextLine(l) for l in scene.lines]
    lines = [l for l in lines if l.text]
    bottom = SAFE_BOTTOM - 56
    avail = bottom - CONTENT_TOP
    shrink = 1.0
    for _ in range(10):
        blocks = []
        for i, tl in enumerate(lines):
            size, weight, color, mx = _default_spec(i, scene.layout)
            size = int((tl.size or size) * shrink)
            weight, color, mx = tl.weight or weight, tl.color or color, tl.max_lines or mx
            fnt = load_font(size, weight)
            toks = _tokens(tl.text)
            wr = _wrap_balanced(toks, fnt, TEXT_W)
            while len(wr) > mx and size > 34:
                size -= 4
                fnt = load_font(size, weight)
                wr = _wrap_balanced(toks, fnt, TEXT_W)
            blocks.append([(ln, fnt, color) for ln in wr])
        chip_h = 64 + 36 if scene.kicker else 0
        total = chip_h + sum(len(b) * int(b[0][1].size * 1.17) + 30 for b in blocks) - (30 if blocks else 0)
        if total <= avail:
            break
        shrink *= 0.9
    y = bottom - total if scene.layout == "lower" else CONTENT_TOP + (avail - total) // 2 + 20
    y = max(y, CONTENT_TOP)
    items: List[Item] = []
    if scene.kicker:
        items.append(_chip_item(scene.kicker, y, align))
        y += chip_h
    for b in blocks:
        for ln, fnt, color in b:
            items.append(_text_item(ln, fnt, color, align, y))
            y += int(fnt.size * 1.17)
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


class _Prepared:
    """A scene with its base image scaled once, its scrim and text items laid out, ready to draw at any time."""

    def __init__(self, scene: Scene, index: int, is_first: bool):
        self.scene, self.index = scene, index
        src = _load(scene.image)
        self.has_photo = src is not None
        if src is None:
            tall = 0.2 if scene.kind == "end" else 0.24
            src = brand_background((W, H), scene.seed, skyline=True, floor=0.985, tall=tall)
        s = max(W / src.width, H / src.height)
        self.base = src.resize((max(W, round(src.width * s)), max(H, round(src.height * s))), Image.LANCZOS)
        flip = index % 2
        self.z0, self.z1 = (1.0, 1.10) if not flip else (1.10, 1.0)
        if self.has_photo and self.base.width > W * 1.25:   # landscape photo in a portrait frame: pan across it
            self.fx0, self.fx1 = (0.34, 0.66) if not flip else (0.66, 0.34)
        else:
            self.fx0, self.fx1 = (0.47, 0.53) if not flip else (0.53, 0.47)
        self.fy0, self.fy1 = (0.52, 0.46) if not flip else (0.46, 0.52)
        self.depth = None
        if self.has_photo and os.environ.get("REEL_PARALLAX", "on").lower() != "off":
            try:
                from .depth import depth_map
                self.depth = depth_map(self.base)  # 2.5D: nearness per pixel, or None (plain zoom)
            except Exception:
                self.depth = None
        if self.depth is not None:  # with parallax the zoom stays gentle so the depth motion reads clearly
            self.z0, self.z1 = (1.02, 1.07) if not flip else (1.07, 1.02)
        self.mask = self._scrim_mask()
        self.solid = Image.new("RGB", (W, H), NAVY_BLACK)
        self.items = layout_scene(scene)
        self.badge = _chip_item(scene.badge, CONTENT_TOP - 4, "left", filled=False) if scene.badge else None
        self.delay = 0.12 if is_first else 0.30

    def _scrim_mask(self) -> Image.Image:
        grad = Image.linear_gradient("L").resize((W, H))
        if not self.has_photo:
            lut = [int(40 * min(1.0, v / 120)) for v in range(256)]
        elif self.scene.layout == "lower":
            lut = [int(255 * (0.12 + 0.80 * clamp01((v / 255 - 0.28) / 0.55))) for v in range(256)]
        else:
            lut = [int(255 * (0.52 + 0.28 * v / 255)) for v in range(256)]
        return grad.point(lut)

    def background(self, p: float) -> Image.Image:
        z = self.z0 + (self.z1 - self.z0) * p
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

    def frame(self, lt: float, p: float) -> Image.Image:
        img = Image.composite(self.solid, self.background(p), self.mask)
        if self.badge:
            _blit(img, self.badge, ease_out_cubic((lt - 0.1) / 0.5), rise=0)
        for k, it in enumerate(self.items):
            _blit(img, it, ease_out_cubic((lt - self.delay - 0.16 * k) / 0.6), rise=46)
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
    y = SAFE_TOP + 40
    return Item(img, SIDE - PAD, y - PAD, (SIDE, y, SIDE + w, y + h))


def _chrome(img: Image.Image, tag: Item, progress: float, alpha: float) -> None:
    if alpha <= 0.004:
        return
    over = img.copy() if alpha < 0.999 else img
    _blit(over, tag, 1.0, rise=0)
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


class Renderer:
    def __init__(self, scenes: Sequence[Scene], seconds_per_scene: float = 3.0, transition: str = "fade", xfade: float = 0.45,
                 progress: bool = True, end_card: bool = True):
        scenes = list(scenes)
        if end_card and not (scenes and scenes[-1].kind == "end"):
            scenes.append(end_scene())
        _no_phone_numbers(scenes)
        if transition not in ("fade", "slide"):
            raise ReelError("transition must be 'fade' or 'slide'")
        self.transition, self.progress = transition, progress
        self.tl = plan([s.seconds if s.seconds else seconds_per_scene for s in scenes], xfade)
        self.prep = [_Prepared(s, i, i == 0) for i, s in enumerate(scenes)]
        self.tag = _tag_item()

    def _scene_frame(self, i: int, t: float) -> Image.Image:
        lt = t - self.tl.starts[i]
        return self.prep[i].frame(lt, clamp01(lt / self.tl.durations[i]))

    def frame_at(self, t: float) -> Image.Image:
        t = min(t, self.tl.total - 1e-6)
        act = active_scenes(self.tl, t)
        if len(act) == 1:
            i = act[0][0]
            img = self._scene_frame(i, t)
            chrome_a = 0.0 if self.prep[i].scene.kind == "end" else 1.0
        else:
            (i, _), (j, w) = act
            a, b = self._scene_frame(i, t), self._scene_frame(j, t)
            e = ease_in_out_cubic(w)
            if self.transition == "slide":
                img = Image.new("RGB", (W, H))
                off = int(W * e)
                img.paste(a, (-off, 0))
                img.paste(b, (W - off, 0))
            else:
                img = Image.blend(a, b, e)
            chrome_a = (1 - e) if self.prep[j].scene.kind == "end" else 1.0
        _chrome(img, self.tag, t / self.tl.total if self.progress else 0.0, chrome_a)
        return img

    def frames(self) -> Iterator[bytes]:
        for k in range(self.tl.frames):
            yield self.frame_at(k / FPS).tobytes()


def make_reel(scenes: Sequence[Scene], out_path, seconds_per_scene: float = 3.0, music=None, transition: str = "fade",
              xfade: float = 0.45, progress: bool = True, end_card: bool = True, timeout: float = 900.0) -> Path:
    """Render `scenes` (plus the brand end card) to an MP4 at `out_path` and return the path.

    `music` is an optional path to a royalty-free audio file that YOU have the rights to; nothing is bundled or downloaded.
    Without it the reel has a silent stereo AAC track (some players need an audio stream)."""
    r = Renderer(scenes, seconds_per_scene, transition, xfade, progress, end_card)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    total = r.tl.total
    args = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if music:
        if not Path(music).is_file():
            raise ReelError("music file not found")
        args += ["-stream_loop", "-1", "-i", str(music), "-af", f"afade=t=in:d=0.6,afade=t=out:st={max(0.0, total - 1.4):.2f}:d=1.4,volume=0.7"]
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    args += ["-map", "0:v:0", "-map", "1:a:0", "-t", f"{total:.3f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
             "-maxrate", "8M", "-bufsize", "16M", "-g", "60", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(out)]
    try:
        ffmpeg.run_with_frames(args, r.frames(), timeout=timeout)
    except ffmpeg.FfmpegError as e:
        out.unlink(missing_ok=True)
        raise ReelError(str(e))
    if out.stat().st_size > MAX_BYTES:
        out.unlink(missing_ok=True)
        raise ReelError("the reel came out larger than 20 MB")
    return out


def contact_sheet(video, out_png, frames: int = 8, cols: int = 4, thumb_w: int = 360) -> Path:
    """A PNG grid of evenly spaced frames (for reviewing a reel at a glance)."""
    info = ffmpeg.probe(video)
    rate = max(0.05, frames / max(info.duration, 0.5))
    rows = -(-frames // cols)
    ffmpeg.run(["-y", "-i", str(video), "-vf", f"fps={rate:.4f},scale={thumb_w}:-1,tile={cols}x{rows}:padding=6:color=0x101828",
                "-frames:v", "1", str(out_png)])
    return Path(out_png)
