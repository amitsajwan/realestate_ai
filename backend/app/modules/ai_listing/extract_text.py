"""Deterministic keyword parsers: property type, furnishing, possession, amenities, RERA, project name."""
import re
from typing import Optional

from .gazetteer import CITIES, LOCALITIES

NEAR_CLAUSE = re.compile(r"(?<![a-z])(?:near|nearby|opp|opposite|behind|adjacent to|next to|close to|beside)(?:\s+[a-z][a-z']*){1,3}")


def strip_near(t: str) -> str:
    return NEAR_CLAUSE.sub(" ", t)


_TYPES = (
    ("plot", r"plot|plots|land|zameen|jamin|jaga|bhukhand|farm ?land|plotting|n\.?a\.? plot"),
    ("villa", r"villa|villas|bungalow|bungalows|bangla|row ?house|rowhouse|row ?houses"),
    ("shop", r"shop|shops|showroom|dukan|dukaan|retail space"),
    ("office", r"office|offices|co-?working"),
    ("commercial", r"commercial|godown|warehouse|industrial|factory|hotel|mall|business space"),
    ("house", r"independent house|house|kothi|ghar|tenement"),
    ("apartment", r"flat|flats|apartment|apartments|apt|bhk|studio|penthouse|builder floor|condo|1 ?rk"),
)
_TYPE_RES = [(k, re.compile(r"(?<![a-z])(?:" + p + r")(?![a-z])")) for k, p in _TYPES]


def parse_type(clean: str, has_bhk: bool) -> Optional[tuple[str, float]]:
    for k, rx in _TYPE_RES:
        if rx.search(clean):
            return k, 0.9
    return ("apartment", 0.6) if has_bhk else None


def parse_furnishing(t: str) -> Optional[tuple[str, float]]:
    if re.search(r"un-?furnish|bare ?shell|not furnished|no furniture", t):
        return "unfurnished", 0.9
    if re.search(r"semi[\s-]*furnish|part(?:ly|ially)? furnish", t):
        return "semi", 0.9
    if re.search(r"(?:fully|full)[\s-]*furnish|furnished|furnishing done", t):
        return "furnished", 0.9
    return None


_MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
_DATE = re.compile(r"(?<![a-z])(?P<m>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*[',\-]?\s*(?P<y>20\d{2})(?!\d)")
_YEAR_POSS = re.compile(r"(?:possession|handover|delivery|completion)\s*(?:by|in|from|date|on|:|-)?\s*(?:year\s*)?(?P<y>20\d{2})(?!\d)")
_POSS_WORD = re.compile(r"possession|handover|ready by|delivery|completion|poss\b")
_READY = re.compile(r"ready[\s-]*to[\s-]*move|(?<![a-z])rtm(?![a-z])|ready possession|possession ready|immediate possession|"
                    r"immediate|ready flat|ready property|(?<![a-z])ready(?![a-z])|oc received|occupancy certificate|"
                    r"possession available|move[\s-]*in ready")
_UC = re.compile(r"under[\s-]*construction|(?<![a-z])u/c(?![a-z])|(?<![a-z])uc(?![a-z])|new launch|pre[\s-]*launch|"
                 r"ongoing project|not ready")


def parse_possession(t: str) -> Optional[tuple[str, float]]:
    for m in _DATE.finditer(t):
        ctx = t[max(0, m.start() - 25):m.end() + 25]
        if _POSS_WORD.search(ctx):
            return f"{m.group('y')}-{_MONTHS[m.group('m')]:02d}", 0.95
    m = _YEAR_POSS.search(t)
    if m:
        return m.group("y"), 0.9
    if _UC.search(t):
        return "under_construction", 0.9
    if _READY.search(t):
        return "ready", 0.9
    return None


AMENITIES: dict[str, str] = {
    "Parking": r"parking|car park|garage",
    "Lift": r"lifts?|elevators?",
    "Gym": r"gym|gymnasium|fitness cent(?:er|re)",
    "Swimming pool": r"swimming pool|pool",
    "Garden": r"garden|landscaped|lawn",
    "Security": r"security|guard|cctv|gated",
    "Power backup": r"power backup|generator|dg backup|inverter|full backup",
    "Clubhouse": r"club ?house",
    "Play area": r"play area|children'?s? play|kids play|play ground|playground",
    "Terrace": r"terrace",
    "Balcony": r"balcon(?:y|ies)",
    "Intercom": r"intercom",
    "Vastu compliant": r"vastu",
    "Modular kitchen": r"modular kitchen",
    "24x7 water": r"24\s*[x*]\s*7 water|water supply|borewell",
    "Jogging track": r"jogging track",
    "Servant room": r"servant room",
}
_AM_RES = [(k, re.compile(r"(?<![a-z])(?:" + p + r")(?![a-z])")) for k, p in AMENITIES.items()]


def parse_amenities(clean: str) -> list[str]:
    return [k for k, rx in _AM_RES if rx.search(clean)]


_RERA_MH = re.compile(r"(?<![a-z0-9])(p\d{11})(?!\d)", re.I)
_RERA_GEN = re.compile(r"rera\s*(?:reg\w*\.?|no\.?|number|id)?\s*(?:no\.?|number)?\s*[:#\-]?\s*([a-z0-9][a-z0-9/\-]{7,})", re.I)


def parse_rera(raw: str) -> Optional[str]:
    m = _RERA_MH.search(raw) or _RERA_GEN.search(raw)
    return m.group(1).upper() if m and re.search(r"\d", m.group(1)) else None


_STOP = {"in", "at", "near", "the", "for", "flat", "sale", "rent", "bhk", "ready", "new", "a", "an", "and", "with",
         "prime", "good", "excellent", "very", "best", "top", "fully", "semi", "under", "spacious", "beautiful",
         "luxury", "luxurious", "available", "sell", "selling", "on", "of", "to", "my", "our", "hi", "hello", "urgent"}
_PROJ_SUFFIX = (r"Heights?|Towers?|Residency|Residences?|Apartments?|Enclave|Park|Society|CHS|Complex|Gardens?|Villas?|"
                r"Homes|Greens|Paradise|Arcade|Plaza|Meadows|Estate|Elite|Icon|Skyline|Casa|Nest|Vista|Bliss|Orchid|Sky|"
                r"Square|Court|Woods|Enclaves|Paradiso|Utopia|Grandeur")
_PROJECT = re.compile(r"((?:[A-Z][A-Za-z0-9'&]+\s+){1,3}(?:" + _PROJ_SUFFIX + r"))(?![A-Za-z])")
_PROJECT_CUE = re.compile(r"(?:project|society|building|complex)\s*(?:name)?\s*(?:is|:|-)?\s*([A-Z][A-Za-z0-9']+(?:\s+[A-Z][A-Za-z0-9']+){0,3})")
_IN_AT = re.compile(r"(?:(?<![A-Za-z])(?:in|at|In|At)|@)\s+([A-Z][A-Za-z']+(?:\s+[A-Z][A-Za-z']+){0,2})")
_GEO_WORDS = {a.lower() for c, al in CITIES.items() for a in (c, *al)} | {k.lower() for k in LOCALITIES}
_BAD_LOC = {"ready", "prime", "excellent", "good", "rent", "sale", "lakh", "cr", "crore", "semi", "fully", "bhk", "flat",
            "furnished", "the", "a", "an", "top", "new"}


def _clean_words(s: str) -> str:
    words = s.split()
    while words and words[0].lower() in _STOP:
        words.pop(0)
    return " ".join(words)


def parse_project(raw: str) -> Optional[str]:
    cue = _PROJECT_CUE.search(raw)
    cands = []
    if cue:
        cands.append(_clean_words(cue.group(1)))
    for m in _PROJECT.finditer(raw):
        cands.append(_clean_words(m.group(1)))
    for c in cands:
        low = c.lower()
        if c and " " in c or (c and low not in _GEO_WORDS and low not in _STOP):
            if low not in _GEO_WORDS and len(c) > 2:
                return c
    return None


def parse_unknown_locality(raw: str, project: Optional[str]) -> Optional[str]:
    """'in/at <Capitalised Words>' that is neither a known place nor the project."""
    for m in _IN_AT.finditer(raw):
        words = _clean_words(m.group(1))
        low = words.lower()
        if not words or low in _GEO_WORDS or low in _BAD_LOC or (project and words in project):
            continue
        if re.search(_PROJ_SUFFIX + "$", words):
            continue
        return words
    return None
