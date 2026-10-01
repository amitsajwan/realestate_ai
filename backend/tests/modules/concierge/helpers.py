"""Shared setup for the concierge tests (helper module, contains no tests)."""
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.modules.concierge.service import ConciergeService
from app.modules.listings.service import ListingService
from app.modules.onboarding.invites import InviteService
from app.modules.onboarding.service import OnboardingService
from app.modules.social.config import SocialConfig
from app.modules.social.service import SocialService

from ..listings_fakes import ListingsDb

DRY = SocialConfig(dry_run=True, media_base_url="https://media.test")
PHONE = "+919876543210"
FULL = dict(title="2BHK in Baner", transaction="sale", property_type="apartment", price_inr=8500000, city="Pune",
            locality="Baner", description={"en": "Bright 2BHK near the main road."})


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 12, 0, 0)

    def __call__(self):
        self.t += timedelta(seconds=1)
        return self.t


class FakeUsers:
    def __init__(self):
        self.users = {}

    async def get_by_phone(self, phone):
        return self.users.get(phone)

    async def create(self, phone):
        u = SimpleNamespace(id=f"u{len(self.users) + 1}", phone=phone)
        self.users[phone] = u
        return u

    async def mark_onboarded(self, user, name):
        pass


async def fake_branding(name, city):
    return {"tagline": "t", "about": "a", "colors": {"primary": "#111"}}


def make(db=None, config=DRY):
    db = db or ListingsDb()
    clock, users = Clock(), FakeUsers()
    invites = InviteService(db, "secret", now=clock)

    async def no_token(u):
        return "tok"

    onboarding = OnboardingService(db, invites, users, no_token, "https://pune.test", branding=fake_branding)
    svc = ConciergeService(db, invites=invites, onboarding=onboarding, users=users, listings=ListingService(db, now=clock),
                           social=SocialService(db, config_loader=lambda: config), site_url="https://pune.test", now=clock)
    return svc, db, invites


def pack(agent_id: str, listing_id: str) -> dict:
    return {"_id": listing_id, "agent_id": agent_id, "version": 1,
            "share_url": f"https://pune.test/agent/rahul/listings/{listing_id}?src=whatsapp",
            "facebook": {"post": "Ready 2 BHK in Baner"}, "instagram": {"caption": "2 BHK in Baner", "hashtags": ["#Pune"]},
            "images": {k: {"path": f"/uploads/marketing/{listing_id}/{k}.jpg", "width": 1080, "height": 1080}
                       for k in ("cover", "facts", "amenities", "cta")}}
