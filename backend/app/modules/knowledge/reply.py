"""Grounded replies: answer a buyer's question ONLY from a Grounding (see grounding.py).

Flow of `answer(question, grounding, channel, llm)`:
  1. Language of the question: English, Hindi, Marathi (Devanagari), Hinglish or romanized Marathi. The reply uses the same language.
  2. Topic routing (price, size, possession, floor, parking, amenities, nearby, commute, maintenance, RERA, site visit, availability,
     negotiation, loan ...) by keyword rules over English, Hindi, Marathi and romanized wording. Each topic is looked up in the grounding.
  3. Everything found -> the answer. When an LLM is available it phrases the answer from the grounding alone; the draft is rejected unless
     every number and proper noun is in the grounding or the question, with no phone, link, hype or prediction. Otherwise the sentences
     are used as they are (the deterministic path, also the fallback when the LLM fails).
  4. Part (or all) not covered -> a plain, honest sentence naming what we do not have, with the interest link so the agent can share it.
     `confident` is then False and `missing` names the gap for the owner. Never 'we will forward your query'.
Sample homes: availability and visit questions say honestly that it is an illustration; price questions give only the labelled sample figure.
Channels: 'facebook' (public reply with the {interest_url} placeholder), 'instagram' (never a URL: 'link in our bio'), 'chat' (website widget).
"""
from app.core import brand
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

from app.modules.marketing.polish import HYPE, PHONE

from .grounding import INTEREST, URL, Grounding

# ---- language -------------------------------------------------------------------------------------------------------
DEV = re.compile(r"[ऀ-ॿ]")
MR_DEV = re.compile(r"आहे|आहेत|किती|कुठे|कधी|मिळेल|पाहिजे|हवे|तुम्ही|जवळ|माहिती|काय|आम्ही|किंमत|आहे का|करता")
HI_DEV = re.compile(r"है|हैं|कितना|कितनी|कितने|कब|कहाँ|कहां|क्या|मिलेगा|मिलेगी|में|नहीं|चाहिए|करें|कीमत|दाम")
MR_LAT = re.compile(r"\b(kiti|kuthe|kadhi|aahe|ahe|aahet|milel|pahije|hava|havi|kay|jawal|asel|aahe ka|ahe ka)\b", re.I)
HI_LAT = re.compile(r"\b(kitna|kitni|kitne|kab|kahan|kya|hai|hain|milega|milegi|nahi|nahin|hoga|hogi|chahiye|paas|door|sakta|sakte|batao|bataiye|bataye|dikhao|kaise|mein|wala|wali|ka|ki|ke|kar|aap|mujhe)\b", re.I)


def detect_language(text: str) -> str:
    """'en' | 'hi' | 'mr' (Devanagari) | 'hinglish' (Hindi in Roman letters) | 'mr_latn' (Marathi in Roman letters)."""
    t = text or ""
    if DEV.search(t):
        return "mr" if len(MR_DEV.findall(t)) > len(HI_DEV.findall(t)) else "hi"
    mr, hi = len(MR_LAT.findall(t)), len(HI_LAT.findall(t))
    if mr > hi:
        return "mr_latn"
    return "hinglish" if hi else "en"


LANG_NAME = {"en": "English", "hi": "Hindi in Devanagari script", "mr": "Marathi in Devanagari script",
             "hinglish": "Hinglish (Hindi written in Roman letters)", "mr_latn": "Marathi written in Roman letters"}

# ---- topics ---------------------------------------------------------------------------------------------------------
# name: (question regex, fact regexes in priority order, labels en / hi / mr / short)
I = re.I
Topic = Tuple["re.Pattern", Tuple["re.Pattern", ...], Tuple[str, str, str, str]]


def _t(q: str, facts: Tuple[str, ...], en: str, hi: str, mr: str, short: str) -> Topic:
    return re.compile(q, I), tuple(re.compile(f, I) for f in facts), (en, hi, mr, short)


TOPICS: Dict[str, Topic] = {
    "price": _t(r"\b(price|prices|cost|rate|kimat|kimmat|keemat|daam|dam|kitne\s*(ka|ki|mein|me)|kitna\s*(price|rate|paisa|padega|lagega))\b|₹|किंमत|कीमत|दाम|भाव|कितने\s*का|किती\s*रुपये",
                ("PRICE",), "the price", "कीमत", "किंमत", "price"),
    "carpet": _t(r"carpet|कार्पेट|कारपेट", (r"carpet area",), "the carpet area", "कार्पेट एरिया", "कार्पेट एरिया", "carpet area"),
    "size": _t(r"\bsize\b|sq\.?\s?ft|sqft|square\s*(feet|foot)|built.?up|how\s*big|kitna\s*bada|area\s*(kitna|kya|kiti)|how\s*many\s*(bhk|bedrooms?|rooms)|kitne\s*(bhk|bedroom|room)|kiti\s*(bhk|room)|bedrooms?\b|एरिया|क्षेत्रफ|साइज|कितना\s*बड़ा|बेडरूम|चौरस",
               (r"carpet area", r"built-up", r"\bBHK\b"), "the size", "साइज", "साइज", "size"),
    "possession": _t(r"possession|handover|hand\s*over|\bready\b|rtm|move\s*in|under\s*construction|kab\s*(tak\s*)?(mil|milega|milegi|ready)|kadhi\s*(milel|taba)|ताबा|पजेशन|कब\s*मिल|रेडी|तैयार|कधी\s*मिळ",
                     (r"possession", r"ready to move", r"under construction", r"handover"), "the possession details", "पजेशन", "ताब्याची माहिती", "possession"),
    "floor": _t(r"\bfloors?\b|मंज़िल|मंजिल|मजला|माळा|फ्लोर", (r"\bfloor\b",), "the floor", "मंज़िल", "मजला", "floor"),
    "facing": _t(r"\bfacing\b|\bfaces\b|\bdirection\b|दिशा", (r"\bfaces\b",), "the facing direction", "दिशा", "दिशा", "facing"),
    "parking": _t(r"parking|पार्किंग|garage|gaadi|car\s*(space|park)", (r"parking",), "the parking details", "पार्किंग", "पार्किंगची माहिती", "parking"),
    "amenities": _t(r"amenit|\bgym\b|swimming|\bpool\b|club\s?house|\blift\b|elevator|garden|play\s?(area|ground)|security|facilit|सुविधा|जिम|लिफ्ट",
                    (r"amenities", r"\b(gym|pool|clubhouse|lift|garden|play area|security)\b"), "the amenities", "सुविधाओं", "सुविधांची माहिती", "amenities"),
    "power": _t(r"power\s*back\s*up|backup|generator|\bbijli\b|बिजली|वीज", (r"^Power backup", r"power backup"), "the power backup details", "पावर बैकअप", "पॉवर बॅकअप", "power backup"),
    "school": _t(r"schools?\b|college|शाळा|स्कूल|कॉलेज|vidyalaya", (r"school|college",), "details of nearby schools", "आसपास के स्कूल", "जवळच्या शाळांची माहिती", "nearby school"),
    "hospital": _t(r"hospital|clinic|doctor|अस्पताल|हॉस्पिटल|दवाखाना|रुग्णालय", (r"hospital|clinic",), "details of nearby hospitals", "आसपास के अस्पताल", "जवळच्या रुग्णालयांची माहिती", "nearby hospital"),
    "market": _t(r"market|\bmall\b|grocery|\bshops?\b|supermarket|मार्केट|बाजार|दुकान|मॉल", (r"market|\bmall\b|shop|grocer",), "details of nearby markets", "आसपास के बाजार", "जवळच्या बाजाराची माहिती", "nearby market"),
    "metro": _t(r"metro|\bstation\b|\btrain\b|मेट्रो", (r"metro|station",), "the metro details", "मेट्रो", "मेट्रोची माहिती", "metro"),
    "nearby": _t(r"nearby|near\s*by|close\s*to|neighbou?rhood|aas\s*paas|aaspaas|paas\s*(mein|me|mai)|nazdik|jawal|आसपास|आस\s*पास|जवळ|पास\s*में|नज़दीक|नजदीक|connectivity|\broads?\b",
                 (r"^Nearby ", r"connectivity", r"\bnearby\b|\broads?\b"), "details of nearby places", "आसपास की जगहों", "जवळपासची माहिती", "nearby places"),
    "commute": _t(r"commute|office|\bit\s*park|\beon\b|world\s*trade|wtc|how\s*far|distance|travel\s*time|\bdrive\b|traffic|kitna\s*door|kitni\s*door|kiti\s*(lamb|antar)|दूर|अंतर|ऑफिस|आईटी|ट्रैफिक|ट्रॅफिक|\blamb\b",
                  (r"^Nearby office", r"office|campus|commute|rush hour|trip to work|drive"), "the commute details", "आने-जाने का समय", "प्रवासाची माहिती", "commute"),
    "maintenance": _t(r"maintenance|maintainance|मेंटेनेंस|मेंटेनन्स|देखभाल|society\s*charges", (r"maintenance",), "the maintenance figure", "मेंटेनेंस", "मेंटेनन्सची रक्कम", "maintenance"),
    "water": _t(r"\bwater\b|borewell|tanker|पानी|पाणी", (r"water",), "the water supply details", "पानी की सप्लाई", "पाण्याची माहिती", "water supply"),
    "rera": _t(r"\brera\b|maharera|रेरा|registered|registration\s*(no|number)", (r"\bRERA\b",), "the RERA number", "RERA नंबर", "RERA क्रमांक", "RERA number"),
    "visit": _t(r"visit|see\s*(it|the\s*(flat|home|house|property))|appointment|come\s*and\s*see|dekhne|dekh\s*sakta|dekhna|देखने|देखना|भेट|पाहायला|पाहता\s*येईल|sunday|saturday|weekend|रविवार",
                (r"site visit",), "the visit", "विज़िट", "भेट", "visit"),
    "booking": _t(r"\bbook(ing|ed)?\b|reserve|token\s*amount|advance\s*(amount|payment)|बुकिंग|बुक", (r"(?!x)x",), "the booking process and amount", "बुकिंग की जानकारी", "बुकिंगची माहिती", "booking"),
    "availability": _t(r"available|availability|still\s*(there|open|on)|\bsold\b|booked|uplabdh|उपलब्ध|अवेलेबल",
                       (r"available|under offer",), "the live availability", "अभी उपलब्धता", "सध्याची उपलब्धता", "availability"),
    "negotiation": _t(r"negotiab|negotiat|discount|bargain|best\s*price|final\s*price|kam\s*(hoga|ho\s*sakta|karo)|कम\s*(होगा|हो\s*सकता)|सौदा|मोलभाव|कमी\s*होईल|तडजोड",
                      (r"(?!x)x",), "a confirmed answer on negotiation", "मोलभाव", "किंमतीत तडजोडीची माहिती", "price negotiation"),
    "loan": _t(r"\bloan\b|\bemi\b|finance|\bbank\b|mortgage|लोन|कर्ज|ईएमआई", (r"loan",), "loan details", "लोन", "कर्ज", "loan"),
    "furnishing": _t(r"furnish|furniture|फर्निश|फर्निचर", (r"furnish",), "the furnishing details", "फर्निशिंग", "फर्निशिंगची माहिती", "furnishing"),
    "location": _t(r"\bwhere\b|location|locat|kahan|kahaan|kuthe|kuthhe|कहाँ|कहां|कुठे|लोकेशन|कोठे", (r"located in", r"east Pune|eastern corridor"), "the location", "लोकेशन", "ठिकाण", "location"),
    "address": _t(r"address|\bpata\b|पता|पत्ता", (r"(?!x)x",), "the exact address", "पूरा पता", "पूर्ण पत्ता", "exact address"),
    "builder": _t(r"builder|developer|who\s*(built|is\s*building)|project\s*name|बिल्डर|डेव्हलपर|डेवलपर", (r"builder", r"project is"), "the builder details", "बिल्डर", "बिल्डरची माहिती", "builder"),
}
AREA_TOPICS = {"commute", "metro", "nearby", "location"}          # may be answered from the area's facts
GENERAL_TOPICS = {"visit", "loan", "rera"}            # may be answered from process statements true for any home
SAMPLE_TOPICS = {"availability", "visit", "negotiation", "booking"}
WEAK_PRICE = re.compile(r"\bprice|₹|kimat|kimmat|keemat|किंमत|कीमत|दाम|भाव|daam", I)
DISTANCE = re.compile(r"how\s*far|distance|travel\s*time|kitna\s*door|kitni\s*door|kiti\s*(lamb|antar)|दूर|अंतर|\blamb\b|minutes|\btime\b", I)
FACT_DIGIT = re.compile(r"\d")


def _fact_matches(topic: str, fact: str) -> Optional[int]:
    """Priority index when `fact` answers `topic`, else None."""
    if fact.startswith("Check:"):
        return None
    if topic == "price":
        return 0 if re.search(r"₹|\bprice\b|\brent\b", fact, I) and FACT_DIGIT.search(fact) else None
    for i, rx in enumerate(TOPICS[topic][1]):
        if rx.search(fact):
            return i
    return None


def topics_in(question: str) -> List[str]:
    """Topics the question touches, in order of appearance."""
    q = _norm(question)
    hits = [(m.start(), name) for name, (rx, _, _) in TOPICS.items() if (m := rx.search(q))]
    names = {n for _, n in hits}
    if "carpet" in names:
        names.discard("size")
    if "maintenance" in names and not WEAK_PRICE.search(q):
        names.discard("price")
    if "price" in names and "negotiation" in names:
        names.discard("price")
    if "availability" in names and "possession" in names and not re.search(r"possession|handover|ready", q, I):
        names.discard("possession")
    if "commute" in names and names & {"school", "hospital", "market"} and not re.search(r"office|commute|it\s*park|eon|world\s*trade|wtc", q, I):
        names.discard("commute")
    if "nearby" in names and names & {"school", "hospital", "market", "metro", "commute"}:
        names.discard("nearby")
    if "location" in names and len(names) > 1:
        names.discard("location")
    if "address" in names:
        names.discard("location")
    if not names and re.search(r"how\s*much|kitna|kitni|kitne|kiti", q, I):
        names.add("price")
    order = {n: p for p, n in hits}
    return sorted(names, key=lambda n: order.get(n, 10_000))


def has_topic(question: str) -> bool:
    return bool(topics_in(question))


def _norm(text: str) -> str:
    return (text or "").translate(str.maketrans("०१२३४५६७८९", "0123456789"))


# ---- result ---------------------------------------------------------------------------------------------------------
@dataclass
class Reply:
    text: str
    confident: bool
    missing: Optional[str] = None
    basis: List[str] = field(default_factory=list)   # the facts the answer rests on (for the owner's audit)
    language: str = "en"
    via: str = "rules"                                # 'llm' | 'rules'


CHANNELS = ("facebook", "instagram", "chat")
MAX_BODY = {"facebook": 260, "instagram": 260, "chat": 420}
MAX_FOUND = {"facebook": 2, "instagram": 2, "chat": 3}


def _channel(c: str) -> str:
    return c if c in CHANNELS else "chat"


# Wording. Facts stay as written (English); the framing is in the buyer's language, and an LLM, when present, localises the whole answer.
FOR = {"home": " for this home", "area": " for this area", "post": ""}
UNKNOWN = {
    "en": {"facebook": "I do not have {what}{for_}, but the agent can tell you: {interest_url}",
           "instagram": "I do not have {what}{for_}, but the agent can tell you; see the link in our bio.",
           "chat": "I do not have {what}{for_}; I will ask our team to confirm it for you."},
    "hinglish": {"facebook": "{what} ki jaankari mere paas nahi hai, lekin agent share kar sakte hain: {interest_url}",
                 "instagram": "{what} ki jaankari mere paas nahi hai, lekin agent share kar sakte hain; link in our bio dekhein.",
                 "chat": "{what} ki jaankari mere paas nahi hai; hum apni team se confirm karwa lete hain."},
    "hi": {"facebook": "{what} की जानकारी मेरे पास नहीं है, लेकिन एजेंट बता सकते हैं: {interest_url}",
           "instagram": "{what} की जानकारी मेरे पास नहीं है, लेकिन एजेंट बता सकते हैं; हमारे बायो का लिंक देखें।",
           "chat": "{what} की जानकारी मेरे पास नहीं है; हम अपनी टीम से इसकी पुष्टि करवा लेते हैं।"},
    "mr": {"facebook": "{what} माझ्याकडे नाही, पण एजंट सांगू शकतात: {interest_url}",
           "instagram": "{what} माझ्याकडे नाही, पण एजंट सांगू शकतात; आमच्या बायोमधील लिंक पहा.",
           "chat": "{what} माझ्याकडे नाही; आम्ही आमच्या टीमकडून याची खात्री करून घेऊ."},
    "mr_latn": {"facebook": "{what} chi mahiti majhyakade nahi, pan agent sangu shaktat: {interest_url}",
                "instagram": "{what} chi mahiti majhyakade nahi, pan agent sangu shaktat; link in our bio baha.",
                "chat": "{what} chi mahiti majhyakade nahi; aamhi aamchya team kadun khatri karun gheu."},
}
TAIL = {
    "en": {"facebook": "More details: {interest_url}", "instagram": "More details at the link in our bio.", "chat": ""},
    "hinglish": {"facebook": "Poori jaankari: {interest_url}", "instagram": "Poori jaankari link in our bio par hai.", "chat": ""},
    "hi": {"facebook": "पूरी जानकारी: {interest_url}", "instagram": "पूरी जानकारी हमारे बायो के लिंक पर है।", "chat": ""},
    "mr": {"facebook": "संपूर्ण माहिती: {interest_url}", "instagram": "संपूर्ण माहिती आमच्या बायोमधील लिंकवर आहे.", "chat": ""},
    "mr_latn": {"facebook": "Sampurna mahiti: {interest_url}", "instagram": "Sampurna mahiti link in our bio madhe aahe.", "chat": ""},
}


def _label(topic: str, lang: str) -> str:
    en, hi, mr, short = TOPICS[topic][2]
    return {"en": en, "hi": hi, "mr": mr}.get(lang, short)


def _join_labels(labels: List[str], lang: str) -> str:
    labels = list(dict.fromkeys(labels))
    if len(labels) <= 1:
        return "".join(labels)
    word = {"en": "and", "hinglish": "aur", "hi": "और", "mr": "आणि", "mr_latn": "ani"}[lang]
    return ", ".join(labels[:-1]) + f" {word} {labels[-1]}"


# ---- lookup ---------------------------------------------------------------------------------------------------------
@dataclass
class Plan:
    found: List[Tuple[str, str]] = field(default_factory=list)   # (topic, sentence)
    missing: List[str] = field(default_factory=list)             # topic names
    over: Dict[str, str] = field(default_factory=dict)           # topic -> a more specific gap (key of OVERRIDE), e.g. the distance, one amenity


def _faq_hit(topic: str, items: List[Dict[str, str]], question: str = "", q_topics: Optional[Set[str]] = None) -> Optional[str]:
    """A written answer whose question is about this topic (and no topic the buyer did not ask about); amenity questions must share a word,
    so 'is there a pool?' is not answered with the clubhouse FAQ."""
    for item in items:
        t = set(topics_in(item["q"]))
        if topic not in t or not t <= (q_topics or {topic}):
            continue
        if topic == "amenities" and not (_words(question) & _words(item["q"])):
            continue
        return item["a"]
    return None


def _pick(topic: str, pool: List[str], limit: int = 1) -> List[str]:
    scored = sorted(((p, f) for f in pool if (p := _fact_matches(topic, f)) is not None), key=lambda x: x[0])
    out: List[str] = []
    for _, f in scored:
        if f not in out:
            out.append(f)
    return out[:limit]


def plan(question: str, g: Grounding) -> Plan:
    p = Plan()
    q = _norm(question)
    qt = topics_in(question)
    for topic in qt:
        multi = 3 if topic in ("school", "hospital", "market", "metro", "nearby") else 1
        if g.sample and topic in SAMPLE_TOPICS:
            p.found += [(topic, s) for s in g.facts[:2]]
            continue
        hit = _faq_hit(topic, g.faq, q, set(qt)) if (g.kind != "area" or topic in AREA_TOPICS) else None
        picked = [hit] if hit else []
        if hit and g.kind == "area" and not DISTANCE.search(q):
            picked = _pick(topic, g.facts, multi) or picked      # the area's curated FAQ answers 'how far' questions; its facts answer the rest
        # home-level facts first, then (for area-type topics) the area's facts; a pure area grounding keeps its sentences in `facts`
        if not picked:
            picked = _pick(topic, g.facts, multi) if (g.kind != "area" or topic in AREA_TOPICS) else []
        if not picked and topic in AREA_TOPICS:
            picked = _pick(topic, g.area_facts, multi)
            hit = _faq_hit(topic, g.area_faq, q, set(qt))
            if not picked and hit:
                picked = [hit]
        if not picked and topic in GENERAL_TOPICS:
            picked = _pick(topic, g.general)
            if topic == "rera" and g.kind == "listing":
                p.missing.append(topic)
        if topic == "commute" and DISTANCE.search(q) and not any(s.startswith("Nearby office") for s in picked):
            p.missing.append("commute")     # we can frame the commute but have no measured distance or time
            p.over["commute"] = "distance"
        if topic == "amenities" and picked and not hit:
            asked = AMENITY_WORDS.search(q)
            word = {"swimming": "pool", "elevator": "lift"}.get(asked.group(1).lower(), asked.group(1).lower()) if asked else None
            if word and not re.search(re.escape(word.split()[0]), " ".join(picked), I):
                p.missing.append("amenities")  # the list is shown, but the amenity asked about is not on it
                p.over["amenities"] = "amenity"
        p.found += [(topic, s) for s in picked]
        if not picked and topic not in p.missing:
            p.missing.append(topic)
    # a sentence is quoted once
    seen: Set[str] = set()
    p.found = [(t, s) for t, s in p.found if not (s in seen or seen.add(s))]
    return p


STOP = set("what which where when does have this that with from your about there their them will would could should have been into more than the and for are you our can how why who is it of to in on at a an be or if do any".split())


def _words(text: str) -> Set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", (text or "").lower()) if w not in STOP}


def overlap_hit(question: str, g: Grounding) -> Optional[str]:
    """Last resort for questions with no topic: the faq answer or fact sharing at least two content words with the question."""
    qw = _words(question)
    best, score = None, 1
    for item in g.faq + g.area_faq:
        s = len(qw & _words(item["q"] + " " + item["a"]))
        if s > score:
            best, score = item["a"], s
    for f in g.facts + g.area_facts:
        s = len(qw & _words(f))
        if not f.startswith("Check:") and s > score:
            best, score = f, s
    return best


# ---- validation of LLM text -----------------------------------------------------------------------------------------
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
PREDICT = re.compile(r"\b(will (rise|go up|increase|double|appreciate)|expected to (rise|grow|open)|appreciation|guaranteed returns?)\b", I)
BRUSH_OFF = re.compile(r"\b(will|shall) (forward|reply|get back)|forward(ed)? (this|your)|our team will reply", I)
CAPITAL = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-zA-Z]{2,}\b")
ALLOWED_NAMES = {"pune", "property", "team", "rera", "maharera", "bhk", "i", "tap"}


def _nums(text: str) -> Set[str]:
    return {n.replace(",", "").rstrip(".") for n in NUM.findall(_norm(text))}


FUNCTION_WORDS = set("""about above after again against also because been before being below between both could does doing down during each either enough every
from have having here hence into just least like made make many more most much must never next none only other over please quite rather really same should since
some still such than that their them then there these they this those though through under until upon very want wants what when where whether which while whom
whose will with within without would your yours agent details detail confirm share visit request home house place listed listing currently available sorry thanks
thank kindly right note price shown shows state given yes""".split())


def valid_text(text: str, source: str, channel: str, limit: int, strict: bool = False) -> bool:
    """`source` is everything the answer may draw on (the grounding, or the English text being translated); the question is NOT a source, so a number
    or name typed by a commenter can never become a stated fact. `strict` (English answers written freely by the model) also rejects any
    content word that the grounding does not contain, which catches invented claims like 'away from the road noise'."""
    t = (text or "").strip()
    if not t or len(t) > limit:
        return False
    if PHONE.search(t) or HYPE.search(t) or URL.search(t) or PREDICT.search(t) or BRUSH_OFF.search(t) or "{" in t or "}" in t:
        return False
    if not _nums(t) <= _nums(source):
        return False
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z']+", source)]
    vocab = set(words) | ALLOWED_NAMES
    for m in CAPITAL.finditer(t):
        if m.group(0).lower() not in vocab:
            return False
    if strict:
        known = {w[:5] for w in words}
        for w in re.findall(r"[a-z]{5,}", t.lower()):
            if w not in FUNCTION_WORDS and w[:5] not in known:
                return False
    return True


LLM_SYSTEM = (
    f"You answer a home buyer's question for the {brand.TEAM} using ONLY the FACTS given. Reply with ONE JSON object: "
    '{"answerable": true or false, "answer": "..."}. The answer is 1 or 2 short, plain, friendly sentences written in {lang}. '
    "Use only numbers, names and claims that appear in FACTS (never repeat a number or name that only the QUESTION contains). If FACTS do not fully answer the question, set answerable=false and answer=''. "
    "A sample home is only an illustration: never say it is available. Never invent prices, distances, dates, schools, amenities or approvals. "
    "Never include phone numbers, links, promises, predictions, or words like best, perfect, guaranteed, dream. Never say you will forward the query."
)
TRANSLATE_SYSTEM = (
    "Rewrite the TEXT in {lang}, keeping every number and name exactly and adding nothing. Reply with ONE JSON object: {\"text\": \"...\"}."
)


def _facts_block(g: Grounding) -> str:
    lines = [f"- {f}" for f in g.facts + g.area_facts + g.general]
    lines += [f"- (what to check) {a}" for a in g.advice]
    faq = "\n".join(f"Q: {x['q']} A: {x['a']}" for x in g.faq)
    return f"SUBJECT: {g.subject}{' (a SAMPLE home, not for sale)' if g.sample else ''}\nFACTS:\n" + "\n".join(lines) + (f"\nFAQ:\n{faq}" if faq else "")


SAMPLE_WORD = re.compile(r"sample|illustrat|सैंपल|सॅम्पल|नमूना|नमुना|उदाहरण", I)


async def _llm_answer(question: str, g: Grounding, lang: str, channel: str, llm) -> Tuple[str, Optional[str]]:
    """('ok', text) | ('no', None) when the model says the grounding does not answer | ('fail', None) when it is absent, down or its draft is unsafe."""
    if llm is None or not hasattr(llm, "json") or lang != "en":  # other languages: the grounded English sentences are translated instead (see _localise)
        return "fail", None
    try:
        raw = await llm.json(LLM_SYSTEM.replace("{lang}", LANG_NAME[lang]), f"{_facts_block(g)}\n\nQUESTION:\n{question[:400]}")
    except Exception:
        return "fail", None
    if not isinstance(raw, dict) or not isinstance(raw.get("answerable"), bool):
        return "fail", None
    if raw["answerable"] is False:
        return "no", None
    text = str(raw.get("answer") or "").strip()
    if not valid_text(text, g.corpus(), channel, MAX_BODY[channel], strict=True) or (g.sample and not SAMPLE_WORD.search(text)):
        return "fail", None
    return "ok", text


async def _localise(body: str, lang: str, channel: str, llm) -> Tuple[str, bool]:
    """Put an already grounded English answer into the buyer's language -> (text, translated). The English text stays when the LLM is absent or
    its output fails the checks (same numbers, same names, no phone, link or hype)."""
    if lang == "en" or llm is None or not hasattr(llm, "json"):
        return body, False
    try:
        raw = await llm.json(TRANSLATE_SYSTEM.replace("{lang}", LANG_NAME[lang]), f"TEXT:\n{body}")
    except Exception:
        return body, False
    text = str(raw.get("text") or "").strip() if isinstance(raw, dict) else ""
    if not valid_text(text, body, channel, MAX_BODY[channel] * 2) or (SAMPLE_WORD.search(body) and not SAMPLE_WORD.search(text)):
        return body, False
    return text, True


def _basis_for(text: str, g: Grounding) -> List[str]:
    """Facts an LLM answer rests on: the grounding sentences that share numbers or at least two content words with it."""
    tw, tn = _words(text), _nums(text)
    out = [f for f in g.facts + g.area_facts if (tn and tn & _nums(f)) or len(tw & _words(f)) >= 2]
    return out[:4]


# ---- entry point ----------------------------------------------------------------------------------------------------
def _cap(sentence: str, limit: int) -> str:
    """Keep a long list sentence within the limit by cutting at a comma, never mid-word."""
    if len(sentence) <= limit:
        return sentence
    head = sentence[:limit]
    if ", " in head:
        return head.rsplit(", ", 1)[0].rstrip(".,;") + ", among others."
    return head.rsplit(" ", 1)[0].rstrip(".,;") + "."


def _body(found: List[Tuple[str, str]], channel: str, room: int) -> List[str]:
    return [_cap(s, MAX_BODY[channel]) for _, s in found[:room]]


UNKNOWN_DETAIL = {"en": "that detail", "hi": "इस बात", "mr": "ही माहिती", "hinglish": "yeh detail", "mr_latn": "tya goshti"}
OVERRIDE = {
    "distance": {"en": "the exact distance or travel time", "hi": "सही दूरी या समय", "mr": "नेमके अंतर किंवा वेळ",
                 "hinglish": "exact distance ya time", "mr_latn": "nemke antar kiwa vel"},
    "amenity": {"en": "confirmation of that amenity", "hi": "उस सुविधा की पुष्टि", "mr": "त्या सुविधेची खात्री",
                "hinglish": "us amenity ki confirmation", "mr_latn": "tya suvidhechi khatri"},
}
AMENITY_WORDS = re.compile(r"\b(gym|swimming|pool|club\s?house|lift|elevator|garden|play\s?(area|ground)|security)\b", I)


async def answer(question: str, grounding: Grounding, channel: str = "facebook", llm=None) -> Reply:
    """A grounded reply. `text` may contain the placeholder {interest_url} (facebook only) for the caller to fill with the real interest link."""
    ch, g = _channel(channel), grounding
    q = (question or "").strip()
    lang = detect_language(q)
    pl = plan(q, g)
    tail = TAIL[lang][ch].replace("{interest_url}", INTEREST)

    if not topics_in(q):  # no known topic: the LLM may answer from the grounding; without it, the best matching sentence
        status, text = await _llm_answer(q, g, lang, ch, llm)
        if text:
            return Reply(f"{text} {tail}".strip(), True, None, _basis_for(text, g), lang, "llm")
        hit = overlap_hit(q, g) if status == "fail" else None
        if hit:
            text, done = await _localise(_cap(hit, MAX_BODY[ch]), lang, ch, llm)
            return Reply(f"{text} {tail}".strip(), True, None, [hit], lang, "llm" if done else "rules")
        pl.missing = ["other"]

    if not pl.missing:  # everything is covered: the LLM phrases it from the grounding, else the sentences themselves are used
        basis = [s for _, s in pl.found]
        status, text = await _llm_answer(q, g, lang, ch, llm)
        if text:
            return Reply(f"{text} {tail}".strip(), True, None, basis, lang, "llm")
        text, done = await _localise(" ".join(_body(pl.found, ch, MAX_FOUND[ch])), lang, ch, llm)
        return Reply(f"{text} {tail}".strip(), True, None, basis, lang, "llm" if done else "rules")

    # something is not covered: say what we can, then say plainly what we do not have
    labels = [UNKNOWN_DETAIL[lang] if m == "other" else OVERRIDE[pl.over[m]][lang] if m in pl.over else _label(m, lang) for m in pl.missing]
    unknown = UNKNOWN[lang][ch].format(what=_join_labels(labels, lang), for_=FOR[g.noun] if lang == "en" else "", interest_url=INTEREST)
    found = _body(pl.found, ch, MAX_FOUND[ch] - 1 if ch != "chat" else 2)
    text = " ".join(found)
    if found and lang != "en":
        text, _ = await _localise(text, lang, ch, llm)
    gap = "; ".join(q[:100] if m == "other" else (OVERRIDE[pl.over[m]]["en"] if m in pl.over else _label(m, "en")) for m in pl.missing)
    return Reply(f"{text} {unknown}".strip(), False, gap, [s for _, s in pl.found], lang, "rules")


