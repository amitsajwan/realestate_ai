"""`/area-pictures` (Studio, owner-only) and `/public/areas/{slug}/pictures` (the site, live only)."""
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.core.auth_backend import current_active_user
from app.modules.areastats import pictures as p
from app.modules.areastats import router as ar
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 17, 6, 0, tzinfo=timezone.utc)
OWNER = SimpleNamespace(id="owner1", is_superuser=True)
AGENT = SimpleNamespace(id="agent1", is_superuser=False)


def client(user, svc):
    app = FastAPI()
    app.include_router(ar.router, prefix="/area-pictures")
    app.include_router(ar.public_router, prefix="/public")
    app.dependency_overrides[ar.get_pictures] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: user
    return TestClient(app)


def test_only_the_owner_may_list_or_decide(tmp_path):
    svc = p.AreaPictures(FakeDb(), now=lambda: NOW, root=tmp_path)
    c = client(AGENT, svc)
    assert c.get("/area-pictures", params={"area": "kharadi"}).status_code == 403
    assert c.post("/area-pictures/p1/decide", json={"live": True}).status_code == 403


def test_the_owner_lists_approves_and_the_first_approval_sets_trust(tmp_path):
    svc = p.AreaPictures(FakeDb(), now=lambda: NOW, root=tmp_path)
    c = client(OWNER, svc)
    r = c.get("/area-pictures", params={"area": "kharadi"})
    assert r.status_code == 200 and r.json() == {"area": {"key": "kharadi", "name": "Kharadi", "slug": "kharadi"},
                                                  "trusted": False, "items": []}

    import asyncio
    doc = asyncio.get_event_loop().run_until_complete(
        svc.add(p.areas.get("kharadi"), 2017, Image.new("RGB", (5, 5)), "2017-03-12", 0.0, None, p.box_for("kharadi")))
    r = c.get("/area-pictures", params={"area": "kharadi"})
    assert len(r.json()["items"]) == 1 and r.json()["items"][0]["status"] == "pending"

    r = c.post(f"/area-pictures/{doc['_id']}/decide", json={"live": True})
    assert r.status_code == 200 and r.json()["status"] == "live"
    r = c.get("/area-pictures", params={"area": "kharadi"})
    assert r.json()["trusted"] is True


def test_decide_404s_for_an_unknown_picture(tmp_path):
    svc = p.AreaPictures(FakeDb(), now=lambda: NOW, root=tmp_path)
    c = client(OWNER, svc)
    assert c.post("/area-pictures/nope/decide", json={"live": True}).status_code == 404


def test_the_public_pictures_endpoint_shows_live_only_and_404s_for_an_unknown_area(tmp_path):
    svc = p.AreaPictures(FakeDb(), now=lambda: NOW, root=tmp_path)
    c = client(OWNER, svc)
    import asyncio
    loop = asyncio.get_event_loop()
    pending = loop.run_until_complete(svc.add(p.areas.get("kharadi"), 2017, Image.new("RGB", (5, 5)), "2017-03-12", 0.0, None,
                                              p.box_for("kharadi")))
    loop.run_until_complete(svc.decide(pending["_id"], True, "owner1"))
    r = c.get("/public/areas/kharadi/pictures")
    assert r.status_code == 200
    body = r.json()
    assert body["pictures"] == [{"year": 2017, "captured_on": "2017-03-12", "src": pending["url"], "width": 5, "height": 5,
                                 "credit": "Contains modified Copernicus Sentinel data 2017"}]
    assert c.get("/public/areas/nowhere/pictures").status_code == 404
