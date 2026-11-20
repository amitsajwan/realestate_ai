"""A project's site from above as a moving picture: one clear Sentinel-2 picture a dry month, cross-faded, the date ticking
beside it, and the measured sentence at the end (docs/plan/satellite-view.md, "timelapse"). Two shapes from the same key
frames: a landscape loop for the project page (text left, ground right) and a 9:16 reel (text above, ground below).

Everything on screen is code-written: the project's name, the month of each pass, and the sentence `areastats.sitepics.story`
wrote from the yearly measure. No model writes or draws anything here; the pictures are the satellite's, enhanced by
`areastats.pictures.enhance`, which adds no detail.

The pictures come in by `backend/scripts/project_from_above.py`, which fetches them and calls `page_video` and `reel_video`.
"""
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterator, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from app.core import brand
from app.modules.marketing.images import latin, load_font
from app.modules.reels import compose as _compose
from app.modules.reels import ffmpeg

log = logging.getLogger(__name__)

NAVY = (16, 35, 64)
GOLD = (240, 177, 59)
WHITE = (255, 255, 255)
SOFT = (196, 205, 222)
DIM = (140, 152, 176)
RING = (255, 210, 0)

PAGE = (960, 540)
PAGE_FPS = 24
REEL = (_compose.W, _compose.H)
REEL_FPS = _compose.FPS
REEL_TEXT_TOP, REEL_TEXT_BOTTOM, REEL_TEXT_RIGHT = 0.14, 0.72, 0.88   # Instagram's safe zone (reels.compose)

FIRST_HOLD = 1.2      # seconds on the first month, so the eye finds the ring before the ground starts to change
FADE = 0.22           # cross-fade between two months
PER_MIN, PER_MAX = 0.3, 0.75
END_FADE = 0.6
END_HOLD = 3.5        # the measured sentence, long enough to read
REEL_SECONDS = 27.0   # under the reels' 29 s


@dataclass(frozen=True)
class Shot:
    day: str              # YYYY-MM-DD, the pass
    picture: Image.Image  # square, enhanced, the pin at its centre


def month_label(day: str) -> str:
    return date.fromisoformat(day).strftime("%b %Y")


def per_frame(n: int, seconds: float) -> float:
    """Seconds each month stays on screen so that `n` months, the first hold and the ending fit in `seconds`."""
    if n < 2:
        return PER_MAX
    room = seconds - FIRST_HOLD - END_FADE - END_HOLD
    return max(PER_MIN, min(PER_MAX, room / (n - 1)))


def schedule(n: int, per: float) -> List[Tuple[str, int, float]]:
    """The play order as (what, key, seconds): "hold" a key frame, or "fade" into it from the one before. Key n is the end
    card (the last month with the sentence)."""
    out = [("hold", 0, FIRST_HOLD)]
    for i in range(1, n):
        out += [("fade", i, FADE), ("hold", i, max(0.0, per - FADE))]
    out += [("fade", n, END_FADE), ("hold", n, END_HOLD)]
    return out


def seconds_of(plan: Sequence[Tuple[str, int, float]], fps: int) -> float:
    """The length `play` gives: each step is rounded to whole frames, and the encoder must expect exactly that many."""
    return sum(round(s * fps) for _, _, s in plan) / fps


def play(keys: Sequence[Image.Image], plan: Sequence[Tuple[str, int, float]], fps: int) -> Iterator[bytes]:
    """Raw RGB frames of the plan: a hold repeats one key frame, a fade blends the previous key into the next."""
    raw = [k.convert("RGB").tobytes() for k in keys]
    for what, i, secs in plan:
        n = round(secs * fps)
        if what == "hold":
            for _ in range(n):
                yield raw[i]
        else:
            a, b = keys[i - 1].convert("RGB"), keys[i].convert("RGB")
            for f in range(n):
                yield Image.blend(a, b, (f + 1) / n).tobytes()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int, max_lines: int) -> List[str]:
    lines: List[str] = []
    for word in latin(text).split():
        if lines and draw.textlength(f"{lines[-1]} {word}", font=font) <= width:
            lines[-1] = f"{lines[-1]} {word}"
        else:
            lines.append(word)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    return lines


def _ring(pic: Image.Image) -> Image.Image:
    out = pic.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    cx, cy, r = out.width // 2, out.height // 2, max(10, out.width // 34)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RING, width=max(2, out.width // 180))
    return out


def _timeline(d: ImageDraw.ImageDraw, x0: int, x1: int, y: int, days: Sequence[str], at: int, size: int) -> None:
    """A thin line from the first pass to the last, a tick at each new year and a gold dot at this month."""
    first, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
    span = max(1, (last - first).days)
    pos = lambda day: x0 + (x1 - x0) * (date.fromisoformat(day) - first).days / span   # noqa: E731
    d.line((x0, y, x1, y), fill=DIM, width=max(2, size // 8))
    font = load_font(size, "regular")
    for year in range(first.year + 1, last.year + 1):
        x = pos(f"{year}-01-01")
        d.line((x, y - size // 3, x, y + size // 3), fill=DIM, width=max(1, size // 10))
        d.text((x, y + size // 2), str(year), font=font, fill=DIM, anchor="mt")
    x = pos(days[at])
    r = max(5, size // 2)
    d.line((x0, y, x, y), fill=GOLD, width=max(2, size // 8))
    d.ellipse((x - r, y - r, x + r, y + r), fill=GOLD)


def page_keys(name: str, place: str, shots: Sequence[Shot], story: str, credit: str) -> List[Image.Image]:
    """The landscape key frames: text on a navy panel at the left, the ground on the right."""
    w, h = PAGE
    side = h
    panel = w - side
    pad = 32
    days = [s.day for s in shots]
    pics = [_ring(s.picture).resize((side, side), Image.LANCZOS) for s in shots]
    label, title, sub = load_font(15, "semibold"), load_font(28, "bold"), load_font(17, "regular")
    big, body, small = load_font(54, "bold"), load_font(17, "regular"), load_font(12, "regular")

    def base(i: int) -> Tuple[Image.Image, ImageDraw.ImageDraw, int]:
        img = Image.new("RGB", PAGE, NAVY)
        img.paste(pics[i], (panel, 0))
        d = ImageDraw.Draw(img)
        d.text((pad, pad), "FROM ABOVE", font=label, fill=GOLD)
        y = pad + 30
        for line in _wrap(d, name, title, panel - 2 * pad, 2):
            d.text((pad, y), line, font=title, fill=WHITE)
            y += 36
        d.text((pad, y + 4), latin(place), font=sub, fill=SOFT)
        d.text((pad, h - pad - 34), latin(credit), font=small, fill=DIM)
        d.text((pad, h - pad - 14), brand.SITE.replace("https://", ""), font=small, fill=GOLD)
        return img, d, y + 40

    keys = []
    for i in range(len(shots)):
        img, d, y = base(i)
        d.text((pad, y + 40), month_label(days[i]), font=big, fill=WHITE)
        _timeline(d, pad + 6, panel - pad - 6, y + 140, days, i, 13)
        d.text((pad, y + 190), "One clear satellite pass a month,", font=body, fill=SOFT)
        d.text((pad, y + 214), "October to May. Nothing drawn in.", font=body, fill=SOFT)
        keys.append(img)
    img, d, y = base(len(shots) - 1)
    yy = y + 24
    for line in _wrap(d, story, body, panel - 2 * pad, 9):
        d.text((pad, yy), line, font=body, fill=WHITE)
        yy += 25
    keys.append(img)
    return keys


def reel_keys(name: str, place: str, shots: Sequence[Shot], story: str, credit: str) -> List[Image.Image]:
    """The 9:16 key frames: text above in the safe zone, the ground below it."""
    w, h = REEL
    x0, top, right = 72, int(h * REEL_TEXT_TOP), int(w * REEL_TEXT_RIGHT)
    pic_side, pic_y = 1000, 740
    days = [s.day for s in shots]
    pics = [_ring(s.picture).resize((pic_side, pic_side), Image.LANCZOS) for s in shots]
    label, title, sub = load_font(34, "semibold"), load_font(60, "bold"), load_font(36, "regular")
    big, body, small = load_font(104, "bold"), load_font(40, "medium"), load_font(26, "regular")

    def base(i: int) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGB", REEL, NAVY)
        img.paste(pics[i], ((w - pic_side) // 2, pic_y))
        d = ImageDraw.Draw(img)
        d.text((x0, top), "FROM ABOVE", font=label, fill=GOLD)
        d.text((x0, pic_y - 46), latin(credit), font=small, fill=DIM)
        return img, d

    keys = []
    for i in range(len(shots)):
        img, d = base(i)
        y = top + 52
        for line in _wrap(d, name, title, right - x0, 2):
            d.text((x0, y), line, font=title, fill=WHITE)
            y += 72
        d.text((x0, y + 4), latin(place), font=sub, fill=SOFT)
        d.text((x0, y + 64), month_label(days[i]), font=big, fill=WHITE)
        _timeline(d, x0 + 8, right - 8, pic_y - 112, days, i, 24)
        keys.append(img)
    img, d = base(len(shots) - 1)
    y = top + 60
    for line in _wrap(d, story, body, right - x0, 7):
        d.text((x0, y), line, font=body, fill=WHITE)
        y += 54
    keys.append(img)
    return keys


def page_video(name: str, place: str, shots: Sequence[Shot], story: str, credit: str, out: Path,
               seconds: float = 22.0) -> Tuple[Path, Path]:
    """The landscape loop for the project page (silent H.264, small) and its poster (the last month), side by side."""
    if len(shots) < 3:
        raise ValueError("a timelapse needs at least three months")
    keys = page_keys(name, place, shots, story, credit)
    plan = schedule(len(shots), per_frame(len(shots), seconds))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = PAGE
    ffmpeg.run_with_frames(["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(PAGE_FPS), "-i", "-",
                            "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p",
                            "-g", str(PAGE_FPS * 2), "-movflags", "+faststart", str(out)],
                           play(keys, plan, PAGE_FPS))
    poster = out.with_suffix(".webp")
    keys[len(shots) - 1].save(poster, "WEBP", quality=82, method=6)
    return out, poster


def reel_video(name: str, place: str, shots: Sequence[Shot], story: str, credit: str, out: Path,
               music: Optional[Path] = None) -> Path:
    """The 9:16 reel (reels.compose.encode: H.264 1080x1920 with the brand music) and its cover, the last month."""
    if len(shots) < 3:
        raise ValueError("a timelapse needs at least three months")
    keys = reel_keys(name, place, shots, story, credit)
    plan = schedule(len(shots), per_frame(len(shots), REEL_SECONDS))
    path = _compose.encode(play(keys, plan, REEL_FPS), seconds_of(plan, REEL_FPS), out, music=music)
    keys[len(shots) - 1].save(_compose.cover_path(path), "JPEG", quality=86, optimize=True, progressive=True)
    return path


def caption(name: str, place: str, first_day: str, last_day: str, story: str, url: str) -> str:
    """The post's words, all from the record: what it shows, the measured sentence, what the pictures are, the page."""
    return (f"{latin(name)}, {latin(place)}, from above: one clear satellite pass a month, {month_label(first_day)} to "
            f"{month_label(last_day)}.\n\n{story}\n\nSentinel-2 pictures at 10 m, sharpened by code; nothing is drawn in. "
            f"The circle takes in neighbouring plots.\n\nThe project's MahaRERA facts: {url}\n\n{brand.HASHTAG} #Pune")
