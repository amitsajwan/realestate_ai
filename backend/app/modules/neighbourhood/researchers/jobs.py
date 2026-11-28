"""Researcher: jobs. Once for all of Pune (scope "city"), every 30 days: for each work hub (data/hubs.json), the companies on
its own tenant list and the homes near it, stored per hub in `work_hub_research` (store.put_hub) for its page.

- companies: read from the hub's `companies_url` with its `companies_pattern` (hubs.parse_companies). A hub with no published
  list has none: we never guess (hubs.py). When its page cannot be read this time, the last list read stays.
- homes_nearby: project pages in search (areastats.pages.listing) with a checked pin within HOMES_KM, not finished and not sold
  out, nearest first, with the lowest asked price we publish and the filed possession month.
- commute_from is not stored: hub pages work it out from the places' commute research when read (views.hub_view), so a place
  measured after this run shows at once.

The city result (what `present` reads for a place) is each hub's companies; a place shows its hubs within NEAR_KM with the
first SHOWN_COMPANIES companies each.
"""
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.modules.areastats import pages

from ..geo import km, shown_km
from ..hubs import HUBS, Hub, parse_companies
from .base import Context, Found, Researcher, ViewContext

log = logging.getLogger(__name__)

HOMES_KM = 5.0
HOMES_SHOWN = 12
NEAR_KM = 10.0
SHOWN_COMPANIES = 8
SOURCE = "MahaRERA project register (our copy) and each hub's own tenant list"


async def companies_of(ctx: Context, h: Hub, last: Optional[dict]) -> tuple:
    """(companies, companies_source or None). The last list read stays when the page fails or reads as nothing."""
    kept = list(((last or {}).get("data") or {}).get("companies") or [])
    kept_source = ((last or {}).get("data") or {}).get("companies_source")
    if not h.companies_url or not h.companies_pattern:
        return [], None
    try:
        r = await ctx.http.get(h.companies_url, headers={"User-Agent": "Mozilla/5.0 (compatible; research)"},
                               follow_redirects=True)
        names = parse_companies(r.text, h.companies_pattern) if r.status_code == 200 else []
    except Exception as e:   # one hub's site down never stops the others
        log.info("jobs: %s tenant list not read (%s)", h.slug, type(e).__name__)
        names = []
    if not names:
        return kept, kept_source
    return names, {"name": f"{h.name}, its own list", "url": h.companies_url, "read_on": ctx.now.date().isoformat()}


def homes_near(rows: List[dict], h: Hub) -> List[dict]:
    out = []
    for r in rows:
        m = r.get("map") or {}
        if m.get("lat") is None or not r.get("active") or r.get("sold_out"):
            continue
        d = km(h.lat, h.lon, m["lat"], m["lon"])
        if d <= HOMES_KM:
            row = {"slug": r["slug"], "name": r.get("marketed_name") or r.get("name") or r["slug"], "km": shown_km(d)}
            if r.get("price_from"):
                row["price_from"] = r["price_from"]
            if r.get("completion_now"):
                row["possession"] = str(r["completion_now"])[:7]
            out.append(row)
    out.sort(key=lambda x: (x["km"], x["name"]))
    return out[:HOMES_SHOWN]


async def _run(ctx: Context, place: str) -> Optional[Found]:
    rows = await pages.listing(ctx.db, only_indexable=True, limit=20000)
    out: Dict[str, dict] = {}
    for h in HUBS:
        last = await ctx.store.hub(h.slug)
        companies, source = await companies_of(ctx, h, last)
        data = {"companies": companies, "homes_nearby": homes_near(rows, h)}
        if source:
            data["companies_source"] = source
        sources = [{"name": "MahaRERA project register (our copy)", "url": "https://maharera.maharashtra.gov.in/",
                    "read_on": ctx.now.date().isoformat()}] + ([source] if source else [])
        await ctx.store.put_hub(h.slug, data, sources, ctx.now)
        out[h.slug] = {"companies": companies, "companies_count": len(companies)}
    return Found(data={"hubs": out}, sources=[{"name": SOURCE, "read_on": ctx.now.date().isoformat()}])


def _present(data: Any, view: ViewContext) -> Optional[dict]:
    if view.lat is None or view.lon is None:
        return None
    stored = (data or {}).get("hubs") or {}
    rows = []
    for h in HUBS:
        if not h.work:
            continue
        d = km(view.lat, view.lon, h.lat, h.lon)
        if d > NEAR_KM:
            continue
        companies = list((stored.get(h.slug) or {}).get("companies") or [])
        rows.append({"hub": h.name, "hub_slug": h.slug, "km": shown_km(d), "companies": companies[:SHOWN_COMPANIES],
                     "companies_count": len(companies)})
    if not rows:
        return None
    rows.sort(key=lambda r: (r["km"], r["hub"]))
    return {"hubs": rows, "page_ready": any(r["companies"] for r in rows)}


RESEARCHER = Researcher(kind="jobs", every=timedelta(days=30), run=_run, present=_present, scope="city")
