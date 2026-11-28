"""Drive times from Google's Routes API: four reads per hub (9 am and 6 pm, Google's low and high), a monthly cap, and the last
good times kept when a read fails."""
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.modules.neighbourhood import budget, runner
from app.modules.neighbourhood.config import Config
from app.modules.neighbourhood.researchers import commute
from app.modules.neighbourhood.researchers.base import Context, ViewContext
from app.modules.neighbourhood.store import Store
from tests.modules.neighbourhood.helpers import NOW, db_with, project

CFG = Config(google_key="k", routes=True, route_elements_per_month=100, places_per_cycle=5)


def _kharadi():
    return db_with(project("A", pin=(18.550, 73.940)), project("B", pin=(18.552, 73.942)), project("C", pin=(18.551, 73.941)))


def routes(calls):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        pessimistic = body["trafficModel"] == "PESSIMISTIC"
        out = []
        for o in range(len(body["origins"])):
            for d in range(len(body["destinations"])):
                i = max(o, d)   # one side is the place, the other the hubs
                secs = 600 * (i + 1) + (420 if pessimistic else 0)
                out.append({"originIndex": o, "destinationIndex": d, "duration": f"{secs}s", "distanceMeters": 5000 * (i + 1),
                            "condition": "ROUTE_EXISTS", "status": {}})
        return httpx.Response(200, json=out)
    return handler


def test_departures_are_the_next_weekday_at_9_and_18_ist():
    friday_evening = datetime(2026, 11, 27, 14, 0, tzinfo=timezone.utc)   # 19:30 IST, Friday
    assert commute.departure(friday_evening, commute.AM) == "2026-11-30T03:30:00Z"   # Monday 09:00 IST
    assert commute.departure(friday_evening, commute.PM) == "2026-11-30T12:30:00Z"
    assert commute.departure(datetime(2026, 11, 30, 2, 0, tzinfo=timezone.utc), commute.AM) == "2026-11-30T03:30:00Z"


def test_targets_are_the_four_nearest_hubs_and_the_airport():
    got = commute.targets(18.551, 73.941)
    assert len(got) == 5 and got[-1].kind == "airport" and got[0].slug in ("eon-it-park-kharadi", "world-trade-center-kharadi")
    assert sum(1 for h in got if h.kind == "airport") == 1


@pytest.mark.asyncio
async def test_a_place_is_measured_with_low_and_high_minutes_both_ways_and_the_reads_are_counted():
    db = await _kharadi()
    calls = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(routes(calls))) as http:
        found = await commute.RESEARCHER.run(Context(db=db, store=Store(db), now=NOW, cfg=CFG, http=http), "kharadi")
    assert len(calls) == 4 and {c["trafficModel"] for c in calls} == {"OPTIMISTIC", "PESSIMISTIC"}
    assert all(c["routingPreference"] == "TRAFFIC_AWARE_OPTIMAL" for c in calls)
    first = found.data["rows"][0]
    assert first["am"] == [10, 17] and first["pm"] == [10, 17] and first["km"] == 5.0
    assert len(found.data["rows"]) == 5
    assert await budget.used(Store(db), NOW) == 20


@pytest.mark.asyncio
async def test_over_the_monthly_cap_the_place_waits_and_nothing_is_asked():
    db = await _kharadi()
    await budget.spend(Store(db), NOW, 90)
    calls = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(routes(calls))) as http:
        ctx = Context(db=db, store=Store(db), now=NOW, cfg=CFG, http=http)
        with pytest.raises(budget.NotNow):
            await commute.RESEARCHER.run(ctx, "kharadi")
    assert calls == []
    assert await budget.used(Store(db), NOW + timedelta(days=5)) == 0   # December starts at zero


@pytest.mark.asyncio
async def test_the_loop_does_not_mark_a_place_tried_when_the_budget_is_spent(monkeypatch):
    db = await _kharadi()
    await budget.spend(Store(db), NOW, 95)

    async def two(db):
        return ["kharadi", "wagholi"]
    monkeypatch.setattr(runner.places, "all_places", two)
    monkeypatch.setattr(runner, "REGISTRY", (commute.RESEARCHER,))
    async with httpx.AsyncClient(transport=httpx.MockTransport(routes([]))) as http:
        counts = await runner.run_once(db, NOW, http=http, cfg=CFG)
    assert counts["commute"]["waiting"] == 1 and counts["commute"]["ran"] == 0
    assert await Store(db).tried("commute") == {}


@pytest.mark.asyncio
async def test_a_failed_read_keeps_the_last_good_times(monkeypatch):
    db = await _kharadi()
    store = Store(db)
    await store.put("commute", "kharadi", {"rows": [{"hub": "EON", "hub_slug": "eon-it-park-kharadi", "km": 3, "am": [8, 12],
                                                     "pm": [9, 14]}]}, [], NOW - timedelta(days=40))

    async def one(db):
        return ["kharadi"]
    monkeypatch.setattr(runner.places, "all_places", one)
    monkeypatch.setattr(runner, "REGISTRY", (commute.RESEARCHER,))
    failing = httpx.MockTransport(lambda r: httpx.Response(403, json={"error": {"status": "PERMISSION_DENIED"}}))
    async with httpx.AsyncClient(transport=failing) as http:
        counts = await runner.run_once(db, NOW, http=http, cfg=CFG)
    doc = await store.get("commute", "kharadi")
    assert counts["commute"]["failed"] == 1 and doc["ok"] is False and doc["data"]["rows"][0]["am"] == [8, 12]


def test_commute_is_off_without_a_key_or_its_switch():
    assert not commute.RESEARCHER.enabled(Config(google_key="", routes=True))
    assert not commute.RESEARCHER.enabled(Config(google_key="k", routes=False))
    assert commute.RESEARCHER.enabled(CFG)


ROWS = {"rows": [{"hub": "Hinjawadi Phase 1", "hub_slug": "hinjawadi-phase-1", "km": 35, "am": [60, 95], "pm": [70, 100]},
                 {"hub": "EON IT Park, Kharadi", "hub_slug": "eon-it-park-kharadi", "km": 3, "am": [8, 12], "pm": [9, 14]},
                 {"hub": "Pune Airport", "hub_slug": "pune-airport", "km": 9, "am": [20, 30], "pm": [22, 35]}]}


def test_rows_read_fastest_first_and_three_hubs_make_a_page():
    block = commute.RESEARCHER.present(ROWS, ViewContext(place="kharadi", lat=18.55, lon=73.94))
    assert [r["hub_slug"] for r in block["rows"]] == ["eon-it-park-kharadi", "pune-airport", "hinjawadi-phase-1"]
    assert block["page_ready"] and block["measured_from"] == "place" and block["from"] == "the Kharadi centre"
    assert "pin_km" not in block["rows"][0]
    assert commute.RESEARCHER.present({"rows": ROWS["rows"][:2]}, ViewContext(place="kharadi"))["page_ready"] is False


def test_on_a_pinned_project_the_place_times_show_with_the_pins_own_straight_line_km():
    view = ViewContext(place="kharadi", lat=18.5518, lon=73.9511, project={"page_slug": "x"})
    block = commute.RESEARCHER.present(ROWS, view)
    eon = block["rows"][0]
    assert eon["am"] == [8, 12] and eon["pin_km"] == 0.0 and block["measured_from"] == "place"


def test_no_rows_no_block():
    assert commute.RESEARCHER.present({"rows": []}, ViewContext(place="kharadi")) is None
