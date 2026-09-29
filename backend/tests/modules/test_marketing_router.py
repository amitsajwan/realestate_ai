from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.core.auth_backend import current_active_user
from app.modules.marketing import router as mr
from app.modules.marketing.service import MarketingService

from .listings_fakes import ListingsDb
from .marketing_helpers import PROFILE, listing


@pytest.fixture
def env(tmp_path):
    db = ListingsDb()
    (tmp_path / "images").mkdir()
    svc = MarketingService(db, tmp_path, "https://site.test")
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(mr.router, prefix="/listings")

    @app.get("/listings/{listing_id}")
    async def other(listing_id: str):  # a sibling route: must not be shadowed by /marketing
        return {"other": listing_id}

    app.dependency_overrides[mr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    db.get_collection("agent_public_profiles").docs.append(dict(PROFILE))
    db.get_collection("listings").docs.append(listing())
    return TestClient(app), db, who, tmp_path


def test_generate_and_get(env):
    c, db, _, up = env
    assert c.get("/listings/L1/marketing").status_code == 404  # nothing generated yet
    r = c.post("/listings/L1/marketing")
    assert r.status_code == 200
    p = r.json()
    assert p["version"] == 1 and p["language"] == "en" and p["listing_id"] == "L1" and p["generated_at"].endswith("Z")
    assert p["share_url"] == "https://site.test/agent/rahul/listings/L1?src=whatsapp"
    assert p["share_url"] in p["whatsapp"]["message"]
    assert [i["kind"] for i in p["instagram"]["images"]] == ["cover", "facts", "amenities", "cta"]
    assert all(i["width"] == i["height"] == 1080 for i in p["instagram"]["images"])
    assert p["instagram"]["images"][0]["url"] == "http://testserver/uploads/marketing/L1/cover.jpg"
    st = p["whatsapp"]["status_image"]
    assert st["kind"] == "status" and (st["width"], st["height"]) == (1080, 1920)
    assert (up / "marketing/L1/status.jpg").is_file()
    assert p["reel"]["duration_s"] == 15 and p["angle"].startswith("Ready-to-move 2 BHK")
    got = c.get("/listings/L1/marketing")
    assert got.status_code == 200 and got.json() == p
    stored = db.get_collection("marketing_packs").docs[0]
    assert stored["_id"] == "L1" and stored["agent_id"] == "A1"


def test_regenerate_bumps_version_and_overwrites(env):
    c, db, _, up = env
    first = c.post("/listings/L1/marketing", json={}).json()
    listings = db.get_collection("listings").docs
    listings[0]["price_inr"] = 12500000
    second = c.post("/listings/L1/marketing", json={"language": "hi"}).json()
    assert (first["version"], second["version"]) == (1, 2)
    assert second["language"] == "hi" and "Rs 1.25 Cr" in second["headline"]
    assert len(db.get_collection("marketing_packs").docs) == 1
    assert c.get("/listings/L1/marketing").json()["version"] == 2
    assert len(list((up / "marketing/L1").glob("*.jpg"))) == 5


def test_url_uses_request_base(env):
    c, *_ = env
    r = c.post("/listings/L1/marketing", headers={"host": "api.example.in"}).json()
    assert r["whatsapp"]["status_image"]["url"] == "http://api.example.in/uploads/marketing/L1/status.jpg"


def test_other_agent_gets_404(env):
    c, db, who, _ = env
    assert c.post("/listings/L1/marketing").status_code == 200
    who.id = "A2"
    assert c.post("/listings/L1/marketing").status_code == 404
    assert c.get("/listings/L1/marketing").status_code == 404


def test_unknown_listing_404(env):
    c, *_ = env
    assert c.post("/listings/nope/marketing").status_code == 404


def test_draft_is_409_and_others_allowed(env):
    c, db, _, up = env
    docs = db.get_collection("listings").docs
    docs[0]["status"] = "draft"
    r = c.post("/listings/L1/marketing")
    assert r.status_code == 409 and "live" in r.json()["detail"].lower()
    assert not (up / "marketing").exists()
    for status in ("under_offer", "live"):
        docs[0]["status"] = status
        assert c.post("/listings/L1/marketing").status_code == 200
    for status in ("sold", "paused", "expired"):
        docs[0]["status"] = status
        assert c.post("/listings/L1/marketing").status_code == 409


def test_invalid_language_rejected(env):
    c, *_ = env
    assert c.post("/listings/L1/marketing", json={"language": "fr"}).status_code == 422


def test_route_does_not_shadow_siblings(env):
    c, *_ = env
    assert c.get("/listings/L1").json() == {"other": "L1"}


def test_uses_local_photo_and_no_amenities_card(env):
    c, db, _, up = env
    Image.new("RGB", (800, 600), (30, 30, 200)).save(up / "images" / "p.jpg")
    doc = db.get_collection("listings").docs[0]
    doc["media"] = [{"url": "http://testserver/uploads/images/p.jpg", "kind": "image", "order": 0}]
    doc["amenities"] = []
    p = c.post("/listings/L1/marketing").json()
    assert [i["kind"] for i in p["instagram"]["images"]] == ["cover", "facts", "cta"]
    with Image.open(up / "marketing/L1/cover.jpg") as i:
        r, g, b = i.getpixel((900, 300))
        assert b > 2.5 * r


def test_agent_without_public_profile_still_works(env):
    c, db, _, _ = env
    db.get_collection("agent_public_profiles").docs.clear()
    p = c.post("/listings/L1/marketing").json()
    assert p["share_url"] == "https://site.test/listings/L1?src=whatsapp"
    assert "Message us" in p["instagram"]["caption"]
