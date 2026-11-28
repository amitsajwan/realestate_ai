"""The research loop (.claude/skills/add-background-loop): once an hour, every researcher that is switched on runs for the
places whose data is older than its `every`, at most cfg.places_per_cycle places each, important places first. A failure for
one place is noted on that place and never stops the others; the last good data stays on the page.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx

from app.core.database import get_database
from app.platform.heartbeats import heartbeat

from . import config, places
from .researchers import REGISTRY, Context, Researcher
from .store import CITY, Store

log = logging.getLogger(__name__)

INTERVAL_S = 3600


def _aware(d: Optional[datetime]) -> Optional[datetime]:
    if d is None:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def due(r: Researcher, place_list, tried: Dict[str, datetime], now: datetime, limit: int):
    """The places this researcher should run for now: never tried first, then the oldest, keeping the given order."""
    if r.scope == "city":
        last = _aware(tried.get(CITY))
        return [CITY] if last is None or now - last >= r.every else []
    never = [p for p in place_list if p not in tried]
    stale = sorted((p for p in place_list if p in tried and now - _aware(tried[p]) >= r.every), key=lambda p: _aware(tried[p]))
    return (never + stale)[:limit]


async def run_once(db, now: datetime, http=None, cfg=None) -> Dict[str, dict]:
    cfg = cfg or config.load()
    store = Store(db)
    place_list = await places.all_places(db)
    counts: Dict[str, dict] = {}
    own_client = http is None
    client = http or httpx.AsyncClient(timeout=30)
    try:
        ctx = Context(db=db, store=store, now=now, cfg=cfg, http=client)
        for r in REGISTRY:
            if not r.enabled(cfg):
                continue
            c = counts.setdefault(r.kind, {"ran": 0, "stored": 0, "failed": 0})
            for place in due(r, place_list, await store.tried(r.kind), now, cfg.places_per_cycle):
                c["ran"] += 1
                try:
                    found = await r.run(ctx, place)
                except Exception as e:
                    log.warning("neighbourhood: %s for %s failed: %s", r.kind, place, e)
                    await store.put(r.kind, place, None, [], now, ok=False, note=str(e)[:300])
                    c["failed"] += 1
                    continue
                if found is None:
                    await store.put(r.kind, place, None, [], now, ok=False, note="nothing found")
                    continue
                await store.put(r.kind, place, found.data, found.sources, now)
                c["stored"] += 1
    finally:
        if own_client:
            await client.aclose()
    return counts


async def loop() -> None:
    while True:
        cfg = config.load()
        if cfg.enabled:
            try:
                async with heartbeat("neighbourhood", get_database):
                    counts = await run_once(get_database(), datetime.now(timezone.utc), cfg=cfg)
                    log.info("neighbourhood: %s", counts)
            except Exception:
                log.exception("neighbourhood: cycle failed")
        await asyncio.sleep(INTERVAL_S)
