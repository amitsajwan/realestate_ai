"""A project's site from above as a moving picture: one clear Sentinel-2 picture a dry season, cross-faded slowly, the date
and a line about that picture written large across its top, and the measured sentence at the end
(docs/plan/satellite-view.md, "timelapse"). Two shapes from the same pictures: a square video for the project page and a
9:16 reel.

Owner 2026-11-20 on the first version (41 months at half a second, text in a side panel): "too fast and repetition", "is
text readable", "with every image change we need interpretation". So: about 17 pictures (a season each) held about 1.5 s,
text big enough to read on a phone, and each picture's line from `areastats.sitepics.captions`.

Owner 2026-11-20: the video should end on the site as it is now, and that is its thumbnail. So the page video's last frame is
the newest pass alone, "Now" and its month over it and nothing else, held after the sentence, and the poster is that frame.
(The sharper "now" is Google's satellite, which may only be shown through its embed: the page shows it beside the video.)

Everything on screen is code-written: the project's name, each pass's month, the line the yearly measure gives that day,
and the sentence `sitepics.story` wrote. No model writes or draws anything here: at 10 m a pixel a model looking at the
picture would guess. The pictures are the satellite's, made clearer by `areastats.pictures` (enhance, even_out), which add
no detail.

`areastats.fromabove` (the daily pass, through wiring) and `backend/scripts/project_from_above.py` call `page_video` and
`reel_video`.
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
SOFT = (210, 218, 232)
DIM = (150, 162, 186)
RING = (255, 210, 0)

PAGE = (720, 720)
PAGE_FPS = 24
PAGE_SECONDS = 37.0
REEL = (_compose.W, _compose.H)
REEL_FPS = _compose.FPS
REEL_TEXT_TOP, REEL_TEXT_RIGHT = 0.14, 0.88   # Instagram's safe zone (reels.compose)
REEL_SECONDS = 28.5                           # under the reels' 29 s

FIRST_HOLD = 1.8      # seconds on the first picture, so the eye finds the ring before the ground starts to change
FADE = 0.5            # the longest cross-fade; with a picture a month it is most of each step, so the ground flows
PER_MIN, PER_MAX = 0.45, 1.8
END_FADE = 0.8
END_HOLD = 4.5        # the measured sentence, long enough to read
NOW_FADE = 0.8
NOW_HOLD = 3.0        # the page video ends on the newest pass, as it is now


@dataclass(frozen=True)
class Shot:
    day: str              # YYYY-MM-DD, the pass
    picture: Image.Image  # square, enhanced, the pin at its centre
    say: str = ""         # the line for this picture (sitepics.captions)


def month_label(day: str) -> str:
    return date.fromisoformat(day).strftime("%b %Y")


def per_frame(n: int, seconds: float, now: bool = False) -> float:
    """Seconds each picture stays on screen so that `n` pictures, the first hold and the ending (with `now`, the newest pass
    after the sentence) fit in `seconds`."""
    if n < 2:
        return PER_MAX
    room = seconds - FIRST_HOLD - END_FADE - END_HOLD - ((NOW_FADE + NOW_HOLD) if now else 0.0)
    return max(PER_MIN, min(PER_MAX, room / (n - 1)))


def schedule(n: int, per: float, now: bool = False) -> List[Tuple[str, int, float]]:
    """The play order as (what, key, seconds): "hold" a key frame, or "fade" into it from the one before. Key n is the end
    card (the last picture with the sentence); with `now`, key n + 1 is the newest pass alone, the video's last frame."""
    out = [("hold", 0, FIRST_HOLD)]
    for i in range(1, n):
        fade = min(FADE, per * 0.75)
        out += [("fade", i, fade), ("hold", i, max(0.0, per - fade))]
    out += [("fade", n, END_FADE), ("hold", n, END_HOLD)]
    if now:
        out += [("fade", n + 1, NOW_FADE), ("hold", n + 1, NOW_HOLD)]
    return out


def seconds_of(plan: Sequence[Tuple[str, int, float]], fps: int) -> float:
    """The length `play` gives: each step is rounded to whole frames, and the encoder must expect exactly that many."""
    return sum(round(s * fps) for _, _, s in plan) / fps


Key = Tuple[Image.Image, Image.Image]   # (the ground, RGB) and (the words over it, RGBA, same size)


def flat(key: Key) -> Image.Image:
    """One key frame as it is seen: the words over the ground."""
    ground, words = key
    return Image.alpha_composite(ground.convert("RGBA"), words).convert("RGB")


def play(keys: Sequence[Key], plan: Sequence[Tuple[str, int, float]], fps: int) -> Iterator[bytes]:
    """Raw RGB frames of the plan: a hold repeats one key frame; a fade blends the ground of the previous key into the next
    and switches the words halfway, so two dates never sit on top of each other."""
    raw = [flat(k).tobytes() for k in keys]
    for what, i, secs in plan:
        n = round(secs * fps)
        if what == "hold":
            for _ in range(n):
                yield raw[i]
        else:
            (a, wa), (b, wb) = keys[i - 1], keys[i]
            a, b = a.convert("RGBA"), b.convert("RGBA")
            for f in range(n):
                t = (f + 1) / n
                yield Image.alpha_composite(Image.blend(a, b, t), wa if t < 0.5 else wb).convert("RGB").tobytes()


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


def _ring(pic: Image.Image, side: int) -> Image.Image:
    out = pic.convert("RGB").resize((side, side), Image.LANCZOS)
    d = ImageDraw.Draw(out)
    cx, cy, r = side // 2, side // 2, side // 6   # 100 m around the pin in 600 m: the ground the readings and words cover
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RING, width=max(3, side // 200))
    return out


def _layer(size: Tuple[int, int]) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    words = Image.new("RGBA", size, (0, 0, 0, 0))
    return words, ImageDraw.Draw(words)


def _shade(d: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], alpha: int) -> None:
    """A navy band under words laid over the picture, so white words read on any ground."""
    d.rectangle(box, fill=NAVY + (alpha,))


def _progress(d: ImageDraw.ImageDraw, x0: int, x1: int, y: int, days: Sequence[str], at: int, thick: int,
              labels=None) -> None:
    """A thin line from the first pass to the last, a tick at each new year and the part played so far in gold."""
    first, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
    span = max(1, (last - first).days)
    pos = lambda day: x0 + (x1 - x0) * (date.fromisoformat(day) - first).days / span   # noqa: E731
    d.line((x0, y, x1, y), fill=DIM, width=thick)
    for year in range(first.year + 1, last.year + 1):
        x = pos(f"{year}-01-01")
        d.line((x, y - thick * 2, x, y + thick * 2), fill=DIM, width=max(1, thick // 2))
        if labels is not None:
            d.text((x, y + thick * 3), str(year), font=labels, fill=SOFT, anchor="mt")
    x = pos(days[at])
    d.line((x0, y, x, y), fill=GOLD, width=thick)
    d.ellipse((x - thick * 2, y - thick * 2, x + thick * 2, y + thick * 2), fill=GOLD)


def page_keys(name: str, place: str, shots: Sequence[Shot], story: str, credit: str, ring: bool = True) -> List[Key]:
    """The square key frames: the picture full size, the date and its line large across the top, a progress line and the
    credit along the bottom; then the end card with the sentence; then the newest pass again with only "Now" and its month,
    the last frame and the poster. `ring` False for a whole area (areastats.areaspace): there is no pin to circle."""
    side = PAGE[0]
    pad = 26
    days = [s.day for s in shots]
    pics = [_ring(s.picture, side) if ring else s.picture.convert("RGB").resize((side, side), Image.LANCZOS) for s in shots]
    big, line, small = load_font(58, "bold"), load_font(32, "semibold"), load_font(16, "regular")
    title, body = load_font(36, "bold"), load_font(29, "medium")

    def foot(d: ImageDraw.ImageDraw, i: int) -> None:
        _shade(d, (0, side - 62, side, side), 190)
        _progress(d, pad, side - pad, side - 44, days, i, 4)
        d.text((pad, side - 26), latin(credit), font=small, fill=SOFT)
        d.text((side - pad, side - 26), brand.SITE.replace("https://", ""), font=small, fill=GOLD, anchor="ra")

    keys: List[Key] = []
    for i, s in enumerate(shots):
        words, d = _layer(PAGE)
        said = _wrap(d, s.say, line, side - 2 * pad, 2) if s.say else []
        _shade(d, (0, 0, side, 100 + 40 * len(said)), 170)
        d.text((pad, 18), month_label(s.day), font=big, fill=WHITE)
        for k, t in enumerate(said):
            d.text((pad, 92 + 38 * k), t, font=line, fill=GOLD)
        foot(d, i)
        keys.append((pics[i], words))
    end = Image.blend(pics[-1], Image.new("RGB", (side, side), NAVY), 0.72)
    words, d = _layer(PAGE)
    y = 40
    for t in _wrap(d, name, title, side - 2 * pad, 2):
        d.text((pad, y), t, font=title, fill=WHITE)
        y += 46
    d.text((pad, y + 2), latin(place) + ", from space", font=line, fill=GOLD)
    y += 70
    for t in _wrap(d, story, body, side - 2 * pad, 10):
        d.text((pad, y), t, font=body, fill=WHITE)
        y += 40
    foot(d, len(shots) - 1)
    keys.append((end, words))
    words, d = _layer(PAGE)
    _shade(d, (0, 0, side, 100), 170)
    d.text((pad, 18), "Now", font=big, fill=GOLD)
    d.text((pad + d.textlength("Now ", font=big), 18), month_label(shots[-1].day), font=big, fill=WHITE)
    foot(d, len(shots) - 1)
    keys.append((pics[-1], words))
    return keys


def reel_keys(name: str, place: str, shots: Sequence[Shot], story: str, credit: str) -> List[Key]:
    """The 9:16 key frames: name, date and the picture's line above in the safe zone, the ground below."""
    w, h = REEL
    x0, top, right = 72, int(h * REEL_TEXT_TOP), int(w * REEL_TEXT_RIGHT)
    pic_side, pic_y = 1000, 780
    days = [s.day for s in shots]
    label, title, sub = load_font(34, "semibold"), load_font(58, "bold"), load_font(36, "regular")
    big, line, body, small = load_font(100, "bold"), load_font(48, "semibold"), load_font(44, "medium"), load_font(26, "regular")
    years = load_font(24, "regular")

    def ground(pic: Image.Image) -> Image.Image:
        img = Image.new("RGB", REEL, NAVY)
        img.paste(_ring(pic, pic_side), ((w - pic_side) // 2, pic_y))
        return img

    def frame(i: int) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        words, d = _layer(REEL)
        d.text((x0, top), "FROM ABOVE", font=label, fill=GOLD)
        _progress(d, x0 + 8, right - 8, pic_y - 62, days, i, 6, labels=years)
        d.text((x0, pic_y + pic_side + 14), latin(credit), font=small, fill=DIM)
        return words, d

    keys: List[Key] = []
    for i, s in enumerate(shots):
        words, d = frame(i)
        y = top + 48
        for t in _wrap(d, name, title, right - x0, 1):
            d.text((x0, y), t, font=title, fill=WHITE)
        d.text((x0, y + 74), latin(place), font=sub, fill=SOFT)
        d.text((x0, y + 128), month_label(s.day), font=big, fill=WHITE)
        for k, t in enumerate(_wrap(d, s.say, line, right - x0, 2) if s.say else []):
            d.text((x0, y + 250 + 56 * k), t, font=line, fill=GOLD)
        keys.append((ground(s.picture), words))
    words, d = frame(len(shots) - 1)
    y = top + 52
    for t in _wrap(d, story, body, right - x0, 7):
        d.text((x0, y), t, font=body, fill=WHITE)
        y += 58
    keys.append((ground(shots[-1].picture), words))
    return keys


def page_video(name: str, place: str, shots: Sequence[Shot], story: str, credit: str, out: Path,
               seconds: float = PAGE_SECONDS, ring: bool = True) -> Tuple[Path, Path]:
    """The square video for the project page (silent H.264, small) and its poster (its last frame: the newest pass, "Now"),
    side by side."""
    if len(shots) < 3:
        raise ValueError("a timelapse needs at least three pictures")
    keys = page_keys(name, place, shots, story, credit, ring)
    plan = schedule(len(shots), per_frame(len(shots), seconds, now=True), now=True)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = PAGE
    ffmpeg.run_with_frames(["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(PAGE_FPS), "-i", "-",
                            "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p",
                            "-g", str(PAGE_FPS * 2), "-movflags", "+faststart", str(out)],
                           play(keys, plan, PAGE_FPS))
    poster = out.with_suffix(".webp")
    flat(keys[-1]).save(poster, "WEBP", quality=82, method=6)
    return out, poster


def reel_video(name: str, place: str, shots: Sequence[Shot], story: str, credit: str, out: Path,
               music: Optional[Path] = None) -> Path:
    """The 9:16 reel (reels.compose.encode: H.264 1080x1920 with the brand music) and its cover, the last picture."""
    if len(shots) < 3:
        raise ValueError("a timelapse needs at least three pictures")
    keys = reel_keys(name, place, shots, story, credit)
    plan = schedule(len(shots), per_frame(len(shots), REEL_SECONDS))
    path = _compose.encode(play(keys, plan, REEL_FPS), seconds_of(plan, REEL_FPS), out, music=music)
    flat(keys[len(shots) - 1]).save(_compose.cover_path(path), "JPEG", quality=86, optimize=True, progressive=True)
    return path


def caption(name: str, place: str, first_day: str, last_day: str, story: str, url: str) -> str:
    """The post's words, all from the record: what it shows, the measured sentence, what the pictures are, the page."""
    return (f"{latin(name)}, {latin(place)}, from above: one clear satellite pass a season, {month_label(first_day)} to "
            f"{month_label(last_day)}.\n\n{story}\n\nSentinel-2 pictures at 10 m, sharpened by code; nothing is drawn in. "
            f"The circle takes in neighbouring plots.\n\nThe project's MahaRERA facts: {url}\n\n{brand.HASHTAG} #Pune")
