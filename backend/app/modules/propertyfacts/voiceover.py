"""The voice-over step: the marketing run makes its reels with our music only; a reel's voice is asked for afterwards, one
reel at a time from Studio, in Hinglish, English or Marathi, a female or a male voice (owner, 2026-10-16: the voice is the
last step, made on demand; Google's Chirp 3 HD on the server's key, no Gemini).

It talks like a person showing a project to friends, not like an ad read:
  opening  the host's greeting and who shows what, written by code, never by a model ("Namaskar dosto! Aaj Avasetu ki team
           aapko dikha rahi hai Lodha Camelot, Lohegaon."), the greeting rotated per reel so a campaign's reels do not open
           alike; no time of day (a reel goes out at another hour than it is made). "dikha rahi hai" agrees with "team", so it
           is right whoever speaks.
  lines    the model says each screen line the way a person talks over that picture: short sentences, the small spoken words
           of the language ("dekhiye", "matlab", "बघा") and pause tags ([pause short] before a price, [pause] between two
           thoughts). A line is kept only when it keeps to its screen line's facts (ad_reel.said_ok on the line without its
           tags); otherwise the screen line itself is read (ad_reel.spoken).
  voice    each line one Chirp 3 HD request (reels.voice.synth_spoken), a little slower than a read; "Avasetu" is said
           a-va-SAY-too and Pune's names as Pune says them (voice.NAMES).
The caption then opens with the same greeting in writing (Script.intro).

Two styles (owner, 2026-10-16: "a story with facts when needed", reels that touch):
  story    (the default) the voice talks to ONE viewer: a hook that names a feeling or problem the facts answer ("Roz do ghante
           traffic mein?" when an IT park is near), a small "socho..." day-in-the-life over the pictures, a key fact said
           plainly where its picture is, what the team checked as trust, a warm invite to comment INFO. Every number, name,
           distance and amenity must be in the reel's facts (story_ok); never an invented buyer, quote, sale or scarcity.
  facts    each screen line said the way a person says it (line_ok), as before.
The greeting is said slower and warmer, as its own piece ("Naaamaste dostooo..."), before the rest (reels.voice.synth_greeting)."""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core import brand
from app.modules.creative import i18n

from . import ad_reel
from .campaign import Ctx

log = logging.getLogger(__name__)

GENDERS = ("female", "male")
# per choice: the voice's language (reels.voice.VOICES), the greetings (said, written), the opening (said, written) and how the
# model should talk
LANGS: Dict[str, Dict[str, Any]] = {
    "hinglish": {
        "label": "Hinglish", "tts": "hi",
        "hello": (("नमस्ते दोस्तों!", "Namaste dosto!"), ("नमस्कार दोस्तों!", "Namaskar dosto!"), ("हैलो दोस्तों!", "Hello dosto!")),
        "open": ("आज {who} की टीम आपको दिखा रही है {what}।", "Aaj {who} ki team aapko dikha rahi hai {what}."),
        "talk": ("Hinglish: Hindi in Devanagari script, with the English words Pune buyers use left in English letters (BHK, "
                 "price, MahaRERA, carpet area, possession, amenities, clubhouse, project names)"),
        "words": "देखिए, तो, मतलब, अच्छा, और हाँ",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'और यहाँ आपको मिलेगा gym, swimming pool, और parking भी।' "
                    "Screen: 'Airport: 0.9 km' -> 'Airport? [pause short] एक किलोमीटर से भी कम दूर है।' "
                    "Screen: '₹2.24 crore' -> 'अब price की बात करें, [pause short] तो 2.24 करोड़ से शुरू होता है।' "
                    "Screen: 'Designed by Hafeez Contractor' -> 'इसे design किया है Hafeez Contractor ने।'"),
        "story": ("hook: 'रोज़ ऑफिस के traffic में दो घंटे? [pause short] सोचिए, अगर ऑफिस पास ही हो।' "
                  "line 'Gym, Swimming pool and Parking': 'सोचिए, [pause short] सुबह gym, शाम को swimming pool, और parking की कोई टेंशन नहीं।' "
                  "line '₹2.24 crore': 'और price? [pause short] 2.24 करोड़ से शुरू।' "
                  "line 'Checked by the Avasetu team: ...': 'और हाँ, MahaRERA record हमारी टीम ने खुद पढ़ा है, और distances Google Maps से check किए हैं।' "
                  "last: 'अगर दिल करे, तो comment में INFO लिखिए, हम सारी details भेज देंगे।'"),
        "place": "hi",
    },
    "en": {
        "label": "English", "tts": "en",
        "hello": (("Hello friends!", "Hello friends!"), ("Hello Pune!", "Hello Pune!"), ("Hey friends!", "Hey friends!")),
        "open": ("Today the {who} team is showing you {what}.", "Today the {who} team is showing you {what}."),
        "talk": "Indian English, the way a Pune property agent talks to friends",
        "words": "so, look, see, and yes",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'And you get a gym, a swimming pool, and parking too.' "
                    "Screen: 'Airport: 0.9 km' -> 'The airport? [pause short] Less than a kilometre away.' "
                    "Screen: '₹2.24 crore' -> 'Now the price. [pause short] It starts at 2.24 crore.'"),
        "story": ("hook: 'Two hours in office traffic, every day? [pause short] Imagine your office was right next door.' "
                  "line 'Gym, Swimming pool and Parking': 'Imagine it. [pause short] A morning workout, an evening swim, and no parking worries.' "
                  "line '₹2.24 crore': 'And the price? [pause short] It starts at 2.24 crore.' "
                  "line 'Checked by the Avasetu team: ...': 'And yes, our team read the MahaRERA record itself, and checked the distances on Google Maps.' "
                  "last: 'If it feels right, comment INFO, and we will send you every detail.'"),
        "place": "",
    },
    "mr": {
        "label": "Marathi", "tts": "mr",
        "hello": (("नमस्कार मंडळी!", "नमस्कार मंडळी!"), ("नमस्कार पुणेकरांनो!", "नमस्कार पुणेकरांनो!"),
                  ("नमस्कार मित्रांनो!", "नमस्कार मित्रांनो!")),
        "open": ("आज {who} टीम तुम्हाला दाखवत आहे {what}.", "आज {who} टीम तुम्हाला दाखवत आहे {what}."),
        "talk": ("Marathi in Devanagari script, with the English property words left in English letters (BHK, MahaRERA, "
                 "carpet area, possession, amenities, project names)"),
        "words": "बघा, म्हणजे, तर, आणि हो",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'आणि इथे gym, swimming pool, आणि parking सुद्धा आहे.' "
                    "Screen: 'Airport: 0.9 km' -> 'Airport? [pause short] एक किलोमीटरपेक्षाही कमी अंतरावर.' "
                    "Screen: '₹2.24 crore' -> 'आता किंमत बघा, [pause short] 2.24 कोटींपासून सुरू होते.'"),
        "story": ("hook: 'रोज ऑफिसच्या traffic मध्ये दोन तास? [pause short] विचार करा, ऑफिस जवळच असेल तर.' "
                  "line 'Gym, Swimming pool and Parking': 'विचार करा, [pause short] सकाळी gym, संध्याकाळी swimming pool, आणि parking चं टेन्शन नाही.' "
                  "line '₹2.24 crore': 'आणि किंमत? [pause short] 2.24 कोटींपासून सुरू.' "
                  "line 'Checked by the Avasetu team: ...': 'आणि हो, MahaRERA record आमच्या टीमने स्वतः वाचलं आहे, आणि अंतर Google Maps वर तपासलं आहे.' "
                  "last: 'मनात आलं तर comment मध्ये INFO लिहा, आम्ही सगळी माहिती पाठवू.'"),
        "place": "mr",
    },
}
DEFAULT_LANG, DEFAULT_GENDER = "hinglish", "female"
FILLERS = sorted({w.strip() for spec in LANGS.values() for w in spec["words"].split(",")}, key=len, reverse=True)
TRAILING_FILLER = re.compile(r"(?:\s*\[pause(?: short)?\])*[\s,]*(?<!\S)(?:" + "|".join(re.escape(w) for w in FILLERS)
                             + r")[\s,.!।?]*$", re.I)
WRITTEN_BRAND = {"mr": "अवासेतू"}   # the brand as a Marathi caption writes it (said a-va-SAY-too)

SYSTEM = (
    "You are a Pune property creator recording the voice-over of a short reel about one project: you talk to friends, you do "
    "not read an ad. For each screen line, in the same order, write what you SAY over that picture, in {talk}. "
    "Each line is one or two complete, grammatical sentences a person would really say, in your own words: never a "
    "word-by-word translation of the screen text, never a slogan or a fragment. Talk like a person: short sentences, "
    "now and then a small spoken word ({words}) at the START of a sentence (never at its end, never alone), now and then "
    "a question to the listener. Mark pauses with these tags only, inside a line, never at its end: [pause short] for a "
    "breath (before a price or a number, after a question), [pause] between two thoughts; at most two tags in a line. "
    "Examples: {example} "
    "Keep every fact and name of its line and add none: no number, price, distance or name that is not on the line. "
    "Distances as people say them (0.9 km: less than a kilometre; 3.9 km: about 4 kilometres), prices as written with "
    "Western digits (2.24 crore), no registration numbers (say MahaRERA registered), no hype (best, luxury, dream, "
    "guaranteed), no only/just/sirf/फक्त, no forecast of prices or returns. "
    "A greeting is said just before the first line, so do not greet. A line 'Checked by the X team: ...' says that X team "
    "checked those things. The last line asks to comment INFO for the details. "
    'Reply with JSON only: {{"lines": ["...", ...]}}')


STORY_SYSTEM = (
    "You are a warm Pune property creator recording the voice-over of a short reel that touches people: you speak to ONE "
    "viewer as a friend, never to a crowd, never like an ad. The reel's pictures and their screen lines are fixed; you write "
    "what you SAY, in {talk}. "
    "hook: one short line (at most 14 words) that names a real feeling or everyday problem of the buyer this project fits, "
    "chosen from the facts only (a long commute when an office or IT park is near, a growing family when it has 3 BHK or "
    "more, the search for a first home, a quiet place after work); it may be a question; no number in it. "
    "lines: one per screen line, in the same order. Tell a small 'imagine...' story of a day living there with the facts of "
    "that line; where a line carries a key fact (price, size, distance, number of homes, MahaRERA), say that fact clearly "
    "and exactly as given. The 'Checked by the X team: ...' line says plainly what that team checked, as trust. The last "
    "line is a warm personal invite to comment INFO for the details, with no pressure. "
    "Rules: every number, name, distance, price and amenity you say must be in the facts; never invent a person, a family, "
    "a buyer, a quote, a sale, 'few left' or any urgency; no visit or check except those in the facts; no hype (best, luxury, "
    "dream, perfect, guaranteed), no only/just/sirf/फक्त, no forecast of prices or returns. Complete natural sentences; small "
    "spoken words ({words}) only at the START of a sentence; pause tags [pause short] and [pause] inside a line only, at "
    "most two in a line; each line at most 25 words. Distances as people say them (3.9 km: about 4 kilometres), prices "
    "with Western digits. A greeting and the project's name are said just before your hook's end, so do not greet. "
    "Examples: {story} "
    'Reply with JSON only: {{"hook": "...", "lines": ["...", ...]}}')
DIRECTOR_SYSTEM = (
    "You direct voice-overs for Instagram reels of Indian homes; the reels that touch people are your job. You get the "
    "reel's facts, its screen lines and a draft voice-over (a hook and one line per screen line) in {talk}. Make it touch: "
    "the hook names a real feeling of THIS reel's viewer in under 2 seconds; the lines flow as one small story spoken to one "
    "person, each picture adding something; a key fact is said clearly where its picture is; the end is warm, inviting, "
    "never pushy. Fix what is flat, stiff, translated word by word, a fragment, repeated, or too long (at most 25 words a "
    "line). Keep the same number of lines in the same order, keep every fact exactly, add no number, name or claim that "
    "is not in the facts, no invented buyers, sales or urgency, no hype, no only/just/sirf. Pause tags [pause short] and "
    "[pause] inside lines only, at most two a line. The last line asks to comment INFO. "
    "Then pick the background music's mood for this reel: calm (a story that touches, a home for a family), warm (a "
    "friendly showcase), or lively (a launch, a price or an offer). "
    'Reply with JSON only: {{"hook": "...", "lines": ["...", ...], "mood": "calm|warm|lively"}}')
MOODS = ("calm", "warm", "lively")
STYLES = ("story", "facts")
DEFAULT_STYLE = "story"
# what nobody may claim in a story: buyers, sales, scarcity, a quote
INVENTED = re.compile(r"(?:sold|booked|bookings?|buyers? (?:love|said|have)|famil(?:y|ies) (?:have|already)|clients?|customers?|"
                      r"few (?:left|units)|limited|hurry|last chance|testimonial)|बिक|बुक|ग्राहक|जल्दी करें|सीमित|"
                      r"विकल|खरेदीदार", re.I)


def opening(c: Ctx, lang: str, n: int = 0) -> Tuple[str, str, str]:
    """(greeting said, who shows what said, both written): the host's opening for reel `n` of the campaign."""
    spec = LANGS[lang]
    said_hello, written_hello = spec["hello"][n % len(spec["hello"])]
    place = (c.locality or "").split(",")[0].strip()
    # Lohegaon as Marathi/Hindi spell it, for their voice (it then says it right); a Marathi caption writes it so too
    said_place = i18n.PLACES.get(place, {}).get(spec["place"], place) if spec["place"] else place
    written_place = said_place if lang == "mr" else place
    what = lambda p: ", ".join(x for x in (c.project, p) if x) or c.where or "this project"   # noqa: E731
    who = c.voice.name or brand.NAME
    said_open, written_open = spec["open"]
    written_who = WRITTEN_BRAND.get(lang, who) if who == brand.NAME else who
    return (said_hello, said_open.format(who=who, what=what(said_place)),
            f"{written_hello} 🙏 {written_open.format(who=written_who, what=what(written_place))}")


def _tidy(line: str) -> str:
    """A model's line with only our pause tags ([pause long] made [pause]) and at most two of them."""
    from app.modules.reels.voice import spoken_markup
    t = spoken_markup(line.replace("[pause long]", "[pause]"))
    # a filler left hanging at the end ("... registered [pause] अच्छा") and pause tags at the end go: a person stops there
    t = TRAILING_FILLER.sub("", t).strip()
    t = re.sub(r"(?:\s*\[pause(?: short)?\])+\s*$", "", t).strip()
    n = 0

    def keep(m: "re.Match") -> str:
        nonlocal n
        n += 1
        return m.group(0) if n <= 2 else ""
    return " ".join(re.sub(r"\[pause(?: short)?\]", keep, t).split())


# a check or a visit nobody made: "our team visited", "verified", "hum gaye the", "भेट दिली"
CLAIMED_WORK = re.compile(r"\bvisit|\bverif|\bsite\s+(?:dekh|par\s+gaye)|\bgaye\s+the\b|\bwent\s+to\b|"
                          r"भेट|गए\s+थे|गेलो|वेरिफ|सत्यापि", re.I)


def line_ok(said: str, screen: str, last: bool = False) -> bool:
    """A spoken line keeps to its screen line (ad_reel.said_ok, read without its pause tags), claims no visit or
    verification the screen line does not, and the last one still asks for INFO."""
    from app.modules.reels.voice import unpaused
    t = unpaused(said)
    if not t or (CLAIMED_WORK.search(t) and not CLAIMED_WORK.search(screen)):
        return False
    if last and ad_reel.CTA_WORD not in t:
        return False
    return ad_reel.said_ok(t, screen, most=max(3 * len(screen.split()) + 8, 18))   # a sentence said, not the caption


def _allowed(facts: str) -> set:
    """The numbers a line may say: those in the facts, and each rounded the way people say it (3.9 -> 4)."""
    from .campaign import _numbers
    shown = [float(x) for x in _numbers(facts) if re.fullmatch(r"\d+(?:\.\d+)?", x)]
    return set(_numbers(facts)) | {str(round(x)) for x in shown} | {str(int(x) + 1) for x in shown}


def story_ok(said: str, facts: str, last: bool = False, most: int = 30) -> bool:
    """A story line keeps to the reel's facts: no number, price or name outside them (rounded distances allowed), no guard
    problem, no invented buyer, sale or urgency, no visit or check the facts do not name; the last one asks for INFO."""
    from app.modules.creative.guards import problems_in
    from app.modules.reels.voice import unpaused

    from .campaign import _numbers
    t = unpaused(said)
    if not t or len(t.split()) > most or INVENTED.search(t):
        return False
    if CLAIMED_WORK.search(t) and not CLAIMED_WORK.search(facts):
        return False
    if last and ad_reel.CTA_WORD not in t:
        return False
    said_n = set(_numbers(t))
    if said_n - _allowed(facts):
        return False
    rounded = said_n - set(_numbers(facts))
    return not [p for p in problems_in(t, facts) if p.removeprefix("number not in facts: ") not in rounded]


async def story(s: ad_reel.Script, c: Ctx, lang: str, llm: Any = None) -> Tuple[str, List[str], int, str]:
    """(hook, one spoken line per screen line, how many the model wrote that passed, music mood) in the story style, written
    like an ad team: the writer drafts, the director makes it touch and picks the music. A line that fails `story_ok` is said
    as in the facts style (line_ok) when that passes, else as its screen line."""
    screens = [x.replace("*", "") for x in s.lines()]
    facts = " | ".join([ad_reel.corpus(c), *screens])
    about = f"This reel is about: {screens[0]} ({s.format.replace('_', ' ')})"   # each reel's own subject: its story differs
    lines_in = "Screen lines:\n" + "\n".join(f"- {x}" for x in screens)

    def take(r: Any) -> Tuple[str, List[str]]:
        r = r if isinstance(r, dict) else {}
        said = [_tidy(str(x)) for x in r.get("lines") or []]
        return _tidy(str(r.get("hook") or "")), said if len(said) == len(screens) else []

    def judge(hook: str, said: List[str]) -> Tuple[str, List[str], int]:
        """The draft with every line that fails the checks said plainly instead, and how many of the model's lines stayed."""
        hook = hook if hook and story_ok(hook, facts, most=18) else ""
        out, kept = [], 0
        for i, screen in enumerate(screens):
            last = i == len(screens) - 1
            if i < len(said) and (story_ok(said[i], facts, last=last) or line_ok(said[i], screen, last=last)):
                out.append(said[i])
                kept += 1
            else:
                out.append(ad_reel.spoken(screen))
        return hook, out, kept + bool(hook)

    best, mood = judge("", []), "warm"
    if llm is None:
        return (*best, mood)
    spec = LANGS[lang]
    try:   # the writer's draft
        hook, said = take(await llm.json(STORY_SYSTEM.format(talk=spec["talk"], words=spec["words"], story=spec["story"]),
                                         f"Facts: {facts}\n{about}\n{lines_in}"))
        best = judge(hook, said)
    except Exception:
        log.info("voice-over: story failed", exc_info=True)
        return (*best, mood)
    try:   # the director's pass: kept when as many of its lines pass the checks
        draft = "Draft:\n" + json.dumps({"hook": hook, "lines": said}, ensure_ascii=False)
        r = await llm.json(DIRECTOR_SYSTEM.format(talk=spec["talk"]), f"Facts: {facts}\n{about}\n{lines_in}\n{draft}")
        mood = str((r or {}).get("mood") or "").strip().lower() if isinstance(r, dict) else ""
        mood = mood if mood in MOODS else "warm"
        directed = judge(*take(r))
        if directed[2] >= best[2]:
            best = directed
    except Exception:
        log.info("voice-over: director pass failed, the draft kept", exc_info=True)
    return (*best, mood)


async def spoken(s: ad_reel.Script, lang: str, llm: Any = None) -> Tuple[List[str], int]:
    """(one spoken line per screen line, how many the model wrote that passed): the model's where `line_ok`, else the
    screen line as the voice says it (ad_reel.spoken)."""
    screens = [x.replace("*", "") for x in s.lines()]
    said: List[str] = []
    if llm is not None:
        spec = LANGS[lang]
        try:
            r = await llm.json(SYSTEM.format(talk=spec["talk"], words=spec["words"], example=spec["example"]),
                               "Screen lines:\n" + "\n".join(f"- {x}" for x in screens)) or {}
            said = [_tidy(str(x)) for x in r.get("lines") or []]
        except Exception:
            log.info("voice-over: spoken lines failed", exc_info=True)
        if len(said) != len(screens):
            said = []
    out, kept = [], 0
    for i, screen in enumerate(screens):
        if i < len(said) and line_ok(said[i], screen, last=i == len(screens) - 1):
            out.append(said[i])
            kept += 1
        else:
            out.append(ad_reel.spoken(screen))
    return out, kept


async def script(s: ad_reel.Script, c: Ctx, lang: str, n: int = 0, llm: Any = None,
                 style: str = DEFAULT_STYLE) -> Tuple[List[str], Dict[str, Any]]:
    """The reel's spoken lines with the host's opening in the first (the greeting marked «...» to be said slower), and
    `s.intro` set to the written opening. ([lines], {"language", "style", "by": "llm"|"template", "kept", "hook"})."""
    if lang not in LANGS:
        raise ValueError(f"unknown voice language {lang!r}")
    hello, said_open, written_open = opening(c, lang, n)
    if style == "story":
        hook, lines, kept, mood = await story(s, c, lang, llm)
        first = " [pause] ".join(x for x in (hook, said_open, lines[0]) if x)
    else:
        hook, mood, (lines, kept) = "", "warm", await spoken(s, lang, llm)
        first = f"{said_open} [pause] {lines[0]}"
    lines[0] = f"«{hello}» {first}"
    s.intro = written_open
    return lines, {"language": lang, "style": style, "by": "llm" if kept else "template", "kept": kept, "hook": hook,
                   "mood": mood}


SAMPLE = {"mr": "लोढा कॅमलॉट, लोहगाव"}   # the sample project of the options, as each language writes it


def choices() -> List[Dict[str, str]]:
    """The options Studio shows: each language with an opening as it sounds (for a sample project)."""
    out = []
    for key, spec in LANGS.items():
        hello, open_ = spec["hello"][0][1], spec["open"][1]
        what = SAMPLE.get(key, "Lodha Camelot, Lohegaon")
        out.append({"key": key, "label": spec["label"],
                    "sample": f"{hello} {open_.format(who=WRITTEN_BRAND.get(key, brand.NAME), what=what)}"})
    return out


def tts_lang(lang: str) -> str:
    return LANGS[lang]["tts"]


def ask_ok(lang: Optional[str], gender: Optional[str], style: Optional[str] = None) -> Tuple[str, str, str]:
    """(language, gender, style) of a request, the defaults where missing; ValueError for an unknown one."""
    lang, gender, style = lang or DEFAULT_LANG, gender or DEFAULT_GENDER, style or DEFAULT_STYLE
    if lang not in LANGS or gender not in GENDERS or style not in STYLES:
        raise ValueError("Pick Hinglish, English or Marathi, a female or male voice, and Story or Facts.")
    return lang, gender, style
