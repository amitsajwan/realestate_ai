"""Areas by place: a pinned project belongs to the area it is in, not the one its pincode suggests; edges are not walls; a hand
placement is never moved; the register sweep does not move it back."""
from datetime import datetime, timezone

from app.core import area_bounds
from app.modules.areastats import areamap, placement
from app.modules.newsroom import register
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import MahaReraProject

from ..fakes import FakeDb

NOW = datetime(2026, 10, 23, 9, 0, tzinfo=timezone.utc)
CHECKED = {"enrichment": {"steps": {"places": {"ok": True}}}}
PAGE = {"promoter": "Some Builder", "registered_on": "2024-01-10", "completion_now": "2029-10-30", "project_type": "Residential",
        "news": [], "pincode": "411014", "locality_from": "pincode"}


def google(lat, lon):
    return {"geo": {"lat": lat, "lon": lon, "located_from": "google"}, **CHECKED}


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, name, locality, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": name, "locality": locality, "pune_place": locality,
                                         "page_slug": name.lower().replace(" ", "-"), **PAGE, **extra})
    return db, store


def test_the_boundaries_put_real_projects_where_google_says_they_are():
    assert area_bounds.containing(18.5731, 73.9093) == []                        # Ekaanta, Viman Nagar (411014: "Kharadi")
    assert "kharadi" in area_bounds.containing(18.5533, 73.9290)                 # Venkatesh Vanaya, Kharadi
    assert "upper_kharadi" in area_bounds.containing(18.5676, 73.9683)           # Lodha Camelot
    assert set(area_bounds.near(18.5508, 73.9689)) >= {"kharadi", "upper_kharadi"}   # Godrej Ivara, on both edges
    assert "lohegaon" in area_bounds.containing(18.600, 73.915)


async def test_a_kharadi_label_in_viman_nagar_moves_out_and_a_real_kharadi_one_stays():
    db, store = await seeded(
        ("PR1260002600747", "Ekaanta", "kharadi", {**google(18.5731, 73.9093), "map_pin": {
            "status": "auto", "lat": 18.5731, "lon": 73.9093, "address": "Survey 207, Viman Nagar, Pune 411014"}}),
        ("P1", "Venkatesh Vanaya", "kharadi", google(18.5533, 73.9290)),
        ("P2", "Edge House", "kharadi", google(18.5560, 73.9240)),          # 350 m west of the line: an edge is not a wall
    )
    got = await placement.refresh(store, NOW)
    assert [(m["name"], m["from"], m["to"]) for m in got["moved"]] == [("Ekaanta", "kharadi", "Viman Nagar")]
    e = await store.project("PR1260002600747")
    assert (e["locality"], e["pune_place"], e["locality_from"], e["position"]["was"]) == (None, "viman_nagar", "position", "kharadi")
    assert (await store.project("P1"))["locality"] == "kharadi" and (await store.project("P2"))["locality"] == "kharadi"
    assert await placement.refresh(store, NOW) is None                         # once a day


async def test_a_project_on_two_areas_edges_shows_on_both_maps_and_a_hand_placement_never_moves():
    db, store = await seeded(("PR1260002502426", "Godrej Ivara", "upper_kharadi", {}),   # pinned by hand, VERIFIED Upper Kharadi
                             ("P1", "Zen Elite", "kharadi", {**google(18.5478, 73.9525), "hot_score": 30}),
                             ("P3", "Vanaya", "kharadi", {**google(18.5533, 73.9290), "hot_score": 20}))
    await placement.refresh(store, NOW)
    ivara = await store.project("PR1260002502426")
    assert ivara["locality"] == "upper_kharadi" and "kharadi" in ivara["also_areas"]
    from app.modules.newsroom import store as s
    s._SHARED.clear()
    names = [i["name"] for i in (await areamap.public(db, "kharadi", NOW))["items"]]
    assert "Godrej Ivara" in names and "Zen Elite" in names


async def test_the_register_sweep_does_not_move_a_placed_project_back_but_a_hand_placement_wins():
    db, store = await seeded(("PR1260002600747", "Ekaanta", None, {"locality_from": "position", "pune_place": "viman_nagar"}))
    card = MahaReraProject(regno="PR1260002600747", name="Ekaanta", promoter="X", pincode="411014", district="Pune", location="Haveli",
                           last_modified="2026-10-01", url="https://maharerait.maharashtra.gov.in/public/project/view/1")
    await store.record_projects(register.records([card], NOW))
    e = await store.project("PR1260002600747")
    assert (e["locality"], e["pune_place"]) == (None, "viman_nagar")
    hand = [{**register.records([card], NOW)[0], "locality": "kharadi", "locality_from": "checked by hand"}]
    await store.record_projects(hand)
    assert (await store.project("PR1260002600747"))["locality"] == "kharadi"
