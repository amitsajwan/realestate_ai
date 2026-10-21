"""The owner's weekly SEO note and the pages to ask Google for (docs/plan/seo-system.md section 4 and 5.1).

Once a week (inside the seo loop, app/modules/seo/runner.py) every owner (INSIGHTS_OWNER_IDS, else the calendar's, else the
concierge's) gets one Studio notification (`seo_week`, shown on Home under "Needs you now", opening Insights → Rankings): the
week's numbers beside last week's, and how many pages wait for "Request indexing". Search Console allows that request only by
hand (no API for our page types), so `request_list` picks the pages worth the owner's ~10 clicks a day: sitemap pages Google has
not indexed, list and guide pages first (they link many pages), then project pages buyers look at (hot score, then impressions).
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlparse

from app.modules.insights.collector import owner_ids
from app.modules.newsroom.store import Store
from app.modules.notifications.service import notify

from . import coverage, scoreboard, targets

MARK = "seo_note"
KIND = "seo_week"
EVERY = timedelta(days=7)
PER_DAY = 10
WAITING = ("Discovered - currently not indexed", "URL is unknown to Google", "Crawled - currently not indexed")
HUBS = ("/projects/area/", "/localities/", "/guides/", "/builders/")


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def request_list(store: Store, n: int = PER_DAY * 7) -> List[dict]:
    """Up to n not-indexed sitemap pages, most worth a Request-indexing first: [{url, state, why}]."""
    docs = await store.db.get_collection(coverage.COLLECTION).find({"state": {"$in": list(WAITING)}}).to_list(None)
    if not docs:
        return []
    by_slug = {d.get("page_slug"): d for d in await store.shared_projects() if d.get("page_slug")}

    def rank(doc: dict):
        path = urlparse(doc["_id"]).path
        if path.startswith(HUBS) or path.count("/") <= 1:
            return (0, -path.count("/"), path)
        p = by_slug.get(path.rsplit("/", 1)[-1]) if path.startswith("/projects/") else None
        return (1, -float((p or {}).get("hot_score") or 0), -int((p or {}).get("gsc_impressions") or 0), path)

    def why(doc: dict) -> str:
        path = urlparse(doc["_id"]).path
        if path.startswith(HUBS) or path.count("/") <= 1:
            return "links many pages"
        p = by_slug.get(path.rsplit("/", 1)[-1]) or {}
        return "hot project" if p.get("hot_score") else ("seen on Google" if p.get("gsc_impressions") else "project page")

    docs.sort(key=rank)
    return [{"url": d["_id"], "state": d.get("state"), "why": why(d)} for d in docs[:n]]


def summary(week: Optional[dict], ago: Optional[dict], cov: dict, board: dict, waiting: int) -> str:
    def num(k: str) -> str:
        v = (week or {}).get(k)
        if v is None:
            return "-"
        p = (ago or {}).get(k)
        return f"{v:,}" + (f" ({'+' if v - p >= 0 else ''}{v - p:,})" if isinstance(p, int) and isinstance(v, int) else "")
    idx = f"{cov.get('indexed', 0):,} of {cov.get('inspected', 0):,} checked" if cov.get("inspected") else "not checked yet"
    mb = f"{board.get('above_mb', 0)} of {board.get('searches', 0)}" if board.get("searches") else "-"
    return (f"SEO week: clicks {num('clicks')}, impressions {num('impressions')}, page one {num('page_one')}; indexed {idx}; "
            f"above MagicBricks {mb}. {waiting} pages to ask Google for, {PER_DAY} a day: Insights → Rankings.")


async def run_once(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """This week's note to the owners. None when it was sent this week or there is no owner."""
    owners = owner_ids()
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not owners or (not force and last is not None and now - last < EVERY):
        return None
    snaps = (await store.get_mark(targets.MARK)).get("history") or []
    week = snaps[-1] if snaps else None
    ago = next((h for h in reversed(snaps) if week and _aware(week.get("at")) and _aware(h.get("at"))
                and _aware(week["at"]) - _aware(h["at"]) >= timedelta(days=7)), None)
    waiting = await store.db.get_collection(coverage.COLLECTION).count_documents({"state": {"$in": list(WAITING)}})
    text = summary(week, ago, await store.get_mark(coverage.MARK), await store.get_mark(scoreboard.MARK), waiting)
    for owner in owners:
        await notify(store.db, owner, KIND, text, {"href": "/studio/newsroom/insights?tab=rankings"}, now=now)
    await store.set_mark(MARK, at=now, text=text)
    return {"owners": len(owners), "waiting": waiting}
