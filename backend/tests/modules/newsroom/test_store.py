from datetime import timedelta

from app.modules.newsroom.store import Store

from ..fakes import FakeDb
from .helpers import NOW, item


def make():
    t = {"n": 0}

    def clock():
        t["n"] += 1
        return NOW + timedelta(seconds=t["n"])
    return Store(FakeDb(), clock=clock)


async def test_add_new_skips_existing_ids():
    s = make()
    assert await s.add_new([item(1), item(2)]) == 2
    assert await s.add_new([item(2), item(3)]) == 1
    assert (await s.counts())["new"] == 3


async def test_next_batch_oldest_first_and_limited():
    s = make()
    await s.add_new([item(1), item(2), item(3)])
    assert [d["_id"] for d in await s.next_batch("new", 2)] == ["i1", "i2"]
    assert await s.next_batch("relevant", 5) == []


async def test_move_sets_fields_and_appends_history():
    s = make()
    await s.add_new([item(1)])
    await s.move("i1", "relevant", "kept", relevance={"keep": True})
    d = await s.get("i1")
    assert d["status"] == "relevant" and d["relevance"] == {"keep": True}
    assert [h["status"] for h in d["history"]] == ["new", "relevant"]
    assert d["history"][1]["note"] == "kept"


async def test_queue_is_pending_review_newest_first():
    s = make()
    await s.add_new([item(1), item(2), item(3)])
    await s.move("i1", "pending_review")
    await s.move("i2", "pending_review")
    await s.move("i3", "rejected")
    assert [d["_id"] for d in await s.queue()] == ["i2", "i1"]


async def test_counts_has_every_status():
    s = make()
    c = await s.counts()
    assert c["new"] == 0 and "pending_review" in c and "failed" in c


async def test_published_since_counts_only_done_recent():
    s = make()
    await s.add_new([item(1), item(2), item(3)])
    await s.move("i1", "published", published_at=NOW)
    await s.move("i2", "scheduled", published_at=NOW - timedelta(days=2))
    await s.move("i3", "approved", published_at=NOW)
    assert await s.published_since(NOW - timedelta(hours=24)) == 1


async def test_run_status_roundtrip():
    s = make()
    assert await s.get_run() == {}
    await s.set_run(last_error=None, last_run_at=NOW)
    await s.set_run(last_error="x")
    r = await s.get_run()
    assert r["last_error"] == "x" and r["last_run_at"] == NOW
