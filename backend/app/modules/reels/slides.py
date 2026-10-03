"""A reel made from a post's finished slides (a carousel already designed at 1080x1350): each slide shown whole, with a soft
blurred copy of itself behind it, a gentle zoom and cross-fades, over the Avasetu signature music.

Used where a carousel cannot be swiped: Facebook shows a multi-photo Page post as a grid, so the Facebook copy of a carousel goes
out as one Reel that plays the slides in order. The slides already carry their own text and brand, so nothing is drawn on top.
Each slide is scaled to sit inside the Reels safe area (clear of the top bar, the caption and account row at the bottom, and most
of the like/comment/share column on the right).
"""
from pathlib import Path
from typing import Iterator, List, Sequence

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from .compose import FPS, H, MAX_SECONDS, W, ReelError, clamp01, cover_path, ease_in_out_cubic, encode

SLIDE_W = 940                   # 1080x1350 slide -> 940x1175
SLIDE_TOP = 250                 # ends at 1425, above the caption/account row (Instagram and Facebook cover roughly the last 20%)
SECONDS_PER_SLIDE = 3.2
XFADE = 0.45
ZOOM = 0.035                    # the slide grows by 3.5% while it is on screen
MAX_SLIDES = 8


def _open(path) -> Image.Image:
    try:
        with Image.open(path) as im:
            return ImageOps.exif_transpose(im).convert("RGB")
    except Exception:
        raise ReelError("could not read a slide")


class _Slide:
    def __init__(self, img: Image.Image):
        s = SLIDE_W / img.width
        self.fg = img.resize((SLIDE_W, round(img.height * s)), Image.LANCZOS)
        if SLIDE_TOP + self.fg.height > H - 300:  # a very tall slide: fit it by height instead
            h = H - 300 - SLIDE_TOP
            self.fg = img.resize((round(img.width * h / img.height), h), Image.LANCZOS)
        cover = max(W / img.width, H / img.height)
        bg = img.resize((round(img.width * cover) + 2, round(img.height * cover) + 2), Image.BILINEAR)
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
        self.bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(42))).enhance(0.45)

    def frame(self, p: float) -> Image.Image:
        z = 1.0 + ZOOM * p
        fw, fh = round(self.fg.width * z), round(self.fg.height * z)
        fg = self.fg.resize((fw, fh), Image.BILINEAR) if z != 1.0 else self.fg
        img = self.bg.copy()
        cx, cy = W // 2, SLIDE_TOP + self.fg.height // 2
        img.paste(fg, (cx - fw // 2, cy - fh // 2))
        return img


def timeline(n: int, seconds: float = SECONDS_PER_SLIDE, xfade: float = XFADE):
    """(start of each slide, seconds each slide is on screen, total). Slide i+1 starts `xfade` before slide i ends (the cross-fade);
    a long carousel shortens every slide so the reel stays under MAX_SECONDS."""
    if n * seconds - (n - 1) * xfade > MAX_SECONDS:
        seconds = (MAX_SECONDS + (n - 1) * xfade) / n
    starts = [i * (seconds - xfade) for i in range(n)]
    return starts, seconds, n * seconds - (n - 1) * xfade


def _frames(slides: List[_Slide], starts: List[float], seconds: float, total: float) -> Iterator[bytes]:
    for k in range(int(round(total * FPS))):
        t = k / FPS
        i = max(j for j in range(len(slides)) if starts[j] <= t)
        img = slides[i].frame(clamp01((t - starts[i]) / seconds))
        if i > 0 and t < starts[i] + XFADE:  # still fading in over the previous slide
            prev = slides[i - 1].frame(clamp01((t - starts[i - 1]) / seconds))
            img = Image.blend(prev, img, ease_in_out_cubic((t - starts[i]) / XFADE))
        yield img.tobytes()


def make_slides_reel(slides: Sequence, out_path, music=None, timeout: float = 900.0) -> Path:
    """Render the slides (image paths, in order) to an MP4 at `out_path`, and its cover (the first slide, as shown) next to it."""
    paths = list(slides)[:MAX_SLIDES]
    if len(paths) < 2:
        raise ReelError("a slides reel needs at least two slides")
    prepared = [_Slide(_open(p)) for p in paths]
    starts, seconds, total = timeline(len(prepared))
    out = encode(_frames(prepared, starts, seconds, total), total, out_path, music=music, timeout=timeout)
    prepared[0].frame(0.0).save(cover_path(out), "JPEG", quality=86, optimize=True, progressive=True)
    return out
