"""Project and area information ('about') from the agent's own words, plus curated area facts.

Rule: nothing is invented. Every item is either matched in the agent's text by a keyword rule (or proposed by the
LLM and then checked word by word against the agent's text) or comes from area_seed.py. Items carry
`source: 'agent' | 'area_guide'` in suggestions so the agent sees where each line came from.
"""
import asyncio
import logging
import re
from typing import Any, Optional

from .area_seed import AREA_SEED, area_key
from .extract_text import parse_amenities, parse_project
from .llm import LLM_TIMEOUT
from .text_norm import normalise

log = logging.getLogger(__name__)
MAX_TEXT = 6000
MAX_HIGHLIGHTS = 6

# phrase shown -> pattern over normalised (lower-case, Devanagari keywords mapped) text. Hinglish included.
_HIGHLIGHTS: dict[str, str] = {
    "East facing": r"east[\s-]*facing|purv mukhi|poorv mukhi|east face",
    "West facing": r"west[\s-]*facing",
    "North facing": r"north[\s-]*facing",
    "South facing": r"south[\s-]*facing",
    "Corner flat": r"corner (?:flat|unit|apartment|house)",
    "Park facing": r"park[\s-]*facing|garden[\s-]*facing",
    "Road facing": r"road[\s-]*facing",
    "Good natural light and ventilation": r"(?:natural|good|lot of) (?:light|ventilation)|hawadar|hawa aur roshni|airy|well ventilated",
    "Gated society": r"gated (?:society|community|complex)",
    "Newly constructed": r"new(?:ly)? (?:construction|built|constructed)|brand new building",
    "Well maintained": r"well[\s-]*maintained",
    "Quiet neighbourhood": r"quiet (?:area|locality|neighbou?rhood|society)|shaant|calm (?:area|society)",
    "Vastu compliant": r"vastu",
    "Ready to move": r"ready[\s-]*to[\s-]*move|(?<![a-z])rtm(?![a-z])",
    "Occupancy certificate received": r"(?:oc|occupancy certificate) (?:received|available|done)|oc received",
    "Resale flat": r"resale",
    "Lake view": r"lake[\s-]*view",
    "Open terrace": r"open terrace",
}
_HL_RES = [(k, re.compile(r"(?<![a-z])(?:" + p + r")(?![a-z])")) for k, p in _HIGHLIGHTS.items()]

# Hinglish amenity words not in the shared English vocabulary
_HINGLISH_AMEN = {
    "Parking": r"parking milegi|gaadi (?:ki )?parking|gadi (?:ki )?parking",
    "Lift": r"lift hai|lift available",
    "Security": r"watchman|chowkidar|guard hai",
    "Power backup": r"generator|backup hai|bijli backup|light jaane",
    "24x7 water": r"24 ?(?:ghante|hours|hrs) (?:paani|pani|water)|(?:paani|pani) 24|24x7 (?:paani|pani)|(?:paani|pani) (?:ki )?(?:dikkat|problem) nahi",
}
_HI_AM_RES = [(k, re.compile(p)) for k, p in _HINGLISH_AMEN.items()]

_NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "ek": 1, "do": 2, "teen": 3, "char": 4, "1": 1, "2": 2, "3": 3, "4": 4}
_PARK = re.compile(
    r"(?<![a-z0-9])(?:(?P<n>one|two|three|four|ek|do|teen|char|[1-4])\s*(?:x\s*)?)?(?P<kind>covered|open|car|bike|two[\s-]*wheeler|stilt|basement|reserved)?\s*(?:car\s*)?parking(?:s)?(?![a-z])")
_WATER = (
    (re.compile(r"24\s*[x*]\s*7 water|24 ?(?:hours?|hrs) water|24 ?(?:ghante|hours|hrs) (?:paani|pani)|(?:paani|pani) 24"), "24x7 water supply"),
    (re.compile(r"(?<![a-z])(?:municipal|corporation|pmc|pcmc) water|nagar palika"), "Municipal water supply"),
    (re.compile(r"(?<![a-z])borewell|bore well"), "Borewell water"),
    (re.compile(r"(?<![a-z])tanker"), "Tanker water"),
)
_POWER = (
    (re.compile(r"(?:full|100%?) (?:power )?backup|full backup|complete backup"), "Full power backup"),
    (re.compile(r"(?:lift|common area)s?(?: and| &|,)? (?:common areas? )?(?:power )?backup|backup (?:for|in) (?:lift|common)"), "Power backup for lifts and common areas"),
    (re.compile(r"power backup|generator|dg backup|inverter|(?<![a-z])backup hai|bijli backup"), "Power backup available"),
)
_MAINT = re.compile(
    r"maintenance\s*(?:charges?|is|of|:|-|rs\.?|inr|₹)?\s*(?:rs\.?|inr|₹)?\s*(?P<amt>\d[\d,]*(?:\.\d+)?)\s*(?P<k>k|thousand)?\s*(?:/|per|a|pm|p\.m|each)?\s*(?P<per>month|mo|mahina|mahine|year|yr|annum|quarter|sq ?ft|psf)?")
_NEAR = re.compile(
    r"(?<![a-z])(?:near(?:by)?|opp(?:osite)?|next to|walking distance (?:to|from)|close to)\s+(?P<name>(?:[A-Za-z][\w'.&]*\s+){0,3}?(?:school|hospital|college|market|mall|park|metro station|bus stop|bus stand|railway station|garden))(?![a-z])", re.I)
_NEAR_GENERIC = (
    ("school", re.compile(r"school (?:nearby|near by|close|paas|pass|ke paas|jawal)|(?:nearby|paas mein|paas me) school|school (?:is )?within walking")),
    ("hospital", re.compile(r"hospital (?:nearby|near by|close|paas|ke paas)|(?:nearby|paas mein|paas me) hospital")),
    ("market", re.compile(r"market (?:nearby|near by|close|paas|ke paas)|(?:nearby|paas mein|paas me) market|shopping nearby")),
    ("park", re.compile(r"park (?:nearby|near by|close|paas|ke paas)|(?:nearby|paas mein|paas me) (?:park|garden)")),
)
_GENERIC_NAME = {"school": "School nearby", "hospital": "Hospital nearby", "market": "Market nearby", "park": "Park nearby"}
_NEAR_TYPE = (("school", "school|college"), ("hospital", "hospital"), ("market", "market|mall"), ("park", "park|garden"),
              ("transit", "metro|bus|railway"))
_SOCIETY = (
    (re.compile(r"gated (?:society|community|complex)"), "Gated society"),
    (re.compile(r"co-?operative (?:housing )?society|(?<![a-z])chs(?![a-z])"), "Co-operative housing society"),
)
_PHONEISH = re.compile(r"\d[\s\-.]?\d[\s\-.]?\d[\s\-.]?\d[\s\-.]?\d[\s\-.]?\d[\s\-.]?\d[\s\-.]?\d[\s\-.]?\d[\s\-.]?\d")


def _n_words(n: Optional[str]) -> str:
    return {"one": "1", "ek": "1", "two": "2", "do": "2", "three": "3", "teen": "3", "four": "4", "char": "4"}.get(n or "", n or "")


def _rupees(amt: str, k: Optional[str]) -> Optional[int]:
    try:
        v = float(amt.replace(",", ""))
    except ValueError:
        return None
    if k:
        v *= 1000
    return int(v) if 100 <= v <= 1_000_000 else None


def _inr(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return "₹" + ",".join(parts + [tail])


def extract_about(text: str) -> dict[str, Any]:
    """Deterministic: the `about` fields found in the agent's words, in the stored shape. {} when nothing is found."""
    raw = (text or "")[:MAX_TEXT]
    t = normalise(raw)
    if not t:
        return {}
    out: dict[str, Any] = {}

    highlights = [k for k, rx in _HL_RES if rx.search(t)][:MAX_HIGHLIGHTS]
    amen = parse_amenities(t)
    for k, rx in _HI_AM_RES:
        if k not in amen and rx.search(t):
            amen.append(k)
    if amen:
        out["amenities"] = amen
    if highlights:
        out["highlights"] = highlights

    pk = None
    for m in _PARK.finditer(t):
        n, kind = _n_words(m.group("n")), (m.group("kind") or "").replace("-", " ")
        pk = " ".join(x for x in (n, kind, "parking") if x).capitalize()
        if n or kind:
            break
    if pk is None and re.search(r"parking milegi|parking hai|parking available", t):
        pk = "Parking available"
    if pk == "Parking":
        pk = "Parking available"
    if pk:
        out["parking"] = pk

    for rx, label in _WATER:
        if rx.search(t):
            out["water"] = label
            break
    for rx, label in _POWER:
        if rx.search(t):
            out["power_backup"] = label
            break

    m = _MAINT.search(t)
    if m:
        amt = _rupees(m.group("amt"), m.group("k"))
        per = (m.group("per") or "")
        if amt:
            unit = {"month": "per month", "mo": "per month", "mahina": "per month", "mahine": "per month",
                    "year": "per year", "yr": "per year", "annum": "per year", "quarter": "per quarter",
                    "sqft": "per sq ft", "sq ft": "per sq ft", "psf": "per sq ft"}.get(per, "")
            out["maintenance"] = f"{_inr(amt)} {unit}".strip()

    for rx, label in _SOCIETY:
        if rx.search(t):
            out["society"] = label
            break

    nearby: list[dict] = []
    for m in _NEAR.finditer(raw):
        name = " ".join(m.group("name").split())
        if _PHONEISH.search(name):
            continue
        low = name.lower()
        typ = next((ty for ty, p in _NEAR_TYPE if re.search(p, low)), "other")
        if len(name.split()) == 1:  # bare 'near school': say it as the generic line below
            continue
        if not any(n["name"].lower() == low for n in nearby):
            nearby.append({"type": typ, "name": name[:120]})
    for typ, rx in _NEAR_GENERIC:
        if rx.search(t) and not any(n["type"] == typ for n in nearby):
            nearby.append({"type": typ, "name": _GENERIC_NAME[typ]})
    if nearby:
        out["nearby"] = nearby[:6]

    project = parse_project(raw)
    if project:
        out["project_name"] = project
    return out


# ---- LLM proposals, kept only if traceable to the agent's own words ---------------------------------------------

_ABOUT_SYSTEM = (
    "You read a real-estate agent's message (English, Hindi, Marathi or Hinglish) and copy out facts about the project "
    "and area that the agent actually said. Reply with ONE JSON object with optional keys: highlights (array of short "
    "English lines, at most 6), amenities (array of short names), water, power_backup, maintenance, parking, society "
    "(short strings), nearby (array of {type: school|hospital|transit|office|market|park|other, name}). Use only what the "
    "message says. Never add facts, distances, prices or claims that are not in the message. Omit what is not mentioned."
)
_WORD = re.compile(r"[a-z0-9]{4,}")
_TYPES = {"school", "hospital", "transit", "office", "market", "park", "other"}


def traceable(item: str, text_norm: str) -> bool:
    """Every longer word of `item` (or its stem) appears in the agent's text."""
    words = _WORD.findall(item.lower())
    if not words:
        return False
    return all(w in text_norm or w[:-1] in text_norm or w[:4] in text_norm for w in words)


def sanitise_llm_about(raw: Any, text: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    tn = normalise(text)
    out: dict[str, Any] = {}

    def s(v: Any, n: int = 120) -> Optional[str]:
        if not isinstance(v, str):
            return None
        v = " ".join(v.split())[:n]
        return v if v and not _PHONEISH.search(v) and "http" not in v.lower() and traceable(v, tn) else None

    hl = [x for x in (s(v, 80) for v in (raw.get("highlights") or [])[:10] if isinstance(v, str)) if x][:MAX_HIGHLIGHTS]
    if hl:
        out["highlights"] = hl
    am: list[str] = []
    for v in (raw.get("amenities") or [])[:20]:
        if isinstance(v, str):
            am += [x for x in parse_amenities(v.lower()) if x not in am]  # only the known vocabulary
    if am:
        out["amenities"] = am
    for k in ("water", "power_backup", "maintenance", "parking", "society"):
        v = s(raw.get(k))
        if v:
            out[k] = v
    nb = []
    for n in (raw.get("nearby") or [])[:10]:
        if isinstance(n, dict):
            name = s(n.get("name"))
            if name:
                nb.append({"type": n.get("type") if n.get("type") in _TYPES else "other", "name": name})
    if nb:
        out["nearby"] = nb[:6]
    return out


def merge_about(det: dict[str, Any], llm: dict[str, Any]) -> dict[str, Any]:
    """Deterministic wins on scalars; lists are unioned (case-insensitive), capped."""
    out = dict(det)
    for k, v in llm.items():
        if k in ("highlights", "amenities"):
            cur = list(out.get(k, []))
            low = {c.lower() for c in cur}
            cur += [x for x in v if x.lower() not in low]
            out[k] = cur[:MAX_HIGHLIGHTS if k == "highlights" else 20]
        elif k == "nearby":
            cur = list(out.get(k, []))
            have = {(c["type"], c["name"].lower()) for c in cur}
            cur += [n for n in v if (n["type"], n["name"].lower()) not in have]
            out[k] = cur[:6]
        elif k not in out:
            out[k] = v
    return out


async def about_from_text(text: str, llm: Any = None) -> dict[str, Any]:
    """Deterministic extraction, plus LLM proposals when a model is configured (silent fallback on any failure)."""
    det = extract_about(text)
    fn = getattr(llm, "json", None) if llm is not None else None
    if fn is None or not (text or "").strip():
        return det
    try:
        raw = await asyncio.wait_for(fn(_ABOUT_SYSTEM, text[:4000]), LLM_TIMEOUT + 0.5)
    except Exception as e:
        log.info("ai_listing about LLM unavailable: %s", type(e).__name__)
        return det
    return merge_about(det, sanitise_llm_about(raw, text))


# ---- suggestion with source tags -----------------------------------------------------------------------------------

def _tag(items: list, source: str, key: str = "text") -> list[dict]:
    return [{key: i, "source": source} for i in items]


async def suggest_about(locality: Optional[str], project_name: Optional[str], bhk: Optional[float], text: str,
                        llm: Any = None) -> dict[str, Any]:
    """A DRAFT the agent must confirm. Agent items come from the agent's words; area_guide items only from area_seed."""
    found = await about_from_text(text, llm)
    out: dict[str, Any] = {
        "highlights": _tag(found.get("highlights", []), "agent"),
        "amenities": _tag(found.get("amenities", []), "agent"),
        "nearby": [{**n, "source": "agent"} for n in found.get("nearby", [])],
        "connectivity": [],
        "fields": {k: {"text": found[k], "source": "agent"} for k in
                   ("water", "power_backup", "maintenance", "parking", "society") if found.get(k)},
        "project_name": (project_name or found.get("project_name") or None),
        "area_known": False,
        "area_name": None,
    }
    key = area_key(locality)
    if key:
        seed = AREA_SEED[key]
        out["area_known"], out["area_name"] = True, seed["name"]
        out["connectivity"] = [{"text": c["text"], "source": "area_guide"} for c in seed["connectivity"]]
        have = {n["name"].lower() for n in out["nearby"]}
        out["nearby"] += [{"type": n["type"], "name": n["name"], "source": "area_guide"}
                          for n in seed["nearby"] if n["name"].lower() not in have]
    return out
