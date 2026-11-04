"""Upcoming projects MahaRERA has not registered yet: owner-written, no prices, served only while live."""
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.modules.areastats import router as ar
from app.modules.areastats import upcoming
from app.modules.newsroom.store import PROJECTS, Store

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


async def test_the_coming_soon_list_shows_only_live_projects_and_only_the_few_words_the_band_needs():
    db = FakeDb()
    await upcoming.put(db, {**BODY, "note": "2 & 3 BHK · coming soon", "logo": "/upcoming/logos/esbee.png"}, NOW)
    await upcoming.put(db, {**BODY, "slug": "old-page", "status": "hidden"}, NOW)
    got = client(db).get("/api/v1/public/register/upcoming").json()
    assert [u["slug"] for u in got] == ["esbee-upper-kharadi"]
    assert set(got[0]) == {"slug", "name", "builder", "logo", "area", "area_name", "area_slug", "note"}


async def test_the_page_lists_only_the_chosen_builder_projects_that_are_live_and_not_finished():
    db = FakeDb()
    for regno, slug, completion in (("P1", "esbee-azura-mundhwa", "2028-12-31"), ("P2", "old-esbee-camp", "2019-01-31"), ("P3", "not-chosen-wagholi", "2029-01-31")):
        await Store(db).projects.insert_one({"_id": regno, "regno": regno, "name": slug, "locality": "wagholi", "page_slug": slug, "news": [],
                                             "promoter": "Esbee", "completion_now": completion})
    await upcoming.put(db, {**BODY, "builder_projects": ["esbee-azura-mundhwa", "old-esbee-camp", "gone-page"]}, NOW)
    got = (await upcoming.get(db, "esbee-upper-kharadi"))
    listed = await upcoming.builder_projects(db, got, NOW)
    assert [p["slug"] for p in listed] == ["esbee-azura-mundhwa"]
    assert listed[0]["source"] == "MahaRERA" and "2028" in listed[0]["fact"]
    served = client(db).get("/api/v1/public/register/upcoming/esbee-upper-kharadi").json()
    assert [p["slug"] for p in served["builder_projects"]] == ["esbee-azura-mundhwa"]


VJ = {**BODY, "slug": "vilas-javdekar-upper-kharadi", "name": "Vilas Javdekar new project", "builder": "Vilas Javdekar"}
FRESH = {"regno": "P1", "name": "Yashwin Grand", "promoter": "Vilas Javdekar Developers", "pincode": "412207",
         "locality": "upper_kharadi", "registered_on": "2026-10-10"}


async def _watching(*records, tells):
    db = FakeDb()
    await upcoming.put(db, VJ, NOW)
    for r in records:
        await db.get_collection(PROJECTS).insert_one({"_id": r["regno"], **r})

    async def tell(db, u, d, now):
        tells.append((u["slug"], d["regno"]))

    upcoming.configure(tell=tell)
    return Store(db)


async def test_a_new_project_by_the_builder_is_told_to_the_owner_once():
    tells = []
    store = await _watching(FRESH, tells=tells)
    assert await upcoming.refresh(store, NOW) == {"told": 1}
    assert tells == [("vilas-javdekar-upper-kharadi", "P1")]
    assert await upcoming.refresh(store, NOW) is None                      # today's round is done
    assert await upcoming.refresh(store, NOW, force=True) == {"told": 0}   # and it is not told again


async def test_a_shared_surname_or_an_old_project_of_the_builder_is_not_told():
    tells = []
    store = await _watching({**FRESH, "regno": "P2", "promoter": "Pandit Javdekar Associates"},
                            {**FRESH, "regno": "P3", "registered_on": "2024-01-10"}, tells=tells)
    assert await upcoming.refresh(store, NOW) == {"told": 0} and tells == []


async def test_a_new_project_far_from_our_area_is_not_told():
    tells = []
    store = await _watching({**FRESH, "regno": "P4", "pincode": "411045", "locality": "baner"}, tells=tells)
    assert await upcoming.refresh(store, NOW) == {"told": 0} and tells == []


def test_the_projects_own_name_matches_in_its_area_when_another_company_filed_it():
    u = {"name": "Ceratec Central Park", "builder": "Ceratec Group", "area": "wagholi", "area_name": "Wagholi"}
    assert upcoming.looks_like(u, {"name": "CENTRAL PARK PHASE 1", "promoter": "Sunrise Land LLP", "locality": "wagholi"})
    assert not upcoming.looks_like(u, {"name": "CENTRAL PARK PHASE 1", "promoter": "Sunrise Land LLP", "locality": "kharadi"})


async def test_the_alert_says_how_many_buyers_are_waiting_and_sends_buyers_nothing(monkeypatch):
    from app import wiring

    monkeypatch.setenv("CONCIERGE_OWNER_IDS", "OWNER")
    db = FakeDb()
    u = await upcoming.put(db, VJ, NOW)
    await db.get_collection("contacts").insert_one({"_id": "c1", "message": "Vilas Javdekar new project (upcoming, not yet MahaRERA registered)"})
    await db.get_collection("contacts").insert_one({"_id": "c2", "message": "Lodha Camelot, a site visit"})
    await wiring._tell_upcoming_registered(db, u, FRESH, NOW)
    sent = await db.get_collection("notifications").find({}).to_list(None)
    assert [n["agent_id"] for n in sent] == ["OWNER"] and sent[0]["kind"] == "upcoming_registered"
    assert "1 waiting" in sent[0]["summary"] and "P1" in sent[0]["summary"]
