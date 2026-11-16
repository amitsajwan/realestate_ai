"""The MahaRERA tracker's report of possession dates that moved (areastats.pages.date_moves, GET /public/areas/stats):
the builder's own moves only, net of MahaRERA's 2026 blanket extension, each project once."""
from datetime import date, datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.areastats import pages
from app.modules.areastats import router as area_router
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

TODAY = date(2026, 11, 15)


def rec(n, first, now, registered="2024-03-01", locality="kharadi", **kw):
    regno = f"P5210000{n:04d}"
    return {"_id": regno, "regno": regno, "name": f"Project {n}", "page_slug": f"project-{n}", "locality": locality,
            "registered_on": registered, "completion_at_registration": first, "completion_now": now, "units_total": 100, **kw}


DOCS = [
    rec(1, "2027-06-30", "2028-12-31"),                    # 18 months, less the 4-month extension: 14
    rec(2, "2027-06-30", "2027-10-30"),                    # the extension alone
    rec(3, "2028-03-31", "2028-03-31"),                    # never moved
    rec(4, "2027-01-31", "2027-12-31"),                    # 11 months, less 4: 7
    rec(5, "2027-01-31", "2029-01-31", cluster_primary="P52100000001"),   # a tower of project 1: counted with it, not again
    rec(6, "2024-01-31", "2025-12-31"),                    # finished: not being built
    rec(7, "2027-06-30", "2029-06-30", project_type="Commercial"),        # offices: not homes
]


def test_moves_count_the_builders_own_moves_once_per_project_biggest_first():
    got = pages.date_moves(DOCS, TODAY)
    assert (got["with_dates"], got["moved"], got["extension_only"]) == (4, 2, 1)
    assert got["median_months"] == 10
    assert [(b["name"], b["months"], b["from"], b["to"]) for b in got["biggest"]] == [
        ("Project 1", 14, "2027-06-30", "2028-12-31"), ("Project 4", 7, "2027-01-31", "2027-12-31")]
    assert got["biggest"][0]["page"] == "/projects/project-1"


def test_an_area_with_no_dates_says_so_and_names_nothing():
    assert pages.date_moves([], TODAY) == {"with_dates": 0, "moved": 0, "extension_only": 0, "median_months": None, "biggest": []}


async def test_the_city_tracker_carries_each_areas_moves():
    db = FakeDb()
    store = Store(db)
    for d in DOCS:
        await store.projects.insert_one({**d, "checked_at": datetime(2026, 11, 14, tzinfo=timezone.utc)})
    app = FastAPI()
    app.include_router(area_router.public_router, prefix="/public")
    app.dependency_overrides[area_router.get_db] = lambda: db
    body = TestClient(app).get("/public/areas/stats").json()
    by = {a["area"]["key"]: a for a in body["areas"]}
    assert by["kharadi"]["date_moves"]["moved"] >= 1 and by["wagholi"]["date_moves"]["with_dates"] == 0
