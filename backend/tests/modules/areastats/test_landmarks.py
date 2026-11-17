"""Landmarks near an area, with the metro: every station checked and placed in Pune, the nearest running ones named first, a station
being built never said as running, distances rounded and measured from the middle of the area."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import pune_metro
from app.core.areas import AREAS
from app.modules.areastats import areamap, landmarks
from app.modules.areastats import router as ar

from ..fakes import FakeDb

PUNE = (18.40, 73.65, 18.70, 74.10)   # south, west, north, east: Pune and Pimpri-Chinchwad with their edges


def _in_pune(lat: float, lon: float) -> bool:
    s, w, n, e = PUNE
    return s <= lat <= n and w <= lon <= e


def test_every_station_has_a_line_a_status_a_source_and_a_position_inside_pune():
    assert len(pune_metro.STATIONS) >= 50
    for s in pune_metro.STATIONS:
        assert s.line in pune_metro.LINES and s.status in (pune_metro.RUNNING, pune_metro.BEING_BUILT), s
        assert _in_pune(s.lat, s.lon), s
        assert s.source and s.osm.split("/")[0] in ("node", "way", "relation"), s
    # one row per station and line; District Court is the one stop on all three
    keys = [(s.name, s.line) for s in pune_metro.STATIONS]
    assert len(keys) == len(set(keys))
    assert {s.line for s in pune_metro.STATIONS if s.name == "District Court"} == {"1", "2", "3"}


def test_lines_one_and_two_have_maha_metros_29_running_stations_and_line_three_its_17():
    running = [s for s in pune_metro.STATIONS if s.running]
    assert sum(1 for s in running if s.line in ("1", "2")) == 29     # punemetrorail.org, 2026-11-17: 30 stations, 29 operational
    assert sum(1 for s in running if s.line == "3") == 17            # opened 2026-11-04 with 17 of its 23
    assert sum(1 for s in pune_metro.STATIONS if s.line == "3") == 23


def test_every_landmark_is_in_pune_with_how_it_was_checked_and_every_area_names_some():
    assert set(landmarks.AREA_PLACES) == {a.key for a in AREAS}
    for key, p in landmarks.PLACES.items():
        assert p.kind in landmarks.KINDS and p.how and _in_pune(p.lat, p.lon), key
    for area, keys in landmarks.AREA_PLACES.items():
        assert 4 <= len(keys) <= 10 and all(k in landmarks.PLACES for k in keys), area


def test_distances_are_rounded_to_what_we_know():
    assert landmarks.rounded(0.04) == 0.1          # never "0 km"
    assert landmarks.rounded(0.66) == 0.7
    assert landmarks.rounded(3.2) == 3.0 and landmarks.rounded(3.3) == 3.5
    assert landmarks.rounded(11.4) == 11.0


def test_distances_are_measured_from_the_middle_of_the_area_and_say_so():
    got = landmarks.public("kharadi")
    m = areamap.MAPS["kharadi"].box
    assert (got["middle"]["lat"], got["middle"]["lon"]) == (round((m[0] + m[2]) / 2, 5), round((m[1] + m[3]) / 2, 5))   # map's centre
    assert got["middle"]["label"] == "the middle of Kharadi"
    for row in got["metro"] + got["landmarks"]:
        assert row["distance"].startswith("about ") and row["distance"].endswith("the middle of Kharadi"), row
        assert "min" not in row["distance"]                                                            # never a travel time
        assert row["km"] == landmarks.rounded(landmarks.km(got["middle"]["lat"], got["middle"]["lon"], row["lat"], row["lon"]))
        assert row["maps"] == f"https://www.google.com/maps/search/?api=1&query={row['lat']},{row['lon']}"
    airport = next(r for r in got["landmarks"] if r["name"] == "Pune Airport")
    assert airport["distance"] == "about 4.5 km north-west of the middle of Kharadi"
    # areas without a drawn map: their boundary's centre (Lohegaon), else their hand-checked point (Baner)
    assert landmarks.public("lohegaon")["middle"]["how"] == "the centre of the area's boundary"
    assert "node/6616602606" in landmarks.public("baner")["middle"]["how"]


def test_the_nearest_running_stations_come_first_in_order_of_distance():
    got = landmarks.public("kharadi")["metro"]
    assert [m["name"] for m in got] == ["Ramwadi", "Kalyani Nagar"]
    assert all(m["running"] and m["status"] == "running" and m["tracker"] is None for m in got)
    assert got[0]["km"] <= got[1]["km"] and got[0]["line_short"] == "Aqua Line"


def test_a_second_station_much_further_than_the_first_is_not_named(monkeypatch):
    # standing on Hinjawadi Phase 1 station, the next one is under a km on: both are named
    names = [s.name for s in landmarks.nearest_metro(18.590967, 73.7463)]
    assert names[0] == "Hinjawadi Phase 1" and len(names) == 2
    # a line whose next stop is 3 km further on: only the near one is named
    monkeypatch.setattr(pune_metro, "STATIONS", (
        pune_metro.Station("Near", "2", pune_metro.RUNNING, 18.55, 73.90, "node/1", "test"),
        pune_metro.Station("Far", "2", pune_metro.RUNNING, 18.55, 73.87, "node/2", "test")))
    assert [s.name for s in landmarks.nearest_metro(18.55, 73.91)] == ["Near"]


def test_a_station_being_built_is_named_only_when_nearer_and_never_as_running():
    got = landmarks.public("baner")["metro"]
    first = got[0]
    assert first["name"] == "Baner Gaon" and first["status"] == "being built" and first["running"] is False
    assert first["tracker"] == "/news/track/pune-metro-line-3"
    assert all(m["running"] for m in got[1:]) and got[1]["km"] > first["km"]
    # where the nearest station runs, nothing being built is added
    assert all(m["running"] for m in landmarks.public("hinjawadi")["metro"])
    for a in AREAS:
        for m in landmarks.public(a.slug)["metro"]:
            s = next(x for x in pune_metro.STATIONS if x.name == m["name"] and x.line == m["line"])
            assert m["running"] == (s.status == pune_metro.RUNNING) and m["status"] == s.status


def test_landmarks_are_grouped_by_kind_nearest_first_within_a_kind():
    rows = landmarks.public("keshav-nagar")["landmarks"]
    order = list(landmarks.KINDS)
    assert [order.index(r["kind"]) for r in rows] == sorted(order.index(r["kind"]) for r in rows)
    work = [r["km"] for r in rows if r["kind"] == "work"]
    assert work == sorted(work)


def test_only_landmarks_and_stations_inside_a_maps_frame_become_its_icons():
    box = areamap.MAPS["kharadi"].box
    icons = landmarks.on_map(box)
    names = {i["name"]: i["icon"] for i in icons}
    assert names["EON IT Park (EON Free Zone)"] == "office" and names["Manipal Hospital, Kharadi"] == "hospital"
    assert "Pune Airport" not in names and "Ramwadi" not in names          # both just outside Kharadi's frame
    assert all(0 <= i["x"] <= 1 and 0 <= i["y"] <= 1 for i in icons)
    # a box over Ramwadi draws the station, said with its status, before the places
    ramwadi = landmarks.on_map((18.55, 73.907, 18.57, 73.92))
    assert ramwadi[0]["icon"] == "metro" and ramwadi[0]["label"] == "Ramwadi metro (running)"
    assert any(i["icon"] == "shopping" and i["name"].startswith("Phoenix") for i in ramwadi)


def test_the_route_answers_an_area_by_slug_and_says_404_for_one_we_do_not_cover():
    app = FastAPI()
    app.include_router(ar.public_router)
    c = TestClient(app)
    ok = c.get("/areas/upper-kharadi/landmarks")
    assert ok.status_code == 200 and "max-age" in ok.headers["cache-control"]
    body = ok.json()
    assert body["area"]["slug"] == "upper-kharadi" and body["metro"] and body["landmarks"]
    assert "not travel times" in body["note"]
    assert c.get("/areas/hadapsar/landmarks").status_code == 404


async def test_the_map_answer_carries_the_icons_inside_its_frame():
    app = FastAPI()
    app.include_router(ar.public_router)
    app.dependency_overrides[ar.get_db] = lambda: FakeDb()
    body = TestClient(app).get("/register/map?area=upper-kharadi").json()
    assert {i["name"] for i in body["landmarks"]} >= {"EON IT Park (EON Free Zone)", "G H Raisoni College of Engineering, Wagholi"}
