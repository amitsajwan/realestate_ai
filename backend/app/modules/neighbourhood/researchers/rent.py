"""Researcher: rent. Asked rent by flat size for one place, from the portals' rental listings and our own agents' rent listings
(owner 2026-11-28: reading the portals is fine; asked rent only, a range with how many listings and which month, never "you
will earn"). What each portal gives and how listings become rows: rent_sources.py.

One run for one place (every EVERY, 30 days; at most NEIGHBOURHOOD_PLACES_PER_CYCLE places a loop cycle, the loop's limit):
1. the portals' rent pages for the place, read politely through areastats.webfacts.read_page (its robots.txt rules, AvasetuBot's
   user agent, 2 s between two reads of one site): MagicBricks once per size (1, 2 and 3 BHK, 30 listings each), NoBroker and
   Square Yards once (about 25 of every size). The address is guessed from the place's words (and rent_sources.ALIASES); a
   place none of whose guesses answers costs one Serper search ("flats for rent in <place> Pune"), at most
   NEIGHBOURHOOD_RENT_SEARCHES_PER_RUN a cycle, whose results give each portal's own word for the place. The words that worked
   are kept with the data, so next month asks no search;
2. our agents' live rent listings in the place (listings.ListingService.public_by_locality: flats of 1 to 3 BHK);
3. rows (rent_sources.rows): low (25th percentile), median, high (75th), listings and listings per source, for this month;
4. yield_pct, when areastats has starting prices for that size from 3 projects or more in the place still being sold: the
   median rent of a year over the median starting price. It is a gross figure on asking prices, so pages call it that.
Nothing read from any portal or agent is a failure (the last good rows stay on the page); a thin month is stored and hidden.

present: rows with ROW_MIN (10) listings or more; hidden when none. page_ready with 2 such rows. On a project page with its own
pin the place's rows stay, and `within_km` / `listings_within_km` say how many of the listings with a position are within
NEAR_KM of the project, when there are ROW_MIN of them.
"""
import logging
import re
import statistics
from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.modules.areastats import pages as area_pages
from app.modules.areastats import webfacts, websearch
from app.modules.listings.service import ListingService

from .. import rent_sources
from ..schools_geo import km
from .base import Context, Found, Researcher, ViewContext

log = logging.getLogger(__name__)

EVERY = timedelta(days=30)
ROW_MIN = 10
PAGE_ROWS = 2
NEAR_KM = 2.0
PRICE_PROJECTS_MIN = 3
YIELD_RANGE = (0.5, 10.0)          # a gross yield outside this is a mismatch of sizes or a sale price read as rent
TRANSPORT = None                   # tests pass an httpx.MockTransport here
PORTALS = {"magicbricks": "MagicBricks", "nobroker": "NoBroker", "squareyards": "Square Yards"}
FOUND_IN = {"magicbricks": re.compile(r"magicbricks\.com/(?:\d-bhk-)?flats-for-rent-in-([a-z0-9-]+?)-pune-pppfr"),
            "nobroker": re.compile(r"nobroker\.in/(?:\d-?bhk-)?flats-for-rent-in-([a-z0-9-]+?)_pune"),
            "squareyards": re.compile(r"squareyards\.com/rent/property-for-rent-in-([a-z0-9-]+?)-pune")}

_searches: Dict[str, Any] = {"cycle": None, "spent": 0}


async def fetch(url: str) -> Optional[str]:
    return await webfacts.read_page(url, transport=TRANSPORT)


def _urls(portal: str, word: str) -> List[str]:
    if portal == "magicbricks":
        return [rent_sources.magicbricks_url(word, b) for b in rent_sources.BHKS]
    if portal == "nobroker":
        return [rent_sources.nobroker_url(word)]
    return [rent_sources.squareyards_url(word)]


async def read_portal(portal: str, word: str) -> tuple:
    """(listings, [{site, url, ok, listings}]) from one portal's pages for one spelling of the place. Every size's page is
    asked: a place may have no 1 BHK page and still have 2 and 3 BHK ones."""
    got: List[dict] = []
    read = []
    for url in _urls(portal, word):
        page = await fetch(url)
        found = rent_sources.PARSERS[portal](page) if page else []
        read.append({"site": portal, "url": url, "ok": bool(found), "listings": len(found)})
        got += found
    return got, read


def _name(place: str) -> str:
    return place.replace("_", " ").replace("-", " ").strip().title()


def _search_allowed(ctx: Context) -> bool:
    if _searches["cycle"] != ctx.now:
        _searches.update({"cycle": ctx.now, "spent": 0})
    return bool(getattr(ctx.cfg, "serper_key", "")) and _searches["spent"] < int(getattr(ctx.cfg, "rent_searches_per_run", 0) or 0)


async def search_words(ctx: Context, place: str) -> Dict[str, str]:
    """{portal: its word for the place} from one Serper search; {} without a key, past the cycle's cap, or on failure."""
    if not _search_allowed(ctx):
        return {}
    _searches["spent"] += 1
    try:
        results = await websearch.serper(ctx.cfg.serper_key)(f"flats for rent in {_name(place)} Pune")
    except Exception as e:
        log.info("rent: search for %s failed (%s)", place, type(e).__name__)
        return {}
    out: Dict[str, str] = {}
    for r in results:
        for portal, pat in FOUND_IN.items():
            m = pat.search(r.get("link") or "")
            if m and portal not in out:
                out[portal] = m.group(1)
    return out


async def agent_rents(db, place: str) -> List[dict]:
    """Our agents' live rent listings of flats in the place, as rent_sources listings (source "avasetu")."""
    items, _ = await ListingService(db).public_by_locality(_name(place), limit=500)
    out = []
    for it in items:
        if it.transaction != "rent" or (it.property_type or "apartment") != "apartment" or it.bhk is None or it.bhk != int(it.bhk):
            continue
        got = rent_sources._listing("avasetu", it.id, it.price_inr, int(it.bhk), it.carpet_sqft, it.project_name or "")
        if got:
            out.append(got)
    return out


async def sale_prices(db, place: str) -> Dict[str, int]:
    """{"2 BHK": median starting price} over the place's projects still being sold that areastats prices, for sizes with
    PRICE_PROJECTS_MIN projects or more."""
    per: Dict[str, List[int]] = {}
    for d in await area_pages.listing(db, only_indexable=False, place=place):
        if not d.get("active") or d.get("sold_out"):
            continue
        for h in d.get("homes") or []:
            if h.get("bhk") and h.get("from_inr"):
                per.setdefault(h["bhk"], []).append(int(h["from_inr"]))
    return {b: int(statistics.median(v)) for b, v in per.items() if len(v) >= PRICE_PROJECTS_MIN}


def with_yield(rows: List[dict], prices: Dict[str, int]) -> List[dict]:
    out = []
    for r in rows:
        price = prices.get(r["bhk"])
        y = round(r["median"] * 12 / price * 100, 1) if price else None
        out.append({**r, **({"yield_pct": y} if y and YIELD_RANGE[0] <= y <= YIELD_RANGE[1] else {})})
    return out


async def _run(ctx: Context, place: str) -> Optional[Found]:
    prev = await ctx.store.get("rent", place)
    known: Dict[str, str] = dict((((prev or {}).get("data") or {}).get("words")) or {})
    listings: List[dict] = []
    read: List[dict] = []
    words: Dict[str, str] = {}
    missing = []
    for portal in PORTALS:
        tries = [known[portal]] if portal in known else rent_sources.place_words(place)
        for word in tries:
            got, r = await read_portal(portal, word)
            read += r
            if got:
                listings += got
                words[portal] = word
                break
        else:
            missing.append(portal)
    if missing:
        found = await search_words(ctx, place)
        for portal in missing:
            word = found.get(portal)
            if not word or word in rent_sources.place_words(place):
                continue
            got, r = await read_portal(portal, word)
            read += r
            if got:
                listings += got
                words[portal] = word
    try:
        listings += await agent_rents(ctx.db, place)
    except Exception as e:
        log.info("rent: agents' listings for %s not read (%s)", place, e)
    if not listings:
        raise RuntimeError("no rent listing read: " + ", ".join(f"{r['site']} {'ok' if r['ok'] else 'none'}" for r in read[:6]))
    rows = rent_sources.rows(listings)
    try:
        prices = await sale_prices(ctx.db, place)
    except Exception as e:
        log.info("rent: sale prices for %s not read (%s)", place, e)
        prices = {}
    rows = with_yield(rows, prices)
    day = ctx.now.date().isoformat()
    used = {l["source"] for l in listings}
    sources = [{"name": f"{PORTALS[p]} rent listings", "url": _urls(p, words[p])[0], "read_on": day} for p in PORTALS
               if p in used and p in words]
    if "avasetu" in used:
        sources.append({"name": "Avasetu agents' rent listings", "read_on": day})
    if any("yield_pct" in r for r in rows):
        sources.append({"name": "Asking prices of new projects (Avasetu project pages)", "read_on": day})
    points = [[l["bhk"], l["rent"], l["lat"], l["lon"]] for l in rent_sources.dedupe(listings) if "lat" in l]
    return Found(data={"month": ctx.now.strftime("%Y-%m"), "rows": rows, "points": points, "words": {**known, **words},
                       "read": read}, sources=sources)


def _present(data: Any, view: ViewContext) -> Optional[dict]:
    if not isinstance(data, dict):
        return None
    rows = [{k: r[k] for k in ("bhk", "low", "median", "high", "listings", "yield_pct") if k in r}
            for r in data.get("rows") or [] if r.get("listings", 0) >= ROW_MIN]
    if not rows:
        return None
    out = {"month": data.get("month") or "", "rows": rows, "page_ready": len(rows) >= PAGE_ROWS}
    if view.project is not None and isinstance(view.lat, (int, float)) and isinstance(view.lon, (int, float)):
        near = sum(1 for p in data.get("points") or [] if km(view.lat, view.lon, p[2], p[3]) <= NEAR_KM)
        if near >= ROW_MIN:
            out.update({"within_km": NEAR_KM, "listings_within_km": near})
    return out


RESEARCHER = Researcher(kind="rent", every=EVERY, run=_run, present=_present,
                        enabled=lambda cfg: bool(getattr(cfg, "rent_enabled", True)))
