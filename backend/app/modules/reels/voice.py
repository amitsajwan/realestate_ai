"""Voiceover through Google Cloud Text-to-Speech (Chirp 3 HD Indian voices). Key: GOOGLE_TTS_API_KEY (restricted to the TTS API).
Returns MP3 bytes; errors never leak the key.

Chirp 3 HD voices take plain text or a small part of SSML (<break>, <prosody>, <voice>) in a normal request; they do not take
<mark>, so the service cannot say when each line starts. `take_ssml` writes a whole script as one request with a long pause
between lines, which reels.narration cuts back into lines (https://cloud.google.com/text-to-speech/docs/chirp3-hd)."""
import base64
import os
import re
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



# ---- the voice-over step (propertyfacts.voiceover): Chirp 3 HD only, on the server's key, talking like a person ------------
# Chirp 3 HD reads pause tags ([pause short], [pause], [pause long]) in `markup` only
# https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd
SPEAKERS = {"female": "Zephyr", "male": "Charon"}   # owner 2026-10-16: Kore sounded dull; Zephyr is the bright one
SPOKEN_RATE = 1.05        # a reel host's pace, not a read (owner 2026-10-16: the slow voice irritated next to entertainment reels)
SPOKEN_RATES = {"hi": 1.0, "mr": 1.0}   # 0.88 sounded slow and flat next to entertainment reels (owner 2026-10-16, later)
PAUSE_TAG = re.compile(r"(\[pause(?: short| long)?\])")
# how our names are said: in Devanagari (spoken_names), the one form every Indian voice says right; en-IN takes no custom
# pronunciations (all refused, 2026-10-19), so there is no IPA list


def spoken_markup(text: str) -> str:
    """`text` as markup: our pause tags kept, any other bracket dropped."""
    parts = PAUSE_TAG.split(text)   # the tags at the odd places
    return " ".join(" ".join(p if i % 2 else p.replace("[", "").replace("]", "") for i, p in enumerate(parts)).split())


def unpaused(text: str) -> str:
    """`text` without its pause tags (what the checks read)."""
    return " ".join(PAUSE_TAG.sub(" ", text).split())


GREETING_RATE = 0.9       # the greeting a little drawn out, in the same voice (a raised pitch sounded like another one)


def synth_greeting(text: str, lang: str = "en", gender: str = "female") -> bytes:
    """MP3 of the host's greeting said slowly, in the same voice as the lines. Raises VoiceError."""
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise VoiceError("GOOGLE_TTS_API_KEY is not set")
    code = VOICES.get(lang, VOICES["en"])[0]
    name = f"{code}-Chirp3-HD-{SPEAKERS.get(gender, SPEAKERS['female'])}"
    for inp, rate in (({"markup": spoken_markup(spoken(text, lang))}, GREETING_RATE),):
        body = {"input": inp, "voice": {"languageCode": code, "name": name},
                "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate, "sampleRateHertz": 48000}}
        try:
            r = httpx.post(URL, headers={"X-Goog-Api-Key": key}, json=body, timeout=60)
        except Exception as e:
            raise VoiceError(f"voice service unreachable ({type(e).__name__})")
        if r.status_code < 400:
            return base64.b64decode(r.json()["audioContent"])
    raise VoiceError(f"greeting HTTP {r.status_code}".replace(key, "[redacted]"))


def for_voice(text: str, lang: str) -> str:
    """`text` with our Latin names in Devanagari for a Hindi or Marathi voice (Avasetu, the Pune places of creative.i18n);
    unchanged for English."""
    units = {"en": "square feet", "hi": "स्क्वेयर फीट", "mr": "स्क्वेअर फूट"}   # "sqft" was spelled out letter by letter
    text = re.sub(r"\bsq\.?\s*ft\b|\bsqft\b", units.get(lang, units["en"]), text, flags=re.I)
    if lang not in ("hi", "mr"):
        return text
    return _names_in_devanagari(text, lang)


def _names_in_devanagari(text: str, lang: str) -> str:
    """`text` with our names (spoken_names, creative.i18n's spelling for `lang` where it has one) in Devanagari."""
    from app.modules.creative.i18n import PLACES
    from .spoken_names import SPOKEN
    names = {**SPOKEN, **{k: v[lang] for k, v in PLACES.items() if v.get(lang)}}
    for name in sorted(names, key=len, reverse=True):   # "Upper Kharadi" before "Kharadi"
        text = re.sub(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", names[name], text)
    return text


def spoken(text: str, lang: str) -> str:
    """`text` as it goes to a voice: units in words and our names in Devanagari for every language, English too (an Indian
    English voice says "अपर खराड़ी" right and guesses "Upper Kharadi"; owner 2026-10-19 on the Upper Kharadi reels). English
    takes the Hindi spellings. Captions keep `for_voice` (an English caption shows the Latin name)."""
    if lang in ("hi", "mr"):
        return for_voice(text, lang)
    return _names_in_devanagari(for_voice(text, lang), "hi")


def synth_spoken(text: str, lang: str = "en", gender: str = "female", rate: Optional[float] = None) -> bytes:
    """MP3 of one spoken line with its pause tags, in the Chirp 3 HD voice of `gender` for `lang` (en, hi or mr). Our names
    go as custom pronunciations; when the service refuses them, the name is respelled instead. Raises VoiceError."""
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise VoiceError("GOOGLE_TTS_API_KEY is not set")
    rate = rate or SPOKEN_RATES.get(lang, SPOKEN_RATE)
    code = VOICES.get(lang, VOICES["en"])[0]
    name = f"{code}-Chirp3-HD-{SPEAKERS.get(gender, SPEAKERS['female'])}"
    markup = spoken_markup(spoken(text, lang))

    def ask(inp: dict):
        body = {"input": inp, "voice": {"languageCode": code, "name": name},
                "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate, "sampleRateHertz": 48000}}
        try:
            return httpx.post(URL, headers={"X-Goog-Api-Key": key}, json=body, timeout=60)
        except Exception as e:
            raise VoiceError(f"voice service unreachable ({type(e).__name__})")

    r = ask({"markup": markup})
    if r.status_code >= 400:
        msg = (r.json().get("error") or {}).get("message", "") if r.headers.get("content-type", "").startswith("application/json") else ""
        raise VoiceError((f"HTTP {r.status_code}" + (f": {msg}" if msg else "")).replace(key, "[redacted]")[:200])
    return base64.b64decode(r.json()["audioContent"])



# ---- Gemini's voice, first choice for the voice-over step (owner, 2026-10-16: the Chirp voice sounded slow and one-toned next
# to entertainment reels; Gemini, on the paid project key, takes a direction: an energetic, warm reel host). Chirp above stays
# the fallback, for a whole reel at a time (narration.spoken_lines), so one reel never mixes two voices.
GEMINI_TTS_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_TTS_MODELS = ("gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts")
GEMINI_SR = 24000   # Gemini's audio: 16-bit mono PCM at 24 kHz
# Only the words go to Gemini: it reads any direction aloud (2026-10-16: "Read this aloud as a warm, energetic..." made a 12-word
# line 17.9 s instead of 4.8 s; a short "Say warmly:" still 8.3 s), and this model takes no system instruction. Its natural
# voice is livelier than Chirp's; the words and their punctuation carry the rest.


def gemini_on() -> bool:
    """Gemini speaks the voice-overs when its key is set, unless REEL_VOICE_ENGINE=chirp."""
    return bool(os.environ.get("GEMINI_API_KEY")) and (os.environ.get("REEL_VOICE_ENGINE") or "gemini").lower() != "chirp"


def gemini_text(text: str, lang: str) -> str:
    """A line as Gemini reads it: our names in Devanagari for Hindi or Marathi (for_voice), the pause tags as punctuation (it
    reads no tags), no other brackets."""
    t = spoken(text, lang).replace("[pause short]", ",").replace("[pause long]", "...").replace("[pause]", "...")
    return " ".join(t.replace("[", "").replace("]", "").split())


def gemini_speech(text: str, lang: str = "en", gender: str = "female", greeting: bool = False) -> bytes:
    """A WAV (24 kHz mono) of one line in Gemini's voice of `gender`, directed as a reel host. Raises VoiceError when no model
    answers with audio."""
    import io
    import wave as wav_mod
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise VoiceError("GEMINI_API_KEY is not set")
    prompt = gemini_text(text, lang)   # `greeting` kept for the caller: the words alone say it (no direction, see above)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {
                "voiceName": SPEAKERS.get(gender, SPEAKERS["female"])}}}}}
    why = "no model answered"
    for model in GEMINI_TTS_MODELS:
        try:
            r = httpx.post(GEMINI_TTS_URL.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=90)
        except Exception as e:
            why = f"{model} unreachable ({type(e).__name__})"
            continue
        if r.status_code >= 400:
            why = f"{model} HTTP {r.status_code}"
            continue
        try:
            parts = (r.json().get("candidates") or [{}])[0].get("content", {}).get("parts") or []
            pcm = b"".join(base64.b64decode(p["inlineData"]["data"]) for p in parts if (p.get("inlineData") or {}).get("data"))
        except ValueError:
            pcm = b""
        if not pcm:
            why = f"{model} answered without audio"
            continue
        out = io.BytesIO()
        with wav_mod.open(out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(GEMINI_SR)
            w.writeframes(pcm)
        return out.getvalue()
    raise VoiceError(f"gemini speech: {why}".replace(key, "[redacted]"))
