"""Stage 1, Understand: decide in code (no LLM) whether a raw item is worth working on."""
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Dict, List

from ..policy import AREA_KEYWORDS, BANNED, CORRIDOR_KEYWORDS, MAX_AGE_DAYS, PILLAR_KEYWORDS, PUNE_HINT
from ..types import RawItem, Relevance


def _phrase(p: str, plural: bool = False) -> "re.Pattern[str]":
    body = r"\s+".join(re.escape(w) for w in p.lower().split())
    return re.compile(r"(?<![a-z0-9])" + body + (r"s?" if plural else "") + r"(?![a-z0-9])")


_AREA_RE: Dict[str, List["re.Pattern[str]"]] = {a: [_phrase(k) for k in ks] for a, ks in AREA_KEYWORDS.items()}
_CORRIDOR_RE = [_phrase(k) for k in CORRIDOR_KEYWORDS]
_HINT_RE = [_phrase(k) for k in PUNE_HINT]
_PILLAR_RE: Dict[str, List["re.Pattern[str]"]] = {p: [_phrase(k, True) for k in ks] for p, ks in PILLAR_KEYWORDS.items()}

_HOROSCOPE = re.compile(r"\b(horoscope|zodiac|rashifal|astrology|lucky number)\b", re.I)
_CRIME = re.compile(
    r"\b(murder(ed)?|stabb?(ed|ing)|arrest(ed)?|theft|robbery|robbed|kidnap\w*|rape[ds]?|assault(ed)?|"
    r"molest\w*|killed|suicide|fir registered|accused|held for|cheating case|extortion|drunk driving)\b", re.I)
_CLASSIFIED = re.compile(
    r"^\s*(for (sale|rent)|wanted|required|urgent sale|resale)\b|\b(owner|direct from owner)\b.*\b(call|whatsapp)\b|"
    r"(\+?91[\s-]?)?\b[6-9]\d{9}\b|\bcall\s*(now|us|@)|\bwhatsapp\s*(now|us|@)", re.I)
_PROMO = re.compile(
    r"\b(bookings?\s+(are\s+)?(now\s+)?open|pre[- ]?launch|book\s+now|site visit)\b", re.I)
_STOP = {"the", "a", "an", "of", "in", "on", "to", "for", "and", "at", "by", "is", "as", "with", "from", "says", "after", "new"}


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _hits(patterns, text: str) -> int:
    return sum(1 for p in patterns if p.search(text))


def _no(reason: str) -> Relevance:
    return Relevance(keep=False, reason=reason)


def assess(item: RawItem, now: datetime) -> Relevance:
    when = item.published_at or item.fetched_at
    if _aware(now) - _aware(when) > timedelta(days=MAX_AGE_DAYS):
        return _no(f"stale: older than {MAX_AGE_DAYS} days")
    title, body = item.title or "", item.text or ""
    full = f"{title}\n{body}".lower()

    areas = [a for a, pats in _AREA_RE.items() if any(p.search(full) for p in pats)]
    corridor = any(p.search(full) for p in _CORRIDOR_RE) and any(p.search(full) for p in _HINT_RE)
    if not areas and not corridor:
        return _no("off-topic: no target area or corridor")

    if _HOROSCOPE.search(full):
        return _no("non-news: horoscope")
    if _CLASSIFIED.search(title) or _CLASSIFIED.search(body[:400]):
        return _no("non-news: classified ad or contact details")
    crime_words = {m.group(0).lower() for m in _CRIME.finditer(full)}
    if _CRIME.search(title) or len(crime_words) >= 2:
        return _no("non-news: crime or accident that only mentions the area")
    banned = {m.group(0).lower() for m in BANNED.finditer(full)}
    if banned and (_PROMO.search(full) or len(banned) >= 2):
        return _no("non-news: promotional hype")

    scores = {}
    for pillar, pats in _PILLAR_RE.items():
        s = 2 * _hits(pats, title.lower()) + _hits(pats, body.lower())
        if s:
            scores[pillar] = s
    pillar = max(scores, key=scores.get) if scores else "locality_life"
    why = ("areas: " + ", ".join(areas)) if areas else "corridor topic with Pune hint"
    return Relevance(keep=True, pillar=pillar, areas=areas, reason=why)


def _norm_title(t: str) -> List[str]:
    # drop a trailing " - Publisher" / " | Publisher"
    t = re.split(r"\s+[-|–—]\s+(?=[^-|–—]*$)", t.strip(), maxsplit=1)[0]
    return [w for w in re.sub(r"[^a-z0-9 ]+", " ", t.lower()).split() if w not in _STOP]


def same_story(a_title: str, b_title: str) -> bool:
    a, b = _norm_title(a_title), _norm_title(b_title)
    if not a or not b:
        return False
    sa, sb = set(a), set(b)
    jaccard = len(sa & sb) / len(sa | sb)
    ratio = SequenceMatcher(None, " ".join(a), " ".join(b)).ratio()
    overlap = len(sa & sb) / min(len(sa), len(sb))
    return jaccard >= 0.6 or ratio >= 0.85 or (len(sa & sb) >= 5 and overlap >= 0.75)
