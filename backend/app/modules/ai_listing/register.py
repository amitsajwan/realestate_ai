"""The AI draft's project match in OUR MahaRERA register (never live MahaRERA: too slow for a form), from the registration
number or project name the agent gave. A registration number only in MahaRERA's form (P + 11 digits or PR/PP/PM + 13
digits, core/rera.py; "Gat No." is land). It fills a DRAFT the agent confirms."""
import logging
import re
from typing import Any, Dict, List, Optional

from app.core import pune_places, rera
from app.core.rera import CANDIDATES, _words, core

log = logging.getLogger(__name__)

RERA = rera.SEARCH         # service.py fullmatches a typed number against it
# words that describe a building and name none: "Commercial Complex" went live as a project's name when the number on the same
# listing says UBC (2026-11-07). A real marketed name has at least one word outside this list and keeps priority over MahaRERA's.
DESCRIBES = {"the", "a", "new", "commercial", "residential", "complex", "project", "projects", "building", "buildings", "tower",
             "towers", "shop", "shops", "office", "offices", "flat", "flats", "apartment", "apartments", "and", "for", "sale"}
EARLY_MONTHS = 6           # a possession this far ahead of the builder's filed date is worth a second look


def _rec(d: dict) -> Dict[str, Any]:
    return {"regno": d.get("regno") or d.get("_id"), "name": d.get("name", ""), "taluka": d.get("taluka") or ""}


async def match_register(register: Any, rera_no: Optional[str], project_name: Optional[str]) -> Dict[str, Any]:
    """{"record": register doc | None, "candidates": [{regno, name, taluka}]}. Only a registration number is a confident
    match; a name (exact or close) is offered for a one-tap pick. Never raises."""
    out: Dict[str, Any] = {"record": None, "candidates": []}
    if register is None:
        return out
    try:
        if rera_no:
            d = await register.project(rera_no.strip().upper())
            if d:
                out["record"] = d
                return out
        name = (project_name or "").strip()
        if not name:
            return out
        everything = await register.all_projects()
        exact = [d for d in everything if _words(d.get("name", "")) == _words(name)]
        close = [d for d in everything if d not in exact and core(name) and core(d.get("name", "")) == core(name)]
        out["candidates"] = [_rec(d) for d in (exact + close)[:CANDIDATES]]
    except Exception as e:
        log.info("ai_listing register match failed: %s", type(e).__name__)
    return out


def register_fields(d: dict) -> Dict[str, Any]:
    """What the draft takes from a register record: the facts the agent never has to type or check again (the new-listing
    screen shows them as one "From MahaRERA" card). `locality_verified` is False when the place is our guess from the PIN."""
    regno = d.get("regno") or d.get("_id") or ""
    verified = regno.strip().upper() in pune_places.VERIFIED
    loc = (pune_places.BY_KEY[pune_places.VERIFIED[regno.strip().upper()]].name if verified else None)         or d.get("pune_place_name") or d.get("locality")
    if not loc and d.get("pincode"):
        loc = pune_places.place_name(d.get("name", ""), d.get("pincode", ""), d.get("taluka", ""), regno)
    totals = d.get("building_totals") or {}
    read = d.get("details_checked_at")
    return {k: v for k, v in {
        "regno": regno, "name": d.get("name"), "locality": loc, "locality_verified": verified, "taluka": d.get("taluka"),
        "pincode": d.get("pincode"), "promoter": d.get("promoter"),
        "completion_at_registration": d.get("completion_at_registration"), "completion_now": d.get("completion_now"),
        "towers": totals.get("towers"), "max_floors": totals.get("max_floors"),
        "units_total": d.get("units_total"), "units_booked": d.get("units_booked"),
        "read_at": read.date().isoformat() if hasattr(read, "date") else None,
    }.items() if v not in (None, "")}


def same_place(locality: Optional[str], project: Optional[str]) -> bool:
    """True when the 'locality' is really the project's name ("Gulmohar City" / "Gulmohar City Plots")."""
    if not locality or not project:
        return False
    a, b = _words(locality), _words(project)
    return bool(a) and (a == b or bool(core(locality)) and core(locality) == core(project))


def generic_name(name: Optional[str]) -> bool:
    """True when the 'project name' only says what kind of building it is."""
    words = _words(name or "").split()
    return bool(words) and all(w in DESCRIBES for w in words)


def _same_area(a: str, b: str) -> bool:
    """One place inside the other's name ("Upper Kharadi" / "Kharadi") is a detail, not a disagreement."""
    x, y = _words(a).replace(" ", ""), _words(b).replace(" ", "")
    return x in y or y in x


def _months(ym: Optional[str]) -> Optional[int]:
    m = re.match(r"(\d{4})-(\d{2})", str(ym or ""))
    return int(m.group(1)) * 12 + int(m.group(2)) if m else None


def listing_mismatches(listing: dict, record: dict) -> List[Dict[str, str]]:
    """Where a saved listing disagrees with the MahaRERA record of its own number, for the agent to settle: [{field, yours,
    maharera}]. The listing is never changed here: the agent may know better. Only a generic name counts, since marketed names
    differ from MahaRERA's working ones on purpose, and only a possession well before the filed date, since a later one is
    cautious."""
    fields = register_fields(record)
    out: List[Dict[str, str]] = []
    name, area = listing.get("project_name") or "", listing.get("locality") or ""
    if generic_name(name) and fields.get("name"):
        out.append({"field": "project_name", "yours": name, "maharera": fields["name"]})
    if area and fields.get("locality") and not _same_area(area, fields["locality"]):
        out.append({"field": "locality", "yours": area, "maharera": fields["locality"]})
    yours, filed = _months(listing.get("possession")), _months(fields.get("completion_at_registration"))
    if yours and filed and filed - yours > EARLY_MONTHS:
        out.append({"field": "possession", "yours": listing["possession"], "maharera": fields["completion_at_registration"][:7]})
    return out
