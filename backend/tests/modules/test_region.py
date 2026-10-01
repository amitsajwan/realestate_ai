import pytest

from app.core.region import MESSAGE, check_city


def test_pune_and_neighbouring_pune_areas_are_allowed():
    for c in ("Pune", "pune", "Pimpri-Chinchwad", "PCMC", "Pune, Maharashtra"):
        assert check_city(c) == c


def test_other_cities_are_refused_with_a_friendly_message():
    with pytest.raises(ValueError) as e:
        check_city("Mumbai")
    assert MESSAGE in str(e.value)


def test_empty_stays_empty_and_the_region_can_be_widened(monkeypatch):
    assert check_city(None) is None and check_city("") == ""
    monkeypatch.setenv("ALLOWED_CITIES", "pune,mumbai")
    assert check_city("Mumbai") == "Mumbai"
    monkeypatch.setenv("ALLOWED_CITIES", "*")
    assert check_city("Delhi") == "Delhi"
