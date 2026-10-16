"""The voice-over step: the marketing run makes its reels with our music only; a reel's voice is asked for afterwards, one
reel at a time from Studio, in Hinglish, English or Marathi, a female or a male voice (owner, 2026-10-16: the voice is the
last step, made on demand; Google's Chirp 3 HD on the server's key, no Gemini).

It talks like a person showing a project to friends, not like an ad read:
  opening  the host's greeting and who shows what, written by code, never by a model ("Namaskar dosto! Aaj Avasetu ki team
           aapko dikha rahi hai Lodha Camelot, Lohegaon."), the greeting rotated per reel so a campaign's reels do not open
           alike; no time of day (a reel goes out at another hour than it is made). "dikha rahi hai" agrees with "team", so it
           is right whoever speaks.
  lines    the model says each screen line the way a person talks over that picture, never the screen text read out or
           pasted in: short sentences, the small spoken words of the language ("dekhiye", "matlab", "बघा") at a sentence's
           start, pause tags ([pause short] before a price, [pause] between two thoughts). Every line is checked against the
           reel's facts (story_ok / line_ok): numbers with their units, only distances rounded, only the checks the team
           made, no invented buyers, sales or urgency. A scene with no line that passes says the code's sentence (the
           price, the checks, the comment ask: `fixed`) or nothing (its music plays).
  voice    each line one Chirp 3 HD request (reels.voice.synth_spoken), Hindi and Marathi slower than English; our names in
           Devanagari for a Hindi or Marathi voice ("अवास सेतु": AvaS-Setu, "खराडी": khar-aa-di, voice.for_voice).
  models   DeepSeek V3.2 first, in a fixed order (`writer_llm`): the shared client's round-robin gave weak free models.
The caption then opens with the same greeting in writing (Script.intro).

Two styles (owner, 2026-10-16: "a story with facts when needed", reels that touch):
  story    (the default) the voice talks to ONE viewer: a hook of one idea (at most 8 words, no number, no project name:
           "बड़े परिवार के लिए जगह चाहिए?"), a small "socho..." day-in-the-life over the pictures, a key fact said plainly
           where its picture is, what the team checked as trust, a warm invite to comment INFO. The writer drafts; the
           editor keeps each line or rewrites it when it is unclear on first hearing, and picks the music's mood; each
           scene takes the editor's line, else the writer's, when it passes (the report says which).
  facts    each screen line said the way a person says it (line_ok), as before.
The greeting is said slower, in the same voice, as its own piece ("Naaamaste dostooo..."), before the rest
(reels.voice.synth_greeting)."""
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
        "open": ("{what}।", "Aaj {who} ki team aapko dikha rahi hai {what}."),   # said short: reels under 20 s (owner)
        "talk": ("Hinglish: Hindi in Devanagari script, with the English words Pune buyers use left in English letters (BHK, "
                 "price, MahaRERA, carpet area, possession, amenities, clubhouse, project names)"),
        "words": "देखिए, तो, मतलब, अच्छा, और हाँ",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'और यहाँ आपको मिलेगा gym, swimming pool, और parking भी।' "
                    "Screen: 'Airport: 0.9 km' -> 'Airport? [pause short] एक किलोमीटर से भी कम दूर है।' "
                    "Screen: '₹2.24 crore' -> 'अब price की बात करें, [pause short] तो 2.24 करोड़ से शुरू होता है।' "
                    "Screen: 'Designed by Hafeez Contractor' -> 'इसे design किया है Hafeez Contractor ने।'"),
        "story": ("hook: 'ऑफिस के पास घर चाहिए?' "
                  "line 'Gym, Swimming pool and Parking': 'सोचिए, [pause short] सुबह gym, शाम को swimming pool, और parking की कोई टेंशन नहीं।' "
                  "line '₹2.24 crore': 'और price? [pause short] 2.24 करोड़ से शुरू।' "
                  "line 'Checked by the Avasetu team: ...': 'और हाँ, MahaRERA record हमारी टीम ने खुद पढ़ा है, और distances Google Maps से check किए हैं।' "
                  "last: 'Price list और floor plans चाहिए? Comment में INFO लिखिए, हम भेज देंगे।'"),
        "place": "hi",
    },
    "en": {
        "label": "English", "tts": "en",
        "hello": (("Hello friends!", "Hello friends!"), ("Hello Pune!", "Hello Pune!"), ("Hey friends!", "Hey friends!")),
        "open": ("{what}.", "Today the {who} team is showing you {what}."),
        "talk": "Indian English, the way a Pune property agent talks to friends",
        "words": "so, look, see, and yes",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'And you get a gym, a swimming pool, and parking too.' "
                    "Screen: 'Airport: 0.9 km' -> 'The airport? [pause short] Less than a kilometre away.' "
                    "Screen: '₹2.24 crore' -> 'Now the price. [pause short] It starts at 2.24 crore.'"),
        "story": ("hook: 'Want a home near your office?' "
                  "line 'Gym, Swimming pool and Parking': 'Imagine it. [pause short] A morning workout, an evening swim, and no parking worries.' "
                  "line '₹2.24 crore': 'And the price? [pause short] It starts at 2.24 crore.' "
                  "line 'Checked by the Avasetu team: ...': 'And yes, our team read the MahaRERA record itself, and checked the distances on Google Maps.' "
                  "last: 'Want the price list and floor plans? Comment INFO and we will send them.'"),
        "place": "",
    },
    "mr": {
        "label": "Marathi", "tts": "mr",
        "hello": (("नमस्कार मंडळी!", "नमस्कार मंडळी!"), ("नमस्कार पुणेकरांनो!", "नमस्कार पुणेकरांनो!"),
                  ("नमस्कार मित्रांनो!", "नमस्कार मित्रांनो!")),
        "open": ("{what}.", "आज {who} टीम तुम्हाला दाखवत आहे {what}."),
        "talk": ("Marathi in Devanagari script, with the English property words left in English letters (BHK, MahaRERA, "
                 "carpet area, possession, amenities, project names)"),
        "words": "बघा, म्हणजे, तर, आणि हो",
        "example": ("Screen: 'Gym, Swimming pool and Parking' -> 'आणि इथे gym, swimming pool, आणि parking सुद्धा आहे.' "
                    "Screen: 'Airport: 0.9 km' -> 'Airport? [pause short] एक किलोमीटरपेक्षाही कमी अंतरावर.' "
                    "Screen: '₹2.24 crore' -> 'आता किंमत बघा, [pause short] 2.24 कोटींपासून सुरू होते.'"),
        "story": ("hook: 'ऑफिसजवळ घर हवंय?' "
                  "line 'Gym, Swimming pool and Parking': 'विचार करा, [pause short] सकाळी gym, संध्याकाळी swimming pool, आणि parking चं टेन्शन नाही.' "
                  "line '₹2.24 crore': 'आणि किंमत? [pause short] 2.24 कोटींपासून सुरू.' "
                  "line 'Checked by the Avasetu team: ...': 'आणि हो, MahaRERA record आमच्या टीमने स्वतः वाचलं आहे, आणि अंतर Google Maps वर तपासलं आहे.' "
                  "last: 'Price list आणि floor plans हवेत? Comment मध्ये INFO लिहा, आम्ही पाठवू.'"),
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
    "checked those things. The last line asks to comment INFO for the price list and floor plans. "
    'Reply with JSON only: {{"lines": ["...", ...]}}')


STORY_SYSTEM = (
    "You are a warm Pune property creator recording the voice-over of a short reel that touches people: you speak to ONE "
    "viewer as a friend, never to a crowd, never like an ad. The reel's pictures and their screen lines are fixed; you write "
    "what you SAY, in {talk}. The screen text is already on screen for people watching muted: never repeat it, never "
    "translate it word by word, never paste English slogans into your line; say what it means for the viewer's life in "
    "fresh words of your own. "
    "hook: one short, clear line (at most 8 words, ONE idea) that names a real feeling or everyday problem of the buyer this "
    "project fits, chosen from the facts only (a long commute when an office or IT park is near, a growing family when it "
    "has 3 BHK or more, the search for a first home, a quiet place after work); it may be a question; no number and no "
    "project name in it (the name is said right after it). "
    "The reel lasts under 20 seconds, so the WHOLE voice-over (hook and lines together) is at most {budget} words: speak "
    "only the hook, the key facts (the price, the BHK or size, one distance or MahaRERA) and the last line; give an empty "
    "string \"\" for every other screen line (its text and the music carry it). "
    "lines: one per screen line, in the same order. Tell a small 'imagine...' story of a day living there with the facts of "
    "that line; where a line carries a key fact (price, size, distance, number of homes, MahaRERA), say that fact clearly "
    "and exactly as given. The 'Checked by the X team: ...' line says plainly what that team checked, as trust. The last "
    "line is a warm personal invite to comment INFO for the price list and floor plans, with no pressure. "
    "Rules: every number, name, distance, price and amenity you say must be in the facts; never invent a person, a family, "
    "a buyer, a quote, a sale, 'few left' or any urgency; no visit or check except those in the facts; describe no quality "
    "the facts do not state (airy, spacious, quiet, peaceful, green, well-lit); no hype (best, luxury, "
    "dream, perfect, guaranteed), no only/just/sirf/फक्त, no forecast of prices or returns. Complete natural sentences; small "
    "spoken words ({words}) only at the START of a sentence; pause tags [pause short] and [pause] inside a line only, at "
    "most two in a line; each line one or two short sentences, at most 18 words, each sentence clear on first hearing "
    "(a listener cannot read it again). Distances as people say them (3.9 km: about 4 kilometres), prices "
    "with Western digits. A greeting and the project's name are said just before your hook's end, so do not greet. "
    "Examples: {story} "
    'Reply with JSON only: {{"hook": "...", "lines": ["...", ...]}}')
DIRECTOR_SYSTEM = (
    "You are the script editor of Instagram reels of Indian homes. You get the reel's facts, its screen lines and a draft "
    "voice-over (a hook and one line per screen line) in {talk}. Read every line as a listener who hears it once: is it "
    "clear on first hearing, grammatical, natural spoken {talk}, one or two short sentences, at most 18 words? If yes, "
    "return it UNCHANGED. If not (unclear, a run-on, odd word order, stiff, translated word by word, a fragment, too "
    "long), rewrite it so it is, keeping its facts. The hook: at most 8 words, ONE clear idea, no project name, no number. "
    "Keep the whole voice-over at most {budget} words (empty strings for the lines left silent are right). "
    "Keep the same number of lines in the same order, keep every fact exactly, add no number, name or claim that "
    "is not in the facts, no quality the facts do not state (airy, spacious, quiet, peaceful), no invented buyers, sales or "
    "urgency, no hype, no only/just/sirf. Pause tags [pause short] and "
    "[pause] only after a comma, a question or a sentence, at most two a line. The last line asks to comment INFO for the price list and floor plans. Keep the draft's language and "
    "script; never paste the English screen text into a line, never say a registration number or a list number "
    "(1, 2, 3), never 'dream home'; say 'check' for what the team did, never 'verify'. "
    "Then pick the background music's mood for this reel: calm (a story that touches, a home for a family), warm (a "
    "friendly showcase), or lively (a launch, a price or an offer). "
    'Reply with JSON only: {{"hook": "...", "lines": ["...", ...], "mood": "calm|warm|lively"}}')
MOODS = ("calm", "warm", "lively")
# when a story line fails its checks: the price and the checks are said by code in the language; any other scene is a
# breath of music (the English screen text read by a Hindi voice sounded wrong, live 2026-10-16)
FIXED = {
    "hinglish": {"cta": "Price list और floor plans के लिए comment में INFO लिखिए।", "price": "और price, {price} से शुरू।",
                 "both": "{team} ने MahaRERA record पढ़ा है, और distances Google Maps से check की हैं।",
                 "MahaRERA record read": "{team} ने MahaRERA record पढ़ा है।",
                 "distances from Google Maps": "{team} ने distances Google Maps से check की हैं।"},
    "en": {"cta": "Comment INFO for the price list and floor plans.", "price": "And the price starts at {price}.",
           "both": "The {team} has read the MahaRERA record and checked the distances on Google Maps.",
           "MahaRERA record read": "The {team} has read the MahaRERA record.",
           "distances from Google Maps": "The {team} has checked the distances on Google Maps."},
    "mr": {"cta": "Price list आणि floor plans साठी comment मध्ये INFO लिहा.", "price": "आणि किंमत {price} पासून सुरू.",
           "both": "{team}ने MahaRERA record वाचलं आहे, आणि अंतर Google Maps वर तपासलं आहे.",
           "MahaRERA record read": "{team}ने MahaRERA record वाचलं आहे.",
           "distances from Google Maps": "{team}ने अंतर Google Maps वर तपासलं आहे."},
}
# words the whole voice-over may have (Hindi/Marathi ~2.5 words a second, English ~2.7): with the greeting and the project's
# name, a reel stays under 20 seconds (owner 2026-10-16: "ours should be less than 20 s")
BUDGET = {"hinglish": 30, "en": 34, "mr": 28}
STYLES = ("story", "facts")
DEFAULT_STYLE = "story"
# what nobody may claim in a story: buyers, sales, scarcity, a quote
INVENTED = re.compile(r"\b(?:sold|booked|bookings?|buyers? (?:love|said|have)|famil(?:y|ies) (?:have|already)|clients?|customers?|"
                      r"few (?:left|units)|limited|hurry|last chance|testimonial)\b|बिक|बुक|ग्राहक|जल्दी करें|सीमित|"
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
    # a person pauses after a comma, a question or a sentence, never inside a phrase ("रिकॉर्ड और [pause] Google Maps")
    t = re.sub(r"(?<![,?!।.—:])\s*\[pause(?: short)?\]", "", t.replace(" [pause", "[pause")).replace("[pause", " [pause")
    n = 0

    def keep(m: "re.Match") -> str:
        nonlocal n
        n += 1
        return m.group(0) if n <= 2 else ""
    return " ".join(re.sub(r"\[pause(?: short)?\]", keep, t).split())


# a check or a visit nobody made: "our team visited", "verified", "hum gaye the", "भेट दिली"
CLAIMED_WORK = re.compile(r"\bvisit|\bverif|\bsite\s+(?:dekh|par\s+gaye)|\bgaye\s+the\b|\bwent\s+to\b|"
                          r"भेट|गए\s+थे|गेलो|वेरिफ|सत्यापि", re.I)


# a line that says somebody checked something: it may only name what the team really checked (review 2026-10-16: "team ne
# price check kiya" passed). The reel's facts say "Checked by the X team: MahaRERA record read, distances from Google Maps".
CHECK_WORDS = re.compile(r"\bcheck|चेक|जाँच|जांच|तपास|परख", re.I)
CHECKED_THINGS = {"MahaRERA record read": re.compile(r"maharera|महारेरा", re.I),
                  "distances from Google Maps": re.compile(r"google\s*maps|गूगल\s*मैप|distance|दूरी|अंतर", re.I)}


def checks_ok(said: str, facts: str) -> bool:
    """A check the line speaks of is one the team made: it names MahaRERA or the Google Maps distances, and only those the
    facts list as checked."""
    done = [k for k in CHECKED_THINGS if k in facts and "Checked by" in facts]
    named = [k for k, rx in CHECKED_THINGS.items() if rx.search(said)]
    return bool(named) and all(k in done for k in named)


def line_ok(said: str, screen: str, last: bool = False) -> bool:
    """A spoken line keeps to its screen line (ad_reel.said_ok, read without its pause tags), claims no visit or
    verification the screen line does not, and the last one still asks for INFO."""
    from app.modules.reels.voice import unpaused
    t = unpaused(said)
    if not t or (CLAIMED_WORK.search(t) and not CLAIMED_WORK.search(screen)):
        return False
    if CHECK_WORDS.search(t) and not checks_ok(t, screen):
        return False
    if last and ad_reel.CTA_WORD not in t:
        return False
    return ad_reel.said_ok(t, screen, most=max(3 * len(screen.split()) + 8, 18))   # a sentence said, not the caption


KM = re.compile(r"(\d+(?:\.\d+)?)\s*km\b", re.I)


def _allowed(facts: str) -> set:
    """The numbers a line may say: those in the facts exactly, and a DISTANCE rounded the way people say it (3.9 km -> 4).
    A price, a size, a BHK count or a number of homes is never rounded (review 2026-10-16: "₹2.24 crore" let "3" through)."""
    from .campaign import _numbers
    km = [float(x) for x in KM.findall(facts)]
    return set(_numbers(facts)) | {str(round(x)) for x in km} | {str(int(x) + 1) for x in km}


# a number said with a unit must be a number the facts give with that unit: "3 crore" is not "3 BHK" (review 2026-10-16)
PRICE_N = re.compile(r"(\d+(?:\.\d+)?)\s*(?:crore|cr\b|करोड़|कोटी|lakh|लाख)", re.I)
KM_N = re.compile(r"(\d+(?:\.\d+)?)\s*(?:km\b|kilomet|किलोमीटर)", re.I)


def units_ok(said: str, facts: str) -> bool:
    """Every price in `said` is a price of the facts, every distance one of their distances (or it rounded)."""
    prices = set(PRICE_N.findall(facts))
    kms = [float(x) for x in KM_N.findall(facts)]
    near = {str(round(x)) for x in kms} | {str(int(x) + 1) for x in kms} | {f"{x:g}" for x in kms}
    return all(p in prices for p in PRICE_N.findall(said)) and all(f"{float(k):g}" in near for k in KM_N.findall(said))


LIST_NUMBERS = re.compile(r"\b1\s*,?\s*2\s*,?\s*3\b")


def _pasted(said: str, screen: str) -> bool:
    """`said` carries its English screen line (4 words or more) word for word inside it."""
    norm = lambda t: " ".join(re.sub(r"[^\w]+", " ", t.lower()).split())   # noqa: E731
    sc = norm(screen)
    return len(sc.split()) >= 4 and sc in norm(said)


def _same(said: str, screen: str) -> bool:
    """`said` is its screen line read out (the same words, give or take marks and pause tags)."""
    from app.modules.reels.voice import unpaused
    norm = lambda t: re.sub(r"[^\w]+", " ", t.lower()).split()   # noqa: E731
    a, b = norm(unpaused(said)), norm(screen)
    return bool(b) and (a == b or (len(set(a) - set(b)) <= 1 and len(a) <= len(b) + 1))


def story_ok(said: str, facts: str, last: bool = False, most: int = 30) -> bool:
    """A story line keeps to the reel's facts: no number, price or name outside them (rounded distances allowed), no guard
    problem, no invented buyer, sale or urgency, no visit or check the facts do not name; the last one asks for INFO."""
    from app.modules.creative.guards import problems_in
    from app.modules.reels.voice import unpaused

    from .campaign import _numbers
    t = unpaused(said)
    if not t or len(t.split()) > most or INVENTED.search(t) or ad_reel._REGNO.search(t) or LIST_NUMBERS.search(t):
        return False
    if CLAIMED_WORK.search(t) and not CLAIMED_WORK.search(facts):
        return False
    if CHECK_WORDS.search(t) and not checks_ok(t, facts):
        return False
    if last and ad_reel.CTA_WORD not in t:
        return False
    said_n = set(_numbers(t))
    if said_n - _allowed(facts) or not units_ok(t, facts):
        return False
    rounded = said_n - set(_numbers(facts))
    return not [p for p in problems_in(t, facts) if p.removeprefix("number not in facts: ") not in rounded]


def fixed(s: ad_reel.Script, lang: str, i: int) -> str:
    """What scene `i` says when no model line passed: the comment ask, the team's checks or the price in the language,
    written by code; any other scene is deliberately silent (its music plays, a breath; "" means silent)."""
    words, screens = FIXED[lang], s.lines()
    if i == len(screens) - 1:
        return words["cta"]
    if s.checked and screens[i] == s.checked_line():
        key = "both" if len(s.checked) > 1 else s.checked[0]
        team = s.team or "team"
        if lang != "en":   # "Avasetu टीम ने", "Avasetu टीमने": the word as the language says it
            team = re.sub(r"\bteam\b", "टीम", team, flags=re.I)
        return words.get(key, words["both"]).format(team=team)
    price = re.search(r"₹\s?[\d.,]+\s*(?:crore|cr|lakh)", screens[i].replace("*", ""), re.I)
    if price:
        said = re.sub(r"\bcr\b", "crore", price.group(0).replace("₹", "").strip(), flags=re.I)   # "2.24 cr" said "2.24 crore"
        return words["price"].format(price=said)
    return ""


class InOrder:
    """The text models in a fixed order, the first usable answer wins: a voice-over's writer and director use the best model
    we have (live 2026-10-16: the shared client's round-robin gave the director a weak free model that pasted the screen text)."""

    def __init__(self, providers, temperature: float = 0.6):
        self.providers, self.temperature = list(providers), temperature
        self.answered = ""   # which model gave the last answer (host and models), for the logs

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


def writer_llm() -> Optional[InOrder]:
    """Gemini (our paid key, the creative room's model) first, then DeepSeek V3.2 (SambaNova), then gpt-oss-120b (Groq), then
    the others; None without a text key. (Live 2026-10-16: SambaNova's free credit ran out, answering 402.)"""
    import os

    from app.platform.llm import GEMINI_CRITICAL_MODEL, GEMINI_OPENAI_URL, GroqLLM, text_providers
    providers = [p for p in text_providers() if getattr(p, "url", "") != GEMINI_OPENAI_URL]
    rank = lambda p: 0 if "sambanova" in (getattr(p, "url", "") or "") else 1 if "groq.com" in (getattr(p, "url", "") or "") else 2  # noqa: E731
    providers = sorted(providers, key=rank)
    gkey = os.environ.get("GEMINI_API_KEY")
    if gkey:
        # Gemini thinks before it writes: a whole script took over the shared 20 s budget (10 s a model) and fell to Groq
        providers.insert(0, GroqLLM(gkey, model=os.environ.get("AI_CRITICAL_MODEL", GEMINI_CRITICAL_MODEL), url=GEMINI_OPENAI_URL,
                                    timeout=90.0))
    return InOrder(providers) if providers else None


async def story(s: ad_reel.Script, c: Ctx, lang: str, llm: Any = None) -> Tuple[str, List[str], Dict[str, Any], str]:
    """(hook, one spoken line per screen line, report, music mood) in the story style, written like an ad team: the writer
    drafts, the editor keeps or rewrites each line and picks the music (`merge` says what each scene got)."""
    screens = [x.replace("*", "") for x in s.lines()]
    facts = " | ".join([ad_reel.corpus(c), *screens])
    about = f"This reel is about: {screens[0]} ({s.format.replace('_', ' ')})"   # each reel's own subject: its story differs
    lines_in = "Screen lines:\n" + "\n".join(f"- {x}" for x in screens)

    def take(r: Any) -> Tuple[str, List[str]]:
        r = r if isinstance(r, dict) else {}
        said = [_tidy(str(x)) for x in r.get("lines") or []]
        return _tidy(str(r.get("hook") or "")), said if len(said) == len(screens) else []

    project = (c.project or "").lower()

    def hook_ok(h: str) -> bool:   # one clear idea, the project's name said after it (live: "Lodha Camelot में, परिवार...")
        return bool(h) and story_ok(h, facts, most=10) and not (project and project in h.lower())

    def line_ok_at(i: int, line: str) -> bool:
        screen, last = screens[i], i == len(screens) - 1
        # the screen text read out, or pasted into the line, is not a voice-over (live 2026-10-16)
        if not line or _same(line, screen) or _pasted(line, screen):
            return False
        return story_ok(line, facts, last=last, most=22) or line_ok(line, screen, last=last)

    def merge(*drafts: Tuple[str, str, List[str]]) -> Tuple[str, List[str], Dict[str, Any]]:
        """Line by line, the first draft's line that passes the checks (the editor's before the writer's), else the line
        code writes for that scene (`fixed`); (hook, lines, report): where the hook and each scene's line came from
        ("editor", "writer", "template", "silent") and how many of the model's lines stayed."""
        hook, hook_from = next(((h, who) for who, h, _ in drafts if hook_ok(h)), ("", "none"))
        out, scenes = [], []
        for i in range(len(screens)):
            line, who = next(((d[i], w) for w, _, d in drafts if i < len(d) and line_ok_at(i, d[i])), (None, ""))
            if line is None and i < len(screens) - 1 and any(i < len(d) and not d[i] for _, _, d in drafts[:1]):
                line, who = "", "silent"   # the editor (or writer) left this scene to its text and music: the budget
            if line is None:
                line = fixed(s, lang, i)
                who = "template" if line else "silent"
            out.append(line)
            scenes.append(who)
        kept = sum(w in ("editor", "writer") for w in scenes)
        return hook, out, {"hook": hook_from, "scenes": scenes, "model_lines": kept, "lines": len(screens),
                           "complete": bool(hook) and kept == len(screens)}

    mood = "warm"
    if llm is None:
        return (*merge(), mood)
    spec = LANGS[lang]
    try:   # the writer's draft
        written = ("writer", *take(await llm.json(STORY_SYSTEM.format(talk=spec["talk"], words=spec["words"],
                                                                      story=spec["story"], budget=BUDGET[lang]),
                                                  f"Facts: {facts}\n{about}\n{lines_in}")))
    except Exception:
        log.info("voice-over: story failed", exc_info=True)
        return (*merge(), mood)
    edited: Tuple[str, str, List[str]] = ("editor", "", [])
    try:   # the editor's pass: each line kept, or rewritten when it is not clear on first hearing
        draft = "Draft:\n" + json.dumps({"hook": written[1], "lines": written[2]}, ensure_ascii=False)
        r = await llm.json(DIRECTOR_SYSTEM.format(talk=spec["talk"], budget=BUDGET[lang]), f"Facts: {facts}\n{about}\n{lines_in}\n{draft}")
        mood = str((r or {}).get("mood") or "").strip().lower() if isinstance(r, dict) else ""
        mood = mood if mood in MOODS else "warm"
        edited = ("editor", *take(r))
    except Exception:
        log.info("voice-over: editor pass failed, the draft kept", exc_info=True)
    return (*merge(edited, written), mood)


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


def _words(text: str) -> int:
    from app.modules.reels.voice import unpaused
    return len(unpaused(text).split())


def trim(s: ad_reel.Script, lines: List[str], budget: int) -> Tuple[List[str], List[int]]:
    """The lines within `budget` words: scenes fall silent (their text and music carry them), the least needed first: plain
    scenes (longest first), then the team's checks, then the first scene; the comment ask and the price always stay.
    (lines, the scenes silenced)."""
    screens, out, dropped = s.lines(), list(lines), []
    last = len(screens) - 1
    price = {i for i, x in enumerate(screens) if "₹" in x}
    checked = {i for i, x in enumerate(screens) if s.checked and x == s.checked_line()}
    rank = lambda i: (2 if i == 0 else 1 if i in checked else 0, -_words(out[i]))   # noqa: E731
    for i in sorted((i for i in range(len(out)) if i != last and i not in price and out[i]), key=rank):
        if sum(_words(x) for x in out) <= budget:
            break
        out[i] = ""
        dropped.append(i)
    return out, dropped


async def script(s: ad_reel.Script, c: Ctx, lang: str, n: int = 0, llm: Any = None,
                 style: str = DEFAULT_STYLE) -> Tuple[List[str], Dict[str, Any]]:
    """The reel's spoken lines with the host's opening in the first (the greeting marked «...» to be said slower), and
    `s.intro` set to the written opening. ([lines], {"language", "style", "by": "llm"|"template", "kept", "hook"})."""
    if lang not in LANGS or style not in STYLES:
        raise ValueError(f"unknown voice language or style: {lang!r}, {style!r}")
    if not s.lines():
        raise ValueError("a reel without screen lines has nothing to say")
    hello, said_open, written_open = opening(c, lang, n)
    if style == "story":
        hook, lines, report, mood = await story(s, c, lang, llm)
        lines, dropped = trim(s, lines, BUDGET[lang] - _words(hook))   # under 20 s whatever the model wrote
        for i in dropped:
            report["scenes"][i] = "trimmed"
        first = " [pause] ".join(x for x in (hook, said_open, lines[0]) if x)
    else:
        hook, mood, (lines, kept) = "", "warm", await spoken(s, lang, llm)
        report = {"hook": "none", "model_lines": kept, "lines": len(lines), "complete": kept == len(lines)}
        first = f"{said_open} [pause] {lines[0]}"
    lines[0] = f"«{hello}» {first}"
    # the model's own "नमस्ते, ..." after our greeting is a second hello (live 2026-10-16): only ours stays
    lines[0] = re.sub(r"(\[pause\]\s*)(?:नमस्ते|नमस्कार|हैलो|hello|hi|namaste|namaskar)(?:\s*(?:दोस्तों|dosto|friends))?[,!।]\s*", r"\1",
                      lines[0], flags=re.I)
    s.intro = written_open
    return lines, {"language": lang, "style": style, "by": "llm" if report["model_lines"] else "template",
                   "kept": report["model_lines"], "hook": hook, "mood": mood, "report": report}


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
