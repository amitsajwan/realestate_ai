"""AI reel director: an LLM writes the beats (short on-screen text + a spoken line each) from supplied facts only; a voice is synthesised per
beat, each scene lasts as long as its line, and the narration is mixed under the video. Hindi/Marathi voice + Hinglish on-screen text (the
renderer cannot shape Devanagari)."""
import json
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import ffmpeg, narration
from .compose import Scene, TextLine, make_reel, photo_plan, plan, stretch

END_SECONDS = 2.6   # length of the optional end card (reels have none by default)
XFADE = 0.4
NUM = re.compile(r"\d[\d,.]*")
MIN_SCENES = 3   # hook, one beat, the call to action
# The reel's call to action is a comment our comment assistant answers (engage.brain matches 'interested' / 'details' /
# इंटरेस्टेड): the keyword stays INTERESTED in Roman capitals on screen in every language; the voice may say it in Devanagari.
CTA_WORD = "INTERESTED"
CTA_SCREEN = {"en": "Comment *INTERESTED* for details", "hi": "Details ke liye *INTERESTED* comment karein",
              "mr": "Details sathi *INTERESTED* comment kara"}
CTA_VOICE = {"en": "Like it? Comment interested for the details.", "hi": "पसंद आया? पूरी जानकारी के लिए कमेंट में इंटरेस्टेड लिखिए।",
             "mr": "आवडलं? पूर्ण माहितीसाठी कमेंटमध्ये इंटरेस्टेड लिहा."}

SYSTEM = (
    "You direct a 12 to 16 second vertical property reel for Pune home buyers. Write JSON only: "
    '{"beats": [{"screen": "...", "voice": "..."}], "cta_screen": "...", "cta_voice": "..."}. '
    "Rules: 4 beats. beat 1 is the hook: a question or surprise that makes a buyer stop scrolling. "
    "screen: at most 6 words, Roman letters only (English or Hinglish), wrap ONE key word in *stars* for gold. "
    "voice: one natural spoken sentence of at most 16 words in the requested voice language (Hindi = Devanagari script, Marathi = Devanagari, "
    "English = English). Use ONLY the facts given: never invent numbers, distances, prices, schools, builders or promises. "
    "Never mention phone numbers. "
    "cta: ask viewers to comment the word INTERESTED for details (never a link in bio, never 'tap'). cta_screen: "
    "'Comment *INTERESTED* for details' in English, or Hinglish with INTERESTED in Roman capitals such as "
    "'Details ke liye *INTERESTED* comment karein'; cta_voice says the same in the voice language (Hindi/Marathi: इंटरेस्टेड)."
)


def _numbers(s: str) -> set:
    return {n.replace(",", "").rstrip(".") for n in NUM.findall(s or "")}


def _valid(script: dict, facts: str) -> bool:
    if not isinstance(script, dict) or not isinstance(script.get("beats"), list) or not (3 <= len(script["beats"]) <= 5):
        return False
    allowed = _numbers(facts)
    for b in script["beats"] + [{"screen": script.get("cta_screen", ""), "voice": script.get("cta_voice", "")}]:
        if not isinstance(b, dict) or not str(b.get("screen", "")).strip() or not str(b.get("voice", "")).strip():
            return False
        if len(str(b["screen"]).split()) > 8 or re.search(r"[ऀ-ॿ]", str(b["screen"])):
            return False
        if (_numbers(b["screen"]) | _numbers(b["voice"])) - allowed:
            return False
        if re.search(r"\b[6-9]\d{9}\b", b["screen"] + b["voice"]):
            return False
    return True


numbers_in = _numbers
valid_script = _valid  # 3-5 beats plus a call to action: short Roman-letter screen text, no number that is not in `facts`, no phone numbers


async def write_script(subject: str, facts: Sequence[str], lang: str, llm, fallback: Dict) -> Dict:
    facts_text = "\n".join(f"- {f}" for f in facts)
    if llm is not None:
        for _ in range(3):
            out = await llm.json(SYSTEM, f"Voice language: {dict(en='English', hi='Hindi', mr='Marathi')[lang]}\nSubject: {subject}\nFacts:\n{facts_text}")
            if _valid(out, subject + "\n" + facts_text):
                return {**out, "made_by": "llm"}
    return {**fallback, "made_by": "rules"}


def fit_beats(script: Dict, photos: Sequence) -> tuple:
    """(scene beats, one photo per scene): the hook, as many beats as there are distinct photos for, and the call to action.
    Beats are dropped from the end rather than a photo shown twice; the minimum is the hook, one beat and the CTA."""
    beats = list(script["beats"])
    cta = {"screen": script["cta_screen"], "voice": script["cta_voice"]}
    picks = photo_plan(len(beats) + 1, photos, MIN_SCENES)
    if not picks:  # no photos at all (a trend or explainer reel): branded-background scenes, every beat kept
        return beats + [cta], [None] * (len(beats) + 1)
    return beats[:max(1, len(picks) - 1)] + [cta], picks


def build(script: Dict, photos: Sequence, lang: str, out_path: Path, badge: Optional[str] = None, kicker: Optional[str] = None,
          with_music: bool = True, voiced: bool = True) -> Path:
    """`voiced=False` makes the reel without narration (no TTS key, or on purpose): fixed scene lengths, the Avasetu theme under it."""
    beats, picks = fit_beats(script, photos)
    work = Path(tempfile.mkdtemp(prefix="reel-"))
    clips, durs = [], []
    if voiced:
        clips, _ = narration.voice_lines([b["voice"] for b in beats], lang, work)
        durs = [max(2.2, ffmpeg.probe(c).duration + 0.55) for c in clips]
    else:
        durs = [2.6 if i == 0 else 3.0 for i in range(len(beats))]
    durs = stretch(durs, XFADE)
    scenes = []
    for i, b in enumerate(beats):
        first = i == 0
        lines = [TextLine(b["screen"], size=104 if first else 96)]
        scenes.append(Scene(image=picks[i], lines=lines, layout="lower", badge=badge,
                            kicker=kicker if first else None, seconds=durs[i], seed=f"dir-{i}"))
    if not voiced:
        return make_reel(scenes, out_path, transition="slide", xfade=XFADE)
    tl = plan(durs, XFADE)   # no end card: the last scene (with the brand mark) loops back to the hook
    bed = None
    if with_music:
        from .music import write as write_music
        bed = write_music(work / "bed.wav", seconds=tl.total + 1.0)
    audio = narration.mix(work, clips, tl.starts, tl.total, bed)   # the voice in one take where it cuts cleanly, the music ducked under it
    return make_reel(scenes, out_path, music=audio, transition="slide", xfade=XFADE)
