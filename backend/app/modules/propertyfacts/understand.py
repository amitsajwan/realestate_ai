"""Understand a listing before its posts are made (jobs.MarketingRuns, between the facts and the posts).

The agent gives the minimum (a name or MahaRERA number, a price, a brochure or video). This works out the rest:

    property_type    plot, flat, house... (the agent's own choice wins)
    listing_scope    "single" (one plot or flat on offer) or "layout" (a whole project: many plots or flats)
    size_min_sqft    the sizes on offer; for a single unit both are its size
    size_max_sqft
    total_acres      the project's land, for a layout
    rera_status      "not_registered" when the agent says so (a registered project carries rera_no instead)

A model reads the agent's text and the builder's claims (brochure, video) into candidate values; code decides. A value is
filled in without asking only when it is certain (the agent's own field, MahaRERA, or a plain reading the code can check).
A brochure-only number, two numbers that disagree, or a missing registration becomes a short question with choices. Only
values the agent set or confirmed reach the posts (gather.LISTING_KEYS reads them from the listing as the agent's offer)."""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.rera import BODY

from .facts import same

log = logging.getLogger(__name__)

MAX_QUESTIONS = 6
RERA_NO = re.compile(rf"^{BODY}$", re.I)   # either form (core/rera.py)
SCOPES = ("single", "layout")
TYPES = ("plot", "apartment", "house", "villa", "commercial", "office", "shop")
TYPE_WORD = {"plot": "plot", "apartment": "flat", "house": "house", "villa": "villa"}
KEYS = ("property_type", "listing_scope", "sizes", "total_acres", "rera")

SYSTEM = "You read an Indian real-estate listing and its builder's material into plain fields. Reply with JSON only."
USER = """The agent's listing:
{listing}

What the builder's brochure and video say (may repeat or disagree):
{claims}

Fill these from the text above only; null when it does not say:
- property_type: plot | apartment | house | villa | commercial | null  (flat = apartment; NA plot, bungalow plot = plot)
- scope: "layout" when it is a whole project with many plots or flats on offer, "single" when it is one plot or flat, or null
- scope_sure: true only when the text says so plainly (a number of plots, "plots available", "layout"; or one unit's details)
- sizes_sqft: every plot or flat size on offer, in sq ft as numbers (convert sq yd x9, sq m x10.764, guntha x1089); []
- total_acres: every land area of the whole project mentioned, in acres as numbers (copy each one, even when they differ); []
- other_registration: any registration or survey number that is NOT a MahaRERA number (P + 11 digits, or PR, PP or PM + 13 digits), copied as written, or ""
Reply: {{"property_type": ..., "scope": ..., "scope_sure": ..., "sizes_sqft": [...], "total_acres": [...], "other_registration": ""}}"""


def _num(x: Any) -> Optional[float]:
    try:
        v = float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def _distinct(values: List[float]) -> List[float]:
    out: List[float] = []
    for v in values:
        if not any(same(v, o) for o in out):
            out.append(v)
    return out


def _in_text(v: float, text: str) -> bool:
    """A number the model gives must be printed in the text (as written, or converted from sq yd/sq m/guntha): no invented sizes."""
    digits = {re.sub(r"[,\s]", "", m) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}
    nums = {float(d) for d in digits if d.replace(".", "", 1).isdigit()}
    return any(same(v, n) or same(v, n * 9) or same(v, n * 10.764) or same(v, n * 1089) for n in nums)


def _fmt(v: float) -> str:
    return f"{v:,.0f}" if v == int(v) else f"{v:,.2f}".rstrip("0").rstrip(".")


def listing_text(listing: dict) -> str:
    d = listing.get("description") or {}
    parts = [listing.get("title") or "", d.get("en") or "", d.get("mr") or "", d.get("hi") or ""]
    for k in ("property_type", "project_name", "locality", "price_inr", "carpet_sqft", "bhk"):
        if listing.get(k):
            parts.append(f"{k}: {listing[k]}")
    return "\n".join(p for p in parts if p)


async def read(listing: dict, claims: List[str], llm) -> Dict[str, Any]:
    """The model's candidate values, with every number checked against the text. {} without a model or on failure."""
    if llm is None:
        return {}
    text, said = listing_text(listing), "\n".join(f"- {c}" for c in claims) or "(nothing)"
    try:
        data = await llm.json(SYSTEM, USER.format(listing=text[:3000], claims=said[:4000])) or {}
    except Exception:
        log.info("understand: the model could not read the listing", exc_info=True)
        return {}
    source = text + "\n" + said
    out: Dict[str, Any] = {}
    if data.get("property_type") in TYPES:
        out["property_type"] = data["property_type"]
    if data.get("scope") in SCOPES:
        out["scope"], out["scope_sure"] = data["scope"], bool(data.get("scope_sure"))
    out["sizes"] = _distinct([v for v in (_num(x) for x in data.get("sizes_sqft") or []) if v and _in_text(v, source)])
    out["acres"] = _distinct([v for v in (_num(x) for x in data.get("total_acres") or []) if v and _in_text(v, source)])
    other = str(data.get("other_registration") or "").strip()
    out["other_registration"] = other[:40] if other and not RERA_NO.match(other) else ""
    return out


def _q(key: str, text: str, options: List[Tuple[str, Any]], free_text: str = "") -> dict:
    q = {"key": key, "text": text, "options": [{"label": l, "value": v} for l, v in options]}
    if free_text:
        q["free_text"] = free_text
    return q


def decide(listing: dict, seen: Dict[str, Any], registered: bool, units_total: Optional[int] = None,
           has_files: bool = True, unreadable: bool = False, candidates: Optional[List[dict]] = None,
           points: Optional[List[dict]] = None) -> Tuple[Dict[str, Any], List[dict]]:
    """(fields to set now, questions for the agent). `registered`: the facts already hold a usable MahaRERA number;
    `units_total`: MahaRERA's count of units, when known; `has_files`: a brochure or video is attached; `points`: the
    brochure's selling points not yet confirmed or dismissed (points.pending). Pure: no I/O."""
    auto: Dict[str, Any] = {}
    ask: List[dict] = []
    if not has_files:  # asked first: agents often start before uploading, and the files change everything below
        lead = "The brochure PDF could not be read and no video is attached." if unreadable else "No brochure or video is attached."
        ask.append(_q("files", f"{lead} Add them now (the posts get the builder's details and "
                      "pictures), or go on without?", [("I've added them now", "added"), ("Go on without", "skip")]))

    # what it is
    ptype = listing.get("property_type")
    if ptype and seen.get("property_type") and seen["property_type"] != ptype and {ptype, seen["property_type"]} & {"plot"}:
        ask.append(_q("property_type", f"The listing says {TYPE_WORD.get(ptype, ptype)}, the brochure reads like "
                      f"{TYPE_WORD.get(seen['property_type'], seen['property_type'])}. Which is it?",
                      [(TYPE_WORD.get(ptype, ptype).capitalize(), ptype),
                       (TYPE_WORD.get(seen["property_type"], seen["property_type"]).capitalize(), seen["property_type"])]))
    elif not ptype and seen.get("property_type"):
        ptype = auto["property_type"] = seen["property_type"]
    elif not ptype:
        ask.append(_q("property_type", "What is on offer?", [("Plot", "plot"), ("Flat", "apartment"), ("House", "house")]))
    word = TYPE_WORD.get(ptype or "", "unit")
    words = "flats" if word == "flat" else word + "s"

    # one unit or a whole project
    scope = listing.get("listing_scope")
    sizes = seen.get("sizes") or []
    if not scope:
        # MahaRERA's unit count and the brochure's several sizes outrank the wording ("a plot is available...")
        if len(sizes) > 1 or (units_total or 0) > 1:
            scope = auto["listing_scope"] = "layout"
        elif seen.get("scope") and seen.get("scope_sure"):
            scope = auto["listing_scope"] = seen["scope"]
        else:
            ask.append(_q("listing_scope", f"Is this one {word}, or a whole project with many {words}?",
                          [(f"One {word}", "single"), (f"Many {words} (a layout or project)", "layout")]))

    # sizes: the builder's numbers are confirmed once, never posted on their own
    if not listing.get("size_min_sqft") and sizes:
        lo, hi = min(sizes), max(sizes)
        if scope == "layout" and lo != hi:
            ask.append(_q("sizes", f"The brochure shows {word} sizes from {_fmt(lo)} to {_fmt(hi)} sq ft. Is that right?",
                          [("Yes", {"min": lo, "max": hi}), ("No / not sure", None)]))
        elif not listing.get("carpet_sqft") or lo == hi:
            pick = [(f"{_fmt(s)} sq ft", {"min": s, "max": s}) for s in sizes[:3]]
            ask.append(_q("sizes", f"Which size is the {word} on offer?" if len(sizes) > 1
                          else f"The brochure shows {_fmt(lo)} sq ft. Is that the {word} size?",
                          pick + [("Not sure", None)] if len(sizes) > 1 else [("Yes", {"min": lo, "max": lo}), ("No / not sure", None)]))

    # the land of the whole project
    acres = seen.get("acres") or []
    if scope == "layout" and not listing.get("total_acres") and acres:
        if len(acres) > 1:
            ask.append(_q("total_acres", "The brochure gives different land areas: " + " and ".join(f"{_fmt(a)} acres" for a in acres[:3])
                          + ". Which is right?", [(f"{_fmt(a)} acres", a) for a in acres[:3]] + [("Not sure", None)]))
        else:
            ask.append(_q("total_acres", f"The brochure says the project is {_fmt(acres[0])} acres. Is that right?",
                          [("Yes", acres[0]), ("No / not sure", None)]))

    # MahaRERA: a number, or plainly not registered
    if not registered and not listing.get("rera_no") and not listing.get("rera_status"):
        other = seen.get("other_registration")
        note = f" The brochure shows \"{other}\", which is not a MahaRERA number." if other else ""
        if candidates:  # our register holds close names: one tap picks the project
            ask.append(_q("rera", "Is it one of these MahaRERA projects?",
                          [(f"{c['name']}, {c['regno']}" + (f" ({c['taluka']})" if c.get("taluka") else ""), c["regno"]) for c in candidates]
                          + [("None of these", None), ("Not registered", "not_registered")], free_text="Another MahaRERA number"))
        else:
            ask.append(_q("rera", f"Is this project registered on MahaRERA?{note}",
                          [("Not registered", "not_registered")], free_text="MahaRERA number, like PR1260002501386 or P52100012345"))

    # the brochure's selling points (price, booking, water, roads...): used in posts only once the agent says so
    if points:
        listed = "; ".join(str(p.get("text") or "") for p in points if p.get("text"))
        ask.append(_q("selling_points", f"Use these selling points from the brochure in your posts? {listed}.",
                      [("Use all", "all"), ("Choose in the listing", "later")]))
    return auto, ask[:MAX_QUESTIONS]


def answer_points(listing: dict, value: Any) -> Dict[str, Any]:
    """The listing's selling_points after the agent's answer: "all" confirms every pending point, "later" sets them aside
    (dismissed: not used, not asked again; the agent can confirm them in the listing)."""
    if value not in ("all", "later"):
        raise ValueError("Pick one of the choices.")
    out = []
    for p in listing.get("selling_points") or []:
        if isinstance(p, dict) and not p.get("confirmed") and not p.get("dismissed"):
            p = {**p, "confirmed": True} if value == "all" else {**p, "dismissed": True}
        out.append(p)
    return {"selling_points": out}


def apply_answer(key: str, value: Any) -> Dict[str, Any]:
    """The listing fields one answer sets ({} for "not sure"). Raises ValueError for an answer that does not fit."""
    if value is None or key == "files":
        return {}
    if key == "property_type":
        if value not in TYPES:
            raise ValueError("Pick one of the choices.")
        return {"property_type": value}
    if key == "listing_scope":
        if value not in SCOPES:
            raise ValueError("Pick one of the choices.")
        return {"listing_scope": value}
    if key == "sizes":
        lo, hi = _num((value or {}).get("min")), _num((value or {}).get("max"))
        if not (lo and hi and lo <= hi):
            raise ValueError("Pick one of the choices.")
        return {"size_min_sqft": round(lo), "size_max_sqft": round(hi)}
    if key == "total_acres":
        a = _num(value)
        if not a:
            raise ValueError("Pick one of the choices.")
        return {"total_acres": a}
    if key == "rera":
        v = str(value).strip().upper().replace(" ", "")
        if v == "NOT_REGISTERED":
            return {"rera_status": "not_registered"}
        if not RERA_NO.match(v):
            raise ValueError("A MahaRERA number is two letters and 13 digits, like PR1260002501386, or P and 11 digits, like P52100012345.")
        return {"rera_no": v}
    raise ValueError("Unknown question.")


def fill_size(listing: dict, fields: Dict[str, Any]) -> Dict[str, Any]:
    """A confirmed size also gives the listing its area when it has none (the price card and rate per sq ft read it)."""
    if fields.get("size_min_sqft") and not listing.get("carpet_sqft"):
        return {**fields, "carpet_sqft": fields["size_min_sqft"]}
    return fields
