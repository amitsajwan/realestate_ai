"""The publish ledger: every real post goes out at most once per key, whatever retries and crashes happen around it."""
import asyncio
from datetime import datetime, timezone

import pytest

from app.modules.social import distribution
from app.modules.social.distribution import COLLECTION, OutcomeUnknown, Paused, send
from app.platform.controls import set_controls
from app.platform.meta_graph.publisher import PublishError, Result

from .fakes import FakeDb

NOW = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)


class Graph:
    """Counts real posts; `fail` makes the next call raise."""

    def __init__(self):
        self.calls, self.fail = 0, None

    async def post(self):
        self.calls += 1
        if self.fail:
            e, self.fail = self.fail, None
            raise e
        return Result(external_id=f"post{self.calls}", permalink=f"https://fb.test/post{self.calls}")


@pytest.fixture(autouse=True)
def ledger_on(monkeypatch):
    monkeypatch.delenv("PUBLISH_LEDGER", raising=False)


async def test_a_key_is_posted_once_and_later_sends_return_the_same_post():
    db, g = FakeDb(), Graph()
    first = await send(db, "calendar:c1", g.post, now=lambda: NOW)
    again = await send(db, "calendar:c1", g.post, now=lambda: NOW)
    assert g.calls == 1
    assert (again.external_id, again.permalink) == (first.external_id, first.permalink) == ("post1", "https://fb.test/post1")
    doc = db.get_collection(COLLECTION).docs[0]
    assert doc["_id"] == "calendar:c1" and doc["status"] == "sent" and doc["external_id"] == "post1"


async def test_different_keys_post_separately():
    db, g = FakeDb(), Graph()
    await send(db, "news:n1:facebook", g.post)
    await send(db, "news:n1:instagram", g.post)
    assert g.calls == 2


async def test_a_failed_attempt_is_retried_and_then_recorded_as_sent():
    db, g = FakeDb(), Graph()
    g.fail = PublishError("Graph API request timed out")
    with pytest.raises(PublishError):
        await send(db, "social:p1", g.post)
    doc = db.get_collection(COLLECTION).docs[0]
    assert doc["status"] == "failed" and "timed out" in doc["error"]
    res = await send(db, "social:p1", g.post)
    assert res.external_id == "post2" and g.calls == 2
    doc = db.get_collection(COLLECTION).docs[0]
    assert doc["status"] == "sent" and doc["attempts"] == 2


async def test_an_attempt_that_never_finished_blocks_a_retry_instead_of_risking_a_duplicate():
    """The process died after claiming (the post may be live): the next attempt must not post again."""
    db, g = FakeDb(), Graph()
    await db.get_collection(COLLECTION).insert_one({"_id": "calendar:c9", "status": "sending", "attempts": 1})
    with pytest.raises(OutcomeUnknown, match="may already be live"):
        await send(db, "calendar:c9", g.post)
    assert g.calls == 0


async def test_the_post_went_out_but_recording_it_failed_then_a_retry_does_not_post_again():
    db, g = FakeDb(), Graph()
    col = db.get_collection(COLLECTION)
    real_update = col.update_one

    async def broken_update(flt, update):
        if update.get("$set", {}).get("status") == "sent":
            raise ConnectionError("mongo blip")
        return await real_update(flt, update)

    col.update_one = broken_update
    with pytest.raises(ConnectionError):
        await send(db, "calendar:c2", g.post)  # the caller sees an error and will retry
    col.update_one = real_update
    with pytest.raises(OutcomeUnknown):
        await send(db, "calendar:c2", g.post)
    assert g.calls == 1  # posted once, never twice


async def test_dry_runs_never_touch_the_ledger_and_never_block_a_real_post():
    db, g = FakeDb(), Graph()
    await send(db, "calendar:c3", g.post, dry_run=True)
    assert db.get_collection(COLLECTION).docs == []
    await send(db, "calendar:c3", g.post)
    assert g.calls == 2 and db.get_collection(COLLECTION).docs[0]["status"] == "sent"


async def test_the_ledger_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("PUBLISH_LEDGER", "off")
    db, g = FakeDb(), Graph()
    await send(db, "calendar:c4", g.post)
    await send(db, "calendar:c4", g.post)
    assert g.calls == 2 and db.get_collection(COLLECTION).docs == []


async def test_a_pause_stops_the_post_before_anything_is_sent():
    db, g = FakeDb(), Graph()
    await set_controls(db, {"posting_paused": True}, "OWNER", NOW)
    with pytest.raises(Paused):
        await send(db, "calendar:c5", g.post, paused_flag="posting_paused")
    assert g.calls == 0 and db.get_collection(COLLECTION).docs == []
    await send(db, "calendar:c5", g.post, paused_flag="news_paused")  # another flag does not stop it
    assert g.calls == 1


async def test_two_processes_racing_for_one_key_post_once():
    db = FakeDb()
    started, release, calls = asyncio.Event(), asyncio.Event(), []

    async def slow_post():
        calls.append(1)
        started.set()
        await release.wait()
        return Result(external_id="only")

    first = asyncio.create_task(send(db, "social:p9", slow_post))
    await started.wait()
    with pytest.raises(OutcomeUnknown):  # the second sees the claim while the first is still posting
        await send(db, "social:p9", slow_post)
    release.set()
    assert (await first).external_id == "only" and len(calls) == 1


def test_the_default_publisher_is_dry_unless_live():
    from app.platform.meta_graph.config import SocialConfig
    from app.platform.meta_graph.graph import GraphPublisher
    from app.platform.meta_graph.publisher import DryRunPublisher
    assert isinstance(distribution.default_publisher(SocialConfig(dry_run=True)), DryRunPublisher)
    assert isinstance(distribution.default_publisher(SocialConfig(dry_run=False)), GraphPublisher)
