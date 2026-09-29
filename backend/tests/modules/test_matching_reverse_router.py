"""HTTP-level tests for /inbox/matching-leads, /inbox/performance and /inbox/today actions."""
import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.tracking import router as tr

from .reverse_helpers import add_lead, add_view, make


@pytest.fixture
def env():
    loop = asyncio.new_event_loop()
    svc, db, clock = loop.run_until_complete(make())
    loop.run_until_complete(add_lead(db, clock, "B1", name="Priya Sharma", base=40, bhk=2, lo=8_000_000,
                                     hi=9_000_000, localities=["Baner"], first_listing="L1", source="whatsapp"))
    loop.run_until_complete(add_view(db, clock, "L1", "anon-visitor-1"))
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(tr.public_router, prefix="/t")
    app.include_router(tr.inbox_router, prefix="/inbox")
    app.dependency_overrides[tr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    return TestClient(app), who


def test_matching_leads_ok(env):
    c, _ = env
    r = c.get("/inbox/matching-leads", params={"listing_id": "L1"})
    assert r.status_code == 200
    body = r.json()
    assert body["listing"]["id"] == "L1" and [b["lead_id"] for b in body["buyers"]] == ["B1"]
    assert body["buyers"][0]["draft"]["whatsapp_url"].startswith("https://wa.me/9876543210?text=")


def test_matching_leads_validation_and_404(env):
    c, who = env
    assert c.get("/inbox/matching-leads").status_code == 422
    assert c.get("/inbox/matching-leads", params={"listing_id": "nope"}).status_code == 404
    assert c.get("/inbox/matching-leads", params={"listing_id": "L7"}).status_code == 404  # A2's listing
    who.id = "A2"
    assert c.get("/inbox/matching-leads", params={"listing_id": "L1"}).status_code == 404
    r = c.get("/inbox/matching-leads", params={"listing_id": "L7"})
    assert r.status_code == 200 and r.json()["buyers"] == []


def test_performance_endpoint(env):
    c, who = env
    items = c.get("/inbox/performance").json()["items"]
    top = items[0]
    assert top["listing_id"] == "L1" and (top["views"], top["unique_visitors"], top["enquiries"]) == (1, 1, 1)
    assert top["qualified"] == 1 and top["site_visits"] == 0 and top["by_source"] == {"whatsapp": 1}
    who.id = "A2"
    assert [i["listing_id"] for i in c.get("/inbox/performance").json()["items"]] == ["L7"]


def test_today_includes_actions_and_keeps_old_fields(env):
    c, _ = env
    t = c.get("/inbox/today").json()
    assert set(t) == {"counts", "hot_buyers", "follow_ups", "actions", "headline"}
    assert t["actions"][0] == {"type": "call", "title": "Call Priya Sharma", "detail": "2 BHK, 80L-90L, hot buyer",
                               "priority": 1, "lead_id": "B1"}
    assert {a["type"] for a in t["actions"]} == {"call", "create_marketing"}
    assert len(t["actions"]) <= 6
