"""A reel made from a post's finished slides (a carousel already designed at 1080x1350), over the Avasetu signature music.

Used where a carousel cannot be swiped: Facebook shows a multi-photo Page post as a grid, so the Facebook copy of a carousel goes
out as one Reel that plays the slides in order.

The opening decides everything: on the first such reel (the agent promo, 2026-10-04) 62% of plays were gone within one second
and almost all by second four, because frame one was a small, text-heavy poster on a blurred background that faded slowly into
the next. So:
- frame one is a hook card: the post's hook line in big type on the brand background (compose's hook scene, readable at once,
  no fade-in), for HOOK_SECONDS, in place of the carousel's cover slide (which says the same thing); without a hook line, the
  first slide starts zoomed in and settles, so something moves at once;
- then the slides, each whole inside the Reels safe area over a blurred copy of itself, on a quick punch-in cut every
  SECONDS_PER_SLIDE (no slow cross-fades), with a gentle zoom while on screen.
The slides carry their own text and brand, so nothing is drawn on top of them.
"""
from pathlib import Path
from typing import Iterator, List, Optional, Sequence

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from .compose import (FPS, H, MAX_SECONDS, W, ReelError, Renderer, Scene, TextLine, clamp01, cover_path, ease_out_cubic, encode,
                      write_cover)

SLIDE_W = 940                   # 1080x1350 slide -> 940x1175
SLIDE_TOP = 250                 # ends at 1425, above the caption/account row (Instagram and Facebook cover roughly the last 20%)
SECONDS_PER_SLIDE = 2.4
HOOK_SECONDS = 1.6
PUNCH = 0.22                    # each slide arrives zoomed 7% in and settles in this many seconds (a cut with energy, not a fade)
PUNCH_SCALE = 0.07
ZOOM = 0.03                     # then it grows by 3% while it is on screen
MAX_SLIDES = 8
HOOK_MAX = 90                   # characters: a longer line is cut at a word (compose shrinks the type to fit 4 lines)


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

    def frame(self, lt: float, seconds: float) -> Image.Image:
        """The slide `lt` seconds after its cut: a short punch-in that settles, then a slow zoom."""
        z = 1.0 + PUNCH_SCALE * (1 - ease_out_cubic(lt / PUNCH)) + ZOOM * clamp01(lt / seconds)
        fw, fh = round(self.fg.width * z), round(self.fg.height * z)
        fg = self.fg.resize((fw, fh), Image.BILINEAR) if (fw, fh) != self.fg.size else self.fg
        img = self.bg.copy()
        cx, cy = W // 2, SLIDE_TOP + self.fg.height // 2
        img.paste(fg, (cx - fw // 2, cy - fh // 2))
        return img


def clean_hook(text: Optional[str]) -> Optional[str]:
    """The first line of a caption or a hook field, without emoji, hashtags or links; None when nothing usable is left."""
    if not text:
        return None
    line = next((l for l in str(text).splitlines() if l.strip()), "")
    words = [w for w in line.split() if not w.startswith(("#", "http")) and any(ch.isalnum() for ch in w)]
    out = " ".join("".join(ch for ch in w if ch.isascii() or ch in "₹–—'’") for w in words).strip(" -–—:")
    if len(out) < 8:
        return None
    return out if len(out) <= HOOK_MAX else out[:HOOK_MAX].rsplit(" ", 1)[0] + "…"


def timeline(n: int, seconds: float = SECONDS_PER_SLIDE, hook: bool = False):
    """(start of each slide, seconds each slide is on screen, total). Cuts, no overlap; a long carousel shortens every slide so the
    reel stays under MAX_SECONDS."""
    lead = HOOK_SECONDS if hook else 0.0
    if lead + n * seconds > MAX_SECONDS:
        seconds = (MAX_SECONDS - lead) / n
    return [lead + i * seconds for i in range(n)], seconds, lead + n * seconds


def _frames(slides: List[_Slide], starts: List[float], seconds: float, total: float, opener: Optional[Renderer]) -> Iterator[bytes]:
    for k in range(int(round(total * FPS))):
        t = k / FPS
        if opener is not None and t < starts[0]:
            yield opener.frame_at(t).tobytes()
            continue
        i = max(j for j in range(len(slides)) if starts[j] <= t + 1e-9)
        yield slides[i].frame(t - starts[i], seconds).tobytes()


def make_slides_reel(slides: Sequence, out_path, music=None, hook: Optional[str] = None, kicker: Optional[str] = None,
                     timeout: float = 900.0) -> Path:
    """Render the slides (image paths, in order) to an MP4 at `out_path`, opening on `hook` (big type) when given, and write its
    cover (the hook card, or the first slide) next to it."""
    paths = list(slides)[:MAX_SLIDES]
    if len(paths) < 2:
        raise ReelError("a slides reel needs at least two slides")
    hook = clean_hook(hook)
    if hook and len(paths) > 2:
        paths = paths[1:]  # the carousel's first slide is its cover, the same hook again: the hook card replaces it
    prepared = [_Slide(_open(p)) for p in paths]
    opener = None
    if hook:
        # the hook scene runs a little past HOOK_SECONDS so no cross-fade starts while it shows; the empty scene after it is never
        # shown and only takes the brand mark compose puts on a reel's last scene (frame one must read as content, not as an ad)
        opener = Renderer([Scene(lines=[TextLine(hook, size=124, max_lines=4)], kicker=kicker, seconds=HOOK_SECONDS + 0.5,
                                 seed="slides-hook"), Scene(seconds=1.0, seed="slides-hook-end")], progress=False)
    starts, seconds, total = timeline(len(prepared), hook=bool(hook))
    out = encode(_frames(prepared, starts, seconds, total, opener), total, out_path, music=music, timeout=timeout)
    if opener is not None:
        write_cover(opener, out)
    else:
        prepared[0].frame(PUNCH, seconds).save(cover_path(out), "JPEG", quality=86, optimize=True, progressive=True)
    return out
