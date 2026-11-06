"""What a project's page already holds, for an agent listing that project (owner, 2026-11-06: "when we add a listing we may already have a
page in Avasetu; how can an agent get going quickly"; docs/plan/listing-flow.md).

The agent starts from the page: its name, the home sizes and the prices it publishes, and the pictures it may show. Only what the page
itself shows is offered, so never a picture copied from another site and never a price the page would not print."""
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.modules.newsroom.store import Store

from . import pages, prices
from .areamap import _photos

MAX_PHOTOS = 8
SIZE = re.compile(r"^(\d(?:\.5)?) BHK$")


def _homes(rows: List[dict]) -> List[dict]:
    """One row per size at its lowest published price, smallest first. 'All homes' and plots say nothing about a size."""
    low: Dict[float, int] = {}
    for r in rows:
        m = SIZE.match(str(r.get("bhk") or ""))
        if m:
            bhk = float(m.group(1))
            low[bhk] = min(low.get(bhk, r["from_inr"]), r["from_inr"])
    return [{"bhk": b, "price_inr": low[b]} for b in sorted(low)]


async def listing_start(db, regno: str, now: Optional[datetime] = None) -> Optional[dict]:
    """{slug, name, homes, photos, property_type} for the project with this MahaRERA number, a tower's being its project's page; None when
    it has no page. `property_type` is left out for a project of shops or offices: the agent says which they sell."""
    now = now or datetime.now(timezone.utc)
    docs = await Store(db).shared_projects()
    doc = next((d for d in docs if (d.get("regno") or d["_id"]) == regno), None)
    if doc is None:
        return None
    page = pages.primary_of(doc, docs)
    if not page.get("page_slug"):
        return None
    field, _ = pages._area_of(page)
    peers = [d for d in docs if field and d.get(field) == page.get(field)]
    shown = prices.homes_only(prices.public(pages.group_primary(doc, docs).get("prices"), now), prices.floor_for(page, prices.overall_floors(peers, now)))
    return {"slug": page["page_slug"], "name": pages.names(page)[0], "homes": _homes((shown or {}).get("rows") or []),
            "photos": [{"url": p["url"], "alt": p["alt"]} for p in _photos([page], MAX_PHOTOS)],
            "property_type": "apartment" if pages.homes(page) else None}
