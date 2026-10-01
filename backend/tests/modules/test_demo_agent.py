"""The demo agent: owner-only `demo` branding flag (passthrough, agents cannot set it) and scripts/create_demo_agent.py."""
import re
from types import SimpleNamespace

import pytest

from app.modules.listings.service import ListingService
from app.modules.onboarding import branding as bd
from app.modules.onboarding.schemas import SiteCreate, SiteUpdate
from app.modules.showcase import samples
from app.services.agent_public_service import AgentPublicService
from scripts import create_demo_agent as cda

from .fakes import FakeDb
from .test_onboarding import make

pytestmark = pytest.mark.asyncio

PHONE_LIKE = re.compile(r"(?:\+?\d[\s\-().]*){7,}")


# ---- the flag ---------------------------------------------------------------------------------------------
def test_demo_is_an_owner_only_key_not_an_agent_field():
    assert "demo" in bd.OWNER_ONLY_KEYS
    assert "demo" not in SiteUpdate.model_fields and "demo" not in SiteCreate.model_fields
    assert "demo" not in SiteUpdate(demo=True, tagline="Baner homes").model_dump()


async def test_agent_cannot_set_demo_on_create_or_update():
    svc, db, _, users, _ = make()
    user = await users.create("+919876543210")
    await svc.create_site(user, SiteCreate(name="Priya Deshmukh", city="Pune", demo=True))
    out = await svc.update_site(user, SiteUpdate(**{"demo": True, "tagline": "Baner homes, honestly"}))
    assert "demo" not in out["branding_data"]
    doc = await db.get_collection("agent_public_profiles").find_one({"user_id": user.id})
    assert "demo" not in doc["branding_data"]


async def test_agent_edit_keeps_the_owner_set_demo_flag():
    svc, db, _, users, _ = make()
    user = await users.create("+919876543210")
    await svc.create_site(user, SiteCreate(name="Priya Deshmukh", city="Pune"))
    profiles = db.get_collection("agent_public_profiles")
    doc = await profiles.find_one({"user_id": user.id})
    await profiles.update_one({"user_id": user.id}, {"$set": {"branding_data": {**doc["branding_data"], "demo": True}}})
    out = await svc.update_site(user, SiteUpdate(tagline="Baner homes, honestly", demo=False))
    assert out["branding_data"]["demo"] is True and out["branding_data"]["tagline"] == "Baner homes, honestly"


# ---- the script ---------------------------------------------------------------------------------------------
class DemoUsers:
    def __init__(self):
        self.users, self.onboarded = {}, []

    async def get_by_phone(self, phone):
        return self.users.get(phone)

    async def create(self, phone):
        u = SimpleNamespace(id=f"u{len(self.users) + 1}", phone=phone, is_active=True)
        self.users[phone] = u
        return u

    async def deactivate(self, user):
        user.is_active = False

    async def mark_onboarded(self, user, name):
        self.onboarded.append(name)


async def _run(db, users, tmp_path):
    return await cda.create_demo_agent(db, users, tmp_path, log=lambda *_: None)


async def test_creates_demo_profile_with_flag_images_and_no_contact_details(tmp_path):
    db, users = FakeDb(), DemoUsers()
    out = await _run(db, users, tmp_path)
    user = users.users[cda.DEMO_PHONE]
    assert user.is_active is False and out["user_id"] == user.id
    with pytest.raises(ValueError):  # the placeholder cannot be used to sign in
        from app.modules.onboarding.phone import normalize_indian_mobile
        normalize_indian_mobile(cda.DEMO_PHONE)

    p = await db.get_collection("agent_public_profiles").find_one({"slug": "demo"})
    b = p["branding_data"]
    assert b["demo"] is True and b["business_name"] == "Avasetu Demo Homes" and b["preset"] == "emerald"
    assert b["tagline"] == "Kharadi and Wagholi homes, explained clearly"
    assert b["areas"] == ["Kharadi", "Upper Kharadi", "Wagholi"] and b["languages"] == ["English", "Hindi", "Marathi"]
    assert "rera_agent_no" not in b
    assert p["phone"] == "" and p["email"] == "" and p["is_public"] is True
    for key in ("logo", "banner"):
        assert re.match(r"^/uploads/images/[A-Za-z0-9][A-Za-z0-9._-]+$", b[key])
        assert (tmp_path / "images" / b[key].rsplit("/", 1)[1]).stat().st_size > 1000

    from PIL import Image
    with Image.open(tmp_path / "images" / cda.LOGO_FILE) as im:
        assert im.size == (512, 512)
    with Image.open(tmp_path / "images" / cda.BANNER_FILE) as im:
        assert im.size == (1600, 600)


async def test_nine_live_sample_listings_labelled_like_seed_samples(tmp_path):
    db, users = FakeDb(), DemoUsers()
    await _run(db, users, tmp_path)
    items, total = await ListingService(db).public_list("demo", limit=50)
    assert total == len(samples.HOMES) == 9
    for it in items:
        assert it.title.startswith("Sample: ") and it.description.en.startswith("SAMPLE LISTING")
        assert "not available for sale" in it.description.en
        assert it.status == "live" and not it.rera_no
        assert it.media and all((tmp_path / "images" / m.url.rsplit("/", 1)[1]).is_file() for m in it.media)
    # samples never appear in the real-listings locality feed
    assert (await ListingService(db).public_by_locality("Kharadi"))[0] == []


async def test_idempotent(tmp_path):
    db, users = FakeDb(), DemoUsers()
    first = await _run(db, users, tmp_path)
    second = await _run(db, users, tmp_path)
    assert first["created"] == 9 and second["created"] == 0 and second["updated"] == 9
    assert first["user_id"] == second["user_id"] and len(users.users) == 1
    assert len(db.get_collection("agent_public_profiles").docs) == 1
    assert len(db.get_collection("listings").docs) == 9
    assert first["listings"] == second["listings"]


async def test_public_data_has_no_phone_number_and_passes_the_flag(tmp_path):
    db, users = FakeDb(), DemoUsers()
    await _run(db, users, tmp_path)
    profile = await AgentPublicService(db).get_agent_by_slug("demo")
    data = profile.model_dump()
    assert data["branding_data"]["demo"] is True
    assert not data["phone"] and not data["email"]
    items, _ = await ListingService(db).public_list("demo", limit=50)
    texts = [str(v) for v in data["branding_data"].values()] + [data.get("bio") or ""]
    texts += [i.title + " " + i.description.en for i in items]
    assert not any(PHONE_LIKE.search(t.replace("/uploads/images/", "")) for t in texts if not t.startswith("/uploads"))
    assert all(not i.agent.phone for i in items)


async def test_refuses_to_take_over_a_demo_slug_owned_by_someone_else(tmp_path):
    db, users = FakeDb(), DemoUsers()
    await db.get_collection("agent_public_profiles").insert_one({"_id": "x", "slug": "demo", "user_id": "someone-else"})
    with pytest.raises(SystemExit):
        await _run(db, users, tmp_path)
