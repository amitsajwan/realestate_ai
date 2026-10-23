"""An area's most active projects on its street map: only checked positions, one pin per project sold under one name, homes only."""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.areastats import areamap
from app.modules.areastats import router as ar
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 23, 9, 0, tzinfo=timezone.utc)
PAGE = {"promoter": "Some Builder", "registered_on": "2024-01-10", "completion_now": "2029-10-30", "project_type": "Residential"}
GOOGLE = {"geo": {"lat": 18.5678, "lon": 73.9550, "located_from": "google"}, "enrichment": {"steps": {"places": {"ok": True}}}}


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, slug, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": slug.replace("-", " ").title(), "locality": "upper_kharadi",
                                         "page_slug": slug, "news": [], **PAGE, **extra})
    return db


async def test_only_checked_positions_make_pins_in_most_active_order_and_the_rest_are_counted():
    db = await seeded(
        ("P52100046510", "yashwin-enchante", {"hot_score": 16, "units_total": 941, "units_booked": 887,
                                             "completion_now": "2027-10-30", "registered_on": "2022-08-10"}),                                  # pinned by hand
        ("P52100080905", "saina-serenity", {"hot_score": 30, **GOOGLE}),                                          # its own Google place
        ("P52100099999", "centre-point", {"hot_score": 50, "geo": {"lat": 18.58, "lon": 73.98, "located_from": "locality"}}),
        ("P52100023185", "menlo-business-hub", {"hot_score": 60, "project_type": "Commercial", **GOOGLE}),
    )
    got = await areamap.public(db, "upper-kharadi", NOW)
    assert [(e["n"], e["name"]) for e in got["items"]] == [(1, "Saina Serenity"), (2, "Yashwin Enchante")]
    assert got["left_out"] == 1                                   # the locality's centre point is never a pin
    assert got["map"] == "/maps/upper-kharadi.svg" and "OpenStreetMap" in got["attribution"]
    y = got["items"][1]
    assert y["booked"] == 887 and y["total"] == 941 and y["stage_label"] == "Nearly ready"
    assert 0 < y["x"] < 1 and 0 < y["y"] < 1


async def test_phases_sold_under_one_name_are_one_pin_with_their_homes_added_up():
    db = await seeded(("P52100054937", "pristine-o2-world-part-1", {"hot_score": 12, "units_total": 610, "units_booked": 548}),
                      ("P52100079026", "pristine-o2-world-part-3", {"hot_score": 12, "units_total": 612, "units_booked": 168}),
                      ("P52100066545", "pristine-o2-world-part-2", {"hot_score": 12, "units_total": 408}))   # bookings not reported
    items = (await areamap.public(db, "upper_kharadi", NOW))["items"]
    assert len(items) == 1 and items[0]["name"] == "Pristine O2 World"
    assert (items[0]["booked"], items[0]["total"]) == (716, 1222)   # a phase without a booking count is left out of both
    assert set(items[0]["regnos"]) >= {"P52100054937", "P52100079026"}


async def test_an_area_without_a_drawn_map_has_none_and_the_route_says_404():
    db = await seeded()
    assert await areamap.public(db, "baner", NOW) is None
    app = FastAPI()
    app.include_router(ar.public_router)
    app.dependency_overrides[ar.get_db] = lambda: db
    c = TestClient(app)
    assert c.get("/register/map?area=baner").status_code == 404
    ok = c.get("/register/map?area=upper-kharadi")
    assert ok.status_code == 200 and ok.json()["items"] == []


async def test_a_phase_years_old_showing_0_booked_is_unreported_not_empty():
    # Majestique Towers East on 2026-10-23: Phase 3 (registered 2021) shows 0 booked; Phase 8 (2026) shows 21 of 192
    db = await seeded(("PR1260002600313", "majestique-tower-east-phase-8", {"hot_score": 40, "registered_on": "2026-04-30",
                                                                          "units_total": 192, "units_booked": 21}),
                      ("P52100028815", "majestique-towers-east-phase-3", {"hot_score": 5, "registered_on": "2021-03-30",
                                                                          "completion_now": "2026-10-30", "units_total": 184, "units_booked": 0}))
    m = (await areamap.public(db, "upper_kharadi", NOW))["items"][0]
    assert (m["name"], m["booked"], m["total"]) == ("Majestique Towers East", 21, 192)
