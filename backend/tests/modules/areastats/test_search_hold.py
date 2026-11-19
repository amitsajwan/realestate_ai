"""Search holds still (docs/plan/search-recovery.md R1): a page in search keeps its place and its text for a while, and is
rewritten only when its own facts change."""
from datetime import timedelta

from app.modules.areastats import enrich, entry, pages

from .test_enrich import FULL as WITH_PRICE, FakeLLM, GOOD, NOW, POINTS_TEXT, ready
from .test_pages import FULL

READY = {**FULL, "page_text": "Few homes left: Few homes are left to book here.", "prices": {"rows": [{"bhk": "2 BHK"}]}}
THIN = {**READY, "prices": {"rows": []}}            # its one fact of its own gone: not ready for search
IN = {"in": True, "at": NOW - timedelta(days=5)}
OUT = {"in": False, "at": NOW - timedelta(days=5)}


def test_a_page_never_in_search_waits_its_turn_once_ready():
    assert pages.searchable(READY, NOW) and not pages.searchable(THIN, NOW)
    assert pages.search_state(READY, NOW) == {"wait": True, "at": NOW}
    assert pages.search_state(THIN, NOW) is None             # no hold to wait out when it is filled


def test_a_waiting_page_is_out_of_search_until_let_in():
    waiting = {**READY, "search_state": {"wait": True, "at": NOW}}
    assert not pages.searchable(waiting, NOW) and pages.waiting(waiting)
    assert pages.search_state(waiting, NOW) is None          # only areastats.entry lets it in
    assert pages.searchable({**READY, "search_state": {"in": True, "at": NOW}}, NOW)


def test_a_page_in_search_stays_in_when_it_loses_a_fact():
    assert pages.searchable({**THIN, "search_state": IN}, NOW)
    assert pages.search_state({**THIN, "search_state": IN}, NOW) is None


def test_a_page_held_in_leaves_at_once_when_it_breaks():
    assert not pages.searchable({**THIN, "search_state": IN, "page_text": None}, NOW)       # no text
    assert not pages.searchable({**THIN, "search_state": IN, "completion_now": "2015-01-01"}, NOW)   # finished
    assert not pages.searchable({**THIN, "search_state": IN, "completion_now": None}, NOW)  # not listable


def test_a_page_that_left_search_stays_out_when_ready_again():
    assert not pages.searchable({**READY, "search_state": OUT}, NOW)
    assert pages.search_state({**READY, "search_state": OUT}, NOW) is None


def test_after_the_hold_the_rule_decides_again():
    later = NOW + timedelta(days=pages.SEARCH_HOLD_DAYS)
    assert not pages.searchable({**THIN, "search_state": IN}, later)
    assert pages.search_state({**THIN, "search_state": IN}, later) == {"in": False, "at": later}
    assert pages.searchable({**READY, "search_state": OUT}, later)
    assert pages.search_state({**READY, "search_state": OUT}, later) == {"wait": True, "at": later}   # back in by its turn


def test_only_the_projects_own_lines_decide_a_rewrite():
    sheet = [{"key": "booked", "text": "Homes booked: 10 of 100 (10%)"}, {"key": "area0", "text": "Taller than 5 of 9"},
             {"key": "ask0", "text": "Ask about the parking"}, {"key": "builder_record", "text": "2 of 4 moved"}]
    key = enrich.own_facts_key(sheet)
    around = [sheet[0], {"key": "area0", "text": "Taller than 6 of 10"}, {"key": "ask0", "text": "Ask about water"}]
    assert enrich.own_facts_key(around) == key
    assert enrich.own_facts_key([{"key": "booked", "text": "Homes booked: 12 of 100 (12%)"}, *sheet[1:]]) != key


def test_a_settled_page_is_one_in_search_with_model_text_and_the_same_facts():
    page = {**READY, "page_facts_key": "k"}
    assert enrich.settled(page, "k", NOW)
    assert enrich.settled({**READY}, "k", NOW)                          # written before the key: kept, the key stored
    assert not enrich.settled(page, "other", NOW)                       # its own facts changed
    assert not enrich.settled({**page, "page_text_by": "code"}, "k", NOW)   # code's stopgap points give way
    assert not enrich.settled({**THIN, "page_facts_key": "k"}, "k", NOW)   # not in search: written as before


async def test_a_page_in_search_is_not_rewritten_while_its_facts_stand():
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**WITH_PRICE, "promoter": "Rohan Builders"}))
    await enrich.step(store, FakeLLM(GOOD), NOW, None, timedelta(minutes=30))
    doc = await store.project("P1")
    assert doc["page_text"] == POINTS_TEXT and doc["page_text_by"] == "model" and doc["page_facts_key"]
    assert doc["search_state"] == {"wait": True, "at": NOW}
    await entry.admit(store, NOW)
    assert (await store.project("P1"))["search_state"] == {"in": True, "at": NOW}

    await store.set_project("P1", enriched_at=None)
    llm = FakeLLM("Another text. With other words.")
    out = await enrich.step(store, llm, NOW + timedelta(days=1), None, timedelta(minutes=30))
    doc = await store.project("P1")
    assert doc["page_text"] == POINTS_TEXT and doc["page_text_at"] == NOW
    assert "text kept: in search and its own facts have not changed" in out["notes"]


def test_no_page_in_search_is_given_to_a_newer_writer():
    assert enrich.REWRITES_PER_DAY == 0


OUTSIDE = {"completion_now": "2029-06-30", "promoter": "Kolte Patil", "pune_place": "moshi"}


ONE_FACT = {"page_text": "Written.", "page_text_by": "code", "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 5000000}]}}


def test_a_page_outside_our_areas_goes_in_with_text_and_one_fact_of_its_own_as_ours_do():
    assert pages.searchable({**OUTSIDE, **ONE_FACT}, NOW)                                         # owner 2026-11-19
    assert pages.searchable({**OUTSIDE, **ONE_FACT, "watched_by": ["property_facts"]}, NOW)
    assert not pages.searchable({**OUTSIDE, **ONE_FACT, "prices": {}}, NOW)                       # no fact of its own
    assert not pages.searchable({**OUTSIDE, **ONE_FACT, "page_text": None}, NOW)                  # no text


def test_offices_outside_our_areas_need_a_fact_other_than_a_flat_price():
    offices = {**OUTSIDE, **ONE_FACT, "project_type": "Commercial"}
    assert not pages.searchable(offices, NOW)
    assert pages.searchable({**offices, "web_facts": {"facts": [{"key": "land_acres"}]}}, NOW)
