"""The work hubs with pages of their own (/work-hubs/<slug>): IT parks and job centres Pune buyers commute to. The list is
data/hubs.json (name, slug, place, position, kind, where its company list comes from). The research workstream fills in
`card` and `page` and the hub researcher (researchers/jobs.py) that keeps each hub's companies and nearby homes.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

DATA = Path(__file__).with_name("data") / "hubs.json"


@dataclass(frozen=True)
class Hub:
    slug: str
    name: str
    place: str
    lat: float
    lon: float
    kind: str = "it_park"          # it_park | business_district | airport | station | industrial
    companies_url: str = ""        # the hub's own tenant list, when it publishes one


def _load() -> Tuple[Hub, ...]:
    if not DATA.exists():
        return ()
    return tuple(Hub(**h) for h in json.loads(DATA.read_text(encoding="utf-8")))


HUBS: Tuple[Hub, ...] = _load()
BY_SLUG: Dict[str, Hub] = {h.slug: h for h in HUBS}


def card(h: Hub) -> dict:
    return {"slug": h.slug, "name": h.name, "place": h.place, "kind": h.kind}


def page(h: Hub, stored: Optional[dict]) -> Optional[dict]:
    return None
