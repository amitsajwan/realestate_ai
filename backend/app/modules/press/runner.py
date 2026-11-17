"""The monthly press loop: once in the first week of the month, if `PRESS_AGENT` is on, builds the story and drafts
this month's pitches, through a lease and heartbeat like every background loop (`add-background-loop` skill).
CLAUDE.md rule 6: no AI agent ever publishes or sends; this only prepares drafts and tells the owner they are ready."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

from .config import load
from .service import monthly_run
from .store import Store

log = logging.getLogger(__name__)

INTERVAL_S = 24 * 3600         # checked daily; the month's real work runs once, in its first FIRST_WEEK_DAYS days
FIRST_WEEK_DAYS = 7

TellOwner = Callable[[dict], Awaitable[None]]
_tell_owner: Optional[TellOwner] = None


def configure(tell_owner: TellOwner) -> None:
    """`tell_owner(result)`: a Studio notification that this month's drafts are ready (press sits below the owner's
    console and the notifications module; wiring.py passes this in, as it does for every such alert)."""
    global _tell_owner
    _tell_owner = tell_owner


def enabled() -> bool:
    return load().enabled


async def cycle(db, now: Optional[datetime] = None) -> Optional[dict]:
    """One check: build this month's story and pitches once, in the month's first week, never twice a month. `now`
    fixes the clock for tests. None when there is nothing to do (outside the window, or already done)."""
    now = now or datetime.now(timezone.utc)
    if now.day > FIRST_WEEK_DAYS:
        return None
    month = now.strftime("%Y-%m")
    if await Store(db).story(month) is not None:
        return None
    result = await monthly_run(db, now)
    if result.get("pitches") and _tell_owner is not None:
        try:
            await _tell_owner(result)
        except Exception:
            log.exception("press: could not tell the owner the drafts are ready")
    return result


async def loop() -> None:
    from app.core.database import get_database
    from app.platform.heartbeats import heartbeat

    log.info("press: loop started")
    while True:
        try:
            async with heartbeat("press", get_database, on=enabled()):
                if enabled():
                    out = await cycle(get_database())
                    if out:
                        log.info("press: %s", out)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("press: monthly run failed")
        await asyncio.sleep(INTERVAL_S)
