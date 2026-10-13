"""PF-4: what is near a place, from OpenStreetMap. Up to 3 nearest named places per category.

Overpass answers everything in one query but the public server is often busy (504) or refuses us (406; verified 2026-10-06), so
when it fails each category is asked of Nominatim instead (one request a second, bounded to the area). Distances are
straight-line ("about 2.3 km away") for now; road distance (OSRM) can replace `km` later without changing callers. OSM is sparse
outside the city, so a category with nothing found is noted rather than implied absent. To add a category, add one line to
CATEGORIES.

Our own copy comes first: data/pune_places.json.gz, the named places of these categories around Pune from a Geofabrik
OpenStreetMap extract (scripts/build_osm_places.py, made once). A place inside its box is answered from it with no network;
Overpass and Nominatim are only asked for places outside it. When no source could be read, the note says so instead of
claiming there is nothing nearby."""
import gzip
import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .facts import Reading
from .place import NOMINATIM, GetJson

OVERPASS = "https://overpass-api.de/api/interpreter"
# tried in order when OVERPASS refuses or times out (2026-10-13: overpass-api.de answers our server 406 whatever the agent)
OVERPASS_MIRRORS = ("https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.private.coffee/api/interpreter")
LOCAL_PLACES = Path(__file__).resolve().parent / "data" / "pune_places.json.gz"
LOCAL_BOX = (17.85, 19.40, 73.30, 75.20)   # south, north, west, east: where the copy covers a full 10 km radius
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


@lru_cache(maxsize=1)
def _local_rows() -> Tuple[Tuple[Any, ...], ...]:
    try:
        with gzip.open(LOCAL_PLACES, "rt", encoding="utf-8") as f:
            return tuple(tuple(r) for r in json.load(f))
    except (OSError, ValueError):
        return ()


def from_local(lat: float, lon: float) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """The nearest named places from our copy; None when the copy is missing or does not cover this place."""
    s, n, w, e = LOCAL_BOX
    rows = _local_rows()
    if not rows or not (s <= lat <= n and w <= lon <= e):
        return None
    best: Dict[str, List[Dict[str, Any]]] = {}
    dlat = RADIUS_M / 111000
    for cat, name, plat, plon, kind, oid in rows:
        if abs(plat - lat) > dlat or abs(plon - lon) > dlat * 1.1:
            continue
        d = km(lat, lon, plat, plon)
        if d <= RADIUS_M / 1000:
            _add(best, cat, name, d, f"https://www.openstreetmap.org/{kind}/{oid}")
    return best


async def around(get_json: GetJson, lat: float, lon: float, now=None) -> Tuple[List[Reading], List[str]]:
    """(readings "nearby.<category>" = [{name, km}], notes about categories with nothing found)."""
    best = from_local(lat, lon)
    checked = best is not None
    if best is None:
        data = await get_json(OVERPASS, {"data": query(lat, lon)})
        if isinstance(data, dict) and isinstance(data.get("elements"), list):
            best, checked = from_overpass(data["elements"], lat, lon), True
        else:
            best = {}
            d = RADIUS_M / 111000  # degrees of latitude in the radius; good enough for a search box
            for cat, (_, _, phrase) in CATEGORIES.items():
                rows = await get_json(NOMINATIM, {"q": phrase, "format": "jsonv2", "limit": 10, "bounded": 1,
                                                  "viewbox": f"{lon - d},{lat + d},{lon + d},{lat - d}"})
                checked = checked or isinstance(rows, list)
                from_nominatim(cat, rows, lat, lon, best)
    rs = [Reading(f"nearby.{k}", [{"name": i["name"], "km": i["km"]} for i in v], "osm", v[0]["url"], now)
          for k, v in best.items()]
    missing = [CATEGORIES[k][0].lower() for k in CATEGORIES if k not in best]
    if not checked:
        return rs, ["nearby places could not be checked right now (the map service did not answer)"]
    notes = [f"no named {', '.join(missing)} mapped within {RADIUS_M // 1000} km"] if missing else []
    return rs, notes


def label(key: str) -> str:
    return CATEGORIES.get(key.split(".", 1)[-1], (key, (), ""))[0]


# A map's name is not a card's name: "Maharashtra Industrial Development Corporation" is what buyers call "Ranjangaon MIDC".
_GENERIC_INDUSTRY = re.compile(r"(?i)^(maharashtra industrial development corporation|m\.?i\.?d\.?c\.?|(additional |new )?"
                               r"industrial (area|estate|zone|shade|shed)s?)$")
_BUS_NOISE = re.compile(r"(?i)\b(pmpml|pmpl|pampml|msrtc|kmt|private)\b")


def short_name(cat: str, name: str, town: str = "") -> str:
    """The name a buyer uses for a mapped place: an industrial estate is "<town> MIDC", a railway station "<name> station",
    a bus stand "<name> bus stand" / "<name> ST stand"; odd characters, alternative names (";") and brackets dropped.
    `town`: where the place is (the listing's locality: every place is within RADIUS_M of it), used when the map's name says
    nothing about where it is."""
    cat = cat.split(".", 1)[-1]
    n = (name or "").split(";")[0]
    n = re.sub(r"\([^)]*\)", " ", n)
    n = re.sub(r"[^\w .,&'/-]", " ", n)          # the replacement character, emoji, stray symbols
    n = re.sub(r"\s+", " ", n).strip(" ,-")
    if not n:
        return (name or "").strip()
    if cat == "industry":
        if _GENERIC_INDUSTRY.match(n):
            return f"{town} MIDC" if town else "MIDC"
        m = re.match(r"(?i)^m\.?i\.?d\.?c\.?\s+(.+)$", n)          # "MIDC Bhosari" -> "Bhosari MIDC"
        if m:
            return f"{m.group(1)} MIDC"
        m = re.match(r"(?i)^(.+?)\s+industrial area$", n)  # "Shikrapur-Sanaswadi Industrial Area" -> "... MIDC"
        if m and m.group(1).lower() not in ("additional", "new"):
            return f"{m.group(1)} MIDC"
        return n
    if cat == "railway":
        n = re.sub(r"(?i)\s*(railway station|railway stn|rly station|station)$", "", n).strip()
        return n if re.search(r"(?i)junction$", n) else f"{n} station"
    if cat == "bus":
        st = re.search(r"(?i)\bs\.?\s?t\.?\b", n)
        n = _BUS_NOISE.sub(" ", n)
        n = re.sub(r"(?i)\b(s\.?\s?t\.?|bus|stand|station|terminus|terminal|depot|stop|parking)\b", " ", n)
        n = re.sub(r"\s+", " ", n).strip(" ,-")
        if not n:
            return f"{town} bus stand" if town else (name or "").strip()
        return f"{n} ST stand" if st else f"{n} bus stand"
    return n
