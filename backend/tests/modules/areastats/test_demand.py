"""Search demand: phrases from Search Console and Google results, placed by the rules, rising ones, and our own rank."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import demand, websearch

from .test_pages import FULL, seeded

NOW = datetime(2026, 10, 12, 6, 0, tzinfo=timezone.utc)


def row(query, impressions, position=10.0, page="https://avasetu.in/localities/kharadi"):
    return {"query": query, "page": page, "impressions": impressions, "clicks": 0, "position": position}


def test_phrases_are_placed_by_the_rules():
    projects = [{"_id": "P1", "regno": "P1", "name": "LODHA CAMELOT PHASE 1 - TOWER A", "locality": "kharadi"}]
    assert demand.classify("lodha camelot possession date", projects) == {"kind": "project", "area": "kharadi", "regno": "P1"}
    assert demand.classify("2 bhk flats in upper kharadi", projects) == {"kind": "area", "area": "upper_kharadi", "regno": None}
    assert demand.classify("stamp duty in pune 2026", projects) == {"kind": "topic", "area": None, "regno": None}
    assert demand.normalize("  Is Kharadi GOOD for investment?? ") == "is kharadi good for investment"


async def test_rising_needs_growth_over_the_28_days_before_or_a_new_phrase_with_enough_searches(monkeypatch):
    db, store = await seeded()
    await demand.from_gsc(store, [row("kharadi metro", 20), row("wagholi flats", 40), row("baner rent", 3)], NOW - timedelta(days=30))
    await demand.from_gsc(store, [row("kharadi metro", 60), row("wagholi flats", 45), row("baner rent", 30), row("new phrase", 12)], NOW)
    by = {t["phrase"]: t for t in await demand.top(store, limit=10)}
    assert by["kharadi metro"]["rising"] and by["kharadi metro"]["gsc_prev"] == 20          # 3x the 28 days before
    assert not by["wagholi flats"]["rising"]                                                  # steady
    assert by["baner rent"]["rising"]                                                         # 3 -> 30
    assert by["new phrase"]["rising"] and by["new phrase"]["gsc_prev"] is None                # new this week, enough searches
    assert [t["phrase"] for t in await demand.top(store, rising_only=True, area="kharadi")] == ["kharadi metro"]


async def test_google_results_give_our_rank_and_what_else_people_search(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in")
    db, store = await seeded(("P1", "Lodha Camelot", "kharadi", FULL))
    docs = [{"_id": "new launch projects in Kharadi Pune", "kind": "area", "area": "kharadi", "at": NOW, "results": [
        {"title": "x", "link": "https://www.housiey.com/k", "position": 1, "type": "organic"},
        {"title": "ad", "link": "https://www.avasetu.in/ad", "position": 0, "ad": True, "type": "ad"},     # an ad is not a rank
        {"title": "Kharadi projects", "link": "https://www.avasetu.in/localities/kharadi", "position": 4, "type": "organic"},
        {"title": "lodha camelot price", "link": "", "position": 0, "type": "related"},
        {"title": "Is Kharadi good for investment?", "link": "https://q.in", "position": 0, "type": "question"}]},
        {"_id": "upcoming residential projects in Kharadi Pune", "kind": "area", "area": "kharadi", "at": NOW - timedelta(days=2),
         "results": [{"title": "lodha camelot price", "link": "", "position": 0, "type": "related"}]}]
    out = await demand.from_results(store, docs, NOW)
    assert out == {"ranked": 1, "phrases": 3}                                  # only today's searches get a rank today
    by = {t["phrase"]: t for t in await demand.top(store, limit=10)}
    assert by["new launch projects in kharadi pune"]["rank"]["position"] == 4
    assert by["lodha camelot price"]["kind"] == "project" and by["lodha camelot price"]["regno"] == "P1"
    assert by["lodha camelot price"]["seen_in"] == ["new launch projects in Kharadi Pune", "upcoming residential projects in Kharadi Pune"]
    assert by["is kharadi good for investment"]["sources"] == ["question"]
    # the next day we are gone from the top 10: the rank says so, and the history keeps both days
    docs[0]["results"] = docs[0]["results"][:2]
    docs[0]["at"] = NOW + timedelta(days=1)
    await demand.from_results(store, docs[:1], NOW + timedelta(days=1))
    doc = await store.db.get_collection(demand.DEMAND).find_one({"_id": "new launch projects in kharadi pune"})
    assert doc["rank"]["position"] is None and [h["position"] for h in doc["rank_history"]] == [4, None]


async def test_the_google_signal_keeps_the_phrases():
    db, store = await seeded(("P1", "Lodha Camelot", "kharadi", FULL))

    async def search(q):
        return [{"title": "Lodha Camelot Kharadi", "link": "https://m.in/c", "snippet": "", "position": 1, "ad": False, "type": "organic"},
                {"title": "kharadi new launch 2026", "link": "", "snippet": "", "position": 0, "ad": False, "type": "related"}]
    await websearch.signal(search)(store, [await store.project("P1")], NOW)
    assert "kharadi new launch 2026" in [t["phrase"] for t in await demand.top(store, limit=50)]
