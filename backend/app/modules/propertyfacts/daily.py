"""The day's best listings marketed without anyone pressing "Post & market" (owner, 2026-11-19: "we can have 5 listings a day, our
best ones"; of 55 live listings 3 had ever been marketed, each by hand).

Every INTERVAL_S, with LISTING_DAILY_PICKS > 0:
  1. Follow the open picks. A pick's run done -> its posts go to the calendar (MarketingRuns.to_calendar, from tomorrow) and every
     row it added is approved (calendar.store.approve, by "daily listing pick"), so they publish through the calendar's usual path
     (social.distribution, the pause switches). A failed or cancelled run ends the pick; a run that stops to ask the agent
     questions (understand.py) is cancelled after ASKING_GIVE_UP and the listing waits for its agent.
  2. Pick the next one, 09:00-18:00 IST, when no pick is running, fewer than LISTING_DAILY_PICKS were picked today, and the
     campaign rows already waiting on Instagram fill less than AHEAD of the calendar's slots (2 a day: schedule.POST_TIMES). The
     slots are the real pace: five listings a day would be ten posts a day on each channel, which the calendar spreads anyway.
     The best listing first (`rank`): a price, a MahaRERA number, the most pictures, selling points, newest. A listing marketed
     (or tried) in the last REMARKET_AFTER is not picked again.

Picks live in `listing_daily_picks` (this module's): _id "<IST day>:<listing id>", status running | calendared | failed | skipped.
"""
import asyncio
import logging
import os
from datetime import datetime, time, timedelta, timezone
from typing import Callable, Optional

from app.core.database import get_database
from app.modules.calendar.store import Store as CalendarStore, aware
from app.platform.heartbeats import heartbeat

from . import schedule
from .jobs import default_runs

log = logging.getLogger(__name__)

COLLECTION = "listing_daily_picks"
INTERVAL_S = 1800
IST = timezone(timedelta(hours=5, minutes=30))
PICK_HOURS = (time(9, 0), time(18, 0))
AHEAD = timedelta(days=3)
REMARKET_AFTER = timedelta(days=60)
ASKING_GIVE_UP = timedelta(hours=12)
APPROVER = "daily listing pick"
OPEN_RUNS = ("queued", "facts", "posts", "asking", "done")


def per_day() -> int:
    try:
        return max(0, min(5, int(os.getenv("LISTING_DAILY_PICKS", "0") or 0)))
    except ValueError:
        return 0


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _naive(d: datetime) -> datetime:
    """UTC without a zone, as Mongo hands dates back."""
    return d.astimezone(timezone.utc).replace(tzinfo=None) if d.tzinfo else d


def pictures(listing: dict) -> int:
    return sum(1 for m in listing.get("media") or [] if (m or {}).get("kind") == "image")


def rank(listing: dict) -> tuple:
    """Higher is better: a buyer can act on a price and a MahaRERA number; pictures make the post; selling points the copy."""
    made = listing.get("published_at") or listing.get("created_at")
    return (bool(listing.get("price_inr")), bool(listing.get("rera_no")), min(pictures(listing), 6),
            bool(listing.get("selling_points")), _aware(made).timestamp() if isinstance(made, datetime) else 0)


def eligible(listing: dict) -> bool:
    return (listing.get("status") == "live" and listing.get("visibility", "public") == "public" and pictures(listing) >= 2
            and not str(listing.get("title") or "").lower().startswith("sample"))


async def follow(db, runs, now: datetime) -> int:
    """Move the running picks on; returns how many reached the calendar."""
    picks, done = db.get_collection(COLLECTION), 0
    for p in await picks.find({"status": "running"}).to_list(50):
        try:
            run = await db.get_collection("marketing_runs").find_one({"_id": p["run_id"]}) or {}
            st = run.get("status")
            if st == "done":
                tomorrow = (_aware(now).astimezone(IST) + timedelta(days=1)).date()
                out = await runs.to_calendar(p["agent_id"], p["listing_id"], start=tomorrow)
                cal, approved = CalendarStore(db), 0
                for row in out.get("calendar") or []:
                    if row.get("row_id") and await cal.approve(row["row_id"], by=APPROVER):
                        approved += 1
                await picks.update_one({"_id": p["_id"]}, {"$set": {"status": "calendared", "rows": approved, "finished_at": now}})
                done += 1
            elif st in ("failed", "cancelled") or not run:
                await picks.update_one({"_id": p["_id"]}, {"$set": {"status": "failed", "reason": str(run.get("error") or st or "run gone")[:200],
                                                                    "finished_at": now}})
            elif st == "asking" and _naive(now) - _naive(p["created_at"]) >= ASKING_GIVE_UP:
                await db.get_collection("marketing_runs").update_one({"_id": run["_id"], "status": "asking"},
                                                                     {"$set": {"status": "cancelled", "finished_at": now}})
                await picks.update_one({"_id": p["_id"]}, {"$set": {"status": "skipped", "reason": "the run needs the agent's answers",
                                                                    "finished_at": now}})
        except Exception as e:   # one pick's trouble never stops the others
            log.warning("daily listing pick %s: %s", p["_id"], e)
            await picks.update_one({"_id": p["_id"]}, {"$set": {"status": "failed", "reason": str(e)[:200], "finished_at": now}})
    return done


async def waiting_rows(db, now: datetime) -> int:
    """Campaign rows still to go out on Instagram (read through the calendar's own store, which owns its dates)."""
    from_ = _aware(now)
    return sum(1 for d in await CalendarStore(db).all()
               if d.get("channel") == "instagram" and str(d.get("slug", "")).startswith("campaign-")
               and d.get("status") in ("planned", "approved", "scheduled") and aware(d["due_at"]) >= from_)


async def pick(db, runs, now: datetime, limit: int) -> Optional[str]:
    """Start the next best listing's run; returns its listing id, or None when it is not the time or nothing is due."""
    local = _aware(now).astimezone(IST)
    if limit <= 0 or not (PICK_HOURS[0] <= local.time() < PICK_HOURS[1]):
        return None
    picks = db.get_collection(COLLECTION)
    day = local.date().isoformat()
    if await picks.find_one({"status": "running"}) or await picks.count_documents({"day": day}) >= limit:
        return None
    if await waiting_rows(db, now) >= len(schedule.POST_TIMES) * AHEAD.days:
        return None
    since = _naive(now) - REMARKET_AFTER
    recent = {r["listing_id"] for r in await db.get_collection("marketing_runs").find(
        {"created_at": {"$gte": since}, "status": {"$in": list(OPEN_RUNS)}}).to_list(5000)}
    recent |= {p["listing_id"] for p in await picks.find({"created_at": {"$gte": since}}).to_list(5000)}
    pool = [l for l in await db.get_collection("listings").find({"status": "live"}).to_list(2000)
            if eligible(l) and str(l["_id"]) not in recent]
    if not pool:
        return None
    best = max(pool, key=rank)
    lid = str(best["_id"])
    doc, _ = await runs.create(best["agent_id"], lid)
    await picks.insert_one({"_id": f"{day}:{lid}", "day": day, "listing_id": lid, "agent_id": best["agent_id"], "run_id": doc["_id"],
                            "title": str(best.get("title") or "")[:120], "status": "running", "created_at": now})
    log.info("daily listing pick: %s (%s)", lid, best.get("title"))
    return lid


async def cycle(db, runs, now: datetime, limit: Optional[int] = None) -> dict:
    limit = per_day() if limit is None else limit
    return {"calendared": await follow(db, runs, now), "picked": await pick(db, runs, now, limit)}


async def loop(make_runs: Optional[Callable] = None) -> None:
    while True:
        if per_day() > 0:
            try:
                async with heartbeat("listing_daily", get_database):
                    await cycle(get_database(), (make_runs or default_runs)(), datetime.utcnow())
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("daily listing pick cycle failed")
        await asyncio.sleep(INTERVAL_S)
