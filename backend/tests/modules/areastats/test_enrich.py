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
    """Answers with the text's paragraphs as the sections, in SECTIONS order, and a search line."""
    def __init__(self, text):
        self.text, self.calls = text, 0

    async def json(self, system, user):
        self.calls += 1
        return {"sections": [{"heading": h, "text": t} for h, t in zip(enrich.SECTIONS, self.text.split("\n\n"))],
                "search_summary": "Rohan Abhilasha 4, Wagholi: homes by Rohan Builders, registered with MahaRERA"}


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
    doc = await store.project("P1")
    assert doc["page_text"] == GOOD and doc["page_text_version"] == enrich.TEXT_VERSION
    page = await pages.project_page(db, doc["page_slug"])
    assert [s["heading"] for s in page["sections"]] == ["The project", "Location"] and page["enriched_at"] == "2026-10-06"
    assert page["search_description"] == "Rohan Abhilasha 4, Wagholi: homes by Rohan Builders, registered with MahaRERA"


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


def test_facts_label_both_dates_and_leave_distances_to_the_page():
    doc = {**FULL, "_id": "P1", "name": "Ivy", "locality": "wagholi", "regno": "P1"}
    g = {"nearby": [{"label": "Hospital", "name": "HOSPITAL 9", "km": 0.5}, {"label": "Hospital", "name": "Care Hospital", "km": 0.6}]}
    facts = enrich.facts_text(doc, g)
    assert "Completion date filed when the project was registered: 31 Dec 2028 (this is a completion date, not the registration date)" in facts
    assert "Care Hospital" not in facts and "km" not in facts   # the page lists them beside the map


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
    new = {"_id": "N", "page_slug": "n", "locality": "wagholi", **FULL, "units_booked": None}   # homes open unknown: not on a top list
    keys = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (old, seen, new)])
    assert [k[1] for k in keys] == ["S", "O", "N"]
    assert enrich.priority({**old, "enrichment": {"score": "4/4"}, "page_text_version": enrich.TEXT_VERSION}, set(), NOW) is None
    assert enrich._priority({**old, "enrichment": {"score": "4/4"}}, NOW)[0] == enrich.BACKFILL   # an older writer's text


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
    assert [k[1] for k in order] == ["N", "L"]                                 # hot first, in every area (owner 2026-10-22)
    hot_free = {**later, "_id": "H", "hot_score": 99}
    order = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (nearly, later, hot_free)])
    assert [k[1] for k in order] == ["H", "N", "L"]                            # 90% booked waits behind the other hot ones


def test_our_areas_outward_from_kharadi_and_new_launches_or_hot_first():
    base = {"page_slug": "x", **FULL, "registered_on": "2020-01-01", "units_booked": None}   # homes open unknown: no top list
    wakad = {**base, "_id": "W", "locality": "wakad", "pune_place": "wakad", "hot_score": 99}
    lohegaon = {**base, "_id": "L", "locality": "lohegaon", "pune_place": "lohegaon"}
    kharadi_old = {**base, "_id": "K", "locality": "kharadi", "pune_place": "kharadi", "gsc_impressions": 500}
    kharadi_new = {**base, "_id": "N", "locality": "kharadi", "pune_place": "kharadi", "registered_on": "2026-08-01"}
    upper = {**base, "_id": "U", "locality": "upper_kharadi", "pune_place": "upper_kharadi"}
    order = sorted([(enrich.priority(d, set(), NOW), d["_id"]) for d in (wakad, lohegaon, kharadi_old, kharadi_new, upper)])
    assert [k[1] for k in order] == ["W", "U", "N", "K", "L"]                  # hot first in every area, then outward from Kharadi


# Godrej Ivara on 2026-10-22: registered Feb 2026, MahaRERA's Order 66/2026 added 4 months, the builder moved nothing
IVARA = {"_id": "PR1260002502426", "regno": "PR1260002502426", "name": "Godrej Ivara", "locality": "upper_kharadi",
         "promoter": "Manjari Housing Projects LLP", "registered_on": "2026-02-20", "completion_at_registration": "2032-08-16",
         "completion_now": "2032-12-16", "units_total": 2792, "units_booked": 489}


class DraftLLM:
    """Answers with the given section texts ("The project", then "Location"); records what it was asked and forgotten."""
    def __init__(self, *texts, summary="Godrej Ivara, Upper Kharadi: homes by Manjari Housing, completion 16 Dec 2032", answer=None):
        self.texts, self.summary, self.answer, self.asked, self.forgot = texts, summary, answer, [], []

    async def json(self, system, user):
        self.asked.append(user)
        if self.answer is not None:
            return self.answer
        return {"sections": [{"heading": h, "text": t} for h, t in zip(enrich.SECTIONS, self.texts)],
                "search_summary": self.summary}

    async def forget(self, system, user):
        self.forgot.append(user)


IVARA_PROJECT = ("Godrej Ivara is a housing project by Manjari Housing Projects LLP, sold under the Godrej Properties brand, in "
                 "Upper Kharadi, Pune.")


async def test_a_draft_calling_maharera_s_blanket_extension_a_move_is_refused():
    for moved in ("The builder has moved the completion date later.", "The completion date was pushed back by the builder.",
                  "Its completion date shows an increase over the first one.", "The developer extended the completion date."):
        llm = DraftLLM(IVARA_PROJECT + " " + moved)
        draft, refused = await enrich.write_text(llm, IVARA, None)
        assert draft is None, moved
        assert any("2026 extension" in r for r in refused), moved
        assert llm.forgot == llm.asked                           # a budgeted client asks again next round
    draft, refused = await enrich.write_text(DraftLLM(IVARA_PROJECT + " The builder has not moved its completion date."), IVARA, None)
    assert refused == [] and draft["text"] == IVARA_PROJECT + " The builder has not moved its completion date."


async def test_a_draft_whose_first_sentence_repeats_the_name_is_refused():
    garbled = ("Godrej Ivara Godrej Properties Godrej Ivara, developed by Manjari Housing Projects LLP, is a housing project in "
               "Upper Kharadi, Pune. It is registered with MahaRERA.")
    draft, refused = await enrich.write_text(DraftLLM(garbled), IVARA, None)
    assert draft is None
    assert "the first sentence names Godrej Ivara twice" in refused


def test_the_writer_is_told_the_blanket_extension_is_the_whole_difference():
    facts = enrich.facts_text(IVARA, None)
    assert "the builder did not move it" in facts
    builder_moved = {**IVARA, "completion_now": "2033-06-16"}
    assert "the builder did not move it" not in enrich.facts_text(builder_moved, None)


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


def test_the_writer_is_told_what_the_page_shows_and_which_counts_are_the_whole_projects():
    facts = enrich.facts_text(EDEN, EDEN_NEAR, EDEN_WEB, None, pinned=True)
    assert ("Towers: 5 for the whole project, from the builder's site (parkeden.in); this registration has 2 with MahaRERA"
            in facts)
    assert "Land: 7.5 acres (from parkeden.in)" in facts           # not a count of this registration: as it is
    shown = "\n".join(enrich.on_page(EDEN))
    assert "Completion date filed with MahaRERA: 28 Feb 2031 (at registration 31 Oct 2030); it changed only by MahaRERA's order" in shown
    assert "Homes: 249 in this registration, 27 booked" in shown and "3 BHK from Rs 19,900,000" in shown
    assert "BHK types: 3 BHK, 4 BHK" in shown
    # fewer or as many towers on the web as MahaRERA registers: nothing to scope
    assert enrich.whole_project_counts({**EDEN, "building_totals": {"towers": 5}}, EDEN_WEB) == []


async def test_park_eden_drafts_that_repeat_the_page_or_misscope_a_count_are_refused():
    async def write(*texts):
        llm = DraftLLM(*texts, summary=EDEN_SUMMARY)
        draft, refused = await enrich.write_text(llm, EDEN, EDEN_NEAR, EDEN_WEB, None, pinned=True)
        assert ("ALREADY ON THE PAGE (do not repeat):" in llm.asked[0] and "27 booked" in llm.asked[0])
        assert llm.forgot == ([] if draft else llm.asked)
        return draft, refused

    draft, refused = await write(EDEN_PROJECT + " 27 of the 249 homes are booked.", EDEN_LOCATION)
    assert draft is None and "repeats the homes total (249)" in refused and "repeats the booking count (27)" in refused
    draft, refused = await write(EDEN_PROJECT + " Of its homes, 222 are still available.", EDEN_LOCATION)
    assert draft is None and "repeats the homes left (222)" in refused
    draft, refused = await write(EDEN_PROJECT + " Its completion date is 28 Feb 2031, an increase from 31 Oct 2030.", EDEN_LOCATION)
    assert draft is None
    assert {"repeats the completion date (28 Feb 2031)", "repeats the completion date (31 Oct 2030)",
            "says the date moved, but the only change is MahaRERA's 2026 extension"} <= set(refused)
    misscoped = EDEN_PROJECT.replace("This registration covers two buildings of up to 22 floors; the whole project has five "
                                     "towers on 7.5 acres, according to the builder's site.",
                                     "It has five towers of up to 22 floors on 7.5 acres.")
    draft, refused = await write(misscoped, EDEN_LOCATION)
    assert draft is None and "gives the whole project's towers (5) as this registration's (2)" in refused
    draft, refused = await write(EDEN_PROJECT + " Homes start at Rs 1.99 Cr.", EDEN_LOCATION)
    assert draft is None and "gives a price (the page shows the prices)" in refused
    draft, refused = await write(EDEN_PROJECT, "No specific nearby places are mentioned in the provided facts.")
    assert draft is None and 'the "Location" section is empty or says nothing' in refused

    draft, refused = await write(EDEN_PROJECT, EDEN_LOCATION)
    assert refused == []
    assert draft == {"text": EDEN_PROJECT + "\n\n" + EDEN_LOCATION, "summary": EDEN_SUMMARY,
                     "sections": [{"heading": "The project", "text": EDEN_PROJECT},
                                  {"heading": "Location", "text": EDEN_LOCATION}]}


async def test_an_accepted_draft_is_stored_as_sections_with_the_search_line():
    db, store = await ready((EDEN["_id"], EDEN["name"], "kharadi",
                             {**{k: v for k, v in EDEN.items() if k not in ("_id", "name")}, "web_facts": EDEN_WEB}))
    llm = DraftLLM(EDEN_PROJECT, summary=EDEN_SUMMARY)
    await enrich.enrich_one(store, await store.project(EDEN["_id"]), llm, NOW, reread=False)
    doc = await store.project(EDEN["_id"])
    assert doc["page_sections"] == [{"heading": "The project", "text": EDEN_PROJECT}]
    assert doc["page_text"] == EDEN_PROJECT and doc["page_summary"] == EDEN_SUMMARY and doc["page_text_version"] == 4


def test_an_answer_in_an_older_writers_shape_is_no_draft_and_does_not_crash():
    for old in ({"text": GOOD}, {"summary": GOOD, "sections": [], "search_summary": "x"}, None, "text", {"sections": "x"},
                {"sections": [None, {"heading": 3}, {"heading": "The homes and the building", "text": GOOD}]}):
        assert enrich.draft_of(old)["sections"] == [] and enrich.draft_of(old)["text"] == ""
    facts = enrich.facts_text(EDEN, None)
    assert 'no "The project" section' in enrich.refused(EDEN, None, enrich.draft_of({"summary": GOOD}), facts)
    # headings as the model may case them are the page's headings
    assert enrich.draft_of({"sections": [{"heading": "the project", "text": EDEN_PROJECT}]})["sections"][0]["heading"] == "The project"


def test_pages_written_by_an_older_writer_are_rewritten_after_everything_else():
    old = {"_id": "O", "page_slug": "o", "locality": "baner", **FULL, "enriched_at": NOW - timedelta(days=3),
           "enrichment": {"score": "4/4", "steps": {"web": {"ok": True, "at": NOW - timedelta(days=3)}}}, "page_text_version": 3}
    assert enrich.TEXT_VERSION == 4
    key = enrich._priority(old, NOW)
    assert key[:2] == (enrich.BACKFILL, 0)                        # web pages read lately: a cheap rewrite (one model call)
    assert enrich._priority({**old, "page_text_version": 4}, NOW) is None


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
    assert out["reading"] and out["text"] and doc["page_text"] == GOOD and not doc["reading_due"]
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
    await store.set_project("P1", enrichment={"steps": {"text": kept_text}}, page_text=GOOD)
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
