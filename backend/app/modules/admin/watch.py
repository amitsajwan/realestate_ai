"""The rows of Studio's Admin -> Health, gathered in one place, and the system watch that reads them.

The Health screen shows the rows; the watch (a loop in the conversations worker, so it does not stop with the newsroom worker
whose loops it watches) tells the owner when one goes wrong. One set of rows, so the screen and the alarm never disagree.
Serper sat at 0 credits on 2026-11-19 and the pages it feeds stopped growing while the Health row said so to nobody: the badge
had 54 unread notifications and phone alerts were off.

- Alarm: a BAD row, or a WARN row in ALARM_WARN, is told once (Studio badge and the owner's phones), again every REPEAT while it
  lasts, and "working again" when it clears.
- Daily report at DAILY_HOUR IST, problems or not: a missing morning report is itself the sign that something is down.
- `alive()` for the outside check (.github/workflows/watchdog.yml): not OK when the watch has stopped or a row is BAD, so a dead
  server or a dead watch still reaches the owner by GitHub's email.

State: collection `system_watch` (owned here): one document per row in alarm {_id: key, status, label, text, since, told_at},
`_daily` {day} and `_loops` {row}, the background loops row worked out by the watch (it alone is given the worker's intervals).
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, List, Optional

from app.core.database import get_database
from app.modules.areastats import owner as areastats_owner
from app.modules.areastats.enrich import load as enrich_cfg
from app.modules.engage.config import load as engage_cfg
from app.modules.notifications import notify
from app.platform import heartbeats
from app.platform.heartbeats import heartbeat

from . import health
from .service import AdminService

log = logging.getLogger(__name__)


async def health_rows(svc: AdminService, ai_ping: Callable = health.default_ai_ping, ctl: Optional[dict] = None) -> List[dict]:
    """Every Health row, as /admin/overview returns them."""
    from app.modules.calendar.config import load as load_calendar
    from app.modules.engage.config import load as load_engage
    from app.modules.newsroom.config import load as load_newsroom
    from app.platform.meta_graph.config import load as load_social
    from app.modules.whatsapp.config import load as load_wa
    from app.modules.whatsapp.dm_config import load as load_dm
    ctl = ctl if ctl is not None else await svc.controls()
    cal_run, news_run = await svc.run_status("calendar_status"), await svc.run_status("newsroom_status")
    rows = health.build_health(social=load_social(), wa=load_wa(), engage=load_engage(), calendar=load_calendar(), newsroom=load_newsroom(),
                               meta=await svc.meta_status(), cal_run=cal_run, news_run=news_run, controls=ctl,
                               ai=await health.ai_status(ai_ping), dm=load_dm())
    rows += await _seo_rows(svc)
    from app.modules.areastats.websearch import credits, provider
    rows.append(health.search_row(provider() is not None, await credits()))
    rows.append(await _press_row(svc))
    rows += await _watch_rows(svc.db, datetime.now(timezone.utc))
    return rows


async def _watch_rows(db, now: datetime) -> List[dict]:
    """Project reading, the background loops (as the watch last worked them out) and the watch itself."""
    rows = [health.reading_row(enrich_cfg().enabled, await areastats_owner.reading(db, now))]
    kept = await db.get_collection(COLLECTION).find_one({"_id": "_loops"}) or {}
    rows.append(kept.get("row"))
    beat = (await heartbeats.read_all(db)).get(NAME)
    rows.append(health.loop_row(NAME, "System watch", beat, float(INTERVAL_S), now, "",
                                "nobody is told when something stops"))
    return [r for r in rows if r]


async def _seo_rows(svc: AdminService) -> list:
    from app.modules.areastats.enrich import POLL_SECONDS as ENRICH_POLL_S
    from app.modules.areastats.enrich import load as enrich_cfg
    from app.modules.areastats.searchconsole import key as gsc_key
    from app.modules.seo import freshness, review
    from app.modules.seo.indexnow import key as indexnow_key
    from app.modules.seo.runner import INTERVAL_S as SEO_INTERVAL_S
    from app.modules.seo.runner import enabled as seo_on
    from app.platform import heartbeats
    names = ["indexnow", "gsc_coverage", "gsc_pages", freshness.MARK, review.MARK]
    marks = {d["_id"]: d for d in await svc.c("newsroom_status").find({"_id": {"$in": names}}).to_list(len(names))}
    beats, now = await heartbeats.read_all(svc.db), datetime.now(timezone.utc)
    from app.modules.areaphotos.config import load as photo_scout_cfg
    from app.modules.areaphotos.runner import INTERVAL_S as PHOTO_SCOUT_INTERVAL_S
    loops = [health.loop_row("seo", "SEO loop", beats.get("seo"), float(SEO_INTERVAL_S) if seo_on() else None, now, "",
                             "rankings, coverage and IndexNow are not being updated"),
             health.loop_row("enrich", "Project page refresh", beats.get("project_enrich"),
                             float(ENRICH_POLL_S) if enrich_cfg().enabled else None, now,
                             "Set PROJECT_ENRICH_ENABLED=true in the server settings",
                             "project pages are not re-read, so their dates and facts go old"),
             health.loop_row("photo_scout", "Photo scout", beats.get("area_photo_scout"),
                             float(PHOTO_SCOUT_INTERVAL_S) if photo_scout_cfg().enabled else None, now,
                             "Set AREA_PHOTO_SCOUT=true in the server settings",
                             "no new Commons photos are suggested for the area guides")]
    from app.modules.communities.discover import COLLECTION as COMMUNITIES
    from app.modules.communities.runner import enabled as articles_on
    hoods = await svc.c(COMMUNITIES).find({}).to_list(None)
    held = sorted((d for d in hoods if not d.get("published") and d.get("write_notes")), key=lambda d: d.get("written_at"), reverse=True)
    articles = {"found": len(hoods), "published": sum(1 for d in hoods if d.get("published")),
                "last_note": f"{held[0]['name']}: {held[0]['write_notes'][0]}" if held else None}
    from app.modules.areastats.pictures import AreaPictures
    from app.modules.areastats.picturesloop import enabled as pictures_on
    pictures_summary = await AreaPictures(svc.db).health_summary()
    return health.seo_rows(indexnow_on=indexnow_key() is not None, gsc_on=gsc_key() is not None, indexnow=marks.get("indexnow"),
                           coverage=marks.get("gsc_coverage"), pages=marks.get("gsc_pages"), articles_on=articles_on(),
                           articles=articles) + [r for r in loops if r] + [
        health.freshness_row(marks.get(freshness.MARK), freshness.WINDOW.days), health.page_check_row(marks.get(review.MARK), now),
        health.pictures_row(pictures_on(), pictures_summary)]


async def _press_row(svc: AdminService) -> dict:
    from app.modules.press.config import load as press_cfg
    from app.modules.press.runner import INTERVAL_S as PRESS_INTERVAL_S
    from app.modules.press.store import Store as PressStore
    from app.platform import heartbeats
    cfg, now = press_cfg(), datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")
    story = await PressStore(svc.db).story(month) if cfg.enabled else None
    beat = (await heartbeats.read_all(svc.db)).get("press") if cfg.enabled else None
    return health.press_row(cfg.enabled, story is not None, beat, PRESS_INTERVAL_S if cfg.enabled else None, now, month)


# ---- the system watch ---------------------------------------------------------------------------------------------------------
NAME = "system_watch"                 # loop, lease and heartbeat name
COLLECTION = "system_watch"
INTERVAL_S = 15 * 60
REPEAT = timedelta(hours=24)          # a problem that lasts is told again once a day, not every round
DAILY_HOUR = 9                        # IST
IST = timezone(timedelta(hours=5, minutes=30))
# warnings worth a phone alert: each turns into a stop within days (credits run out, reads keep coming back empty)
ALARM_WARN = frozenset({"google_search", "reading"})
SCREEN = {"screen": "/studio/admin"}

Tell = Callable[[str, str], Awaitable[None]]


def alarms(rows: List[dict]) -> Dict[str, dict]:
    return {r["key"]: r for r in rows
            if r.get("status") == health.BAD or (r.get("status") == health.WARN and r.get("key") in ALARM_WARN)}


def _said(r: dict) -> str:
    return f"{r['label']}: {r['text']}" + (f". Fix: {r['fix']}" if r.get("fix") else "")


def daily_report(rows: List[dict]) -> str:
    """One line for the morning: what needs the owner first, then the reading and search numbers."""
    need = list(alarms(rows).values())
    by_key = {r["key"]: r for r in rows}
    facts = [f"{by_key[k]['label']}: {by_key[k]['text']}" for k in ("reading", "google_search") if k in by_key]
    head = (f"{len(need)} need you: " + "; ".join(r["label"] for r in need)) if need else f"All {len(rows)} checks fine"
    return ". ".join([head] + facts)


async def watch_once(db, now: datetime, rows: List[dict], tell: Tell) -> dict:
    """Tell what went wrong, what lasts (once per REPEAT) and what was fixed; the daily report once a day after DAILY_HOUR IST."""
    coll = db.get_collection(COLLECTION)
    known = {d["_id"]: d for d in await coll.find({}).to_list(200)}
    current, told = alarms(rows), []
    for key, r in current.items():
        k = known.get(key)
        at = heartbeats._aware((k or {}).get("told_at"))
        if not k or k.get("status") != r["status"] or not at or now - at >= REPEAT:
            await tell("system_alert", _said(r))
            told.append(key)
            fields = {"status": r["status"], "label": r["label"], "text": r["text"], "told_at": now,
                      "since": (k or {}).get("since") or now}
        else:
            fields = {"text": r["text"]}
        await coll.update_one({"_id": key}, {"$set": fields}, upsert=True)
    for key, k in known.items():
        if key.startswith("_") or key in current:
            continue
        await tell("system_alert", f"Fixed: {k.get('label') or key} is working again")
        await coll.delete_one({"_id": key})
        told.append(key)
    day, daily = now.astimezone(IST), known.get("_daily") or {}
    if day.hour >= DAILY_HOUR and daily.get("day") != day.date().isoformat():
        await tell("system_daily", daily_report(rows))
        await coll.update_one({"_id": "_daily"}, {"$set": {"day": day.date().isoformat(), "at": now}}, upsert=True)
        told.append("_daily")
    return {"alarms": sorted(current), "told": told}


async def alive(db, now: datetime) -> dict:
    """For the outside check: OK while the watch runs and nothing is BAD. Names the rows, nothing more (it is a public answer)."""
    age = heartbeats.age_s((await heartbeats.read_all(db)).get(NAME), now)
    if age is None or age > 3 * INTERVAL_S:
        return {"ok": False, "failing": [NAME]}
    bad = [d["_id"] for d in await db.get_collection(COLLECTION).find({"status": health.BAD}).to_list(200)]
    return {"ok": not bad, "failing": sorted(bad)}


async def _tell_owner(db, kind: str, summary: str) -> None:
    owner = engage_cfg().owner_agent_id
    if not owner:
        log.warning("system watch: no ENGAGE_OWNER_AGENT_ID, nobody to tell: %s", summary)
        return
    await notify(db, owner, kind, summary, SCREEN)


async def cycle(db, now: datetime, intervals: Dict[str, Optional[float]], tell: Optional[Tell] = None,
                rows_of: Optional[Callable[[], Awaitable[List[dict]]]] = None) -> dict:
    """One round: work out the loops row (stored for the Health screen), read every row, tell what changed."""
    loops = health.loops_row(await heartbeats.read_all(db), intervals, now)
    await db.get_collection(COLLECTION).update_one({"_id": "_loops"}, {"$set": {"row": loops, "at": now}}, upsert=True)
    rows = await (rows_of() if rows_of else health_rows(AdminService(db)))

    async def to_owner(kind: str, summary: str) -> None:
        await _tell_owner(db, kind, summary)
    return await watch_once(db, now, rows, tell or to_owner)


def loop_with(intervals: Callable[[], Dict[str, Optional[float]]]) -> Callable[[], Awaitable[None]]:
    """The watch loop, given the worker's `expected_intervals` (app.worker passes it: no module imports the worker)."""
    async def loop() -> None:
        while True:
            try:
                async with heartbeat(NAME, get_database):
                    out = await cycle(get_database(), datetime.now(timezone.utc), intervals())
                    if out["told"]:
                        log.info("system watch: told %s; in alarm %s", out["told"], out["alarms"])
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("system watch: cycle failed")
            await asyncio.sleep(INTERVAL_S)
    return loop
