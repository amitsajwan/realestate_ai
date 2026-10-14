"""The readable() guard: OSM objects named by vowel-less abbreviations ("CTR") never reach a card; real short names do.
And the Google-first `around`: searchNearby places lead, OpenStreetMap answers the categories it missed."""
import json

import httpx

from app.modules.propertyfacts.surroundings import OVERPASS, Nearby, _add, around, from_overpass, readable

LAT, LON = 18.5601, 73.9200


def _place(name, dlat, ptype="hospital", uri="https://maps.google.com/maps?cid=1"):
    return {"displayName": {"text": name}, "location": {"latitude": LAT + dlat, "longitude": LON},
            "googleMapsUri": uri, "primaryType": ptype}


def _google(answers):
    """A fake Google server: each call gets the next canned list of places; records the request bodies."""
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        i = len(calls) - 1
        return httpx.Response(200, json={"places": answers[i] if i < len(answers) else []})
    return httpx.MockTransport(handler), calls


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


async def test_nearby_asks_two_calls_and_groups_by_category():
    t, calls = _google([[_place("Kokilabe Hospital", 0.01), _place("Orchard School", 0.02, "school")],
                        [_place("Magarpatta Citywall", 0.03), _place("Somewhere Far", 0.5)]])
    best, answered = await Nearby("k", transport=t).search(LAT, LON)
    assert answered and calls[0]["includedPrimaryTypes"] and calls[1]["textQuery"]
    assert [i["name"] for i in best["hospital"]] == ["Kokilabe Hospital"]
    assert best["school"][0]["url"] == "https://maps.google.com/maps?cid=1"
    assert best["industry"][0]["km"] == 3.3 and "Somewhere Far" not in [i["name"] for i in best["industry"]]


async def test_nearby_without_key_asks_nothing():
    best, answered = await Nearby(None).search(LAT, LON)
    assert best == {} and not answered


def _osm_json():
    async def get_json(url, params):
        if url == OVERPASS:
            return {"elements": [{"type": "node", "id": 1, "lat": LAT + 0.01, "lon": LON, "tags": {"amenity": "school", "name": "OSM School"}},
                                 {"type": "node", "id": 2, "lat": LAT + 0.02, "lon": LON, "tags": {"amenity": "bank", "name": "HDFC Bank"}}]}
        return None
    return get_json


async def test_around_google_leads_and_osm_fills_only_what_it_missed():
    t, _ = _google([[_place("Kokilabe Hospital", 0.009)], []])
    rs, _ = await around(_osm_json(), LAT, LON, nearby=Nearby("k", transport=t))
    got = {r.key: (r.value[0]["name"], r.source, r.url) for r in rs if r.key.startswith("nearby.")}
    assert got["nearby.hospital"] == ("Kokilabe Hospital", "google", "https://maps.google.com/maps?cid=1")
    assert got["nearby.school"][:2] == ("OSM School", "osm")   # Google did not name a school; OSM's stands
    assert got["nearby.bank"][1] == "osm"                  # banks are not in Google's ten types


async def test_around_without_google_still_asks_osm():
    rs, _notes = await around(_osm_json(), LAT, LON)
    assert {r.key for r in rs} == {"nearby.school", "nearby.bank"}
    assert all(r.source == "osm" for r in rs)
