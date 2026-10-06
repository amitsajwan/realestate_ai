"""Our own page for every project in the MahaRERA register (docs/plan/project-pages.md): /projects/<slug>.

Each register record gets a `page_slug` once ("rohan-abhilasha-4-wagholi") and keeps it. The page shows the record's facts with
their source and read date, and a paragraph written by code from those facts only. A page is `indexable` (sitemap, no noindex)
only when it has a filed completion date and homes booked out of the total: thinner pages exist, but stay out of search until the
register's details step fills them in.

Other modules get a project's page with `page_for(db, regno)`; a project the register does not have yet is added through the watch
list first (areastats.watch), and then has its page at once.
"""
import re
import unicodedata
from datetime import datetime
from typing import List, Optional

from app.core import brand
from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from .service import _count, _day

SAME_AREA = 6
_WORDS = re.compile(r"[a-z0-9]+")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()


def base_slug(doc: dict) -> str:
    """Name words (at most 8) plus the area, e.g. "rohan-abhilasha-4-wagholi"; the area word is not repeated."""
    words = _WORDS.findall(_ascii(doc.get("name", "")))[:8] or ["project"]
    area = BY_KEY.get(doc.get("locality") or "")
    tail = _WORDS.findall(_ascii(area.name if area else "pune"))
    if " ".join(tail) not in " ".join(words):
        words += tail
    return "-".join(words)[:80].strip("-")


async def assign_slug(store: Store, doc: dict) -> str:
    """The record's page slug, given once and stored; a clash gets the registration number's last 5 characters."""
    if doc.get("page_slug"):
        return doc["page_slug"]
    slug = base_slug(doc)
    other = await store.projects.find_one({"page_slug": slug})
    if other and other["_id"] != doc["_id"]:
        slug = f"{slug}-{_ascii(doc['_id'])[-5:]}"
    await store.set_project(doc["_id"], page_slug=slug)
    return slug


async def assign_all(store: Store, docs: Optional[List[dict]] = None) -> int:
    """Give every record in our areas or on the watch list its page slug (cheap: only the ones without one). Returns how many."""
    n = 0
    for d in docs if docs is not None else await store.all_projects():
        if not d.get("page_slug") and (d.get("locality") in BY_KEY or d.get("watched_by")):
            await assign_slug(store, d)
            n += 1
    return n


def indexable(doc: dict) -> bool:
    total, booked = _count(doc.get("units_total")), _count(doc.get("units_booked"))
    return bool(_day(doc.get("completion_now")) and total and booked is not None and booked <= total)


def _long(day: Optional[str]) -> Optional[str]:
    if not day:
        return None
    y, m, d = day.split("-")
    return f"{int(d)} {_MONTHS[int(m) - 1]} {y}"


def paragraph(doc: dict) -> str:
    """Plain sentences from the record's facts only: no adjectives, no prices, nothing the register does not say."""
    area = BY_KEY.get(doc.get("locality") or "")
    where = f"in {area.name}, Pune" if area else ("in Pune district" + (f" (pincode {doc['pincode']})" if doc.get("pincode") else ""))
    who = f" by {doc['promoter']}" if doc.get("promoter") else ""
    out = [f"{doc.get('name') or 'This project'} is a project{who} {where}, registered with MahaRERA as {doc.get('regno') or doc['_id']}."]
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if now and first and now != first:
        out.append(f"Its filed completion date is {_long(now)}; at registration it was {_long(first)}.")
    elif now:
        out.append(f"Its filed completion date is {_long(now)}.")
    total, booked = _count(doc.get("units_total")), _count(doc.get("units_booked"))
    read = doc.get("details_checked_at")
    if total and booked is not None and booked <= total:
        when = f" when we read the record on {_long(read.date().isoformat())}" if isinstance(read, datetime) else ""
        out.append(f"{booked} of {total} homes were booked{when}.")
    out.append("Check the MahaRERA record before you book, and ask the builder for the agreement's possession date in writing.")
    return " ".join(out)


def view(doc: dict, same_area: List[dict]) -> dict:
    area = BY_KEY.get(doc.get("locality") or "")
    read = doc.get("details_checked_at")
    return {
        "slug": doc.get("page_slug"), "name": doc.get("name", ""), "regno": doc.get("regno") or doc["_id"],
        "promoter": doc.get("promoter") or None, "pincode": doc.get("pincode") or None,
        "area": {"key": area.key, "slug": area.slug, "name": area.name} if area else None,
        "completion_now": _day(doc.get("completion_now")), "completion_at_registration": _day(doc.get("completion_at_registration")),
        "units_total": _count(doc.get("units_total")), "units_booked": _count(doc.get("units_booked")),
        "details_read_at": read.date().isoformat() if isinstance(read, datetime) and doc.get("details_ok") else None,
        "listed_or_updated": _day(doc.get("last_modified")), "maharera_url": doc.get("source_url") or None,
        "paragraph": paragraph(doc), "indexable": indexable(doc),
        "same_area": [{"name": s.get("name", ""), "slug": s["page_slug"], "completion_now": _day(s.get("completion_now"))} for s in same_area],
        "source": "MahaRERA public records",
    }


def _similar(doc: dict, docs: List[dict]) -> List[dict]:
    """Other indexable projects in the same area, the closest completion year first."""
    if not doc.get("locality"):
        return []
    year = int((_day(doc.get("completion_now")) or "0")[:4] or 0)
    others = [d for d in docs if d["_id"] != doc["_id"] and d.get("locality") == doc["locality"] and d.get("page_slug") and indexable(d)]
    others.sort(key=lambda d: (abs(int(_day(d.get("completion_now"))[:4]) - year) if year else 0, d.get("name", "")))
    return others[:SAME_AREA]


async def project_page(db, slug: str) -> Optional[dict]:
    store = Store(db)
    doc = await store.projects.find_one({"page_slug": slug})
    if doc is None or not (doc.get("locality") in BY_KEY or doc.get("watched_by")):
        return None
    peers = await store.projects_in([doc["locality"]], limit=2000) if doc.get("locality") else []
    return view(doc, _similar(doc, peers))


async def page_for(db, regno: str) -> Optional[dict]:
    """{slug, path, url, indexable} for a project in the register (in our areas or watched); None when it is not there."""
    store = Store(db)
    doc = await store.project((regno or "").strip().upper())
    if doc is None or not (doc.get("locality") in BY_KEY or doc.get("watched_by")):
        return None
    slug = await assign_slug(store, doc)
    return {"slug": slug, "path": f"/projects/{slug}", "url": f"{brand.SITE}/projects/{slug}", "indexable": indexable(doc)}


async def listing(db, area: Optional[str] = None, only_indexable: bool = True, limit: int = 2000) -> List[dict]:
    """Pages for the sitemap and area pages: {slug, name, area, completion_now, indexable}, newest listed first."""
    store = Store(db)
    docs = [d for d in await store.all_projects() if d.get("page_slug") and (d.get("locality") in BY_KEY or d.get("watched_by"))]
    if area:
        key = (BY_KEY.get(area) or next((a for a in BY_KEY.values() if a.slug == area), None))
        docs = [d for d in docs if key and d.get("locality") == key.key]
    if only_indexable:
        docs = [d for d in docs if indexable(d)]
    docs.sort(key=lambda d: (_day(d.get("last_modified")) or "", d.get("name", "")), reverse=True)
    return [{"slug": d["page_slug"], "regno": d.get("regno") or d["_id"], "name": d.get("name", ""), "area": d.get("locality"),
             "completion_now": _day(d.get("completion_now")),
             "listed_or_updated": _day(d.get("last_modified")), "indexable": indexable(d)} for d in docs[:limit]]
