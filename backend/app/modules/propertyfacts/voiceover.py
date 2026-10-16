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
The caption then opens with the same greeting in writing (Script.intro)."""
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
        "hello": (("नमस्कार दोस्तों!", "Namaskar dosto!"), ("हैलो पुणे!", "Hello Pune!"), ("नमस्ते दोस्तों, कैसे हो?", "Namaste dosto, kaise ho?")),
        "open": ("आज {who} की टीम आपको दिखा रही है {what}।", "Aaj {who} ki team aapko dikha rahi hai {what}."),
        "talk": ("Hinglish: Hindi in Devanagari script, with the English words Pune buyers use left in English letters (BHK, "
                 "price, MahaRERA, carpet area, possession, amenities, clubhouse, project names)"),
        "words": "देखिए, तो, मतलब, अच्छा, और हाँ",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'और यहाँ आपको मिलेगा gym, swimming pool, और parking भी।' "
                    "Screen: 'Airport: 0.9 km' -> 'Airport? [pause short] एक किलोमीटर से भी कम दूर है।' "
                    "Screen: '₹2.24 crore' -> 'अब price की बात करें, [pause short] तो 2.24 करोड़ से शुरू होता है।' "
                    "Screen: 'Designed by Hafeez Contractor' -> 'इसे design किया है Hafeez Contractor ने।'"),
        "place": "hi",
    },
    "en": {
        "label": "English", "tts": "en",
        "hello": (("Hello friends!", "Hello friends!"), ("Hello Pune!", "Hello Pune!"), ("Hi everyone!", "Hi everyone!")),
        "open": ("Today the {who} team is showing you {what}.", "Today the {who} team is showing you {what}."),
        "talk": "Indian English, the way a Pune property agent talks to friends",
        "words": "so, look, see, and yes",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'And you get a gym, a swimming pool, and parking too.' "
                    "Screen: 'Airport: 0.9 km' -> 'The airport? [pause short] Less than a kilometre away.' "
                    "Screen: '₹2.24 crore' -> 'Now the price. [pause short] It starts at 2.24 crore.'"),
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


def opening(c: Ctx, lang: str, n: int = 0) -> Tuple[str, str]:
    """(said, written): the host's greeting and who shows what, for reel `n` of the campaign."""
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
    return (f"{said_hello} {said_open.format(who=who, what=what(said_place))}",
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


async def script(s: ad_reel.Script, c: Ctx, lang: str, n: int = 0, llm: Any = None) -> Tuple[List[str], Dict[str, Any]]:
    """The reel's spoken lines with the host's opening before the first, and `s.intro` set to the written opening.
    ([lines], {"language", "by": "llm"|"template", "kept"})."""
    if lang not in LANGS:
        raise ValueError(f"unknown voice language {lang!r}")
    lines, kept = await spoken(s, lang, llm)
    said_open, written_open = opening(c, lang, n)
    lines[0] = f"{said_open} [pause] {lines[0]}"
    s.intro = written_open
    return lines, {"language": lang, "by": "llm" if kept else "template", "kept": kept}


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


def ask_ok(lang: Optional[str], gender: Optional[str]) -> Tuple[str, str]:
    """(language, gender) of a request, the defaults where missing; ValueError for an unknown one."""
    lang, gender = lang or DEFAULT_LANG, gender or DEFAULT_GENDER
    if lang not in LANGS or gender not in GENDERS:
        raise ValueError("Pick Hinglish, English or Marathi, and a female or male voice.")
    return lang, gender
