import logging
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.marketing.service import MarketingService
from app.modules.social import router as sr
from app.modules.social.config import SocialConfig
from app.modules.social.service import SocialService

from .listings_fakes import ListingsDb
from .marketing_helpers import PROFILE, listing
from .test_social_helpers import DRY, REAL, TOKEN, FakeGraph, graph_service, make_db

BODY = {"channels": ["facebook_page", "instagram"], "approve": True, "consent": True}


def client(db, svc):
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(sr.router, prefix="/social")
    app.dependency_overrides[sr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    return TestClient(app), who


def test_status_endpoint_has_no_secrets():
    cfg = SocialConfig(dry_run=True, page_id="P", page_token=TOKEN, media_base_url="https://m.test")
    c, _ = client(make_db(), SocialService(make_db(), config_loader=lambda: cfg))
    r = c.get("/social/status")
    assert r.status_code == 200
    assert r.json() == {"dry_run": True, "channels": {"facebook_page": True, "instagram": False}, "brand": "Avasetu", "media_url_ok": True}
    assert TOKEN not in r.text


def test_every_route_requires_the_authenticated_user():
    assert len(sr.router.routes) == 4
    for route in sr.router.routes:
        assert current_active_user in [d.call for d in route.dependant.dependencies], route.path


def test_publish_dry_run_list_and_idempotency():
    db = make_db()
    c, _ = client(db, SocialService(db, config_loader=lambda: DRY))
    r = c.post("/social/listings/L1/publish", json=BODY)
    assert r.status_code == 200
    pubs = r.json()["publications"]
    assert [p["status"] for p in pubs] == ["dry_run", "dry_run"] and pubs[0]["channel"] == "facebook_page"
    assert set(pubs[0]) == {"id", "listing_id", "agent_id", "channel", "pack_version", "status", "external_id", "permalink", "error",
                            "consent", "approved_at", "created_at", "updated_at", "attempts", "payload"}
    assert set(pubs[0]["payload"]) == {"text", "image_urls"}
    assert c.post("/social/listings/L1/publish", json=BODY).status_code == 409
    assert c.post("/social/listings/L1/publish", json={**BODY, "force": True}).status_code == 200
    items = c.get("/social/listings/L1/publications").json()["items"]
    assert len(items) == 4 and items[0]["created_at"] >= items[-1]["created_at"]


@pytest.mark.parametrize("over", [{"approve": False}, {"consent": False}, {"approve": None}, {}])
def test_422_without_approve_and_consent(over):
    db = make_db()
    c, _ = client(db, SocialService(db, config_loader=lambda: DRY))
    payload = {"channels": ["facebook_page"], **({} if over == {} else {"approve": True, "consent": True, **over})}
    assert c.post("/social/listings/L1/publish", json=payload).status_code == 422
    assert not db.get_collection("publications").docs
    assert c.post("/social/listings/L1/publish", json={"channels": [], "approve": True, "consent": True}).status_code == 422
    assert c.post("/social/listings/L1/publish", json={"channels": ["twitter"], "approve": True, "consent": True}).status_code == 422


def test_other_agent_gets_404_and_states_409():
    db = make_db()
    c, who = client(db, SocialService(db, config_loader=lambda: DRY))
    who.id = "A2"
    assert c.post("/social/listings/L1/publish", json=BODY).status_code == 404
    assert c.get("/social/listings/L1/publications").status_code == 404
    who.id = "A1"
    assert c.post("/social/listings/L1/publish", json=BODY).status_code == 200
    who.id = "A2"
    pid = db.get_collection("publications").docs[0]["_id"]
    assert c.post(f"/social/publications/{pid}/retry").status_code == 404
    db.get_collection("listings").docs[0]["status"] = "draft"
    who.id = "A1"
    assert c.post("/social/listings/L1/publish", json={**BODY, "force": True}).status_code == 409
    db2 = make_db()
    db2.get_collection("marketing_packs").docs.clear()
    c2, _ = client(db2, SocialService(db2, config_loader=lambda: DRY))
    assert c2.post("/social/listings/L1/publish", json=BODY).status_code == 409


def test_instagram_without_images_is_400():
    db = make_db(images=())
    c, _ = client(db, SocialService(db, config_loader=lambda: DRY))
    r = c.post("/social/listings/L1/publish", json=BODY)
    assert r.status_code == 400 and "image" in r.json()["detail"]


def test_retry_endpoint_and_token_never_in_responses_or_logs(caplog):
    caplog.set_level(logging.DEBUG)
    db = make_db()
    echo = {"error": {"message": f"bad token {TOKEN} ?access_token={TOKEN}", "code": 190}}
    c, _ = client(db, graph_service(db, FakeGraph({("POST", "/v23.0/PAGE1/photos"): (400, echo)})))
    r = c.post("/social/listings/L1/publish", json={**BODY, "channels": ["facebook_page"]})
    assert r.status_code == 200
    pub = r.json()["publications"][0]
    assert pub["status"] == "failed" and pub["attempts"] == 1 and TOKEN not in r.text
    c2, _ = client(db, graph_service(db, FakeGraph({("POST", "/v23.0/PAGE1/photos"): (200, {"id": "1", "post_id": "PAGE1_1"})})))
    ok = c2.post(f"/social/publications/{pub['id']}/retry")
    assert ok.status_code == 200 and ok.json()["status"] == "published" and ok.json()["attempts"] == 2
    assert c2.post(f"/social/publications/{pub['id']}/retry").status_code == 409  # only failed ones
    assert c2.get("/social/listings/L1/publications").status_code == 200
    for text in (r.text, ok.text, c2.get("/social/listings/L1/publications").text, caplog.text, repr(db.get_collection("publications").docs)):
        assert TOKEN not in text


def test_end_to_end_with_a_real_marketing_pack(tmp_path):
    """Generate a pack with the marketing module, then post it (dry run) with the images re-based onto the public https url."""
    db = ListingsDb()
    (tmp_path / "images").mkdir()
    db.get_collection("agent_public_profiles").docs.append(dict(PROFILE))
    db.get_collection("listings").docs.append(listing())
    import asyncio
    asyncio.run(MarketingService(db, tmp_path, "https://site.test").generate("A1", "L1", "en", "http://localhost:8000/"))
    cfg = SocialConfig(dry_run=True, media_base_url="https://media.test")
    c, _ = client(db, SocialService(db, config_loader=lambda: cfg))
    pubs = c.post("/social/listings/L1/publish", json=BODY).json()["publications"]
    fb, ig = pubs
    assert fb["payload"]["image_urls"] == ["https://media.test/uploads/marketing/L1/cover.jpg"]
    assert ig["payload"]["image_urls"] == [f"https://media.test/uploads/marketing/L1/{k}.jpg" for k in ("cover", "facts", "amenities", "cta")]
    assert fb["payload"]["text"].endswith("https://site.test/agent/rahul/listings/L1?src=whatsapp")
    assert "#" in ig["payload"]["text"] and fb["pack_version"] == 1
