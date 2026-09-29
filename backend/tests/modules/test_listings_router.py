from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.listings import router as lr

from .listings_fakes import ListingsDb

FULL = {
    "title": "2BHK in Baner", "transaction": "sale", "property_type": "apartment", "price_inr": 8500000,
    "city": "Pune", "locality": "Baner", "bhk": 2, "description": {"en": "Nice"},
    "media": [{"url": "https://x/a.jpg", "kind": "image", "order": 0}],
}


@pytest.fixture
def env():
    db = ListingsDb()
    svc = lr.ListingService(db)
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(lr.router, prefix="/listings")
    app.include_router(lr.public_router, prefix="/public")

    @app.post("/listings/ai/draft")
    async def ai_draft():  # stand-in for the ai_listing module, mounted AFTER the listings router
        return {"ai": True}

    app.dependency_overrides[lr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    db.get_collection("agent_public_profiles").docs.append(
        {"slug": "rahul", "agent_id": "A1", "agent_name": "Rahul", "phone": "1", "photo": None, "is_public": True})
    return TestClient(app), who


def test_full_flow(env):
    c, _ = env
    r = c.post("/listings", json=FULL)
    assert r.status_code == 201
    lid = r.json()["id"]
    assert c.get(f"/listings/{lid}").json()["status"] == "draft"
    assert c.patch(f"/listings/{lid}", json={"price_inr": 9000000}).json()["price_inr"] == 9000000
    assert c.get("/public/listings/" + lid).status_code == 404
    assert c.post(f"/listings/{lid}/publish").status_code == 200


def test_publish_and_public(env):
    c, _ = env
    lid = c.post("/listings", json=FULL).json()["id"]
    assert c.post(f"/listings/{lid}/publish").json()["status"] == "live"
    pub = c.get(f"/public/listings/{lid}").json()
    assert pub["agent"]["slug"] == "rahul" and "visibility" not in pub
    page = c.get("/public/agents/rahul/listings?limit=1").json()
    assert page["total"] == 1 and page["items"][0]["id"] == lid
    assert c.get("/public/agents/nobody/listings").status_code == 404
    assert c.post(f"/listings/{lid}/status", json={"status": "paused"}).json()["status"] == "paused"
    assert c.post(f"/listings/{lid}/status", json={"status": "sold"}).status_code == 409
    assert c.post(f"/listings/{lid}/status", json={"status": "bogus"}).status_code == 422
    assert c.get("/public/agents/rahul/listings").json() == {"items": [], "total": 0}


def test_publish_422_lists_missing(env):
    c, _ = env
    lid = c.post("/listings", json={"title": "x"}).json()["id"]
    r = c.post(f"/listings/{lid}/publish")
    assert r.status_code == 422 and "price_inr" in r.json()["detail"]["missing"]


def test_owner_isolation_and_listing_filter(env):
    c, who = env
    lid = c.post("/listings", json=FULL).json()["id"]
    who.id = "A2"
    assert c.get(f"/listings/{lid}").status_code == 404
    assert c.patch(f"/listings/{lid}", json={"title": "z"}).status_code == 404
    assert c.post(f"/listings/{lid}/publish").status_code == 404
    assert c.get("/listings").json() == {"items": []}
    who.id = "A1"
    assert len(c.get("/listings?status=draft").json()["items"]) == 1
    assert c.get("/listings?status=live").json()["items"] == []
    assert c.get("/listings?status=bogus").status_code == 422


def test_validation_errors_422(env):
    c, _ = env
    assert c.post("/listings", json={"price_inr": -1}).status_code == 422
    assert c.post("/listings", json={"status": "live"}).status_code == 422
    lid = c.post("/listings", json=FULL).json()["id"]
    assert c.patch(f"/listings/{lid}", json={"agent_id": "A9"}).status_code == 422


def test_literal_ai_draft_route_not_shadowed(env):
    c, _ = env
    assert c.post("/listings/ai/draft").json() == {"ai": True}
