"""Gather a listing's facts from every automatic source into one sheet (docs/CONTENT_PLATFORM.md PF track).

Today: the listing itself, its place (Nominatim), its MahaRERA registration, surroundings (PF-4), calculators (PF-7) and the
facts the agent confirmed from the builder's brochure (brochure.py; level builder_claim, never above MahaRERA or the listing).
The builder record (PF-3) and portals (PF-5) add readings here as they land."""
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.modules.agentprojects.maharera import make_fetch

from . import brochure, calc, registration, surroundings
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

    def __init__(self, timeout: float = 60.0, register: Any = None, facts_store: Any = None, brochures: Any = None):
        """`register`: the newsroom Store, read before MahaRERA; `facts_store`: where gathered sheets are kept; `brochures`: the
        listing's brochure kits (brochure.Brochures). All optional."""
        self.timeout = timeout
        self.register, self.facts_store, self.brochures = register, facts_store, brochures
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


def brochure_notes(kit: dict, used: int) -> List[str]:
    reg = kit.get("registration") or {}
    out = [f"Brochure: {used} confirmed fact(s) used, always worded as the builder's claim."] if used else []
    if reg.get("status") in ("unverified", "unknown", "registered_by_agent"):
        out.append("Brochure registration: " + (reg.get("note") or reg["status"]))
    return out


def disagreements(facts: Dict[str, Fact]) -> List[str]:
    """Plain lines for every brochure value another source contradicts (shown with the run, like a project issue)."""
    out = []
    for k, f in facts.items():
        for r in f.disagree:
            if r.source == "brochure":
                out.append(f"The builder's brochure says {r.value} for {k}, but {', '.join(f.sources) or 'another source'} "
                           f"says {f.value}; the brochure's value is not used.")
    return out


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

    kits = getattr(clients, "brochures", None)
    lid = doc.get("id") or doc.get("_id")
    kit = await kits.current(str(lid)) if kits is not None and lid else None
    kit_name, kit_rera = brochure.lookup_inputs(kit)
    match, official = await registration.lookup(clients.get_text, clients.fetch_general, doc.get("project_name") or kit_name,
                                                doc.get("rera_no") or kit_rera, where, now, getattr(clients, "register", None))
    rs += official
    if match.project is None:
        notes.append("MahaRERA: " + match.how)
    elif not any(r.key == "possession_now" for r in official):
        notes.append("MahaRERA: matched the registration but could not read its details")
    if kit is not None:
        claimed = brochure.readings(kit, now, {r.key: r.value for r in official}, doc)
        rs += claimed
        notes += brochure_notes(kit, len(claimed))
    first = sheet(rs)
    rs += calc.readings({k: f.value for k, f in first.items() if f.usable}, now)
    out = Sheet(sheet(rs), where, match, notes)
    notes += disagreements(out.facts)
    facts_store = getattr(clients, "facts_store", None)
    if facts_store is not None:  # keep every gathered sheet: the next campaign, and the sources behind each post
        await facts_store.save(out, doc, now)
    return out
