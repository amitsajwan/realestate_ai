"""Are our areas' project pages still fresh? Once a day, inside the seo loop (docs/plan/seo-system.md 8a, step 1).

We are cited because each page opens with a dated answer from its own record; when the register read or the enrichment stops
answering, pages keep old text and old dates and nothing fails loudly. So once a day we count the live project pages in our
areas (indexable, a group's primary, filed completion date still to come: finished projects are not re-read on purpose) whose
`pages.page_updated` is within WINDOW. The details read comes back every 30 days (areastats.refresh DETAILS_MAX_AGE_DAYS), so
a healthy page is never older than that; WINDOW leaves a few days for the queue. Kept on the `seo_freshness` mark: {at, pages,
fresh, by_area: {area: {pages, fresh}}, oldest: [{slug, updated}]}; Admin → Health reads it (admin/health.freshness_row).
Reads only.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.areas import BY_KEY
from app.modules.areastats import pages
from app.modules.newsroom.store import Store

MARK = "seo_freshness"
EVERY = timedelta(hours=24)
WINDOW = timedelta(days=35)
OLDEST = 5


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def counted(doc: dict, today: date) -> bool:
    """A page we expect to be re-read: live, in our areas, its own group's page, and not finished."""
    return (bool(doc.get("page_slug")) and doc.get("locality") in BY_KEY and not doc.get("cluster_primary")
            and pages.indexable(doc) and not pages.is_old(doc, today))


def share(docs: List[dict], now: datetime) -> dict:
    """{pages, fresh, by_area, oldest} over the counted pages (see the module note)."""
    since = now - WINDOW
    by_area: Dict[str, Dict[str, int]] = {}
    stale = []
    for d in docs:
        if not counted(d, now.date()):
            continue
        updated = pages.page_updated(d)
        fresh = bool(updated) and datetime.fromisoformat(updated) >= since
        a = by_area.setdefault(d["locality"], {"pages": 0, "fresh": 0})
        a["pages"] += 1
        a["fresh"] += fresh
        if not fresh:
            stale.append((updated or "", d["page_slug"]))
    stale.sort()
    return {"pages": sum(a["pages"] for a in by_area.values()), "fresh": sum(a["fresh"] for a in by_area.values()),
            "by_area": by_area, "oldest": [{"slug": s, "updated": u or None} for u, s in stale[:OLDEST]]}


async def run_once(store: Store, now: datetime) -> Optional[dict]:
    """Today's count onto the mark. None when it was counted in the last EVERY, or no page counts yet (an empty register)."""
    last = _aware((await store.get_mark(MARK)).get("at"))
    if last is not None and now - last < EVERY:
        return None
    out = share(await store.shared_projects(), now)
    if not out["pages"]:
        return None
    await store.set_mark(MARK, at=now, **out)
    return {"pages": out["pages"], "fresh": out["fresh"]}
