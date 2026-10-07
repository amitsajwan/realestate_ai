"""The worker process (python -m app.worker) and RUN_BACKGROUND_LOOPS: who starts the background loops. No real Mongo."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI

from app import worker
from app.core import application
from app.modules.reels import listing_reel
from tests.platform_layer.test_leases import LeaseDb

T0 = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)


def recording_loop(name, state):
    async def loop():
        state["running"].add(name)
        try:
            await asyncio.Event().wait()
        finally:
            state["running"].discard(name)
            state["stopped"].append(name)
    return loop


@pytest.fixture
def events(monkeypatch):
    seen = []

    async def init():
        seen.append("init")

    async def close():
        seen.append("close")

    monkeypatch.setattr(worker, "setup_logging", lambda **_: None)  # the real one reconfigures logging for later tests
    monkeypatch.setattr(worker, "init_database", init)
    monkeypatch.setattr(worker, "close_database", close)
    return seen


async def test_worker_runs_each_loop_under_its_lease_and_releases_them_on_stop(events, monkeypatch):
    db, state, stop = LeaseDb(), {"running": set(), "stopped": []}, asyncio.Event()
    released_before_close = []

    async def close():
        now = datetime.now(timezone.utc)
        released_before_close.append(all(d["expires_at"] <= now for d in db.col.docs.values()))
        events.append("close")
    monkeypatch.setattr(worker, "close_database", close)
    names = ("engage", "newsroom", "calendar", "listing_reels")
    table = {n: recording_loop(n, state) for n in names}
    task = asyncio.create_task(worker.run(stop, table=table, get_db=lambda: db))
    for _ in range(50):
        await asyncio.sleep(0.01)
        if len(state["running"]) == 4:
            break
    assert state["running"] == set(names)
    assert set(db.col.docs) == set(names)  # one lease per loop, held by this worker
    holders = {d["holder"] for d in db.col.docs.values()}
    assert len(holders) == 4  # one holder id per loop

    stop.set()  # what SIGTERM does
    await asyncio.wait_for(task, 5)
    assert state["running"] == set() and sorted(state["stopped"]) == sorted(names)
    now = datetime.now(timezone.utc)
    assert all(d["expires_at"] <= now for d in db.col.docs.values())  # released: the next process takes over at once
    assert events == ["init", "close"] and released_before_close == [True]  # the database closes after the release


async def test_worker_does_not_run_a_loop_another_process_holds(events):
    db, state, stop = LeaseDb(), {"running": set(), "stopped": []}, asyncio.Event()
    db.col.docs["calendar"] = {"_id": "calendar", "holder": "api:1", "expires_at": T0 + timedelta(days=3650), "renewed_at": T0}
    task = asyncio.create_task(worker.run(stop, table={"calendar": recording_loop("calendar", state)}, get_db=lambda: db))
    await asyncio.sleep(0.05)
    assert state["running"] == set()
    stop.set()
    await asyncio.wait_for(task, 5)
    assert db.col.docs["calendar"]["holder"] == "api:1"


async def test_worker_in_production_refuses_to_start_without_the_database(events, monkeypatch):
    async def down():
        raise ConnectionError("mongo unreachable")
    monkeypatch.setattr(worker, "init_database", down)
    monkeypatch.setattr(worker.settings, "environment", "production")
    started = []
    monkeypatch.setattr(worker, "start_loops", lambda *a, **k: started.append(1) or {})
    with pytest.raises(ConnectionError):
        await worker.run(asyncio.Event(), table={})
    assert started == []


def test_the_worker_runs_the_eight_loops_under_the_api_lease_names():
    from app.modules.calendar.runner import loop as calendar_loop
    from app.modules.insights.collector import loop as insights_loop
    from app.modules.knowledge.gaps import loop as gaps_loop
    from app.modules.engage.runner import loop as engage_loop
    from app.modules.newsroom.runner import loop as newsroom_loop
    from app.modules.propertyfacts.jobs import loop as marketing_loop
    from app.modules.areastats.enrich import loop as enrich_loop
    assert worker.loops() == {"engage": engage_loop, "newsroom": newsroom_loop, "calendar": calendar_loop,
                              "listing_reels": listing_reel.loop, "marketing_runs": marketing_loop,
                              "project_enrich": enrich_loop, "insights": insights_loop,
                              "answer_gaps": gaps_loop}


# ---- --check ----------------------------------------------------------------------------------------------------------
INTERVALS = {"engage": 60.0, "newsroom": None, "calendar": 300.0, "listing_reels": 900.0}


async def test_check_passes_when_every_enabled_loop_is_fresh(capsys):
    docs = {"engage": {"last_start_at": T0 - timedelta(seconds=30)},
            "calendar": {"last_ok_at": T0 - timedelta(seconds=500), "last_error": "boom"},
            "listing_reels": {"last_start_at": T0 - timedelta(seconds=70)}}

    async def read():
        return docs
    assert await worker.check(read, INTERVALS, T0) == 0
    out = capsys.readouterr().out
    assert "OFF   newsroom" in out and "OK    calendar" in out and "last error: boom" in out


async def test_check_fails_on_a_stale_or_missing_heartbeat_but_not_on_a_disabled_loop(capsys):
    docs = {"engage": {"last_start_at": T0 - timedelta(seconds=121)},  # limit is 2 x 60s
            "calendar": {"last_start_at": T0 - timedelta(seconds=10)},
            "newsroom": {"last_start_at": T0 - timedelta(days=30)}}  # switched off: not checked

    async def read():
        return docs
    assert await worker.check(read, INTERVALS, T0) == 1
    out = capsys.readouterr().out
    assert "STALE engage: last heartbeat 121s ago (limit 120s)" in out
    assert "STALE listing_reels: last heartbeat never" in out
    assert "newsroom" in out and "STALE newsroom" not in out


async def test_check_says_so_when_it_cannot_read_the_heartbeats(capsys):
    async def read():
        raise ConnectionError("mongo down")
    assert await worker.check(read, INTERVALS, T0) == 2
    assert "could not read" in capsys.readouterr().out


def test_disabled_loops_are_not_expected(monkeypatch):
    for k in ("ENGAGE_ENABLED", "NEWSROOM_ENABLED", "CALENDAR_ENABLED", "SOCIAL_DRY_RUN"):
        monkeypatch.delenv(k, raising=False)
    got = worker.expected_intervals()
    assert got["engage"] is None and got["newsroom"] is None and got["calendar"] is None
    assert got["insights"] is None   # dry run (the default): nothing real is published, so there is nothing to read
    assert got["listing_reels"] == listing_reel.HEARTBEAT_INTERVAL_S
    monkeypatch.setenv("CALENDAR_ENABLED", "true")
    monkeypatch.setenv("CALENDAR_INTERVAL_SECONDS", "120")
    assert worker.expected_intervals()["calendar"] == 120.0


# ---- RUN_BACKGROUND_LOOPS in the API process -----------------------------------------------------------------------------
async def _noop(*_a, **_k):
    return None


@pytest.fixture
def api_startup(monkeypatch):
    import app.utils.database_init as database_init
    monkeypatch.setattr(application, "setup_logging", lambda **_: None)
    for name in ("init_database", "close_database", "start_token_cleanup", "stop_token_cleanup"):
        monkeypatch.setattr(application, name, _noop)
    monkeypatch.setattr(database_init, "initialize_database", _noop)
    started = []
    monkeypatch.setattr(application, "start_background_loops", lambda app: started.append(app))
    return started


async def test_api_starts_the_loops_by_default(api_startup, monkeypatch):
    assert application.settings.run_background_loops is True  # the default: nothing changes until the worker is deployed
    app = FastAPI()
    async with application.lifespan(app):
        assert api_startup == [app]


async def test_api_leaves_the_loops_to_the_worker_when_switched_off(api_startup, monkeypatch):
    monkeypatch.setattr(application.settings, "run_background_loops", False)
    app = FastAPI()
    async with application.lifespan(app):
        assert api_startup == []
        assert getattr(app.state, "engage_task", None) is None


@pytest.fixture
def fake_leader(monkeypatch):
    import app.platform.leases as leases
    calls = []

    async def run_as_leader(name, loop, get_db):
        calls.append(name)
        await asyncio.Event().wait()
    monkeypatch.setattr(leases, "run_as_leader", run_as_leader)
    monkeypatch.setattr(listing_reel, "_task", None)
    yield calls
    task = listing_reel._task
    if task is not None:
        task.cancel()


async def test_reel_routes_start_no_reel_worker_in_the_api_when_switched_off(fake_leader, monkeypatch):
    monkeypatch.setattr(application.settings, "run_background_loops", False)  # the same settings object ensure_worker reads
    assert listing_reel.ensure_worker() is None
    await asyncio.sleep(0)
    assert fake_leader == [] and listing_reel._task is None


async def test_reel_routes_start_the_reel_worker_by_default(fake_leader):
    task = listing_reel.ensure_worker()
    await asyncio.sleep(0)
    assert fake_leader == ["listing_reels"] and listing_reel.ensure_worker() is task  # idempotent
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


# ---- each runner records its heartbeat ------------------------------------------------------------------------------------
class LoopDb:
    """worker_heartbeats as in test_heartbeats; every other collection is empty (nothing paused)."""

    def __init__(self):
        from tests.platform_layer.test_heartbeats import HbCollection
        self.hb = HbCollection()

    def get_collection(self, name):
        if name == "worker_heartbeats":
            return self.hb

        class Empty:
            async def find_one(self, *a, **k):
                return None
        return Empty()


async def _spin(module, monkeypatch, db, loop=None):
    from app.platform import heartbeats
    heartbeats._last_write.clear()
    real_sleep = asyncio.sleep

    async def quick(_):
        await real_sleep(0)

    if hasattr(module, "get_database"):
        monkeypatch.setattr(module, "get_database", lambda: db)
    monkeypatch.setattr(module.asyncio, "sleep", quick)
    task = asyncio.create_task((loop or module.loop)())
    for _ in range(10):
        await real_sleep(0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    return db.hb.docs


async def test_calendar_runner_records_a_heartbeat_only_while_enabled(monkeypatch):
    from app.modules.calendar import runner
    monkeypatch.setattr(runner, "run_once", _noop_counts)
    monkeypatch.setattr(runner, "prerender_reels", lambda *a, **k: asyncio.sleep(0))
    monkeypatch.delenv("CALENDAR_ENABLED", raising=False)
    assert await _spin(runner, monkeypatch, LoopDb()) == {}
    monkeypatch.setenv("CALENDAR_ENABLED", "true")
    doc = (await _spin(runner, monkeypatch, LoopDb()))["calendar"]
    assert doc["last_start_at"] and doc["last_ok_at"] and "last_error" not in doc


async def test_newsroom_runner_records_a_failed_cycle_as_an_error(monkeypatch):
    from app.modules.newsroom import runner
    monkeypatch.setenv("NEWSROOM_ENABLED", "true")
    monkeypatch.setattr(runner, "default_stages", lambda: (_ for _ in ()).throw(RuntimeError("no stages")))

    class Store:
        def __init__(self, db):
            pass

        async def set_run(self, **k):
            pass
    monkeypatch.setattr(runner, "Store", Store)
    doc = (await _spin(runner, monkeypatch, LoopDb()))["newsroom"]
    assert doc["last_error"] == "RuntimeError: no stages" and "last_ok_at" not in doc


async def test_engage_runner_records_a_heartbeat_when_connected(monkeypatch):
    from app.modules.engage import runner
    monkeypatch.setenv("ENGAGE_ENABLED", "true")
    monkeypatch.setenv("META_PAGE_ID", "P1")
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "EAAB" + "x" * 30)

    class Svc:
        def __init__(self, *a, **k):
            pass

        async def run_once(self):
            return {}
    monkeypatch.setattr(runner, "EngageService", Svc)
    monkeypatch.setattr(runner, "EngageGraph", lambda cfg: None)
    monkeypatch.setattr(runner, "default_llm", lambda: None)
    monkeypatch.setattr(runner, "_ig", lambda cfg: None)
    monkeypatch.setattr(runner, "interest_resolver", lambda *a: None)
    doc = (await _spin(runner, monkeypatch, LoopDb()))["engage"]
    assert doc["last_start_at"] and doc["last_ok_at"]


async def test_reel_loop_records_a_heartbeat(monkeypatch):
    db = LoopDb()

    class Jobs:
        async def fail_stale(self):
            pass

        async def run_once(self):
            return False
    docs = await _spin(listing_reel, monkeypatch, db, lambda: listing_reel.loop(lambda: Jobs(), poll=0, get_db=lambda: db))
    assert docs["listing_reels"]["last_start_at"] and docs["listing_reels"]["last_ok_at"]


async def _noop_counts(*a, **k):
    return {}


async def test_worker_applies_the_startup_wiring_before_its_loops_run(events, monkeypatch):
    """The loops use callbacks wired at startup (app/wiring.py): the comment assistant's listing facts, the grounded
    answers' sample homes. The API wires them when its route list loads; the worker must wire them itself."""
    from app.modules.engage import service as engage_service
    from app.modules.knowledge import grounding

    monkeypatch.setattr(engage_service, "_listing_facts", {"from_docs": None})  # as in a fresh worker process
    monkeypatch.setattr(grounding, "_sources", {**grounding._sources, "evergreen_post": lambda slug: None})
    seen = {}

    async def loop():
        seen["listing_facts"] = engage_service._listing_facts["from_docs"]
        seen["evergreen_post"] = grounding._sources["evergreen_post"]
        await asyncio.Event().wait()

    stop = asyncio.Event()
    task = asyncio.create_task(worker.run(stop, table={"engage": loop}, get_db=lambda: LeaseDb()))
    for _ in range(50):
        await asyncio.sleep(0.01)
        if seen:
            break
    stop.set()
    await asyncio.wait_for(task, 5)
    from app.modules.calendar.library import BY_SLUG
    from app.modules.marketing.facts import Facts
    assert seen["listing_facts"] == Facts.from_docs
    assert seen["evergreen_post"] == BY_SLUG.get
