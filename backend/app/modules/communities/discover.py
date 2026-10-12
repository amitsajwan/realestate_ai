"""Find: the named neighbourhoods around each area we cover, from OpenStreetMap, ranked by evidence.

Once a week, for every area in app/core/areas.py: where the area is (Nominatim, the same lookup as property facts), then every
OSM place node named within RADIUS_M of it that is a suburb, neighbourhood, quarter, village or hamlet. A place that is one of
our areas, or nearer to another of our areas, is left to that area. Each is kept in `communities` ({_id: "<area>/<slug>",
area, name, slug, lat, lon, osm_url, km_from_area, projects_named, found_at}). `projects_named` counts register projects in the
same area whose name says the neighbourhood (whole words): the evidence that buyers know the name. Records are never deleted;
one OSM drops is simply not refreshed, and keeps its page.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.areas import AREAS, Area
from app.modules.newsroom.store import Store
from app.modules.propertyfacts.place import GetJson, locate
from app.modules.propertyfacts.surroundings import OVERPASS, km

COLLECTION = "communities"
RADIUS_M = 4000
KINDS = ("suburb", "neighbourhood", "quarter", "village", "hamlet")
MIN_NAME = 4


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


def query(lat: float, lon: float, radius_m: int = RADIUS_M) -> str:
    return (f'[out:json][timeout:25];node(around:{radius_m},{lat},{lon})["place"~"^({"|".join(KINDS)})$"]["name"];'
            "out tags;")


def _ours(name: str) -> bool:
    low = name.lower()
    return any(low == a.name.lower() or low in a.aliases for a in AREAS)


def places(data: Any, area: Area, lat: float, lon: float, centres: Dict[str, tuple]) -> List[dict]:
    """The neighbourhoods in an Overpass answer that belong to `area`: named in English letters, not one of our areas, and
    nearer to this area's centre than to any other area's."""
    out: Dict[str, dict] = {}
    for e in (data or {}).get("elements") or []:
        tags = e.get("tags") or {}
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        if len(name) < MIN_NAME or not re.fullmatch(r"[A-Za-z0-9 .'()-]+", name) or _ours(name):
            continue
        try:
            plat, plon = float(e["lat"]), float(e["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        d = km(lat, lon, plat, plon)
        if any(km(c[0], c[1], plat, plon) < d for k, c in centres.items() if k != area.key):
            continue
        slug = slugify(name)
        if slug and (slug not in out or d < out[slug]["km_from_area"]):
            out[slug] = {"name": name, "slug": slug, "lat": plat, "lon": plon, "km_from_area": round(d, 1),
                         "osm_url": f"https://www.openstreetmap.org/node/{e.get('id')}"}
    return sorted(out.values(), key=lambda p: p["km_from_area"])


def projects_named(name: str, docs: List[dict]) -> List[dict]:
    pat = re.compile(r"\b" + r"\s+".join(map(re.escape, name.lower().split())) + r"\b")
    return [d for d in docs if pat.search((d.get("name") or "").lower())]


async def run(store: Store, get_json: GetJson, now: datetime) -> dict:
    """Refresh every area's neighbourhoods. {"areas": located, "found": neighbourhoods kept}."""
    centres: Dict[str, tuple] = {}
    for a in AREAS:
        p = await locate(get_json, a.name)
        if p is not None:
            centres[a.key] = (p.lat, p.lon)
    projects = await store.all_projects()
    coll = store.db.get_collection(COLLECTION)
    found = 0
    for a in AREAS:
        if a.key not in centres:
            continue
        lat, lon = centres[a.key]
        data = await get_json(OVERPASS, {"data": query(lat, lon)})
        mine = [d for d in projects if d.get("locality") == a.key]
        for p in places(data, a, lat, lon, centres):
            _id = f"{a.slug}/{p['slug']}"
            fields = {**p, "area": a.key, "projects_named": len(projects_named(p["name"], mine)), "found_at": now}
            if await coll.find_one({"_id": _id}):
                await coll.update_one({"_id": _id}, {"$set": fields})
            else:
                await coll.insert_one({"_id": _id, **fields})
            found += 1
    return {"areas": len(centres), "found": found}


def rank(doc: dict) -> tuple:
    """Write order: most projects named after it, then nearest to its area's centre."""
    return (-int(doc.get("projects_named") or 0), float(doc.get("km_from_area") or 99))


def area_of(doc: dict) -> Optional[Area]:
    return next((a for a in AREAS if a.key == doc.get("area")), None)
