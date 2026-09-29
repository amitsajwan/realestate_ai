from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.modules.onboarding.otp import OTPError, OTPService
from app.modules.onboarding.phone import normalize_indian_mobile
from app.modules.onboarding.schemas import SiteCreate
from app.modules.onboarding.service import OnboardingService, default_branding, placeholder_email
from app.modules.onboarding.slug import slugify, unique_slug

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 12, 0, 0)

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


class SentBox:
    def __init__(self):
        self.sent = []

    async def send(self, phone, code):
        self.sent.append((phone, code))


class FakeUsers:
    def __init__(self):
        self.users = {}
        self.onboarded = []

    async def get_by_phone(self, phone):
        return self.users.get(phone)

    async def create(self, phone):
        u = SimpleNamespace(id=f"u{len(self.users) + 1}", phone=phone)
        self.users[phone] = u
        return u

    async def mark_onboarded(self, user, name):
        self.onboarded.append((user.id, name))


async def _branding(name, city):
    return default_branding(name, city)


async def _token(user):
    return f"token-for-{user.id}"


def make(clock=None):
    clock = clock or Clock()
    db, box, users = FakeDb(), SentBox(), FakeUsers()
    otp = OTPService(db, box, "secret", now=clock)
    svc = OnboardingService(db, otp, users, _token, "https://x.test/", branding=_branding)
    return svc, db, box, users, clock


def test_phone_normalisation():
    assert normalize_indian_mobile("+91 98765 43210") == "+919876543210"
    assert normalize_indian_mobile("09876543210") == "+919876543210"
    assert normalize_indian_mobile("919876543210") == "+919876543210"
    for bad in ("12345", "5876543210", "+1 415 555 2671", ""):
        with pytest.raises(ValueError):
            normalize_indian_mobile(bad)


def test_slugify():
    assert slugify("Rahul Sharma!") == "rahul-sharma"
    assert slugify("  Ünïcode Réalty ") == "unicode-realty"


async def test_unique_slug_skips_taken_and_reserved():
    col = FakeDb().get_collection("p")
    assert await unique_slug(col, "admin", "Rahul Sharma") == "rahul-sharma"
    await col.insert_one({"slug": "rahul-sharma"})
    assert await unique_slug(col, "Rahul Sharma") == "rahul-sharma-2"


async def test_otp_login_creates_user_and_token():
    svc, _, box, users, clock = make()
    code = await svc.request_code("+919876543210")
    assert box.sent == [("+919876543210", code)]
    res = await svc.verify_and_login("+919876543210", code)
    assert res["is_new_user"] and not res["has_site"]
    assert res["access_token"] == "token-for-u1"
    # same phone again logs into the same user
    clock.advance(minutes=1)
    code2 = await svc.request_code("+919876543210")
    res2 = await svc.verify_and_login("+919876543210", code2)
    assert not res2["is_new_user"] and res2["access_token"] == "token-for-u1"
    assert len(users.users) == 1


async def test_wrong_code_counts_attempts_then_locks():
    svc, _, _, _, _ = make()
    code = await svc.request_code("+919876543210")
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        with pytest.raises(OTPError):
            await svc.verify_and_login("+919876543210", wrong)
    with pytest.raises(OTPError) as e:
        await svc.verify_and_login("+919876543210", code)  # even the right code is now locked
    assert e.value.status_code == 429


async def test_code_expires_and_is_single_use():
    svc, _, _, _, clock = make()
    code = await svc.request_code("+919876543210")
    clock.advance(minutes=6)
    with pytest.raises(OTPError):
        await svc.verify_and_login("+919876543210", code)
    clock.advance(seconds=1)
    code = await svc.request_code("+919876543210")
    await svc.verify_and_login("+919876543210", code)
    with pytest.raises(OTPError):
        await svc.verify_and_login("+919876543210", code)


async def test_resend_cooldown_and_hourly_cap():
    svc, _, _, _, clock = make()
    await svc.request_code("+919876543210")
    with pytest.raises(OTPError) as e:
        await svc.request_code("+919876543210")
    assert e.value.status_code == 429
    for _ in range(4):
        clock.advance(seconds=31)
        await svc.request_code("+919876543210")
    clock.advance(seconds=31)
    with pytest.raises(OTPError):
        await svc.request_code("+919876543210")  # 6th within the hour


async def test_create_site_is_live_shape_and_idempotent():
    svc, db, _, users, _ = make()
    user = await users.create("+919876543210")
    data = SiteCreate(name="Rahul Sharma", city="Pune", specialties=["2BHK"])
    res = await svc.create_site(user, data)
    assert res["created"] and res["slug"] == "rahul-sharma"
    assert res["site_url"] == "https://x.test/agent/rahul-sharma"
    doc = await db.get_collection("agent_public_profiles").find_one({"slug": "rahul-sharma"})
    # shape the existing public-site endpoints read
    for key in ("agent_id", "agent_name", "bio", "phone", "languages", "is_public", "branding_data"):
        assert key in doc
    assert doc["agent_id"] == user.id and doc["phone"] == "+919876543210"
    assert doc["site_config"]["sections"] == ["about", "listings", "contact"]
    assert users.onboarded == [(user.id, "Rahul Sharma")]

    again = await svc.create_site(user, SiteCreate(name="Other Name", city="Pune"))
    assert not again["created"] and again["slug"] == "rahul-sharma"
    assert await db.get_collection("agent_public_profiles").count_documents({}) == 1


async def test_two_agents_same_name_get_distinct_slugs():
    svc, _, _, users, _ = make()
    a, b = await users.create("+919876543210"), await users.create("+919876543211")
    ra = await svc.create_site(a, SiteCreate(name="Rahul Sharma", city="Pune"))
    rb = await svc.create_site(b, SiteCreate(name="Rahul Sharma", city="Pune"))
    assert ra["slug"] != rb["slug"]


def test_placeholder_email_is_valid_for_legacy_user_model():
    """Regression: '.local' addresses are rejected by email validation (found in real-Mongo e2e run)."""
    from pydantic import TypeAdapter, EmailStr
    assert TypeAdapter(EmailStr).validate_python(placeholder_email("+919876543210"))
