"""The AI editor for a partner's video: decides what the reel keeps and says, before video_reel renders it.

    1. listen - the speech, with timestamps (Groq Whisper, verbose_json segments)
    2. look   - one vision call on a timed contact sheet of frames: what each shot shows and how good it looks
    3. edit   - the LLM picks the best 25-45 s at sentence boundaries (no phone numbers, no dated offers), writes a short
                on-screen hook in the post's language and the caption

Every step is optional: without speech the edit works from the frames, without any AI the whole clip is used with no hook
(the plain reel). Code keeps the last word: segments are clipped to the video and to the length limits, anything that says a
phone number is cut, and the hook and caption must pass the same checks as every post (creative.guards)."""
import asyncio
import base64
import io
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw

from . import ffmpeg

log = logging.getLogger(__name__)

TARGET_MIN, TARGET_MAX = 25.0, 45.0
MIN_SEGMENT = 1.5
SHEET_TILES = 12            # frames on the contact sheet (4 x 3)
HOOK_MAX_WORDS = 8
STT_TIMEOUT = 60.0
VISION_TIMEOUT = 45.0
PHONE = re.compile(r"(?:\d[\s-]?){8,}")
LANG_NAME = {"en": "English", "mr": "Marathi (Devanagari script)", "hi": "Hindi (Devanagari script)"}


@dataclass
class EditPlan:
    segments: List[Tuple[float, float]]           # in source seconds, in play order
    hook: str = ""                                 # on-screen in the first seconds ('' = none)
    caption: str = ""                              # '' = the caller's own caption
    source: str = "rules"                          # "ai" when the LLM made the edit
    notes: List[str] = field(default_factory=list)
    speech: List[Dict[str, Any]] = field(default_factory=list)   # the transcript ([{start, end, text}]) the edit was made from

    @property
    def seconds(self) -> float:
        return round(sum(e - s for s, e in self.segments), 2)


# ---- 1. listen ---------------------------------------------------------------------------------------------------------
def _audio_for_stt(src: Path, work: Path) -> Optional[Path]:
    out = work / "speech.mp3"
    try:
        ffmpeg.run(["-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(out), "-y"])
        return out if out.stat().st_size > 1000 else None
    except ffmpeg.FfmpegError:
        return None


async def transcribe(audio: Path, language: str = "mr") -> List[Dict[str, Any]]:
    """[{start, end, text}] from Groq Whisper, or [] (no key, no speech, any failure)."""
    from app.platform.llm import GROQ_STT_URL, STT_MODEL, groq_api_key
    key = os.environ.get("AI_STT_API_KEY") or groq_api_key()
    if not key:
        return []
    form = {"model": STT_MODEL, "response_format": "verbose_json", "temperature": "0"}
    if language in ("mr", "hi", "en"):
        form["language"] = language
    try:
        async with httpx.AsyncClient(timeout=STT_TIMEOUT) as c:
            r = await c.post(GROQ_STT_URL, data=form, files={"file": ("speech.mp3", audio.read_bytes(), "audio/mpeg")},
                             headers={"Authorization": f"Bearer {key}"})
        r.raise_for_status()
        segs = r.json().get("segments") or []
        return [{"start": round(float(s["start"]), 2), "end": round(float(s["end"]), 2), "text": str(s.get("text") or "").strip()}
                for s in segs if s.get("text") and float(s.get("no_speech_prob") or 0) < 0.6]
    except Exception as e:
        log.info("video director: transcription failed (%s)", type(e).__name__)
        return []


# ---- 2. look -----------------------------------------------------------------------------------------------------------
def contact_sheet(src: Path, duration: float, work: Path, crop: str = "") -> Tuple[bytes, List[float]]:
    """A 4x3 JPEG of SHEET_TILES frames, each labelled with its time, and those times. `crop` (video_reel.strip_crop) shows
    each frame as the reel will: without the contact strip we remove."""
    from .video_reel import H, W, _fit
    times = [round(duration * (i + 0.5) / SHEET_TILES, 1) for i in range(SHEET_TILES)]
    tw, th, lh = 270, 480, 34   # the time label sits in a strip ABOVE each tile, never on the picture (it was read as text)
    sheet = Image.new("RGB", (tw * 4, (th + lh) * 3), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        p = work / f"t{i}.jpg"
        ffmpeg.run(["-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-vf", f"{_fit(W, H)}{crop},scale={tw}:{th}", str(p), "-y"])
        x, y = (i % 4) * tw, (i // 4) * (th + lh)
        d.text((x + 8, y + 5), f"t={t:.0f}s", fill=(255, 255, 255), font_size=22)
        sheet.paste(Image.open(p).convert("RGB"), (x, y + lh))
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=80)
    return buf.getvalue(), times


LOOK_PROMPT = (
    "This is a contact sheet of frames from a real-estate site video: 12 tiles, left to right, top to bottom; the grey strip "
    "above each tile gives its time (t=...s) and is not part of the picture. For each tile: say briefly what it shows "
    "(presenter talking, plot boundary stones, road, entrance gate, signboard, layout map, greenery...), rate how good it looks "
    "as a reel shot 0-10 (sharp, well lit, interesting), copy any caption or subtitle text laid over the picture exactly as "
    "you read it (\"\" if none; a small logo in a corner and words printed on a signboard in the scene do not count), and "
    "copy any phone number you can actually read in the picture digit by digit (\"\" if none; never guess). Reply with JSON "
    'only: {"shots": [{"t": <seconds>, "what": "...", "score": <0-10>, "caption": "...", "digits": "..."}]}'
)
PHONE_DIGITS = 8
# a still with a dated offer or festival line burned in (it goes stale, and offers are not ours to repeat)
OFFER = re.compile(r"ऑफर|मोफत|फ्री|नवरात्र|दसर|दसऱ|विजयादशमी|दिवाळी|गुढी|offer|free|discount|navratri|dussehra|diwali", re.I)   # digits read in a frame from which it counts as showing a phone number


def _flags(shot: Dict[str, Any]) -> Dict[str, Any]:
    """phone_on_screen / text_on_screen decided by code from what the model READ (a yes/no question was answered 'yes' for
    every frame of a video that showed no number at all)."""
    digits = re.sub(r"\D", "", str(shot.get("digits") or ""))
    caption = str(shot.get("caption") or "").strip()
    return {**shot, "phone_on_screen": len(digits) >= PHONE_DIGITS, "text_on_screen": len(caption) >= 3}


SPAN = 0.9   # the part of a video that is surveyed: the last 10% is usually a closing card with a phone number
_SURVEYS: Dict[Tuple[str, float, float], Tuple[List[Dict[str, Any]], str, List[float]]] = {}


async def survey(src: Path, duration: float) -> Tuple[List[Dict[str, Any]], str, List[float]]:
    """(shots, strip crop, tile times) for this video, asked of the vision model ONCE per file (the edit and the stills both
    use it; a second call within a minute hits the free tier's rate limit). The tiles are cropped like the reel, so a phone
    number in the strip we remove is not reported."""
    from .video_reel import _sample_frames, find_bottom_bar, strip_crop
    key = (str(src), src.stat().st_mtime, round(duration, 1))
    if key in _SURVEYS:
        return _SURVEYS[key]
    work = Path(tempfile.mkdtemp(prefix="video-survey-"))
    try:
        crop = strip_crop(find_bottom_bar(await asyncio.to_thread(_sample_frames, src, duration, work)))
        sheet, times = await asyncio.to_thread(contact_sheet, src, duration * SPAN, work, crop)
        shots = await look(sheet)
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    if len(_SURVEYS) > 16:
        _SURVEYS.clear()
    if shots:   # a failed look is not remembered: the next step may try again
        _SURVEYS[key] = (shots, crop, times)
    return shots, crop, times


async def look(sheet_jpeg: bytes) -> List[Dict[str, Any]]:
    """[{t, what, score, phone_on_screen}] from the configured vision model(s), or []."""
    from app.modules.photoquality.vision_review import default_clients, parse_reply
    img = "data:image/jpeg;base64," + base64.b64encode(sheet_jpeg).decode()
    for client in default_clients():
        body = {"model": client.model, "temperature": 0, "max_completion_tokens": 1200,
                "messages": [{"role": "user", "content": [{"type": "text", "text": LOOK_PROMPT},
                                                          {"type": "image_url", "image_url": {"url": img}}]}]}
        try:
            async with httpx.AsyncClient(timeout=VISION_TIMEOUT) as c:
                r = await c.post(client.url, json=body, headers={"Authorization": f"Bearer {client.api_key}"})
            r.raise_for_status()
            data = parse_reply(r.json()["choices"][0]["message"]["content"] or "") or {}
            shots = [_flags(s) for s in data.get("shots") or [] if isinstance(s, dict) and "t" in s]
            if shots:
                return shots
        except Exception as e:
            log.info("video director: vision via %s failed (%s)", client.model, type(e).__name__)
    return []


FRAME_MIN_SCORE = 6
FRAMES_KEPT = 8
MIN_STILLS = 3


async def best_frames(src, out_dir, keep: int = FRAMES_KEPT) -> List[str]:
    """Stills for the campaign's post cards: SHEET_TILES frames across the video (the last 10% left out: closing cards carry
    phone numbers), the burned-in contact strip cropped off, the vision model's best `keep` (score >= FRAME_MIN_SCORE, no
    phone on screen), best first. Without the vision model: evenly spaced frames. Paths of JPEGs in `out_dir`, or []."""
    from .video_reel import H, W, _fit
    src, out_dir = Path(src), Path(out_dir)
    try:
        p = ffmpeg.probe(src)
        if not p.duration or not p.width:
            return []
        usable = p.duration * SPAN
        shots, crop, times = await survey(src, p.duration)
        times = times or [round(usable * (i + 0.5) / SHEET_TILES, 1) for i in range(SHEET_TILES)]
        if shots:
            # clean shots first (our card text goes on top: the video's own captions would collide with it), then the rest;
            # when fewer than MIN_STILLS score well, any phone-free shot is used rather than plain cards
            safe = [s for s in shots if not s.get("phone_on_screen") and not OFFER.search(str(s.get("caption") or ""))]
            good = [s for s in safe if _score(s) >= FRAME_MIN_SCORE]
            ranked = sorted(good if len(good) >= MIN_STILLS else safe, key=lambda s: (bool(s.get("text_on_screen")), -_score(s)))
            # the exact tile time the model judged (it answers rounded seconds; captions change within a second)
            picks = [min(times, key=lambda x: abs(x - _t(s))) for s in ranked]
        else:
            picks = times[1:-1]
        chosen: List[float] = []
        for t in picks:   # no two stills from the same moment
            if all(abs(t - c) >= usable / SHEET_TILES * 0.9 for c in chosen):
                chosen.append(t)
            if len(chosen) >= keep:
                break
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob("frame*.jpg"):   # stills of an earlier run must never be mistaken for this one's
            old.unlink(missing_ok=True)
        out = []
        for i, t in enumerate(chosen):
            f = out_dir / f"frame{i:02d}.jpg"
            await asyncio.to_thread(ffmpeg.run, ["-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                                                 "-vf", _fit(W, H) + crop, "-q:v", "3", str(f), "-y"])
            if f.is_file():
                out.append(str(f))
        return out
    except Exception as e:
        log.info("video director: frames failed (%s)", type(e).__name__)
        return []


def _t(s: Dict[str, Any]) -> float:
    try:
        return float(s.get("t") or 0)
    except (TypeError, ValueError):
        return 0.0


def _score(s: Dict[str, Any]) -> float:
    try:
        return float(s.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


# ---- 3. edit -----------------------------------------------------------------------------------------------------------
EDIT_SYSTEM = (
    "You are a short-form video editor for an Indian real-estate agent. You cut a long site video into one Instagram/Facebook "
    "reel that makes a home buyer stop scrolling and want a site visit. You only choose time ranges from the video and write "
    "short text; you never invent facts. You think like the agent's sales lead (open with what a buyer "
    "asks first: where it is, what they can see or get there) and like a designer (the hook is read in one second on a phone, "
    "so it is short and concrete). Reply with JSON only."
)

EDIT_RULES = """Rules:
- Choose 3 to 7 segments from the video, in the order they should play, {tmin:.0f} to {tmax:.0f} seconds in total.
- Start and end each segment on a sentence boundary of the speech (use the transcript times), so no word is cut.
- Open with the strongest moment: the clearest view of the site or the presenter's best line, never a slow start.
- Leave out: any phone number (spoken or on screen), festival or dated offers ("this Dussehra", "free"), prices, "investment",
  "returns", "safe", "guaranteed", repetition, and the closing call-to-action card.
- hook: at most {hook_words} words in {lang}, shown on screen for the first 3 seconds; a plain fact or question about the place
  that a buyer cares about (e.g. location, plot sizes, roads). No hype words, no prices, no phone numbers, no emojis.
- caption: 2-4 short lines in {lang} about what the video shows, only from the transcript and the facts below; end with a
  question to the viewer. No phone number, no price, no hashtags, no claims about investment or returns.
Reply: {{"segments": [{{"start": <s>, "end": <s>}}], "hook": "...", "caption": "..."}}"""


def _edit_prompt(duration: float, speech: List[Dict], shots: List[Dict], facts: Dict[str, str], language: str) -> str:
    lines = [f"Video length: {duration:.1f} s.", "Facts (the only facts you may state): " +
             "; ".join(f"{k}: {v}" for k, v in facts.items() if v)]
    if speech:
        lines.append("Transcript (start-end seconds: words):")
        lines += [f"{s['start']:.1f}-{s['end']:.1f}: {s['text']}" for s in speech]
    else:
        lines.append("No usable speech: cut on the shots below, segments of 2-6 seconds.")
    if shots:
        lines.append("Shots (time: what, score 0-10):")
        lines += [f"{float(s['t']):.0f}s: {s.get('what', '')}, {s.get('score', '?')}" + (" [PHONE ON SCREEN]" if s.get("phone_on_screen") else "")
                  for s in shots]
    lines.append(EDIT_RULES.format(tmin=TARGET_MIN, tmax=TARGET_MAX, hook_words=HOOK_MAX_WORDS, lang=LANG_NAME.get(language, "English")))
    if language in ("mr", "hi"):   # speech-to-text misspells places (शिकरपूर); the hook and caption must not
        from app.modules.creative import i18n
        lines.append("Spell place names and terms exactly as: " + i18n.glossary(language) + ".")
    return "\n".join(lines)


def clean_segments(raw, duration: float, speech: List[Dict], shots: List[Dict]) -> List[Tuple[float, float]]:
    """The LLM's segments made safe: inside the video, at least MIN_SEGMENT long, not overlapping what is already kept, no
    speech or shot with a phone number, at most TARGET_MAX + 5 s in total."""
    banned = [(s["start"], s["end"]) for s in speech if PHONE.search(s["text"])]
    step = duration / SHEET_TILES
    banned += [(float(s["t"]) - step / 2, float(s["t"]) + step / 2) for s in shots if s.get("phone_on_screen")]
    out: List[Tuple[float, float]] = []
    total = 0.0
    for r in raw or []:
        try:
            a, b = max(0.0, float(r["start"])), min(duration, float(r["end"]))
        except (KeyError, TypeError, ValueError):
            continue
        for x, y in banned:   # trim a segment so it stops before (or starts after) a phone number
            if a < y and b > x:
                a, b = (y, b) if x <= a else (a, x)
        if b - a < MIN_SEGMENT or any(a < y and b > x for x, y in out):
            continue
        b = min(b, a + (TARGET_MAX + 5 - total))
        if b - a < MIN_SEGMENT:
            break
        out.append((round(a, 2), round(b, 2)))
        total += b - a
    return out


def _clean_text(text: str, corpus: str, max_words: int = 0) -> str:
    from app.modules.creative.guards import problems_in
    text = re.sub(r"\s+", " ", str(text or "")).strip().strip('"')
    if max_words and len(text.split()) > max_words:
        return ""
    return text if text and not problems_in(text, corpus) else ""


async def plan(src, *, facts: Dict[str, str], language: str = "mr", llm=None, max_seconds: float = 90.0,
               trim_end: float = 0.0) -> EditPlan:
    """The edit for this video. Never raises; without AI it is the whole clip (up to max_seconds) and no hook."""
    src = Path(src)
    p = ffmpeg.probe(src)
    usable = max(1.0, (p.duration or 0) - max(0.0, trim_end))
    fallback = EditPlan(segments=[(0.0, round(min(usable, max_seconds), 2))])
    if llm is None or not p.duration:
        fallback.notes.append("no AI: the whole clip, no hook")
        return fallback
    work = Path(tempfile.mkdtemp(prefix="video-director-"))
    try:
        audio = await asyncio.to_thread(_audio_for_stt, src, work) if p.has_audio else None
        speech, (shots, _, _) = await asyncio.gather(transcribe(audio, language) if audio else _none(), survey(src, p.duration))
        shots = [s for s in shots if _t(s) < usable]
        speech = [s for s in speech if s["start"] < usable]
        try:
            reply = await llm.json(EDIT_SYSTEM, _edit_prompt(usable, speech, shots, facts, language)) or {}
        except Exception as e:
            log.info("video director: edit failed (%s)", type(e).__name__)
            reply = {}
        segs = clean_segments(reply.get("segments"), usable, speech, shots)
        notes = [f"speech segments: {len(speech)}", f"shots: {len(shots)}"]
        if sum(b - a for a, b in segs) < TARGET_MIN * 0.6:
            fallback.notes += notes + ["the AI edit was too short or unusable: the whole clip"]
            fallback.speech = speech
            return fallback
        corpus = " ".join([*(s["text"] for s in speech), *(str(v) for v in facts.values())])
        return EditPlan(segments=segs, hook=_clean_text(reply.get("hook"), corpus, HOOK_MAX_WORDS),
                        caption=_clean_text(reply.get("caption"), corpus), source="ai", notes=notes, speech=speech)
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)


async def _none() -> list:
    return []
