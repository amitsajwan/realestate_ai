"""The public view of a kept fact sheet, for a listing's page. Usable facts only (official, measured, corroborated), shaped for
display, each block with its source. Pure: takes the stored `property_facts` document."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from .surroundings import label

NEARBY_MAX = 5
OSM_COPYRIGHT = "https://www.openstreetmap.org/copyright"


def _usable(doc: dict) -> Dict[str, dict]:
    return {f["key"]: f for f in doc.get("facts") or [] if f.get("usable")}


def _val(facts: Dict[str, dict], key: str) -> Any:
    f = facts.get(key)
    return f["value"] if f else None


def _iso(v: Any) -> Optional[str]:
    return v.isoformat() if isinstance(v, datetime) else (v or None)


def _read_at(facts: Dict[str, dict], key: str) -> Optional[str]:
    f = facts.get(key)
    rs = (f or {}).get("readings") or []
    return _iso(rs[0].get("fetched_at")) if rs else None


def view(doc: Optional[dict]) -> Optional[dict]:
    """None when there is nothing worth showing."""
    if not doc:
        return None
    f = _usable(doc)
    out: Dict[str, Any] = {"project": doc.get("project_name"), "locality": doc.get("locality"),
                           "gathered_at": _iso(doc.get("gathered_at"))}

    if _val(f, "rera_no") and _val(f, "maharera_url"):
        out["maharera"] = {
            "rera_no": _val(f, "rera_no"), "url": _val(f, "maharera_url"), "name": _val(f, "project_name"),
            "project_type": _val(f, "project_type"), "registered_on": _val(f, "registered_on"),
            "completion_at_registration": _val(f, "possession_at_registration"), "completion_now": _val(f, "possession_now"),
            "moved_months": _val(f, "possession_moved_months"), "units_total": _val(f, "units_total"),
            "promoter": _val(f, "promoter"), "read_at": _read_at(f, "possession_now") or _read_at(f, "rera_no"),
        }

    near: List[dict] = []
    for k, fact in f.items():
        if k.startswith("nearby.") and isinstance(fact.get("value"), list):
            near += [{"label": label(k), "name": p.get("name"), "km": p.get("km")} for p in fact["value"] if p.get("name")]
    if near:
        out["nearby"] = sorted(near, key=lambda p: p["km"])[:NEARBY_MAX]
        out["nearby_source"] = {"name": "OpenStreetMap contributors", "url": OSM_COPYRIGHT}

    # the agent's own offer, which posts quote ("₹32.3 lakh for a plot"): shown with its source, never as a project price
    offer = {k: _val(f, k) for k in ("transaction", "property_type", "price_inr", "plot_sqft", "carpet_sqft", "bhk")
             if _val(f, k) is not None}
    if offer.get("price_inr") or offer.get("plot_sqft") or offer.get("carpet_sqft"):
        out["offer"] = {**offer, "source": "the agent's listing", "read_at": _read_at(f, "price_inr")}

    numbers: Dict[str, Any] = {}
    for k in ("price_per_sqft", "plot_guntha", "plot_sqm", "emi"):
        if _val(f, k) is not None:
            numbers[k] = _val(f, k)
    if numbers:
        out["numbers"] = numbers

    return out if any(k in out for k in ("maharera", "nearby", "numbers", "offer")) else None
