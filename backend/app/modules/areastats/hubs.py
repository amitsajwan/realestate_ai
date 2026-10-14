"""Pages that link project pages together (docs/plan/rank-loop.md R5, R6): the internal links Google reads to decide which pages
of a site matter.

- active(db, area or place):  "Most active projects in <area>" for area and place pages: projects the page doctor is working
                              on first (`seo_link_slot`), then by hot score; each with ONE fact line and its source, never a score;
- near_guide(db, doc):        the published neighbourhood guide nearest a project (within NEAR_KM), for "Near <neighbourhood>";
- near_projects(db, guide):   project pages within NEAR_KM of a guide, for "Projects nearby";
- builders(db) / builder_page(db, slug): one page per promoter with every Pune project of theirs in the register.
Links use the name people search for (`search_name`, seo.targets) when there is one. Read-only.
"""
from datetime import datetime, timezone
from typing import List, Optional

from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from . import hot
from .enrich import km_between
from .pages import _long, _served, booked, can_host, cluster_updated, indexable, is_old, months_later, names
from .text import builder_slug
from .service import _count, _day

ACTIVE = 8
NEAR_KM = 2.0
NEAR_PROJECTS = 8
BUILDER_MIN = 2                 # indexable projects a builder page needs before it goes in search
COMMUNITIES = "communities"


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def link_name(d: dict) -> str:
    """The anchor text for a link into a project page: how people search for it, else its marketed name."""
    return d.get("search_name") or names(d)[0]


def fact_line(d: dict, now: datetime) -> dict:
    """One sourced fact for a project in a list: homes booked lately, else the filed completion date, else the registration."""
    b = hot.bookings(d, now)
    if b:
        return {"fact": b["evidence"], "source": "MahaRERA"}
    if _day(d.get("completion_now")):
        moved = months_later(d)
        return {"fact": f"completion filed for {_long(_day(d['completion_now']))}" + (f", moved {moved} months later" if moved else ""),
                "source": "MahaRERA"}
    return {"fact": f"registered with MahaRERA as {d.get('regno') or d['_id']}", "source": "MahaRERA"}


def _primaries(docs: List[dict]) -> List[dict]:
    """The records that are a page of their own: served, and not standing behind a primary search may list."""
    hosted = {d["_id"] for d in docs if can_host(d)}
    return [d for d in docs if _served(d) and d.get("cluster_primary") not in hosted]


def _slot(d: dict, now: datetime) -> bool:
    until = _aware(d.get("seo_link_slot_until"))
    return bool(until and until > now)


async def active(db, area: Optional[str] = None, place: Optional[str] = None, limit: int = ACTIVE,
                 now: Optional[datetime] = None) -> List[dict]:
    """Up to `limit` active project pages in an area (key or slug) or a Pune place: doctor's link slots first, then hot score,
    then Google impressions. [{slug, name, fact, source}]."""
    now = now or datetime.now(timezone.utc)
    docs = _primaries(await Store(db).all_projects())
    if area:
        a = BY_KEY.get(area) or next((x for x in BY_KEY.values() if x.slug == area), None)
        if a is None:
            return []
        docs = [d for d in docs if d.get("locality") == a.key]
    elif place:
        want = place.strip().lower().replace("-", "_")
        docs = [d for d in docs if d.get("pune_place") == want]
    else:
        return []
    docs = [d for d in docs if indexable(d) and not is_old(d)]
    docs.sort(key=lambda d: (not _slot(d, now), -(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0), d.get("name", "")))
    return [{"slug": d["page_slug"], "name": link_name(d), **fact_line(d, now)} for d in docs[:limit]]


def _geo(d: dict) -> Optional[tuple]:
    g = d.get("geo") or {}
    checked = (((d.get("enrichment") or {}).get("steps") or {}).get("places") or {}).get("ok")
    return (float(g["lat"]), float(g["lon"])) if g.get("lat") is not None and g.get("lon") is not None and checked else None


async def near_guide(db, doc: dict) -> Optional[dict]:
    """The nearest published neighbourhood guide within NEAR_KM of a project whose position was checked: {name, path, km}."""
    at = _geo(doc)
    if at is None:
        return None
    best = None
    for g in await db.get_collection(COMMUNITIES).find({"published": True}).to_list(None):
        if g.get("lat") is None or g.get("lon") is None:
            continue
        k = km_between(at, (float(g["lat"]), float(g["lon"])))
        if k <= NEAR_KM and (best is None or k < best[0]):
            best = (k, g)
    if best is None:
        return None
    k, g = best
    a = BY_KEY.get(g.get("area") or "")
    if a is None or not g.get("slug"):
        return None
    return {"name": g.get("name"), "path": f"/localities/{a.slug}/{g['slug']}", "km": round(k, 1)}


async def near_projects(db, area_slug: str, slug: str, limit: int = NEAR_PROJECTS) -> List[dict]:
    """Project pages within NEAR_KM of a published guide, nearest first: [{slug, name, km, fact, source}]."""
    g = await db.get_collection(COMMUNITIES).find_one({"_id": f"{area_slug}/{slug}"})
    if not g or not g.get("published") or g.get("lat") is None:
        return []
    now, centre, out = datetime.now(timezone.utc), (float(g["lat"]), float(g["lon"])), []
    for d in _primaries(await Store(db).all_projects()):
        at = _geo(d)
        if at is None or not indexable(d):
            continue
        k = km_between(centre, at)
        if k <= NEAR_KM:
            out.append((k, d))
    out.sort(key=lambda x: (x[0], x[1].get("name", "")))
    return [{"slug": d["page_slug"], "name": link_name(d), "km": round(k, 1), **fact_line(d, now)} for k, d in out[:limit]]


# ---- builder pages (R6) ---------------------------------------------------------------------------------------------------

def _by_builder(docs: List[dict]) -> dict:
    out: dict = {}
    for d in _primaries(docs):
        s = builder_slug(d.get("promoter"))
        if s:
            out.setdefault(s, []).append(d)
    return out


async def builders(db, only_indexable: bool = True) -> List[dict]:
    """Every builder with projects in the register: [{slug, name, projects, indexable, page_updated}], most projects first."""
    docs = await Store(db).all_projects()
    out = []
    for s, mine in _by_builder(docs).items():
        n = sum(1 for d in mine if indexable(d))
        if only_indexable and n < BUILDER_MIN:
            continue
        stamps = [x for x in (cluster_updated(d, docs) for d in mine) if x]
        out.append({"slug": s, "name": _builder_name(mine), "projects": len(mine), "indexable": n >= BUILDER_MIN,
                    "page_updated": max(stamps) if stamps else None})
    out.sort(key=lambda r: (-r["projects"], r["slug"]))
    return out


def _builder_name(mine: List[dict]) -> str:
    """The promoter's name as MahaRERA writes it most often."""
    counts: dict = {}
    for d in mine:
        n = " ".join(str(d.get("promoter") or "").split())
        if n:
            counts[n] = counts.get(n, 0) + 1
    return max(counts.items(), key=lambda x: (x[1], -len(x[0])))[0] if counts else ""


async def builder_page(db, slug: str) -> Optional[dict]:
    """A builder's page: every Pune project of theirs (towers merged) with MahaRERA's dates and bookings, and how often the
    filed completion date moved. None for an unknown builder."""
    docs = await Store(db).all_projects()
    mine = _by_builder(docs).get(slug)
    if not mine:
        return None
    now = datetime.now(timezone.utc)
    mine.sort(key=lambda d: (is_old(d), _day(d.get("completion_now")) or "9999", d.get("name", "")))
    moved = [m for m in (months_later(d) for d in mine) if m]
    with_dates = sum(1 for d in mine if months_later(d) is not None)
    total = sum(_count(d.get("units_total")) or 0 for d in mine)
    sold = sum(booked(d) or 0 for d in mine)
    areas = sorted({BY_KEY[d["locality"]].name for d in mine if d.get("locality") in BY_KEY})
    stamps = [x for x in (cluster_updated(d, docs) for d in mine) if x]
    n_index = sum(1 for d in mine if indexable(d))
    return {
        "slug": slug, "name": _builder_name(mine), "projects_count": len(mine), "areas": areas,
        "active": sum(1 for d in mine if not is_old(d)), "units_total": total or None, "units_booked": sold or None,
        "with_dates": with_dates, "moved_later": len(moved), "avg_months_later": round(sum(moved) / len(moved)) if moved else None,
        "indexable": n_index >= BUILDER_MIN, "page_updated": max(stamps) if stamps else None, "source": "MahaRERA public records",
        "projects": [{"slug": d["page_slug"], "name": link_name(d), "legal_name": d.get("name", ""), "regno": d.get("regno") or d["_id"],
                      "area": BY_KEY[d["locality"]].name if d.get("locality") in BY_KEY else d.get("pune_place_name"),
                      "completion_now": _day(d.get("completion_now")), "months_later": months_later(d),
                      "units_total": _count(d.get("units_total")), "units_booked": booked(d), "active": not is_old(d),
                      **fact_line(d, now)} for d in mine],
    }
