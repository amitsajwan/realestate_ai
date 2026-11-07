"""Slow background enrichment of project pages: priority, the checker, one per interval, urgent requests, the page text."""
import re
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.areastats import enrich, pages

from ..fakes import FakeDb
from .test_pages import FULL, seeded

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
FULL = {**FULL, "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 5000000}]}}   # a fact of its own: the writer runs only with one
GATHERED = {"nearby": [{"label": "school", "name": "Lexicon School", "km": 1.2}], "numbers": {}, "maharera": {"project_type": "Residential"}}


POINTS = ("Few homes are left to book here.", "The record is read from MahaRERA.")
LABELS = ("Few homes left", "On the record", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth")
POINTS_TEXT = "Few homes left: Few homes are left to book here.\n\nOn the record: The record is read from MahaRERA."


class FakeLLM:
    """Answers with the text's paragraphs as the sections, in SECTIONS order, and a search line."""
    def __init__(self, text):
        self.text, self.calls = text, 0

    async def json(self, system, user):
        self.calls += 1
        summary = "Rohan Abhilasha 4, Wagholi: homes by Rohan Builders, registered with MahaRERA"
        if system == enrich.POINTS_SYSTEM:   # the text's sentences as points, each naming every fact
            keys = re.findall(r"^\[(.+?)\]", user, re.M)
            said = POINTS if self.text == GOOD else re.split(r"(?<=[.])\s+", self.text.replace("\n\n", " "))
            return {"points": [{"label": LABELS[i], "text": t, "facts": keys} for i, t in enumerate(said)], "search_summary": summary}
        return {"points": [], "search_summary": summary}


# what the page does not already show: no dates, no bookings, no prices (TEXT_VERSION 4); stored as page_text, joined
GOOD = ("Rohan Abhilasha 4 is a residential project by Rohan Builders in Wagholi, Pune, filed with MahaRERA as one of the "
        "builder's Abhilasha projects.\n\n"
        "The project is in Wagholi, on the eastern side of Pune, an area where many new housing projects are registered.")


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
    # Baner: outside east Pune, so no project here is on a top list that goes first (the next test)
    db, store = await ready(("A", "Alpha", "baner", {**FULL, "units_total": 100, "units_booked": 50}),
                            ("B", "Bravo", "baner", {**FULL, "gsc_impressions": 40}),
                            ("C", "Charlie", "baner", {}),
                            ("D", "Delta", "baner", {**FULL, "units_total": 900, "units_booked": 10}),
                            ("E", "Echo", "baner", {**FULL, "enriched_at": NOW - timedelta(days=5), "enrichment": {"score": "4/4"},
                                                         "page_text_version": enrich.TEXT_VERSION}))
    order = []
    for _ in range(4):
        d = await enrich.next_project(store, NOW)
        order.append(d["_id"])
        await store.set_project(d["_id"], enriched_at=NOW, enrichment={"score": "4/4"}, page_text_version=enrich.TEXT_VERSION)
    assert order == ["B", "D", "A", "C"]          # Google impressions, then indexable (bigger first), then thin; E is fresh
    assert await enrich.next_project(store, NOW) is None
    await enrich.enrich_now(db, "e")
    assert (await enrich.next_project(store, NOW))["_id"] == "E"   # urgent beats freshness


async def test_east_pune_top_list_projects_go_with_the_hot_ones_even_finished_while_homes_are_left():
    db, store = await ready(("G", "Golf", "baner", {**FULL, "gsc_impressions": 40}),                       # Google shows it
                            ("T", "Tango", "wagholi", {**FULL, "units_total": 100, "units_booked": 50}),   # 50 open: on the top list
                            ("R", "Romeo", "wagholi", {**FULL, "completion_now": "2026-03-31", "units_total": 224,
                                                       "units_booked": 142}),                              # finished, 82 open
                            ("S", "Sierra", "wagholi", {**FULL, "completion_now": "2026-03-31", "units_total": 52,
                                                        "units_booked": 50}))                              # finished, 2 open
    order = []
    while (d := await enrich.next_project(store, NOW)) is not None:
        order.append(d["_id"])
        await store.set_project(d["_id"], enriched_at=NOW, enrichment={"score": "4/4"}, page_text_version=enrich.TEXT_VERSION)
    assert order == ["T", "R", "G"]               # the top list first; a finished project with 2 homes left is not worked on


async def test_the_owners_banner_picks_go_with_the_hot_ones(monkeypatch):
    db, store = await ready(("G", "Golf", "baner", {**FULL, "gsc_impressions": 40}),     # Google shows it
                            ("P", "Papa", "baner", {**FULL}))                           # picked for the banner
    slug = (await store.project("P"))["page_slug"]

    async def shown(db_):
        return {slug}
    monkeypatch.setitem(enrich._deps, "shown", shown)
    assert (await enrich.next_project(store, NOW))["_id"] == "P"
    monkeypatch.setitem(enrich._deps, "shown", None)
    assert (await enrich.next_project(store, NOW))["_id"] == "G"


async def test_among_pages_google_shows_those_just_off_page_one_go_first():
    # Baner: no top list goes first here (east Pune only)
    db, store = await ready(("A", "Alpha", "baner", {**FULL, "gsc_impressions": 900, "gsc_position": 3.2}),
                            ("B", "Bravo", "baner", {**FULL, "gsc_impressions": 60, "gsc_position": 11.4}),
                            ("C", "Charlie", "baner", {**FULL, "gsc_impressions": 5, "gsc_position": 12.0}))
    order = []
    for _ in range(3):
        d = await enrich.next_project(store, NOW)
        order.append(d["_id"])
        await store.set_project(d["_id"], enriched_at=NOW)
    assert order == ["B", "A", "C"]   # C is near page one but seen too rarely to count




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
    assert len(gatherer) == 2 and llm.calls == 3   # "Other": the draft does not name it, so it goes back once


async def test_a_refused_draft_keeps_the_code_paragraph_and_the_page_shows_accepted_text():
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    await enrich.step(store, FakeLLM("A luxury project with the best views in Pune, homes from Rs 55 lakh, book now."), NOW, None,
                      timedelta(minutes=30))
    doc = await store.project("P1")
    assert "luxury" not in doc["page_text"] and doc["enriched_at"] == NOW
    page = await pages.project_page(db, doc["page_slug"])
    assert page["paragraph"].startswith("Rohan Abhilasha 4 is a project by Rohan Builders")

    await store.set_project("P1", enriched_at=None)
    await enrich.step(store, FakeLLM(GOOD), NOW, None, timedelta(minutes=30))
    doc = await store.project("P1")
    assert doc["page_text"] == POINTS_TEXT and doc["page_text_version"] == enrich.TEXT_VERSION
    page = await pages.project_page(db, doc["page_slug"])
    assert page["sections"] == [] and [x["label"] for x in page["points"]] == ["Few homes left", "On the record"] and page["enriched_at"] == "2026-10-06"
    assert page["search_description"] == "Rohan Abhilasha 4, Wagholi: homes by Rohan Builders, registered with MahaRERA"


async def test_without_a_gatherer_it_still_writes_from_the_register_facts(monkeypatch):
    monkeypatch.setitem(enrich._deps, "gather", None)
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    out = await enrich.step(store, FakeLLM(GOOD), NOW, None, timedelta(minutes=30))
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
    # the register's own read is older than DETAILS_FRESH_DAYS: the round reads MahaRERA's general record itself
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "details_checked_at": NOW - timedelta(days=40)}))
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
    assert page["details"]["towers"] == 2 and page["builder"]["count"] == 1
    assert page["map"] is None   # the fact sheet's position is the locality's, not measured on the project (2026-11-01)


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
    new = {"_id": "N", "page_slug": "n", "locality": "wagholi", **FULL, "units_booked": None}   # homes open unknown: not on a top list
    keys = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (old, seen, new)])
    assert [k[1] for k in keys] == ["S", "O", "N"]
    assert enrich.priority({**old, "enrichment": {"score": "4/4"}, "page_text_version": enrich.TEXT_VERSION}, set(), NOW) is None
    assert enrich._priority({**old, "enrichment": {"score": "4/4"}, "prices": {"rows": [{"bhk": 2}]}}, NOW)[0] == enrich.BACKFILL   # an older writer's text, with facts to write from
    assert enrich._priority({**old, "enrichment": {"score": "4/4"}}, NOW) is None   # nothing of its own: no rewrite


def test_builder_track_record_from_the_register():
    docs = [{"_id": "A", "name": "One", "promoter": "Rohan Builders Pvt. Ltd.", "completion_at_registration": "2028-01-31", "completion_now": "2029-01-31"},
            {"_id": "B", "name": "Two", "promoter": "ROHAN BUILDERS PRIVATE LIMITED", "completion_at_registration": "2027-06-30", "completion_now": "2027-06-30"},
            {"_id": "C", "name": "Other", "promoter": "Someone Else"}]
    rec = pages.track_record(docs[0], docs)
    assert rec["count"] == 2 and rec["moved_later"] == 1 and rec["avg_months_later"] == 12


def test_completed_projects_are_not_enriched_and_nearly_sold_ones_go_last():
    base = {"page_slug": "x", "locality": "baner", **FULL}                    # outside east Pune: no top list goes first
    done = {**base, "_id": "D", "completion_now": "2026-09-30"}               # filed completion date passed
    assert enrich.priority(done, set(), NOW) is None
    assert enrich.priority(done, {"D"}, NOW) == (-1,)                          # a campaign still gets it
    assert enrich.status_of(done, NOW.date()) == "finished"
    nearly = {**base, "_id": "N", "units_total": 100, "units_booked": 92, "hot_score": 99}
    later = {**base, "_id": "L", "units_total": 100, "units_booked": 10}
    order = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (nearly, later)])
    assert [k[1] for k in order] == ["L", "N"]                                 # 90% booked waits, hot or not, outside east Pune
    hot_free = {**later, "_id": "H", "hot_score": 99}
    order = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (nearly, later, hot_free)])
    assert [k[1] for k in order] == ["H", "L", "N"]                            # hot first within its area
    east = [{**d, "locality": "wagholi", "units_booked": d["units_booked"] if d["_id"] == "N" else None} for d in (nearly, later, hot_free)]
    order = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in east])
    assert [k[1] for k in order] == ["H", "N", "L"]                            # east Pune: hot first, 90% booked behind the other hot


def test_east_pune_first_then_outward_from_kharadi_a_hot_project_elsewhere_in_its_areas_turn():
    base = {"page_slug": "x", **FULL, "registered_on": "2020-01-01", "units_booked": None}   # homes open unknown: no top list
    wakad = {**base, "_id": "W", "locality": "wakad", "pune_place": "wakad", "hot_score": 99}
    lohegaon = {**base, "_id": "L", "locality": "lohegaon", "pune_place": "lohegaon"}
    kharadi_old = {**base, "_id": "K", "locality": "kharadi", "pune_place": "kharadi", "gsc_impressions": 500}
    kharadi_new = {**base, "_id": "N", "locality": "kharadi", "pune_place": "kharadi", "registered_on": "2026-08-01"}
    upper = {**base, "_id": "U", "locality": "upper_kharadi", "pune_place": "upper_kharadi"}
    wagholi_hot = {**base, "_id": "G", "locality": "wagholi", "pune_place": "wagholi", "hot_score": 99}
    order = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (wakad, lohegaon, kharadi_old, kharadi_new, upper, wagholi_hot)])
    assert [k[1] for k in order] == ["G", "U", "N", "K", "L", "W"]   # east Pune's hot first, then outward; hot Wakad after east Pune


# Godrej Ivara on 2026-10-22: registered Feb 2026, MahaRERA's Order 66/2026 added 4 months, the builder moved nothing
IVARA = {"_id": "PR1260002502426", "regno": "PR1260002502426", "name": "Godrej Ivara", "locality": "upper_kharadi",
         "promoter": "Manjari Housing Projects LLP", "registered_on": "2026-02-20", "completion_at_registration": "2032-08-16",
         "completion_now": "2032-12-16", "units_total": 2792, "units_booked": 489}




IVARA_PROJECT = ("Godrej Ivara is a housing project by Manjari Housing Projects LLP, sold under the Godrej Properties brand, in "
                 "Upper Kharadi, Pune.")








# ---- Park Eden Phase I, 2026-10-25 (docs/plan/project-page-v2.md, "What was wrong") -------------------------------------------
# MahaRERA registers 2 buildings under this number; the builder's site says 5 towers (the whole project, all phases). The filed
# date went 31 Oct 2030 -> 28 Feb 2031 by MahaRERA's extension alone; 27 of 249 homes booked. The live page said all three wrong.
EDEN = {"_id": "P52100054321", "regno": "P52100054321", "name": "PARK EDEN PHASE I", "locality": "kharadi",
        "promoter": "Eden Realty LLP", "registered_on": "2024-03-12", "completion_at_registration": "2030-10-31",
        "completion_now": "2031-02-28", "units_total": 249, "units_booked": 27,
        "building_totals": {"towers": 2, "max_floors": 22, "units_total": 249, "units_residential": 249, "units_other": None},
        "prices": {"rows": [{"bhk": "3 BHK", "from_inr": 19900000}, {"bhk": "4 BHK", "from_inr": 27500000}]}}
EDEN_WEB = {"facts": [{"key": "towers", "label": "Towers", "value": 5, "text": "5", "official": True,
                       "sources": [{"site": "parkeden.in", "url": "https://parkeden.in/", "quote": "5 towers"}]},
                      {"key": "land_acres", "label": "Land", "value": 7.5, "text": "7.5 acres", "official": True,
                       "sources": [{"site": "parkeden.in", "url": "https://parkeden.in/", "quote": "7.5 acres"}]}]}
EDEN_NEAR = {"nearby": [{"label": "school", "name": "Lexicon School", "km": 1.2}], "numbers": {}}
EDEN_PROJECT = ("Park Eden Phase I is the first phase of Park Eden, by Eden Realty LLP in Kharadi, Pune. This registration "
                "covers two buildings of up to 22 floors; the whole project has five towers on 7.5 acres, according to the "
                "builder's site.")
EDEN_LOCATION = ("The project is in Kharadi, on the eastern side of Pune. Lexicon School is 1.2 km away in a straight line "
                 "from the project's pin.")
EDEN_SUMMARY = "Park Eden Phase I, Kharadi: homes in two buildings by Eden Realty LLP, completion filed for 28 Feb 2031"






async def test_an_accepted_draft_is_stored_as_sections_with_the_search_line():
    db, store = await ready((EDEN["_id"], EDEN["name"], "kharadi",
                             {**{k: v for k, v in EDEN.items() if k not in ("_id", "name")}, "web_facts": EDEN_WEB}))
    await enrich.enrich_one(store, await store.project(EDEN["_id"]), FakeLLM(GOOD), NOW, reread=False)
    doc = await store.project(EDEN["_id"])
    assert [x["heading"] for x in doc["page_sections"]] == ["Few homes left", "On the record"] and doc["page_sections"][0]["facts"]
    assert doc["page_text"] == POINTS_TEXT and doc["page_text_version"] == enrich.TEXT_VERSION
    assert any(f["key"] == "web_towers" for f in doc["fact_sheet"]["facts"])




def test_pages_written_by_an_older_writer_are_rewritten_after_everything_else():
    old = {"_id": "O", "page_slug": "o", "locality": "baner", **FULL, "enriched_at": NOW - timedelta(days=3),
           "enrichment": {"score": "4/4", "steps": {"web": {"ok": True, "at": NOW - timedelta(days=3)}}, "versions": dict(enrich.VERSIONS)},
           "page_text_version": 3}
    assert enrich.TEXT_VERSION == 7
    key = enrich._priority(old, NOW)
    assert key[:2] == (enrich.BACKFILL, 0)                        # web pages read lately: a cheap rewrite (one model call)
    assert enrich._priority({**old, "page_text_version": enrich.TEXT_VERSION}, NOW) is None


def test_a_page_in_search_keeps_its_text_two_weeks_before_a_newer_writer_takes_it():
    # Baner: not on an east Pune Top list, whose pages are re-read for pictures on their own schedule
    old = {"_id": "O", "page_slug": "o", "locality": "baner", **FULL, "enriched_at": NOW - timedelta(days=3),
           "enrichment": {"score": "4/4", "steps": {"web": {"ok": True, "at": NOW - timedelta(days=3)}}}, "page_text_version": 3,
           "page_text": "About the project.", "page_text_at": NOW - timedelta(days=3), "prices": {"rows": [{"bhk": 2}]}}
    assert enrich._priority(old, NOW) is None                                         # in search, written 3 days ago: rests
    assert enrich._priority({**old, "page_text_at": NOW - timedelta(days=15)}, NOW)[0] == 2   # read by an older version: with what is in search
    thin = {k: v for k, v in old.items() if k != "page_text"}
    assert enrich._priority(thin, NOW)[0] == enrich.BACKFILL                          # not in search: no rest needed


def test_a_thin_page_is_tried_again_after_a_week_a_page_in_search_after_two_months():
    # Baner: not hot, not on an east Pune Top list; enriched 10 days ago with the current writer
    done = {"_id": "T", "page_slug": "t", "locality": "baner", **FULL, "prices": {}, "enriched_at": NOW - timedelta(days=10),
            "enrichment": {"score": "4/4", "steps": {}}, "page_text_version": enrich.TEXT_VERSION,
            "page_text": "About the project.", "page_text_at": NOW - timedelta(days=10)}
    assert enrich._priority(done, NOW) is not None                                    # text only: out of search, due again
    assert enrich._priority({**done, "enriched_at": NOW - timedelta(days=5)}, NOW) is None   # within the week: waits
    full = {**done, "profile": {"highlights": ["Clubhouse"]}}
    assert enrich._priority(full, NOW) is None                                        # in search: waits REFRESH_DAYS


# ---- facts often, the model by budget (docs/plan/enrich-lanes.md) ------------------------------------------------------------

def _maharera(monkeypatch, reads):
    async def general(mid):
        reads.append("general")
        return GENERAL

    async def buildings(mid):
        reads.append("buildings")
        return BUILDINGS
    monkeypatch.setitem(enrich._deps, "general", general)
    monkeypatch.setitem(enrich._deps, "buildings", buildings)


async def test_a_recent_register_read_and_buildings_are_used_without_asking_maharera_again(monkeypatch):
    reads = []
    _maharera(monkeypatch, reads)
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL}))   # the register read it 3 days ago
    await enrich.enrich_one(store, await store.project("P1"), FakeLLM(GOOD), NOW)
    assert reads == ["buildings"]
    steps = (await store.project("P1"))["enrichment"]["steps"]
    assert steps["maharera_general"]["ok"] and "the register's read of 2026-10-03" in steps["maharera_general"]["checked"]
    await enrich.enrich_one(store, await store.project("P1"), FakeLLM(GOOD), NOW + timedelta(days=1))
    assert reads == ["buildings"]                                                 # buildings read a day ago: kept
    await enrich.enrich_one(store, await store.project("P1"), FakeLLM(GOOD), NOW + timedelta(days=1), urgent=True)
    assert reads == ["buildings", "general", "buildings"]                         # a campaign gets fresh reads


async def test_the_enrichments_own_maharera_read_keeps_the_homes_booked_reading_and_the_date_move(monkeypatch):
    # enrichment refreshes details_checked_at, so the register refresh skips the record: if enrichment dropped the readings, a
    # hot project's sales and date moves were lost (2026-10-26: no Pune record had two booked readings)
    _maharera(monkeypatch, [])
    old = {**FULL, "units_booked": 230, "completion_now": "2029-04-30", "details_checked_at": NOW - timedelta(days=40),
           "booked_history": [{"at": NOW - timedelta(days=40), "booked": 230}]}
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", old))
    await enrich.enrich_one(store, await store.project("P1"), FakeLLM(GOOD), NOW)
    doc = await store.project("P1")
    assert [h["booked"] for h in doc["booked_history"]] == [230, 244]
    assert doc["completion_history"] == [{"from": "2029-04-30", "to": "2029-10-30", "seen_at": NOW}]


async def test_without_a_model_the_facts_round_runs_and_the_reading_is_put_off_not_failed(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    out = await enrich.step(store, None, NOW, None, timedelta(minutes=5))
    doc = await store.project("P1")
    assert gatherer == ["P1"] and out["reading_due"] and doc["reading_due"] and "page_text" not in doc
    assert any("reading put off (no LLM key)" in n for n in doc["enrich_notes"])
    # waiting for a model is not a service failure (those are retried daily, MahaRERA reads and all)
    assert not enrich.unanswered({"enrichment": {"steps": {"web": {"ok": False, "checked": "no LLM key"}}}})
    assert enrich.reading_key(doc, NOW) is not None
    # a model is set up: the reading turn writes the text from the kept facts, without gathering again
    out = await enrich.read_step(store, FakeLLM(GOOD), NOW + timedelta(minutes=1), None, timedelta(minutes=10))
    doc = await store.project("P1")
    assert out["reading"] and out["text"] and doc["page_text"] == POINTS_TEXT and not doc["reading_due"]
    assert gatherer == ["P1"] and doc["enriched_at"] == NOW and doc["read_at"] == NOW + timedelta(minutes=1)
    assert await enrich.read_step(store, FakeLLM(GOOD), NOW + timedelta(hours=1), None, timedelta(minutes=10)) is None


class Spent:
    """A budgeted model with no room left today (areastats.budget.Reader's shape)."""
    budgeted, deferred = True, 0

    def can_read(self, tier):
        return False


async def test_a_spent_budget_puts_the_reading_off_and_the_reading_turn_waits_for_room():
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders",
                                                                     "page_text": GOOD, "page_text_version": enrich.TEXT_VERSION}))
    out = await enrich.step(store, Spent(), NOW, None, timedelta(minutes=5))
    doc = await store.project("P1")
    assert out["reading_due"] and doc["page_text"] == GOOD                       # the last text stays
    assert any("model budget for today is spent" in n for n in doc["enrich_notes"])
    assert await enrich.read_step(store, Spent(), NOW, None, timedelta(minutes=10)) is None


async def test_a_question_put_off_half_way_keeps_that_steps_last_result():
    from app.modules.areastats import budget
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    kept_text = {"ok": True, "at": NOW - timedelta(days=9), "refused_reasons": []}
    # its own facts changed since GOOD was written (a key that is not this sheet's), so the writer is asked (enrich.settled)
    await store.set_project("P1", enrichment={"steps": {"text": kept_text}}, page_text=GOOD, page_facts_key="older facts")
    reader = await budget.Reader(db, NOW, free=None, gemini=None, lite=None).start()
    reader.can_read = lambda tier: True        # room at the start of the round, none by the time the text is asked
    out = await enrich.enrich_one(store, await store.project("P1"), reader, NOW)
    doc = await store.project("P1")
    assert out["reading_due"] and doc["enrichment"]["steps"]["text"] == kept_text and doc["page_text"] == GOOD


def test_premium_projects_are_hot_shown_by_google_or_in_the_first_areas():
    from app.modules.areastats import budget
    base = {"page_slug": "x", **FULL}
    assert enrich.tier_of({**base, "locality": "wakad"}) == budget.PLAIN
    assert enrich.tier_of({**base, "locality": "wakad", "hot_score": 99}) == budget.PREMIUM
    assert enrich.tier_of({**base, "locality": "wakad", "gsc_impressions": 3}) == budget.PREMIUM
    assert enrich.tier_of({**base, "locality": "kharadi"}) == budget.PREMIUM
    assert enrich.tier_of({**base, "locality": "wakad"}, urgent=True) == budget.URGENT


async def test_a_page_written_as_sections_keeps_the_code_paragraph_as_its_paragraph():
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    sections = [{"heading": "The project", "text": "The project is laid out as towers around a central garden."}]
    await store.set_project("P1", page_text=sections[0]["text"], page_sections=sections, page_text_version=4)
    doc = await store.project("P1")
    page = await pages.project_page(db, doc["page_slug"])
    assert page["paragraph"] == pages.paragraph(await store.project("P1")) and page["sections"] == sections


def _thin_phase(**kw):
    return {"_id": "P1", "regno": "P1", "name": "Ganga Arcadia A Building", "promoter": "Goel Ganga", "pincode": "411014",
            "page_slug": "ganga-arcadia", "locality": "kharadi", "completion_now": "2030-01-01", "page_text": "Text.",
            "page_text_version": enrich.TEXT_VERSION, "enrichment": {"score": "4/4"}, "enriched_at": NOW - timedelta(days=1), **kw}


def test_a_thin_page_read_under_its_registration_name_is_read_once_more_under_the_whole_project():
    assert enrich.priority(_thin_phase(), set(), NOW) is not None
    assert enrich.priority(_thin_phase(web_read_as="Ganga Arcadia"), set(), NOW) is None      # read once, whatever it found
    assert enrich.priority(_thin_phase(prices={"rows": [{"bhk": "2 BHK"}]}), set(), NOW) is None   # has a fact of its own
    assert enrich.priority(_thin_phase(cluster_primary="P9"), set(), NOW) is None            # read on its group's primary
    assert enrich.priority(_thin_phase(name="Godrej Ivara"), set(), NOW) is None             # the name is already the project's
    assert enrich.priority(_thin_phase(enriched_at=NOW - timedelta(hours=1)), set(), NOW) is None   # not again within MIN_GAP



# ---- writer 5: longer, and our own words (owner 2026-11-04) ----------------------------------------------------------------

ROSE = {"_id": "P1", "name": "Rose Court", "regno": "P1"}
BODY = ("Rose Court stands on a corner plot and keeps its two buildings apart, so that most homes look over the open ground "
        "between them and not into a neighbour's window, which is uncommon for a project of this size in the area.")




def test_nine_words_from_the_sources_are_a_shared_phrase_not_copying():
    assert enrich.lifted(ROSE, BODY, " ".join(BODY.split()[5:14])) is None


def test_a_filed_company_name_is_not_copying():
    name = "Rose Court Phase One Of The Very Long Registered Name Here"
    doc = {**ROSE, "name": name}
    assert enrich.lifted(doc, f"{name} has two buildings.", f"Company: {name}") is None


def test_a_draft_that_reads_like_another_project_of_the_area_is_refused():
    other = {"_id": "P2", "name": "Lily Park", "regno": "P2", "page_text": BODY.replace("Rose Court", "Lily Park")}
    assert enrich.alike(ROSE, BODY, [other]) == "Lily Park"
    assert enrich.alike(ROSE, BODY, [{"_id": "P3", "name": "Tulip Row", "page_text": "A short and quite different text about some other place entirely."}]) is None


def test_phases_of_one_project_may_read_alike():
    one, two = {"_id": "P1", "name": "Rose Court Part 1", "regno": "P1"}, {"_id": "P2", "name": "Rose Court Part 2", "regno": "P2", "page_text": BODY}
    assert enrich.alike(one, BODY, [two]) is None


def test_a_page_is_not_compared_with_itself():
    assert enrich.alike({**ROSE, "page_text": BODY}, BODY, [{**ROSE, "page_text": BODY}]) is None


def test_code_works_out_homes_per_building_and_height():
    lines = enrich.worked_out({"units_total": 120, "building_totals": {"towers": 3, "max_floors": 22}})
    assert "about 40 homes per building" in lines[0] and "high-rise" in lines[1]
    assert enrich.worked_out({"units_total": 12, "building_totals": {"towers": 1, "max_floors": 4}}) == ["Worked out: a low-rise project, going by its tallest building"]
    assert enrich.worked_out({}) == []




def _in_search(**kw):
    return {"_id": "P1", "regno": "P1", "name": "Rose Court", "completion_now": "2030-01-01", "promoter": "Rose LLP", "project_type": "Residential",
            "page_text": "Some text.", "page_text_at": NOW - timedelta(days=3), "prices": {"rows": [{"bhk": "2 BHK"}]}, **kw}


def test_a_page_in_search_keeps_its_text_from_a_newer_writer_while_it_rests():
    assert enrich.keeps_text(_in_search(page_text_version=enrich.TEXT_VERSION - 1), NOW)


def test_a_page_in_search_is_written_again_once_rested():
    assert not enrich.keeps_text(_in_search(page_text_version=enrich.TEXT_VERSION - 1, page_text_at=NOW - timedelta(days=enrich.REST_DAYS + 1)), NOW)


def test_a_page_on_the_current_writer_is_not_held_back():
    assert not enrich.keeps_text(_in_search(page_text_version=enrich.TEXT_VERSION), NOW)


def test_a_page_out_of_search_does_not_rest():
    assert not enrich.keeps_text(_in_search(page_text_version=enrich.TEXT_VERSION - 1, prices={}), NOW)




class Answers:
    """Answers in turn with these texts as "The project", and keeps what it was asked."""
    def __init__(self, *texts):
        self.texts, self.asked = list(texts), []

    async def json(self, system, user):
        self.asked.append(user)
        return {"sections": [{"heading": "The project", "text": self.texts.pop(0)}], "search_summary": ""}








def _building(i, floors=10, homes=100, **kw):
    return {"_id": f"B{i}", "name": f"Tower {i}", "locality": "kharadi", "completion_now": "2031-01-01", "units_total": homes,
            "building_totals": {"towers": 1, "max_floors": floors}, "promoter": f"Co {i}", **kw}


def test_the_writer_is_told_how_the_project_sits_among_its_area():
    doc = {**ROSE, "locality": "kharadi", "completion_now": "2031-01-01", "units_total": 500, "promoter": "Rose LLP",
           "building_totals": {"towers": 2, "max_floors": 30}}
    area = [_building(i, floors=10 + i) for i in range(8)] + [_building(9, floors=40, promoter="Rose LLP")]
    lines = enrich.area_context(doc, area)
    assert any("higher than that of 8 of 9" in x for x in lines)
    assert any("more homes than 9 of 9" in x for x in lines)
    assert any("The same filing company has 1 other project still being built in Kharadi" in x for x in lines)


def test_an_area_with_too_few_projects_compares_nothing():
    assert enrich.area_context({**ROSE, "locality": "kharadi", "units_total": 5}, [_building(i) for i in range(3)]) == []


def test_only_the_record_decides_what_is_worth_asking():
    assert enrich.worth_asking({**ROSE, "completion_now": "2031-01-01", "promoter": "Rose LLP"}, None) == []
    assert any("occupancy certificate" in x for x in enrich.worth_asking({**ROSE, "completion_now": "2021-01-01"}, None))






async def test_outside_pages_are_read_live_and_a_page_that_fails_is_left_out():
    async def fetch(url):
        if "bad" in url:
            raise RuntimeError("no answer")
        return None if "empty" in url else "<p>Some page text</p>"
    web = {"read": [{"site": "a.com", "url": "https://a.com/x"}, {"site": "bad.com", "url": "https://bad.com/x"}, {"site": "e.com", "url": "https://empty.com/x"}]}
    assert await enrich.outside_pages(web, fetch) == [("a.com", "Some page text")]












# ---- the flow: facts first, the writer last, pages in search first (owner 2026-11-04) -----------------------------------------

OWN = {"prices": {"rows": [{"bhk": "2 BHK", "from_inr": 5000000}]}}


def test_towers_are_not_worth_a_model_but_offices_are():
    assert enrich.worth_model({"project_type": "Residential"})
    assert enrich.worth_model({"project_type": "Commercial"})
    assert not enrich.worth_model({"cluster_primary": "P9"})


def test_offices_are_read_after_the_homes_of_their_area():
    homes = enrich.priority({"_id": "H", "regno": "H", "locality": "kharadi", "project_type": "Residential"}, set(), NOW)
    offices = enrich.priority({"_id": "O", "regno": "O", "locality": "kharadi", "project_type": "Commercial"}, set(), NOW)
    assert homes < offices


def test_a_number_on_another_line_of_the_sheet_is_kept_and_that_line_named():
    sheet = [{"key": "booked", "text": "Homes booked: 1 of 24 (4%)"}, {"key": "buildings", "text": "Buildings in this registration: 1, up to 6 floors"}]
    kept, why = enrich.points_of({"points": [_point("Taller than most", "It rises 6 floors and has 24 homes.", "booked")]}, sheet, ROSE, None)
    assert not why and kept[0]["facts"] == ["booked", "buildings"]


def test_a_number_on_no_line_of_the_sheet_still_goes():
    sheet = [{"key": "booked", "text": "Homes booked: 1 of 24 (4%)"}]
    kept, why = enrich.points_of({"points": [_point("Taller", "It rises 6 floors.", "booked")]}, sheet, ROSE, None)
    assert not kept and "6" in why[0]


OFFICE = {**ROSE, "project_type": "Commercial", "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 8500000}]}, "units_total": 24}


def test_a_point_may_not_call_offices_homes():
    sheet = [{"key": "booked", "text": "Shop and office units booked: 1 of 24 (4%)"}]
    kept, why = enrich.points_of({"points": [_point("Few sold", "Only 1 of 24 homes are booked.", "booked"),
                                             _point("Few taken", "Only 1 of 24 units are booked.", "booked")]}, sheet, OFFICE, None)
    assert [x["heading"] for x in kept] == ["Few taken"] and "homes" in why[0]


def test_the_sheet_of_offices_says_units_and_holds_no_flat_price():
    sheet = {f["key"]: f["text"] for f in enrich.fact_sheet(OFFICE, None, None, None, False)}
    assert sheet["homes"].startswith("Shop and office units in this registration: 24")
    assert not any(k.startswith("price_") for k in sheet)


def test_code_written_points_say_units_for_offices():
    sheet = [{"key": "booked", "text": "Shop and office units booked: 1 of 24 (4%)"}, {"key": "buildings", "text": "Buildings in this registration: 1, up to 6 floors"}]
    assert "1 of 24 units booked" in enrich.code_points(OFFICE, sheet)["text"]


def test_a_tower_goes_after_everything_and_only_for_its_facts():
    key = enrich._priority({"_id": "T", "cluster_primary": "P9", "enriched_at": NOW - timedelta(days=enrich.REFRESH_DAYS + 1)}, NOW)
    assert key == (enrich.BACKFILL + 1, 0)
    assert enrich._priority({"_id": "T", "cluster_primary": "P9", "enriched_at": NOW - timedelta(days=9)}, NOW) is None


def test_a_page_in_search_on_an_old_writer_is_due_a_rewrite_even_while_resting():
    assert enrich.rewrite_due(_in_search(page_text_version=enrich.TEXT_VERSION - 1), NOW)


def test_a_refused_page_waits_before_it_costs_two_more_calls():
    d = _in_search(page_text_version=enrich.TEXT_VERSION - 1, text_refused_at=NOW - timedelta(days=1))
    assert not enrich.rewrite_due(d, NOW)
    assert enrich.rewrite_due({**d, "text_refused_at": NOW - timedelta(days=enrich.THIN_RETRY_DAYS + 1)}, NOW)


def test_pages_in_search_go_first_most_seen_first():
    a, b = _in_search(_id="A", page_text_version=4, gsc_impressions=5), _in_search(_id="B", page_text_version=4, gsc_impressions=50)
    assert enrich.priority(b, set(), NOW, rewrite=True) < enrich.priority(a, set(), NOW, rewrite=True)
    assert enrich.priority(a, set(), NOW, rewrite=True) < (0, 0)


async def test_the_rewrites_stop_at_the_days_cap_and_start_again_the_next_day():
    db, store = await ready(("P1", "Rose Court", "baner", {**FULL}))
    for _ in range(enrich.REWRITES_PER_DAY):
        await enrich.count_rewrite(store, NOW)
    assert await enrich.rewrites_left(store, NOW) == 0
    assert await enrich.rewrites_left(store, NOW + timedelta(days=1)) == enrich.REWRITES_PER_DAY


async def test_no_fact_of_its_own_means_no_model_is_asked_to_write(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "prices": {}, "promoter": "Rohan Builders"}))
    llm = FakeLLM(GOOD)
    out = await enrich.enrich_one(store, await store.project("P1"), llm, NOW)
    assert llm.calls == 0 and not out["text"] and "no text written: no fact of its own yet" in out["notes"]


async def test_with_a_fact_of_its_own_the_writer_runs_last(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, **OWN, "promoter": "Rohan Builders"}))
    llm = FakeLLM(GOOD)
    out = await enrich.enrich_one(store, await store.project("P1"), llm, NOW)
    assert llm.calls >= 1 and out["text"]


async def test_a_tower_costs_no_model_call_and_waits_for_no_reading(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, **OWN, "cluster_primary": "P9", "promoter": "Rohan Builders"}))
    llm = FakeLLM(GOOD)
    out = await enrich.enrich_one(store, await store.project("P1"), llm, NOW)
    assert llm.calls == 0 and not out["reading_due"]


def test_a_tower_is_not_taken_for_a_reading():
    assert enrich.reading_key({"_id": "T", "reading_due": True, "cluster_primary": "P9"}, NOW) is None


def test_the_stock_openings_of_the_first_pages_are_refused():
    for line in ("Rose Court consists of two buildings.", "Rose Court takes shape as one block.", "A boutique footprint.", "A specific part of the wider development."):
        assert enrich.STOCK.search(line), line














# ---- the fact sheet and the points (owner 2026-11-04) ----------------------------------------------------------------------------

SHEET = [{"key": "booked", "text": "Homes booked: 1 of 24 (4%)"}, {"key": "buildings", "text": "Buildings in this registration: 1, up to 4 floors"},
         {"key": "ask0", "text": "the filed completion date has passed, so has the occupancy certificate been given"}]


def _point(label, text, *facts):
    return {"label": label, "text": text, "facts": list(facts)}


def test_a_fact_sheet_says_where_each_fact_came_from():
    doc = {**ROSE, "completion_now": "2031-01-01", "units_total": 24, "units_booked": 1, "source_url": "https://maharera.example/1",
           "building_totals": {"towers": 1, "max_floors": 4}, "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 9000000, "sources": [{"site": "a.com", "url": "https://a.com", "quote": "90 lakh"}]}]}}
    sheet = {f["key"]: f for f in enrich.fact_sheet(doc, None, None, None, False)}
    assert sheet["booked"]["text"] == "Homes booked: 1 of 24 (4%)" and sheet["booked"]["source"] == "MahaRERA"
    assert sheet["booked"]["url"] == "https://maharera.example/1"
    assert sheet["price_2BHK"]["text"] == "2 BHK from \u20b990 L" and sheet["price_2BHK"]["quote"] == "90 lakh"
    assert "filed" in sheet and "worked0" in sheet


def test_a_point_keeps_only_numbers_from_the_facts_it_names():
    kept, why = enrich.points_of({"points": [_point("Very few homes sold", "Only 1 of 24 homes are booked.", "booked"),
                                             _point("Small building", "It has 99 homes.", "buildings")]}, SHEET, ROSE, None)
    assert [x["heading"] for x in kept] == ["Very few homes sold"] and kept[0]["facts"] == ["booked"]
    assert "99" in why[0]


def test_a_point_naming_no_fact_we_hold_goes():
    kept, why = enrich.points_of({"points": [_point("Nice", "It is quiet.", "made_up")]}, SHEET, ROSE, None)
    assert kept == [] and "no fact named" in why[0]


def test_a_question_needs_a_fact_that_raises_it():
    kept, _ = enrich.points_of({"points": [_point("Ask first", "Ask the builder about the certificate.", "ask0"),
                                           _point("Ask this", "Ask the builder about floors.", "buildings")]}, SHEET, ROSE, None)
    assert [x["heading"] for x in kept] == ["Ask first"]


def test_a_point_copying_a_live_outside_page_goes():
    text = "Rose Court keeps its two buildings well apart on a corner plot beside the river road here."
    kept, why = enrich.points_of({"points": [_point("Set apart", text, "buildings")]}, SHEET, ROSE, None, [("99acres.com", "Overview " + text)])
    assert kept == [] and "copies 99acres.com" in why[0]


async def test_points_are_kept_as_sections_with_the_facts_they_used():
    class Model:
        async def json(self, system, user):
            assert "[booked] Homes booked" in user
            return {"points": [_point("Very few homes sold", "Only 1 of 24 homes are booked.", "booked"), _point("A small building", "One block of 4 floors.", "buildings")],
                    "search_summary": "Rose Court, Kharadi: one block of 4 floors, 1 of 24 homes booked so far"}
    draft, why = await enrich.write_points(Model(), ROSE, SHEET)
    assert why == [] and draft["sections"][0] == {"heading": "Very few homes sold", "text": "Only 1 of 24 homes are booked.", "facts": ["booked"]}
    assert draft["text"].startswith("Very few homes sold: Only 1 of 24") and draft["summary"].startswith("Rose Court")


async def test_one_point_is_too_few_and_goes_back_once():
    class Model:
        calls = 0
        async def json(self, system, user):
            Model.calls += 1
            return {"points": [_point("Very few homes sold", "Only 1 of 24 homes are booked.", "booked")]}
    draft, why = await enrich.write_points(Model(), ROSE, SHEET)
    assert draft is None and Model.calls == 2 and "only 1 points kept" in why[0]


def test_a_point_saying_the_date_moved_goes_when_only_the_extension_changed_it_and_the_others_stay(monkeypatch):
    doc = {**ROSE, "completion_now": "2030-04-30", "completion_at_registration": "2029-12-31"}
    monkeypatch.setattr(enrich.pages, "extension_months", lambda d: 4)
    monkeypatch.setattr(enrich.pages, "months_later", lambda d: 0)
    sheet = SHEET + [{"key": "filed", "text": "Completion date filed with MahaRERA: 30 Apr 2030"}]
    kept, why = enrich.points_of({"points": [_point("Date pushed back", "The completion date was moved to 30 Apr 2030.", "filed"),
                                             _point("Very few homes sold", "Only 1 of 24 homes are booked.", "booked")]}, sheet, doc, None)
    assert [x["heading"] for x in kept] == ["Very few homes sold"] and "says the date moved" in why[0]


def test_a_size_says_what_kind_of_area_it_is():
    assert enrich.size_kind("725 sq ft carpet area") == "carpet area"
    assert enrich.size_kind("1,100 sq ft super built-up") == "saleable area"
    assert enrich.size_kind("725 sq ft") == "area kind not stated"


def test_the_fact_sheet_keeps_the_size_beside_its_price():
    row = {"bhk": "2 BHK", "from_inr": 9000000, "sources": [{"site": "a.com", "url": "https://a.com", "quote": "725 sq. ft. carpet area at 90 lakh"}]}
    sheet = {f["key"]: f for f in enrich.fact_sheet({**ROSE, "prices": {"rows": [row]}}, None, None, None, False)}
    assert sheet["size_2BHK"]["text"] == "2 BHK size from 725 sq ft, carpet area" and sheet["size_2BHK"]["source"] == "a.com"


def test_homes_per_acre_needs_homes_and_land_to_cover_the_same_ground():
    land = {"key": "land_acres", "value": 2.5}
    assert enrich.homes_per_acre({"name": "Rose Court", "units_total": 450}, land, {}) == 180
    assert enrich.homes_per_acre({"name": "Rose Court Phase 2", "units_total": 450}, land, {}) is None
    assert enrich.homes_per_acre({"name": "Rose Court", "units_total": 450, "cluster_id": "c"}, land, {}) is None
    assert enrich.homes_per_acre({"name": "Rose Court", "units_total": 450}, land, {"towers": 2}) is None
    assert enrich.homes_per_acre({"name": "Rose Court", "units_total": 450}, None, {}) is None


def test_a_superlative_or_an_average_goes():
    for text in ("The tallest project in the area.", "It has more homes than the average."):
        kept, why = enrich.points_of({"points": [_point("Stands out", text, "buildings")]}, SHEET, ROSE, None)
        assert kept == [] and "overclaims" in why[0]


def test_one_part_of_a_project_is_not_ranked_by_its_homes():
    doc = {**ROSE, "name": "Kharadi New Project Tower 5", "locality": "kharadi", "units_total": 4, "completion_now": "2031-01-01", "building_totals": {"towers": 1, "max_floors": 2}}
    area = [_building(i, floors=10 + i) for i in range(9)]
    lines = enrich.area_context(doc, area)
    assert any("higher than" in x for x in lines) and not any("more homes" in x for x in lines)
    homes = next(f for f in enrich.fact_sheet(doc, None, None, None, False) if f["key"] == "homes")
    assert "one part of a bigger project" in homes["text"]


def test_a_brand_filing_through_its_own_company_raises_no_question():
    assert enrich.worth_asking({**ROSE, "name": "Lodha Camelot", "promoter": "Lodha Developers Limited", "completion_now": "2031-01-01"}, None) == []


async def test_a_label_on_other_pages_goes_back_then_goes():
    others = [{"_id": f"O{i}", "name": f"Other {i}", "page_text": "x", "page_text_version": 7, "page_sections": [{"heading": "Taller than most"}]} for i in range(3)]

    class Model:
        asked = []
        async def json(self, system, user):
            Model.asked.append(user)
            return {"points": [_point("Taller than most", "One block of 4 floors.", "buildings"), _point("Only 4% booked", "Just 1 of 24 homes.", "booked"), _point("Ask on the certificate", "Ask the builder about it.", "ask0")]}
    draft, why = await enrich.write_points(Model(), ROSE, SHEET, others=others)
    assert len(Model.asked) == 2 and "Taller than most" in Model.asked[1]
    assert why == [] and [x["heading"] for x in draft["sections"]] == ["Only 4% booked", "Ask on the certificate"]


def test_a_place_outside_our_areas_is_compared_under_its_own_name():
    doc = {**ROSE, "pune_place": "tathawade", "pune_place_name": "Tathawade", "completion_now": "2031-01-01", "building_totals": {"towers": 1, "max_floors": 30}}
    lines = enrich.area_context(doc, [_building(i, floors=10 + i) for i in range(9)])
    assert any("being built in Tathawade" in x and "9 of 9" in x for x in lines)


async def test_a_refused_draft_leaves_points_that_do_not_repeat_the_name(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders", "page_text": "Few homes left: Most are booked.",
                                                                     "page_text_version": enrich.TEXT_VERSION, "page_sections": [{"heading": "Few homes left", "text": "Most are booked."}]}))
    await enrich.enrich_one(store, await store.project("P1"), FakeLLM("A luxury project."), NOW)
    doc = await store.project("P1")
    assert doc["page_text"] == "Few homes left: Most are booked." and doc["page_sections"]


TABLE = "Configuration\n2 BHK\n725 - 780 sq ft Carpet Area\n3 BHK\n1,050 sq ft Carpet Area\nClub house"


def test_a_size_table_is_read_without_a_price_and_without_a_model():
    from app.modules.areastats import prices
    found = prices.sizes_on(TABLE)
    assert (found["2 BHK"]["low"], found["2 BHK"]["high"], found["2 BHK"]["kind"]) == (725, 780, "carpet area")
    assert found["3 BHK"]["low"] == 1050


def test_a_page_sizing_many_kinds_of_home_is_a_list_and_gives_nothing():
    from app.modules.areastats import prices
    many = "\n".join(f"{n} BHK 1,500 sq ft" for n in ("2", "2.5", "3", "3.5", "4"))
    assert prices.sizes_on(many) == {}


def test_a_size_no_home_could_be_is_left_out():
    from app.modules.areastats import prices
    assert prices.sizes_on("2 BHK towers on 5,000 sq ft of retail") == {}


WEB = {"read": [{"site": "builder.com", "official": True, "url": "https://builder.com/p", "why": "2 facts"},
                {"site": "a.com", "url": "https://a.com/p", "why": "1 facts"}, {"site": "b.com", "url": "https://b.com/p", "why": "0 facts"},
                {"site": "x.com", "url": "https://x.com/p", "why": "page does not name the project"}]}


def test_the_builders_site_alone_publishes_a_size():
    rows = enrich.home_sizes([("builder.com", "2 BHK 725 sq ft carpet")], WEB)
    assert rows[0]["bhk"] == "2 BHK" and rows[0]["official"] and rows[0]["low"] == 725


def test_two_sites_must_agree_and_one_alone_is_said_to_be_one():
    one = enrich.home_sizes([("a.com", "2 BHK 725 sq ft")], WEB)
    assert one[0]["one_site"] and one[0]["low"] == 725
    assert [r["sites"] for r in enrich.home_sizes([("a.com", "2 BHK 725 sq ft"), ("b.com", "2 BHK 740 sq ft")], WEB)] == [["a.com", "b.com"]]
    assert enrich.home_sizes([("a.com", "2 BHK 725 sq ft"), ("b.com", "2 BHK 1100 sq ft")], WEB) == []


def test_a_page_not_about_the_project_counts_for_nothing():
    assert [r["sites"] for r in enrich.home_sizes([("a.com", "2 BHK 725 sq ft"), ("x.com", "2 BHK 725 sq ft")], WEB)] == [["a.com"]]


def test_a_size_goes_on_the_fact_sheet_with_its_kind():
    doc = {**ROSE, "home_sizes": [{"bhk": "2 BHK", "low": 725, "high": 780, "kind": "carpet area", "sites": ["builder.com"], "url": "u", "quote": "q"}]}
    sheet = {f["key"]: f for f in enrich.fact_sheet(doc, None, None, None, False)}
    assert sheet["size_2BHK"]["text"] == "2 BHK size: 725 to 780 sq ft, carpet area"


def test_a_building_word_is_not_an_overclaim():
    kept, _ = enrich.points_of({"points": [_point("One tall block", "Its highest building has 4 floors, on average about 1 home.", "buildings", "booked")]}, SHEET, ROSE, None)
    assert [x["heading"] for x in kept] == ["One tall block"]


def test_code_writes_points_when_a_page_with_facts_has_no_text():
    out = enrich.code_points(ROSE, SHEET + [{"key": "filed", "text": "Completion date filed with MahaRERA: 30 Apr 2030"}])
    assert [x["heading"] for x in out["sections"]][0] == "4% of homes booked" and "1 of 24" in out["text"] and "30 Apr 2030" in out["text"]


def test_code_writes_nothing_from_too_little():
    assert enrich.code_points(ROSE, [{"key": "homes", "text": "Homes in this registration: 9"}]) is None


async def test_a_page_with_facts_keeps_a_text_when_every_draft_fails(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders", "building_totals": {"towers": 2, "max_floors": 9}}))
    await enrich.enrich_one(store, await store.project("P1"), FakeLLM("A luxury project."), NOW)
    doc = await store.project("P1")
    assert doc["page_text"] and doc["page_text_version"] == enrich.TEXT_VERSION and len(doc["page_sections"]) >= 2


def test_a_size_from_one_site_says_so_and_brings_no_page_into_search():
    doc = {**ROSE, "home_sizes": [{"bhk": "2 BHK", "low": 725, "high": 725, "kind": "carpet area", "one_site": True, "sites": ["a.com"]}]}
    assert not enrich.pages.own_facts(doc)
    assert "on one property site" in next(f for f in enrich.fact_sheet(doc, None, None, None, False) if f["key"] == "size_2BHK")["text"]
    assert enrich.pages.own_facts({**doc, "home_sizes": [{**doc["home_sizes"][0], "one_site": False}]})


def test_the_sheet_names_the_brand_beside_the_filing_company():
    doc = {**ROSE, "name": "Lodha Camelot", "promoter": "Lodha Developers Limited"}
    assert "brand Lodha" in next(f for f in enrich.fact_sheet(doc, None, None, None, False) if f["key"] == "brand")["text"]


def test_a_project_finishing_before_2027_gets_no_model():
    assert not enrich.worth_model({"completion_now": "2026-12-31"})
    assert enrich.worth_model({"completion_now": "2027-01-01"})
    assert enrich.worth_model({})   # a date not read yet is no reason to skip it


def test_a_project_finishing_before_2027_is_not_priced():
    doc = {"page_slug": "x", "promoter": "Rose LLP", "project_type": "Residential", "completion_now": "2026-12-31", "units_total": 100, "units_booked": 10}
    assert not enrich.pricing.selling(doc, NOW)
    assert enrich.pricing.selling({**doc, "completion_now": "2027-06-30"}, NOW)


def test_a_record_with_no_pincode_is_measured_from_its_areas():
    assert enrich.area_pincode({"locality": "upper_kharadi"}) == "411014"
    assert enrich.area_pincode({"locality": "lohegaon"}) == "411047"
    assert enrich.area_pincode({"locality": "hinjawadi"}) == "411057"
    assert enrich.area_pincode({"pune_place": "moshi"}) is None


READ_DOC = {**ROSE, "booked_history": [{"at": datetime(2026, 8, 1, tzinfo=timezone.utc), "booked": 10}, {"at": datetime(2026, 11, 1, tzinfo=timezone.utc), "booked": 50}],
            "fact_sheet": {"facts": [{"key": "booked", "text": "Homes booked: 50 of 100 (50%)"},
                                     {"key": "area_booked", "text": "50% booked here; the middle of 20 Kharadi projects is 30%"}]}}


class Reads:
    def __init__(self, text, facts=("read_pace", "booked")):
        self.text, self.facts, self.calls = text, list(facts), 0

    async def json(self, system, user):
        self.calls += 1
        assert "[read_pace] 40 more homes booked" in user
        return {"read": self.text, "facts": self.facts}


async def test_the_read_is_kept_from_the_facts_and_written_once():
    db, store = await ready(("P1", "Rose Court", "kharadi", {**FULL}))
    llm = Reads("Half the homes are gone, and 40 more homes were booked in about three months, which is quick for this project.")
    assert (await enrich.buyer_read(store, {**READ_DOC, "_id": "P1"}, llm, NOW))["facts"] == ["read_pace", "booked"]
    doc = await store.project("P1")
    assert doc["page_read"]["text"].startswith("Half the homes")
    assert await enrich.buyer_read(store, {**READ_DOC, "_id": "P1", "page_read": doc["page_read"]}, llm, NOW) is None and llm.calls == 1


async def test_too_little_to_read_asks_no_model():
    db, store = await ready(("P1", "Rose Court", "kharadi", {**FULL}))
    llm = Reads("x")
    assert await enrich.buyer_read(store, {**ROSE, "_id": "P1", "fact_sheet": {"facts": READ_DOC["fact_sheet"]["facts"][:1]}}, llm, NOW) is None and llm.calls == 0


async def test_a_read_suggesting_a_visit_or_a_number_not_in_its_facts_is_not_kept():
    db, store = await ready(("P1", "Rose Court", "kharadi", {**FULL}))
    for text in ("Our team visited the site and 40 more homes were booked, which looks quick for this project overall.",
                 "About 77 more homes were booked in those months, which is quick for a project of this kind here."):
        assert await enrich.buyer_read(store, {**READ_DOC, "_id": "P1"}, Reads(text), NOW) is None
    assert "page_read" not in await store.project("P1")


def test_the_read_is_given_the_middle_in_plain_words():
    assert enrich.plain_middle("88% booked here; the middle of 13 Kharadi projects registered within a year of it is 86%") == "88% booked here; 13 similar Kharadi projects are at about 86%"


async def test_a_read_that_predicts_is_not_kept():
    db, store = await ready(("P1", "Rose Court", "kharadi", {**FULL}))
    text = "Half the homes are gone and 40 more homes were booked lately, so the builder will likely meet its date this time."
    assert await enrich.buyer_read(store, {**READ_DOC, "_id": "P1"}, Reads(text), NOW) is None


def test_the_builders_other_projects_are_no_word_on_this_ones_date():
    text = "Half the homes are booked. Across Pune, 8 of its 59 projects moved their dates by 3 months."
    assert enrich.this_project(text) == "Half the homes are booked."
    assert not enrich.says_moved(enrich.this_project(text))
    assert enrich.says_moved(enrich.this_project("The completion date was moved to 2031."))
