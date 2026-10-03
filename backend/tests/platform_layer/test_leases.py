"""Runner leases: one copy of each background loop, however many processes start it."""
import asyncio
import copy
from datetime import datetime, timedelta, timezone

import pytest
from pymongo.errors import DuplicateKeyError

from app.platform import leases
from app.platform.leases import acquire, release, run_as_leader

T0 = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)


class LeaseCollection:
    """Just enough of a Motor collection for leases: _id equality, $or, $lt, matched_count, unique _id."""

    def __init__(self):
        self.docs = {}
        self.down = False

    def _check(self):
        if self.down:
            raise ConnectionError("mongo down")

    @staticmethod
    def _match(doc, flt):
        for key, cond in flt.items():
            if key == "$or":
                if not any(LeaseCollection._match(doc, c) for c in cond):
                    return False
            elif isinstance(cond, dict):
                if "$lt" in cond and not (doc.get(key) is not None and doc[key] < cond["$lt"]):
                    return False
            elif doc.get(key) != cond:
                return False
        return True

    async def update_one(self, flt, update):
        self._check()
        doc = self.docs.get(flt["_id"])
        matched = doc is not None and self._match(doc, flt)
        if matched:
            doc.update(update["$set"])
        return type("R", (), {"matched_count": int(matched)})

    async def insert_one(self, doc):
        self._check()
        if doc["_id"] in self.docs:
            raise DuplicateKeyError("E11000 duplicate key")
        self.docs[doc["_id"]] = copy.deepcopy(doc)


class LeaseDb:
    def __init__(self):
        self.col = LeaseCollection()

    def get_collection(self, name):
        assert name == leases.COLLECTION
        return self.col


async def test_first_caller_takes_the_lease_and_others_are_refused():
    db = LeaseDb()
    assert await acquire(db, "newsroom", "a", T0)
    assert not await acquire(db, "newsroom", "b", T0 + timedelta(seconds=1))
    assert await acquire(db, "calendar", "b", T0)  # leases are per loop


async def test_holder_renews_and_a_follower_takes_over_only_after_expiry():
    db = LeaseDb()
    assert await acquire(db, "engage", "a", T0, ttl_s=90)
    assert await acquire(db, "engage", "a", T0 + timedelta(seconds=60), ttl_s=90)   # renewed until T0+150
    assert not await acquire(db, "engage", "b", T0 + timedelta(seconds=120))       # still held
    assert await acquire(db, "engage", "b", T0 + timedelta(seconds=151))           # expired: b takes over
    assert db.col.docs["engage"]["holder"] == "b"
    assert not await acquire(db, "engage", "a", T0 + timedelta(seconds=152))       # a has lost it


async def test_release_hands_over_at_once_but_only_by_the_holder():
    db = LeaseDb()
    await acquire(db, "calendar", "a", T0)
    await release(db, "calendar", "b", T0 + timedelta(seconds=1))  # not b's to release
    assert not await acquire(db, "calendar", "b", T0 + timedelta(seconds=2))
    await release(db, "calendar", "a", T0 + timedelta(seconds=3))
    assert await acquire(db, "calendar", "b", T0 + timedelta(seconds=4))


FAST = dict(ttl_s=0.6, renew_s=0.05, step_down_s=0.3)


def counting_loop(state):
    async def loop():
        state["starts"] += 1
        state["running"] += 1
        state["max_running"] = max(state["max_running"], state["running"])
        try:
            await asyncio.Event().wait()
        finally:
            state["running"] -= 1
    return loop


def new_state():
    return {"starts": 0, "running": 0, "max_running": 0}


async def test_two_runners_never_run_the_loop_at_the_same_time():
    db, state = LeaseDb(), new_state()
    runners = [asyncio.create_task(run_as_leader("newsroom", counting_loop(state), lambda: db, **FAST)) for _ in range(4)]
    await asyncio.sleep(0.4)
    assert state["running"] == 1 and state["max_running"] == 1 and state["starts"] == 1
    for r in runners:
        r.cancel()
    await asyncio.gather(*runners, return_exceptions=True)
    assert state["running"] == 0


async def test_clean_shutdown_releases_and_a_follower_takes_over_quickly():
    db, state = LeaseDb(), new_state()
    leader = asyncio.create_task(run_as_leader("calendar", counting_loop(state), lambda: db, holder="a", **FAST))
    await asyncio.sleep(0.1)
    follower = asyncio.create_task(run_as_leader("calendar", counting_loop(state), lambda: db, holder="b", **FAST))
    await asyncio.sleep(0.1)
    assert db.col.docs["calendar"]["holder"] == "a" and state["running"] == 1
    leader.cancel()
    await asyncio.gather(leader, return_exceptions=True)
    await asyncio.sleep(0.15)  # well under the 0.6 s TTL: the release lets b start without waiting for expiry
    assert db.col.docs["calendar"]["holder"] == "b"
    assert state["running"] == 1 and state["max_running"] == 1 and state["starts"] == 2
    follower.cancel()
    await asyncio.gather(follower, return_exceptions=True)


async def test_leader_steps_down_when_it_cannot_renew_before_the_lease_expires():
    db, state = LeaseDb(), new_state()
    runner = asyncio.create_task(run_as_leader("engage", counting_loop(state), lambda: db, **FAST))
    await asyncio.sleep(0.1)
    assert state["running"] == 1
    db.col.down = True
    await asyncio.sleep(0.2)
    assert state["running"] == 1          # a short database blip does not stop the loop
    await asyncio.sleep(0.25)
    assert state["running"] == 0          # stopped after step_down_s, before the TTL could let anyone else in
    db.col.down = False
    await asyncio.sleep(0.15)
    assert state["running"] == 1 and state["starts"] == 2  # lease still ours: picks the loop back up
    runner.cancel()
    await asyncio.gather(runner, return_exceptions=True)


async def test_a_loop_that_crashes_is_restarted_by_its_leader():
    db, calls = LeaseDb(), []

    async def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("boom")
        await asyncio.Event().wait()

    runner = asyncio.create_task(run_as_leader("listing_reels", flaky, lambda: db, **FAST))
    await asyncio.sleep(0.2)
    assert len(calls) == 2
    runner.cancel()
    await asyncio.gather(runner, return_exceptions=True)


def test_step_down_is_shorter_than_the_lease():
    assert leases.STEP_DOWN_S + leases.RENEW_S < leases.TTL_S
