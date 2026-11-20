"""The day's best listings marketed without anyone pressing "Post & market" (owner, 2026-11-19: "we can have 5 listings a day, our
best ones"; of 55 live listings 3 had ever been marketed, each by hand).

Every INTERVAL_S, with LISTING_DAILY_PICKS > 0:
  1. Follow the open picks. A pick's run done -> its posts go to the calendar (MarketingRuns.to_calendar, from tomorrow) and every
     row it added is approved (calendar.store.approve, by "daily listing pick"), so they publish through the calendar's usual path
     (social.distribution, the pause switches). A failed or cancelled run ends the pick; a run that stops to ask the agent
     questions (understand.py) is cancelled after ASKING_GIVE_UP and the listing waits for its agent.
  2. Pick the next one, 09:00-18:00 IST, when no pick is running, fewer than LISTING_DAILY_PICKS were picked today, and the
     campaign rows already waiting on Instagram fill less than AHEAD of the calendar's slots (5 a day: schedule.POST_TIMES). The
     slots are the real pace: a listing is its post and its reel, so about two listings a day go out on each channel.
     The best listing first (`rank`): a price, a MahaRERA number, the most pictures, selling points, newest. A listing marketed
     (or tried) in the last REMARKET_AFTER is not picked again.

The top push (owner, 2026-11-20: "for each hot or our top listings we have to trigger marketing, like 50 best projects, today
itself ... eligible projects that have completion after 2027, and have good images"): `queue_top` lines up the best TOP_N listings
whose project MahaRERA says completes in 2028 or later and that hold GOOD_PICTURES pictures photoquality scored GOOD_PICTURE or
more, hottest project first (areastats.hot's hot_score), as `waiting` picks. Each cycle starts waiting picks while fewer than
IN_FLIGHT runs are going, at any hour, so the renderer works through them in a few hours without the queue looking stuck
(render_job.STUCK_AFTER); while picks wait or run the loop comes back every FAST_S instead of INTERVAL_S. Their posts are approved
as above and the calendar's free slots (5 a day on each channel: schedule.POST_TIMES) spread them over the following days;
the daily pick waits meanwhile (one is running, and the waiting rows fill AHEAD).

Picks live in `listing_daily_picks` (this module's): _id "<IST day>:<listing id>", status waiting | running | calendared | failed |
skipped; the top push's carry `batch: "top"`, their place in the order and the project's hot score.
"""
import asyncio
import logging
import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.core.database import close_database, get_database, init_database
from app.modules.calendar.store import Store as CalendarStore, aware
from app.modules.newsroom.store import Store as Register
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
TOP_N = 50
TOP_COMPLETION_FROM = date(2028, 1, 1)   # "completion after 2027": MahaRERA's current completion date in 2028 or later
GOOD_PICTURE = 80                        # photoquality score (0-100) of a picture good enough to lead a post
GOOD_PICTURES = 3                        # a carousel and a reel need at least three of them
IN_FLIGHT = 3                            # top-push runs going at once
FAST_S = 120


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


def good_pictures(listing: dict) -> int:
    return sum(1 for m in listing.get("media") or [] if (m or {}).get("kind") == "image"
               and ((m.get("quality") or {}).get("score") or 0) >= GOOD_PICTURE)


def _day(v: Any) -> Optional[date]:
    """A register date (a datetime, or an ISO string as some reads keep it) as a date; None when there is none."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v or "")[:10])
    except ValueError:
        return None


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
            elif st == "asking" and _naive(now) - _naive(p.get("started_at") or p["created_at"]) >= ASKING_GIVE_UP:
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


async def _recent(db, now: datetime) -> Set[str]:
    """Listings marketed (or tried) within REMARKET_AFTER: by a run of their own, or picked here."""
    since = _naive(now) - REMARKET_AFTER
    recent = {r["listing_id"] for r in await db.get_collection("marketing_runs").find(
        {"created_at": {"$gte": since}, "status": {"$in": list(OPEN_RUNS)}}).to_list(5000)}
    recent |= {p["listing_id"] for p in await db.get_collection(COLLECTION).find({"created_at": {"$gte": since}}).to_list(5000)}
    return recent


async def top(db, n: int = TOP_N) -> List[Tuple[dict, dict]]:
    """The listings the top push markets, best first, with their project's register record: live and public, at least
    GOOD_PICTURES good pictures, a MahaRERA number whose project completes on or after TOP_COMPLETION_FROM. Hottest project
    first, then the daily pick's `rank`."""
    reg, out = Register(db), []
    for l in await db.get_collection("listings").find({"status": "live"}).to_list(2000):
        regno = str(l.get("rera_no") or "").strip().upper()
        if not regno or not eligible(l) or good_pictures(l) < GOOD_PICTURES:
            continue
        project = await reg.project(regno) or {}
        done = _day(project.get("completion_now"))
        if done and done >= TOP_COMPLETION_FROM:
            out.append((l, project))
    out.sort(key=lambda lp: (lp[1].get("hot_score") or 0, rank(lp[0])), reverse=True)
    return out[:n]


async def queue_top(db, now: datetime, n: int = TOP_N) -> Dict[str, List[str]]:
    """Line the top listings up as waiting picks (the loop starts them). Listings marketed lately are left as they are, so
    pressing twice adds nothing. -> {"queued": titles, "already": titles}."""
    picks, recent = db.get_collection(COLLECTION), await _recent(db, now)
    day = _aware(now).astimezone(IST).date().isoformat()
    out: Dict[str, List[str]] = {"queued": [], "already": []}
    for order, (l, project) in enumerate(await top(db, n)):
        lid, title = str(l["_id"]), str(l.get("title") or "")[:120]
        if lid in recent:
            out["already"].append(title)
            continue
        await picks.insert_one({"_id": f"{day}:{lid}", "day": day, "listing_id": lid, "agent_id": l["agent_id"], "run_id": None,
                                "title": title, "status": "waiting", "batch": "top", "order": order,
                                "hot": project.get("hot_score") or 0, "created_at": now})
        out["queued"].append(title)
    log.info("top push: %d queued, %d marketed lately", len(out["queued"]), len(out["already"]))
    return out


async def start_waiting(db, runs, now: datetime) -> List[str]:
    """Start waiting picks, best first, while fewer than IN_FLIGHT picks are running. -> the listing ids started."""
    picks, started = db.get_collection(COLLECTION), []
    running = await picks.count_documents({"status": "running"})
    for p in await picks.find({"status": "waiting"}).sort("order", 1).to_list(500):
        if running >= IN_FLIGHT:
            break
        try:
            doc, _ = await runs.create(p["agent_id"], p["listing_id"])
        except Exception as e:   # a listing taken down since it was queued: that pick ends, the rest go on
            await picks.update_one({"_id": p["_id"]}, {"$set": {"status": "failed", "reason": str(e)[:200], "finished_at": now}})
            continue
        await picks.update_one({"_id": p["_id"]}, {"$set": {"status": "running", "run_id": doc["_id"], "started_at": now}})
        running += 1
        started.append(p["listing_id"])
    return started


async def busy(db) -> bool:
    """Picks waiting or running: the loop comes back sooner."""
    return bool(await db.get_collection(COLLECTION).find_one({"status": {"$in": ["waiting", "running"]}}))


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
    recent = await _recent(db, now)
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
    out = {"calendared": await follow(db, runs, now), "started": await start_waiting(db, runs, now)}
    return {**out, "picked": await pick(db, runs, now, limit)}


async def loop(make_runs: Optional[Callable] = None) -> None:
    while True:
        wait = INTERVAL_S
        if per_day() > 0:
            try:
                async with heartbeat("listing_daily", get_database):
                    await cycle(get_database(), (make_runs or default_runs)(), datetime.utcnow())
                    wait = FAST_S if await busy(get_database()) else INTERVAL_S
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("daily listing pick cycle failed")
        await asyncio.sleep(wait)


async def _main(n: int) -> None:
    """`python -m app.modules.propertyfacts.daily --top 50`: queue the top push by hand (the owner's 2026-11-20 run)."""
    await init_database()
    try:
        out = await queue_top(get_database(), datetime.utcnow(), n)
        print(f"queued {len(out['queued'])}:", *out["queued"], sep="\n  ")
        print(f"marketed lately {len(out['already'])}:", *out["already"], sep="\n  ")
    finally:
        await close_database()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Queue the top listings for marketing")
    parser.add_argument("--top", type=int, default=TOP_N)
    asyncio.run(_main(parser.parse_args().top))
