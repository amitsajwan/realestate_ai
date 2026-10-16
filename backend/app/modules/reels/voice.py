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
# Chirp 3 HD reads pause tags ([pause short], [pause], [pause long]) in `markup` only, and takes our names' pronunciations
# (custom pronunciations; en-IN, hi-IN and mr-IN take them). https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd
SPEAKERS = {"female": "Zephyr", "male": "Charon"}   # owner 2026-10-16: Kore sounded dull; Zephyr is the bright one
SPOKEN_RATE = 0.95        # a little slower than a read: a person showing a project, not an ad
SPOKEN_RATES = {"hi": 0.88, "mr": 0.88}   # Hindi and Marathi came out too quick at the English pace (owner 2026-10-16)
PAUSE_TAG = re.compile(r"(\[pause(?: short| long)?\])")
# how our names are said (IPA, sent as Chirp's custom pronunciations), and the spelling that says them when the service
# refuses a pronunciation; a Hindi or Marathi line writes a place in Devanagari, which its voice says right
NAMES = {   # owner, 2026-10-16: Avasetu is "AvaS-Setu" (not "Av-setu"), Kharadi is "khar-aa-di" (not "kardi")
    "Avasetu": "əʋaːs seːt̪uː", "Kharadi": "kʰəˈraːɖiː", "Wagholi": "ʋaːˈɡʰoːliː", "Lohegaon": "loːˈɦeːɡaːʋ",
    "Hinjawadi": "ˈɦɪndʒəʋaːɖiː", "Hinjewadi": "ˈɦɪndʒəʋaːɖiː", "Wakad": "ˈʋaːkəɖ", "Baner": "ˈbaːneːr",
    "Keshav Nagar": "ˈkeːʃəʋ ˈnəɡər", "Ranjangaon": "ˈraːndʒəɳɡaːʋ", "Shirur": "ʃɪˈruːr", "Viman Nagar": "ʋɪˈmaːn ˈnəɡər",
    "Hadapsar": "ˈɦəɖəpsər", "Lodha": "ˈloːɖʱaː", "Magarpatta": "ˈməɡərpəʈʈaː", "Kesnand": "ˈkeːsnənd",
    "Shikrapur": "ˈʃɪkraːpuːr"}
# a Hindi or Marathi voice reads a Latin name the English way ("Kharadi" came out "kardi"): its lines always get the name in
# Devanagari before they are said (`for_voice`), pronunciations or not
DEVANAGARI = {"Avasetu": "अवास सेतु"}
RESPELL = {"Avasetu": {"en": "Avaas Setu", "hi": "अवास सेतु", "mr": "अवास सेतु"}, "Kharadi": {"en": "khaa-raa-dee"},
           "Wagholi": {"en": "vaa-gho-lee"}, "Lohegaon": {"en": "lo-hay-gaon"}, "Hinjawadi": {"en": "hin-ja-waa-dee"},
           "Hinjewadi": {"en": "hin-ja-waa-dee"}, "Wakad": {"en": "vaa-kud"}, "Baner": {"en": "baa-ner"},
           "Keshav Nagar": {"en": "kay-shuv nuh-gur"}, "Ranjangaon": {"en": "raan-jun-gaon"}, "Shirur": {"en": "shi-roor"},
           "Viman Nagar": {"en": "vi-maan nuh-gur"}, "Hadapsar": {"en": "huh-dup-sur"}, "Lodha": {"en": "lo-dhaa"},
           "Magarpatta": {"en": "mug-ur-puttaa"}, "Kesnand": {"en": "kays-nund"}, "Shikrapur": {"en": "shik-raa-pur"}}


def spoken_markup(text: str) -> str:
    """`text` as markup: our pause tags kept, any other bracket dropped."""
    parts = PAUSE_TAG.split(text)   # the tags at the odd places
    return " ".join(" ".join(p if i % 2 else p.replace("[", "").replace("]", "") for i, p in enumerate(parts)).split())


def unpaused(text: str) -> str:
    """`text` without its pause tags (what the checks read)."""
    return " ".join(PAUSE_TAG.sub(" ", text).split())


GREETING_RATE = 0.78      # "Naaamaste dostooo": the greeting drawn out, in the same voice (a raised pitch sounded like another one)


def synth_greeting(text: str, lang: str = "en", gender: str = "female") -> bytes:
    """MP3 of the host's greeting said slowly, in the same voice as the lines. Raises VoiceError."""
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise VoiceError("GOOGLE_TTS_API_KEY is not set")
    code = VOICES.get(lang, VOICES["en"])[0]
    name = f"{code}-Chirp3-HD-{SPEAKERS.get(gender, SPEAKERS['female'])}"
    for inp, rate in (({"markup": spoken_markup(text)}, GREETING_RATE),):
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
    from app.modules.creative.i18n import PLACES
    names = {**{k: v[lang] for k, v in PLACES.items() if v.get(lang)}, **DEVANAGARI}
    for name in sorted(names, key=len, reverse=True):   # "Upper Kharadi" before "Kharadi"
        text = re.sub(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", names[name], text)
    return text


def synth_spoken(text: str, lang: str = "en", gender: str = "female", rate: Optional[float] = None) -> bytes:
    """MP3 of one spoken line with its pause tags, in the Chirp 3 HD voice of `gender` for `lang` (en, hi or mr). Our names
    go as custom pronunciations; when the service refuses them, the name is respelled instead. Raises VoiceError."""
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise VoiceError("GOOGLE_TTS_API_KEY is not set")
    rate = rate or SPOKEN_RATES.get(lang, SPOKEN_RATE)
    code = VOICES.get(lang, VOICES["en"])[0]
    name = f"{code}-Chirp3-HD-{SPEAKERS.get(gender, SPEAKERS['female'])}"
    markup = spoken_markup(for_voice(text, lang))
    said = [n for n in NAMES if n in markup] if lang == "en" else []   # Hindi/Marathi lines carry the names in Devanagari

    def ask(inp: dict):
        body = {"input": inp, "voice": {"languageCode": code, "name": name},
                "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate, "sampleRateHertz": 48000}}
        try:
            return httpx.post(URL, headers={"X-Goog-Api-Key": key}, json=body, timeout=60)
        except Exception as e:
            raise VoiceError(f"voice service unreachable ({type(e).__name__})")

    r = ask({"markup": markup, **({"customPronunciations": {"pronunciations": [
        {"phrase": n, "phoneticEncoding": "PHONETIC_ENCODING_IPA", "pronunciation": NAMES[n]} for n in said]}} if said else {})})
    if r.status_code == 400 and said:   # pronunciations refused: the names respelled instead
        for n in said:
            markup = markup.replace(n, RESPELL.get(n, {}).get(lang, n))
        r = ask({"markup": markup})
    if r.status_code >= 400:
        msg = (r.json().get("error") or {}).get("message", "") if r.headers.get("content-type", "").startswith("application/json") else ""
        raise VoiceError((f"HTTP {r.status_code}" + (f": {msg}" if msg else "")).replace(key, "[redacted]")[:200])
    return base64.b64decode(r.json()["audioContent"])

