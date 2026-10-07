"""Voiceover through Google Cloud Text-to-Speech (Chirp 3 HD Indian voices). Key: GOOGLE_TTS_API_KEY (restricted to the TTS API).
Returns MP3 bytes; errors never leak the key."""
import base64
import os
from typing import Optional

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


def synth(text: str, lang: str = "en", voice: Optional[str] = None, rate: float = 1.05) -> bytes:
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise VoiceError("GOOGLE_TTS_API_KEY is not set")
    code, default = VOICES.get(lang, VOICES["en"])
    name = voice or os.environ.get(f"REEL_VOICE_{lang.upper()}") or default
    body = {"input": {"text": text}, "voice": {"languageCode": code, "name": name},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate, "sampleRateHertz": 48000}}
    try:
        r = httpx.post(URL, params={"key": key}, json=body, timeout=60)
    except Exception as e:
        raise VoiceError(f"voice service unreachable ({type(e).__name__})")
    if r.status_code >= 400:
        msg = (r.json().get("error") or {}).get("message", f"HTTP {r.status_code}") if r.headers.get("content-type", "").startswith("application/json") else f"HTTP {r.status_code}"
        raise VoiceError(msg.replace(key, "[redacted]")[:200])
    return base64.b64decode(r.json()["audioContent"])
