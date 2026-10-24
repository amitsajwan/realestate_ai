"""Searches we have no good page for (docs/plan/rank-loop.md R7): matched to page types we already have, never written by AI.

Weekly, inside the seo loop, from two readings of `search_demand`:
- Search Console (`gsc`): phrases with MIN_IMPRESSIONS or more in 28 days (or rising) where none of our pages sits in the top 20;
- our own Google searches (`rank`, areastats.websearch through Serper): searches run in the last WINDOW_DAYS where our site is not
  in the results or sits below the top 20. Search Console only reports searches where we already show, nearly always inside the
  top 20, so on its own it found no gaps; these are the searches we are missing from.
A phrase is judged by its own words, not by the kind it was filed under: a search that only names one project (no words like
"flats", "projects", "2 bhk", "price" or a budget) is the project page's business, not a gap. Each is matched by fixed rules to an
EXISTING page type:
  "2 bhk <area>"             -> /2-bhk/<area slug>      (3 bhk likewise)
  "under 50 lakh <area>" ... -> /price/<band>/<area slug>
  "<builder> projects"       -> /builders/<slug>
  "projects / flats / property rates in <area>" -> /projects/area/<area slug> (the place page)
A match says the page exists but does not rank: the owner links it or the doctor works on it. No match is listed as a search
with no page type, for the owner to decide. Searches naming one of our areas come first, then the most seen. Each item says
where it came from (`source`: "search_console" or "searched"). Stored on the `seo_gaps` mark; read-only otherwise.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.core.areas import in_search as named_in
from app.modules.areastats import brands, searchconsole, websearch
from app.modules.newsroom.store import Store

MARK = "seo_gaps"
DEMAND = "search_demand"
EVERY = timedelta(days=7)
MIN_IMPRESSIONS = 30
TOP = 20
KEEP = 60
WINDOW_DAYS = 28      # our own Google searches older than this no longer count
# (slug, phrase pattern): the budget pages (frontend lib/site/filters.ts BANDS)
BANDS = [("under-50-lakh", r"(under|below|within|upto|up to)\s*50\s*(l|lakh|lakhs|lac)"),
         ("50-75-lakh", r"50\s*(-|to)\s*75\s*(l|lakh|lakhs|lac)"),
         ("75-lakh-1-crore", r"75\s*(l|lakh|lakhs|lac)?\s*(-|to)\s*1\s*(cr|crore)"),
         ("1-1.5-crore", r"1\s*(-|to)\s*1\.5\s*(cr|crore)"),
         ("1.5-2-crore", r"1\.5\s*(-|to)\s*2\s*(cr|crore)")]
BHK = re.compile(r"\b([23])\s*bhk\b", re.I)
PROJECTS = re.compile(r"\b(projects?|new launch|upcoming|under construction|flats?|apartments?|propert(y|ies)|homes?|houses?)\b", re.I)
PRICE = re.compile(r"\b(price|prices|rates?|cost)\b", re.I)


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def template(phrase: str, builder_slugs: List[str]) -> Optional[str]:
    """The existing page type for a search, by fixed rules; None when there is none."""
    areas = named_in(phrase)
    area = areas[0] if areas else None
    m = BHK.search(phrase)
    if m and area:
        return f"/{m.group(1)}-bhk/{area.slug}"
    for slug, rx in BANDS:
        if area and re.search(rx, phrase, re.I):
            return f"/price/{slug}/{area.slug}"
    brand = brands.for_search(phrase)   # "godrej projects pune": the brand page, not one of its companies
    if brand is not None and brand.slug in builder_slugs:
        return f"/builders/{brand.slug}"
    words = "-".join(re.findall(r"[a-z0-9]+", phrase.lower()))
    for b in builder_slugs:
        if b and (words.startswith(b + "-") or f"-{b}-" in f"-{words}-"):
            return f"/builders/{b}"
    if area and (PROJECTS.search(phrase) or PRICE.search(phrase)):
        return f"/projects/area/{area.slug}"   # the place page owns "flats / projects / property prices in <area>"
    return None


def asks_for_homes(phrase: str) -> bool:
    """The search asks for homes, prices or a budget, not just one project by name."""
    return bool(BHK.search(phrase) or PROJECTS.search(phrase) or PRICE.search(phrase)
                or any(re.search(rx, phrase, re.I) for _, rx in BANDS))


def _console_gap(d: dict) -> Optional[dict]:
    g = d.get("gsc") or {}
    imp = int(g.get("impressions") or 0)
    if not (imp >= MIN_IMPRESSIONS or (d.get("rising") and imp > 0)):
        return None
    pos = g.get("position")
    if pos is not None and float(pos) <= TOP:
        return None
    return {"source": "search_console", "impressions": imp, "position": pos, "shown_pages": (g.get("pages") or [])[:3]}


def _searched_gap(d: dict, now: datetime) -> Optional[dict]:
    r = d.get("rank") or {}
    at = _aware(r.get("at"))
    if at is None or now - at > timedelta(days=WINDOW_DAYS):
        return None
    pos = r.get("position")
    if pos is not None and int(pos) <= TOP:
        return None
    g = d.get("gsc") or {}
    return {"source": "searched", "impressions": int(g.get("impressions") or 0), "position": pos,
            "shown_pages": (g.get("pages") or [])[:3], "searched_at": at.isoformat()}


def gap(d: dict, slugs: List[str], now: datetime) -> Optional[dict]:
    """One search_demand row as a gap item, or None when we rank for it, it was not seen, or it only names a project."""
    phrase = d.get("phrase") or d["_id"]
    page = template(phrase, slugs)
    if d.get("kind") == "project" and not asks_for_homes(phrase):
        return None   # "<project> kharadi pune": the project page answers it, even when its builder has a page
    found = _console_gap(d) or _searched_gap(d, now)
    if found is None:
        return None
    areas = named_in(phrase)
    return {"phrase": phrase, **found, "rising": bool(d.get("rising")), "area": areas[0].key if areas else None,
            "page": page, "action": "work on this page" if page else "no page type: owner decides"}


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    if searchconsole.key() is None and websearch.provider() is None and not force:   # nothing reads searches
        return None
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    from app.modules.areastats.hubs import builders
    slugs = [b["slug"] for b in await builders(store.db)]
    items = [g for g in (gap(d, slugs, now) for d in await store.db.get_collection(DEMAND).find({}).to_list(20000)) if g]
    # our areas first, then the most seen (Search Console impressions), then searches with a page type before those without
    items.sort(key=lambda r: (r["area"] is None, -r["impressions"], r["page"] is None, r["phrase"]))
    with_page = sum(1 for r in items if r["page"])
    await store.set_mark(MARK, at=now, items=items[:KEEP], total=len(items), with_page=with_page,
                         searched=sum(1 for r in items if r["source"] == "searched"))
    return {"gaps": len(items), "with_page": with_page}
