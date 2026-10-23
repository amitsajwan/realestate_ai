"""The worker process: runs the background loops outside the API (docs/ARCHITECTURE.md §1 and §6).

    python -m app.worker                       run every loop until SIGTERM/SIGINT
    python -m app.worker --role conversations  run one role's loops; --loops accepts an explicit comma-separated subset
    python -m app.worker --check [selection]   print one line per selected loop; exit 1 when an enabled loop's heartbeat is
                                               older than twice its interval, 2 when the database cannot be read
                                               (deploy/gcp/health_check.sh calls this); then, for information only, whether
                                               the MahaRERA register and project enrichment are
                                   moving (WARN lines; the exit code is the heartbeats' alone)

Same image, same settings as the API. Each loop starts through its runner lease (app/platform/leases.py), so the worker and an
API process with RUN_BACKGROUND_LOOPS=true never run the same loop twice. On shutdown the loops are cancelled, which releases
their leases, before the database closes. Production refuses to start without its database, like the API.
"""
import argparse
import asyncio
import signal
import sys
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.database import close_database, get_database, init_database
from app.core.logging_config import get_logger, setup_logging
from app.platform import heartbeats
from app.platform.leases import run_as_leader

LoopTable = Dict[str, Callable[[], Awaitable[Any]]]
ALL_LOOP_NAMES = (
    "engage", "newsroom", "calendar", "calendar_reels", "listing_reels", "marketing_runs", "project_enrich", "insights",
    "answer_gaps", "inbound_messages", "token_cleanup", "radar", "seo", "communities", "knowledge_index", "lead_followups",
    "video_cleanup",
)   # render_dispatch is not among them: only the `dispatch` role starts it (it calls Cloud Run; development has none)
ROLE_LOOPS = {
    "conversations": ("engage", "answer_gaps", "inbound_messages", "lead_followups"),
    "newsroom": ("newsroom", "seo", "communities", "project_enrich", "radar", "insights", "calendar", "token_cleanup",
                 "knowledge_index", "video_cleanup"),
    "media": ("calendar_reels", "listing_reels", "marketing_runs"),
    # on the VM in place of media once reels are drawn by the Cloud Run Job (reels.render_job): it only starts that job
    "dispatch": ("render_dispatch",),
}


def loops() -> LoopTable:
    """Lease name -> loop. The names are also the heartbeat names."""
    from app.modules.admin.video_cleanup import loop as video_cleanup_loop
    from app.modules.areastats.enrich import loop as enrich_loop
    from app.modules.calendar.runner import loop as calendar_loop
    from app.modules.calendar.runner import render_loop as calendar_reels_loop
    from app.modules.engage.runner import loop as engage_loop
    from app.modules.inbox.followups import loop as lead_followups_loop
    from app.modules.insights.collector import loop as insights_loop
    from app.modules.knowledge.gaps import loop as gaps_loop
    from app.modules.knowledge.index import loop as knowledge_index_loop
    from app.modules.newsroom.runner import loop as newsroom_loop
    from app.modules.propertyfacts.jobs import loop as marketing_loop
    from app.modules.whatsapp.jobs import loop as inbound_loop
    from app.services.token_cleanup_service import loop as token_cleanup_loop
    from app.modules.radar import loop as radar_loop
    from app.modules.reels.listing_reel import loop as reels_loop
    from app.modules.communities.runner import loop as communities_loop
    from app.modules.seo.runner import loop as seo_loop
    from app.modules.reels.render_job import dispatch_loop
    return {"engage": engage_loop, "newsroom": newsroom_loop, "calendar": calendar_loop,
            "calendar_reels": calendar_reels_loop, "listing_reels": reels_loop,
            "marketing_runs": marketing_loop, "project_enrich": enrich_loop, "insights": insights_loop,
            "answer_gaps": gaps_loop, "inbound_messages": inbound_loop, "token_cleanup": token_cleanup_loop,
            "radar": radar_loop, "seo": seo_loop,
            "communities": communities_loop, "knowledge_index": knowledge_index_loop, "render_dispatch": dispatch_loop,
            "lead_followups": lead_followups_loop, "video_cleanup": video_cleanup_loop}


def requested_loop_names(role: Optional[str] = None, value: Optional[str] = None) -> Tuple[str, ...]:
    if role:
        return ROLE_LOOPS[role]
    if value is None:
        return ALL_LOOP_NAMES
    names = tuple(dict.fromkeys(name.strip() for name in value.split(",") if name.strip()))
    unknown = sorted(set(names) - set(ALL_LOOP_NAMES))
    if not names:
        raise ValueError("--loops must name at least one loop")
    if unknown:
        raise ValueError(f"unknown loop(s): {', '.join(unknown)}")
    return names


def select_loops(table: LoopTable, names: Tuple[str, ...]) -> LoopTable:
    return {name: table[name] for name in names}


def start_loops(table: LoopTable, get_db: Callable[[], Any] = get_database) -> Dict[str, asyncio.Task]:
    return {name: asyncio.create_task(run_as_leader(name, loop, get_db), name=f"loop:{name}") for name, loop in table.items()}


async def stop_loops(tasks: Dict[str, asyncio.Task]) -> None:
    """Cancel every loop and wait, so each releases its runner lease while the database is still open."""
    for t in tasks.values():
        t.cancel()
    await asyncio.gather(*tasks.values(), return_exceptions=True)


async def run(stop: asyncio.Event, table: Optional[LoopTable] = None, get_db: Callable[[], Any] = get_database) -> None:
    setup_logging(environment=settings.environment)
    logger = get_logger("worker")
    from app.readiness import log_readiness
    await asyncio.to_thread(log_readiness, "worker")   # what the marketing pipeline can do here (voice, LLM, ffmpeg, social...)
    try:
        await init_database()
    except Exception as e:
        logger.error(f"worker: failed to connect to MongoDB: {e}")
        if settings.environment == "production":
            raise  # never run production loops without the database: crash so the container restarts once Mongo is up
        logger.warning("worker: continuing without a database (development only); the loops wait for their leases")
    from app.wiring import wire
    wire()  # the callbacks the loops use; the API applies them when its route list loads (app/api/v1/router.py)
    tasks = start_loops(loops() if table is None else table, get_db)
    logger.info("worker: started %s", ", ".join(tasks))
    try:
        await stop.wait()
    finally:
        logger.info("worker: stopping")
        await stop_loops(tasks)
        await close_database()
        logger.info("worker: stopped")


# ---- --check --------------------------------------------------------------------------------------------------------
def expected_intervals() -> Dict[str, Optional[float]]:
    """Loop name -> seconds between cycles, or None when the loop is switched off by config (it is not checked then)."""
    from app.modules.admin.video_cleanup import INTERVAL_S as VIDEO_CLEANUP_INTERVAL_S
    from app.modules.areastats.enrich import POLL_SECONDS as ENRICH_POLL_S
    from app.modules.areastats.enrich import load as enrich_cfg
    from app.modules.calendar.config import load as calendar_cfg
    from app.modules.calendar.runner import PRERENDER_INTERVAL_S
    from app.modules.engage.config import load as engage_cfg
    from app.modules.inbox.followups import INTERVAL_S as LEAD_FOLLOWUPS_INTERVAL_S
    from app.modules.insights.collector import INTERVAL_S as INSIGHTS_INTERVAL_S
    from app.modules.insights.collector import enabled as insights_on
    from app.modules.knowledge.gaps import INTERVAL_S as GAPS_INTERVAL_S
    from app.modules.knowledge.index import INTERVAL_S as KNOWLEDGE_INDEX_INTERVAL_S
    from app.modules.knowledge.vectors import enabled as knowledge_index_on
    from app.modules.whatsapp.jobs import HEARTBEAT_INTERVAL_S as INBOUND_INTERVAL_S
    from app.services.token_cleanup_service import INTERVAL_S as TOKEN_CLEANUP_INTERVAL_S
    from app.platform.meta_graph.config import load as social_cfg
    from app.modules.newsroom.config import load as newsroom_cfg
    from app.modules.propertyfacts.jobs import HEARTBEAT_INTERVAL_S as MARKETING_INTERVAL_S
    from app.modules.radar.config import load as radar_cfg
    from app.modules.reels.listing_reel import HEARTBEAT_INTERVAL_S
    from app.modules.communities.runner import POLL_SECONDS as COMMUNITIES_POLL_S
    from app.modules.communities.runner import enabled as communities_on
    from app.modules.seo.runner import INTERVAL_S as SEO_INTERVAL_S
    from app.modules.seo.runner import enabled as seo_on
    from app.modules.reels.render_job import DISPATCH_EVERY_S
    e, n, c = engage_cfg(), newsroom_cfg(), calendar_cfg()
    return {
        "engage": float(e.interval_s) if (e.enabled and e.page_id and e.page_token) else None,  # as engage/runner.py
        "newsroom": float(n.interval_s) if n.enabled else None,
        "calendar": float(c.interval_s) if c.enabled else None,
        "calendar_reels": float(PRERENDER_INTERVAL_S) if c.enabled else None,
        "listing_reels": HEARTBEAT_INTERVAL_S,  # always on (polls the reel queue)
        "marketing_runs": MARKETING_INTERVAL_S,  # always on (polls the Start marketing queue)
        "project_enrich": float(ENRICH_POLL_S) if enrich_cfg().enabled else None,  # PROJECT_ENRICH_ENABLED
        "insights": float(INSIGHTS_INTERVAL_S) if insights_on(social_cfg()) else None,  # real posts with a token, not dry run
        "answer_gaps": float(GAPS_INTERVAL_S),  # always on (reads stored replies, notifies agents)
        "inbound_messages": float(INBOUND_INTERVAL_S),  # always on (durable Meta webhook intake)
        "token_cleanup": float(TOKEN_CLEANUP_INTERVAL_S),
        "radar": float(radar_cfg().interval_s) if radar_cfg().enabled else None,  # RADAR_ENABLED
        "seo": float(SEO_INTERVAL_S) if seo_on() else None,  # INDEXNOW_KEY or GSC_SA_KEY_B64
        "communities": float(COMMUNITIES_POLL_S) if communities_on() else None,  # COMMUNITY_ARTICLES_ENABLED
        "knowledge_index": float(KNOWLEDGE_INDEX_INTERVAL_S) if knowledge_index_on() else None,  # QDRANT_URL + EMBEDDER_URL
        "render_dispatch": float(DISPATCH_EVERY_S),  # always on where the dispatch role runs
        "lead_followups": float(LEAD_FOLLOWUPS_INTERVAL_S),  # always on (waiting alerts); LEAD_AUTO_FOLLOWUP adds the auto template
        "video_cleanup": float(VIDEO_CLEANUP_INTERVAL_S),  # always on (drawn reels older than 2 days)
    }


def evaluate(docs: Dict[str, dict], intervals: Dict[str, Optional[float]], now: datetime) -> Tuple[List[str], List[str]]:
    """(report lines, names of stale loops)."""
    lines, bad = [], []
    for name, interval in intervals.items():
        if interval is None:
            lines.append(f"OFF   {name}")
            continue
        age = heartbeats.age_s(docs.get(name), now)
        shown = "never" if age is None else f"{int(age)}s ago"
        doc = docs.get(name) or {}
        err_at, ok_at = heartbeats._aware(doc.get("last_error_at")), heartbeats._aware(doc.get("last_ok_at"))
        # an error a later good cycle has passed is history, not news (radar showed Oct 9's error for days)
        err = doc.get("last_error") if not (err_at and ok_at and ok_at > err_at) else None
        if heartbeats.stale(docs.get(name), interval, now):
            bad.append(name)
            lines.append(f"STALE {name}: last heartbeat {shown} (limit {int(2 * interval)}s)")
        else:
            lines.append(f"OK    {name}: last heartbeat {shown}" + (f" (last error: {err})" if err else ""))
    return lines, bad


async def check(read: Optional[Callable[[], Awaitable[Dict[str, dict]]]] = None,
                intervals: Optional[Dict[str, Optional[float]]] = None, now: Optional[datetime] = None) -> int:
    """Print the heartbeat report; 0 = all fresh, 1 = stale, 2 = could not read the heartbeats."""
    try:
        docs = await asyncio.wait_for((read or _read_heartbeats)(), 20)
    except Exception as e:
        print(f"ERROR could not read the heartbeats: {type(e).__name__}")
        return 2
    lines, bad = evaluate(docs, expected_intervals() if intervals is None else intervals, now or datetime.now(timezone.utc))
    print("\n".join(lines))
    if read is None:   # the real database: is the MahaRERA register and enrichment work getting done? (information only)
        try:
            print("\n".join(await asyncio.wait_for(_register_status(now or datetime.now(timezone.utc)), 30)))
        except Exception as e:
            print(f"WARN could not read the project register: {type(e).__name__}")
    return 1 if bad else 0


async def _register_status(now: datetime) -> List[str]:
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.modules.areastats.refresh import status
    from app.modules.newsroom.store import Store
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=10000)
    try:
        return await status(Store(client[settings.database_name]), now)
    finally:
        client.close()


async def _read_heartbeats() -> Dict[str, dict]:
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=10000)
    try:
        return await heartbeats.read_all(client[settings.database_name])
    finally:
        client.close()


# ---- entry point ----------------------------------------------------------------------------------------------------
async def _main(names: Tuple[str, ...]) -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await run(stop, table=select_loops(loops(), names))


async def _drain() -> int:
    """`--drain`: the renderer's whole run (reels.render_job.drain), then exit 0; 2 without a database."""
    setup_logging(environment=settings.environment)
    try:
        await init_database()
    except Exception as e:
        get_logger("worker").error(f"renderer: failed to connect to MongoDB: {e}")
        return 2
    from app.wiring import wire
    wire()
    from app.modules.propertyfacts.jobs import default_runs
    from app.modules.reels.render_job import drain
    try:
        await drain(get_database(), default_runs)
    finally:
        await close_database()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.worker", description="Run the background loops.")
    parser.add_argument("--check", action="store_true", help="report loop heartbeats; exit 1 if one is stale")
    parser.add_argument("--drain", action="store_true",
                        help="the renderer (Cloud Run Job): do the queued media work until the queues stay empty, then exit")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--role", choices=sorted(ROLE_LOOPS), help="run or check the loops assigned to a worker role")
    selection.add_argument("--loops", help="comma-separated loop names to run or check")
    args = parser.parse_args(argv)
    try:
        names = requested_loop_names(args.role, args.loops)
    except ValueError as exc:
        parser.error(str(exc))
    if args.drain:
        return asyncio.run(_drain())
    if args.check:
        intervals = expected_intervals()
        return asyncio.run(check(intervals={name: intervals[name] for name in names}))
    asyncio.run(_main(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
