"""The AI draft's project match in OUR MahaRERA register (never live MahaRERA: too slow for a form), from the registration
number or project name the agent gave. A registration number only in MahaRERA's form (P + 11 digits or PR/PP/PM + 13
digits, core/rera.py; "Gat No." is land). It fills a DRAFT the agent confirms."""
import logging
from typing import Any, Dict, Optional

from app.core import pune_places, rera
from app.core.rera import CANDIDATES, _words, core

log = logging.getLogger(__name__)

RERA = rera.SEARCH         # service.py fullmatches a typed number against it


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
