"""The project's pin on Google Maps (propertyfacts.pin): found under the name it is sold by, not only the tower MahaRERA registered."""
import json
from datetime import datetime, timedelta

import httpx
import pytest

from app.modules.propertyfacts import pin
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 16, 9, 0)
HADAPSAR = (18.5089, 73.9260)


def place(name, lat=18.51, lon=73.93, address="Hadapsar, Pune, Maharashtra 411028", types=("apartment_complex",), pid="gp1"):
    return {"id": pid, "displayName": {"text": name}, "formattedAddress": address,
            "location": {"latitude": lat, "longitude": lon}, "types": list(types)}


def google(answers):
    """Google Maps answering each Text Search with the places kept for its query; the queries asked are in `asked`."""
    asked = []

    def handler(request):
        q = json.loads(request.content)["textQuery"]
        asked.append(q)
        return httpx.Response(200, json={"places": answers.get(q, [])})
    return httpx.MockTransport(handler), asked


def test_a_tower_code_or_label_at_the_end_is_not_the_projects_name():
    assert pin.sold_as("Kumar Primeview G2") == "Kumar Primeview"
    assert pin.sold_as("Sara Kasturi Building C") == "Sara Kasturi"
    assert pin.sold_as("BramhaCorp Business Park T9 A1") == "BramhaCorp Business Park"
    assert pin.sold_as("City One Panache 2.O") == "City One Panache"
    assert pin.sold_as("Sara Nilaay C D") == "Sara Nilaay"
    assert pin.sold_as("Venkatesh Vanaya Phase II") == "Venkatesh Vanaya"


def test_a_name_with_nothing_to_cut_or_too_short_to_cut_has_no_other_name():
    assert pin.sold_as("Lodha Camelot") == ""
    assert pin.sold_as("VTP X1") == ""
    assert pin.sold_as("Majestique Towers East") == ""


def test_a_builders_name_alone_never_stands_for_a_project():
    assert pin.also_known("Kumar Primeview G2", ["Kumar", "Kumar Primeview", "kumar primeview"]) == ["Kumar Primeview"]
    assert pin.also_known("Kharadi Pune Phase I", ["Lodha Giardino", "Kharadi Pune"], locality="Kharadi") == ["Lodha Giardino"]


@pytest.mark.asyncio
async def test_a_tower_is_found_at_its_projects_pin_without_a_second_search():
    transport, asked = google({"Kumar Primeview G2, Hadapsar, Pune": [place("Kumar Primeview")]})
    pins = pin.Pins(FakeDb(), "key", transport=transport)
    p, note = await pins.find("PR1260002502134", "Kumar Primeview G2", "Hadapsar", "411028", HADAPSAR, NOW)
    assert (p.lat, p.lon, p.place_id) == (18.51, 73.93, "gp1")
    assert note.startswith("Google Maps: Kumar Primeview")
    assert asked == ["Kumar Primeview G2, Hadapsar, Pune"]


@pytest.mark.asyncio
async def test_a_project_registered_under_another_name_is_asked_once_more_under_the_name_it_is_sold_by():
    transport, asked = google({"Kharadi Pune Phase I, Kharadi, Pune": [place("Kharadi Bypass")],
                               "Lodha Giardino, Kharadi, Pune": [place("Lodha Giardino", address="Kharadi, Pune 411014")]})
    pins = pin.Pins(FakeDb(), "key", transport=transport)
    p, _ = await pins.find("P1", "Kharadi Pune Phase I", "Kharadi", "411014", (18.51, 73.93), NOW, names=["Lodha Giardino", "Lodha"])
    assert p is not None and p.name == "Lodha Giardino"
    assert asked == ["Kharadi Pune Phase I, Kharadi, Pune", "Lodha Giardino, Kharadi, Pune"]


@pytest.mark.asyncio
async def test_the_other_checks_still_refuse_a_namesake():
    far = place("Kumar Primeview", lat=18.75, lon=74.24)                       # 40 km from Hadapsar
    shop = place("Kumar Primeview Sales Lounge", types=("store",))
    other_pincode = place("Kumar Primeview", address="Wagholi, Pune 412207")
    transport, asked = google({"Kumar Primeview G2, Hadapsar, Pune": [far, shop, other_pincode]})
    pins = pin.Pins(FakeDb(), "key", transport=transport)
    p, note = await pins.find("P1", "Kumar Primeview G2", "Hadapsar", "411028", HADAPSAR, NOW)
    assert p is None and note.startswith("not found on Google Maps")
    assert len(asked) == pin.NAMES_SEARCHED


@pytest.mark.asyncio
async def test_a_not_found_kept_before_we_knew_the_sold_name_is_asked_again_and_then_kept():
    db = FakeDb()
    await db.get_collection(pin.COLLECTION).insert_one(
        {"_id": "P1", "at": NOW - timedelta(days=3), "place_id": None, "checked": "not found on Google Maps",
         "project": "Kumar Primeview G2", "locality": "Hadapsar"})
    transport, asked = google({})
    pins = pin.Pins(db, "key", transport=transport)
    assert (await pins.find("P1", "Kumar Primeview G2", "Hadapsar", "411028", HADAPSAR, NOW))[0] is None
    assert len(asked) == 2                                                     # asked again under both names
    assert (await pins.find("P1", "Kumar Primeview G2", "Hadapsar", "411028", HADAPSAR, NOW + timedelta(days=1)))[0] is None
    assert len(asked) == 2                                                     # the answer is kept for REFRESH_DAYS now


@pytest.mark.asyncio
async def test_a_not_found_for_a_name_with_no_other_name_is_not_asked_again():
    db = FakeDb()
    await db.get_collection(pin.COLLECTION).insert_one(
        {"_id": "P1", "at": NOW - timedelta(days=3), "place_id": None, "checked": "not found on Google Maps",
         "project": "Lodha Camelot", "locality": "Kharadi"})
    transport, asked = google({})
    pins = pin.Pins(db, "key", transport=transport)
    assert (await pins.find("P1", "Lodha Camelot", "Kharadi", "411014", HADAPSAR, NOW))[0] is None
    assert asked == []
