"""Weekly search gaps: searches with no page of ours in the top 20, from Search Console and from our own Google searches."""
from datetime import datetime, timedelta, timezone

from app.modules.newsroom.store import Store
from app.modules.seo import gaps

from ..fakes import FakeDb

NOW = datetime(2026, 10, 25, 9, 0, tzinfo=timezone.utc)


def searched(phrase, position, at=NOW - timedelta(days=2), kind="area", area=None, **more):
    return {"_id": phrase, "phrase": phrase, "sources": ["searched"], "kind": kind, "area": area,
            "rank": {"position": position, "at": at}, "rank_history": [{"at": at, "position": position}], **more}


async def seeded(*rows):
    store = Store(FakeDb())
    for r in rows:
        await store.db.get_collection(gaps.DEMAND).insert_one(r)
    return store


async def test_gaps_lists_searched_phrases_where_we_are_absent():
    store = await seeded(
        # filed as a project (and under the wrong area) by demand.classify, but the words ask for Kharadi's projects
        searched("new launch projects in kharadi pune", None, kind="project", area="wagholi", regno="P52100047587"),
        searched("2 bhk flats in wagholi pune", None),
        searched("flats in baner pune", 4),                                       # we rank: not a gap
        searched("ready to move flats in hinjawadi pune", None, at=NOW - timedelta(days=40)),   # too old to count
        searched("godrej ivara kharadi pune", None, kind="project", regno="PR1260002502426"),  # one project's name only
    )
    assert await gaps.run_once(store, NOW, force=True) == {"gaps": 2, "with_page": 2}
    mark = await store.get_mark(gaps.MARK)
    got = {i["phrase"]: i for i in mark["items"]}
    assert set(got) == {"new launch projects in kharadi pune", "2 bhk flats in wagholi pune"}
    k = got["new launch projects in kharadi pune"]
    assert (k["source"], k["position"], k["area"], k["page"]) == ("searched", None, "kharadi", "/projects/area/kharadi")
    assert got["2 bhk flats in wagholi pune"]["page"] == "/2-bhk/wagholi"
    assert mark["searched"] == 2


async def test_search_console_gaps_still_count_and_our_areas_come_first():
    store = await seeded(
        {"_id": "stamp duty pune", "phrase": "stamp duty pune", "kind": "topic", "gsc": {"impressions": 90, "position": 31.0}},
        {"_id": "flats in lohegaon", "phrase": "flats in lohegaon", "kind": "area", "area": "lohegaon",
         "gsc": {"impressions": 40, "position": 24.5, "pages": ["/localities/lohegaon"]}},
        {"_id": "flats in wakad", "phrase": "flats in wakad", "kind": "area", "gsc": {"impressions": 300, "position": 8.0}},
        searched("property rates in keshav nagar pune", None),
    )
    await gaps.run_once(store, NOW, force=True)
    items = (await store.get_mark(gaps.MARK))["items"]
    assert [(i["phrase"], i["source"]) for i in items] == [
        ("flats in lohegaon", "search_console"), ("property rates in keshav nagar pune", "searched"),
        ("stamp duty pune", "search_console")]
    assert items[0]["shown_pages"] == ["/localities/lohegaon"] and items[2]["page"] is None


async def test_gaps_keep_at_most_keep_items():
    store = await seeded(*[searched(f"flats in wagholi pune under {n} lakh", None) for n in range(gaps.KEEP + 5)])
    await gaps.run_once(store, NOW, force=True)
    mark = await store.get_mark(gaps.MARK)
    assert (len(mark["items"]), mark["total"]) == (gaps.KEEP, gaps.KEEP + 5)
