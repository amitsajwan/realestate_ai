from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.concierge import router as cr

from .helpers import FULL, make

BODY = {"name": "Rahul Sharma", "mobile": "98765 43210", "label": "Rahul, Baner"}


def client(user, svc):
    cr.limiter.hits.clear()
    app = FastAPI()
    app.include_router(cr.router, prefix="/concierge")
    app.dependency_overrides[cr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: user
    return TestClient(app)


OWNER = SimpleNamespace(id="OWNER", is_superuser=True)


def test_closed_by_default_and_every_route_is_owner_only(monkeypatch):
    monkeypatch.delenv("CONCIERGE_OWNER_IDS", raising=False)
    svc, _, _ = make()
    c = client(SimpleNamespace(id="agent1", is_superuser=False), svc)
    assert c.get("/concierge/agents").status_code == 403
    assert c.post("/concierge/agents", json=BODY).status_code == 403
    for route in cr.router.routes:
        deps = [d.call for d in route.dependant.dependencies]
        assert any(getattr(d, "__name__", "") in ("owner_only", "dep") for d in deps), route.path


def test_owner_ids_env_grants_access(monkeypatch):
    monkeypatch.setenv("CONCIERGE_OWNER_IDS", "u9, u10")
    svc, _, _ = make()
    assert client(SimpleNamespace(id="u10", is_superuser=False), svc).get("/concierge/agents").status_code == 200
    assert client(SimpleNamespace(id="u11", is_superuser=False), svc).get("/concierge/agents").status_code == 403


def test_agent_flow_over_http():
    svc, db, _ = make()
    c = client(OWNER, svc)
    r = c.post("/concierge/agents", json=BODY)
    assert r.status_code == 201
    out = r.json()
    aid = out["agent"]["id"]
    assert len(out["code"]) == 6 and out["whatsapp_url"].startswith("https://wa.me/919876543210")
    assert c.get("/concierge/agents").json()["items"][0]["mobile"] == "98******10"
    assert "9876543210" not in c.get("/concierge/agents").text and "9876543210" not in c.get(f"/concierge/agents/{aid}").text
    assert c.get("/concierge/agents/nope").status_code == 404
    assert c.post(f"/concierge/agents/{aid}/consent").json()["given"] is True
    r = c.post(f"/concierge/agents/{aid}/listings", json=FULL)
    assert r.status_code == 201
    lid = r.json()["id"]
    assert c.patch(f"/concierge/agents/{aid}/listings/{lid}", json={"locality": "Aundh"}).json()["locality"] == "Aundh"
    assert c.post(f"/concierge/agents/{aid}/listings/{lid}/publish").json()["status"] == "live"
    assert c.get(f"/concierge/agents/{aid}/branding").status_code == 200
    assert c.post(f"/concierge/agents/{aid}/branding", json={"logo": "/uploads/images/a.png"}).json()["logo"]


def test_validation_over_http():
    svc, _, _ = make()
    c = client(OWNER, svc)
    aid = c.post("/concierge/agents", json=BODY).json()["agent"]["id"]
    assert c.post("/concierge/agents", json={**BODY, "mobile": "12345"}).status_code == 422
    assert c.post(f"/concierge/agents/{aid}/listings", json={**FULL, "city": "Mumbai"}).status_code == 422
    assert c.post(f"/concierge/agents/{aid}/listings", json={**FULL, "price_inr": 5}).status_code == 422
    assert c.post(f"/concierge/agents/{aid}/listings/missing/publish").status_code == 404
    assert c.post("/concierge/agents/ghost/listings", json=FULL).status_code == 404


def test_rate_limit_on_invites():
    svc, _, _ = make()
    c = client(OWNER, svc)
    codes = [c.post("/concierge/agents", json={**BODY, "mobile": f"98765432{i:02d}"}).status_code for i in range(11)]
    assert codes[:10] == [201] * 10 and codes[10] == 429


def test_post_without_consent_is_409_over_http():
    svc, db, _ = make()
    c = client(OWNER, svc)
    aid = c.post("/concierge/agents", json=BODY).json()["agent"]["id"]
    assert c.post(f"/concierge/agents/{aid}/listings/x/post", json={"channels": ["instagram"]}).status_code == 409
    assert c.post(f"/concierge/agents/{aid}/listings/x/post", json={"channels": ["twitter"]}).status_code == 422
