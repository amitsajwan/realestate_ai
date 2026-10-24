"""The pages the owner asks Google to index by hand: our areas' place pages and guides first, tiny neighbourhood guides last."""
from datetime import datetime, timezone

from app.modules.newsroom.store import PROJECTS, Store
from app.modules.seo import coverage, note

from ..fakes import FakeDb

NOW = datetime(2026, 10, 25, 9, 0, tzinfo=timezone.utc)
SITE = "https://avasetu.in"
PATHS = [
    "/localities/wakad/kaspate-vasti", "/localities/baner/rutuja-park", "/localities/lohegaon/viman-nagar",
    "/projects/area/baner", "/projects/area/kharadi/2-bhk", "/projects/area/upper-kharadi", "/projects/area/kharadi/2-bhk/under-1-crore",
    "/projects/area/hadapsar", "/localities/kharadi", "/localities/hadapsar", "/guides/mhada-pune-lottery", "/builders/godrej",
    "/projects/godrej-ivara-pune", "/projects/lodha-camelot", "/projects/quiet-tower", "/projects/seen-tower", "/projects/far-hot",
]
RECORDS = [
    {"_id": "P1", "page_slug": "godrej-ivara-pune", "locality": "upper_kharadi", "hot_score": 9, "gsc_impressions": 10},
    {"_id": "P2", "page_slug": "lodha-camelot", "locality": "kharadi", "hot_score": 9, "gsc_impressions": 40},
    {"_id": "P3", "page_slug": "quiet-tower", "locality": "wagholi"},
    {"_id": "P4", "page_slug": "seen-tower", "locality": "wagholi", "gsc_impressions": 5},
    {"_id": "P5", "page_slug": "far-hot", "locality": "hadapsar", "hot_score": 5},
]


async def store_with_waiting_pages() -> Store:
    db = FakeDb()
    for path in PATHS:
        await db.get_collection(coverage.COLLECTION).insert_one(
            {"_id": SITE + path, "state": "Discovered - currently not indexed", "checked_at": NOW})
    await db.get_collection(coverage.COLLECTION).insert_one({"_id": SITE + "/projects/area/wagholi", "state": "Submitted and indexed"})
    for r in RECORDS:
        await db.get_collection(PROJECTS).insert_one(r)
    return Store(db)


async def test_request_list_puts_our_area_pages_before_neighbourhood_guides():
    got = await note.request_list(await store_with_waiting_pages())
    assert [(g["url"].replace(SITE, ""), g["why"]) for g in got] == [
        ("/projects/area/baner", "area page"),
        ("/projects/area/upper-kharadi", "area page"),
        ("/localities/kharadi", "area guide"),
        ("/guides/mhada-pune-lottery", "guide"),
        ("/projects/area/kharadi/2-bhk", "area list"),
        ("/projects/area/kharadi/2-bhk/under-1-crore", "area list"),
        ("/projects/lodha-camelot", "hot project"),
        ("/projects/godrej-ivara-pune", "hot project"),
        ("/builders/godrej", "builder page"),
        ("/localities/hadapsar", "other area guide"),
        ("/projects/area/hadapsar", "other area page"),
        ("/projects/seen-tower", "seen on Google"),
        ("/projects/quiet-tower", "project page"),
        ("/projects/far-hot", "project page"),
        ("/localities/baner/rutuja-park", "neighbourhood guide"),
        ("/localities/lohegaon/viman-nagar", "neighbourhood guide"),
        ("/localities/wakad/kaspate-vasti", "neighbourhood guide"),
    ]


async def test_a_neighbourhood_guide_is_judged_by_its_area_segment_not_any_segment():
    key, why = note._rank("/localities/hadapsar/viman-nagar", {})
    assert why == "neighbourhood guide" and key[1] is True   # hadapsar is not ours, even though viman-nagar looks like a place
    assert note._rank("/projects/area/hadapsar/kharadi-road", {})[1] == "other area list"


async def test_request_list_is_empty_when_nothing_waits():
    assert await note.request_list(Store(FakeDb())) == []
