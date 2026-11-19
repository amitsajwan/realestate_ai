"""The system watch (admin/watch.py): the owner hears when something stops, once, again daily while it lasts, and when it is
fixed; a morning report every day; an outside check that fails when the watch itself is quiet."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.admin import health, router as ar, watch
from app.modules.areastats import budget, owner
from app.modules.areastats.webfacts import NO_ANSWER
from app.platform import heartbeats

from ..fakes import FakeDb

NOW = datetime(2026, 11, 19, 2, 0, tzinfo=timezone.utc)      # 07:30 in India, before the morning report
MORNING = datetime(2026, 11, 19, 3, 45, tzinfo=timezone.utc)  # 09:15 in India

OUT = {"key": "google_search", "label": "Google search (Serper)", "status": "bad", "text": "Out of credits (0)", "fix": "Top up"}
FINE = {"key": "google_search", "label": "Google search (Serper)", "status": "ok", "text": "2499 searches left", "fix": ""}
OFF = {"key": "messenger", "label": "Messenger", "status": "warn", "text": "DM replies are off", "fix": ""}


class Told:
    def __init__(self):
        self.said = []

    async def __call__(self, kind, summary):
        self.said.append((kind, summary))


async def test_a_problem_is_told_once_then_daily_while_it_lasts_then_fixed():
    db, told = FakeDb(), Told()
    await watch.watch_once(db, NOW, [OUT, OFF], told)
    assert told.said == [("system_alert", "Google search (Serper): Out of credits (0). Fix: Top up")]
    await watch.watch_once(db, NOW + timedelta(minutes=15), [OUT, OFF], told)
    assert len(told.said) == 1                                       # every 15 minutes would be noise
    await watch.watch_once(db, NOW + watch.REPEAT, [OUT, OFF], told)
    assert len(told.said) == 2 and told.said[-1][0] == "system_alert"   # still out a day later: said again
    await watch.watch_once(db, NOW + watch.REPEAT + timedelta(minutes=15), [FINE, OFF], told)
    assert told.said[-1] == ("system_alert", "Fixed: Google search (Serper) is working again")


async def test_a_switched_off_feature_is_no_alarm_but_low_credits_are():
    db, told = FakeDb(), Told()
    low = {**FINE, "status": "warn", "text": "120 searches left"}
    await watch.watch_once(db, NOW, [OFF, low], told)
    assert [s for _, s in told.said] == ["Google search (Serper): 120 searches left"]


async def test_a_problem_getting_worse_is_told_at_once():
    db, told = FakeDb(), Told()
    await watch.watch_once(db, NOW, [{**OUT, "status": "warn", "text": "120 searches left"}], told)
    await watch.watch_once(db, NOW + timedelta(minutes=15), [OUT], told)
    assert len(told.said) == 2


async def test_the_morning_report_comes_once_a_day_after_nine_in_india():
    db, told = FakeDb(), Told()
    await watch.watch_once(db, NOW, [FINE], told)
    assert told.said == []
    await watch.watch_once(db, MORNING, [FINE], told)
    await watch.watch_once(db, MORNING + timedelta(hours=3), [FINE], told)
    assert told.said == [("system_daily", "All 1 checks fine. Google search (Serper): 2499 searches left")]
    await watch.watch_once(db, MORNING + timedelta(days=1), [FINE], told)
    assert len(told.said) == 2


def test_the_morning_report_leads_with_what_needs_the_owner():
    assert watch.daily_report([OUT, OFF]).startswith("1 need you: Google search (Serper)")


def test_a_stopped_or_failing_loop_is_named_and_a_slow_round_is_not():
    beats = {"seo": {"last_ok_at": NOW - timedelta(hours=3)},
             "project_enrich": {"last_start_at": NOW - timedelta(minutes=14)},            # one long round, not stopped
             "radar": {"last_ok_at": NOW - timedelta(hours=2), "last_error_at": NOW - timedelta(minutes=5), "last_error": "boom"}}
    intervals = {"seo": 900.0, "project_enrich": 180.0, "radar": 600.0, "press": None, "engage": 60.0}
    row = health.loops_row(beats, intervals, NOW)
    assert row["status"] == "bad"
    assert "seo (3 hours)" in row["text"] and "engage (never ran)" in row["text"] and "radar: boom" in row["text"]
    assert "project_enrich" not in row["text"] and "press" not in row["text"]
    fine = health.loops_row({"seo": {"last_ok_at": NOW - timedelta(minutes=5)}}, {"seo": 900.0}, NOW)
    assert fine["status"] == "ok" and fine["text"] == "All 1 running"


def test_reading_that_comes_back_empty_is_an_alarm():
    assert health.reading_row(True, {"reads": 0})["status"] == "bad"
    assert health.reading_row(True, {"reads": 40, "with_sites": 30, "no_answer": 20})["status"] == "bad"
    assert health.reading_row(True, {"reads": 40, "with_sites": 30, "no_answer": 7})["status"] == "warn"
    assert health.reading_row(True, {"reads": 4, "with_sites": 4, "no_answer": 4})["status"] == "ok"    # too few to judge
    assert health.reading_row(False, {"reads": 0}) is None                                                # reading switched off
    refused = health.reading_row(True, {"reads": 40, "with_sites": 30, "no_answer": 0, "paid_refusing": ["lite"], "free_calls": 400})
    assert refused["status"] == "bad" and "ai.studio/spend" in refused["fix"]


async def test_reading_counts_the_last_day_from_the_records():
    db = FakeDb()
    projects = db.get_collection("projects")
    answered = {"web_facts": {"at": NOW, "read": [{"why": "2 facts"}]}, "enrichment": {"steps": {"web": {"checked": "2 facts from 1 of 2 sites"}}}}
    unanswered = {"web_facts": {"at": NOW, "read": [{"why": NO_ANSWER}]},
                  "enrichment": {"steps": {"web": {"checked": f"0 facts from 0 of 2 sites; {NO_ANSWER} on 2 of 2 pages"}}}}
    await projects.insert_one({"_id": "A", "enriched_at": NOW, **answered, "search_state": {"in": True, "at": NOW}})
    await projects.insert_one({"_id": "B", "enriched_at": NOW, **unanswered})
    await projects.insert_one({"_id": "C", "enriched_at": NOW, "cluster_primary": "A", **unanswered})     # a tower: read on A
    await projects.insert_one({"_id": "D", "enriched_at": NOW - timedelta(days=2), **unanswered})        # not today
    await db.get_collection(budget.USAGE).insert_one({"_id": budget.day_of(NOW), "free_calls": 400, "pools": {
        "lite": {"streak": budget.REFUSED_AFTER, "failed_at": NOW - timedelta(minutes=5)},
        "gemini": {"streak": budget.REFUSED_AFTER, "failed_at": NOW - timedelta(hours=5)}}})       # long ago: tried again since
    r = await owner.reading(db, NOW)
    assert (r["reads"], r["with_sites"], r["no_answer"], r["into_search"]) == (2, 2, 1, 1)
    assert r["paid_refusing"] == ["lite"] and r["free_calls"] == 400


async def test_the_watch_works_out_the_loops_row_and_tells_the_owner():
    db, told = FakeDb(), Told()
    await heartbeats.record(lambda: db, "seo", {"last_ok_at": NOW - timedelta(hours=5)})

    async def rows():
        kept = await db.get_collection(watch.COLLECTION).find_one({"_id": "_loops"})
        return [kept["row"]]
    out = await watch.cycle(db, NOW, {"seo": 900.0}, tell=told, rows_of=rows)
    assert out["alarms"] == ["loops"] and "seo" in told.said[0][1]


async def test_the_outside_check_fails_when_the_watch_is_quiet_or_something_is_red():
    db = FakeDb()
    assert (await watch.alive(db, NOW)) == {"ok": False, "failing": ["system_watch"]}
    await heartbeats.record(lambda: db, watch.NAME, {"last_ok_at": NOW - timedelta(minutes=10)})
    assert (await watch.alive(db, NOW))["ok"]
    await watch.watch_once(db, NOW, [OUT], Told())
    assert (await watch.alive(db, NOW)) == {"ok": False, "failing": ["google_search"]}
    assert not (await watch.alive(db, NOW + timedelta(hours=1)))["ok"]     # the watch stopped: that alone fails the check


def test_the_public_check_answers_503_when_not_ok(monkeypatch):
    async def bad(db, now):
        return {"ok": False, "failing": ["loops"]}
    monkeypatch.setattr(watch, "alive", bad)
    monkeypatch.setattr(ar, "get_database", lambda: None)
    app = FastAPI()
    app.include_router(ar.public_router, prefix="/public")
    r = TestClient(app).get("/public/alive")
    assert r.status_code == 503 and r.json() == {"ok": False, "failing": ["loops"]}
    assert r.headers["cache-control"] == "no-store"


def test_alerts_ring_the_phone():
    from app.modules.notifications.push import TITLES
    assert "system_alert" in TITLES and "system_daily" in TITLES

