"""Background loop: YouTube discovery and collection, then the pipeline, every RADAR_INTERVAL_SECONDS. Does nothing unless
RADAR_ENABLED. Paused by the owner's `radar_paused` switch."""
import asyncio
import logging

from app.core.database import get_database
from app.platform.controls import is_paused
from app.platform.heartbeats import heartbeat
from app.platform.llm import default_llm
from app.platform.youtube import default_client

from . import pipeline, store, youtube_source
from .config import load

log = logging.getLogger(__name__)


async def run_once(db, cfg, yt, llm) -> dict:
    out = {}
    if yt is not None:
        await youtube_source.seed(db)
        out["videos_added"] = await youtube_source.discover(db, yt, cfg)
        out.update(await youtube_source.collect(db, yt, cfg))
    out.update(await pipeline.process(db, llm, cfg, own=youtube_source.OWN_NAMES))
    return out


async def loop() -> None:
    log.info("radar: loop started")
    indexed = False
    while True:
        cfg = load()
        try:
            async with heartbeat("radar", get_database, on=cfg.enabled):
                if cfg.enabled:
                    db = get_database()
                    if await is_paused(db, "radar_paused"):
                        log.info("radar: paused by owner, cycle skipped")
                    else:
                        if not indexed:
                            await store.ensure_indexes(db)
                            indexed = True
                        yt = default_client()
                        if yt is None:
                            log.warning("radar: YOUTUBE_API_KEY not set; only pasted signals are processed")
                        counts = await run_once(db, cfg, yt, default_llm())
                        log.info("radar: cycle done %s", counts)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("radar: cycle failed")
        await asyncio.sleep(cfg.interval_s)
