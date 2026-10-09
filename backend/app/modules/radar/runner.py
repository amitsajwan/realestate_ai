"""Background loop, every RADAR_INTERVAL_SECONDS (docs/RADAR.md §9). Does nothing unless RADAR_ENABLED; paused by the owner's
`radar_paused` switch. A cycle: learn from new labels -> collect from each source -> pipeline -> redraft -> follow-ups.
Daily: the discovery agent. Weekly: scorer refit, draft rules, demand themes. One failing source never stops the others."""
import asyncio
import logging

from app.core.database import get_database
from app.platform.controls import is_paused
from app.platform.heartbeats import heartbeat
from app.platform.llm import default_llm

from . import discovery, examples, followup, learn, pipeline, store, themes
from . import draft as drafting
from .config import RadarConfig, load
from .sources import ALL as SOURCES
from .sources.youtube import OWN_NAMES

log = logging.getLogger(__name__)


async def _job(db, name: str, every_h: float, coro_fn) -> dict:
    if not await store.due(db, name, every_h):
        return {}
    try:
        res = await coro_fn()
    except Exception:
        log.exception("radar: %s failed", name)
        res = {"error": True}
    await store.note_run(db, name, res)
    return {name: res}


async def run_once(db, cfg: RadarConfig, llm) -> dict:
    out: dict = {}
    await examples.seed(db)
    await learn.load_active(db)
    drafting.set_rules(await learn.current_draft_rules(db))
    out["learned"] = await learn.sync(db)
    for name in cfg.sources:
        src = SOURCES.get(name)
        if src is None or not src.available():
            continue
        try:
            await src.seed(db)
            out.update(await src.collect(db, cfg))
        except Exception:
            log.exception("radar: source %s failed", name)
    out.update(await pipeline.process(db, llm, cfg, own=OWN_NAMES))
    out["redrafted"] = await pipeline.redraft(db, cfg, llm)
    out["followup"] = await followup.step(db, llm)
    if cfg.discovery_enabled:
        out.update(await _job(db, "discovery", 24, lambda: discovery.run(db, llm, cfg.discovery_steps)))
    out.update(await _job(db, "refit", 24 * 7, lambda: learn.refit(db)))
    out.update(await _job(db, "draft_rules", 24 * 7, lambda: learn.draft_rules(db, llm)))
    out.update(await _job(db, "themes", 24 * 7, lambda: themes.build(db, llm)))
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
                        counts = await run_once(db, cfg, default_llm())
                        log.info("radar: cycle done %s", counts)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("radar: cycle failed")
        await asyncio.sleep(cfg.interval_s)
