"""The renderer's drain works the marketing-run queue it is handed (app.worker passes propertyfacts.jobs.default_runs)."""
from app.modules.calendar import runner as calendar_runner
from app.modules.reels import listing_reel, render_job

from ..fakes import FakeDb


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
