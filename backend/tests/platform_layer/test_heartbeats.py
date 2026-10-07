"""Loop heartbeats: start / success / error recorded per cycle; recording never breaks a loop."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.platform import heartbeats
from app.platform.heartbeats import age_s, heartbeat, read_all, stale

T0 = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)


class HbCollection:
    def __init__(self, fail=None, hang=False):
        self.docs, self.fail, self.hang, self.writes = {}, fail, hang, 0

    async def update_one(self, flt, update, upsert=False):
        if self.hang:
            await asyncio.Event().wait()
        if self.fail:
            raise self.fail
        assert upsert
        self.writes += 1
        self.docs.setdefault(flt["_id"], {"_id": flt["_id"]}).update(update["$set"])

    def find(self, flt):
        docs = list(self.docs.values())

        class Cursor:
            async def to_list(self, n):
                return docs[:n]
        return Cursor()


class HbDb:
    def __init__(self, **kw):
        self.col = HbCollection(**kw)

    def get_collection(self, name):
        assert name == heartbeats.COLLECTION
        return self.col


@pytest.fixture(autouse=True)
def _fresh_throttle():
    heartbeats._last_write.clear()
    yield
    heartbeats._last_write.clear()


def clock_at(*times):
    it = iter(times)
    return lambda: next(it)


async def test_a_good_cycle_records_start_and_success():
    db = HbDb()
    async with heartbeat("calendar", lambda: db, clock=clock_at(T0, T0 + timedelta(seconds=2))):
        assert db.col.docs["calendar"]["last_start_at"] == T0
    doc = db.col.docs["calendar"]
    assert doc["last_ok_at"] == T0 + timedelta(seconds=2) and "last_error" not in doc and doc["host"]


async def test_a_failing_cycle_records_a_short_sanitised_error_and_still_raises():
    db = HbDb()
    with pytest.raises(RuntimeError):
        async with heartbeat("engage", lambda: db, clock=clock_at(T0, T0)):
            raise RuntimeError("graph said no: access_token=EAAsecretsecretsecretsecret " + "x" * 1000)
    doc = db.col.docs["engage"]
    assert doc["last_error_at"] == T0 and "last_ok_at" not in doc
    assert doc["last_error"].startswith("RuntimeError: graph said no") and "secret" not in doc["last_error"]
    assert len(doc["last_error"]) <= 300


async def test_failed_marks_a_cycle_that_handles_its_own_error():
    db = HbDb()
    async with heartbeat("newsroom", lambda: db) as hb:
        hb.failed(ValueError("feed down"))
    assert db.col.docs["newsroom"]["last_error"] == "ValueError: feed down"
    assert "last_ok_at" not in db.col.docs["newsroom"]


async def test_cancellation_records_nothing_and_propagates():
    db = HbDb()
    with pytest.raises(asyncio.CancelledError):
        async with heartbeat("calendar", lambda: db):
            raise asyncio.CancelledError()
    assert set(db.col.docs["calendar"]) == {"_id", "last_start_at", "host"}


@pytest.mark.parametrize("get_db", [
    lambda: (_ for _ in ()).throw(RuntimeError("Database not initialized")),
    lambda: HbDb(fail=ConnectionError("mongo down")),
    lambda: None,
])
async def test_a_database_error_never_breaks_the_cycle(get_db):
    ran = []
    async with heartbeat("engage", get_db):
        ran.append(1)
    assert ran == [1]


async def test_a_hanging_write_is_given_up(monkeypatch):
    monkeypatch.setattr(heartbeats, "WRITE_TIMEOUT_S", 0.05)
    db = HbDb(hang=True)
    async with heartbeat("calendar", lambda: db):
        pass  # returns after the timeouts instead of hanging the loop


async def test_a_loop_switched_off_touches_no_database():
    calls = []
    async with heartbeat("newsroom", lambda: calls.append(1), on=False) as hb:
        hb.failed("x")
    assert calls == []


async def test_every_s_limits_start_and_ok_writes_but_not_errors():
    db, t = HbDb(), [0.0]
    mono = lambda: t[0]  # noqa: E731
    for _ in range(5):  # 5 quick cycles: one start and one ok write
        async with heartbeat("listing_reels", lambda: db, every_s=60, monotonic=mono):
            pass
    assert db.col.writes == 2
    t[0] = 61.0
    async with heartbeat("listing_reels", lambda: db, every_s=60, monotonic=mono):
        pass
    assert db.col.writes == 4
    with pytest.raises(OSError):
        async with heartbeat("listing_reels", lambda: db, every_s=60, monotonic=mono):
            raise OSError("disk full")
    assert db.col.writes == 5 and db.col.docs["listing_reels"]["last_error"] == "OSError: disk full"


async def test_staleness_is_twice_the_interval_from_the_latest_sign_of_life():
    assert stale(None, 60, T0) and age_s({}, T0) is None
    doc = {"last_start_at": (T0 - timedelta(seconds=200)).replace(tzinfo=None),  # Motor gives naive UTC
           "last_ok_at": T0 - timedelta(seconds=100)}
    assert age_s(doc, T0) == 100
    assert stale(doc, 49, T0) and not stale(doc, 50, T0)


async def test_read_all_returns_one_doc_per_loop():
    db = HbDb()
    async with heartbeat("engage", lambda: db):
        pass
    async with heartbeat("calendar", lambda: db):
        pass
    assert set(await read_all(db)) == {"engage", "calendar"}


async def test_a_loop_that_beats_every_cycle_stops_when_cancelled():
    """asyncio.wait_for on 3.11 can swallow a cancel that races a write that finishes at once; the loop must still stop."""
    db = HbDb()

    async def loop():
        while True:
            async with heartbeat("engage", lambda: db):
                pass
            await asyncio.sleep(0)
    for _ in range(20):
        task = asyncio.create_task(loop())
        for _ in range(5):
            await asyncio.sleep(0)
        task.cancel()
        await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), 1)
        assert task.cancelled()
