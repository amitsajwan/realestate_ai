"""The research module's frame: the loop picks what is due, keeps the last good data when a run fails, and the views hide
blocks a researcher has nothing for."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules import neighbourhood
from app.modules.neighbourhood import runner, views
from app.modules.neighbourhood.researchers import Found, Researcher
from app.modules.neighbourhood.store import CITY, Store
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 28, 9, 0, tzinfo=timezone.utc)


def _r(kind="x", every=timedelta(days=30), scope="place"):
    async def run(ctx, place):
        return None
    return Researcher(kind=kind, every=every, run=run, present=lambda d, v: None, scope=scope)


def test_the_module_exports_its_views_and_collections():
    assert neighbourhood.AREA_RESEARCH == "area_research"
    assert callable(neighbourhood.area_view) and callable(neighbourhood.project_view)


def test_due_runs_never_tried_places_first_then_the_oldest_within_the_limit():
    tried = {"a": NOW - timedelta(days=40), "b": NOW - timedelta(days=31), "c": NOW - timedelta(days=1)}
    assert runner.due(_r(), ["a", "b", "c", "d"], tried, NOW, 2) == ["d", "a"]
    assert runner.due(_r(), ["c"], tried, NOW, 5) == []


def test_a_city_wide_researcher_runs_once_for_all_of_pune():
    assert runner.due(_r(scope="city"), ["a", "b"], {}, NOW, 5) == [CITY]
    assert runner.due(_r(scope="city"), ["a"], {CITY: NOW - timedelta(days=2)}, NOW, 5) == []


@pytest.mark.asyncio
async def test_a_failed_run_keeps_the_last_good_data():
    db = FakeDb()
    store = Store(db)
    await store.put("rent", "kharadi", {"rows": [1]}, [{"name": "x", "read_on": "2026-11-01"}], NOW - timedelta(days=40))
    await store.put("rent", "kharadi", None, [], NOW, ok=False, note="timeout")
    doc = await store.get("rent", "kharadi")
    assert doc["data"] == {"rows": [1]} and doc["ok"] is False and doc["tried_at"] == NOW


@pytest.mark.asyncio
async def test_a_place_with_nothing_researched_has_no_view(monkeypatch):
    monkeypatch.setattr(views, "_changes", None)   # no tracker lines either (wiring passes newsroom's in)
    assert await views.area_view(FakeDb(), "kharadi", NOW) is None
