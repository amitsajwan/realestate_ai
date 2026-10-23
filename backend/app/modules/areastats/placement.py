"""Areas by place (docs/plan/area-maps.md): a project whose position was checked belongs to the area it is IN (app.core.area_bounds),
not the one its MahaRERA pincode suggests. Ekaanta (411014, so "Kharadi") is in Viman Nagar (owner, 2026-10-23).

Once a day (inside the enrichment loop, through wiring.py) every register record with a checked position (a pin checked by hand,
an `auto`/`approved` map pin, or the project's own Google place) in or around an area with a boundary is looked at:
- it keeps its area when the position is inside that area's boundary or within EDGE_KM of it (an edge is not a wall);
- else it moves to the first boundary that holds it, or, in none of ours, out of our areas: `locality` None and its Pune place
  from the neighbourhood in Google's address (Wadgaon Sheri, Viman Nagar ...), so its page stays and the area lists drop it;
- a project placed by hand (pune_places.VERIFIED) is never moved;
- `also_areas`: every other area whose boundary holds it, so it shows on those maps too, after their own projects (Godrej Ivara
  is on the Kharadi and the Upper Kharadi map).
A moved record says so (`locality_from` "position", `position` {lat, lon, was, at}); the register sweep keeps it (newsroom.store).
Writes only `locality`, `locality_from`, `pune_place`, `pune_place_name`, `position` and `also_areas` on register records.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from app.core import area_bounds, pune_places
from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from .areamap import MAPS, _google, hand_pinned

log = logging.getLogger(__name__)

# pin_address(db, regno) -> the address Google gave for the project's own pin, or None (propertyfacts keeps the pins)
PinAddress = Callable[[Any, str], Awaitable[Optional[str]]]
_deps: Dict[str, Any] = {}

MARK = "area_placement"
EVERY = timedelta(hours=24)
EAST_PINCODES = ("411014", "412207", "411047", "412307", "411036", "411015", "411032", "411006")


def configure(pin_address: Optional[PinAddress] = None) -> None:
    if pin_address is not None:
        _deps["pin_address"] = pin_address


def position(d: dict) -> Optional[Tuple[float, float, str]]:
    """(lat, lon, address) of a checked position, else None (never a locality's centre or a listing's guess)."""
    for m in MAPS.values():
        p = hand_pinned(m, d)
        if p is not None:
            return p.lat, p.lon, p.how
    mp = d.get("map_pin") or {}
    if mp.get("status") in ("auto", "approved") and mp.get("lat") is not None and mp.get("lon") is not None:
        return float(mp["lat"]), float(mp["lon"]), mp.get("address") or ""
    g = _google(d)
    return (g[0], g[1], "") if g else None


def decide(label: Optional[str], lat: float, lon: float, by_hand: bool = False) -> Tuple[Optional[str], List[str]]:
    """(the area it belongs to, the other areas whose maps also show it)."""
    near = area_bounds.near(lat, lon)
    if by_hand or label in near or label not in area_bounds.BOUNDS and not area_bounds.containing(lat, lon):
        area = label
    else:
        holds = area_bounds.containing(lat, lon)
        area = holds[0] if holds else None
    # other maps only where the pin is INSIDE their boundary: the 500 m edge put Kharadi's busiest projects at the top of Upper
    # Kharadi's map, above its own (2026-10-23)
    return area, [k for k in area_bounds.containing(lat, lon) if k != area]


def place_from_address(address: str) -> Optional[pune_places.Place]:
    """The Pune place Google's address names (the most specific one: the longest name found)."""
    text = (address or "").lower()
    hits = [p for p in pune_places.PLACES for al in (p.name.lower(), *p.aliases) if al and al in text]
    return max(hits, key=lambda p: len(p.name)) if hits else None


async def refresh(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """Place every pinned record in or around our bounded areas. {"moved": [...], "also": n} or None when not due."""
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = mark.get("at")
    if not force and isinstance(last, datetime) and now - (last if last.tzinfo else last.replace(tzinfo=timezone.utc)) < EVERY:
        return None
    moved, also_n = [], 0
    for d in await store.all_projects():
        label = d.get("locality")
        if not (label in area_bounds.BOUNDS or d.get("locality_from") == "position" or d.get("pincode") in EAST_PINCODES):
            continue
        pos = position(d)
        if pos is None:
            continue
        lat, lon, address = pos
        regno = d["_id"]
        area, also = decide(label, lat, lon, by_hand=regno in pune_places.VERIFIED)
        fields: Dict[str, Any] = {}
        if sorted(also) != sorted(d.get("also_areas") or []):
            fields["also_areas"] = also
            also_n += 1
        if area != label:
            if area:
                place_key, place_name = area, BY_KEY[area].name
            else:
                if not address and _deps.get("pin_address"):
                    address = await _deps["pin_address"](store.db, regno) or ""
                p = place_from_address(address)
                place_key, place_name = (p.key, p.name) if p else (d.get("pune_place"), d.get("pune_place_name"))
            fields.update({"locality": area, "locality_from": "position", "pune_place": place_key, "pune_place_name": place_name,
                           "position": {"lat": lat, "lon": lon, "was": label, "at": now}})
            moved.append({"regno": regno, "name": d.get("name"), "from": label, "to": area or place_name})
        if fields:
            await store.set_project(regno, **fields)
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "moved": moved}}, upsert=True)
    if moved:
        log.info("area placement: %d moved by position: %s", len(moved), "; ".join(f"{m['name']} {m['from']} -> {m['to']}" for m in moved))
    return {"moved": moved, "also": also_n}
