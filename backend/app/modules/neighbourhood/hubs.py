"""The work hubs with pages of their own (/work-hubs/<slug>): IT parks, office districts, industrial areas, the airport and the
station that Pune buyers commute to. The list is data/hubs.json: name, slug, the place page it stands in, a position checked on
OpenStreetMap (`how` says which object; good to about 300 m), its kind, and where its company list comes from.

A hub's companies come only from the hub's own published tenant list (`companies_url`, read with `companies_pattern`, a regular
expression whose first group is one company's name). A hub that publishes none has no companies on its page: a list copied
from blogs disagreed with itself (2026-11-28, Magarpatta's towers), so we do not guess.
"""
import html as html_lib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .geo import place_name

DATA = Path(__file__).with_name("data") / "hubs.json"
KIND_WORDS = {"it_park": "an IT park", "business_district": "an office district", "airport": "the airport",
              "station": "the railway station", "industrial": "an industrial area"}
MAX_COMPANIES = 200
READY_COMPANIES = 3   # a hub page is worth indexing with this many companies from its own list,
READY_PLACES = 3      # or drive times from this many places


@dataclass(frozen=True)
class Hub:
    slug: str
    name: str
    place: str                     # the place page's slug (/projects/area/<place>) the hub stands in
    lat: float
    lon: float
    kind: str = "it_park"          # it_park | business_district | airport | station | industrial
    companies_url: str = ""        # the hub's own tenant list, when it publishes one
    companies_pattern: str = ""    # regex, group 1 = one company's name on that page
    how: str = ""                  # how the position was checked

    @property
    def work(self) -> bool:
        """A place people work in (not the airport or the station, which are measured as trips)."""
        return self.kind in ("it_park", "business_district", "industrial")


def _load() -> Tuple[Hub, ...]:
    if not DATA.exists():
        return ()
    return tuple(Hub(**h) for h in json.loads(DATA.read_text(encoding="utf-8")))


HUBS: Tuple[Hub, ...] = _load()
BY_SLUG: Dict[str, Hub] = {h.slug: h for h in HUBS}


def parse_companies(page: str, pattern: str) -> List[str]:
    """Company names from a hub's tenant page, each once, in the page's order. Tags inside a match are dropped and entities
    decoded; a match that is not a plausible name (empty, a sentence, a number) is skipped."""
    if not page or not pattern:
        return []
    out: List[str] = []
    seen = set()
    for m in re.finditer(pattern, page, re.I | re.S):
        name = html_lib.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))
        name = re.sub(r"\s+", " ", name).strip(" ,.-|")
        if not (2 <= len(name) <= 80) or not re.search(r"[A-Za-z]", name) or len(name.split()) > 8:
            continue
        if name.lower() not in seen:
            seen.add(name.lower())
            out.append(name)
        if len(out) >= MAX_COMPANIES:
            break
    return out


def ready(companies: List[str], commute_from: List[dict]) -> bool:
    """A hub's page has enough of its own to be indexed (HubCard.ready, HubPage.page_ready)."""
    return len(companies) >= READY_COMPANIES or len({r["place"] for r in commute_from}) >= READY_PLACES


def card(h: Hub) -> dict:
    return {"slug": h.slug, "name": h.name, "place": h.place, "kind": h.kind}


def _day(d: Optional[datetime]) -> str:
    return d.date().isoformat() if isinstance(d, datetime) else ""


def summary(h: Hub, companies: List[str], homes: List[dict], commute: List[dict]) -> str:
    """Two or three plain sentences from the numbers on the page. No model."""
    lines = [f"{h.name} is {KIND_WORDS.get(h.kind, 'a work hub')} in {place_name(h.place)}, Pune."]
    if companies:
        lines.append(f"Its own list names {len(companies)} companies here.")
    if homes:
        nearest = homes[0]
        lines.append(f"{len(homes)} projects with homes to buy are within 5 km; the nearest we list is {nearest['name']}, about "
                     f"{nearest['km']:g} km away.")
    if commute:
        best = min(commute, key=lambda r: r["am"][0])
        lines.append(f"Of the places we measured, {best['name']} has the shortest weekday 9 am drive, {best['am'][0]} to "
                     f"{best['am'][1]} minutes with typical traffic.")
    return " ".join(lines)


def page(h: Hub, stored: Optional[dict], commute_from: Optional[List[dict]] = None,
         changes: Optional[List[dict]] = None) -> dict:
    """The hub's page (HubPage in frontend/lib/site/research.ts): its companies and homes near it from the jobs researcher's
    stored result, drive times from every place that measured it (worked out when the page is read, so a newly measured place
    shows at once). A hub not researched yet still has its page with what is known."""
    data = (stored or {}).get("data") or {}
    companies = list(data.get("companies") or [])
    homes = list(data.get("homes_nearby") or [])
    commute = sorted(commute_from or [], key=lambda r: (r["am"][0], r["name"]))
    out = {**card(h), "summary": summary(h, companies, homes, commute), "companies": companies, "commute_from": commute,
           "homes_nearby": homes, "changes": list(changes or []), "sources": list((stored or {}).get("sources") or []),
           "updated": _day((stored or {}).get("computed_at")), "page_ready": ready(companies, commute)}
    if data.get("companies_source"):
        out["companies_source"] = data["companies_source"]
    return out
