"""HTTP-level tests with FastAPI TestClient and dependency overrides."""
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.tracking import router as tr

from .qual_helpers import BROWSER, make

import asyncio

BODY = {"agent_slug": "rahul", "anon_id": "anon-visitor-1", "name": "Amit Kumar", "phone": "9876543210",
        "consent": True, "listing_id": "L1", "source": "whatsapp"}


@pytest.fixture
def env():
    svc, db, clock = asyncio.new_event_loop().run_until_complete(make())
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(tr.public_router, prefix="/t")
    app.include_router(tr.inbox_router, prefix="/inbox")
    app.dependency_overrides[tr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    return TestClient(app), who, clock


def test_old_inquiry_body_and_new_fields(env):
    c, _, _ = env
    r = c.post("/t/inquiry", json=BODY)
    assert r.status_code == 200 and r.json() == {"received": True, "new_lead": True}
    r = c.post("/t/inquiry", json={**BODY, "phone": "9123456780", "anon_id": "anon-visitor-2", "bhk": 3,
                                    "budget_min_inr": 8_000_000, "budget_max_inr": 12_000_000,
                                    "timeline": "1_3_months", "financing": "home_loan",
                                    "message": "want it soon"})
    assert r.status_code == 200 and r.json() == {"received": True, "new_lead": True}
    leads = c.get("/inbox/leads").json()["leads"]
    lines = [l["requirement_line"] for l in leads]
    assert set(lines) == {"2 BHK · Baner", "3 BHK · 80L-1.2Cr · Baner · 1-3 months"}


def test_inquiry_validation_errors(env):
    c, _, _ = env
    assert c.post("/t/inquiry", json={**BODY, "budget_min_inr": 9, "budget_max_inr": 5}).status_code == 422
    assert c.post("/t/inquiry", json={**BODY, "timeline": "someday"}).status_code == 422
    assert c.post("/t/inquiry", json={**BODY, "bhk": 0}).status_code == 422
    assert c.post("/t/inquiry", json={**BODY, "consent": False}).status_code == 400


def _lead(c, **extra):
    c.post("/t/inquiry", json={**BODY, "message": "2bhk under 90 lakh, asap, cash", **extra})
    return c.get("/inbox/leads").json()["leads"][0]["id"]


def test_lead_detail_shape(env):
    c, _, _ = env
    d = c.get(f"/inbox/leads/{_lead(c)}").json()
    assert d["requirement"]["timeline"] == "now" and d["requirement"]["financing"] == "own_funds"
    assert set(d["next_action"]) == {"type", "reason"}
    assert d["matches"][0]["listing_id"] == "L1" and d["matches"][0]["match_pct"] == 100
    assert d["follow_up"] == {"due_at": None, "overdue": False}
    assert d["ai_summary"].startswith("Wants a 2 BHK under 90L in Baner")


def test_patch_followup_and_draft(env):
    c, _, clock = env
    lid = _lead(c)
    r = c.patch(f"/inbox/leads/{lid}", json={"stage": "contacted"})
    assert r.status_code == 200 and r.json()["follow_up"]["due_at"].startswith("2026-01-03T12:00:00")
    r = c.patch(f"/inbox/leads/{lid}", json={"follow_up_at": "2026-01-10T09:30:00Z"})
    assert r.json()["follow_up"]["due_at"].startswith("2026-01-10T09:30:00")
    assert c.patch(f"/inbox/leads/{lid}", json={}).status_code == 422
    assert c.patch(f"/inbox/leads/{lid}", json={"follow_up_at": "nonsense"}).status_code == 422

    d = c.post(f"/inbox/leads/{lid}/followup-draft").json()  # no body -> en
    assert d["language"] == "en" and d["message"].startswith("Hi Amit,")
    u = urlparse(d["whatsapp_url"])
    assert u.path == "/919876543210" and unquote(parse_qs(u.query)["text"][0]) == d["message"]
    assert c.post(f"/inbox/leads/{lid}/followup-draft", json={"language": "hi"}).json()["language"] == "hi"
    assert c.post(f"/inbox/leads/{lid}/followup-draft", json={"language": "fr"}).status_code == 422


def test_today_endpoint(env):
    c, _, _ = env
    _lead(c)
    t = c.get("/inbox/today").json()
    assert set(t) == {"counts", "hot_buyers", "follow_ups", "headline"}
    assert set(t["counts"]) == {"new_enquiries_24h", "hot", "site_visits", "follow_ups_due", "uncontacted"}
    assert t["counts"]["uncontacted"] == 1 and t["headline"] == "1 buyer hasn't been contacted today."


def test_owner_isolation_over_http(env):
    c, who, _ = env
    lid = _lead(c)
    who.id = "A2"
    assert c.get(f"/inbox/leads/{lid}").status_code == 404
    assert c.post(f"/inbox/leads/{lid}/followup-draft").status_code == 404
    assert c.patch(f"/inbox/leads/{lid}", json={"follow_up_at": "2026-01-10T09:30:00Z"}).status_code == 404
    t = c.get("/inbox/today").json()
    assert t["counts"]["uncontacted"] == 0 and t["headline"] == "You're all caught up."
    who.id = "A1"
    assert c.get(f"/inbox/leads/{lid}").status_code == 200
