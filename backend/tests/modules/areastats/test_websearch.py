"""Google search results as a hot-projects signal: searches in turn, places and marketers, discovered project numbers, the provider."""
import json
from datetime import datetime, timedelta, timezone

import httpx

from app.modules.areastats import hot, websearch

from .test_pages import FULL, seeded

NOW = datetime(2026, 10, 12, 6, 0, tzinfo=timezone.utc)


def r(title, link, pos, snippet="", ad=False):
    return {"title": title, "link": link, "snippet": snippet, "position": pos, "ad": ad}


def google(answers, asked):
    """A fake provider: query -> results (anything else: none)."""
    async def search(q):
        asked.append(q)
        return answers.get(q, [])
    return search


KHARADI_NEW = [r("New launch projects in Kharadi: Lodha Camelot, Godrej ...", "https://www.housiey.com/kharadi", 2),
               r("Lodha Camelot Kharadi Pune | Price & Floor Plans", "https://lodha-camelot.example-partner.in/", 4,
                 "Project RERA Number : PR1260002501386 | PR1260002501413. Agent RERA A51900029955"),
               r("Some other project", "https://www.99acres.com/x", 6)]
CAMELOT = [r("Lodha Camelot Kharadi - 3 & 4.5 BHK from 2.25 Cr", "https://www.magicbricks.com/lodha-camelot", 1),
           r("Lodha Camelot", "https://www.avasetu.in/projects/lodha-camelot-kharadi", 2),
           r("Lodha Camelot Kharadi | Official partner", "https://ads.example-cp.com/camelot", 0, ad=True),
           r("Lodha Camelot review", "https://www.youtube.com/watch?v=1", 3)]


async def test_one_day_searches_areas_in_turn_then_the_hottest_projects_and_scores_them():
    db, store = await seeded(("PR1260002501399", "LODHA CAMELOT PHASE 1 - TOWER C", "kharadi", FULL),
                             ("P2", "Quiet Homes Wing B", "kharadi", FULL),
                             ("P3", "Om", "wagholi", FULL))                       # too short a name to search for
    asked = []
    answers = {"new launch projects in Kharadi Pune": KHARADI_NEW, "Lodha Camelot Kharadi Pune": CAMELOT}
    projects = [await store.project("PR1260002501399"), await store.project("P2"), await store.project("P3")]
    out = await websearch.signal(google(answers, asked))(store, projects, NOW)

    assert asked[:websearch.AREA_PER_DAY] == [q["q"] for q in websearch.area_queries()[:websearch.AREA_PER_DAY]]
    assert asked[websearch.AREA_PER_DAY:] == ["Lodha Camelot Kharadi Pune", "Quiet Homes Kharadi Pune"]
    s = out["PR1260002501399"]
    assert "top 10 for 2 buyer searches" in s["evidence"] and "best: #2 for 'new launch projects in Kharadi Pune'" in s["evidence"]
    assert "4 sites market it, 1 with Google ads" in s["evidence"] and "avasetu.in" not in s["evidence"]
    assert "youtube.com" not in s["evidence"] and s["source"] == "Google search results"
    assert set(out) == {"PR1260002501399"}
    p = await store.project("PR1260002501399")
    assert p["web_marketers"] == ["ads.example-cp.com", "housiey.com", "lodha-camelot.example-partner.in", "magicbricks.com"]
    assert p["web_advertisers"] == ["ads.example-cp.com"]

    # numbers we do not have are kept with where they were seen; the agent's RERA number is not a project number
    found = await websearch.discovered(store)
    assert [f["regno"] for f in found] == ["PR1260002501386", "PR1260002501413"]
    assert found[0]["seen"][0]["link"] == "https://lodha-camelot.example-partner.in/"

    # the next day: the next area searches in turn, and projects searched within KEEP_DAYS are not searched again
    asked.clear()
    await websearch.signal(google(answers, asked))(store, projects, NOW + timedelta(days=1))
    assert asked == [q["q"] for q in websearch.area_queries()[websearch.AREA_PER_DAY:2 * websearch.AREA_PER_DAY]]


async def test_old_results_stop_counting_and_a_refused_key_stops_the_day():
    db, store = await seeded(("P1", "Lodha Camelot", "kharadi", FULL))
    projects = [await store.project("P1")]
    asked = []
    await websearch.signal(google({"Lodha Camelot Kharadi Pune": CAMELOT}, asked))(store, projects, NOW)
    later = NOW + timedelta(days=websearch.KEEP_DAYS + 1)
    calls = []

    async def refused(q):
        calls.append(q)
        raise httpx.HTTPStatusError("no credit", request=httpx.Request("POST", "https://x"), response=httpx.Response(402))
    assert await websearch.signal(refused)(store, projects, later) == {}
    assert len(calls) == 1                                                       # stopped at the first refusal
    assert (await store.get_mark(websearch.MARK))["next"] == websearch.AREA_PER_DAY   # the refused search is tried again tomorrow


async def test_no_key_no_searches(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    db, store = await seeded(("P1", "Lodha Camelot", "kharadi", FULL))
    assert await websearch.signal()(store, [await store.project("P1")], NOW) == {}


async def test_serper_provider_sends_the_query_for_india_and_reads_organic_and_ads():
    seen = []

    def handler(req):
        seen.append((str(req.url), req.headers["X-API-KEY"], json.loads(req.content)))
        return httpx.Response(200, json={"organic": [{"title": "A", "link": "https://a.in", "snippet": "s", "position": 1}],
                                         "ads": [{"title": "B", "link": "https://b.in"}],
                                         "relatedSearches": [{"query": "kharadi new projects 2026"}],
                                         "peopleAlsoAsk": [{"question": "Is Kharadi good for investment?", "link": "https://c.in",
                                                            "snippet": "s2"}]})
    out = await websearch.serper("k", transport=httpx.MockTransport(handler))("new launch projects in Kharadi Pune")
    assert seen[0] == ("https://google.serper.dev/search", "k", {"q": "new launch projects in Kharadi Pune", "gl": "in", "hl": "en", "num": 10})
    assert out == [{**r("A", "https://a.in", 1, "s"), "type": "organic"}, {**r("B", "https://b.in", 0, ad=True), "type": "ad"},
                   {**r("kharadi new projects 2026", "", 0), "type": "related"},
                   {**r("Is Kharadi good for investment?", "https://c.in", 0, "s2"), "type": "question"}]


def test_marketers_exclude_us_the_regulator_and_social_sites():
    assert websearch.marketer("https://www.housiey.com/x") and websearch.site("https://www.housiey.com/x") == "housiey.com"
    assert not websearch.marketer("https://avasetu.in/projects/x")
    assert not websearch.marketer("https://maharera.maharashtra.gov.in/x")
    assert not websearch.marketer("https://m.facebook.com/x") and not websearch.marketer("")


def test_mentions_need_the_whole_name():
    assert websearch.mentions("Lodha Camelot", "New: LODHA-CAMELOT, Kharadi")
    assert not websearch.mentions("Lodha Camelot", "Lodha Camelots")


async def test_the_google_signal_feeds_the_hot_score():
    db, store = await seeded(("P1", "Lodha Camelot", "kharadi", FULL))
    hot.add_signal("google", websearch.signal(google({"new launch projects in Kharadi Pune": KHARADI_NEW,
                                                      "Lodha Camelot Kharadi Pune": CAMELOT}, [])))
    await hot.refresh(store, NOW)
    top = await hot.top(store)
    assert top[0]["regno"] == "P1" and top[0]["why"][0]["signal"] == "google" and "magicbricks.com" in top[0]["marketed_by"]
