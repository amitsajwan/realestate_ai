"""The safety net: pure code, no LLM. A draft that fails here never reaches the owner as "ready".

Every rule returns a short human-readable problem. Being wrong on the side of rejecting is fine; the owner can edit and re-check.
`marketing.polish` (HYPE, PHONE) is imported here and nowhere else in the newsroom (contract rule).
"""
import re
from datetime import datetime, timezone
from typing import List, Optional, Set

from app.modules.marketing.polish import HYPE, PHONE

from .. import policy
from ..types import CheckResult, Draft, Facts, RawItem

URL = re.compile(r"https?://\S+|www\.\S+", re.I)
HASHTAG = re.compile(r"#\w+")
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
MON = "|".join(m[:3] + r"[a-z]*\.?" for m in MONTHS)
UNITS = {"%": "%", "percent": "%", "per cent": "%", "crore": "cr", "crores": "cr", "cr": "cr", "lakh": "lakh", "lakhs": "lakh",
         "km": "km", "kms": "km", "kilometre": "km", "kilometres": "km", "kilometer": "km", "kilometers": "km",
         "acre": "acre", "acres": "acre", "hectare": "ha", "hectares": "ha", "months": "month", "month": "month",
         "years": "year", "year": "year", "days": "day", "day": "day", "bhk": "bhk", "metres": "m", "meters": "m"}
NUM = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?:st|nd|rd|th)?(?:\s*(%|per cent|percent|crores?|cr|lakhs?|kms?|kilomet(?:re|er)s?|acres?|hectares?|months?|years?|days?|bhk|metres|meters))?(?![\w])", re.I)
DATE_DM = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + MON + r")\b", re.I)
DATE_MD = re.compile(r"\b(" + MON + r")\s+(\d{1,2})(?:st|nd|rd|th)?\b", re.I)

# words that may be capitalised without being in the source (our voice, sentence starters, calendar words)
ALLOW = {"pune", "property", "team", "facebook", "hub", "kharadi", "wagholi", "upper", "rera", "bhk", "i", "ok", "it", "pm", "am", "faq"}
ALLOW |= {m[:3] for m in MONTHS} | {"sept"} | set(MONTHS) | {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
COMMON = set("""a about after all an and approved are as at be before buyers buyer can check comment did do does for from have here how
if in is it its more most new no not now of on one or our renters she so some source sources tell that the their then there these
they this to us was we were what when where which who why will with would you your worth own view according reported said says
latest please read save see share should so still tell thanks thank today update what's whether while yes home homes flat flats
house houses people families city area areas road roads metro line station project projects notice notices rules rule rate rates
loan loans important key quick short good note notes status checking heads ask compare confirm visit talk read look find try make keep use take get wait watch review verify approvals plans approval timeline timelines dates date notices official officials""".split())
COMMON |= {"heads-up", "kharadi's", "pune's"}

TRANSPORT = re.compile(r"\b(metro|railway|rail|station|line|flyover|bridge|road|highway|ring road|airport|corridor|bus|brts|tunnel)\b", re.I)
# claims that something is running or has opened; the source must use the same word near a transport word
TRANSPORT_CLAIMS = [
    (re.compile(r"\b(open|opens|opened|opening|opened to)\b", re.I), "open"),
    (re.compile(r"\b(operational|operations?|operating|running|runs)\b", re.I), "operat|running|runs"),
    (re.compile(r"\binaugurat\w*", re.I), "inaugurat"),
    (re.compile(r"\b(commissioned|commissioning)\b", re.I), "commission"),
    (re.compile(r"\b(launched|launches|launch)\b", re.I), "launch"),
    (re.compile(r"\b(completed|fully complete|ready for use|thrown open)\b", re.I), "completed|fully complete|ready for use|thrown open"),
]
NEGATED = re.compile(r"\b(not|no|yet|never|until|awaits?|awaiting)\b|n't", re.I)
PRICE_WORD = re.compile(r"\b(prices?|rates?|values?|rents?|rentals?|appreciation|returns?|valuations?)\b", re.I)
FORWARD = re.compile(r"\b(will|expected to|likely to|set to|poised to|bound to|going to|predict\w*|forecast\w*|projected to|to (?:rise|jump|surge|climb|soar|double))\b", re.I)
BUILDER_WORD = re.compile(r"\b(builders?|developers?|promoters?|bilders?)\b|\b[A-Z][a-z]+ (?:Developers|Builders|Constructions|Realty|Group|Infra|Properties|Estates|Lifespaces|Homes)\b")
OPINION = re.compile(r"\b(reliable|trusted?|trustworthy|best|top|excellent|renowned|reputed|reputable|leading|great|fraud\w*|cheat\w*|scam\w*|poor|bad|worst|"
                     r"avoid|recommend\w*|shoddy|unreliable|untrustworthy|admired|well[- ]known|known for|quality|superb|amazing)\b", re.I)
WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*")


def _words(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9₹]+", text)]


def _norm(w: str) -> str:
    w = w.lower().replace("’", "'")
    if w.endswith("'s"):
        w = w[:-2]
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def _num(s: str) -> str:
    s = s.replace(",", "")
    return s.rstrip("0").rstrip(".") if "." in s else s


def _figures(text: str):
    """(bare numbers, number+unit pairs, (day, month3) pairs) found in text, links and hashtags ignored."""
    t = HASHTAG.sub(" ", URL.sub(" ", text))
    nums, units = set(), set()
    for m in NUM.finditer(t):
        n = _num(m.group(1))
        nums.add(n)
        if m.group(2):
            units.add((n, UNITS.get(m.group(2).lower(), m.group(2).lower())))
    dates = {(int(a), b[:3].lower()) for a, b in DATE_DM.findall(t)} | {(int(b), a[:3].lower()) for a, b in DATE_MD.findall(t)}
    return nums, units, dates


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", URL.sub(" ", text)) if s.strip()]


def _sentence_start(text: str, start: int) -> bool:
    before = text[:start]
    stripped = before.rstrip()
    if not stripped or "\n" in before[len(stripped):]:
        return True
    last = stripped[-1]
    return not last.isalnum() and last not in ",;&'-"


def _unknown_names(text: str, known: Set[str], allowed: Set[str]) -> List[str]:
    t = HASHTAG.sub(" ", URL.sub(" ", text))
    bad: List[str] = []
    for m in WORD.finditer(t):
        w = m.group(0)
        if not (w[0].isupper()):
            continue
        n = _norm(w)
        if n in known or n in allowed or w.lower() in ALLOW or w.lower() in allowed:
            continue
        if _sentence_start(t, m.start()) and (w.lower() in COMMON or n in COMMON) and not w.isupper():
            continue
        if w not in bad:
            bad.append(w)
    return bad


def check(draft: Draft, facts: Facts, item: RawItem, now: Optional[datetime] = None) -> CheckResult:
    problems: List[str] = []
    full = ((draft.title or "") + "\n" + draft.text).strip()
    source = (item.title or "") + "\n" + (item.text or "")
    now = now or datetime.now(timezone.utc)

    # 1. Figures: every number, date and unit-bound figure must be in the source
    s_nums, s_units, s_dates = _figures(source)
    anchor = facts.as_of or item.published_at
    for d in (facts.as_of, item.published_at):  # the 'as of' date itself may be stated
        if d:
            s_nums |= {str(d.day), str(d.year)}
            s_dates.add((d.day, d.strftime("%b").lower()))
    d_nums, d_units, d_dates = _figures(full)
    missing = sorted(n for n in d_nums if n not in s_nums)
    if missing:
        problems.append("Figures not found in the source: " + ", ".join(missing))
    wrong_units = sorted(f"{n} {u}" for n, u in d_units if (n, u) not in s_units and n in s_nums)
    if wrong_units:
        problems.append("Figure with a unit the source does not give: " + ", ".join(wrong_units))
    bad_dates = sorted(f"{d} {m.title()}" for d, m in d_dates if (d, m) not in s_dates)
    if bad_dates:
        problems.append("Date not found in the source: " + ", ".join(bad_dates))

    # 2. Proper nouns must come from the source or our own allowlist
    known = {_norm(w) for w in _words(source + " " + item.source + " " + " ".join(draft.source_names))}
    names = _unknown_names(full.replace(policy.DISCLAIMER, " "), known, set())
    if names:
        problems.append("Names not in the source: " + ", ".join(names[:8]))

    # 3. Banned, hype, phone
    for label, rx in (("Banned phrase", policy.BANNED), ("Hype word", HYPE), ("Phone number", PHONE)):
        m = rx.search(full)
        if m:
            problems.append(f"{label}: '{m.group(0).strip()}'")

    # 4. No long runs copied from the source, no copied headline
    n = policy.MAX_QUOTE_WORDS + 1
    src_words, dr_words = _words(source), _words(full)
    grams = {tuple(src_words[i:i + n]) for i in range(len(src_words) - n + 1)}
    if any(tuple(dr_words[i:i + n]) in grams for i in range(len(dr_words) - n + 1)):
        problems.append(f"Copies more than {policy.MAX_QUOTE_WORDS} words in a row from the source: reword it")
    t_words = _words(item.title or "")
    if len(t_words) >= 5 and " ".join(t_words) in " ".join(dr_words):
        problems.append("Repeats the source headline: write our own")

    # 5. Source name and link
    if not [s for s in draft.source_names if s and s.strip()]:
        problems.append("No source name")
    if not (draft.link or URL.search(draft.text)):
        problems.append("No link to the source")

    # 6. Post limits: length and a question
    if draft.format == "post":
        if len(draft.text) > policy.POST_MAX_CHARS:
            problems.append(f"Post is {len(draft.text)} characters; the limit is {policy.POST_MAX_CHARS}")
        if "?" not in HASHTAG.sub(" ", URL.sub(" ", draft.text)):
            problems.append("A post must end with a question")

    # 7. Sentence-level rules: price predictions, builder opinions, transport claims
    src_sentences = [s.lower() for s in _sentences(source)]
    for s in _sentences(full):
        if PRICE_WORD.search(s) and FORWARD.search(s):
            problems.append(f"Looks like a price prediction: '{s[:90]}'")
        if BUILDER_WORD.search(s) and OPINION.search(s):
            problems.append(f"Praises or criticises a builder: '{s[:90]}'")
        if TRANSPORT.search(s):
            for rx, stem in TRANSPORT_CLAIMS:
                if rx.search(s) and not NEGATED.search(s) and not any(re.search(stem, x) and TRANSPORT.search(x) for x in src_sentences):
                    problems.append(f"Transport claim ('{rx.search(s).group(0)}') the source does not make: '{s[:90]}'. Approved is not running")
                    break

    # 8. Freshness and the as-of date
    if anchor is None:
        problems.append("No date for this item, so it cannot be labelled 'as of'")
    else:
        a = anchor if anchor.tzinfo else anchor.replace(tzinfo=timezone.utc)
        age = (now - a).days
        if age > policy.MAX_AGE_DAYS:
            problems.append(f"Item is {age} days old; the limit is {policy.MAX_AGE_DAYS}")
        if not re.search(r"\bas of\b", full, re.I):
            problems.append("Missing an 'as of' date line")
    return CheckResult(ok=not problems, problems=problems)
