from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.agentprojects import router as pr
from app.modules.concierge import router as cr

from .test_service import make

BODY = {"name": "Kosmic Kourtyard", "builder": "Triaa Lifespaces", "locality": "Wagholi", "rera_no": "P52100055341",
        "maharera_id": 43848, "status": "live",
        "configurations": [{"label": "2 BHK", "bhk": 2, "carpet_sqft": 765, "price_inr": 7689000}],
        "issues": [{"field": "possession", "theirs": "Dec 2028", "found": "MahaRERA now shows 30 Apr 2029"}]}
OWNER = SimpleNamespace(id="OWNER", is_superuser=True)


def client(user, svc):
    cr.limiter.hits.clear()
    app = FastAPI()
    app.include_router(pr.router, prefix="/agentprojects")
    app.include_router(pr.public_router, prefix="/public")
    app.dependency_overrides[pr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: user
    return TestClient(app)


def test_owner_routes_are_closed_to_agents(monkeypatch):
    monkeypatch.delenv("CONCIERGE_OWNER_IDS", raising=False)
    svc, _, _ = make()
    c = client(SimpleNamespace(id="agent1", is_superuser=False), svc)
    assert c.put("/agentprojects/agents/A1/projects/kosmic", json=BODY).status_code == 403
    assert c.get("/agentprojects/agents/A1/projects").status_code == 403
    assert c.post("/agentprojects/agents/A1/projects/kosmic/check").status_code == 403


async def test_owner_writes_and_public_reads_over_http():
    svc, db, _ = make()
    await db.get_collection("agent_public_profiles").insert_one({"agent_id": "A1", "slug": "house-deal", "is_public": True})
    c = client(OWNER, svc)
    assert c.put("/agentprojects/agents/A1/projects/Bad_Slug", json=BODY).status_code == 422
    r = c.put("/agentprojects/agents/A1/projects/kosmic", json=BODY)
    assert r.status_code == 200 and r.json()["issues"][0]["field"] == "possession"
    assert c.get("/agentprojects/agents/A1/projects").json()["items"][0]["slug"] == "kosmic"
    pub = c.get("/public/agents/house-deal/projects").json()
    assert pub["total"] == 1 and "issues" not in pub["items"][0]
    one = c.get("/public/agents/house-deal/projects/kosmic").json()
    assert one["configurations"][0]["price_per_sqft"] == 10051
    assert c.get("/public/agents/house-deal/projects/nope").status_code == 404
    assert c.get("/public/agents/nobody/projects").status_code == 404
