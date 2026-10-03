"""One runner per background loop, however many processes start it.

Every background loop (comments, newsroom, calendar, listing reels) is started through `run_as_leader(name, loop, get_db)`.
The caller that holds the lease document `worker_leases/<name>` runs the loop; every other caller waits as a follower.

- The leader renews the lease every RENEW_S seconds; the lease is valid for TTL_S seconds after each renewal.
- A leader that cannot renew for STEP_DOWN_S (shorter than TTL_S) cancels its loop before anyone else may take over,
  and a leader that finds the lease held by someone else cancels at once, so two copies never run at the same time.
- A follower takes over once the lease has expired (the leader crashed, hung or lost the database).
- On a clean shutdown the leader releases the lease, so the next process starts the loop without waiting for expiry.

Each call gets its own holder id, so two callers in one process contend like two processes do.
Times are compared on the app clock; all processes run on the same host, so clock skew is not a concern today.
"""
import asyncio
import logging
import os
import socket
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Optional

from pymongo.errors import DuplicateKeyError

log = logging.getLogger(__name__)

COLLECTION = "worker_leases"
TTL_S = 90.0
RENEW_S = 20.0
STEP_DOWN_S = 60.0  # must stay below TTL_S: the leader stops before its lease can expire


def new_holder() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def acquire(db, name: str, holder: str, now: datetime, ttl_s: float = TTL_S) -> bool:
    """Take or renew the lease. True when `holder` holds it until now + ttl_s; False when someone else holds it."""
    col = db.get_collection(COLLECTION)
    fields = {"holder": holder, "expires_at": now + timedelta(seconds=ttl_s), "renewed_at": now}
    # one atomic update: matches only if we already hold the lease or it has expired
    res = await col.update_one({"_id": name, "$or": [{"holder": holder}, {"expires_at": {"$lt": now}}]}, {"$set": fields})
    if res.matched_count:
        return True
    try:
        await col.insert_one({"_id": name, **fields})
        return True
    except DuplicateKeyError:  # the lease exists and is held by someone else
        return False


async def release(db, name: str, holder: str, now: datetime) -> None:
    """Give the lease up (only if we hold it), so a follower can take over at once."""
    await db.get_collection(COLLECTION).update_one({"_id": name, "holder": holder}, {"$set": {"expires_at": now}})


async def _stop(task: Optional[asyncio.Task]) -> None:
    if task and not task.done():
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def run_as_leader(name: str, start: Callable[[], Awaitable[Any]], get_db: Callable[[], Any], *,
                        holder: Optional[str] = None, ttl_s: float = TTL_S, renew_s: float = RENEW_S,
                        step_down_s: float = STEP_DOWN_S, clock: Callable[[], datetime] = _now) -> None:
    """Run `start()` only while this caller holds the lease `name`. Runs until cancelled."""
    holder = holder or new_holder()
    task: Optional[asyncio.Task] = None
    last_ok: Optional[datetime] = None
    try:
        while True:
            try:
                held: Optional[bool] = await acquire(get_db(), name, holder, clock(), ttl_s)
            except asyncio.CancelledError:
                raise
            except Exception:  # database unreachable: keep running only while the lease is surely still ours
                log.exception("%s: could not renew the runner lease", name)
                held = None
            now = clock()
            if held:
                last_ok = now
                if task is None or task.done():
                    if task is not None and not task.cancelled() and task.exception():
                        log.error("%s: loop stopped with an error, restarting", name, exc_info=task.exception())
                    log.info("%s: this process runs the loop (%s)", name, holder)
                    task = asyncio.create_task(start())
            elif task is not None and (held is False or last_ok is None
                                       or (now - last_ok).total_seconds() >= step_down_s):
                log.warning("%s: lease %s, stopping the loop in this process",
                            name, "held elsewhere" if held is False else "not renewed in time")
                await _stop(task)
                task = None
            await asyncio.sleep(renew_s)
    finally:
        was_leader = task is not None
        await _stop(task)
        if was_leader:
            try:
                await release(get_db(), name, holder, clock())
            except Exception:
                log.warning("%s: could not release the runner lease; it expires on its own", name)
