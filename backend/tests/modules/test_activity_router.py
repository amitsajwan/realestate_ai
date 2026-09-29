"""HTTP-level tests for GET /inbox/listings/{id}/activity."""
import asyncio
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.tracking import router as tr

from .activity_helpers import add_event, add_lead, make


@pytest.fixture
def env():
    loop = asyncio.new_event_loop()
    svc, db, clock = loop.run_until_complete(make())
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(tr.public_router, prefix="/t")
    app.include_router(tr.inbox_router, prefix="/inbox")
    app.dependency_overrides[tr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    yield TestClient(app), who, db, clock, loop
    loop.close()


def test_activity_shape_and_empty_state(env):
    c, _, _, _, _ = env
    r = c.get("/inbox/listings/L1/activity")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"listing", "totals", "by_source", "daily", "feed", "people"}
    assert body["listing"]["id"] == "L1" and body["feed"] == [] and len(body["daily"]) == 14
    assert set(body["totals"]) == {"views", "unique_visitors", "enquiries", "qualified", "site_visits", "deals",
                                   "whatsapp_clicks", "call_clicks", "shares"}


def test_activity_with_data_and_limit(env):
    c, _, db, clock, loop = env
    for i in range(5):
        loop.run_until_complete(add_event(db, clock, "listing_view", anon=f"anon-{i}", source="instagram",
                                          ts=datetime(2025, 12, 31, 10, i)))
    loop.run_until_complete(add_lead(db, clock, "c1", first_listing="L1", source="whatsapp"))
    body = c.get("/inbox/listings/L1/activity?limit=2").json()
    assert body["totals"]["views"] == 5 and body["totals"]["unique_visitors"] == 5 and body["totals"]["enquiries"] == 1
    assert len(body["feed"]) == 2 and body["feed"][0]["text"] == "Visitor 5 viewed this from Instagram"
    assert [p["lead_id"] for p in body["people"]] == ["c1"]
    assert body["by_source"]["instagram"] == {"views": 5, "enquiries": 0}


def test_activity_limit_validation(env):
    c, _, _, _, _ = env
    assert c.get("/inbox/listings/L1/activity?limit=0").status_code == 422
    assert c.get("/inbox/listings/L1/activity?limit=101").status_code == 422
    assert c.get("/inbox/listings/L1/activity?limit=100").status_code == 200


def test_activity_is_owner_scoped(env):
    c, who, _, _, _ = env
    assert c.get("/inbox/listings/L7/activity").status_code == 404   # A2's listing
    assert c.get("/inbox/listings/NOPE/activity").status_code == 404
    who.id = "A2"
    assert c.get("/inbox/listings/L1/activity").status_code == 404
    assert c.get("/inbox/listings/L7/activity").status_code == 200
