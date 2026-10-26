"""Fresh project pages in our areas, counted once a day (app/modules/seo/freshness.py; docs/plan/seo-system.md 8a, step 1)."""
from datetime import datetime, timedelta, timezone

from app.modules.newsroom.store import Store
from app.modules.seo import freshness

from ..fakes import FakeDb

NOW = datetime(2026, 10, 26, 9, 0, tzinfo=timezone.utc)


def project(slug, locality="kharadi", read_days_ago=5, **kw):
    return {"_id": slug.upper(), "page_slug": slug, "locality": locality, "promoter": "B", "completion_now": "2029-06-30",
            "details_checked_at": NOW - timedelta(days=read_days_ago) if read_days_ago is not None else None, **kw}


def test_a_page_read_within_the_window_is_fresh_and_an_older_one_is_not():
    out = freshness.share([project("a"), project("b", read_days_ago=50), project("c", read_days_ago=None)], NOW)
    assert (out["pages"], out["fresh"]) == (3, 1)
    assert [o["slug"] for o in out["oldest"]] == ["c", "b"]   # never read first, then the oldest


def test_only_live_pages_in_our_areas_count():
    docs = [project("ours"), project("elsewhere", locality="talegaon"), project("tower-b", cluster_primary="OURS"),
            project("finished", completion_now="2020-01-31"), project("thin", promoter="", pincode=""), project("noslug", page_slug=None)]
    out = freshness.share(docs, NOW)
    assert out["pages"] == 1 and out["by_area"] == {"kharadi": {"pages": 1, "fresh": 1}}


def test_a_failed_details_read_does_not_make_a_page_fresh():
    doc = project("a", read_days_ago=1, details_ok=False)
    assert freshness.share([doc], NOW)["fresh"] == 0


async def test_the_count_runs_once_a_day_onto_its_mark():
    store = Store(FakeDb())
    await store.projects.insert_one(project("a"))
    assert await freshness.run_once(store, NOW) == {"pages": 1, "fresh": 1}
    assert await freshness.run_once(store, NOW + timedelta(hours=3)) is None
    assert (await store.get_mark(freshness.MARK))["fresh"] == 1


async def test_an_empty_register_counts_nothing_and_leaves_no_mark():
    store = Store(FakeDb())
    assert await freshness.run_once(store, NOW) is None
    assert await store.get_mark(freshness.MARK) == {}
