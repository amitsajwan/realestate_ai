"""The renderer's drain works the marketing-run queue it is handed (app.worker passes propertyfacts.jobs.default_runs)."""
from datetime import datetime, timedelta, timezone

from app.modules.calendar import runner as calendar_runner
from app.modules.reels import listing_reel, render_job

from ..fakes import FakeDb


NOW = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)
NAIVE = NOW.replace(tzinfo=None)


class Queue:
    def __init__(self, items):
        self.items, self.cleaned = items, False

    async def fail_stale(self):
        self.cleaned = True

    async def run_once(self):
        return self.items.pop() if self.items else None


async def test_drain_cleans_up_then_takes_the_given_queue_until_it_stays_empty(monkeypatch):
    runs, reels = Queue(["r1", "r2"]), Queue(["w1"])
    monkeypatch.setattr(listing_reel, "default_jobs", lambda: reels)
    async def no_prerender(store, now):
        return 0
    monkeypatch.setattr(calendar_runner, "prerender_reels", no_prerender)
    monkeypatch.setattr(render_job, "IDLE_WAIT_S", 0)
    assert await render_job.drain(FakeDb(), lambda: runs) == 2   # two rounds took work (r2 + w1, then r1)
    assert runs.cleaned and reels.cleaned and not runs.items and not reels.items


def test_an_execution_that_never_started_stops_blocking_the_renderer_after_the_jobs_limit():
    dead = {"name": "renderer-mpm4q", "createTime": "2026-11-05T09:50:19.330716Z", "completionStatus": "EXECUTION_PENDING"}
    assert render_job._alive(dead, NOW) is False


def test_a_recent_execution_with_no_completion_time_counts_as_running():
    assert render_job._alive({"createTime": "2026-11-07T11:30:00.000000Z"}, NOW) is True


def test_a_finished_execution_or_none_is_not_running():
    assert render_job._alive({"createTime": "2026-11-07T11:30:00Z", "completionTime": "2026-11-07T11:40:00Z"}, NOW) is False
    assert render_job._alive({}, NOW) is False


def test_an_unreadable_time_never_starts_a_second_renderer():
    assert render_job._alive({"createTime": "soon"}, NOW) is True


async def test_the_owner_hears_once_about_runs_queued_past_the_limit():
    db = FakeDb()
    runs = db.get_collection("marketing_runs")
    await runs.insert_one({"_id": "old", "status": "queued", "created_at": NAIVE - timedelta(hours=2)})
    await runs.insert_one({"_id": "new", "status": "queued", "created_at": NAIVE - timedelta(minutes=5)})
    await runs.insert_one({"_id": "done", "status": "done", "created_at": NAIVE - timedelta(hours=2)})
    said, told = [], set()

    async def alert(db, summary):
        said.append(summary)

    assert await render_job.warn_of_stuck_runs(db, alert, told, NOW) == 1
    assert await render_job.warn_of_stuck_runs(db, alert, told, NOW) == 0
    assert said == ["1 marketing run waiting over 30 minutes. The renderer may be stuck."]


async def test_wiring_gives_the_loop_an_alert_that_reaches_the_owners_notifications(monkeypatch):
    from app.wiring import _tell_owner_of_stuck_runs, wire
    monkeypatch.setenv("ENGAGE_OWNER_AGENT_ID", "owner")
    wire()
    assert render_job._alert is _tell_owner_of_stuck_runs
    db = FakeDb()
    await render_job._alert(db, "2 marketing runs waiting")
    [note] = await db.get_collection("notifications").find({"agent_id": "owner"}).to_list(5)
    assert note["kind"] == "marketing_stuck" and note["summary"] == "2 marketing runs waiting"


async def test_a_queued_brochure_read_starts_the_renderer_and_one_waiting_for_credit_does_not():
    db = FakeDb()
    await db.get_collection("brochure_jobs").insert_one({"_id": "a", "status": "queued", "not_before": NAIVE + timedelta(hours=6)})
    assert "brochure_reads" not in await render_job.queued(db, NOW)
    await db.get_collection("brochure_jobs").insert_one({"_id": "b", "status": "queued", "not_before": NAIVE - timedelta(minutes=1)})
    assert (await render_job.queued(db, NOW))["brochure_reads"] == 1


async def test_drain_takes_the_brochure_queue_too(monkeypatch):
    runs, reels, reads = Queue([]), Queue([]), Queue(["b1"])
    monkeypatch.setattr(listing_reel, "default_jobs", lambda: reels)

    async def no_prerender(store, now):
        return 0
    monkeypatch.setattr(calendar_runner, "prerender_reels", no_prerender)
    monkeypatch.setattr(render_job, "IDLE_WAIT_S", 0)
    assert await render_job.drain(FakeDb(), lambda: runs, lambda: reads) == 1
    assert reads.cleaned and not reads.items
