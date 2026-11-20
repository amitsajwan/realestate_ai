"""The day's best listings marketed by themselves (propertyfacts/daily.py)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.calendar.store import Store as CalendarStore
from app.modules.propertyfacts import daily, schedule

from ..fakes import FakeDb

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 11, 20, 5, 0)          # 10:30 in Pune
NIGHT = datetime(2026, 11, 20, 16, 0)       # 21:30 in Pune
PICS = [{"url": f"/uploads/images/p{i}.jpg", "kind": "image"} for i in range(3)]


def listing(lid, **kw):
    base = {"_id": lid, "agent_id": "HD", "status": "live", "visibility": "public", "title": f"Project {lid}", "media": PICS,
            "price_inr": 9_000_000, "rera_no": "P52100000001", "created_at": NOW - timedelta(days=10)}
    base.update(kw)
    return base


class Runs:
    """MarketingRuns as the pick uses it: create a run, and send a finished one's posts to the calendar."""

    def __init__(self, db):
        self.db, self.created = db, []

    async def create(self, agent_id, listing_id, again=False, language="en", pick=None):
        doc = {"_id": f"run-{listing_id}", "listing_id": listing_id, "agent_id": agent_id, "status": "queued", "created_at": NOW}
        await self.db.get_collection("marketing_runs").insert_one(doc)
        self.created.append(listing_id)
        return doc, True

    async def to_calendar(self, agent_id, listing_id, start=None):
        cal, rows = CalendarStore(self.db), []
        for i, ch in enumerate(("instagram", "facebook_page")):
            at = datetime(start.year, start.month, start.day, 5, 30, tzinfo=timezone.utc) + timedelta(hours=i)
            rid = await cal.add(f"campaign-{listing_id}-listing", ch, "caption", "", at, kind="post", status="planned")
            rows.append({"row_id": rid, "channel": ch, "due_at": at})
        return {"calendar": rows}


async def seeded(*docs):
    db = FakeDb()
    for d in docs:
        await db.get_collection("listings").insert_one(d)
    return db, Runs(db)


async def test_the_best_listing_is_picked_first_and_one_at_a_time():
    db, runs = await seeded(listing("A", price_inr=None), listing("B"), listing("C", media=PICS[:1]),       # C: one picture
                            listing("D", title="Sample flat"), listing("E", status="draft"))
    assert (await daily.cycle(db, runs, NOW, limit=5))["picked"] == "B"
    assert (await daily.cycle(db, runs, NOW, limit=5))["picked"] is None      # B's run is still going
    assert runs.created == ["B"]


async def test_a_finished_run_goes_to_the_calendar_approved_and_the_next_is_picked():
    db, runs = await seeded(listing("A"), listing("B", created_at=NOW))
    await daily.cycle(db, runs, NOW, limit=5)
    await db.get_collection("marketing_runs").update_one({"_id": "run-B"}, {"$set": {"status": "done"}})
    out = await daily.cycle(db, runs, NOW + timedelta(minutes=30), limit=5)
    assert out == {"calendared": 1, "started": [], "picked": "A"}
    rows = await CalendarStore(db).all()
    assert {r["status"] for r in rows} == {"approved"} and len(rows) == 2
    assert "daily listing pick" in rows[0]["history"][-1]["note"]
    pick = await db.get_collection(daily.COLLECTION).find_one({"_id": "2026-11-20:B"})
    assert pick["status"] == "calendared" and pick["rows"] == 2


async def test_no_pick_at_night_past_the_days_limit_or_when_the_calendar_is_full():
    db, runs = await seeded(listing("A"), listing("B"))
    assert (await daily.cycle(db, runs, NIGHT, limit=5))["picked"] is None
    assert (await daily.cycle(db, runs, NOW, limit=0))["picked"] is None
    cal = CalendarStore(db)
    per = len(schedule.POST_TIMES)
    for i in range(per * daily.AHEAD.days):   # three days of Instagram slots already waiting
        await cal.add(f"campaign-X{i}-listing", "instagram", "c", "", datetime(2026, 11, 21 + i // per, 5, 30 + i % per, tzinfo=timezone.utc),
                      kind="post", status="approved")
    assert (await daily.cycle(db, runs, NOW, limit=5))["picked"] is None


async def test_a_listing_marketed_lately_is_not_picked_again():
    db, runs = await seeded(listing("A"))
    await db.get_collection("marketing_runs").insert_one({"_id": "old", "listing_id": "A", "agent_id": "HD", "status": "done",
                                                          "created_at": NOW - timedelta(days=20)})
    assert (await daily.cycle(db, runs, NOW, limit=5))["picked"] is None


async def test_a_run_waiting_on_the_agents_answers_is_given_up_and_a_failed_one_ends():
    db, runs = await seeded(listing("A"), listing("B", created_at=NOW))
    await daily.cycle(db, runs, NOW, limit=5)
    await db.get_collection("marketing_runs").update_one({"_id": "run-B"}, {"$set": {"status": "asking"}})
    await daily.cycle(db, runs, NOW + timedelta(hours=1), limit=5)
    assert (await db.get_collection(daily.COLLECTION).find_one({"_id": "2026-11-20:B"}))["status"] == "running"
    await daily.cycle(db, runs, NOW + timedelta(hours=13), limit=5)
    pick = await db.get_collection(daily.COLLECTION).find_one({"_id": "2026-11-20:B"})
    assert pick["status"] == "skipped" and (await db.get_collection("marketing_runs").find_one({"_id": "run-B"}))["status"] == "cancelled"
    # the next morning A is picked; its run fails, and the pick ends with the run's error
    assert (await daily.cycle(db, runs, NOW + timedelta(days=1), limit=5))["picked"] == "A"
    await db.get_collection("marketing_runs").update_one({"_id": "run-A"}, {"$set": {"status": "failed", "error": "no facts"}})
    await daily.cycle(db, runs, NOW + timedelta(days=1, minutes=30), limit=5)
    pick = await db.get_collection(daily.COLLECTION).find_one({"_id": "2026-11-21:A"})
    assert pick["status"] == "failed" and pick["reason"] == "no facts"


GOOD = [{"url": f"/uploads/images/g{i}.jpg", "kind": "image", "quality": {"score": 92}} for i in range(4)]
POOR = [{"url": f"/uploads/images/q{i}.jpg", "kind": "image", "quality": {"score": 55}} for i in range(4)]


async def top_seeded():
    db, runs = await seeded(
        listing("cool", media=GOOD, rera_no="P1"),                                       # 2029, hot 0
        listing("hot", media=GOOD, rera_no="P2"),                                        # 2030, hot 40
        listing("warm", media=GOOD, rera_no="P3"),                                       # 2028, hot 12
        listing("soon", media=GOOD, rera_no="P4"),                                       # 2027: completes too early
        listing("blurry", media=POOR + GOOD[:2], rera_no="P2"),                          # two good pictures only
        listing("unscored", media=PICS, rera_no="P2"),                                   # pictures never judged
        listing("unknown", media=GOOD, rera_no="P9"),                                    # not in the register
        listing("network", media=GOOD, rera_no="P2", visibility="network"))
    projects = db.get_collection("projects")
    for regno, done, hot in (("P1", datetime(2029, 4, 30), 0), ("P2", "2030-07-31", 40), ("P3", datetime(2028, 1, 30), 12),
                             ("P4", datetime(2027, 12, 31), 90)):
        await projects.insert_one({"_id": regno, "completion_now": done, "hot_score": hot})
    return db, runs


async def test_the_top_push_takes_projects_completing_after_2027_with_good_pictures_hottest_first():
    db, runs = await top_seeded()
    assert [l["_id"] for l, _ in await daily.top(db)] == ["hot", "warm", "cool"]
    assert [l["_id"] for l, _ in await daily.top(db, n=2)] == ["hot", "warm"]


async def test_top_picks_run_three_at_a_time_at_any_hour_and_reach_the_calendar_approved():
    db, runs = await top_seeded()
    await db.get_collection("listings").insert_one(listing("fourth", media=GOOD, rera_no="P1", created_at=NOW))
    out = await daily.queue_top(db, NIGHT)
    assert out == {"queued": ["Project hot", "Project warm", "Project fourth", "Project cool"], "already": []}
    assert await daily.busy(db)
    first = await daily.cycle(db, runs, NIGHT, limit=5)        # night: no daily pick, but the top push starts
    assert first["started"] == ["hot", "warm", "fourth"] and first["picked"] is None
    assert (await daily.cycle(db, runs, NIGHT, limit=5))["started"] == []      # three in flight
    await db.get_collection("marketing_runs").update_one({"_id": "run-hot"}, {"$set": {"status": "done"}})
    out = await daily.cycle(db, runs, NIGHT + timedelta(minutes=2), limit=5)
    assert out["calendared"] == 1 and out["started"] == ["cool"]
    rows = await CalendarStore(db).all()
    assert len(rows) == 2 and {r["status"] for r in rows} == {"approved"}
    picks = {p["listing_id"]: p for p in await db.get_collection(daily.COLLECTION).find({}).to_list(10)}
    assert picks["hot"]["status"] == "calendared" and picks["hot"]["batch"] == "top" and picks["hot"]["hot"] == 40
    assert picks["cool"]["run_id"] == "run-cool" and picks["cool"]["status"] == "running"


async def test_queueing_the_top_push_twice_adds_nothing_and_lately_marketed_listings_are_left():
    db, runs = await top_seeded()
    await db.get_collection("marketing_runs").insert_one({"_id": "old", "listing_id": "warm", "agent_id": "HD", "status": "done",
                                                          "created_at": NOW - timedelta(days=3)})
    assert await daily.queue_top(db, NOW) == {"queued": ["Project hot", "Project cool"], "already": ["Project warm"]}
    assert await daily.queue_top(db, NOW + timedelta(hours=1)) == {"queued": [], "already": ["Project hot", "Project warm", "Project cool"]}


async def test_a_top_pick_whose_listing_cannot_be_marketed_ends_and_the_next_starts():
    db, runs = await top_seeded()
    await daily.queue_top(db, NOW)

    async def refuse(agent_id, listing_id, **kw):
        if listing_id == "hot":
            raise RuntimeError("Publish this listing first")
        return await Runs.create(runs, agent_id, listing_id)
    runs.create = refuse
    assert await daily.start_waiting(db, runs, NOW) == ["warm", "cool"]
    pick = await db.get_collection(daily.COLLECTION).find_one({"_id": "2026-11-20:hot"})
    assert pick["status"] == "failed" and "Publish" in pick["reason"]
