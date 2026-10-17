"""Guide reels: one useful thing a family needs to know now (a MHADA deadline, a scheme's rule), told in their language over real-
looking pictures, posted on its own (owner 2026-10-17: the MHADA Marathi reel got 2/3 of all our views; "reel should not be
text, proper images"; topic reels post without an approval step).

A guide is a file in guides/<name>.json: the facts with their sources, the shots (a picture prompt, a short screen line and a
spoken line each), the caption and the comment assistant's reply sheet (reply_facts, reply_faq: knowledge.grounding reads them
off the row). From it:
  1. the team writes: a writer offers three versions of the beats from the facts, an editor picks the strongest hook and tightens
     it; code keeps only words that pass `problems` (no number outside the facts, every must-say number said, short lines), else
     the guide's own lines are used as written;
  2. pictures: a hand-made one per shot when it is there, else Gemini draws and checks it (reels.pictures). Drawn pictures carry
     SYMBOLIC on screen; a shot with no picture falls back to the branded background;
  3. two rows (Instagram, Facebook), status approved, due at the guide's time, the words, pictures and reply sheet on each;
  4. the renderer (Cloud Run, calendar pre-render) draws the video before the due time: the voice (Gemini, narration.spoken_lines),
     no music unless the guide names a mood in "music", reels.compose (render_row).

    scripts/guide_reel.py write mhada-outage-mr      # the team's words only (a minute; nothing drawn or posted)
    scripts/guide_reel.py plan mhada-outage-mr       # words + pictures, and the two rows (approved, no video yet)
    scripts/guide_reel.py render mhada-outage-mr     # draw the video now (the renderer does it by itself before the due time)
"""
import json
import logging
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.modules.reels import director as _director
from app.modules.reels import narration, pictures
from app.modules.reels.compose import Scene, TextLine, make_reel, plan, stretch

log = logging.getLogger(__name__)

GUIDES = Path(__file__).resolve().parent / "guides"
SUBDIR = "calendar/guides"
SYMBOLIC = {"mr": "प्रतीकात्मक छायाचित्र", "hi": "प्रतीकात्मक चित्र", "en": "ILLUSTRATION"}
XFADE = 0.4
MIN_SCENE = 2.4          # a screen line needs this long to be read, even under a short spoken line
MAX_SCREEN_WORDS = 6
MAX_VOICE_WORDS = 16     # one breath
MAX_TOTAL_WORDS = 46     # about 22 s: Marathi runs ~2.1 words a second with the pauses (62 words made a 29.4 s reel, 2026-10-17)
LANGS = {"mr": "Marathi", "hi": "Hindi", "en": "English"}
# Never a promise of a home or of better odds (a lottery is a draw). Live 2026-10-17 the editor wrote "पैसे भरले तरच घर मिळेल"
# ("pay and only then you get a home"): any of these in a screen or spoken line refuses the beats. A guide adds its own in "never".
NEVER = ("घर मिळेल", "घर मिळणार", "घर नक्की", "नक्की मिळ", "मिळेलच", "घर मिलेगा", "पक्का घर", "गॅरंटी", "guarantee",
         "100%", "you will get a home", "sure shot")

WRITER = (
    "You are the writer on a small creative team that makes short vertical reels for ordinary families in Pune about government "
    "housing (MHADA, PMAY). The viewer scrolls past in one second unless the first line touches something they care about. "
    "Write three different versions of the reel's beats, one beat per shot, in the order of the shots. Each beat: "
    "'screen' = the big words on screen, at most 5 words, wrap ONE key word or date in *stars*; "
    "'voice' = one natural spoken sentence of at most {line} words, the way a friendly elder sister from Pune would say it, not a "
    "news reader. The language is given; Marathi and Hindi in Devanagari, numbers as digits. Use ONLY the facts given: every date, "
    "time and number must come from them; never promise a home, better odds or help with the application; never mention a phone "
    "number or a website; a date the facts call planned stays planned (Marathi नियोजित). The guide may name words that must stay. Beat 1 is the hook (a question or a sharp truth); the last beat asks the viewer to send this to a friend "
    "who is applying. Keep each shot's meaning (its picture is fixed). "
    'Answer JSON only: {"versions": [{"beats": [{"screen": "...", "voice": "..."}]}]}'
)
EDITOR = (
    "You are the editor on the same team. You get the facts, the shots and the writer's versions. Pick the strongest hook, take the "
    "best beat for each shot from any version, and tighten: shorter is better, spoken words, no repeated idea, every date exactly as "
    "in the facts. Same rules as the writer (screen at most 5 words with one *starred* word; voice at most {line} words; the language "
    "given; facts only). All spoken lines together at most {budget} words: the reel lasts about 20 seconds. "
    'Answer JSON only: {"beats": [{"screen": "...", "voice": "..."}], "why": "one line on the hook you chose"}'
)


@dataclass
class Guide:
    name: str
    data: Dict[str, Any]

    def __getitem__(self, k):
        return self.data[k]

    def get(self, k, default=None):
        return self.data.get(k, default)

    @property
    def slug(self) -> str:
        return self.data["slug"]

    @property
    def lang(self) -> str:
        return self.data.get("lang", "mr")

    @property
    def own_beats(self) -> List[Dict[str, str]]:
        return [{"screen": s["screen"], "voice": s["voice"]} for s in self.data["shots"]]

    def facts_text(self) -> str:
        return "\n".join(f"- {f}" for f in self.data["facts"])


def load(name: str, folder: Path = GUIDES) -> Guide:
    path = Path(folder) / f"{name}.json"
    return Guide(name, json.loads(path.read_text(encoding="utf-8")))


def _words(s: str) -> int:
    return len(str(s).replace("*", "").split())


def problems(beats: Any, guide: Guide) -> List[str]:
    """Why these beats cannot be used ([] = they can): one per shot, short screen and spoken lines, no number that is not in the
    facts (Devanagari digits read as Western ones), every must-say number said or shown, no phone number."""
    shots = guide["shots"]
    if not isinstance(beats, list) or len(beats) != len(shots):
        return [f"{len(beats) if isinstance(beats, list) else 0} beats for {len(shots)} shots"]
    beats = locked([b if isinstance(b, dict) else {} for b in beats], guide)   # judged as they will go out: locked lines are the guide's
    out: List[str] = []
    allowed = _director.numbers_in(guide.facts_text())
    said = set()
    for i, b in enumerate(beats, start=1):
        if not isinstance(b, dict) or not str(b.get("screen", "")).strip() or not str(b.get("voice", "")).strip():
            out.append(f"beat {i} is empty")
            continue
        screen, voice_ = str(b["screen"]), str(b["voice"])
        if _words(screen.replace("·", " ")) > MAX_SCREEN_WORDS:
            out.append(f"beat {i} screen too long")
        if _words(voice_) > MAX_VOICE_WORDS + 2:
            out.append(f"beat {i} voice too long")
        nums = _director.numbers_in(screen) | _director.numbers_in(voice_)
        if nums - allowed:
            out.append(f"beat {i} has numbers not in the facts: {sorted(nums - allowed)}")
        if re.search(r"\b[6-9]\d{9}\b", _director.western_digits(screen + voice_)) or "http" in voice_ + screen:
            out.append(f"beat {i} has a phone number or a link")
        said |= _director.numbers_in(voice_)   # must-say numbers are spoken as digits: a number spelt out in words ("बावीस") cannot be checked
    total, most = sum(_words(b.get("voice", "")) for b in beats if isinstance(b, dict)), guide.get("max_words", MAX_TOTAL_WORDS)
    if total > most:   # the count goes back to the editor: 'too long' alone did not get a shorter answer
        out.append(f"too many words for the reel's length: {total} spoken words, at most {most}")
    said_text = " ".join(f"{b.get('screen', '')} {b.get('voice', '')}" for b in beats if isinstance(b, dict)).lower()
    banned = [w for w in list(NEVER) + list(guide.get("never", [])) if w.lower() in said_text]
    if banned:
        out.append(f"promises a home or odds: {banned}")
    missing = [n for n in guide.get("must_say", []) if n not in said]
    if missing:
        out.append(f"must-say numbers missing: {missing}")
    text = " ".join(f"{b.get('screen', '')} {b.get('voice', '')}" for b in beats if isinstance(b, dict))
    lost = [w for w in guide.get("must_words", []) if w not in text]
    if lost:   # a date the facts call planned stays planned ('सोडत 4 डिसेंबरला होणार आहे' made it sound certain, 2026-10-17)
        out.append(f"must-keep words missing: {lost}")
    return out


def _brief(guide: Guide) -> str:
    shots = "\n".join(f"{i}. picture: {s['prompt']}\n   meaning: {s['voice']}" + (f"\n   screen fixed as: {s['screen']}" if s.get("lock") else "")
                      for i, s in enumerate(guide["shots"], start=1))
    keep = f"Words that must stay: {', '.join(guide.get('must_words', []))}\n" if guide.get("must_words") else ""
    return (f"Language: {LANGS.get(guide.lang, 'Marathi')}\nAudience: {guide.get('audience', '')}\n{keep}"
            f"The one message: {guide.get('message', '')}\nFacts:\n{guide.facts_text()}\nShots:\n{shots}")


def locked(beats: List[Dict[str, str]], guide: Guide) -> List[Dict[str, str]]:
    """A shot marked `"lock": true` keeps the guide's own screen and spoken lines, word for word: a date or time is said and shown
    exactly as checked. Live 2026-10-17 the editor swapped '22 ऑक्टोबर · रात्री 11:59' for 'फक्त 5 दिवस बाकी' on screen, then said
    'रात्री बारापर्यंत' for 11:59 pm and 'दुपारी ४' for 3:59 pm (the 4 passed the number check: '4 pm' was in another fact)."""
    return [{"screen": s["screen"], "voice": s["voice"]} if s.get("lock") else b for b, s in zip(beats, guide["shots"])]


async def write(guide: Guide, llm: Any = None) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    """(beats, note): the team's beats when they pass, else the guide's own; locked screen lines always the guide's. The note
    says who made them and what was refused."""
    beats, note = await _write(guide, llm)
    return locked(beats, guide), note


class _InOrder:
    """The team's models in a fixed order, the first usable answer wins (Gemini, our paid key, first: a free model's Marathi
    is weaker, and the shared client's round-robin can hand a script to the weakest one)."""

    def __init__(self, providers, temperature: float = 0.7):
        self.providers, self.temperature, self.answered = list(providers), temperature, ""

    async def json(self, system: str, user: str):
        for p in self.providers:
            try:
                r = await p.json(system, user, self.temperature)
            except Exception:
                r = None
            if r:
                self.answered = f"{getattr(p, 'host', '')} {getattr(p, 'model', '')}"
                return r
        return None


def team_llm() -> Optional[_InOrder]:
    import os

    from app.platform.llm import GEMINI_CRITICAL_MODEL, GEMINI_OPENAI_URL, GroqLLM, text_providers
    providers = [p for p in text_providers() if getattr(p, "url", "") != GEMINI_OPENAI_URL]
    if os.environ.get("GEMINI_API_KEY"):
        providers.insert(0, GroqLLM(os.environ["GEMINI_API_KEY"], model=os.environ.get("AI_CRITICAL_MODEL", GEMINI_CRITICAL_MODEL),
                                    url=GEMINI_OPENAI_URL, timeout=90.0))
    return _InOrder(providers) if providers else None


async def _write(guide: Guide, llm: Any = None) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    note: Dict[str, Any] = {"made_by": "guide", "refused": []}
    if llm is None:
        llm = team_llm()
    if llm is None:
        return guide.own_beats, note
    brief = _brief(guide)
    # the line limit follows the reel's budget: 14 words a line for 6 shots asked for 84, so no answer fitted 46 (2026-10-17)
    line = str(max(5, guide.get("max_words", MAX_TOTAL_WORDS) // len(guide["shots"])))
    drafts = await llm.json(WRITER.replace("{line}", line), brief)
    versions = [v.get("beats") for v in (drafts or {}).get("versions") or [] if isinstance(v, dict)]
    good = [v for v in versions if not problems(v, guide)]
    note["refused"] += [f"writer v{i + 1}: {'; '.join(problems(v, guide))}" for i, v in enumerate(versions) if problems(v, guide)]
    if versions:
        ask = f"{brief}\n\nWriter's versions:\n{json.dumps(versions, ensure_ascii=False)}"
        system = EDITOR.replace("{budget}", str(guide.get("max_words", MAX_TOTAL_WORDS) - 4)).replace("{line}", line)
        for _ in range(3):   # more goes with what was wrong and the word count (live 2026-10-17: 64, then 55 words for 46)
            edited = await llm.json(system, ask)
            beats = (edited or {}).get("beats")
            found = problems(beats, guide)
            if not found:
                return [{"screen": b["screen"].strip(), "voice": b["voice"].strip()} for b in beats], \
                       {**note, "made_by": "editor", "why": (edited or {}).get("why", ""), "model": getattr(llm, "answered", "")}
            note["refused"].append(f"editor: {'; '.join(found)}")
            ask += f"\n\nYour last answer was refused: {'; '.join(found)}. Fix exactly that.\n{json.dumps(beats, ensure_ascii=False)}"
    if good:
        return good[0], {**note, "made_by": "writer", "model": getattr(llm, "answered", "")}
    return guide.own_beats, note


@dataclass
class Prepared:
    beats: List[Dict[str, str]]
    note: Dict[str, Any]
    pictures: List[Optional[str]]     # uploads-relative, one per shot (None: the branded background)
    drawn: List[bool]                 # drawn by Gemini (carries SYMBOLIC on screen) or hand-made
    shots: List[dict] = field(default_factory=list)


def folder_of(slug: str, uploads: Path) -> Path:
    return Path(uploads) / SUBDIR / slug


async def prepare(guide: Guide, uploads: Path, llm: Any = None, say=lambda s: None) -> Prepared:
    """The team's words and one picture per shot (network calls only: cheap on the VM). The video is drawn later by the renderer
    (render_row), from what is stored on the row."""
    beats, note = await write(guide, llm)
    say(f"words by {note['made_by']}" + (f" ({note.get('why')})" if note.get("why") else ""))
    for r in note["refused"]:
        say(f"  refused: {r}")
    folder = folder_of(guide.slug, uploads)
    photos, shots = pictures.shots(folder, [s["prompt"] for s in guide["shots"]])
    for s in shots:
        say(f"  shot {s['shot']}: {s['from']}" + (f", refused before: {s['rejected']}" if s.get("rejected") else ""))
    rel = [Path(p).resolve().relative_to(Path(uploads).resolve()).as_posix() if p else None for p in photos]
    (folder / "words.json").write_text(json.dumps({"beats": beats, "note": note, "shots": shots}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    return Prepared(beats, note, rel, [s["from"] in ("drawn", "drawn earlier") for s in shots], shots)


def render(beats: Sequence[Dict[str, str]], photos: Sequence[Optional[Path]], drawn: Sequence[bool], out: Path, lang: str = "mr",
           gender: str = "female", music: Optional[str] = None, seed: str = "guide") -> Tuple[Path, float]:
    """The voiced reel: each scene lasts as long as its spoken line (at least MIN_SCENE). Voice only unless `music` names a mood
    (owner 2026-10-17 on the first guide reel: the music bed sounded like "tisss tisss"; no music)."""
    from app.modules.reels import ffmpeg
    work = Path(tempfile.mkdtemp(prefix="guide-"))
    clips = narration.spoken_lines([b["voice"] for b in beats], lang, gender, work)
    durs = stretch([max(MIN_SCENE, ffmpeg.probe(c).duration + 0.45) for c in clips], XFADE)
    badge = SYMBOLIC.get(lang, SYMBOLIC["en"])
    scenes = [Scene(image=photos[i], lines=[TextLine(b["screen"], size=100 if i == 0 else 92)], layout="lower",
                    badge=badge if drawn[i] else None, seconds=durs[i], seed=f"{seed}-{i}")
              for i, b in enumerate(beats)]
    tl = plan(durs, XFADE, max_total=60.0)
    bed = None
    if music:
        from app.modules.reels.music import write as write_music
        bed = write_music(work / "bed.wav", seconds=tl.total + 1.0, mood=music)
    audio = narration.mix(work, clips, tl.starts, tl.total, bed)
    return make_reel(scenes, out, music=audio, transition="fade", xfade=XFADE, max_seconds=60.0), tl.total


def render_row(doc: dict, uploads: Path) -> str:
    """Calendar hook (adapters.render_reel_for, run by the renderer before the row is due): the reel from the words and pictures
    stored on the row. The Instagram and Facebook rows share one file."""
    c = doc.get("creative") or {}
    slug = c.get("reel_key") or doc["slug"]
    dest = folder_of(slug, uploads) / "reel.mp4"
    if not (dest.is_file() and dest.stat().st_size > 0):
        photos = [Path(uploads) / p if p else None for p in c.get("pictures") or []]
        render(c["beats"], photos, c.get("drawn") or [False] * len(photos), dest, c.get("lang", "mr"), c.get("gender", "female"),
               c.get("music"), seed=slug)
    return dest.resolve().relative_to(Path(uploads).resolve()).as_posix()


async def schedule(store, guide: Guide, prep: Prepared, status: str = "approved") -> List[str]:
    """One row per channel, without a video (the renderer draws it before it is due); an existing row for the same slug and
    channel is left alone. Returns the ids added."""
    have = {(ch, s) for ch, s, _ in await store.existing()}
    due = datetime.fromisoformat(guide["due"])
    cover = next((p for p in prep.pictures if p), "")
    ids = []
    for ch in guide["channels"]:
        if (ch, guide.slug) in have:
            continue
        creative = {"role": "buyer", "source": "guide_reels", "template": "guide", "reel_key": guide.slug, "ref": guide.name,
                    "path": "guide", "layout": "reel", "ok": True, "hook": guide.get("hook") or prep.beats[0]["voice"],
                    "hook_type": guide.get("hook_type", "guide"), "lang": guide.lang, "gender": guide.get("gender", "female"),
                    "music": guide.get("music"), "audience": "buyers", "as_of": guide.get("as_of"), "beats": prep.beats,
                    "script": [b["voice"] for b in prep.beats], "pictures": prep.pictures, "drawn": prep.drawn,
                    "words_by": prep.note.get("made_by")}
        ids.append(await store.add(guide.slug, ch, guide["caption"], cover, due, kind="reel", status=status, images=[cover],
                                   creative=creative,
                                   extra={"reply_facts": guide.get("reply_facts", []), "reply_faq": guide.get("reply_faq", [])}))
    return ids
