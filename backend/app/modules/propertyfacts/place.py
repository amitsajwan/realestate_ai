"""Where a locality is: coordinates and taluka from OpenStreetMap's Nominatim. The taluka is what tells two same-named
MahaRERA projects apart (Gulmohar City in Shirur vs in Khed). Nominatim's postcodes are unreliable (it gives Kharadi 411001),
so they are not used.

Usage policy (https://operations.osmfoundation.org/policies/nominatim/): at most 1 request a second, an identifying
User-Agent, and cache the answers. Callers inject `get_json`, so tests never touch the network."""
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "avasetu-propertyfacts/0.1 (https://avasetu.in)"

GetJson = Callable[[str, dict], Awaitable[Any]]  # (url, query params) -> parsed JSON, or None on failure


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lon: float
    taluka: str      # "Shirur"; "Pune City" for the city's own subdistrict
    district: str    # "Pune"
    kind: str        # "village", "suburb", "town"
    url: str         # the OSM object, for the source line


def _taluka(county: str) -> str:
    c = (county or "").strip()
    return c[: -len(" Subdistrict")] if c.endswith(" Subdistrict") else c


def parse(rows: Any) -> Optional[Place]:
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return None
    r = rows[0]
    a = r.get("address") or {}
    try:
        lat, lon = float(r["lat"]), float(r["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    name = a.get("village") or a.get("suburb") or a.get("town") or a.get("city") or r.get("name") or ""
    osm = f"https://www.openstreetmap.org/{r.get('osm_type')}/{r.get('osm_id')}" if r.get("osm_type") and r.get("osm_id") else ""
    return Place(name=name, lat=lat, lon=lon, taluka=_taluka(a.get("county", "")), district=a.get("state_district", ""),
                 kind=r.get("type") or r.get("addresstype") or "", url=osm)


async def locate(get_json: GetJson, locality: str, city: str = "Pune", state: str = "Maharashtra") -> Optional[Place]:
    locality = (locality or "").strip()
    if not locality:
        return None
    q = ", ".join(p for p in (locality, city, state) if p)
    rows = await get_json(NOMINATIM, {"q": q, "format": "jsonv2", "limit": 1, "addressdetails": 1, "countrycodes": "in"})
    return parse(rows)
