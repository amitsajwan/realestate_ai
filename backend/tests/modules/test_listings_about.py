"""The optional `about` object on listings: validation, owner scoping, public exposure."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.listings import router as lr

from .listings_fakes import ListingsDb
from .test_listings_router import FULL

ABOUT = {
    "project_name": "Rohan Heights",
    "highlights": ["East facing", "Corner flat"],
    "amenities": ["Lift", "Gym"],
    "nearby": [{"type": "school", "name": "School nearby", "minutes": 5}],
    "connectivity": ["Metro Line 4 is approved, not running yet."],
    "water": "24x7 water supply", "parking": "1 covered parking", "maintenance": "Maintenance ₹3,000 per month",
    "faq": [{"q": "Is parking included?", "a": "Yes, one covered slot."}],
}


@pytest.fixture
def env():
    db = ListingsDb()
    svc = lr.ListingService(db)
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(lr.router, prefix="/listings")
    app.include_router(lr.public_router, prefix="/public")
    app.dependency_overrides[lr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    db.get_collection("agent_public_profiles").docs.append(
        {"slug": "rahul", "agent_id": "A1", "agent_name": "Rahul", "phone": "1", "photo": None, "is_public": True})
    return TestClient(app), who


def test_about_is_optional(env):
    c, _ = env
    r = c.post("/listings", json=FULL)
    assert r.status_code == 201 and r.json()["about"] is None


def test_create_and_read_about_roundtrip(env):
    c, _ = env
    r = c.post("/listings", json={**FULL, "about": ABOUT})
    assert r.status_code == 201, r.text
    got = c.get(f"/listings/{r.json()['id']}").json()["about"]
    assert got["highlights"] == ["East facing", "Corner flat"]
    assert got["nearby"] == [{"type": "school", "name": "School nearby", "minutes": 5}]
    assert got["faq"][0]["q"] == "Is parking included?"


def test_patch_about_and_owner_scoping(env):
    c, who = env
    lid = c.post("/listings", json=FULL).json()["id"]
    assert c.patch(f"/listings/{lid}", json={"about": {"water": "Borewell water"}}).json()["about"]["water"] == "Borewell water"
    who.id = "B2"  # another agent: 404, never 403
    assert c.patch(f"/listings/{lid}", json={"about": {"water": "x"}}).status_code == 404
    assert c.get(f"/listings/{lid}").status_code == 404


@pytest.mark.parametrize("bad", [
    "Call me on 98765 43210", "Call +91 98765-43210", "9876543210", "Visit https://example.com/flat",
    "see www.mysite.in", "details at mysite.com",
])
def test_phone_numbers_and_links_are_rejected_with_a_clear_message(env, bad):
    c, _ = env
    for body in ({"highlights": [bad]}, {"water": bad}, {"faq": [{"q": "Q", "a": bad}]}, {"nearby": [{"type": "other", "name": bad}]}):
        r = c.post("/listings", json={**FULL, "about": body})
        assert r.status_code == 422
        msg = str(r.json()["detail"])
        assert "phone number" in msg or "web link" in msg


def test_ordinary_numbers_are_fine(env):
    c, _ = env
    about = {"highlights": ["1100 sq ft carpet, 2,00,000 maintenance fund, 24x7 water, 12 floors"], "maintenance": "Maintenance ₹3,000 per month"}
    assert c.post("/listings", json={**FULL, "about": about}).status_code == 201


def test_caps_and_types(env):
    c, _ = env
    for body in (
        {"highlights": ["a"] * 7},
        {"amenities": ["a"] * 21},
        {"connectivity": ["a"] * 9},
        {"nearby": [{"type": "other", "name": "n"}] * 13},
        {"faq": [{"q": "q", "a": "a"}] * 9},
        {"water": "x" * 301},
        {"highlights": ["x" * 301]},
        {"highlights": "not a list"},
        {"highlights": [5]},
        {"nearby": [{"type": "airport", "name": "n"}]},
        {"nearby": [{"type": "school", "name": "n", "minutes": 9999}]},
        {"unknown_field": "x"},
    ):
        assert c.post("/listings", json={**FULL, "about": body}).status_code == 422, body
    ok = {"highlights": ["a"] * 6, "faq": [{"q": "q", "a": "a"}] * 8, "water": "x" * 300}
    assert c.post("/listings", json={**FULL, "about": ok}).status_code == 201


def test_control_characters_and_angle_brackets_are_stripped(env):
    c, _ = env
    r = c.post("/listings", json={**FULL, "about": {"highlights": ["Nice\x00 <script>alert(1)</script>​ view\n\n"]}})
    assert r.status_code == 201
    hl = r.json()["about"]["highlights"][0]
    assert "<" not in hl and ">" not in hl and "\x00" not in hl and "​" not in hl and "\n" not in hl


def test_public_listing_shows_about_but_not_the_faq(env):
    c, _ = env
    lid = c.post("/listings", json={**FULL, "about": ABOUT}).json()["id"]
    c.post(f"/listings/{lid}/publish")
    pub = c.get(f"/public/listings/{lid}").json()
    assert pub["about"]["highlights"] == ["East facing", "Corner flat"]
    assert pub["about"]["water"] == "24x7 water supply"
    assert "faq" not in pub["about"]
    page = c.get("/public/agents/rahul/listings").json()
    assert "faq" not in page["items"][0]["about"]


def test_public_listing_without_about(env):
    c, _ = env
    lid = c.post("/listings", json=FULL).json()["id"]
    c.post(f"/listings/{lid}/publish")
    assert c.get(f"/public/listings/{lid}").json()["about"] is None
