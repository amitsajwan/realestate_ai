"""The readable() guard: OSM objects named by vowel-less abbreviations ("CTR") never reach a card; real short names do."""
from app.modules.propertyfacts.surroundings import _add, from_overpass, readable


def test_readable_rejects_vowel_less_abbreviations_and_keeps_the_rest():
    assert not readable("CTR")
    assert not readable("NCP")
    assert readable("EON")
    assert readable("ISBT")
    assert readable("Phoenix Marketcity")
    assert readable("E")            # a one-letter vowel name passes; a one-letter consonant does not
    assert not readable("X")


def test_add_drops_the_unreadable_place():
    best = {}
    _add(best, "industry", "CTR", 3.3, "u")
    _add(best, "industry", "Hadapsar Industrial Estate", 5.6, "u")
    assert [i["name"] for i in best["industry"]] == ["Hadapsar Industrial Estate"]


def test_from_overpass_skips_a_place_named_only_by_its_abbreviation():
    elements = [
        {"type": "way", "id": 1, "center": {"lat": 18.562, "lon": 73.920}, "tags": {"man_made": "works", "landuse": "industrial", "name": "CTR"}},
        {"type": "way", "id": 2, "center": {"lat": 18.570, "lon": 73.910}, "tags": {"landuse": "industrial", "name": "Pune SEZ"}},
    ]
    best = from_overpass(elements, 18.551, 73.948)
    assert [i["name"] for i in best["industry"]] == ["Pune SEZ"]
