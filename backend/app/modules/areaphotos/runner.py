"""The photo scout's loop (docs/plan/area-pictures.md step 4; .claude/skills/add-background-loop). Checks once a day which
areas are due their weekly round, within the day's Gemini-vision cap; off until AREA_PHOTO_SCOUT=true (config.py)."""
import asyncio
import logging
from datetime import datetime, timezone

from app.core.database import get_database
from app.platform.heartbeats import heartbeat

from . import config, scout

log = logging.getLogger(__name__)

INTERVAL_S = 24 * 3600


async def cycle(now=None) -> dict:
    return await scout.run_once(get_database(), now or datetime.now(timezone.utc))


async def loop() -> None:
    while True:
        cfg = config.load()
        if cfg.enabled:
            try:
                async with heartbeat("area_photo_scout", get_database):
                    await cycle()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("photo scout: a round failed")
        await asyncio.sleep(INTERVAL_S)
