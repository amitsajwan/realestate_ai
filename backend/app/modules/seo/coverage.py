"""Is Google actually indexing our sitemap pages? Search Console's URL Inspection API, a few hundred pages a day.

Once a day (inside the seo loop, app/modules/seo/runner.py) it inspects up to PER_DAY sitemap pages: pages never inspected
first, then those inspected longest ago, so the whole sitemap is covered every few days (Google allows 2,000 a day). Each answer
is kept in `seo_index` ({_id: url, state, verdict, crawled, checked_at}) and the summary on the `gsc_coverage` mark: how many
current sitemap pages are indexed, why the others are not (count per Search Console state, e.g. "Crawled - currently not
indexed") and up to EXAMPLES of them, for the Admin health row. Same read-only service account as searchconsole.py
(GSC_SA_KEY_B64); without it this does nothing.
"""
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx

from app.modules.areastats import searchconsole
from app.modules.newsroom.store import Store

from . import indexnow

log = logging.getLogger(__name__)

API = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
PER_DAY = 200
EVERY = timedelta(hours=24)
COLLECTION = "seo_index"
MARK = "gsc_coverage"
EXAMPLES = 20


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def pick(db, urls: List[str], n: int) -> List[str]:
    """Up to n of `urls`: never inspected first (sitemap order), then the longest ago."""
    seen = {d["_id"]: _aware(d.get("checked_at")) for d in await db.get_collection(COLLECTION).find({}).to_list(None)}
    fresh = [u for u in urls if u not in seen]
    old = sorted((u for u in urls if u in seen), key=lambda u: seen[u] or datetime.min.replace(tzinfo=timezone.utc))
    return (fresh + old)[:n]


async def save(db, url: str, result: dict, now: datetime) -> None:
    s = (result.get("inspectionResult") or {}).get("indexStatusResult") or {}
    fields = {"state": s.get("coverageState") or "Unknown", "verdict": s.get("verdict") or "VERDICT_UNSPECIFIED",
              "crawled": s.get("lastCrawlTime"), "checked_at": now}
    coll = db.get_collection(COLLECTION)
    if await coll.find_one({"_id": url}):
        await coll.update_one({"_id": url}, {"$set": fields})
    else:
        await coll.insert_one({"_id": url, **fields})


async def summary(db, urls: List[str]) -> dict:
    """Coverage of the pages in the sitemap now (pages since dropped from it are not counted)."""
    current = set(urls)
    docs = [d for d in await db.get_collection(COLLECTION).find({}).to_list(None) if d["_id"] in current]
    indexed = [d for d in docs if d.get("verdict") == "PASS"]
    missing = sorted((d for d in docs if d.get("verdict") != "PASS"), key=lambda d: d["_id"])
    return {"sitemap": len(urls), "inspected": len(docs), "indexed": len(indexed),
            "missing_by_state": dict(Counter(d.get("state") or "Unknown" for d in missing).most_common()),
            "not_indexed": [{"url": d["_id"], "state": d.get("state")} for d in missing[:EXAMPLES]]}


async def run_once(store: Store, now: datetime, transport: Optional[httpx.AsyncBaseTransport] = None,
                   force: bool = False) -> Optional[dict]:
    """Inspect today's batch and store the summary. None when switched off or already done today."""
    sa = searchconsole.key()
    if sa is None:
        return None
    last = _aware((await store.get_mark(MARK)).get("at"))
    if not force and last is not None and now - last < EVERY:
        return None
    async with httpx.AsyncClient(timeout=30, transport=transport, follow_redirects=True) as c:
        r = await c.get(indexnow.sitemap_url())
        r.raise_for_status()
        urls = list(dict.fromkeys(u for u, _ in indexnow.parse_sitemap(r.text)))
        bearer = await searchconsole.token(sa, c)
        done = 0
        for url in await pick(store.db, urls, PER_DAY):
            res = await c.post(API, json={"inspectionUrl": url, "siteUrl": searchconsole.site()},
                               headers={"Authorization": f"Bearer {bearer}"})
            if res.status_code == 429:   # quota: keep what we have, carry on tomorrow
                log.warning("coverage: Search Console quota reached after %s pages", done)
                break
            res.raise_for_status()
            await save(store.db, url, res.json(), now)
            done += 1
    out = await summary(store.db, urls)
    await store.set_mark(MARK, at=now, checked_today=done, **out)
    return {"checked": done, "indexed": out["indexed"], "inspected": out["inspected"], "sitemap": out["sitemap"]}
