"""Text guards shared by the copywriter and the critic. Pure functions. Reuses marketing's HYPE and PHONE guards."""
import re
from typing import List

from app.platform.text import HYPE, PHONE

URL = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|in|io|co|app|org|net)\b", re.I)
PRICE = re.compile(r"₹|\brs\.?\s*\d|\binr\b|\blakhs?\b|\bcrores?\b|\bper\s*sq\.?\s*(?:ft|feet)\b|\bsq\.?\s?ft\b", re.I)
PREDICT = re.compile(r"\b(will (?:rise|go up|increase|double|appreciate)|expected to (?:rise|grow|double)|appreciation|guaranteed returns?|invest now)\b", re.I)
# "Kolte Patil Developers", "XYZ Realty Pvt": a builder or company name, which must come from the facts
ORG = re.compile(r"\b(?:[A-Z][\w&'.-]*\s+){1,3}(?:Developers?|Builders?|Constructions?|Realty|Realtors?|Infra(?:structure)?|"
                 r"Estates?|Properties|Promoters?|Buildcon|Ltd|Limited|LLP|Pvt)\b")
TITLE_NAME = re.compile(r"\b(?:mr|mrs|ms|shri|smt|sri)\.?\s+[A-Z]\w+", re.I)
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
HASHTAG = re.compile(r"#\w+")
# Devanagari vowel signs and the virama are combining marks, not \w: they must not split a Marathi/Hindi word in two
WORD = re.compile(r"[A-Za-z0-9ऀ-ॿ][\wऀ-ॿ'’\-]*")

FILLER = (
    "in today's world", "in today’s world", "fast-paced", "game changer", "game-changer", "unlock", "ultimate guide",
    "look no further", "are you looking for", "dive into", "delve", "navigating the", "testament", "elevate your",
    "in the realm", "it's important to note", "it is important to note", "whether you're", "take it to the next level",
    "tips and tricks", "everything you need to know", "now more than ever", "at the end of the day", "stay tuned",
)
GENERIC_HOOK = re.compile(r"^(?:tips? (?:for|to)|things to|guide to|all about|introducing|welcome to|important|know about)\b", re.I)
# Claims a post may not make about a property unless its facts say so (seen live 2026-10-06: "makes this plot affordable",
# "fits your lifestyle", "all costs already shown", "the fixed 2029 date", "the biggest mistake"), in English, Marathi, Hindi
CLAIM = re.compile(r"\b(?:affordab\w*|investment|lifestyle|value for money|secure your|biggest mistake|all costs|fixed date|"
                   r"no hidden)\b|परवडण\w*|गुंतवणूक|जीवनशैली|सर्वात मोठी चूक|सर्व खर्च|निश्चित|किफायती|निवेश|"
                   r"सबसे बड़ी गलती|सारे खर्च", re.I)
CLICKBAIT = re.compile(r"\b(you won'?t believe|shocking|secret they|doctors hate|this one trick|mind-?blowing|must[- ]see)\b", re.I)

# Facts only, in English, Hindi and Marathi. Devanagari vowel signs are not \w, so Devanagari words are bounded by explicit
# look-arounds (a word may carry a suffix: परवडणारे, सस्ता).
_D = "ऀ-ॿ"


def _dev(*words: str) -> str:
    return rf"(?<![{_D}\w])(?:{'|'.join(words)})"


# A value claim: a post states the price, it never judges it for the reader.
VALUE_CLAIM = re.compile(
    r"\b(?:affordab\w*|afford|cheap\w*|inexpensive|budget[- ]friendly|pocket[- ]friendly|value for money|great value|"
    r"good value|bargain|steal deal|great deal|good deal|worth (?:it|every)|overpay\w*|low(?:est)? price|reasonabl[ey] priced|"
    r"secure your (?:land|plot|home|flat))\b|"
    + _dev("सस्त", "किफ़ायत", "किफायत", "परवड", "स्वस्त", "बजेटमध्ये", "बजट में", "पैसा वसूल"), re.I)
# A promise about the reader's life or home.
PROMISE = re.compile(r"\byour (?:new|future|own|forever|perfect) home\b|\bhome of your\b|"
                     + _dev("तुमचे नवीन घर", "तुमचं नवीन घर", "तुमचे स्वतःचे घर", "तुमचं स्वतःचं घर", "स्वप्नातील", "स्वप्नातलं",
                            "आपका नया घर", "आपका अपना घर", "सपनों का", "तुमचे हक्काचे", "तुमचं हक्काचं"), re.I)
# Nothing on an Instagram card or caption can be tapped or clicked.
# (An instruction to tap, not a water tap: "check every tap and switch" is a fine possession tip.)
TAP = re.compile(r"\b(?:double[- ])?(?:tap|click)(?:ing)?\s+(?:to|the link|here|on|below|this|that|link|now)\b|"
                 r"\b(?:double[- ]tap|click here|tap here)\b|" + _dev("टॅप कर", "टैप कर", "क्लिक कर"), re.I)
# "only", "just": a minimiser that sells ("only 3 km", "just ₹32 lakh"). "not only" and "if only" are ordinary English.
MINIMISER = re.compile(r"(?<!\bnot )(?<!\bif )\b(?:only|just|merely)\b|" + _dev("फक्त", "केवळ", "केवल", "सिर्फ़", "सिर्फ"), re.I)
# Real listings are real: never "sample".
SAMPLE = re.compile(r"\bsamples?\b|" + _dev("नमुना", "सॅम्पल", "सैंपल"), re.I)


_ODD = {"‐": "-", "‑": "-", "‒": "-", " ": " ", " ": " ", " ": " ", " ": " ", "​": "", "⁠": "", "­": ""}


def tidy(s: str) -> str:
    """Replace characters the card font cannot draw (non-breaking hyphen, thin spaces, zero-width marks) with plain ones."""
    return "".join(_ODD.get(ch, ch) for ch in s or "")


def repair(s: str) -> str:
    """Drop the minimisers ("only 3 km" -> "3 km", "फक्त 3 km" -> "3 km") and tidy the spacing; a claim is not repaired
    (problems_in rejects it). The first letter keeps its case ("Just 3 km" -> "3 km")."""
    if not s or not MINIMISER.search(s):
        return s
    out = MINIMISER.sub("", s)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"(?m)^[ \t]+|[ \t]+(?=[.,!?:;])", "", out)
    if s[:1].isupper() and out[:1].islower():
        out = out[0].upper() + out[1:]
    return out


def words(s: str) -> List[str]:
    return WORD.findall(s or "")


def word_count(s: str) -> int:
    return len(words(s))


def strip_tags(s: str) -> str:
    return HASHTAG.sub("", s or "")


def numbers(s: str) -> List[str]:
    body = re.sub(r"(?m)^\s*\d+[.)]\s+", "", strip_tags(s))  # "1. first item" numbering is not a claim
    return [n.replace(",", "") for n in NUMBER.findall(body)]


def unsupported_numbers(text: str, corpus: str) -> List[str]:
    """Numbers in `text` that do not occur in the supplied facts (`corpus`)."""
    allowed = set(numbers(corpus))
    return [n for n in numbers(text) if n not in allowed]


_NOT_A_NAME = {"the", "a", "an", "our", "your", "their", "this", "these", "those", "some", "many", "most", "all", "ask", "local"}


def unsupported_orgs(text: str, corpus: str) -> List[str]:
    """Builder or company names in `text` that the facts do not contain ("The Builders" is not a name)."""
    low = (corpus or "").lower()
    out = []
    for m in ORG.finditer(text):
        name = m.group(0)
        if all(w.lower() in _NOT_A_NAME for w in name.split()[:-1]):
            continue
        if name.lower() not in low:
            out.append(name)
    return out


def filler_hits(text: str) -> List[str]:
    low = (text or "").lower()
    return [f for f in FILLER if f in low]


def problems_in(text: str, corpus: str, *, allow_url: bool = False) -> List[str]:
    """Reasons a piece of copy must not be used (empty list means clean). The corpus is the brief's facts."""
    out: List[str] = []
    t = strip_tags(text)
    if HYPE.search(t):
        out.append("hype word")
    if PHONE.search(t):
        out.append("phone number")
    if PRICE.search(t) and not PRICE.search(corpus):
        out.append("price")
    if PREDICT.search(t):
        out.append("prediction")
    if TITLE_NAME.search(t):
        out.append("personal name")
    orgs = unsupported_orgs(t, corpus)
    if orgs:
        out.append("name not in facts: " + ", ".join(orgs))
    if CLICKBAIT.search(t):
        out.append("clickbait")
    if VALUE_CLAIM.search(t):
        out.append("value claim")
    if PROMISE.search(t):
        out.append("promise")
    if TAP.search(t):
        out.append("tap or click")
    if MINIMISER.search(t):
        out.append("only/just")
    if SAMPLE.search(t) and not SAMPLE.search(corpus or ""):  # a project really named "Sample ..." may be named
        out.append("sample")
    claims = [m.group(0) for m in CLAIM.finditer(t) if m.group(0).lower() not in (corpus or "").lower()]
    if claims:
        out.append("claim not in facts: " + ", ".join(claims))
    if not allow_url and URL.search(t):
        out.append("url")
    bad = unsupported_numbers(t, corpus)
    if bad:
        out.append("number not in facts: " + ", ".join(bad))
    hits = filler_hits(t)
    if hits:
        out.append("filler: " + ", ".join(hits))
    return out
