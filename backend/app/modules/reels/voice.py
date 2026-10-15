"""Voiceover through Google Cloud Text-to-Speech (Chirp 3 HD Indian voices). Key: GOOGLE_TTS_API_KEY (restricted to the TTS API).
Returns MP3 bytes; errors never leak the key.

Chirp 3 HD voices take plain text or a small part of SSML (<break>, <prosody>, <voice>) in a normal request; they do not take
<mark>, so the service cannot say when each line starts. `take_ssml` writes a whole script as one request with a long pause
between lines, which reels.narration cuts back into lines (https://cloud.google.com/text-to-speech/docs/chirp3-hd)."""
import base64
import os
from typing import Optional, Sequence
from xml.sax.saxutils import escape

import httpx

URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
VOICES = {  # Charon: a calm male voice, an agent talking (owner, 2026-10-14: Aoede sounded "AI"); override with REEL_VOICE_<LANG>
    "en": ("en-IN", "en-IN-Chirp3-HD-Charon"),
    "hi": ("hi-IN", "hi-IN-Chirp3-HD-Charon"),
    "mr": ("mr-IN", "mr-IN-Chirp3-HD-Charon"),
}


class VoiceError(Exception):
    pass


def available() -> bool:
    return bool(os.environ.get("GOOGLE_TTS_API_KEY"))


LINE_BREAK_MS = 1200   # the pause between lines in a one-take script; longer than any pause the voice makes inside a line


def take_ssml(lines: Sequence[str]) -> str:
    """The lines as one SSML script, a long pause between them."""
    gap = f'<break time="{LINE_BREAK_MS}ms"/>'
    return "<speak>" + gap.join(escape(" ".join(str(x).split())) for x in lines) + "</speak>"


def synth(text: str, lang: str = "en", voice: Optional[str] = None, rate: float = 1.05, ssml: bool = False) -> bytes:
    """MP3 of `text` (plain text, or an SSML document when `ssml`)."""
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise VoiceError("GOOGLE_TTS_API_KEY is not set")
    code, default = VOICES.get(lang, VOICES["en"])
    name = voice or os.environ.get(f"REEL_VOICE_{lang.upper()}") or default
    body = {"input": {"ssml" if ssml else "text": text}, "voice": {"languageCode": code, "name": name},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate, "sampleRateHertz": 48000}}
    try:
        r = httpx.post(URL, headers={"X-Goog-Api-Key": key}, json=body, timeout=60)
    except Exception as e:
        raise VoiceError(f"voice service unreachable ({type(e).__name__})")
    if r.status_code >= 400:
        msg = (r.json().get("error") or {}).get("message", "") if r.headers.get("content-type", "").startswith("application/json") else ""
        raise VoiceError((f"HTTP {r.status_code}" + (f": {msg}" if msg else "")).replace(key, "[redacted]")[:200])
    return base64.b64decode(r.json()["audioContent"])


# ---- Gemini speech: a voice that takes directions (owner, 2026-10-14: the Chirp voice said "I-F-O", got Kharadi wrong and
# kept one flat tone). The line writer (ad_reel.speak) says how each line should sound; Gemini performs it. Google's voice
# above stays the fallback. Output: 16-bit mono PCM at 24 kHz.
GEMINI_TTS_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_VOICE = "Charon"
GEMINI_SR = 24000
# how Pune names are said, for the voice (spelling stays as it is on screen)
PRONOUNCE = {"Kharadi": "khaa-raa-dee", "Wagholi": "vaa-gho-lee", "Lohegaon": "lo-hay-gaon", "Hinjawadi": "hin-ja-waa-dee",
             "Hinjewadi": "hin-ja-waa-dee", "Wakad": "vaa-kud", "Baner": "baa-ner", "Keshav Nagar": "kay-shuv nuh-gur",
             "Ranjangaon": "raan-jun-gaon", "Shirur": "shi-roor", "Viman Nagar": "vi-maan nuh-gur", "Hadapsar": "huh-dup-sur",
             "Lodha": "lo-dhaa", "Magarpatta": "mug-ur-puttaa", "Kesnand": "kays-nund", "Shikrapur": "shik-raa-pur"}
STYLE = ("Speak as a warm, confident Pune property creator talking to a friend on Instagram, in natural Indian English, with real "
         "expression that follows the meaning of each line, never one flat tone.")


def gemini_available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY")) and (os.environ.get("REEL_VOICE_ENGINE") or "gemini").lower() != "google"


def pronunciation(lines: Sequence[str]) -> str:
    said = [f"'{name}' as '{how}'" for name, how in PRONOUNCE.items() if any(name.lower() in l.lower() for l in lines)]
    return ("Pronounce " + ", ".join(said) + ".") if said else ""


def gemini_speech(text: str, voice: Optional[str] = None, timeout: float = 120.0) -> bytes:
    """PCM (16-bit mono, 24 kHz) of `text`, which carries its own directions. Raises VoiceError."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise VoiceError("GEMINI_API_KEY is not set")
    model = os.environ.get("REEL_TTS_MODEL") or GEMINI_TTS_MODEL
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {
                "voiceName": voice or os.environ.get("REEL_GEMINI_VOICE") or GEMINI_VOICE}}}}}
    try:
        r = httpx.post(GEMINI_TTS_URL.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=timeout)
    except Exception as e:
        raise VoiceError(f"gemini speech unreachable ({type(e).__name__})")
    if r.status_code >= 400:
        raise VoiceError(f"gemini speech HTTP {r.status_code}: {r.text[:120]}".replace(key, "[redacted]"))
    try:
        part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
        return base64.b64decode(part["data"])
    except (KeyError, IndexError, ValueError) as e:
        raise VoiceError(f"gemini speech: no audio in the answer ({type(e).__name__})")


def gemini_script(lines: Sequence[str], direction: str = "") -> str:
    """The text Gemini performs: the style, the line writer's direction, the pronunciations, then the lines with a clear pause
    between them (the take is cut at those pauses)."""
    head = " ".join(x for x in (STYLE, direction.strip(), pronunciation(lines),
                                "Leave a pause of about two seconds between lines; read exactly these words.") if x)
    return head + "\n\n" + "\n".join(" ".join(str(l).split()) for l in lines)
