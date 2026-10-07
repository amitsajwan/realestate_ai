"""Stage 1, Understand: decide in code (no LLM) whether a raw item is worth working on."""
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Dict, List

from app.core.areas import AREAS

from ..policy import AREA_KEYWORDS, AREA_PINCODES, BANNED, CORRIDOR_KEYWORDS, MAX_AGE_DAYS, PILLAR_KEYWORDS, PUNE_HINT
from ..types import RawItem, Relevance
from . import topics


def _phrase(p: str, plural: bool = False) -> "re.Pattern[str]":
    body = r"\s+".join(re.escape(w) for w in p.lower().split())
    return re.compile(r"(?<![a-z0-9])" + body + (r"(?:e?s)?" if plural else "") + r"(?![a-z0-9])")  # launch(es), bus(es)


_AREA_RE: Dict[str, List["re.Pattern[str]"]] = {a: [_phrase(k) for k in ks] for a, ks in AREA_KEYWORDS.items()}
_AREA_NAME_RE: Dict[str, List["re.Pattern[str]"]] = {
    a: [_phrase(k) for k in ks if k not in topics.LANDMARKS] for a, ks in AREA_KEYWORDS.items()}
# every area we cover, by the names people write (app.core.areas); the project register reads these
_CORE_NAME_RE: Dict[str, List["re.Pattern[str]"]] = {a.key: [_phrase(al) for al in a.aliases] for a in AREAS}
_OTHER_RE = [_phrase(k) for k in topics.OTHER_LOCALITIES]
_CORRIDOR_RE = [_phrase(k) for k in CORRIDOR_KEYWORDS]
_HINT_RE = [_phrase(k) for k in PUNE_HINT]
_PILLAR_RE: Dict[str, List["re.Pattern[str]"]] = {
    p: [_phrase(k, True) for k in list(ks) + topics.EXTRA_PILLAR_KEYWORDS.get(p, [])] for p, ks in PILLAR_KEYWORDS.items()}
_PIN = re.compile(r"(?<!\d)(\d{6})(?!\d)")
_EDU_RE = [_phrase(k, True) for k in topics.EDUCATION_KEYWORDS]

_HOROSCOPE = re.compile(r"\b(horoscope|zodiac|rashifal|astrology|lucky number)\b", re.I)
_CRIME = re.compile(
    r"\b(murder(ed)?|stabb?(ed|ing)|arrest(ed)?|theft|robbery|robbed|kidnap\w*|rape[ds]?|assault(ed)?|"
    r"molest\w*|killed|suicide|fir registered|accused|held for|cheating case|extortion|drunk driving|"
    r"fraud(ster)?s?|nabbed?|apprehend\w*|duped|swindl\w*|cheated|busted|smuggl\w*|detained|cisf)\b", re.I)
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


def _pin_areas(text: str) -> List[str]:
    return [AREA_PINCODES[p] for p in _PIN.findall(text) if p in AREA_PINCODES]


def named_areas(text: str) -> List[str]:
    """Keys of the areas (app.core.areas) named in `text`, in AREAS order, as whole words: "Wagholikar Heritage" is not
    Wagholi. "Upper Kharadi" names Kharadi too; callers that care pick the finer one."""
    low = (text or "").lower()
    return [a for a, pats in _CORE_NAME_RE.items() if any(p.search(low) for p in pats)]


def other_locality_named(text: str) -> bool:
    """True when `text` names a Pune locality we do not cover (topics.OTHER_LOCALITIES)."""
    low = (text or "").lower()
    return any(p.search(low) for p in _OTHER_RE)


def _news_named(text: str) -> List[str]:
    """Areas in the news scope (policy.AREA_KEYWORDS, landmarks do not count) named in `text`."""
    low = (text or "").lower()
    return [a for a, pats in _AREA_NAME_RE.items() if any(p.search(low) for p in pats)]


def _no(reason: str) -> Relevance:
    return Relevance(keep=False, reason=reason)


def assess(item: RawItem, now: datetime) -> Relevance:
    when = item.published_at or item.fetched_at
    if _aware(now) - _aware(when) > timedelta(days=MAX_AGE_DAYS):
        return _no(f"stale: older than {MAX_AGE_DAYS} days")
    title, body = item.title or "", item.text or ""
    full = f"{title}\n{body}".lower()

    first = re.split(r"(?<=[.!?])\s+|\n+", body.strip(), maxsplit=1)[0].lower() if body.strip() else ""
    head = f"{title}\n{first}".lower()

    # the area must be the subject (title or first sentence), not a passing mention further down
    areas = [a for a, pats in _AREA_RE.items() if any(p.search(head) for p in pats)]
    if areas and _hits(_OTHER_RE, head):  # a landmark alone does not make another locality's story ours
        areas = [a for a in areas if any(p.search(head) for p in _AREA_NAME_RE[a])]
    # pincodes are exact, so they count anywhere; a new-project item (MahaRERA gives "Haveli" in its headline) may name the
    # area only further down, so for those the whole text counts too, by name (a landmark alone is not enough), unless the
    # headline names another locality: "launches project in Hinjewadi ... 20 minutes from Kharadi" is Hinjewadi's story
    supply = (item.source.lower() == "maharera" or _hits(_PILLAR_RE["new_supply"], full) > 0) and not _hits(_OTHER_RE, head)
    body_areas = _pin_areas(full) + (_news_named(full) if supply else [])
    by_body = [a for a in dict.fromkeys(body_areas) if a not in areas]
    areas += by_body
    corridor = any(p.search(full) for p in _CORRIDOR_RE) and any(p.search(full) for p in _HINT_RE)
    if not areas and not corridor:
        mentioned = any(p.search(full) for pats in _AREA_RE.values() for p in pats)
        return _no("off-topic: area only mentioned in passing" if mentioned else "off-topic: no target area or corridor")

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

    label = topics.denied_topic(title, first)
    if label:
        return _no(f"non-buyer topic: {label}")
    if topics.short_lived(title, first):
        return _no("stale by nature: short-lived event or one-day traffic notice")

    scores = {}
    for pillar, pats in _PILLAR_RE.items():
        s = 2 * _hits(pats, title.lower()) + _hits(pats, body.lower())
        if s:
            scores[pillar] = s
    if not scores:
        return _no("no buyer relevance: no pillar keyword evidence")
    pillar = max(scores, key=scores.get)
    if by_body and supply and "new_supply" in scores and len(by_body) == len(areas):
        pillar = "new_supply"  # the area was found only because it is a new-project item
    # buyer-relevance score: pillar evidence, plus the area being in the headline
    in_title = any(p.search(title.lower()) for pats in _AREA_RE.values() for p in pats) or any(p.search(title.lower()) for p in _CORRIDOR_RE)
    score = scores[pillar] + (2 if in_title else 1 if areas else 0)  # area in the first sentence counts for less than in the headline
    if score < topics.MIN_SCORE:
        return _no(f"no buyer relevance: score {score} below {topics.MIN_SCORE}")
    why = (("areas: " + ", ".join(areas)) if areas else "corridor topic with Pune hint") + f"; score {score}"
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
