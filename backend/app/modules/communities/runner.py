"""The communities worker loop (app/worker.py): find neighbourhoods weekly, write one article at a time, a few a day.

Off until COMMUNITY_ARTICLES_ENABLED is on. COMMUNITY_ARTICLES_PER_DAY (default 3) paces the writing. Write order
(`next_doc`): never written, most evidence first (discover.rank); then unpublished ones whose last try is RETRY_DAYS old (more
may be mapped by then); then published ones due a refresh (REFRESH_DAYS), oldest first.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.modules.newsroom.store import Store
from app.modules.propertyfacts.place import GetJson

from . import discover, write

log = logging.getLogger(__name__)

POLL_SECONDS = 900
FIND_EVERY = timedelta(days=7)
REFRESH_DAYS = 60
RETRY_DAYS = 14
FOUND_MARK = "communities_found"
WRITTEN_MARK = "communities_written"


def enabled() -> bool:
    return (os.environ.get("COMMUNITY_ARTICLES_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")


def per_day() -> int:
    try:
        return max(1, min(48, int(os.environ.get("COMMUNITY_ARTICLES_PER_DAY") or 3)))
    except ValueError:
        return 3


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def next_doc(store: Store, now: datetime) -> Optional[dict]:
    docs = await store.db.get_collection(discover.COLLECTION).find({}).to_list(None)
    fresh = sorted((d for d in docs if not d.get("written_at")), key=discover.rank)
    if fresh:
        return fresh[0]
    retry = [d for d in docs if not d.get("published") and now - _aware(d["written_at"]) >= timedelta(days=RETRY_DAYS)]
    if retry:
        return sorted(retry, key=discover.rank)[0]
    due = [d for d in docs if d.get("published") and now - _aware(d.get("updated_at") or d["written_at"]) >= timedelta(days=REFRESH_DAYS)]
    return min(due, key=lambda d: _aware(d.get("updated_at") or d["written_at"])) if due else None


async def step(store: Store, llm, get_json: GetJson, now: datetime) -> dict:
    """One round: find when a week has passed, then write one article when the pace allows."""
    out = {}
    found = _aware((await store.get_mark(FOUND_MARK)).get("at"))
    if found is None or now - found >= FIND_EVERY:
        out["found"] = await discover.run(store, get_json, now)
        # nothing found is usually OpenStreetMap not answering: look again in a day, not a week
        at = now if out["found"].get("found") else now - FIND_EVERY + timedelta(days=1)
        await store.set_mark(FOUND_MARK, at=at, **out["found"])
    last = _aware((await store.get_mark(WRITTEN_MARK)).get("at"))
    if last is None or now - last >= timedelta(days=1) / per_day():
        doc = await next_doc(store, now)
        if doc is not None:
            out["wrote"] = await write.write_one(store, doc, llm, get_json, now)
            await store.set_mark(WRITTEN_MARK, at=now, last=doc["_id"])
    return out


async def loop() -> None:
    from app.core.database import get_database
    from app.modules.propertyfacts.gather import Clients
    from app.platform.heartbeats import heartbeat
    from app.platform.llm import default_llm

    log.info("communities: loop started")
    while True:
        try:
            async with heartbeat("communities", get_database, on=enabled()):
                if enabled():
                    clients = Clients()   # fresh per round: its OSM answers are cached for the process
                    out = await step(Store(get_database()), default_llm(), clients.get_json, datetime.now(timezone.utc))
                    if out:
                        log.info("communities: %s", out)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("communities: round failed")
        await asyncio.sleep(POLL_SECONDS)
