"""A reel from a partner's own video (a builder or agent walkthrough), not from photos. Made by 'Start marketing' when the
listing has a video (propertyfacts.jobs).

The clip is fitted to 1080x1920 at 30 fps and its own sound is kept. A contact strip burned in along the bottom (a phone number
shown for the whole video, as builder videos usually have) is found and removed: the frame is cropped just above it and zoomed
back to full size. The agent's logo with 'Powered by Avasetu' sits small at the bottom on a dark glass pill; the clip is cut to `max_seconds`
(`trim_end` drops a closing card) and an end card with the agent's brand follows. The tracked interest link is in the caption
(the calendar adds each post's own link when it publishes), so every lead from the reel is counted.

Blocking (ffmpeg); call from a worker thread. Text on our cards is Latin only (the bundled fonts have no Devanagari)."""
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from app.core import brand
from app.modules.marketing.images import GOLD, STORY, _logo, brand_background, latin, load_font

from . import ffmpeg

W, H = STORY
FPS = 30
MAX_SECONDS = 90.0      # Reels allow longer; past 90 s watch-through drops and Facebook shows it as a plain video
END_SECONDS = 3.0
MAX_TEXT_GAP = 90       # rows of light text inside a dark strip
MAX_ZOOM = 1.3          # removing a strip that needs more zoom than this would cut too much of the picture: it is left as it is
STRIP_MARGIN = 6        # rows above the strip that are cropped too (anti-aliased edge)
BADGE_BOTTOM = 150      # the badge's bottom edge, px from the frame bottom (clear of the Reels caption area's lowest line)


class VideoReelError(Exception):
    pass


# ---- the burned-in bottom strip ------------------------------------------------------------------------------------------
def _dark_rows(img: Image.Image, top: int) -> set:
    g = img.convert("L").resize((108, img.height))   # 108 columns are enough to tell a solid band from a scene
    px = g.load()
    return {y for y in range(top, g.height) if sum(px[x, y] for x in range(108)) / 108 < 40}


def find_bottom_bar(frames) -> Optional[Tuple[int, int]]:
    """(y0, y1) of a solid dark band in the lower quarter that is in every sampled frame (a burned-in contact strip), or None.
    Bands under 40 px are ignored (letterbox lines, shadows)."""
    common = None
    for f in frames:
        rows = _dark_rows(f, int(f.height * 0.75))
        common = rows if common is None else common & rows
    if not common:
        return None
    ys = sorted(common)
    best, start = (0, -1), ys[0]
    for a, b in zip(ys, ys[1:] + [None]):
        if b is None or b - a > MAX_TEXT_GAP:   # end of a band (the strip's own letters break it for up to MAX_TEXT_GAP rows)
            if a - start > best[1] - best[0]:
                best = (start, a)
            start = b
    return best if best[1] - best[0] >= 40 else None


def _fit(w: int, h: int) -> str:
    """Scale into WxH keeping the aspect and pad (portrait phone videos need no padding)."""
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x0c0e14,"
            f"setsar=1,fps={FPS}")


def strip_crop(bar: Optional[Tuple[int, int]]) -> str:
    """The filter that removes the strip: keep the rows above it, crop the sides to stay 9:16, zoom back to WxH. '' if none."""
    if not bar:
        return ""
    keep_h = bar[0] - STRIP_MARGIN
    if keep_h <= 0 or H / keep_h > MAX_ZOOM:
        return ""
    keep_w = int(W * keep_h / H) // 2 * 2
    return f",crop={keep_w}:{keep_h}:{(W - keep_w) // 2}:0,scale={W}:{H}:flags=lanczos,setsar=1"


def _sample_frames(src: Path, duration: float, work: Path) -> list:
    out = []
    for i, t in enumerate((duration * 0.15, duration * 0.5, duration * 0.85)):
        p = work / f"probe{i}.png"
        ffmpeg.run(["-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-vf", _fit(W, H), str(p), "-y"])
        out.append(Image.open(p).convert("RGB"))
    return out


# ---- our overlays --------------------------------------------------------------------------------------------------------
def _fit_font(d: ImageDraw.ImageDraw, text: str, size: int, weight: str, max_w: int):
    font = load_font(size, weight)
    while d.textlength(text, font=font) > max_w and size > 20:
        size -= 2
        font = load_font(size, weight)
    return font, size


def _center(d: ImageDraw.ImageDraw, text: str, y: int, size: int, fill, weight: str = "semibold") -> int:
    font, size = _fit_font(d, text, size, weight, W - 80)
    d.text(((W - d.textlength(text, font=font)) / 2, y), text, font=font, fill=fill)
    return y + int(size * 1.3)


def _agent_logo(path: Optional[str], height: int) -> Optional[Image.Image]:
    if not path:
        return None
    try:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            return im.resize((max(1, int(im.width * height / im.height)), height), Image.LANCZOS)
    except Exception:
        return None


def badge(agent_name: str, agent_logo: Optional[str]) -> Image.Image:
    """A full-frame RGBA overlay: a small dark glass pill at the bottom (the hook box's language: near-black, gold hairline)
    with the agent's logo on a white chip and 'Powered by Avasetu'. A white pill sat badly on the black letterbox bars of a
    fitted video and blew out on bright frames; the dark one reads on both, and the chip keeps a dark agent logo visible."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    from .compose import _tag_item   # the same brand tag, in the same place, as every other reel (owner, 2026-10-14)
    tag = _tag_item()
    img.alpha_composite(tag.img, (tag.x, tag.y))
    d = ImageDraw.Draw(img)
    logo = _agent_logo(agent_logo, 56)
    name = latin(agent_name)[:40]
    name_font = load_font(32, "semibold")
    small = load_font(22, "medium")
    if not logo and not name:   # our own reel: the brand tag above says it; a partner's keeps its pill below
        return img
    powered = f"Powered by {brand.NAME}"
    top_w = (logo.width + 14 if logo else 0) + (16 if logo and name else 0) + (int(d.textlength(name, font=name_font)) if name else 0)
    inner_w = max(top_w, int(d.textlength(powered, font=small)))
    if inner_w == 0:
        return img
    chip_h = 70 if logo else 44          # the logo with its white chip's padding, else just the name's line
    pw, ph = inner_w + 52, 12 + chip_h + 14 + 30 + 24
    x0, y0 = (W - pw) // 2, H - BADGE_BOTTOM - ph
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=24, fill=(14, 16, 24, 235))
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=24, outline=(255, 255, 255, 36), width=2)
    d.rectangle([x0 + 26, y0 + ph - 10, x0 + pw - 26, y0 + ph - 7], fill=GOLD + (255,))
    x, y = (W - top_w) // 2, y0 + 12
    if logo:
        d.rounded_rectangle([x - 7, y, x + logo.width + 7, y + chip_h], radius=16, fill=(255, 255, 255, 242))
        img.alpha_composite(logo, (x, y + 7))
        x += logo.width + 14 + 16
    if name:
        d.text((x, y + (chip_h - 40) // 2 if logo else y + 2), name, font=name_font, fill=(255, 255, 255, 255))
    d.text(((W - d.textlength(powered, font=small)) / 2, y0 + 12 + chip_h + 14), powered, font=small, fill=(214, 219, 230, 255))
    return img


HOOK_SECONDS = 3.0
HOOK_Y = 380            # top of the hook box: under the brand tag row (compose.CONTENT_TOP), above the presenter


def _hook_font(size: int, devanagari: bool):
    if devanagari:
        from app.modules.creative.layouts.base import DEVANAGARI_FONTS, FONT_DIR
        from PIL import ImageFont
        try:
            return ImageFont.truetype(str(FONT_DIR / DEVANAGARI_FONTS["bold"]), size)
        except OSError:
            pass
    return load_font(size, "bold")


def hook_image(text: str) -> Image.Image:
    """A full-frame RGBA overlay: the hook in up to two lines on a dark rounded box near the top (Marathi/Hindi in Mukta)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    text = (text or "").strip()
    if not text:
        return img
    deva = bool(re.search(r"[ऀ-ॿ]", text))
    d = ImageDraw.Draw(img)
    size, max_w = 76, W - 160
    while True:
        font = _hook_font(size, deva)
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = f"{cur} {w}".strip()
            if d.textlength(t, font=font) <= max_w or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        if (len(lines) <= 2 and all(d.textlength(l, font=font) <= max_w for l in lines)) or size <= 40:
            break
        size -= 4
    lh = int(size * (1.45 if deva else 1.25))
    bw = int(max(d.textlength(l, font=font) for l in lines)) + 80
    bh = lh * len(lines) + 50
    x0 = (W - bw) // 2
    d.rounded_rectangle([x0, HOOK_Y, x0 + bw, HOOK_Y + bh], radius=30, fill=(12, 14, 20, 215))
    d.rectangle([x0 + 30, HOOK_Y + bh - 10, x0 + bw - 30, HOOK_Y + bh - 6], fill=GOLD + (255,))
    for i, l in enumerate(lines):
        d.text(((W - d.textlength(l, font=font)) / 2, HOOK_Y + 22 + i * lh), l, font=font, fill=(255, 255, 255, 255))
    return img


def end_card(title: str, agent_name: str, agent_logo: Optional[str], seed: str = "video-end") -> Image.Image:
    img = brand_background(STORY, seed, floor=0.86, tall=0.30).convert("RGBA")
    d = ImageDraw.Draw(img)
    logo = _agent_logo(agent_logo, 200)
    y = 460
    if logo:
        img.alpha_composite(logo, ((W - logo.width) // 2, y))
        y += logo.height + 50
    if agent_name:
        y = _center(d, latin(agent_name), y, 64, (255, 255, 255), "bold") + 30
    y = _center(d, latin(title), y, 52, GOLD, "semibold") + 50
    y = _center(d, "Site visit, prices and details:", y, 40, (230, 230, 230), "medium")
    y = _center(d, "tap the link in the caption", y + 6, 40, (230, 230, 230), "medium")
    mark = _logo(84)
    powered = f"Powered by {brand.NAME}"
    font = load_font(30, "medium")
    tw = int(d.textlength(powered, font=font)) + (84 + 16 if mark else 0)
    x = (W - tw) // 2
    if mark:
        img.alpha_composite(mark, (x, H - 360))
        x += 84 + 16
    d.text((x, H - 360 + 22), powered, font=font, fill=(230, 230, 230))
    return img.convert("RGB")


# ---- render ----------------------------------------------------------------------------------------------------------------
def render(src, out_path, *, title: str, agent_name: str = "", agent_logo: Optional[str] = None,
           max_seconds: float = MAX_SECONDS, trim_end: float = 0.0, remove_strip: bool = True,
           segments: Optional[Sequence[Tuple[float, float]]] = None, hook: str = "") -> Dict:
    """Write the reel to `out_path`. `segments` (source seconds, in play order; video_director.plan) cut the clip, else the
    whole clip up to `max_seconds` minus `trim_end`; `hook` is shown for the first HOOK_SECONDS.
    Returns {"seconds", "removed_strip": (y0, y1) | None, "source_seconds"}."""
    src, out_path = Path(src), Path(out_path)
    p = ffmpeg.probe(src)
    if not p.duration or not p.width:
        raise VideoReelError("This file does not look like a video we can read")
    if not segments:
        segments = [(0.0, max(1.0, min(p.duration - max(0.0, trim_end), max_seconds - END_SECONDS)))]
    segments = [(max(0.0, a), min(p.duration, b)) for a, b in segments if min(p.duration, b) - max(0.0, a) > 0.2]
    body = sum(b - a for a, b in segments)
    work = Path(tempfile.mkdtemp(prefix="video-reel-"))
    try:
        bar = find_bottom_bar(_sample_frames(src, p.duration, work)) if remove_strip else None
        crop = strip_crop(bar)
        overlay = work / "badge.png"
        badge(agent_name, agent_logo).save(overlay)
        hook_png = work / "hook.png"
        hook_image(hook).save(hook_png)
        card = work / "end.png"
        end_card(title, agent_name, agent_logo).save(card)

        main = work / "main.mp4"
        cuts = []
        for i, (a, b) in enumerate(segments):
            cuts.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}]")
            if p.has_audio:
                cuts.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.05,"
                            f"afade=t=out:st={max(0.0, b - a - 0.08):.3f}:d=0.08[a{i}]")
        n = len(segments)
        joined = "".join(f"[v{i}][a{i}]" if p.has_audio else f"[v{i}]" for i in range(n))
        cuts.append(f"{joined}concat=n={n}:v=1:a={1 if p.has_audio else 0}" + ("[cv][ca]" if p.has_audio else "[cv]"))
        graph = ";".join(cuts) + (f";[cv]{_fit(W, H)}{crop}[v];[v][1:v]overlay=0:0[vb];"
                                  f"[vb][2:v]overlay=0:0:enable='lt(t,{HOOK_SECONDS})',format=yuv420p,"
                                  f"fade=t=out:st={max(0.0, body - 0.4):.2f}:d=0.4[out]")
        audio = ["-map", "[ca]", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"] if p.has_audio else ["-an"]
        ffmpeg.run(["-i", str(src), "-i", str(overlay), "-i", str(hook_png), "-filter_complex", graph,
                    "-map", "[out]", *audio, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
                    "-movflags", "+faststart", str(main), "-y"])

        tail = work / "end.mp4"
        silent = ["-f", "lavfi", "-t", f"{END_SECONDS:.2f}", "-i", "anullsrc=r=48000:cl=stereo"] if p.has_audio else []
        ffmpeg.run(["-loop", "1", "-t", f"{END_SECONDS:.2f}", "-i", str(card), *silent,
                    "-vf", f"fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.3", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", *(["-c:a", "aac", "-b:a", "160k", "-shortest"] if p.has_audio else ["-an"]),
                    str(tail), "-y"])

        streams = "".join(f"[{i}:v][{i}:a]" if p.has_audio else f"[{i}:v]" for i in range(2))
        concat = f"{streams}concat=n=2:v=1:a={1 if p.has_audio else 0}" + ("[v][a]" if p.has_audio else "[v]")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg.run(["-i", str(main), "-i", str(tail), "-filter_complex", concat, "-map", "[v]",
                    *(["-map", "[a]", "-c:a", "aac", "-b:a", "160k"] if p.has_audio else []),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", str(out_path), "-y"])
        return {"seconds": round(body + END_SECONDS, 2), "removed_strip": bar if crop else None,
                "source_seconds": round(p.duration, 2)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


VOICE_START_S = 0.6     # the first spoken line, just after the hook card comes up
VOICE_MIN_GAP_S = 0.35  # between two spoken lines, at the least


def voice_starts(durations: Sequence[float], total: float) -> List[float]:
    """Where each spoken line starts: spread evenly over the clip before its end card, never overlapping, and only the lines
    that fit (a long script over a short clip loses its last lines rather than talking over the end card)."""
    room = max(0.0, total - END_SECONDS - VOICE_START_S)
    slot = room / max(1, len(durations))
    out: List[float] = []
    t = VOICE_START_S
    for d in durations:
        if t + d > total - END_SECONDS + 1.0:   # the end card is 3 s: a line may run a second into it
            break
        out.append(t)
        t = max(t + d + VOICE_MIN_GAP_S, VOICE_START_S + slot * len(out))
    return out


def voice_over(path, lines: Sequence[str], lang: str = "en", gender: str = "female", mood: str = "warm") -> str:
    """Put a voice-over (the lines with their pause tags, voice.synth_spoken, spread over the clip, over our music bed which
    steps back under it) on a finished video reel in place of its sound: for a video nobody speaks in. "spoken", or "off"
    when no line fits. Raises voice.VoiceError / ffmpeg.FfmpegError on failure, the reel at `path` untouched."""
    from . import narration
    from .music import write as write_music

    path = Path(path)
    total = ffmpeg.probe(path).duration or 0.0
    work = Path(tempfile.mkdtemp(prefix="video-voice-"))
    try:
        clips, how = narration.spoken_lines([x for x in lines if x.strip()], lang, gender, work), "spoken"
        starts = voice_starts([ffmpeg.probe(c).duration for c in clips], total)
        if not starts:
            return "off"
        audio = narration.mix(work, clips[:len(starts)], starts, total, write_music(work / "bed.wav", seconds=total + 1.0, mood=mood))
        voiced = work / "voiced.mp4"
        ffmpeg.run(["-i", str(path), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(voiced), "-y"])
        shutil.move(str(voiced), str(path))
        return how
    finally:
        shutil.rmtree(work, ignore_errors=True)
