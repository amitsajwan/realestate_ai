"""Slow background enrichment of project pages: priority, the checker, one per interval, urgent requests, the page text."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.areastats import enrich, pages
from app.modules.newsroom.store import Store

from ..fakes import FakeDb
from .test_pages import FULL, seeded

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
GATHERED = {"nearby": [{"label": "school", "name": "Lexicon School", "km": 1.2}], "numbers": {}, "maharera": {"project_type": "Residential"}}


class FakeLLM:
    def __init__(self, text):
        self.text, self.calls = text, 0

    async def json(self, system, user):
        self.calls += 1
        return {"text": self.text}


GOOD = ("Rohan Abhilasha 4 is a housing project by Rohan Builders in Wagholi, Pune. Its completion date filed with MahaRERA is "
        "30 Oct 2029, later than the 31 Dec 2028 filed at registration. 244 of 416 homes were booked when the record was read.\n\n"
        "Lexicon School is about 1.2 km away.")


@pytest.fixture(autouse=True)
def gatherer(monkeypatch):
    calls = []

    async def gather(db, regno, name, locality, city="Pune", now=None):
        calls.append(regno)
        return GATHERED
    monkeypatch.setitem(enrich._deps, "gather", gather)
    return calls


@pytest.fixture(autouse=True)
def no_maharera(monkeypatch):
    """MahaRERA is never called from tests: both reads answer nothing unless a test sets them."""
    async def nothing(mid):
        return None
    monkeypatch.setattr(enrich, "PAUSE", 0)
    monkeypatch.setitem(enrich._deps, "general", nothing)
    monkeypatch.setitem(enrich._deps, "buildings", nothing)
    monkeypatch.setitem(enrich._deps, "sheet", None)
    monkeypatch.setitem(enrich._deps, "pincode_centre", None)


async def ready(*docs):
    db, store = await seeded(*docs)
    await pages.assign_all(store)
    return db, store


async def test_urgent_first_then_google_then_indexable_then_bigger():
    db, store = await ready(("A", "Alpha", "wagholi", {**FULL, "units_total": 100, "units_booked": 50}),
                            ("B", "Bravo", "wagholi", {**FULL, "gsc_impressions": 40}),
                            ("C", "Charlie", "wagholi", {}),
                            ("D", "Delta", "wagholi", {**FULL, "units_total": 900, "units_booked": 10}),
                            ("E", "Echo", "wagholi", {**FULL, "enriched_at": NOW - timedelta(days=5), "enrichment": {"score": "4/4"}}))
    order = []
    for _ in range(4):
        d = await enrich.next_project(store, NOW)
        order.append(d["_id"])
        await store.set_project(d["_id"], enriched_at=NOW, enrichment={"score": "4/4"})
    assert order == ["B", "D", "A", "C"]          # Google impressions, then indexable (bigger first), then thin; E is fresh
    assert await enrich.next_project(store, NOW) is None
    await enrich.enrich_now(db, "e")
    assert (await enrich.next_project(store, NOW))["_id"] == "E"   # urgent beats freshness


def test_the_checker_refuses_invented_numbers_sales_words_and_links():
    facts = enrich.facts_text({**FULL, "_id": "P1", "name": "Rohan Abhilasha 4", "locality": "wagholi", "regno": "P1"}, GATHERED)
    assert enrich.check_text(GOOD, facts) == []
    assert any("numbers not in the facts" in p for p in enrich.check_text(GOOD + " Prices start at 55 lakh.", facts))
    assert "sales words" in enrich.check_text(GOOD.replace("housing project", "luxury project"), facts)
    assert "links or phone numbers" in enrich.check_text(GOOD + " Call 9876543210.", facts)
    assert "too short" in enrich.check_text("Nice.", facts)


async def test_one_project_per_interval_and_urgent_ones_at_once(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}),
                            ("P2", "Other", "wagholi", {**FULL}))
    llm = FakeLLM(GOOD)
    out = await enrich.step(store, llm, NOW, None, timedelta(minutes=30))
    assert out["regno"] in ("P1", "P2") and out["text"] and out["gathered"] and not out["urgent"]
    assert await enrich.step(store, llm, NOW + timedelta(minutes=10), NOW, timedelta(minutes=30)) is None   # not yet
    await enrich.enrich_now(db, "P2" if out["regno"] == "P1" else "P1")
    urgent = await enrich.step(store, llm, NOW + timedelta(minutes=11), NOW, timedelta(minutes=30))
    assert urgent["urgent"] and await db.get_collection(enrich.REQUESTS).count_documents({}) == 0
    assert len(gatherer) == 2 and llm.calls == 2


async def test_a_refused_draft_keeps_the_code_paragraph_and_the_page_shows_accepted_text():
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    await enrich.step(store, FakeLLM("A luxury project with the best views in Pune, homes from Rs 55 lakh, book now."), NOW, None,
                      timedelta(minutes=30))
    doc = await store.project("P1")
    assert "page_text" not in doc and doc["enriched_at"] == NOW and "kept the code-written paragraph" in doc["enrich_notes"]
    page = await pages.project_page(db, doc["page_slug"])
    assert page["paragraph"].startswith("Rohan Abhilasha 4 is a project by Rohan Builders")

    await store.set_project("P1", enriched_at=None)
    await enrich.step(store, FakeLLM(GOOD), NOW, None, timedelta(minutes=30))
    page = await pages.project_page(db, doc["page_slug"])
    assert page["paragraph"] == GOOD and page["enriched_at"] == "2026-10-06"


async def test_without_a_gatherer_it_still_writes_from_the_register_facts(monkeypatch):
    monkeypatch.setitem(enrich._deps, "gather", None)
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    out = await enrich.step(store, FakeLLM(GOOD.split("\n\n")[0]), NOW, None, timedelta(minutes=30))
    assert out["text"] and "no gatherer configured" in out["notes"]


async def test_enrich_now_for_an_unknown_project_says_so():
    db = FakeDb()
    assert await enrich.enrich_now(db, "NOPE") is False


def test_off_unless_switched_on(monkeypatch):
    monkeypatch.delenv("PROJECT_ENRICH_ENABLED", raising=False)
    assert enrich.load().enabled is False
    monkeypatch.setenv("PROJECT_ENRICH_ENABLED", "on")
    monkeypatch.setenv("PROJECT_ENRICH_EVERY_MINUTES", "30")
    assert enrich.load().enabled and enrich.load().every == timedelta(minutes=30)


def test_facts_label_both_dates_and_drop_junk_names():
    doc = {**FULL, "_id": "P1", "name": "Ivy", "locality": "wagholi", "regno": "P1"}
    g = {"nearby": [{"label": "Hospital", "name": "HOSPITAL 9", "km": 0.5}, {"label": "Hospital", "name": "Care Hospital", "km": 0.6}]}
    facts = enrich.facts_text(doc, g)
    assert "Completion date filed when the project was registered: 31 Dec 2028 (this is a completion date, not the registration date)" in facts
    assert "HOSPITAL 9" not in facts and "Care Hospital, 0.6 km" in facts


BUILDINGS = {"status": "1", "responseObject": [
    {"projectId": 80076, "projectRegistartionNo": "P1", "buildingNameNumber": "A", "buildingWingsNameNumber": "NA",
     "noOfBuildingWingFloorSanctioned": 15, "residentialUnitCount": 90, "nonResidentialUnitCount": 2, "totalUnitCount": 92, "isActive": 1},
    {"projectId": 80076, "projectRegistartionNo": "P1", "buildingNameNumber": "B", "buildingWingsNameNumber": "Wing 1",
     "noOfBuildingWingFloorProposed": 12, "residentialUnitCount": 48, "nonResidentialUnitCount": 0, "totalUnitCount": 48, "isActive": 1}]}
GENERAL = {"status": "1", "responseObject": {"projectRegistartionNo": "P1", "projectName": "Rohan Abhilasha 4",
                                             "projectProposeComplitionDate": "2029-10-30", "originalProjectProposeCompletionDate": "2028-12-31",
                                             "reraRegistrationDate": "2024-01-10", "totalNumberOfUnits": 416, "totalNumberOfSoldUnits": 244}}


async def test_a_round_stores_buildings_and_the_checks(monkeypatch):
    async def general(mid):
        return GENERAL

    async def buildings(mid):
        return BUILDINGS

    async def centre(db, pin):
        return (18.58, 73.98)

    async def sheet(db, regno):
        return {"rera_no": regno, "facts": [{"key": "lat", "value": 18.59, "usable": True}, {"key": "lon", "value": 73.99, "usable": True}]}
    for k, v in (("general", general), ("buildings", buildings), ("pincode_centre", centre), ("sheet", sheet)):
        monkeypatch.setitem(enrich._deps, k, v)
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL}))
    out = await enrich.step(store, FakeLLM(GOOD), NOW, None, timedelta(minutes=10))
    doc = await store.project("P1")
    assert out["score"] == "4/4" and enrich.status_of(doc) == "ok"
    assert doc["building_totals"] == {"towers": 2, "max_floors": 15, "units_total": 140, "units_residential": 138, "units_other": 2}
    assert doc["buildings"][0]["wing"] is None and doc["buildings"][1]["floors"] == 12
    steps = doc["enrichment"]["steps"]
    assert steps["maharera_general"]["checked"] == "regno matches" and steps["buildings"]["count"] == 2
    assert steps["places"]["located_from"] == "locality" and doc["geo"]["km_from_pincode"] < 15
    listed = await enrich.status_list(store)
    assert listed["counts"]["ok"] == 1 and listed["items"][0]["page"].startswith("/projects/")
    page = await pages.project_page(db, doc["page_slug"])
    assert page["details"]["towers"] == 2 and page["map"]["lat"] == 18.59 and page["builder"]["count"] == 1


async def test_another_projects_buildings_are_refused_and_plots_have_none():
    wrong = {"status": "1", "responseObject": [{**BUILDINGS["responseObject"][0], "projectRegistartionNo": "P9"}]}
    with pytest.raises(enrich.project_api.MahaReraError):
        enrich.project_api.parse_buildings(wrong, "P1", 80076)
    assert enrich.project_api.parse_buildings({"status": "1", "responseObject": []}, "P1", 80076) == []


def test_a_far_position_and_the_fill_from_the_fact_sheet():
    assert enrich.km_between((18.5, 73.9), (18.5, 73.9)) == 0
    assert enrich.km_between((18.5, 73.9), (18.9, 74.3)) > 15
    sheet = {"rera_no": "P52100076768", "locality": "Ranjangaon", "facts": [{"key": "pincode", "value": "412220", "usable": True},
                                                                             {"key": "taluka", "value": "Shirur", "usable": True}]}
    doc = {"_id": "P52100076768", "regno": "P52100076768", "name": "Gulmohar City", "locality": None, "pincode": ""}
    assert enrich.place_fill(doc, sheet) == {"pincode": "412220", "place_locality": "Ranjangaon", "taluka": "Shirur"}
    assert enrich.place_fill({**doc, "_id": "OTHER", "regno": "OTHER"}, sheet) == {}


def test_records_enriched_before_the_checks_are_redone_after_googles_new_pages():
    old = {"_id": "O", "enriched_at": NOW - timedelta(days=3), "page_slug": "o", "locality": "wagholi"}
    seen = {"_id": "S", "gsc_impressions": 5, "page_slug": "s", "locality": "wagholi"}
    new = {"_id": "N", "page_slug": "n", "locality": "wagholi", **FULL}
    keys = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (old, seen, new)])
    assert [k[1] for k in keys] == ["S", "O", "N"]
    assert enrich.priority({**old, "enrichment": {"score": "4/4"}}, set(), NOW) is None


def test_builder_track_record_from_the_register():
    docs = [{"_id": "A", "name": "One", "promoter": "Rohan Builders Pvt. Ltd.", "completion_at_registration": "2028-01-31", "completion_now": "2029-01-31"},
            {"_id": "B", "name": "Two", "promoter": "ROHAN BUILDERS PRIVATE LIMITED", "completion_at_registration": "2027-06-30", "completion_now": "2027-06-30"},
            {"_id": "C", "name": "Other", "promoter": "Someone Else"}]
    rec = pages.track_record(docs[0], docs)
    assert rec["count"] == 2 and rec["moved_later"] == 1 and rec["avg_months_later"] == 12
