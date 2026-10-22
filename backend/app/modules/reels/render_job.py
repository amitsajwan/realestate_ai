"""Reels drawn on demand by a Cloud Run Job instead of on the main VM (owner, 2026-10-16: main VM back to e2-medium, the
drawing ~4 min a reel elsewhere; docs/MODERNIZATION.md phase 1b).

The media work is already three Mongo queues with atomic claims: marketing runs (posts, ad reels, reels remakes, voice-overs,
boost pairs: propertyfacts.jobs), listing walkthrough reels (`reel_jobs`: reels.listing_reel) and the calendar's reel
pre-renders (calendar.runner). So the renderer is the same backend image doing the same work:

  drain      `python -m app.worker --drain` (the Cloud Run Job "renderer"): clean up stale items once, then take work from the
             three queues until none has any for IDLE_CHECKS rounds in a row, then exit. It reaches Mongo on the VM's private
             IP and the uploads over NFS from the VM (mounted at /app/uploads, as in the containers), so no file path changes.
  dispatch   the "render_dispatch" loop on the VM (worker role `dispatch`, in place of `media`): every DISPATCH_EVERY_S it asks
             `queued`; when something waits and no renderer is running, it starts the job (Cloud Run Admin API, with the VM's
             own service account). A job cut short (its 60-minute limit) leaves the rest queued and the next round starts
             another.

Rollback: MEDIA_ROLE=media in the VM's .env and `docker compose up -d media`: the VM draws again, as before.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

import httpx

log = logging.getLogger(__name__)

JOB = os.environ.get("RENDER_JOB", "projects/trader-502012/locations/asia-south1/jobs/renderer")
RUN_API = "https://run.googleapis.com/v2"
METADATA_TOKEN = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
DISPATCH_EVERY_S = 20.0
IDLE_CHECKS, IDLE_WAIT_S = 3, 20.0   # drain: a minute with nothing queued, then exit
CALENDAR_LEAD = timedelta(hours=2)   # calendar.runner.PRERENDER_LEAD


async def queued(db, now: Optional[datetime] = None) -> Dict[str, int]:
    """What waits for a renderer, per queue (claimable work only: an item in progress is the running renderer's)."""
    from app.modules.calendar.store import Store
    runs = db.get_collection("marketing_runs")
    out = {
        "marketing_runs": await runs.count_documents({"status": "queued"}),
        "reels_remakes": await runs.count_documents({"reels_queued": True}),
        "voice_overs": await runs.count_documents({"voices_queued": True}),
        "boost_pairs": await runs.count_documents({"boost_queued": True}),
        "walkthrough_reels": await db.get_collection("reel_jobs").count_documents({"status": "queued"}),
        "calendar_reels": len(await Store(db).reels_to_render(now or datetime.now(timezone.utc), CALENDAR_LEAD)),
    }
    return {k: v for k, v in out.items() if v}


async def drain(db, make_runs: Callable[[], Any]) -> int:
    """The Cloud Run Job's whole life: clean up stale items once, then work through the three queues until they stay empty
    for IDLE_CHECKS rounds. Returns how many items it took. `make_runs`: the marketing-run queue (propertyfacts.jobs
    default_runs, passed in by app.worker: the app layer's queue is not imported from here)."""
    from app.modules.calendar.runner import prerender_reels
    from app.modules.calendar.store import Store
    from app.modules.reels.listing_reel import default_jobs
    runs, reels = make_runs(), default_jobs()
    for cleanup in (runs.fail_stale, reels.fail_stale):   # nothing else renders: an item left "making" by a cut job is stale
        try:
            await cleanup()
        except Exception:
            log.exception("renderer: stale clean-up failed")
    done, idle = 0, 0
    while idle < IDLE_CHECKS:
        took = False
        for step in (runs.run_once, reels.run_once):
            try:
                took = bool(await step()) or took
            except Exception:
                log.exception("renderer: %s failed", getattr(step, "__qualname__", step))
        try:
            took = (await prerender_reels(Store(db), datetime.now(timezone.utc)) or 0) > 0 or took
        except Exception:
            log.exception("renderer: calendar pre-render failed")
        if took:
            done, idle = done + 1, 0
        else:
            idle += 1
            await asyncio.sleep(IDLE_WAIT_S)
    log.info("renderer: queues empty after %s item(s); exiting", done)
    return done


# ---- the dispatcher on the VM --------------------------------------------------------------------------------------------
async def _token(client: httpx.AsyncClient) -> str:
    r = await client.get(METADATA_TOKEN, headers={"Metadata-Flavor": "Google"}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


async def running(client: httpx.AsyncClient, token: str) -> bool:
    """A renderer execution is still running (the job's latest execution has no completion time)."""
    r = await client.get(f"{RUN_API}/{JOB}", headers={"Authorization": f"Bearer {token}"}, timeout=20)
    r.raise_for_status()
    latest = r.json().get("latestCreatedExecution") or {}
    return bool(latest) and not latest.get("completionTime")


async def start(client: httpx.AsyncClient, token: str) -> str:
    r = await client.post(f"{RUN_API}/{JOB}:run", headers={"Authorization": f"Bearer {token}"}, json={}, timeout=30)
    r.raise_for_status()
    return str((r.json().get("metadata") or {}).get("name") or "")


async def dispatch_once(db, client: httpx.AsyncClient) -> Optional[str]:
    """Start the renderer when work waits and none runs; returns the execution's name when it started one."""
    waiting = await queued(db)
    if not waiting:
        return None
    token = await _token(client)
    if await running(client, token):
        return None
    name = await start(client, token)
    log.info("renderer started for %s: %s", waiting, name)
    return name


async def dispatch_loop(get_db: Optional[Callable[[], Any]] = None) -> None:
    """The VM's `render_dispatch` loop (worker role `dispatch`)."""
    from app.core.database import get_database
    from app.platform.heartbeats import heartbeat
    get_db = get_db or get_database
    async with httpx.AsyncClient() as client:
        while True:
            try:
                async with heartbeat("render_dispatch", get_db):
                    await dispatch_once(get_db(), client)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("render dispatch: round failed")
            await asyncio.sleep(DISPATCH_EVERY_S)
