"""The place a page names agrees with the sources we read (areastats.placecheck, docs/plan/location-checks.md)."""
from copy import deepcopy
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
            "geo": dict(CENTRE), "enrichment": deepcopy(PLACES_OK), "page_summary": "96 Arrcade in Kharadi offers residential homes",
            **more}


CHARHOLI = [{"title": "Siddhhidata 96 Arrcade Charholi - Brochure, Pros&Cons", "link": "https://housiey.com/projects/siddhhidata-96-arrcade"},
            {"title": "Siddhhidata 96 Arrcade, Chovisawadi, Pune", "link": "https://www.squareyards.com/pune-residential-property/x/1/project"},
            {"title": "Kharadi, Pune Once a sleepy village", "link": "https://example.com/kharadi"}]   # not about the project


async def seeded(doc: dict, results: list, pins=(), places=None, address="") -> Store:
    db = FakeDb()
    store = Store(db)
    await store.projects.insert_one(doc)
    await db.get_collection(RESULTS).insert_one({"_id": "q", "kind": "project", "regno": doc["_id"], "results": results})
    forgotten, kept_pins, searches = [], [], []

    async def pin_pincodes(_db, regno):
        return list(pins)

    async def forget(_db, regno):
        forgotten.append(regno)

    async def search(_db, query, centre):
        searches.append(query)
        return places if places is not None else []

    async def keep_pin(_db, regno, c, now):
        kept_pins.append(c["place_id"])

    async def pin_address(_db, regno):
        return address

    placecheck.configure(pin_pincodes=pin_pincodes, forget_place=forget, search=search, keep_pin=keep_pin, pin_address=pin_address)
    store.forgotten, store.kept_pins, store.searches = forgotten, kept_pins, searches
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


async def test_sources_agreeing_on_a_place_under_neither_pincode_leave_the_filing_standing():
    # "Melody" on 411014: two sites name Nanded City's Melody, another project with the same name
    store = await seeded(arrcade(), CHARHOLI, pins=[])
    got = await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert got["moved"] == [] and [(x["says"], x["by"]) for x in got["kept"]] == [("charholi", "filing")]
    assert (d["locality"], d["page_slug"]) == ("kharadi", "96-arrcade-kharadi") and d["place_check"]["decided"] == "stays"


async def test_sites_naming_the_projects_own_area_keep_it_there_when_they_are_more_than_half_the_others():
    here = CHARHOLI + [{"title": "96 Arrcade in Kharadi, Pune", "link": "https://www.99acres.com/96-arrcade"},
                       {"title": "96 Arrcade Kharadi", "link": "https://housing.com/96-arrcade"}]
    store = await seeded(arrcade(), here, pins=["412105"])
    assert (await placecheck.refresh(store, NOW))["moved"] == []
    assert (await store.projects.find_one({"_id": "P52100078739"}))["locality"] == "kharadi"


async def test_one_copy_of_the_filing_does_not_outweigh_the_sites_that_know_the_project():
    # Sai Crystal Court: 99acres and BeyondWalls say Wadgaon Sheri; one site copying MahaRERA's Kharadi kept it there
    here = CHARHOLI + [{"title": "96 Arrcade in Kharadi, Pune", "link": "https://northstarventures.tech/96-arrcade"}]
    store = await seeded(arrcade(), here, pins=["412105"])
    assert [m["to"] for m in (await placecheck.refresh(store, NOW))["moved"]] == ["Charholi"]


SOLD_AS_KHARADI = [{"title": "96 Arrcade Kharadi Pune", "link": "https://housiey.com/96-arrcade"},
                   {"title": "96 Arrcade in Kharadi", "link": "https://www.magicbricks.com/96-arrcade"}]
WAGHOLI_SIDE = dict(pincode="412207", locality="wagholi", pune_place="wagholi", page_slug="96-arrcade-wagholi")


def place(lat, lon, address, name="96 Arrcade", place_id="g1", types=("premise",)) -> dict:
    return {"name": name, "address": address, "lat": lat, "lon": lon, "place_id": place_id, "types": list(types)}


async def test_sites_alone_never_move_a_project_between_our_areas():
    # builders sell Wagholi as Kharadi, and Google knows no such place: MahaRERA's filing stands and the page claims no position
    store = await seeded(arrcade(**WAGHOLI_SIDE), SOLD_AS_KHARADI, pins=["411014"], places=[])
    got = await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert got["moved"] == [] and got["kept"][0]["by"] == "filing"
    assert d["locality"] == "wagholi" and not pages.own_position(d)


async def test_a_dispute_between_our_areas_is_settled_by_where_google_finds_the_project():
    # inside Kharadi's boundary, whatever the pincode: it moves, and the place found becomes its own pin
    store = await seeded(arrcade(**WAGHOLI_SIDE), SOLD_AS_KHARADI,
                         places=[place(18.5450, 73.9400, "Kharadi, Pune, Maharashtra 412207")])
    got = await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert [(m["to"], m["by"]) for m in got["moved"]] == [("Kharadi", "position")]
    assert (d["locality"], d["locality_from"]) == ("kharadi", "position") and d["page_slug"] == "96-arrcade-kharadi"
    assert pages.own_position(d) and store.kept_pins == ["g1"]


async def test_a_project_google_finds_where_it_is_filed_stays_and_gains_its_map_though_sites_sell_it_by_the_next_area():
    store = await seeded(arrcade(**WAGHOLI_SIDE), SOLD_AS_KHARADI,
                         places=[place(18.5800, 73.9950, "Wagholi, Pune, Maharashtra 412207")])
    got = await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert got["moved"] == [] and got["kept"][0]["by"] == "position"
    assert d["locality"] == "wagholi" and pages.own_position(d)


async def test_on_the_edge_of_two_areas_googles_address_breaks_the_tie():
    # Panchshil Towers: its own pin at the Kharadi-Wagholi edge, "Vitthal Nagar, Kharadi" on Google, 7 sites saying Kharadi
    edge = {"lat": 18.5600, "lon": 73.9570, "located_from": "google"}
    assert {"kharadi", "wagholi"} <= set(placecheck.area_bounds.near(edge["lat"], edge["lon"]))
    store = await seeded(arrcade(geo=edge, **WAGHOLI_SIDE), SOLD_AS_KHARADI, address="Vitthal Nagar, Kharadi, Pune 412207")
    assert [m["to"] for m in (await placecheck.refresh(store, NOW))["moved"]] == ["Kharadi"]


async def test_a_namesake_google_finds_elsewhere_is_not_taken_for_the_project():
    # Nanded City's Melody: right name, but no reading and no pincode puts this project there
    store = await seeded(arrcade(**WAGHOLI_SIDE), SOLD_AS_KHARADI,
                         places=[place(18.4600, 73.7900, "Nanded City, Pune, Maharashtra 411068")])
    got = await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert got["moved"] == [] and not pages.own_position(d) and store.kept_pins == []


async def test_a_sales_gallery_with_the_projects_name_is_not_its_position():
    store = await seeded(arrcade(**WAGHOLI_SIDE), SOLD_AS_KHARADI,
                         places=[place(18.5450, 73.9400, "Kharadi, Pune 411014", name="96 Arrcade Sales Gallery")])
    assert (await placecheck.refresh(store, NOW))["moved"] == []


def test_a_project_named_after_a_place_does_not_vote_for_it():
    # "Kharadi Signet" on 99acres says nothing about where it is; a site that also says where still counts
    doc = arrcade(name="Kharadi Signet", **WAGHOLI_SIDE)
    named = [{"title": "Lodha Kharadi Signet Photos", "link": "https://www.99acres.com/lodha-kharadi-signet-photos"},
             {"title": "Lodha Kharadi Signet, Pune", "link": "https://mypropertyfact.in/lodha-kharadi-signet"}]
    assert placecheck.readings(doc, named) == {}
    said = [{"title": "Kharadi Signet, Wagholi, Pune", "link": "https://app.trythat.ai/listings/x"}]
    assert placecheck.readings(doc, said) == {"wagholi": ["app.trythat.ai"]}


async def test_google_is_not_asked_again_for_a_month_about_a_project_it_does_not_know():
    store = await seeded(arrcade(**WAGHOLI_SIDE), SOLD_AS_KHARADI, places=[])
    await placecheck.refresh(store, NOW)
    asked = list(store.searches)
    assert asked
    await placecheck.refresh(store, NOW + placecheck.EVERY, force=True)
    assert store.searches == asked
    await placecheck.refresh(store, NOW + placecheck.SEARCH_AGAIN + placecheck.EVERY, force=True)
    assert len(store.searches) > len(asked)


async def test_a_move_made_on_the_sources_is_undone_when_the_sources_change():
    # moved to Charholi on two sites; since then listings say Kharadi and Google finds it in Kharadi: back, with its address
    doc = arrcade(locality=None, locality_from="sources", pune_place="charholi", pune_place_name="Charholi",
                  page_slug="96-arrcade-charholi")
    store = await seeded(doc, SOLD_AS_KHARADI, places=[place(18.5450, 73.9400, "Kharadi, Pune, Maharashtra 411014")])
    await placecheck.refresh(store, NOW)
    d = await store.projects.find_one({"_id": "P52100078739"})
    assert (d["locality"], d["locality_from"]) == ("kharadi", "position")
    assert d["page_slug"] == "96-arrcade-kharadi" and d["old_slugs"] == ["96-arrcade-charholi"]


async def test_the_old_review_mark_is_cleared():
    store = await seeded(arrcade(place_doubt={"to": "charholi"}), [])
    await placecheck.refresh(store, NOW)
    assert "place_doubt" not in await store.projects.find_one({"_id": "P52100078739"})


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
