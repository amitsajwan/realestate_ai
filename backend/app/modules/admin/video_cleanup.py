"""Finished reel videos are deleted from the uploads volume MAX_AGE after they were drawn (owner, 2026-10-23).

Instagram and Facebook keep their own copy once a reel is posted, and the VM disk filled at ~150 MB a day with mp4s nobody
opened again. Only the drawn output in VIDEO_DIRS goes: `videos/` (the agents' own walkthrough uploads, the source of their
reels), `promo/` and `agentprojects/` (site assets) are never touched, and neither are covers or pictures.
A video that an open calendar row (planned, approved, scheduled) still points at is kept until that row posts, since the
publish step stages the stored file and would fail without it. A listing reel or marketing run left unposted for MAX_AGE
loses its video like any other: making it again is one click.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Set

from app.core.database import get_database
from app.modules.calendar.config import uploads_dir
from app.modules.calendar.store import OPEN, Store
from app.platform.heartbeats import heartbeat

log = logging.getLogger(__name__)

INTERVAL_S = 3600
MAX_AGE = timedelta(days=2)
VIDEO_DIRS = ("reels", "campaigns", "calendar/reels", "calendar/slidereels", "calendar/guides", "calendar/trend")


async def kept_videos(db) -> Set[str]:
    """Paths (relative to uploads) of the videos open calendar rows will still publish."""
    return {d["video"].lstrip("/") for d in await Store(db).all() if d.get("status") in OPEN and d.get("video")}


def old_videos(root: Path, now: datetime, keep: Iterable[str] = (), max_age: timedelta = MAX_AGE) -> list:
    """The mp4s under VIDEO_DIRS last written before now - max_age, minus `keep`."""
    keep, cutoff = set(keep), (now - max_age).timestamp()
    out = []
    for d in VIDEO_DIRS:
        for p in (root / d).rglob("*.mp4"):
            try:
                if p.is_file() and p.stat().st_mtime < cutoff and p.relative_to(root).as_posix() not in keep:
                    out.append(p)
            except OSError:
                continue  # vanished between the listing and the stat
    return out


async def cycle(db, now: datetime, root: Path) -> dict:
    keep = await kept_videos(db)
    removed, freed = 0, 0
    for p in await asyncio.to_thread(old_videos, root, now, keep):
        try:
            size = p.stat().st_size
            os.remove(p)
            removed, freed = removed + 1, freed + size
        except OSError as e:
            log.warning("video cleanup: could not delete %s: %s", p.name, type(e).__name__)
    if removed:
        log.info("video cleanup: deleted %d videos, %.0f MB", removed, freed / 1e6)
    return {"removed": removed, "freed_bytes": freed, "kept": len(keep)}


async def loop() -> None:
    while True:
        try:
            async with heartbeat("video_cleanup", get_database):
                await cycle(get_database(), datetime.utcnow(), uploads_dir())
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("video cleanup: cycle failed")
        await asyncio.sleep(INTERVAL_S)
