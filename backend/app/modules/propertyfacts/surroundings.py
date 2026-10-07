"""PF-4: what is near a place, from OpenStreetMap. Up to 3 nearest named places per category.

Overpass answers everything in one query but the public server is often busy (504) or refuses us (406; verified 2026-10-06), so
when it fails each category is asked of Nominatim instead (one request a second, bounded to the area). Distances are
straight-line ("about 2.3 km away") for now; road distance (OSRM) can replace `km` later without changing callers. OSM is sparse
outside the city, so a category with nothing found is noted rather than implied absent. To add a category, add one line to
CATEGORIES."""
import math
from typing import Any, Dict, List, Optional, Tuple

from .facts import Reading
from .place import NOMINATIM, GetJson

OVERPASS = "https://overpass-api.de/api/interpreter"
RADIUS_M = 10000
PER_CATEGORY = 3

# key -> (label for posts, Overpass filters, Nominatim search phrase). Every place needs a name: an unnamed school cannot go on a card.
CATEGORIES: Dict[str, Tuple[str, Tuple[str, ...], str]] = {
    "hospital": ("Hospital", ('["amenity"~"^(hospital|clinic)$"]',), "hospital"),
    "school": ("School", ('["amenity"="school"]',), "school"),
    "college": ("College", ('["amenity"~"^(college|university)$"]',), "college"),
    "railway": ("Railway station", ('["railway"="station"]',), "railway station"),
    "bus": ("Bus stand", ('["amenity"="bus_station"]',), "bus station"),
    "industry": ("Industrial area", ('["landuse"="industrial"]',), "industrial"),
    "temple": ("Temple", ('["amenity"="place_of_worship"]["religion"="hindu"]',), "temple"),
    "market": ("Shopping", ('["shop"~"^(mall|supermarket)$"]', '["amenity"="marketplace"]'), "supermarket"),
    "bank": ("Bank", ('["amenity"="bank"]',), "bank"),
}


def query(lat: float, lon: float, radius_m: int = RADIUS_M) -> str:
    parts = [f'nwr(around:{radius_m},{lat},{lon}){f}["name"];' for _, fs, _ in CATEGORIES.values() for f in fs]
    return "[out:json][timeout:25];(" + "".join(parts) + ");out center tags;"


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def category(tags: Dict[str, str]) -> Optional[str]:
    a, shop = tags.get("amenity", ""), tags.get("shop", "")
    if a in ("hospital", "clinic"):
        return "hospital"
    if a == "school":
        return "school"
    if a in ("college", "university"):
        return "college"
    if tags.get("railway") == "station":
        return "railway"
    if a == "bus_station":
        return "bus"
    if tags.get("landuse") == "industrial":
        return "industry"
    if a == "place_of_worship" and tags.get("religion") == "hindu":
        return "temple"
    if shop in ("mall", "supermarket") or a == "marketplace":
        return "market"
    if a == "bank":
        return "bank"
    return None


def _add(best: Dict[str, List[Dict[str, Any]]], cat: str, name: str, d: float, url: str) -> None:
    items = best.setdefault(cat, [])
    if any(i["name"] == name for i in items):
        return
    items.append({"name": name, "km": round(d, 1), "url": url})
    items.sort(key=lambda i: i["km"])
    del items[PER_CATEGORY:]


def from_overpass(elements: List[Dict[str, Any]], lat: float, lon: float) -> Dict[str, List[Dict[str, Any]]]:
    best: Dict[str, List[Dict[str, Any]]] = {}
    for e in elements or []:
        tags = e.get("tags") or {}
        cat, name = category(tags), (tags.get("name:en") or tags.get("name") or "").strip()
        c = e.get("center") or e
        if cat and name and "lat" in c and "lon" in c:
            _add(best, cat, name, km(lat, lon, float(c["lat"]), float(c["lon"])),
                 f"https://www.openstreetmap.org/{e.get('type')}/{e.get('id')}")
    return best


def from_nominatim(cat: str, rows: Any, lat: float, lon: float, best: Dict[str, List[Dict[str, Any]]]) -> None:
    for r in rows if isinstance(rows, list) else []:
        name = (r.get("name") or "").strip()
        tags = {r.get("category", ""): r.get("type", "")}
        if tags.get("amenity") == "place_of_worship":
            tags["religion"] = "hindu"  # Nominatim gives no religion; the search phrase was "temple"
        if not name or category(tags) != cat:
            continue
        try:
            d = km(lat, lon, float(r["lat"]), float(r["lon"]))
        except (KeyError, TypeError, ValueError):
            continue
        if d <= RADIUS_M / 1000:
            _add(best, cat, name, d, f"https://www.openstreetmap.org/{r.get('osm_type')}/{r.get('osm_id')}")


async def around(get_json: GetJson, lat: float, lon: float, now=None) -> Tuple[List[Reading], List[str]]:
    """(readings "nearby.<category>" = [{name, km}], notes about categories with nothing found)."""
    data = await get_json(OVERPASS, {"data": query(lat, lon)})
    if isinstance(data, dict) and isinstance(data.get("elements"), list):
        best = from_overpass(data["elements"], lat, lon)
    else:
        best = {}
        d = RADIUS_M / 111000  # degrees of latitude in the radius; good enough for a search box
        for cat, (_, _, phrase) in CATEGORIES.items():
            rows = await get_json(NOMINATIM, {"q": phrase, "format": "jsonv2", "limit": 10, "bounded": 1,
                                              "viewbox": f"{lon - d},{lat + d},{lon + d},{lat - d}"})
            from_nominatim(cat, rows, lat, lon, best)
    rs = [Reading(f"nearby.{k}", [{"name": i["name"], "km": i["km"]} for i in v], "osm", v[0]["url"], now)
          for k, v in best.items()]
    missing = [CATEGORIES[k][0].lower() for k in CATEGORIES if k not in best]
    notes = [f"no named {', '.join(missing)} mapped within {RADIUS_M // 1000} km"] if missing else []
    return rs, notes


def label(key: str) -> str:
    return CATEGORIES.get(key.split(".", 1)[-1], (key, (), ""))[0]
