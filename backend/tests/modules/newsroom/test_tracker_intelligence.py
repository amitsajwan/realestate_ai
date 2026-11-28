"""Trackers that update themselves (pune-intelligence.md A): a checked suggestion goes live unless it says the thing opened,
Studio-added trackers live in Mongo beside the files, the weekly topic finder proposes new ones, places get their changes,
and every tracker brings its own Google News searches."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.newsroom import changes_for_place, runner, topic_finder, tracker_topics, trackers
from app.modules.newsroom import public as pub
from app.modules.newsroom import router as owner
from app.modules.newsroom.sources.google_news import build_queries
from app.modules.newsroom.stages.filter import assess
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import RawItem

from ..fakes import FakeDb

NOW = datetime(2026, 11, 28, 9, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def no_studio_trackers_leak():
    """The Studio-added trackers are held in the module between reads: each test starts and ends without any."""
    def clear():
        trackers._DEFINED.clear()
        tracker_topics.set_defined({})
        trackers._DEFINED_FOR[0] = (None, 0.0)
    clear()
    yield
    clear()


async def report(store, id, title, source="Punekar News", days_ago=1):
    at = NOW - timedelta(days=days_ago)
    await store.items.insert_one({"_id": id, "status": "dropped", "created_at": at, "raw": {
        "id": id, "source": source, "url": f"https://example.com/{id}", "title": title, "text": title, "published_at": at, "fetched_at": at}})


class FakeLlm:
    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    async def json(self, system, user):
        self.calls += 1
        return self.answer


def apps(store):
    app = FastAPI()
    app.include_router(pub.router, prefix="/public")
    app.include_router(owner.router, prefix="/newsroom")
    app.dependency_overrides[pub.get_store] = lambda: store
    app.dependency_overrides[owner.get_store] = lambda: store
    app.dependency_overrides[owner.owner_only] = lambda: type("U", (), {"id": "owner"})()
    return TestClient(app)


RING = "Pune Ring Road survey halted again as farmers demand higher compensation"


# --- auto-apply ----------------------------------------------------------------------------------------------------------------

async def test_a_checked_suggestion_goes_live_by_itself_and_the_old_line_stays_in_the_history():
    store = Store(FakeDb())
    await report(store, "r1", RING, source="Urban Acres")
    await trackers.attach_new(store, NOW)
    llm = FakeLlm({"changed": True, "stage": None, "status": "The land survey has stopped again over compensation.",
                   "date": "2026-11-27", "sources": ["Urban Acres"], "reason": "The survey stopped."})
    assert await trackers.suggest_due(store, llm, NOW) == 1
    assert await trackers.apply_due(store, NOW) == 1
    v = await trackers.one_view(store, "pune-ring-road")
    assert (v["status"], v["status_date"], v["status_sources"]) == ("The land survey has stopped again over compensation.", "2026-11-27", ["Urban Acres"])
    assert v["history"][1]["status"].startswith("The project's cost is reported up")
    assert await trackers.apply_due(store, NOW) == 0   # once
    row = trackers.studio_view(trackers.get("pune-ring-road"), await store.tracker_state("pune-ring-road"), await store.tracker_reports("pune-ring-road"))
    assert row["auto_updated"] is True and row["new_count"] == 0 and row["suggestion"] is None
    assert await trackers.suggest_due(store, llm, NOW) == 0 and llm.calls == 1   # the reports are no longer new


async def test_a_suggestion_already_waiting_from_before_goes_live_on_the_first_run_without_asking_the_model_again():
    store = Store(FakeDb())
    await report(store, "p1", "Purandar airport land acquisition nearly done, tender to be floated soon", source="Hotelier Buzz", days_ago=12)
    await trackers.attach_new(store, NOW - timedelta(days=11))
    await store.set_tracker_suggestion("purandar-airport", {   # as production held it on 2026-11-28
        "date": "2026-11-16", "stage": 2, "status": "Land acquisition is nearly done, tender to be floated soon", "changed": True,
        "sources": ["Hotelier Buzz"], "reason": "Tender stage is near", "ok": True, "for_ids": ["p1"], "at": NOW - timedelta(days=11)})
    counts = {}
    await runner._track(store, None, NOW, counts)
    assert counts["tracker_updates"] == 1
    v = await trackers.one_view(store, "purandar-airport")
    assert v["status"] == "Land acquisition is nearly done, tender to be floated soon" and v["stage"] == 2 and v["status_date"] == "2026-11-16"


async def test_a_move_to_the_last_stage_or_an_opening_waits_for_the_owner():
    store = Store(FakeDb())
    await report(store, "h1", "Lohegaon Hospital OPD Opened to Patients on Monday", days_ago=0)
    await trackers.attach_new(store, NOW)
    llm = FakeLlm({"changed": True, "stage": 2, "status": "The hospital's OPD has opened to patients.", "date": "2026-11-28",
                   "sources": ["Punekar News"], "reason": "The OPD opened."})
    assert await trackers.suggest_due(store, llm, NOW) == 1
    assert await trackers.apply_due(store, NOW) == 0
    v = await trackers.one_view(store, "lohegaon-hospital")
    assert v["status"].startswith("Built and staffed")   # never 'open' on the site because a model said so
    row = next(t for t in apps(store).get("/newsroom/trackers").json() if t["slug"] == "lohegaon-hospital")
    assert row["suggestion"]["held"] == "moves it to the last stage (Open)" and row["suggestion"]["stage"] == 2


def test_the_owner_guard_reads_opening_words_without_a_stage():
    ring = trackers.get("pune-ring-road")
    assert trackers.needs_owner(ring, None, {"status": "The eastern arm was inaugurated.", "stage": None}) == "says 'inaugurated'"
    assert trackers.needs_owner(ring, None, {"status": "Trains are running on it.", "stage": None}) == "says 'running'"
    assert trackers.needs_owner(ring, None, {"status": "The survey stopped over compensation.", "stage": None}) is None
    airport = trackers.get("purandar-airport")
    assert trackers.needs_owner(airport, None, {"status": "Construction began.", "stage": 3}) is None


async def test_with_the_switch_off_suggestions_wait_as_before(monkeypatch):
    store = Store(FakeDb())
    await report(store, "r1", RING, source="Urban Acres")
    llm = FakeLlm({"changed": True, "stage": None, "status": "The land survey has stopped again over compensation.",
                   "date": "2026-11-27", "sources": ["Urban Acres"], "reason": "The survey stopped."})
    monkeypatch.setenv("NEWSROOM_TRACKER_AUTO", "false")
    from app.modules.newsroom.config import load
    counts = {}
    await runner._track(store, llm, NOW, counts, load().tracker_auto)
    assert counts["suggested"] == 1 and "tracker_updates" not in counts
    assert (await trackers.one_view(store, "pune-ring-road"))["status"].startswith("The project's cost")


# --- Studio-added trackers in Mongo ---------------------------------------------------------------------------------------------

DEFN = {"name": "Kharadi-Shivane road", "kind": "project", "stages": ["Land acquisition", "Construction", "Open"],
        "match": {"all": ["kharadi"], "any": ["shivane"]}, "queries": ["Kharadi Shivane road"], "places": ["kharadi", "warje"],
        "history": [{"date": "2026-11-16", "stage": 0, "status": "Farmland in Vadgaon Sheri is being acquired for the road.", "sources": ["PUNE PULSE"]}]}


async def test_a_tracker_defined_in_mongo_joins_the_files_and_a_file_wins_its_slug():
    store = Store(FakeDb())
    await store.add_tracker_definition("kharadi-shivane-road", dict(DEFN), NOW)
    await store.add_tracker_definition("hcmtr", {**DEFN, "name": "Not the file"}, NOW)
    await store.add_tracker_definition("broken", {"name": "No history", "kind": "project", "history": []}, NOW)
    assert await trackers.refresh(store) == 2
    defs = trackers.definitions()
    assert "kharadi-shivane-road" in defs and defs["hcmtr"]["name"] == "HCMTR" and "broken" not in defs
    assert list(defs)[-1] == "kharadi-shivane-road"   # files first
    assert tracker_topics.topic_of("PMC acquires land for Kharadi-Shivane road")[0] == "kharadi-shivane-road"
    assert "Kharadi Shivane road" in build_queries()
    c = apps(store)
    v = c.get("/public/trackers/kharadi-shivane-road").json()
    assert v["status"].startswith("Farmland") and v["places"] == [{"slug": "kharadi", "name": "Kharadi"}, {"slug": "warje", "name": "Warje"}]


# --- topic finder ----------------------------------------------------------------------------------------------------------------

async def seed_topic(store):
    await report(store, "t1", "Pune: PMC plans skywalk at Hadapsar Gadital junction", source="Punekar News", days_ago=2)
    await report(store, "t2", "Hadapsar Gadital skywalk tender floated by civic body", source="Hindustan Times", days_ago=4)
    await report(store, "t3", "Hadapsar skywalk at Gadital to cost Rs 40 crore", source="Times of India", days_ago=9)
    await report(store, "t4", "Bengaluru skywalk at Silk Board junction gets nod", source="Deccan Herald", days_ago=3)
    await report(store, "t5", "Bengaluru Silk Board skywalk tender floated", source="Deccan Herald", days_ago=3)
    await report(store, "t6", "Bengaluru Silk Board skywalk to cost more", source="The Hindu", days_ago=3)
    await report(store, "t7", "Purandar airport land acquisition nearly done", source="Pune Mirror", days_ago=2)
    await report(store, "t8", "Pune: Baner cafe festival draws crowds", source="Punekar News", days_ago=2)
    await report(store, "t9", "Baner cafe festival returns", source="Punekar News", days_ago=5)
    await report(store, "t10", "Baner cafe festival day two", source="Punekar News", days_ago=6)
    await report(store, "old", "Hadapsar Gadital skywalk first proposed", source="Pune Mirror", days_ago=45)


def test_headlines_of_one_subject_group_together_and_generic_words_do_not_tie_them():
    rows = [{"title": t, "source": "x"} for t in (
        "Pune: PMC plans skywalk at Hadapsar Gadital junction", "Hadapsar Gadital skywalk tender floated by civic body",
        "Pune civic body plans new parking policy", "PMC water cut in Kothrud on Thursday")]
    groups = topic_finder.group(rows)
    assert [len(g) for g in groups] == [2, 1, 1]
    assert topic_finder.core_words(groups[0])[:3] == ["skywalk", "hadapsar", "gadital"]


async def test_the_weekly_finder_proposes_a_pune_subject_with_three_reports_from_two_publishers_once_a_week():
    store = Store(FakeDb())
    await seed_topic(store)
    assert await topic_finder.find_due(store, None, NOW) == 1
    [c] = await topic_finder.candidates(store)
    assert c["key"] == "hadapsar-skywalk" and c["report_count"] == 3 and c["publishers"] == 3 and c["by"] == "rules"
    assert c["name"] == "Skywalk Hadapsar Gadital" and c["status"] is None and c["match"]["all"] == [r"\bskywalk", r"\bhadapsar"]
    assert await topic_finder.find_due(store, None, NOW + timedelta(days=1)) == 0   # same week


async def test_a_model_draft_is_kept_part_by_part_only_where_it_passes_the_checks():
    store = Store(FakeDb())
    await seed_topic(store)
    llm = FakeLlm({"name": "Hadapsar Gadital skywalk", "kind": "project", "stages": ["Planned", "Tendered", "Built"],
                   "queries": ["Hadapsar skywalk", "Gadital skywalk Magarpatta mall"],   # a word not in the headlines
                   "match": {"all": ["nowhere"]},                                     # matches none of them
                   "status": "A tender has been floated for the skywalk, which will cost Rs 90 crore."})   # an invented figure
    assert await topic_finder.find_due(store, llm, NOW) == 1
    [c] = await topic_finder.candidates(store)
    assert c["name"] == "Hadapsar Gadital skywalk" and c["stages"] == ["Planned", "Tendered", "Built"] and c["by"] == "model"
    assert c["queries"] == ["Pune skywalk hadapsar"] and c["match"]["all"] == [r"\bskywalk", r"\bhadapsar"] and c["status"] is None


async def test_adding_a_proposed_tracker_in_studio_saves_it_and_attaches_its_reports():
    store = Store(FakeDb())
    await seed_topic(store)
    await topic_finder.find_due(store, None, NOW)
    c = apps(store)
    [cand] = c.get("/newsroom/trackers/candidates").json()
    assert c.post(f"/newsroom/trackers/candidates/{cand['key']}/add", json={"status": "Plan"}).status_code == 422
    ok = c.post(f"/newsroom/trackers/candidates/{cand['key']}/add",
                json={"name": "Hadapsar Gadital skywalk", "status": "The civic body has floated a tender for the skywalk.",
                      "date": "2026-11-24", "places": ["hadapsar"]})
    assert ok.status_code == 200 and ok.json()["slug"] == "hadapsar-gadital-skywalk" and ok.json()["report_count"] == 4   # the 45-day-old one too: a new tracker looks back FIRST_SCAN days
    assert c.get("/newsroom/trackers/candidates").json() == []
    page = c.get("/public/trackers/hadapsar-gadital-skywalk").json()
    assert page["status"] == "The civic body has floated a tender for the skywalk." and page["places"][0]["slug"] == "hadapsar"
    assert any(t["slug"] == "hadapsar-gadital-skywalk" for t in c.get("/newsroom/trackers").json())
    assert await topic_finder.find_due(store, None, NOW + timedelta(days=7)) == 0   # its reports are on a tracker now


async def test_a_dismissed_subject_is_not_proposed_again():
    store = Store(FakeDb())
    await seed_topic(store)
    await topic_finder.find_due(store, None, NOW)
    c = apps(store)
    assert c.post("/newsroom/trackers/candidates/hadapsar-skywalk/dismiss").status_code == 200
    assert await topic_finder.find_due(store, None, NOW + timedelta(days=7)) == 0
    assert c.post("/newsroom/trackers/candidates/hadapsar-skywalk/dismiss").status_code == 404


# --- places ----------------------------------------------------------------------------------------------------------------------

async def test_changes_for_a_place_are_the_trackers_that_name_it_newest_first():
    store = Store(FakeDb())
    rows = await changes_for_place(store.db, "keshav-nagar")
    assert [r["slug"] for r in rows] == ["keshavnagar-kharadi-bridge", "merged-villages-water"]
    assert rows[0] == {"slug": "keshavnagar-kharadi-bridge", "name": "Keshavnagar-Kharadi bridge", "status": rows[0]["status"],
                       "date": "2026-11-25", "stage": "Built, not formally open"}
    assert "stage" not in rows[1]   # a rule has no stage
    assert await changes_for_place(store.db, "keshav_nagar") == rows   # the key is taken too
    assert await changes_for_place(store.db, "atlantis") == []
    assert len(await changes_for_place(store.db, "kharadi")) <= trackers.CHANGES_MAX


async def test_a_status_update_moves_a_places_change_to_the_top():
    store = Store(FakeDb())
    await store.add_tracker_update("merged-villages-water", {"date": "2026-11-27", "stage": None, "status": "Builders must supply water for three years.",
                                                             "sources": ["Punekar News"], "at": NOW, "by": "auto"})
    rows = await changes_for_place(store.db, "keshav-nagar")
    assert rows[0]["slug"] == "merged-villages-water" and rows[0]["date"] == "2026-11-27"


def test_every_tracker_names_only_real_places_and_brings_two_to_four_searches():
    from app.core import pune_places
    for slug, d in trackers.file_definitions().items():
        assert "places" in d, slug
        assert all(p in pune_places.BY_SLUG for p in d["places"]), slug
        assert 1 <= len(d.get("queries") or []) <= 4, slug
    assert len(trackers.file_definitions()) >= 20


# --- searches and the area gate --------------------------------------------------------------------------------------------------

def test_each_trackers_searches_are_asked_of_google_news():
    qs = build_queries()
    for q in ("Patal Lok Pune underground road", "Vishrantwadi flyover", "Purandar airport land acquisition", "MHADA Pune lottery"):
        assert q in qs
    assert len({q.lower() for q in qs}) == len(qs)


@pytest.mark.parametrize("title,slug", [
    ("Pune Prioritises 23 km Bhosari-Undri Underground Tunnel", "patal-lok-underground-road"),
    ("Vishrantwadi Flyover Gets January Completion Deadline", "vishrantwadi-flyover"),
    ("Pune Metro Phase 2 Targets Four New Corridors For Completion Within Five Years", "pune-metro-phase-2"),
    ("PMC stops extra FSI, TDR benefits unless proposed road widening is completed", "pmc-building-rules-fsi"),
])
def test_a_headline_about_a_tracker_is_attached_and_passes_the_area_gate(title, slug):
    assert trackers.matches(trackers.get(slug), title)
    it = RawItem(id="x", source="Punekar News", url="https://e.test/x", title=title, text=title, published_at=NOW, fetched_at=NOW)
    r = assess(it, NOW)
    assert "off-topic" not in r.reason, r.reason


def test_namesakes_elsewhere_do_not_attach():
    assert not trackers.matches(trackers.get("pune-metro-phase-2"), "Mumbai Metro phase 2 work begins")
    assert not trackers.matches(trackers.get("patal-lok-underground-road"), "Mumbai coastal road tunnel opens")
    assert not trackers.matches(trackers.get("pune-development-plan"), "Kothrud accounts for 244 of Pune's 629 redevelopment plans")
    assert not trackers.matches(trackers.get("mhada-pune-lottery"), "21-Year-Old Poses As IAS Officer, Cheats People With MHADA Lottery Promise")
