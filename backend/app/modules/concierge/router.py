"""Owner-only concierge endpoints. `router` is mounted by the integrator at /concierge (bearer auth).

Closed by default: only superusers and ids in CONCIERGE_OWNER_IDS get in (403 otherwise).
"""
from app.core import brand
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Callable, Deque, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.auth_backend import current_active_user
from app.core.config import settings
from app.core.database import get_database
from app.models.user import User
from app.modules.listings.schemas import ListingCreate, ListingUpdate
from app.modules.listings.service import ListingError, ListingService
from app.modules.onboarding.phone import normalize_indian_mobile

from . import config
from .service import ConciergeError, ConciergeService

router = APIRouter()

CHANNELS = ("facebook_page", "instagram")


class Limiter:
    """Sliding-window limit per owner and bucket (in memory; one owner, one process is the pilot)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock, self.hits = clock, defaultdict(deque)  # type: Callable, Dict[tuple, Deque[float]]

    def check(self, who: str, bucket: str, limit: int, window: float) -> None:
        q, now = self.hits[(who, bucket)], self.clock()
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, "Too many requests, slow down a little")
        q.append(now)


limiter = Limiter()


async def owner_only(user: User = Depends(current_active_user)) -> User:
    if getattr(user, "is_superuser", False) or str(user.id) in config.owner_ids():
        return user
    raise HTTPException(403, f"Only the {brand.NAME} owner can use the concierge")


def writer(bucket: str, limit: int, window: float = 60.0):
    async def dep(user: User = Depends(owner_only)) -> User:
        limiter.check(str(user.id), bucket, limit, window)
        return user
    return dep


def get_service() -> ConciergeService:
    from app.modules.marketing.polish import default_polish
    from app.modules.marketing.service import MarketingService
    from app.modules.onboarding.invites import InviteService
    from app.modules.onboarding.service import BeanieUserStore, OnboardingService
    from app.modules.social.service import SocialService
    db = get_database()
    invites, users = InviteService(db, settings.jwt_secret_key), BeanieUserStore()

    async def no_token(user) -> str:  # the concierge never logs in as the agent
        raise RuntimeError("not used")

    return ConciergeService(
        db, invites=invites, users=users, onboarding=OnboardingService(db, invites, users, no_token, settings.public_site_url),
        listings=ListingService(db), social=SocialService(db), site_url=settings.public_site_url,
        marketing=MarketingService(db, Path(settings.upload_directory), settings.public_site_url, polish=default_polish()))


def _http(e: Exception) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail if hasattr(e, "detail") else str(e))


class CreateAgentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=2, max_length=100)
    mobile: str
    label: str = Field("", max_length=80)
    reissue: bool = False

    @field_validator("name", "label")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("mobile")
    @classmethod
    def _mobile(cls, v: str) -> str:
        return normalize_indian_mobile(v)


class ConsentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    given: bool = True
    text: Optional[str] = None


class PostIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channels: List[str] = Field(default_factory=lambda: list(CHANNELS), min_length=1)

    @field_validator("channels")
    @classmethod
    def _ok(cls, v: List[str]) -> List[str]:
        if any(c not in CHANNELS for c in v):
            raise ValueError("channels must be facebook_page and/or instagram")
        return v


class PackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = "en"


async def _run(coro):
    try:
        return await coro
    except (ConciergeError, ListingError) as e:
        raise _http(e)


@router.post("/agents", status_code=201)
async def create_agent(body: CreateAgentIn, user: User = Depends(writer("invite", 10, 3600)),
                       svc: ConciergeService = Depends(get_service)):
    return await _run(svc.create_agent(str(user.id), body.name, body.mobile, body.label, body.reissue))


@router.get("/agents")
async def list_agents(user: User = Depends(owner_only), svc: ConciergeService = Depends(get_service)):
    return {"items": await svc.list_agents()}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user: User = Depends(owner_only), svc: ConciergeService = Depends(get_service)):
    return await _run(svc.get_agent(agent_id))


@router.post("/agents/{agent_id}/consent")
async def record_consent(agent_id: str, body: Optional[ConsentIn] = None, user: User = Depends(writer("write", 60)),
                         svc: ConciergeService = Depends(get_service)):
    body = body or ConsentIn()
    return await _run(svc.record_consent(str(user.id), agent_id, body.given, body.text))


@router.post("/agents/{agent_id}/listings", status_code=201)
async def create_listing(agent_id: str, body: ListingCreate, user: User = Depends(writer("write", 60)),
                         svc: ConciergeService = Depends(get_service)):
    return await _run(svc.create_listing(str(user.id), agent_id, body))


@router.patch("/agents/{agent_id}/listings/{listing_id}")
async def update_listing(agent_id: str, listing_id: str, body: ListingUpdate, user: User = Depends(writer("write", 60)),
                         svc: ConciergeService = Depends(get_service)):
    return await _run(svc.patch_listing(str(user.id), agent_id, listing_id, body))


@router.post("/agents/{agent_id}/listings/{listing_id}/publish")
async def publish_listing(agent_id: str, listing_id: str, user: User = Depends(writer("write", 60)),
                          svc: ConciergeService = Depends(get_service)):
    return await _run(svc.publish_listing(str(user.id), agent_id, listing_id))


@router.post("/agents/{agent_id}/listings/{listing_id}/pack")
async def make_pack(agent_id: str, listing_id: str, request: Request, body: Optional[PackIn] = None,
                    user: User = Depends(writer("write", 30)), svc: ConciergeService = Depends(get_service)):
    return await _run(svc.make_pack(str(user.id), agent_id, listing_id, str(request.base_url), (body or PackIn()).language))


@router.post("/agents/{agent_id}/listings/{listing_id}/captions")
async def captions(agent_id: str, listing_id: str, body: Optional[PostIn] = None, user: User = Depends(owner_only),
                   svc: ConciergeService = Depends(get_service)):
    return {"captions": await _run(svc.captions(agent_id, listing_id, (body or PostIn()).channels))}


@router.post("/agents/{agent_id}/listings/{listing_id}/post")
async def post_listing(agent_id: str, listing_id: str, body: Optional[PostIn] = None, user: User = Depends(writer("post", 20)),
                       svc: ConciergeService = Depends(get_service)):
    return {"publications": await _run(svc.post_listing(str(user.id), agent_id, listing_id, (body or PostIn()).channels))}


@router.get("/agents/{agent_id}/branding")
async def get_branding(agent_id: str, user: User = Depends(owner_only), svc: ConciergeService = Depends(get_service)):
    return await _run(svc.get_branding(agent_id))


@router.post("/agents/{agent_id}/branding")
async def update_branding(agent_id: str, body: dict, user: User = Depends(writer("write", 60)),
                          svc: ConciergeService = Depends(get_service)):
    return await _run(svc.update_branding(str(user.id), agent_id, body))
