"""New launches: read the day they register anywhere in Pune, again each day until they can show something, and timed."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import budget, enrich, launches, pages, pricing
from app.modules.seo import coverage, note

from ..fakes import FakeDb
from .test_pages import FULL, seeded

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
FOUND = NOW - timedelta(days=3)
LAUNCH = {**FULL, "registered_on": "2026-11-17", "first_seen": FOUND, "page_slug": "new-tower-ravet", "units_total": 168,
          "project_type": "Residential"}
OWN = {"page_text": "Written text.", "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 5000000}]}}


async def test_a_new_project_with_many_homes_outside_our_areas_is_read_first():
    db, store = await seeded(("B", "Baner Old", "baner", {**FULL, "page_slug": "baner-old", "gsc_impressions": 900}),
                             ("L", "New Tower", None, LAUNCH))
    assert (await enrich.next_project(store, NOW))["_id"] == "L"


async def test_small_old_office_and_tower_records_outside_our_areas_wait_as_before():
    db, store = await seeded(("S", "Small", None, {**LAUNCH, "units_total": 49}),
                             ("O", "Old", None, {**LAUNCH, "registered_on": "2026-11-05"}),
                             ("C", "Offices", None, {**LAUNCH, "project_type": "Commercial"}),
                             ("T", "Tower", None, {**LAUNCH, "cluster_primary": "L"}))
    assert await enrich.next_project(store, NOW) is None


async def test_a_launch_is_read_again_a_day_later_until_it_can_go_into_search():
    db, store = await seeded(("L", "New Tower", None, {**LAUNCH, "enriched_at": NOW - timedelta(hours=23)}))
    assert await enrich.next_project(store, NOW) is None
    await store.set_project("L", enriched_at=NOW - timedelta(hours=25))
    assert (await enrich.next_project(store, NOW))["_id"] == "L"
    await store.set_project("L", **OWN)
    assert pages.searchable(await store.project("L"), NOW) and await enrich.next_project(store, NOW) is None


async def test_a_launch_with_nothing_beyond_the_register_stays_out_of_search():
    db, store = await seeded(("L", "New Tower", None, {**LAUNCH, "page_text": "Written text."}))
    assert not pages.searchable(await store.project("L"), NOW)


async def test_a_launch_reads_on_the_premium_budget_while_it_is_new():
    assert pricing.tier_of(LAUNCH, NOW) == budget.PREMIUM
    assert pricing.tier_of(LAUNCH, NOW + timedelta(days=15)) == budget.PLAIN


async def test_a_put_off_reading_of_a_launch_outside_our_areas_is_taken(monkeypatch):
    db, store = await seeded(("L", "New Tower", None, {**LAUNCH, "enriched_at": NOW, "reading_due": True}))
    taken = []

    async def one(store, doc, llm, now, facts=True):
        taken.append(doc["_id"])
        return {"regno": doc["_id"], "text": True, "notes": [], "score": None}
    monkeypatch.setattr(enrich, "enrich_one", one)
    monkeypatch.setattr(enrich, "can_read", lambda llm, tier: True)
    assert await enrich.read_step(store, object(), NOW, None, timedelta(minutes=10))
    assert taken == ["L"]


async def test_the_clock_keeps_the_first_date_of_each_step(monkeypatch):
    db, store = await seeded(("L", "New Tower", None, {**LAUNCH, "enriched_at": FOUND, **OWN}))

    async def indexed(db):
        return {"/projects/new-tower-ravet"}
    monkeypatch.setitem(launches._deps, "indexed", indexed)
    assert await launches.refresh(store, NOW) == 1
    first = (await store.project("L"))["launch_clock"]
    assert first == {"read": NOW, "text": NOW, "search": NOW, "indexed": NOW}

    later = NOW + timedelta(hours=2)
    await store.set_project("L", page_text=None, gsc_impressions=5)      # the page left search; when it got there still stands
    assert await launches.refresh(store, later) == 1
    assert (await store.project("L"))["launch_clock"] == {**first, "shown": later}


async def test_the_clock_runs_once_an_hour_and_skips_projects_found_before_it_started():
    db, store = await seeded(("O", "Older", None, {**LAUNCH, "first_seen": launches.CLOCK_FROM - timedelta(days=1), "enriched_at": FOUND}))
    assert await launches.refresh(store, NOW) == 0
    assert await launches.refresh(store, NOW + timedelta(minutes=59)) is None
    assert "launch_clock" not in await store.project("O")


def test_the_week_counts_big_launches_and_how_long_they_took():
    def timed(days):
        return {**LAUNCH, "launch_clock": {"search": FOUND + timedelta(days=days), "indexed": FOUND + timedelta(days=days + 2)}}
    docs = [timed(1), timed(3), {**LAUNCH, "launch_clock": {"read": FOUND}}, {**timed(1), "units_total": 10}]
    s = launches.summary(docs, NOW)
    assert (s["projects"], s["search"], s["indexed"], s["days_to_search"], s["days_to_indexed"]) == (3, 2, 2, 2, 4)
    line = launches.week_line(s)
    assert line == ("New launches, 28 days: 3 projects with 50+ homes; 2 in search (usually 2 days after we found it), "
                    "2 indexed by Google (usually 4 days after we found it), 0 seen in results.")


def test_a_week_with_no_launches_adds_nothing_to_the_note():
    assert launches.week_line(launches.summary([], NOW)) == ""
    assert note.notes("week", "ai", "", "", "", "") == ["week", "ai"]
    assert note.notes("week", "ai", "", "", "", "launches") == ["week", "ai", "launches"]


async def test_the_indexed_pages_are_those_google_passed():
    db = FakeDb()
    coll = db.get_collection(coverage.COLLECTION)
    await coll.insert_one({"_id": "https://avasetu.in/projects/a", "verdict": "PASS"})
    await coll.insert_one({"_id": "https://avasetu.in/projects/b", "verdict": "NEUTRAL"})
    assert await coverage.indexed_paths(db) == {"/projects/a"}
