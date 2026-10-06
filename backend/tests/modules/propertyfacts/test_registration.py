from datetime import datetime
from pathlib import Path

import pytest

from app.modules.newsroom.sources.maharera import parse_projects
from app.modules.propertyfacts import gather as gather_mod
from app.modules.propertyfacts import place, registration, surroundings

# saved from MahaRERA's public search on 2026-10-06: two projects named Gulmohar City (Shirur 412209, Khed 410501)
SEARCH_PAGE = (Path(__file__).parent / "fixtures" / "maharera_search_gulmohar_city.html").read_text(encoding="utf-8")
GENERAL = {"status": "1", "responseObject": {
    "projectName": "Gulmohar City", "projectRegistartionNo": "P52100076768", "projectTypeName": "Plotted",
    "reraRegistrationDate": "2024-06-28", "originalProjectProposeCompletionDate": "2028-12-31",
    "projectProposeComplitionDate": "2029-04-30", "totalNumberOfUnits": 123, "totalNumberOfSoldUnits": 0}}
NOMINATIM_RANJANGAON = [{"lat": "18.7536353", "lon": "74.2445791", "type": "village", "osm_type": "node", "osm_id": 342117431,
                         "address": {"village": "Ranjangaon", "county": "Shirur", "state_district": "Pune"}}]
OVERPASS_RANJANGAON = {"elements": [
    {"type": "node", "id": 1, "lat": 18.7560, "lon": 74.2460, "tags": {"amenity": "hospital", "name": "Narwade Hospital"}},
    {"type": "way", "id": 2, "center": {"lat": 18.7700, "lon": 74.2600}, "tags": {"landuse": "industrial", "name": "IndoSpace"}}]}
NOW = datetime(2026, 10, 6)
SHIRUR = place.parse(NOMINATIM_RANJANGAON)


@pytest.fixture(autouse=True)
def no_wait(monkeypatch):
    monkeypatch.setattr(registration, "RETRY_DELAY", 0)


def cards():
    return parse_projects(SEARCH_PAGE)


def test_search_url_uses_percent_twenty():
    assert "project_name=Gulmohar%20City&" in registration.search_url("Gulmohar City")


def test_place_parse_reads_taluka_not_postcode():
    assert (SHIRUR.taluka, SHIRUR.kind, SHIRUR.url) == ("Shirur", "village", "https://www.openstreetmap.org/node/342117431")
    city = place.parse([{"lat": "18.55", "lon": "73.94", "address": {"suburb": "Kharadi", "county": "Pune City Subdistrict"}}])
    assert city.taluka == "Pune City"
    assert place.parse([]) is None and place.parse({"error": "x"}) is None


def test_same_name_in_two_talukas_needs_the_place():
    assert registration.choose(cards(), "Gulmohar City").project is None
    m = registration.choose(cards(), "gulmohar city", place=SHIRUR)
    assert m.project.regno == "P52100076768" and m.how == "name and taluka (Shirur)"


def test_registration_number_decides_and_a_wrong_one_matches_nothing():
    assert registration.choose(cards(), "Gulmohar City", rera_no="p52100077275").project.pincode == "410501"
    m = registration.choose(cards(), "Gulmohar City", rera_no="P52100099999")
    assert m.project is None and "not among" in m.how


def test_unknown_name():
    assert registration.choose(cards(), "Sample Heights").project is None


def test_readings_from_card_and_details():
    card = registration.choose(cards(), "Gulmohar City", place=SHIRUR).project
    from app.modules.agentprojects.maharera import parse_general
    rs = {r.key: r for r in registration.readings(card, parse_general(GENERAL, card.regno, 46398), NOW)}
    assert rs["possession_now"].value == "2029-04-30" and rs["possession_now"].source == "maharera"
    assert rs["possession_moved_months"].value == 4 and rs["possession_moved_months"].source == "calc"
    assert rs["units_total"].value == 123 and rs["taluka"].value == "Shirur"
    assert "promoter" not in rs   # the card names no organisation
    assert rs["rera_no"].url == "https://maharerait.maharashtra.gov.in/public/project/view/46398"


class Fakes:
    def __init__(self, page=SEARCH_PAGE, general=GENERAL, nominatim=NOMINATIM_RANJANGAON):
        self.page, self.general, self.nominatim, self.calls = page, general, nominatim, []

    async def get_text(self, url):
        self.calls.append(url)
        return self.page

    async def get_json(self, url, params):
        if url == surroundings.OVERPASS:
            return OVERPASS_RANJANGAON
        return self.nominatim if "Ranjangaon" in params.get("q", "") else []

    async def fetch_general(self, mid):
        self.calls.append(mid)
        return self.general


LISTING = {"transaction": "sale", "property_type": "plot", "price_inr": 3230000, "locality": "Ranjangaon", "city": "Pune",
           "project_name": "Gulmohar City", "amenities": []}


async def test_gather_gulmohar_city():
    f = Fakes()
    s = await gather_mod.gather(LISTING, f, NOW)
    assert s.match.project.regno == "P52100076768" and 46398 in f.calls
    assert s.facts["possession_now"].level == "official" and s.facts["possession_now"].value == "2029-04-30"
    assert s.facts["taluka"].level == "official" and s.facts["taluka"].sources == ["maharera", "osm"]
    assert s.facts["price_inr"].value == 3230000 and s.facts["price_inr"].level == "official"
    assert "amenities" not in s.facts and s.notes[0].startswith("no named school")
    assert s.facts["nearby.hospital"].value == [{"name": "Narwade Hospital", "km": 0.3}]
    assert s.facts["emi"].level == "measured"


async def test_gather_says_what_it_could_not_find():
    s = await gather_mod.gather(LISTING, Fakes(nominatim=None, page=""), NOW)
    assert s.place is None and s.match.project is None
    assert s.notes[0].startswith("could not place") and s.notes[1].startswith("MahaRERA: ")


async def test_gather_with_the_registration_but_no_details():
    s = await gather_mod.gather(LISTING, Fakes(general=None), NOW)
    assert s.facts["rera_no"].value == "P52100076768" and "possession_now" not in s.facts
    assert s.notes[-1] == "MahaRERA: matched the registration but could not read its details"


async def test_no_project_name_skips_the_search():
    f = Fakes()
    s = await gather_mod.gather({**LISTING, "project_name": ""}, f, NOW)
    assert f.calls == [] and "no project name" in s.notes[-1]


async def test_a_site_failure_is_not_reported_as_no_project():
    s = await gather_mod.gather(LISTING, Fakes(page="<html>busy</html>"), NOW)
    assert s.match.project is None and "did not answer" in s.match.how
