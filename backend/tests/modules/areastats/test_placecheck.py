"""The place a page names agrees with the sources we read (areastats.placecheck, docs/plan/location-checks.md)."""
from datetime import datetime, timezone

from app.modules.areastats import pages, placecheck
from app.modules.areastats.websearch import RESULTS
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
CENTRE = {"lat": 18.5512763, "lon": 73.9416575, "located_from": "locality"}
PLACES_OK = {"steps": {"places": {"ok": True, "checked": "within 15 km of the project's pincode area"}}}


def arrcade(**more) -> dict:
    # 96 Arrcade as it was on 2026-11-01: Kharadi by its pincode, a position at Kharadi's centre, text written for Kharadi
    return {"_id": "P52100078739", "regno": "P52100078739", "name": "96 Arrcade", "pincode": "411014", "locality": "kharadi",
            "locality_from": "pincode", "pune_place": "kharadi", "pune_place_name": "Kharadi", "page_slug": "96-arrcade-kharadi",
            "geo": dict(CENTRE), "enrichment": PLACES_OK, "page_summary": "96 Arrcade in Kharadi offers residential homes",
            **more}


CHARHOLI = [{"title": "Siddhhidata 96 Arrcade Charholi - Brochure, Pros&Cons", "link": "https://housiey.com/projects/siddhhidata-96-arrcade"},
            {"title": "Siddhhidata 96 Arrcade, Chovisawadi, Pune", "link": "https://www.squareyards.com/pune-residential-property/x/1/project"},
            {"title": "Kharadi, Pune Once a sleepy village", "link": "https://example.com/kharadi"}]   # not about the project


async def seeded(doc: dict, results: list, pins=()) -> Store:
    db = FakeDb()
    store = Store(db)
    await store.projects.insert_one(doc)
    await db.get_collection(RESULTS).insert_one({"_id": "q", "kind": "project", "regno": doc["_id"], "results": results})
    forgotten = []

    async def pin_pincodes(_db, regno):
        return list(pins)

    async def forget(_db, regno):
        forgotten.append(regno)

    placecheck.configure(pin_pincodes=pin_pincodes, forget_place=forget)
    store.forgotten = forgotten
    return store


async def test_a_project_every_source_puts_in_another_place_leaves_the_area_and_its_page_moves_address():
    store = await seeded(arrcade(), CHARHOLI, pins=["412105"])   # Google's best match was at Charholi's pincode
    got = await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert [m["to"] for m in got["moved"]] == ["Charholi"]
    assert (d["locality"], d["locality_from"], d["pune_place"]) == (None, "sources", "charholi")
    assert d["page_slug"] == "96-arrcade-charholi" and d["old_slugs"] == ["96-arrcade-kharadi"]
    # what was built on Kharadi is gone: its centre as the position, the check that passed it, the text
    assert "geo" not in d and "places" not in d["enrichment"]["steps"] and "page_summary" not in d
    assert store.forgotten == ["P52100078739"]
    assert d["place_check"]["sites"] == ["housiey.com", "squareyards.com"]


async def test_sources_agreeing_on_a_place_under_neither_pincode_only_mark_a_doubt():
    # "Melody" on 411014: two sites name Nanded City's Melody, another project with the same name
    store = await seeded(arrcade(), CHARHOLI, pins=[])
    got = await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert got["moved"] == [] and [x["says"] for x in got["doubt"]] == ["charholi"]
    assert (d["locality"], d["page_slug"]) == ("kharadi", "96-arrcade-kharadi") and d["place_doubt"]["to"] == "charholi"


async def test_one_site_naming_the_projects_own_area_keeps_it_there():
    here = CHARHOLI + [{"title": "96 Arrcade in Kharadi, Pune", "link": "https://www.99acres.com/96-arrcade"}]
    store = await seeded(arrcade(), here, pins=["412105"])
    assert (await placecheck.refresh(store, NOW))["moved"] == []
    assert (await store.projects.find_one({"_id": "P52100078739"}))["locality"] == "kharadi"


async def test_sources_naming_another_of_our_areas_never_move_a_project_there():
    # builders sell Wagholi as Kharadi: a position or a person decides that
    wagholi = arrcade(pincode="412207", locality="wagholi", pune_place="wagholi", page_slug="96-arrcade-wagholi")
    sold = [{"title": "96 Arrcade Kharadi Pune", "link": "https://housiey.com/96-arrcade"},
            {"title": "96 Arrcade in Kharadi", "link": "https://www.magicbricks.com/96-arrcade"}]
    store = await seeded(wagholi, sold, pins=["411014"])
    got = await placecheck.refresh(store, NOW)
    assert got["moved"] == [] and [x["says"] for x in got["doubt"]] == ["kharadi"]


async def test_a_page_moved_by_its_google_pin_gets_a_new_address_and_keeps_its_pin():
    # placed in Wadgaon Sheri by its own Google pin (areastats.placement) while its address still said Kharadi
    pinned = {"lat": 18.552, "lon": 73.925, "located_from": "google"}
    doc = arrcade(name="Kumar Prajwal", locality=None, locality_from="position", pune_place="vadgaon_sheri",
                  pune_place_name="Vadgaon Sheri", page_slug="kumar-prajwal-kharadi", geo=pinned)
    store = await seeded(doc, [])
    assert (await placecheck.refresh(store, NOW))["readdressed"] == 1
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert d["page_slug"] == "kumar-prajwal-vadgaon-sheri" and d["geo"] == pinned


async def test_a_name_that_says_the_area_keeps_its_address():
    doc = arrcade(name="East Street Kharadi", locality=None, pune_place="vadgaon_sheri", page_slug="east-street-kharadi")
    store = await seeded(doc, [])
    assert (await placecheck.refresh(store, NOW))["readdressed"] == 0


def test_only_a_position_measured_on_the_project_is_a_checked_position():
    assert not pages.own_position(arrcade())                                         # Kharadi's centre passed the check
    assert pages.own_position(arrcade(geo={**CENTRE, "located_from": "google"}))
    assert pages.view(arrcade(), [])["map"] is None


async def test_kesnand_counts_as_wagholi_and_an_upper_kharadi_page_keeps_its_wagholi_address():
    kesnand = [{"title": "Sai Royal Homez Kesnand, Pune", "link": "https://www.99acres.com/royal-homez-kesnand"},
               {"title": "Sai Royal Homez in Kesnand, Pune", "link": "https://housing.com/royal-homez"}]
    doc = arrcade(name="Royal Homez", pincode="412207", locality="wagholi", pune_place="wagholi", page_slug="royal-homez-wagholi")
    store = await seeded(doc, kesnand, pins=["412207"])
    assert (await placecheck.refresh(store, NOW))["moved"] == []
    camelot = arrcade(name="Kharadi New Project Tower 1", locality="upper_kharadi", pune_place="upper_kharadi",
                      locality_from="checked by hand", page_slug="kharadi-new-project-tower-1-wagholi")
    store = await seeded(camelot, [])
    assert (await placecheck.refresh(store, NOW))["readdressed"] == 0


async def test_a_moved_page_keeps_written_text_that_does_not_name_the_old_area():
    doc = arrcade(name="Ekaanta", locality=None, locality_from="position", pune_place="viman_nagar", pune_place_name="Viman Nagar",
                  page_slug="ekaanta-kharadi", page_text="Ekaanta has two towers.", page_summary="Ekaanta in Kharadi has two towers.")
    store = await seeded(doc, [])
    await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert d["page_slug"] == "ekaanta-viman-nagar" and d["page_text"] == "Ekaanta has two towers." and "page_summary" not in d
