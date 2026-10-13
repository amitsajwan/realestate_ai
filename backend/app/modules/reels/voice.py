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
VOICES = {  # warm, clear voices; override with REEL_VOICE_<LANG>
    "en": ("en-IN", "en-IN-Chirp3-HD-Aoede"),
    "hi": ("hi-IN", "hi-IN-Chirp3-HD-Aoede"),
    "mr": ("mr-IN", "mr-IN-Chirp3-HD-Aoede"),
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
        r = httpx.post(URL, params={"key": key}, json=body, timeout=60)
    except Exception as e:
        raise VoiceError(f"voice service unreachable ({type(e).__name__})")
    if r.status_code >= 400:
        msg = (r.json().get("error") or {}).get("message", "") if r.headers.get("content-type", "").startswith("application/json") else ""
        raise VoiceError((f"HTTP {r.status_code}" + (f": {msg}" if msg else "")).replace(key, "[redacted]")[:200])
    return base64.b64decode(r.json()["audioContent"])
