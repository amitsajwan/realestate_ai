"""A title from a search keeps the number that tells one phase from another."""
from app.modules.seo import targets

YASH = {"name": "Yash Residency Phase 2 “A Wing”", "locality": "baner"}
AEROPOLIS = {"name": "Aeropolis Phase II", "locality": "lohegaon"}


def test_the_number_after_a_phase_stays_in_the_name():
    assert targets.readable("yash residency phase 2", YASH) == "Yash Residency Phase 2"


def test_people_searching_phase_2_match_a_project_filed_as_phase_ii():
    assert targets.readable("aeropolis phase 2", AEROPOLIS) == "Aeropolis Phase 2"


def test_another_phase_than_the_page_is_not_its_name():
    assert targets.readable("aeropolis phase 3", AEROPOLIS) is None


def test_a_name_ending_on_a_bare_phase_is_cut_short():
    assert targets.readable("aeropolis phase", AEROPOLIS) is None
    assert targets.readable("aeropolis phase 2 bhk", AEROPOLIS) is None


def test_sizes_and_prices_are_still_dropped():
    assert targets.readable("yash residency 2 bhk price", YASH) == "Yash Residency"
