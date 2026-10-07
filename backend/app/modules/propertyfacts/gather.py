"""Gather a listing's facts from every automatic source into one sheet (docs/CONTENT_PLATFORM.md PF track).

Today: the listing itself, its place (Nominatim) and its MahaRERA registration. Surroundings (PF-4), the builder record (PF-3),
portals (PF-5) and calculators (PF-7) add readings here as they land."""
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.modules.agentprojects.maharera import make_fetch

from . import calc, registration, surroundings
from . import place as place_mod
from .facts import Fact, Reading, sheet

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"
LISTING_KEYS = ("transaction", "property_type", "price_inr", "bhk", "carpet_sqft", "locality", "city", "project_name",
                "rera_no", "amenities")


@dataclass
class Sheet:
    facts: Dict[str, Fact]
    place: Optional[place_mod.Place]
    match: Optional[registration.Match]
    notes: List[str] = field(default_factory=list)  # what could not be found, in plain words


def listing_readings(doc: Dict[str, Any], now: datetime) -> List[Reading]:
    out = [Reading(k, doc.get(k), "listing", "", now) for k in LISTING_KEYS if doc.get(k) not in (None, "", [])]
    if doc.get("property_type") == "plot" and doc.get("carpet_sqft"):  # a plot listing's area is the plot's area
        out.append(Reading("plot_sqft", doc["carpet_sqft"], "listing", "", now))
    return out


def place_readings(p: place_mod.Place, now: datetime) -> List[Reading]:
    return [Reading(k, v, "osm", p.url, now) for k, v in
            (("lat", p.lat), ("lon", p.lon), ("taluka", p.taluka), ("district", p.district)) if v not in (None, "")]


class Clients:
    """Real network access, polite by default: Nominatim at most 1 request a second, answers cached for the process."""

    def __init__(self, timeout: float = 60.0, register: Any = None, facts_store: Any = None):
        """`register`: the newsroom Store, read before MahaRERA; `facts_store`: where gathered sheets are kept. Both optional."""
        self.timeout = timeout
        self.register, self.facts_store = register, facts_store
        self._cache: Dict[str, Any] = {}
        self._last_osm = 0.0
        self._osm_lock = asyncio.Lock()
        self.fetch_general = make_fetch()

    async def get_text(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout, headers={"User-Agent": BROWSER_UA}, follow_redirects=True) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.text

    async def get_json(self, url: str, params: dict) -> Any:
        key = url + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        if key in self._cache:
            return self._cache[key]
        async with self._osm_lock:
            wait = 1.0 - (time.monotonic() - self._last_osm)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers={"User-Agent": place_mod.USER_AGENT}) as c:
                    # Overpass queries are long: send them as a form POST, as Overpass expects
                    r = await (c.post(url, data=params) if url == surroundings.OVERPASS else c.get(url, params=params))
                data = r.json() if r.status_code == 200 else None
            except (httpx.HTTPError, ValueError):
                data = None
            finally:
                self._last_osm = time.monotonic()
        if data is not None:
            self._cache[key] = data
        return data


async def gather(doc: Dict[str, Any], clients: Any, now: Optional[datetime] = None) -> Sheet:
    """`clients` needs get_text(url), get_json(url, params) and fetch_general(maharera_id); tests pass fakes."""
    now = now or datetime.utcnow()
    rs = listing_readings(doc, now)
    notes: List[str] = []

    where = await place_mod.locate(clients.get_json, doc.get("locality") or "", doc.get("city") or "Pune")
    if where:
        rs += place_readings(where, now)
        near, missing = await surroundings.around(clients.get_json, where.lat, where.lon, now)
        rs += near
        notes += missing
    else:
        notes.append(f"could not place locality {doc.get('locality')!r} on the map")

    match, official = await registration.lookup(clients.get_text, clients.fetch_general, doc.get("project_name") or "",
                                                doc.get("rera_no") or "", where, now, getattr(clients, "register", None))
    rs += official
    if match.project is None:
        notes.append("MahaRERA: " + match.how)
    elif not any(r.key == "possession_now" for r in official):
        notes.append("MahaRERA: matched the registration but could not read its details")
    first = sheet(rs)
    rs += calc.readings({k: f.value for k, f in first.items() if f.usable}, now)
    out = Sheet(sheet(rs), where, match, notes)
    facts_store = getattr(clients, "facts_store", None)
    if facts_store is not None:  # keep every gathered sheet: the next campaign, and the sources behind each post
        await facts_store.save(out, doc, now)
    return out
