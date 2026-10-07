"""Heartbeats for the background loops: one document per loop in `worker_heartbeats`.

Each runner wraps one cycle in `async with heartbeat(name, get_db, on=<loop enabled>):`; a loop switched off by config
records nothing (it does not touch the database at all) and is not checked. Entering records `last_start_at`; leaving records
`last_ok_at`, or `last_error_at` + `last_error` (sanitised, short) when the cycle raised or called `hb.failed(err)`.
Cancellation records nothing. Recording never raises and never blocks a loop for long: a database error is logged and dropped.

`stale(doc, interval_s, now)` says whether a loop has not started a cycle for more than twice its interval; the worker's
`--check` mode (app/worker.py) uses it for deploy/gcp/health_check.sh.
"""
import asyncio
import logging
import os
import socket
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from app.platform.meta_graph.publisher import sanitize

log = logging.getLogger(__name__)

COLLECTION = "worker_heartbeats"
WRITE_TIMEOUT_S = 5.0
MAX_ERROR = 300

_last_write: Dict[tuple, float] = {}  # (name, field) -> monotonic time of the last start/ok write (the `every_s` throttle)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Any) -> Optional[datetime]:
    if not isinstance(dt, datetime):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # Motor returns naive UTC datetimes


async def record(get_db: Callable[[], Any], name: str, fields: Dict[str, Any]) -> bool:
    """Upsert `fields` into the loop's heartbeat document. True when written; never raises (except cancellation)."""
    try:
        doc = {**fields, "host": f"{socket.gethostname()}:{os.getpid()}"}
        async with asyncio.timeout(WRITE_TIMEOUT_S):  # not wait_for: on 3.11 it can swallow a cancel that races the write
            await get_db().get_collection(COLLECTION).update_one({"_id": name}, {"$set": doc}, upsert=True)
        return True
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.warning("%s: could not record the heartbeat (%s)", name, type(e).__name__)
        return False


class heartbeat:
    """Async context manager around one loop cycle. `every_s` > 0 skips start/ok writes closer together than that
    (for loops that cycle every few seconds); errors are always written."""

    def __init__(self, name: str, get_db: Callable[[], Any], *, on: bool = True, every_s: float = 0.0,
                 clock: Callable[[], datetime] = _now, monotonic: Callable[[], float] = time.monotonic):
        self.name, self.get_db, self.on, self.every_s, self.clock = name, get_db, on, every_s, clock
        self.monotonic = monotonic
        self.error: Optional[str] = None

    def failed(self, err: Any) -> None:
        """Mark this cycle failed without raising (for cycles that handle their own errors)."""
        self.error = _short(err)

    async def _write(self, fields: Dict[str, Any], throttle: bool = True) -> None:
        if not self.on:
            return
        key = (self.name, next(iter(fields)))
        last = _last_write.get(key)
        if throttle and self.every_s > 0 and last is not None and self.monotonic() - last < self.every_s:
            return
        _last_write[key] = self.monotonic()  # also after a failed write, so a database outage is not logged every few seconds
        await record(self.get_db, self.name, fields)

    async def __aenter__(self) -> "heartbeat":
        await self._write({"last_start_at": self.clock()})
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None and issubclass(exc_type, asyncio.CancelledError):
            return False
        if exc is not None:
            self.error = _short(exc)
        if self.error:
            await self._write({"last_error_at": self.clock(), "last_error": self.error}, throttle=False)
        else:
            await self._write({"last_ok_at": self.clock()})
        return False  # never swallow the cycle's own exception


def _short(err: Any) -> str:
    text = f"{type(err).__name__}: {err}" if isinstance(err, BaseException) else str(err)
    return sanitize(text)[:MAX_ERROR]


async def read_all(db) -> Dict[str, dict]:
    """Every loop's heartbeat document by name."""
    docs = await db.get_collection(COLLECTION).find({}).to_list(100)
    return {d["_id"]: d for d in docs}


def age_s(doc: Optional[dict], now: datetime) -> Optional[float]:
    """Seconds since the loop last started (or finished) a cycle; None when it never has."""
    times = [t for t in (_aware((doc or {}).get(k)) for k in ("last_start_at", "last_ok_at", "last_error_at")) if t]
    return (now - max(times)).total_seconds() if times else None


def stale(doc: Optional[dict], interval_s: float, now: datetime) -> bool:
    """True when the loop has not shown a sign of life for more than twice its interval (or never has)."""
    age = age_s(doc, now)
    return age is None or age > 2 * interval_s
