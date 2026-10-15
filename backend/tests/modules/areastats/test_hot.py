"""Hot projects: signals with their evidence, the score, the daily refresh, outside signals, and enrichment going to hot projects first."""
from datetime import datetime, timedelta, timezone

import httpx

from app.modules.areastats import enrich, hot, pages, refresh

from .test_pages import FULL, seeded

NOW = datetime(2026, 10, 12, 6, 0, tzinfo=timezone.utc)


def days_ago(n):
    return NOW - timedelta(days=n)


def test_launch_counts_a_registration_within_a_year_only():
    s = hot.launch({"registered_on": "2026-07-14"}, NOW)
    assert s["source"] == "MahaRERA" and "2026-07-14" in s["evidence"] and 0.5 < s["value"] <= 1
    assert hot.launch({"registered_on": "2024-01-01"}, NOW) is None and hot.launch({}, NOW) is None


def test_bookings_are_homes_sold_inside_the_window():
    d = {"booked_history": [{"at": days_ago(200), "booked": 100}, {"at": days_ago(100), "booked": 120},
                            {"at": days_ago(40), "booked": 150}, {"at": days_ago(5), "booked": 162}]}
    s = hot.bookings(d, NOW)
    assert s["value"] == 42                                             # from the reading just before 90 days (120) to now (162)
    assert s["evidence"] == "42 homes booked between 2026-07-14 and 2026-10-07"   # the window's start, not the old reading's date
    assert "(10% of its 420 homes)" in hot.bookings({**d, "units_total": 420}, NOW)["evidence"]   # big and small projects compare
    assert hot.bookings({"booked_history": [{"at": days_ago(5), "booked": 10}]}, NOW) is None   # one reading says nothing yet
    assert hot.bookings({"booked_history": [{"at": days_ago(50), "booked": 10}, {"at": days_ago(5), "booked": 10}]}, NOW) is None


def test_news_counts_recent_linked_stories_with_their_titles():
    d = {"news": [{"title": "Lodha launches new tower in Kharadi", "source": "Hindustan Times", "published_at": days_ago(3)},
                  {"title": "Old story", "source": "x", "published_at": days_ago(90)},
                  {"title": "As text", "source": "Pune Mirror", "published_at": days_ago(10).isoformat()}]}
    s = hot.news(d, NOW)
    assert s["value"] == 2 and "new tower" in s["evidence"] and s["source"] == "Hindustan Times, Pune Mirror"


def test_search_counts_rising_impressions_double():
    assert hot.search({"gsc_impressions": 100}, NOW)["value"] == 100
    s = hot.search({"gsc_impressions": 300, "gsc_impressions_prev": 100}, NOW)
    assert s["value"] == 700 and "up from 100" in s["evidence"]
    assert hot.search({}, NOW) is None


def test_score_saturates_and_stays_within_100():
    assert hot.score({}) == 0
    one = hot.score({"news": {"value": 2}})
    assert 0 < one < hot.score({"news": {"value": 20}}) < 100
    every = {k: {"value": 1e9} for k in hot.WEIGHTS}
    assert hot.score(every) == 100


async def test_refresh_scores_our_projects_once_a_day_and_top_explains_why():
    db, store = await seeded(
        ("P1", "Camelot", "kharadi", {**FULL, "registered_on": "2026-08-01",
                                     "booked_history": [{"at": days_ago(80), "booked": 10}, {"at": days_ago(2), "booked": 40}]}),
        ("P2", "Quiet", "wagholi", {**FULL, "registered_on": "2019-01-01"}),
        ("P3", "Elsewhere", None, {"registered_on": "2026-08-01"}))             # not ours, not watched: not scored
    await pages.assign_all(store)
    out = await hot.refresh(store, NOW)
    assert out == {"projects": 2, "hot": 1}
    p1, p2 = await store.project("P1"), await store.project("P2")
    assert p1["hot_score"] >= hot.HOT_MIN and {s["signal"] for s in p1["hot_signals"]} == {"launch", "bookings"}
    assert "hot_score" not in p2 and "hot_score" not in await store.project("P3")
    assert await hot.refresh(store, NOW + timedelta(hours=3)) is None        # once a day
    top = await hot.top(store)
    assert [t["regno"] for t in top] == ["P1"] and top[0]["page"] == "/projects/camelot-kharadi"
    assert {w["source"] for w in top[0]["why"]} == {"MahaRERA"}
    assert await hot.top(store, area="wagholi") == []


async def test_an_outside_signal_adds_and_a_failing_one_is_skipped():
    db, store = await seeded(("P1", "Camelot", "kharadi", FULL), ("P2", "Quiet", "kharadi", FULL))
    seen = []

    async def social(store, projects, now):
        seen.append([p["_id"] for p in projects])
        return {"P2": {"value": 5, "evidence": "5 reels", "source": "Instagram"}, "NOT_OURS": {"value": 9, "evidence": "", "source": ""}}

    async def broken(store, projects, now):
        raise RuntimeError("quota")
    hot.add_signal("social", social)
    hot.add_signal("broken", broken)
    assert (await hot.refresh(store, NOW))["projects"] == 2
    assert (await store.project("P2"))["hot_signals"][0]["evidence"] == "5 reels" and "hot_score" not in await store.project("P1")


async def test_youtube_needs_a_key_and_counts_only_videos_naming_the_project(monkeypatch):
    asked = []

    def handler(req):
        asked.append(req.url.params)
        return httpx.Response(200, json={"items": [
            {"snippet": {"title": "Lodha Camelot Kharadi site visit", "channelTitle": "Pune Homes"}},
            {"snippet": {"title": "Camelot Kharadi price review", "channelTitle": "Realty Talk"}},
            {"snippet": {"title": "Best projects in Kharadi", "channelTitle": "Other"}}]})
    fn = hot.youtube_signal(transport=httpx.MockTransport(handler))
    projects = [{"_id": "P1", "name": "Camelot", "locality": "kharadi"}]
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    assert await fn(None, projects, NOW) == {} and asked == []
    monkeypatch.setenv("YOUTUBE_API_KEY", "k")
    out = await fn(None, projects, NOW)
    assert out["P1"]["value"] == 2 and "Pune Homes, Realty Talk" in out["P1"]["evidence"]
    assert asked[0]["q"] == '"Camelot" Kharadi Pune' and asked[0]["publishedAfter"] == "2026-09-12T06:00:00Z"


async def test_enrichment_takes_hot_projects_first_and_refreshes_them_sooner():
    db, store = await seeded(("A", "Alpha", "wagholi", {**FULL, "gsc_impressions": 400}),
                             ("H", "Hot", "wagholi", {**FULL, "hot_score": 60}),
                             ("W", "Warm", "wagholi", {**FULL, "hot_score": hot.HOT_MIN - 1}))
    await pages.assign_all(store)
    assert (await enrich.next_project(store, NOW))["_id"] == "H"
    await store.set_project("H", enriched_at=days_ago(enrich.HOT_REFRESH_DAYS - 1), enrichment={"score": "4/4"})
    assert (await enrich.next_project(store, NOW))["_id"] == "H"              # hot, being built, no profile yet: still first
    await store.set_project("H", profile={"at": NOW})
    assert (await enrich.next_project(store, NOW))["_id"] == "A"              # warm is not hot: Google impressions come next
    await store.set_project("H", enriched_at=days_ago(enrich.HOT_REFRESH_DAYS), enrichment={"score": "4/4"})
    assert (await enrich.next_project(store, NOW))["_id"] == "H"


def test_details_keep_a_dated_homes_booked_reading_only_when_it_changes():
    first = refresh._booked({}, {"units_booked": 10}, NOW)
    assert first == {"booked_history": [{"at": NOW, "booked": 10}]}
    assert refresh._booked(first, {"units_booked": 10}, NOW) == {}
    assert len(refresh._booked(first, {"units_booked": 12}, NOW)["booked_history"]) == 2
    assert refresh._booked({}, {"units_booked": None}, NOW) == {}


def test_search_name_is_what_people_call_the_project():
    assert hot.search_name("LODHA CAMELOT PHASE 1 - TOWER A") == "Lodha Camelot"
    assert hot.search_name("Rohan Abhilasha 4 Wing C") == "Rohan Abhilasha 4"
    assert hot.search_name("Kolte Patil Life Republic Sector R10 (Plot 4)") == "Kolte Patil Life Republic"
    assert hot.search_name("Om Tower") == ""                      # too short to search without unrelated matches


async def test_youtube_stops_on_a_spent_quota_and_skips_one_failed_search(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "k")
    asked = []

    def handler(req):
        asked.append(req.url.params["q"])
        if "Alpha" in req.url.params["q"]:
            return httpx.Response(500)
        if "Bravo" in req.url.params["q"]:
            return httpx.Response(200, json={"items": [{"snippet": {"title": "Bravo Heights tour", "channelTitle": "C"}}]})
        return httpx.Response(403)
    fn = hot.youtube_signal(transport=httpx.MockTransport(handler))
    projects = [{"_id": n[0], "name": n, "locality": "wagholi"} for n in ("Alpha Homes", "Bravo Heights", "Charlie Park", "Delta Greens")]
    out = await fn(None, projects, NOW)
    assert list(out) == ["B"] and len(asked) == 3                 # Alpha failed alone; Charlie's 403 stopped before Delta
