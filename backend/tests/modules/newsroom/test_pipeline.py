from datetime import timedelta

from app.modules.newsroom.config import NewsroomConfig
from app.modules.newsroom.pipeline import run_once
from app.modules.newsroom.store import Store

from ..fakes import FakeDb
from .helpers import NOW, FakePublisher, FakeSource, good_stages, item

CFG = NewsroomConfig(enabled=True, daily_cap=2)
LLM = object()


async def approve(store, id, when=None):
    await store.move(id, "approved", publish={"platform_id": None, "scheduled_for": when})


async def test_happy_path_reaches_pending_review_and_not_beyond():
    s = Store(FakeDb())
    c = await run_once(s, [FakeSource([item(1)])], good_stages(), FakePublisher(), LLM, NOW, CFG)
    d = await s.get("i1")
    assert d["status"] == "pending_review" and c["collected"] == 1 and c["errors"] == 0
    assert [h["status"] for h in d["history"]] == ["new", "relevant", "extracted", "drafted", "checked", "pending_review"]
    assert d["draft"]["format"] == "post" and d["facts"]["facts"][0]["quote"]


async def test_second_run_is_idempotent():
    s, pub = Store(FakeDb()), FakePublisher()
    src = [FakeSource([item(1)])]
    await run_once(s, src, good_stages(), pub, LLM, NOW, CFG)
    before = await s.get("i1")
    c = await run_once(s, src, good_stages(), pub, LLM, NOW, CFG)
    assert c["collected"] == 0 and await s.get("i1") == before and pub.calls == []


async def test_failed_check_drops_with_problems():
    s = Store(FakeDb())
    await run_once(s, [FakeSource([item(1)])], good_stages(check_ok=False), None, LLM, NOW, CFG)
    d = await s.get("i1")
    assert d["status"] == "dropped" and "number not in source" in d["history"][-1]["note"]


async def test_one_item_failing_is_isolated_and_sanitised():
    s = Store(FakeDb())
    c = await run_once(s, [FakeSource([item(1), item(2)])], good_stages(fail_on="i1"), None, LLM, NOW, CFG)
    bad, ok = await s.get("i1"), await s.get("i2")
    assert bad["status"] == "failed" and "EAABCDEFGHIJ" not in bad["history"][-1]["note"] and "extract" in bad["history"][-1]["note"]
    assert ok["status"] == "pending_review" and c["errors"] == 1


async def test_broken_source_does_not_stop_others():
    s = Store(FakeDb())
    c = await run_once(s, [FakeSource([], boom=True), FakeSource([item(1)])], good_stages(), None, LLM, NOW, CFG)
    assert c["collected"] == 1 and c["errors"] == 1


async def test_no_llm_pauses_llm_stages():
    s = Store(FakeDb())
    await run_once(s, [FakeSource([item(1)])], good_stages(), None, None, NOW, CFG)
    assert (await s.get("i1"))["status"] == "relevant"


async def test_publish_now_and_scheduled_statuses():
    s, pub = Store(FakeDb()), FakePublisher()
    await s.add_new([item(1), item(2)])
    for i in ("i1", "i2"):
        await s.move(i, "approved", draft={"format": "post", "text": "t", "link": "https://x.test", "title": None, "source_names": []},
                     publish={"platform_id": None, "scheduled_for": None})
    await s.move("i2", "approved", publish={"platform_id": None, "scheduled_for": NOW + timedelta(hours=2)})
    c = await run_once(s, [], good_stages(), pub, LLM, NOW, CFG)
    a, b = await s.get("i1"), await s.get("i2")
    assert a["status"] == "published" and a["publish"]["platform_id"] == "pid1"
    assert b["status"] == "scheduled" and pub.calls[1][2] == NOW + timedelta(hours=2) and c["published"] == 2


async def test_soon_schedule_posts_now_and_far_schedule_fails():
    s, pub = Store(FakeDb()), FakePublisher()
    await s.add_new([item(1), item(2)])
    d = {"format": "post", "text": "t", "link": None, "title": None, "source_names": []}
    await s.move("i1", "approved", draft=d, publish={"scheduled_for": NOW + timedelta(minutes=2)})
    await s.move("i2", "approved", draft=d, publish={"scheduled_for": NOW + timedelta(days=40)})
    await run_once(s, [], good_stages(), pub, LLM, NOW, CFG)
    assert (await s.get("i1"))["status"] == "published" and pub.calls[0][2] is None
    assert (await s.get("i2"))["status"] == "failed"


async def test_daily_cap_holds_extra_items_approved():
    s, pub = Store(FakeDb()), FakePublisher()
    await s.add_new([item(1), item(2), item(3)])
    d = {"format": "post", "text": "t", "link": None, "title": None, "source_names": []}
    for i in ("i1", "i2", "i3"):
        await s.move(i, "approved", draft=d, publish={"scheduled_for": None})
    c = await run_once(s, [], good_stages(), pub, LLM, NOW, CFG)
    assert len(pub.calls) == 2 and c["capped"] == 1 and (await s.get("i3"))["status"] == "approved"
    await run_once(s, [], good_stages(), pub, LLM, NOW + timedelta(hours=1), CFG)
    assert len(pub.calls) == 2  # still capped within 24h
    await run_once(s, [], good_stages(), pub, LLM, NOW + timedelta(hours=25), CFG)
    assert len(pub.calls) == 3


async def test_publish_failure_marks_failed_and_continues():
    s = Store(FakeDb())
    await s.add_new([item(1)])
    await s.move("i1", "approved", draft={"format": "post", "text": "t", "link": None, "title": None, "source_names": []})
    c = await run_once(s, [], good_stages(), FakePublisher(boom=True), LLM, NOW, CFG)
    assert (await s.get("i1"))["status"] == "failed" and c["errors"] == 1
