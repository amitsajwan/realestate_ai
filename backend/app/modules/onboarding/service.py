"""Onboarding: OTP login and one-step agent website creation."""
import asyncio
import logging
import secrets
from datetime import datetime
from typing import Awaitable, Callable, Protocol

from .otp import OTPService
from .schemas import SiteCreate
from .slug import unique_slug

logger = logging.getLogger(__name__)

# Legacy User.email is mandatory and validated (reserved TLDs like .local/.invalid are rejected).
# Never used for delivery: phone is the real identity.
PLACEHOLDER_EMAIL_DOMAIN = "phone-login.propertyai.app"

DEFAULT_COLORS = {"primary": "#2563eb", "secondary": "#64748b", "accent": "#059669"}


class UserStore(Protocol):
    async def get_by_phone(self, phone: str): ...
    async def create(self, phone: str): ...
    async def mark_onboarded(self, user, name: str) -> None: ...


def placeholder_email(phone: str) -> str:
    return f"{phone.lstrip('+')}@{PLACEHOLDER_EMAIL_DOMAIN}"


def default_branding(name: str, city: str) -> dict:
    return {
        "tagline": f"Your trusted property partner in {city}",
        "about": (f"{name} helps families and investors buy, sell and rent property in {city}. "
                  "Honest advice, verified listings and quick responses on WhatsApp."),
        "colors": dict(DEFAULT_COLORS),
    }


async def ai_branding(name: str, city: str) -> dict:
    """AI branding suggestion with a deterministic fallback so onboarding never blocks on the LLM."""
    fallback = default_branding(name, city)
    try:
        from app.utils.ai import generate_branding
        result = await asyncio.wait_for(asyncio.to_thread(generate_branding, name), timeout=8)
        if isinstance(result, dict) and result.get("tagline") and result.get("about"):
            colors = result.get("colors") if isinstance(result.get("colors"), dict) else DEFAULT_COLORS
            return {"tagline": result["tagline"], "about": result["about"], "colors": colors}
    except Exception as exc:  # any LLM/network failure falls back
        logger.info("AI branding unavailable, using default: %s", exc)
    return fallback


class OnboardingService:
    def __init__(self, db, otp: OTPService, users: UserStore,
                 write_token: Callable[[object], Awaitable[str]], site_base_url: str,
                 branding: Callable[[str, str], Awaitable[dict]] = ai_branding):
        self.profiles = db.get_collection("agent_public_profiles")
        self.otp = otp
        self.users = users
        self.write_token = write_token
        self.site_base_url = site_base_url.rstrip("/")
        self.branding = branding

    def site_url(self, slug: str) -> str:
        return f"{self.site_base_url}/agent/{slug}"

    async def request_code(self, phone: str) -> str:
        return await self.otp.request(phone)

    async def verify_and_login(self, phone: str, code: str) -> dict:
        await self.otp.verify(phone, code)
        user = await self.users.get_by_phone(phone)
        is_new = user is None
        if is_new:
            user = await self.users.create(phone)
        profile = await self.profiles.find_one({"user_id": str(user.id)})
        return {
            "access_token": await self.write_token(user),
            "is_new_user": is_new,
            "has_site": profile is not None,
            "site_url": self.site_url(profile["slug"]) if profile else None,
        }

    async def create_site(self, user, data: SiteCreate) -> dict:
        user_id = str(user.id)
        existing = await self.profiles.find_one({"user_id": user_id})
        if existing:  # idempotent: one site per agent
            return self._result(existing, created=False)

        slug = await unique_slug(self.profiles, data.preferred_slug or "", data.name, f"{data.name}-{data.city}")
        brand = await self.branding(data.name, data.city)
        phone = data.whatsapp or getattr(user, "phone", "") or ""
        now = datetime.utcnow()
        doc = {
            "_id": user_id, "id": user_id, "user_id": user_id, "agent_id": user_id,
            "agent_name": data.name, "slug": slug, "bio": brand["about"],
            "photo": data.photo or "", "phone": phone, "email": "",
            "office_address": data.city, "specialties": data.specialties,
            "experience": "", "languages": data.languages,
            "is_active": True, "is_public": True, "view_count": 0, "contact_count": 0,
            "branding_data": {"tagline": brand["tagline"], "colors": brand["colors"]},
            "site_config": {
                "theme": brand["colors"],
                "hero": {"headline": data.name, "subheadline": brand["tagline"]},
                "sections": ["about", "listings", "contact"],
                "languages": data.languages,
                "city": data.city,
            },
            "created_at": now, "updated_at": now,
        }
        await self.profiles.insert_one(doc)
        await self.users.mark_onboarded(user, data.name)
        return self._result(doc, created=True)

    def _result(self, doc: dict, created: bool) -> dict:
        return {
            "slug": doc["slug"], "site_url": self.site_url(doc["slug"]),
            "agent_name": doc["agent_name"],
            "tagline": (doc.get("branding_data") or {}).get("tagline", ""),
            "created": created,
        }


class BeanieUserStore:
    """UserStore over the existing fastapi-users Beanie User document."""

    async def get_by_phone(self, phone: str):
        from app.models.user import User
        return await User.find_one(User.phone == phone)

    async def create(self, phone: str):
        from app.core.auth_backend import password_helper
        from app.models.user import User
        # email is still mandatory on the legacy User model; phone is the real identity.
        user = User(
            email=placeholder_email(phone),
            hashed_password=password_helper.hash(secrets.token_urlsafe(32)),
            phone=phone, is_verified=True,
        )
        await user.insert()
        return user

    async def mark_onboarded(self, user, name: str) -> None:
        parts = name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else None
        user.onboarding_completed = True
        user.updated_at = datetime.utcnow()
        await user.save()
