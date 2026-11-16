"""Search holds still (docs/plan/search-recovery.md R1): a page in search keeps its place and its text for a while, and is
rewritten only when its own facts change."""
from datetime import timedelta

from app.modules.areastats import enrich, pages

from .test_enrich import FULL as WITH_PRICE, FakeLLM, GOOD, NOW, POINTS_TEXT, ready
from .test_pages import FULL

READY = {**FULL, "page_text": "Few homes left: Few homes are left to book here.", "prices": {"rows": [{"bhk": "2 BHK"}]}}
THIN = {**READY, "prices": {"rows": []}}            # its one fact of its own gone: not ready for search
IN = {"in": True, "at": NOW - timedelta(days=5)}
OUT = {"in": False, "at": NOW - timedelta(days=5)}


def test_a_page_never_in_search_goes_in_once_ready():
    assert pages.searchable(READY, NOW) and not pages.searchable(THIN, NOW)
    assert pages.search_state(READY, NOW) == {"in": True, "at": NOW}
    assert pages.search_state(THIN, NOW) is None             # no hold to wait out when it is filled


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
    assert doc["search_state"] == {"in": True, "at": NOW}

    await store.set_project("P1", enriched_at=None)
    llm = FakeLLM("Another text. With other words.")
    out = await enrich.step(store, llm, NOW + timedelta(days=1), None, timedelta(minutes=30))
    doc = await store.project("P1")
    assert doc["page_text"] == POINTS_TEXT and doc["page_text_at"] == NOW
    assert "text kept: in search and its own facts have not changed" in out["notes"]


def test_no_page_in_search_is_given_to_a_newer_writer():
    assert enrich.REWRITES_PER_DAY == 0


FACTS = {"page_text": "Written.", "page_text_by": "model", "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 5000000}]},
         "web_facts": {"facts": [{"key": "land_acres"}]}, "profile": {"highlights": [{"text": "Clubhouse"}]}}
OUTSIDE = {"completion_now": "2029-06-30", "promoter": "Kolte Patil", "pune_place": "moshi"}


def test_a_page_outside_our_areas_goes_in_only_fully_enriched():
    assert pages.searchable({**OUTSIDE, **FACTS}, NOW)
    assert not pages.searchable({**OUTSIDE, **FACTS, "profile": {}}, NOW)                         # two kinds of fact
    assert not pages.searchable({**OUTSIDE, **FACTS, "page_text_by": "code"}, NOW)                # no model text


def test_a_page_outside_our_areas_already_in_search_stays_by_the_rule_it_came_in_by():
    held = {"in": True, "at": NOW - timedelta(days=90)}
    assert pages.searchable({**OUTSIDE, **FACTS, "profile": {}, "search_state": held}, NOW)


def test_a_page_in_our_areas_needs_no_more_than_before():
    assert pages.searchable({**OUTSIDE, **FACTS, "profile": {}, "page_text_by": "code", "locality": "kharadi"}, NOW)


def test_offices_outside_our_areas_need_one_kind_less_and_a_flat_price_counts_for_nothing():
    offices = {**OUTSIDE, **FACTS, "project_type": "Commercial"}
    assert pages.searchable(offices, NOW)
    assert not pages.searchable({**offices, "web_facts": {}}, NOW)



def test_a_page_outside_our_areas_watched_only_because_it_was_read_still_needs_to_be_fully_enriched():
    read = {**OUTSIDE, **FACTS, "profile": {}, "watched_by": ["property_facts"]}
    assert not pages.searchable(read, NOW)
    assert pages.searchable({**read, "watched_by": ["agent_projects", "property_facts"]}, NOW)
