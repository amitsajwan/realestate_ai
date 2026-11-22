"""Two neighbouring areas side by side (areastats.compare, GET /public/areas/compare/<pair>): only near areas are paired, each
pair has one address, the same places are measured from both middles, and every count is the one the area's own guide shows."""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.areas import AREAS, get
from app.modules.areastats import compare, landmarks
from app.modules.areastats import router as area_router
from app.modules.areastats.service import area_stats

from ..fakes import FakeDb

READ_AT = datetime(2026, 11, 20, 3, 0, tzinfo=timezone.utc)   # 20 Nov IST; filed dates below are years later, so the
                                                               # endpoint's own clock (date_moves) still counts them as being built
EAST = {"kharadi", "upper_kharadi", "wagholi", "lohegaon", "keshav_nagar"}
WEST = {"hinjawadi", "wakad", "baner"}


def rec(n, locality, registered="2026-03-01", first=None, now=None, units=100, booked=40):
    regno = f"P5210000{n:04d}"
    d = {"_id": regno, "regno": regno, "name": f"Project {n}", "page_slug": f"project-{n}", "locality": locality,
         "registered_on": registered, "last_modified": "2026-11-01", "checked_at": READ_AT, "units_total": units,
         "units_booked": booked, "details_ok": True}
    if now:
        d["completion_now"] = now
    if first:
        d["completion_at_registration"] = first
    return d


async def db_with(*docs):
    db = FakeDb()
    for d in docs:
        await db.get_collection("projects").insert_one(d)
    return db


def client(db):
    app = FastAPI()
    app.include_router(area_router.public_router, prefix="/public")
    app.dependency_overrides[area_router.get_db] = lambda: db
    return TestClient(app)


def test_only_areas_on_the_same_side_of_the_city_are_paired():
    keys = [{a.key, b.key} for a, b in compare.pairs()]
    assert len(keys) == 13                        # the east's 5 areas pair 10 ways, the west's 3 pair 3 ways
    assert all(k <= EAST or k <= WEST for k in keys)
    for a, b in compare.pairs():
        assert compare.apart_km(a, b) <= compare.NEAR_KM


def test_each_pair_has_one_address_in_menu_order_and_the_other_order_points_to_it():
    order = [a.key for a in AREAS]
    for a, b in compare.pairs():
        assert order.index(a.key) < order.index(b.key)
    assert compare.find("kharadi-vs-wagholi") == (get("kharadi"), get("wagholi"))
    assert compare.find("wagholi-vs-kharadi") is None
    assert compare.canonical("wagholi-vs-kharadi") == "kharadi-vs-wagholi"
    assert compare.canonical("kharadi-vs-baner") is None          # across the city: not a page
    assert compare.canonical("kharadi-vs-kharadi") is None
    assert compare.canonical("kharadi") is None and compare.canonical("mundhwa-vs-kharadi") is None


def test_the_same_places_are_measured_from_both_middles_work_first():
    a, b = get("kharadi"), get("wagholi")
    rows = compare.distances(a, b)
    keys = [r["key"] for r in rows]
    assert set(keys) == set(landmarks.AREA_PLACES["kharadi"]) | set(landmarks.AREA_PLACES["wagholi"])
    assert len(keys) == len(set(keys))
    assert rows[0]["kind"] == "work"
    (la, oa, _), p = landmarks.middle(a), landmarks.PLACES["eon"]
    eon = next(r for r in rows if r["key"] == "eon")
    assert eon["a_km"] == landmarks.rounded(landmarks.km(la, oa, p.lat, p.lon))
    assert eon["a_km"] < eon["b_km"]              # EON IT Park is in Kharadi
    assert eon["source"] == p.how and eon["maps"].startswith("https://www.google.com/maps/search/")


def test_a_station_being_built_is_never_offered_as_the_metro_to_take():
    for a in AREAS:
        m = compare.nearest_running_metro(a)
        if m is not None:
            assert any(s.name == m["name"] and s.running for s in landmarks.pune_metro.STATIONS)


def test_related_pairs_share_an_area_and_leave_this_one_out():
    rel = compare.related(get("hinjawadi"), get("wakad"))
    assert [r["slug"] for r in rel] == ["wakad-vs-baner", "hinjawadi-vs-baner"]   # nearest first


async def test_each_column_carries_the_counts_its_area_guide_shows():
    docs = [rec(1, "kharadi", registered="2026-02-01", first="2031-06-30", now="2032-12-31"),
            rec(2, "kharadi", registered="2025-05-01", first="2031-06-30", now="2031-06-30"),
            rec(3, "wagholi", registered="2026-04-01", now="2026-12-31", units=50, booked=50)]
    db = await db_with(*docs)
    r = client(db).get("/public/areas/compare/kharadi-vs-wagholi")
    assert r.status_code == 200 and r.headers["cache-control"].startswith("public")
    body = r.json()
    assert body["slug"] == "kharadi-vs-wagholi" and body["as_of"] == "2026-11-20"
    kharadi, wagholi = body["sides"]
    guide = await area_stats(db, "kharadi")
    assert kharadi["area"]["key"] == "kharadi" and kharadi["projects"] == guide["projects"] == 2
    assert (kharadi["units_total"], kharadi["units_booked"]) == (200, 80)
    assert (kharadi["registered_this_year"], kharadi["registered_last_year"]) == (1, 1)
    assert kharadi["completing_this_year"] == 0 and kharadi["dates"] == {"with_dates": 2, "moved": 1, "median_months": 14}
    assert wagholi["completing_this_year"] == 1 and wagholi["dates"] is None    # finishing this year, nothing with both dates
    assert body["distances"] and body["related"] and "not travel times" in body["note"]


async def test_other_orders_and_far_pairs_are_404_naming_the_address_to_use():
    c = client(await db_with(rec(1, "kharadi")))
    r = c.get("/public/areas/compare/wagholi-vs-kharadi")
    assert r.status_code == 404 and r.json()["detail"]["canonical"] == "kharadi-vs-wagholi"
    r = c.get("/public/areas/compare/kharadi-vs-baner")
    assert r.status_code == 404 and r.json()["detail"]["canonical"] is None
    listed = c.get("/public/areas/compare").json()
    assert [p["slug"] for p in listed] == [compare.pair_slug(a, b) for a, b in compare.pairs()]
    assert set(listed[0]) == {"slug", "a", "b", "apart_km"}
