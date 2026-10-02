"""Background loop for the newsroom, like engage/runner.py. Started by the integrator from the app lifespan; idle unless NEWSROOM_ENABLED."""
import asyncio
import logging
from datetime import datetime, timezone

from app.core.database import get_database
from app.modules.admin.controls import is_paused

from . import adapters, digest
from .config import load
from .pipeline import default_stages, run_once
from .store import Store

log = logging.getLogger(__name__)
MAX_PASSES = 15


def load_sources(names) -> list:
    """Instances for the configured source names (see sources.build_sources)."""
    from .sources import build_sources
    return build_sources(list(names))


async def _weekly_digest(store: Store, stages: dict, now: datetime, counts: dict) -> None:
    """Sunday from 18:00 IST: build the week's digest for the owner to approve (once per week, only with at least two stories)."""
    if not digest.is_due(now):
        return
    try:
        built = await digest.build(store, now, stages.get("check"), stages.get("cards"))
        counts["digest"] = 1 if built else 0
    except Exception:
        log.exception("newsroom: digest failed")


async def cycle(store: Store, cfg) -> dict:
    """One guarded cycle; records last_run_at / last_error. Never raises except cancellation."""
    now = datetime.now(timezone.utc)
    try:
        stages = default_stages()
        stages["get"] = adapters.make_fetcher()
        sources, publisher, llm = load_sources(cfg.sources), adapters.SocialPublisher(checker=stages["check"]), adapters.default_llm()
        counts = await run_once(store, sources, stages, publisher, llm, now, cfg)
        for _ in range(MAX_PASSES - 1):  # each pass handles a small batch per stage: keep going while there is work
            if not (counts.get("filter") or counts.get("extract") or counts.get("draft") or counts.get("check")):
                break
            more = await run_once(store, [], stages, publisher, llm, datetime.now(timezone.utc), cfg)
            counts = {k: counts.get(k, 0) + more.get(k, 0) for k in set(counts) | set(more)}
        await _weekly_digest(store, stages, now, counts)
        await store.set_run(last_run_at=now, last_error=None, last_counts=counts)
        return counts
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.exception("newsroom: cycle failed")
        try:
            from app.modules.social.publisher import sanitize
            await store.set_run(last_run_at=now, last_error=sanitize(f"{type(e).__name__}: {e}"))
        except Exception:
            pass
        return {}


async def loop() -> None:
    log.info("newsroom: loop started")
    while True:
        cfg = load()
        try:
            if cfg.enabled and await is_paused(get_database(), "news_paused"):
                log.info("newsroom: paused by owner, cycle skipped")
            elif cfg.enabled:
                counts = await cycle(Store(get_database()), cfg)
                if counts:
                    log.info("newsroom: cycle done %s", counts)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("newsroom: loop error")
        await asyncio.sleep(cfg.interval_s)
