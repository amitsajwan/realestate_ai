"""The pages the owner asks Google to index by hand: our areas' place pages and guides first, tiny neighbourhood guides last."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats.demand import DEMAND
from app.modules.newsroom.store import PROJECTS, Store
from app.modules.notifications.service import MAX_SUMMARY
from app.modules.seo import aivisits, coverage, note, scoreboard

from ..fakes import FakeDb

NOW = datetime(2026, 10, 25, 9, 0, tzinfo=timezone.utc)
SITE = "https://avasetu.in"
PATHS = [
    "/localities/wakad/kaspate-vasti", "/localities/baner/rutuja-park", "/localities/lohegaon/viman-nagar",
    "/projects/area/baner", "/projects/area/kharadi/2-bhk", "/projects/area/upper-kharadi", "/projects/area/kharadi/2-bhk/under-1-crore",
    "/projects/area/hadapsar", "/localities/kharadi", "/localities/hadapsar", "/guides/mhada-pune-lottery", "/builders/godrej",
    "/projects/godrej-ivara-pune", "/projects/lodha-camelot", "/projects/quiet-tower", "/projects/seen-tower", "/projects/far-hot",
]
# in search: listable (a filed date and a promoter), written, and a fact of its own (areastats.pages.searchable)
IN_SEARCH = {"promoter": "Builder", "completion_now": "2029-06-30", "page_text": "Written.", "prices": {"rows": [{"bhk": 2}]}}
RECORDS = [
    {"_id": "P1", "page_slug": "godrej-ivara-pune", "locality": "upper_kharadi", "hot_score": 9, "gsc_impressions": 10, **IN_SEARCH},
    {"_id": "P2", "page_slug": "lodha-camelot", "locality": "kharadi", "hot_score": 9, "gsc_impressions": 40, **IN_SEARCH},
    {"_id": "P3", "page_slug": "quiet-tower", "locality": "wagholi", **IN_SEARCH},
    {"_id": "P4", "page_slug": "seen-tower", "locality": "wagholi", "gsc_impressions": 5, **IN_SEARCH},
    {"_id": "P5", "page_slug": "far-hot", "locality": "hadapsar", "hot_score": 5, **IN_SEARCH},
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


async def test_request_list_leaves_out_project_pages_that_are_not_in_search():
    store = await store_with_waiting_pages()
    projects = store.db.get_collection(PROJECTS)
    await projects.update_one({"_id": "P2"}, {"$set": {"prices": None}})                 # thin now: noindex
    await projects.update_one({"_id": "P1"}, {"$set": {"cluster_primary": "P9"}})        # a tower: redirects to its group
    urls = [r["url"] for r in await note.request_list(store)]
    assert SITE + "/projects/lodha-camelot" not in urls and SITE + "/projects/godrej-ivara-pune" not in urls
    assert SITE + "/projects/quiet-tower" in urls and SITE + "/projects/area/baner" in urls


async def test_request_list_is_empty_when_nothing_waits():
    assert await note.request_list(Store(FakeDb())) == []


# ---- searches by name, the portal watch, and a note that is never cut off (docs/plan/seo-system.md 8b, H5 and H6a) --------

def test_avasetu_is_found_however_buyers_spell_it():
    for q in ("avasetu", "ava setu kharadi", "avsetu", "awasetu flats", "aavasetu", "avasethu", "avasetu.in", "आवासेतु"):
        assert note.BRAND.search(q), q
    for q in ("vasetu", "savasetu", "setu bharatam"):
        assert not note.BRAND.search(q), q


async def test_searches_by_name_add_up_search_consoles_fresh_numbers():
    store = Store(FakeDb())
    demand = store.db.get_collection(DEMAND)
    await demand.insert_one({"_id": "avasetu", "gsc": {"impressions": 90, "clicks": 20, "read_at": NOW}, "gsc_prev": 50})
    await demand.insert_one({"_id": "ava setu kharadi", "gsc": {"impressions": 30, "clicks": 10, "read_at": NOW}})
    await demand.insert_one({"_id": "avasetu wagholi", "gsc": {"impressions": 500, "read_at": NOW - timedelta(days=30)}})   # old
    await demand.insert_one({"_id": "flats in kharadi", "gsc": {"impressions": 900, "read_at": NOW}})
    b = await note.branded(store, NOW)
    assert b == {"phrases": 2, "impressions": 120, "clicks": 30, "before": 50}
    assert note.brand_line(b) == "Searches for Avasetu by name, 28 days: 120 impressions (+70 on the 28 days before), 30 clicks."
    assert note.brand_line({"phrases": 0}) == "Searches for Avasetu by name, 28 days: none yet."


def test_a_portal_showing_homes_booked_or_moved_dates_is_counted_with_examples():
    docs = [{"_id": "rohan abhilasha wagholi", "results": [
        {"type": "organic", "link": "https://www.magicbricks.com/rohan-abhilasha", "title": "Rohan Abhilasha", "snippet": "244 of 416 units booked"},
        {"type": "organic", "link": "https://www.99acres.com/x", "title": "X", "snippet": "Possession date delayed to 2030"},
        {"type": "organic", "link": "https://housing.com/x", "title": "2 BHK flats", "snippet": "Ready to move, 3 BHK from 1 Cr"},
        {"type": "organic", "link": "https://avasetu.in/projects/x", "title": "X", "snippet": "244 of 416 homes booked"},
        {"type": "ad", "ad": True, "link": "https://www.magicbricks.com/ad", "title": "", "snippet": "Units sold fast"}]}]
    fmt = scoreboard.portal_format(docs)
    assert (fmt["magicbricks"]["booked"], fmt["acres99"]["date_moved"], fmt["housing"]["booked"]) == (1, 1, 0)
    assert fmt["magicbricks"]["examples"] == [{"query": "rohan abhilasha wagholi", "link": "https://www.magicbricks.com/rohan-abhilasha",
                                                "shows": ["booked"]}]
    assert scoreboard.format_alert(fmt) == []
    assert scoreboard.format_alert({"magicbricks": {"booked": 2, "date_moved": 1}}) == ["MagicBricks"]
    assert note.portal_line({"format": {"magicbricks": {"booked": 3}}}).startswith("Watch: MagicBricks results now show")


def test_every_part_of_the_weekly_note_fits_a_notification():
    week = note.summary({"clicks": 92_000, "impressions": 5_022_000, "page_one": 59_800}, {"clicks": 80_000, "impressions": 4_000_000,
                        "page_one": 55_000}, {"inspected": 27_600, "indexed": 8_480}, {"searches": 261, "above_mb": 23}, 4_200)
    ai = aivisits.week_line({"totals": {"answer": 12_031, "referral": 1_212, "search": 94_000}},
                            {"ChatGPT": 22, "Gemini": 11, "Perplexity": 9, "Copilot": 3, "Claude": 2, "Grok": 1})
    brand = note.brand_line({"phrases": 3, "impressions": 12_000, "clicks": 3_000, "before": 8_000})
    portal = note.portal_line({"format": {"magicbricks": {"booked": 5}, "acres99": {"date_moved": 4}, "housing": {"booked": 3}}})
    parts = note.notes(week, ai, brand, portal)
    assert len(parts) == 3 and all(len(p) <= MAX_SUMMARY for p in parts)
    assert note.notes(week, ai, brand, "")[1].startswith("AI search, 7 days") and len(note.notes(week, ai, brand, "")) == 2


async def test_the_weekly_run_sends_its_note_in_parts_that_each_fit(monkeypatch):
    monkeypatch.setenv("INSIGHTS_OWNER_IDS", "OWNER")
    store = await store_with_waiting_pages()
    await store.db.get_collection(DEMAND).insert_one({"_id": "avasetu", "gsc": {"impressions": 40, "clicks": 9, "read_at": NOW}})
    assert await note.run_once(store, NOW) is not None
    sent = await store.db.get_collection("notifications").find({"agent_id": "OWNER"}).to_list(None)
    assert [n["summary"][:9] for n in sent] == ["SEO week:", "AI search"]
    assert "Searches for Avasetu by name, 28 days: 40 impressions, 9 clicks." in sent[1]["summary"]


async def test_the_weekly_note_counts_only_pages_in_the_sitemap_now(monkeypatch):
    monkeypatch.setenv("INSIGHTS_OWNER_IDS", "OWNER")
    store = await store_with_waiting_pages()   # `seo_index` holds more pages than the sitemap has since kept
    await store.set_mark(coverage.MARK, inspected=345, indexed=144,
                         missing_by_state={"Crawled - currently not indexed": 120, "Discovered - currently not indexed": 80, "Soft 404": 1})
    assert (await note.run_once(store, NOW))["waiting"] == 200
    sent = await store.db.get_collection("notifications").find({"agent_id": "OWNER"}).to_list(None)
    assert "indexed 144 of 345 checked" in sent[0]["summary"] and "200 pages to ask Google for" in sent[0]["summary"]
