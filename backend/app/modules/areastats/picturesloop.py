"""The `area_pictures` background loop (docs/plan/area-pictures.md step 3, `.claude/skills/add-background-loop`): keeps every
area's "then and now" Sentinel-2 pair current by itself, judged by Gemini vision, the owner approving only the first pair.

Off by default (`AREA_FROM_ABOVE`), and off regardless when the Copernicus client id or secret is not set (app.core.config
`settings`, not read here directly: `enabled()` is the one place that checks both). A cycle costs one Copernicus token call
plus, per area actually due, a catalogue search and up to `pictures.TRIES` Process API calls; the Gemini judge is called only
for a pass that already passed the code checks, so a quiet year (nothing due) touches no network at all.

Runs in the `newsroom` role (app/worker.py): that role already carries the other once-a-day areastats work (searchconsole,
hot, project_enrich's own daily passes); `media`'s role table is not run anywhere today (production's media container runs
`--role dispatch`, docs/RENDERING.md), so a loop placed there would never fire on the live server.
"""
import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core import areas
from app.core.config import settings

from . import budget
from .pictures import (EARLIEST_YEAR, AreaPictures, Failed, box_for, capture_year, needed_years, token)

log = logging.getLogger(__name__)

POLL_SECONDS = 24 * 3600
PER_RUN = 3   # areas attempted per cycle: gentle on Copernicus and the day's Gemini budget


def enabled() -> bool:
    import os
    on = (os.environ.get("AREA_FROM_ABOVE") or "").strip().lower() in ("1", "true", "yes", "on")
    return on and bool(settings.copernicus_client_id) and bool(settings.copernicus_client_secret)


async def due_areas(svc: AreaPictures, today: date) -> List[Tuple[areas.Area, List[int], bool]]:
    """Every area that still needs a picture, with the years it needs and whether this is its first ever (so a failed
    earliest attempt may fall back one year; see `capture_one`)."""
    out = []
    for a in areas.AREAS:
        kept = await svc.kept_years(a.key)
        want = needed_years(kept, today)
        if want:
            out.append((a, want, not kept))
    return out


async def capture_one(svc: AreaPictures, client: httpx.Client, auth: str, area: areas.Area, year: int,
                      reader: Optional[Any], earliest: bool) -> Optional[dict]:
    """One wanted year for one area: `capture_year`, then (only for the series' earliest, never the latest) one adjacent
    year if the first failed entirely. Stores and returns the kept document, or None when nothing could be kept."""
    box = box_for(area.key)
    ask = reader.ask(budget.PLAIN, "area_picture") if reader is not None else None
    got = await capture_year(client, auth, box, area, year, ask)
    actual_year = year
    if got is None and earliest and year == EARLIEST_YEAR:
        got = await capture_year(client, auth, box, area, year + 1, ask)
        actual_year = year + 1
    if got is None:
        return None
    img, meta, judged = got
    return await svc.add(area, actual_year, img, meta["captured_on"], meta["cloud_pct"], judged, box)


async def cycle(db, now: datetime, client: Optional[httpx.Client] = None, reader: Optional[Any] = None,
                per_run: int = PER_RUN) -> Dict[str, Any]:
    """One pass. Does nothing, and touches no network, when no area needs a picture today."""
    svc = AreaPictures(db, now=lambda: now)
    today = now.date() if hasattr(now, "date") else now
    due = await due_areas(svc, today)
    if not due:
        return {"checked": len(areas.AREAS), "kept": 0}
    own_client = client is None
    client = client or httpx.Client()
    kept = 0
    try:
        try:
            auth = await asyncio.to_thread(token, client, settings.copernicus_client_id, settings.copernicus_client_secret)
        except Failed as e:
            log.warning("area pictures: %s", e)
            return {"checked": len(areas.AREAS), "kept": 0, "error": str(e)}
        if reader is None:
            reader = await budget.reader(db, now)
        for area, want, first_ever in due[:per_run]:
            for year in want:
                try:
                    if await capture_one(svc, client, auth, area, year, reader, first_ever):
                        kept += 1
                except Exception:
                    log.exception("area pictures: %s %s failed", area.key, year)
    finally:
        if own_client:
            client.close()
    return {"checked": len(areas.AREAS), "kept": kept}


async def loop() -> None:
    from app.core.database import get_database
    from app.platform.heartbeats import heartbeat
    log.info("area pictures: loop started")
    while True:
        on = enabled()
        try:
            async with heartbeat("area_pictures", get_database, on=on):
                if on:
                    out = await cycle(get_database(), datetime.now(timezone.utc))
                    if out.get("kept") or out.get("error"):
                        log.info("area pictures: %s", out)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("area pictures: cycle failed")
        await asyncio.sleep(POLL_SECONDS)
