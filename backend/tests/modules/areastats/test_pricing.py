"""Prices on their own turn, outward from Kharadi, new launches and hot projects first (app/modules/areastats/pricing.py)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import pricing, prices
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 21, 9, 0, tzinfo=timezone.utc)


def doc(i, place, **kw):
    return {"_id": f"P{i}", "regno": f"P{i}", "name": f"Project {i}", "page_slug": f"project-{i}", "pune_place": place,
            "promoter": "B", "completion_now": "2028-06-30", "registered_on": "2025-01-01", "units_total": 100, "units_booked": 10, **kw}


def priced(days_ago):
    return {"at": NOW - timedelta(days=days_ago), "rows": [{"bhk": "2 BHK", "from_inr": 7_000_000, "official": True, "sources": []}]}


def order(docs):
    return [d for _, d in sorted((pricing.priority(x, NOW), x["_id"]) for x in docs)]


def test_first_places_then_our_areas_outward_then_the_rest():
    assert pricing.ORDER[:5] == ("upper_kharadi", "kharadi", "wagholi", "keshav_nagar", "lohegaon")
    docs = [doc(1, "baner"), doc(2, "dhanori"), doc(3, "wagholi"), doc(4, "kharadi"), doc(5, "upper_kharadi"), doc(6, "lohegaon")]
    assert order(docs) == ["P5", "P4", "P3", "P6", "P1", "P2"]


def test_in_an_area_new_launches_and_hot_first():
    docs = [doc(1, "kharadi", registered_on="2020-01-01"), doc(2, "kharadi", registered_on="2026-09-01"),
            doc(3, "kharadi", registered_on="2020-01-01", hot_score=40), doc(4, "kesnand", locality="wagholi"),
            doc(5, "viman_nagar")]
    assert order(docs) == ["P3", "P2", "P1", "P4", "P5"]   # hottest first among new and hot; Kesnand counts as Wagholi


def test_when_a_project_is_due():
    assert pricing.priority(doc(1, "kharadi", prices_tried_at=NOW - timedelta(days=10), prices=priced(10)), NOW) is None
    assert pricing.priority(doc(1, "kharadi", prices_tried_at=NOW - timedelta(days=31), prices=priced(31)), NOW) is not None
    # found nothing: two weeks; a service failure: a day
    assert pricing.priority(doc(1, "kharadi", prices_tried_at=NOW - timedelta(days=5), prices_checked="0 prices from 2 of 3 sites"), NOW) is None
    assert pricing.priority(doc(1, "kharadi", prices_tried_at=NOW - timedelta(days=2), prices_checked="no LLM key"), NOW) is not None
    assert pricing.priority(doc(1, "kharadi", prices=priced(3)), NOW) is None                      # read by the page rewrite lately
    assert pricing.priority(doc(1, "kharadi", units_booked=100), NOW) is None                     # sold out
    assert pricing.priority(doc(1, "kharadi", completion_now="2026-09-30"), NOW) is None          # completed
    assert pricing.priority(doc(1, "kharadi", cluster_primary="P9"), NOW) is None                 # a tower, priced on its primary


def test_nearly_sold_out_goes_last():
    assert order([doc(1, "kharadi", units_booked=95), doc(2, "kharadi"), doc(3, "hinjawadi")]) == ["P2", "P3", "P1"]


async def test_a_round_reads_one_project_keeps_the_search_budget_and_the_coverage(monkeypatch):
    store = Store(FakeDb())
    for d in (doc(1, "wagholi"), doc(2, "upper_kharadi"), doc(3, "baner", prices=priced(2))):
        await store.projects.insert_one(d)
    seen = []

    async def fake_gather(store_, d, llm, now, fetch=None, search=None, allow_search=True):
        seen.append((d["_id"], allow_search))
        if search:
            await search("q")
        return {"ok": True, "at": now, "checked": "1 prices from 1 of 2 sites"}, {"prices": priced(0)}

    async def serper(q):
        return []
    monkeypatch.setattr(prices, "gather", fake_gather)
    monkeypatch.setenv("PRICES_SEARCHES_PER_DAY", "1")

    out = await pricing.step(store, object(), NOW, None, search=serper)
    assert out == {"regno": "P2", "place": "upper_kharadi", "ok": True, "checked": "1 prices from 1 of 2 sites"}
    assert await pricing.step(store, object(), NOW + timedelta(minutes=5), NOW, search=serper) is None      # not due yet
    assert await pricing.step(store, object(), NOW, None, busy=True, search=serper) is None                 # models resting
    await pricing.step(store, object(), NOW + timedelta(minutes=20), NOW, search=serper)
    assert seen == [("P2", True), ("P1", False)]   # the day's one search is spent
    mark = await store.get_mark(pricing.MARK)
    assert mark["searches"] == 1 and mark["last"]["regno"] == "P1"
    cov = {c["place"]: c for c in mark["coverage"]}
    assert cov["upper_kharadi"] == {"place": "upper_kharadi", "selling": 1, "priced": 1, "none_found": 0, "waiting": 0}
    assert cov["baner"]["priced"] == 1
    p2 = await store.projects.find_one({"_id": "P2"})
    assert p2["prices_tried_at"] == NOW and p2["prices_checked"] == "1 prices from 1 of 2 sites"
