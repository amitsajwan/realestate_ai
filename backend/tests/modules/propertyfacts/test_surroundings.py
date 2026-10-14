"""The readable() guard: OSM objects named by vowel-less abbreviations ("CTR") never reach a card; real short names do.
And the Google-first `around`: searchNearby places lead, OpenStreetMap answers the categories it missed."""
import json

import httpx

from app.modules.propertyfacts.surroundings import GOOGLE_TYPES, OVERPASS, Nearby, _add, around, from_overpass, readable

LAT, LON = 18.5601, 73.9200


def _place(name, dlat, reviews=500, status="OPERATIONAL", uri="https://maps.google.com/maps?cid=1"):
    return {"displayName": {"text": name}, "location": {"latitude": LAT + dlat, "longitude": LON},
            "googleMapsUri": uri, "businessStatus": status, "userRatingCount": reviews}


def _google(answers):
    """A fake Google server: answers {category: places}, the category read from the request's types (the text search is
    "industry"); records the request bodies."""
    calls = []
    by_type = {t: cat for cat, types in GOOGLE_TYPES.items() for t in types}

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        cat = "industry" if "textQuery" in body else by_type[body["includedPrimaryTypes"][0]]
        return httpx.Response(200, json={"places": answers.get(cat, [])})
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


async def test_nearby_asks_each_category_by_popularity_and_groups_them():
    t, calls = _google({"hospital": [_place("Kokilabe Hospital", 0.01)], "school": [_place("Orchard School", 0.02, reviews=0)],
                        "industry": [_place("Magarpatta Citywall", 0.03), _place("Somewhere Far", 0.5)]})
    best, answered = await Nearby("k", transport=t).search(LAT, LON)
    assert answered and len(calls) == len(GOOGLE_TYPES) + 1
    assert all(c["rankPreference"] == "POPULARITY" for c in calls if "includedPrimaryTypes" in c)
    assert [i["name"] for i in best["hospital"]] == ["Kokilabe Hospital"]
    assert best["school"][0]["url"] == "https://maps.google.com/maps?cid=1"   # schools show no reviews: popularity alone
    assert best["industry"][0]["km"] == 3.3 and "Somewhere Far" not in [i["name"] for i in best["industry"]]


async def test_nearby_drops_closed_and_little_known_places():
    """The Camelot post: a closed school and a small clinic beat the known names because they were nearest."""
    t, _ = _google({"school": [_place("Big School", 0.03, reviews=0), _place("Shut School", 0.005, reviews=0, status="CLOSED_PERMANENTLY")],
                    "hospital": [_place("Manipal Hospital", 0.035, reviews=15000), _place("Corner Clinic", 0.005, reviews=12),
                                 _place("Sahyadri Hospital", 0.06, reviews=17000)]})
    best, _ = await Nearby("k", transport=t).search(LAT, LON)
    assert [i["name"] for i in best["school"]] == ["Big School"]
    assert [i["name"] for i in best["hospital"]] == ["Manipal Hospital", "Sahyadri Hospital"]   # known ones, nearest first


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
    t, _ = _google({"hospital": [_place("Kokilabe Hospital", 0.009)]})
    rs, _ = await around(_osm_json(), LAT, LON, nearby=Nearby("k", transport=t))
    got = {r.key: (r.value[0]["name"], r.source, r.url) for r in rs if r.key.startswith("nearby.")}
    assert got["nearby.hospital"] == ("Kokilabe Hospital", "google", "https://maps.google.com/maps?cid=1")
    assert got["nearby.school"][:2] == ("OSM School", "osm")   # Google did not name a school; OSM's stands
    assert got["nearby.bank"][1] == "osm"                  # banks are not asked of Google


async def test_around_without_google_still_asks_osm():
    rs, _notes = await around(_osm_json(), LAT, LON)
    assert {r.key for r in rs} == {"nearby.school", "nearby.bank"}
    assert all(r.source == "osm" for r in rs)
