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
CLICKBAIT = re.compile(r"\b(you won'?t believe|shocking|secret they|doctors hate|this one trick|mind-?blowing|must[- ]see)\b", re.I)


_ODD = {"‐": "-", "‑": "-", "‒": "-", " ": " ", " ": " ", " ": " ", " ": " ", "​": "", "⁠": "", "­": ""}


def tidy(s: str) -> str:
    """Replace characters the card font cannot draw (non-breaking hyphen, thin spaces, zero-width marks) with plain ones."""
    return "".join(_ODD.get(ch, ch) for ch in s or "")


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
    if not allow_url and URL.search(t):
        out.append("url")
    bad = unsupported_numbers(t, corpus)
    if bad:
        out.append("number not in facts: " + ", ".join(bad))
    hits = filler_hits(t)
    if hits:
        out.append("filler: " + ", ".join(hits))
    return out
