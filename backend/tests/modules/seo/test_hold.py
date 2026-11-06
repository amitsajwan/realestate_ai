"""No new title or description fixes while the site settles after the drop of 2026-10-26 (seo/actions.HOLD_UNTIL)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import searchconsole
from app.modules.newsroom.store import Store
from app.modules.seo import actions, targets

from ..fakes import FakeDb

NOW = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)


def test_fixes_wait_until_the_hold_ends():
    assert actions.on_hold(NOW)
    assert actions.on_hold(actions.HOLD_UNTIL - timedelta(seconds=1))
    assert not actions.on_hold(actions.HOLD_UNTIL)


async def test_titles_stay_as_they_are_during_the_hold(monkeypatch):
    monkeypatch.setattr(searchconsole, "key", lambda: {"client_email": "x"})
    store = Store(FakeDb())
    assert await targets.run_once(store, NOW) == {"held": True}
    assert await targets.run_once(store, NOW + timedelta(minutes=5)) is None   # once a round, like before


async def test_the_days_numbers_and_competing_pages_go_on_during_the_hold(monkeypatch):
    monkeypatch.setattr(searchconsole, "key", lambda: {"client_email": "x"})
    db = FakeDb()
    await db.get_collection(targets.DEMAND).insert_one({"_id": "aldea", "phrase": "aldea", "gsc": {"impressions": 9, "position": 7.0,
                                                                                                    "pages": ["/projects/a", "/projects/b"]}})
    store = Store(db)
    assert await targets.run_once(store, NOW) == {"held": True}
    assert len((await store.get_mark(targets.MARK))["history"]) == 1
    assert (await store.get_mark(targets.CONFLICTS))["total"] == 1
    await targets.run_once(store, NOW + timedelta(days=1))
    assert len((await store.get_mark(targets.MARK))["history"]) == 2


async def test_page_one_also_counts_the_pages_in_search_today(monkeypatch):
    """Google keeps showing pages we took out of search until it reads them again, so "page one" alone overstates what we hold."""
    monkeypatch.setattr(searchconsole, "key", lambda: {"client_email": "x"})
    db = FakeDb()
    ready = {"locality": "kharadi", "completion_now": "2029-06-30", "promoter": "Kolte Patil", "page_text": "Written.",
             "prices": {"rows": [{"size": "2 BHK"}]}, "gsc_read_at": NOW, "gsc_position": 4.0, "gsc_impressions": 30}
    await db.get_collection("projects").insert_one({"_id": "P1", "page_slug": "a", **ready})
    await db.get_collection("projects").insert_one({"_id": "P2", "page_slug": "b", **ready, "page_text": ""})   # thin: out of search
    store = Store(db)
    await targets.run_once(store, NOW)
    snap = (await store.get_mark(targets.MARK))["history"][-1]
    assert (snap["page_one"], snap["page_one_listed"]) == (2, 1)
