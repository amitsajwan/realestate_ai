"""Upcoming projects MahaRERA has not registered yet: owner-written, no prices, served only while live."""
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.modules.areastats import router as ar
from app.modules.areastats import upcoming

from ..fakes import FakeDb

NOW = datetime(2026, 10, 23, 9, 0, tzinfo=timezone.utc)
BODY = {"slug": "esbee-upper-kharadi", "name": "Esbee Upper Kharadi", "builder": "Esbee Realty", "area": "upper_kharadi",
        "summary": "An upcoming project the builder has announced and MahaRERA has not registered yet.",
        "facts": [{"label": "Towers", "value": "4 to 5", "source": "Builder's blog, an agent's listing", "to_confirm": True}],
        "homes": [{"bhk": 2, "carpet_sqft": "760 to 800", "source": "An agent's listing", "to_confirm": True}],
        "sources": [{"name": "Builder's blog", "url": "https://www.esbee.in/x/", "read_on": "2026-10-23"}]}


def client(db):
    app = FastAPI()
    app.include_router(ar.public_router, prefix="/api/v1/public")
    app.dependency_overrides[ar.get_db] = lambda: db
    return TestClient(app)


async def test_a_live_upcoming_project_is_served_with_its_area_and_marked_not_registered():
    db = FakeDb()
    await upcoming.put(db, BODY, NOW)
    r = client(db).get("/api/v1/public/register/upcoming/esbee-upper-kharadi")
    assert r.status_code == 200 and "max-age" in r.headers["cache-control"]
    got = r.json()
    assert got["registered"] is False and got["area_name"] == "Upper Kharadi" and got["area_slug"] == "upper-kharadi"
    assert got["facts"][0]["to_confirm"] is True and got["homes"][0]["carpet_sqft"] == "760 to 800"


async def test_a_hidden_or_unknown_upcoming_project_is_not_found():
    db = FakeDb()
    await upcoming.put(db, {**BODY, "status": "hidden"}, NOW)
    assert client(db).get("/api/v1/public/register/upcoming/esbee-upper-kharadi").status_code == 404
    assert client(db).get("/api/v1/public/register/upcoming/nothing").status_code == 404


@pytest.mark.parametrize("change", [{"homes": [{"bhk": 2, "price_inr": 9000000, "source": "x"}]},   # no prices, ever
                                    {"area": "mumbai"}, {"slug": "Esbee Upper"}, {"sources": []}])
async def test_records_with_a_price_an_unknown_area_or_no_source_are_refused(change):
    with pytest.raises(ValidationError):
        await upcoming.put(FakeDb(), {**BODY, **change}, NOW)
