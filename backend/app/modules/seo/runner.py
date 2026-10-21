"""The seo worker loop (app/worker.py): every INTERVAL_S, the Search Console read (areastats.searchconsole), IndexNow
(indexnow.py), the daily index coverage read (coverage.py), then the rank loop (docs/plan/rank-loop.md): daily target searches
and titles (targets.py), the daily page doctor (doctor.py), the weekly search gaps (gaps.py) and the weekly
area list pages that grow from searches (grow.py, docs/plan/area-intent-pages.md). Each step does nothing while
its own setting is unset or nothing is due, and one failing never stops the others.

The read comes FIRST and is ours to make, not the enrichment loop's (docs/plan/seo-review.md D5): targets and the doctor
measure pages on those numbers, so with PROJECT_ENRICH_ENABLED off this loop would otherwise treat 15 pages a day against
yesterday's readings. searchconsole.refresh keeps its own daily mark, so the enrichment loop calling it costs one read."""
import asyncio
import logging
from datetime import datetime, timezone

from app.modules.areastats import searchconsole
from app.modules.newsroom.store import Store
from app.platform import trace

from . import coverage, doctor, gaps, grow, indexnow, scoreboard, targets

log = logging.getLogger(__name__)

INTERVAL_S = 1800


def enabled() -> bool:
    return indexnow.key() is not None or searchconsole.key() is not None


async def round_once(store: Store, now: datetime) -> dict:
    out = {}
    steps = (("gsc", searchconsole.refresh), ("indexnow", indexnow.run_once), ("coverage", coverage.run_once),
             ("targets", targets.run_once), ("doctor", doctor.run_once), ("gaps", gaps.run_once),
             ("grow", grow.run_once), ("scoreboard", scoreboard.run_once))
    for name, step in steps:
        try:
            res = await step(store, now)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.exception("seo: %s failed", name)
            res = {"error": type(e).__name__}
        # one line per step every round, so a quiet loop is visibly alive: skipped = off, or nothing due this round
        if not res:
            trace.event(log, "seo", "site", name, trace.SKIPPED, reason="off or nothing due")
        elif "error" in res:
            trace.event(log, "seo", "site", name, trace.FAILED, reason=res["error"])
        else:
            trace.event(log, "seo", "site", name, trace.OK, **{k: v for k, v in res.items() if isinstance(v, (int, float, str))})
        if res:
            out[name] = res
    return out


async def loop() -> None:
    from app.core.database import get_database
    from app.platform.heartbeats import heartbeat

    log.info("seo: loop started")
    while True:
        try:
            async with heartbeat("seo", get_database, on=enabled()) as hb:
                if enabled():
                    out = await round_once(Store(get_database()), datetime.now(timezone.utc))
                    if out:
                        log.info("seo: %s", out)
                    errors = [k for k, v in out.items() if "error" in v]
                    if errors:
                        hb.failed(", ".join(errors) + " failed")
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("seo: round failed")
        await asyncio.sleep(INTERVAL_S)
