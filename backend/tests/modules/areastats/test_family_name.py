"""The whole project's name, which sites use for all its MahaRERA registrations (areastats.pages.family_name)."""
import pytest

from app.modules.areastats import pages


@pytest.mark.parametrize("name,family", [
    ("Pristine O2 World Part 3", "Pristine O2 World"),
    ("Mahindra IvyLush Tower C and Tower D", "Mahindra IvyLush"),
    ("Gera Avive Towers Phase I", "Gera Avive Towers"),
    ("Gera Island of Joy Project", "Gera Island of Joy"),
    ("Majestique Tower East Phase-9", "Majestique Tower East"),
    ("GG Town Wagholi Phase B Building 8 and 9", "GG Town Wagholi"),
    ("Ganga Arcadia A Building", "Ganga Arcadia"),
    ("Laxmi Emerald C Wing", "Laxmi Emerald"),
    ("Pristine Allure PART2", "Pristine Allure"),
    ("Leela by Empyrean Landmarks Ph2", "Leela by Empyrean Landmarks"),
    ("Eastern Royale Building No. 2", "Eastern Royale"),
    ("Hollyhock City Building No.5 Wing E1 & E2", "Hollyhock City"),
])
def test_what_mahareras_registration_adds_comes_off(name, family):
    assert pages.family_name({"name": name, "promoter": "B"}) == family


@pytest.mark.parametrize("name", ["Lake Tower", "Tierra Phase 2", "Godrej Ivara", "Sky Wings", "Happy Homes Amenity Building"])
def test_a_name_that_would_match_other_things_stays_whole(name):
    assert pages.family_name({"name": name, "promoter": "B"}) == name


def test_a_name_left_with_only_place_words_stays_whole():
    doc = {"name": "Kharadi Pune Phase I - Tower 1 to 4", "promoter": "Lodha", "pune_place": "upper_kharadi", "pune_place_name": "Upper Kharadi"}
    assert pages.family_name(doc) == "Kharadi Pune Phase I - Tower 1 to 4"
