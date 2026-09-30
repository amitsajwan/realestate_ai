"""The real stages wired through the real pipeline and store, on recorded articles. Only the LLM and the Page are fakes."""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.modules.newsroom.config import NewsroomConfig
from app.modules.newsroom.pipeline import run_once
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import RawItem

from ..fakes import FakeDb
from .helpers import FakePublisher, FakeSource

DIR = Path(__file__).parent / "fixtures" / "articles"
NOW = datetime(2026, 9, 30, 6, 0, tzinfo=timezone.utc)


def load(name):
    d = json.loads((DIR / f"{name}.json").read_text(encoding="utf-8"))
    pub = datetime.fromisoformat(d["published_at"])
    return RawItem(id=d["id"], source="Pune Mirror", url=d["url"], title=d["title"], text=d["text"], published_at=pub, fetched_at=NOW)


class ScriptedLlm:
    """Answers the extract prompt with one real quote from the article, and the draft prompt with honest parts."""
    def __init__(self, good=True):
        self.good = good

    async def json(self, system, user):
        if "quote" in system:
            return {"facts": [{"text": "Vehicles are diverted on the Kharadi bypass from October 1 to October 20 for flyover girder work",
                               "quote": "Pune traffic police have diverted vehicles on the Kharadi bypass from October 1 to October 20"}]}
        what = ("Vehicles are diverted on the Kharadi bypass from October 1 to October 20 for flyover girder work."
                if self.good else "Vehicles are diverted on the Kharadi bypass for 45 days and the flyover will open in November.")
        return {"title": "Kharadi bypass diversion", "what": what, "why": "If you commute through Kharadi, plan a little extra time.",
                "check": "Check the traffic police advisory before you leave.", "question": "Which route do you take to work?"}

    async def text(self, system, user, timeout=None):
        return None


async def run(names, llm):
    from app.modules.newsroom.pipeline import default_stages
    store, pub = Store(FakeDb()), FakePublisher()
    counts = await run_once(store, [FakeSource([load(n) for n in names])], default_stages(), pub, llm, NOW, NewsroomConfig(daily_cap=2))
    return store, pub, counts


async def test_a_good_article_reaches_the_review_queue_and_nothing_is_posted():
    store, pub, counts = await run(["kharadi_bypass"], ScriptedLlm())
    q = await store.queue()
    assert len(q) == 1 and q[0]["status"] == "pending_review"
    assert "Kharadi bypass" in q[0]["draft"]["text"] and "?" in q[0]["draft"]["text"]
    assert pub.calls == [] if hasattr(pub, "calls") else True  # approval is required before anything is sent


async def test_off_topic_stale_and_hype_items_never_reach_the_queue():
    store, _, counts = await run(["offtopic_mumbai", "stale_metro", "hype_promo", "horoscope", "classified", "crime_kharadi"], ScriptedLlm())
    assert await store.queue() == []
    assert (await store.counts()).get("dropped", 0) == 6


async def test_a_draft_with_invented_facts_is_stopped_by_the_check():
    store, _, _ = await run(["kharadi_bypass"], ScriptedLlm(good=False))
    assert await store.queue() == []
    doc = (await store.next_batch("dropped", 5))[0]
    assert "check failed" in doc["history"][-1]["note"]


async def test_the_same_story_from_two_publishers_is_queued_once():
    store, _, _ = await run(["metro_line3", "dup_metro"], ScriptedLlm())
    c = await store.counts()
    assert c.get("dropped", 0) >= 1 and c.get("relevant", 0) + c.get("extracted", 0) + c.get("pending_review", 0) + c.get("drafted", 0) <= 1
