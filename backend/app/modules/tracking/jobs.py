"""The geoip loop: keeps DB-IP's free area/network files fresh in the uploads volume, which the API and every role share
(docs/plan/site-live-presence.md D6). Checks once a day, downloads only when a file is missing or over 35 days old. Off unless
GEOIP_REFRESH is on; production turns it on in deploy/gcp/docker-compose.yml."""
import asyncio
import logging
from datetime import datetime

from app.core.database import get_database
from app.platform import geoip
from app.platform.heartbeats import heartbeat

from . import config

log = logging.getLogger(__name__)

INTERVAL_S = 24 * 3600


def enabled() -> bool:
    return config.load().geoip_refresh


async def cycle(directory, now=datetime.utcnow, refresh=geoip.refresh) -> bool:
    """One check: download when stale. Returns True when it downloaded new files."""
    if not geoip.stale(directory, now):
        return False
    return await refresh(directory, now=now)


async def loop() -> None:
    while True:
        if enabled():
            try:
                async with heartbeat("geoip", get_database):
                    await cycle(config.load().geoip_dir)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("geoip: refresh failed")
        await asyncio.sleep(INTERVAL_S)
