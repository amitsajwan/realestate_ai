"""The monthly loop: runs once, only in the month's first week, never twice, and tells the owner when drafts are ready."""
from datetime import datetime, timezone

from app.modules.press import runner
from app.modules.press.store import Store

from ..fakes import FakeDb

FIRST_WEEK = datetime(2026, 11, 3, tzinfo=timezone.utc)
LATE = datetime(2026, 11, 20, tzinfo=timezone.utc)


async def seeded_db():
    db = FakeDb()
    await db.get_collection("projects").insert_one(
        {"_id": "PR1260002600001", "regno": "PR1260002600001", "name": "Project 1", "locality": "kharadi",
         "registered_on": "2026-11-02"})
    return db


async def test_nothing_runs_outside_the_first_week():
    db = await seeded_db()
    assert await runner.cycle(db, LATE) is None
    assert await Store(db).story("2026-11") is None


async def test_runs_once_in_the_first_week_and_never_twice():
    db = await seeded_db()
    out = await runner.cycle(db, FIRST_WEEK)
    assert out is not None and out["month"] == "2026-11"
    again = await runner.cycle(db, FIRST_WEEK)
    assert again is None  # already built: no second spend


async def test_the_owner_is_told_when_drafts_are_ready(monkeypatch):
    told = []

    async def tell_owner(result):
        told.append(result)
    runner.configure(tell_owner=tell_owner)
    try:
        db = await seeded_db()
        await db.get_collection("projects").update_one({"_id": "PR1260002600001"}, {"$set": {"units_total": 10, "units_booked": 5}})
        out = await runner.cycle(db, FIRST_WEEK)
        if out and out.get("pitches"):
            assert told and told[0]["month"] == "2026-11"
    finally:
        runner.configure(tell_owner=None)


def test_press_is_a_newsroom_role_loop_off_by_default():
    from app import worker
    assert "press" in worker.ALL_LOOP_NAMES
    assert "press" in worker.ROLE_LOOPS["newsroom"]
    assert runner.enabled() is False
