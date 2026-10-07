"""Interest links and the link-in-bio hub.

`public_router` is mounted by the integrator at /public (no auth):
  GET  /public/interest/{code}              what the landing page shows
  POST /public/interest/{code}/click        a visit
  POST /public/interest/{code}              the one-tap interest (details optional, only with consent)
  GET  /public/hub                          the Instagram bio-link page data (cached 60 s)
`router` is mounted at /interest (bearer auth): POST /interest/links, GET /interest/links/{ref}.
"""
from app.core import brand
import os
import time
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from .service import InterestError, InterestService, site_url

router = APIRouter()
public_router = APIRouter()

HUB_LIMIT = 12
HUB_TTL_S = 60
_hub_cache: Dict[str, object] = {"at": 0.0, "data": None}


async def _owner_agent_id() -> Optional[str]:
    """The platform owner agent (receives interest in samples and educational pages)."""
    explicit = os.environ.get("INTEREST_OWNER_AGENT_ID") or os.environ.get("ENGAGE_OWNER_AGENT_ID")
    if explicit:
        return explicit
    slug = os.environ.get("INTEREST_OWNER_SLUG") or "avasetu"
    profile = await get_database().get_collection("agent_public_profiles").find_one({"slug": slug, "is_public": True})
    return profile["agent_id"] if profile else None


def get_service() -> InterestService:
    return InterestService(get_database(), owner_agent_id=_owner_agent_id)


def _ip(request: Request) -> Optional[str]:
    fwd = request.headers.get("x-forwarded-for")
    if fwd and fwd.split(",")[0].strip():
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _http(e: InterestError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


class ClickIn(BaseModel):
    anon_id: Optional[str] = Field(None, max_length=64)


class InterestIn(BaseModel):
    anon_id: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = Field(None, max_length=500)
    consent: bool = False
    website: Optional[str] = None  # honeypot


class LinkIn(BaseModel):
    kind: str
    ref: str = Field(..., min_length=1, max_length=120)
    channel: str
    title: str = Field("", max_length=140)
    locality: str = Field("", max_length=80)
    image_url: str = Field("", max_length=500)
    subtitle: str = Field("", max_length=200)


# ---- public ----

@public_router.get("/interest/{code}")
async def interest_page(code: str, svc: InterestService = Depends(get_service)):
    try:
        return await svc.view(code)
    except InterestError as e:
        raise _http(e)


@public_router.post("/interest/{code}/click", status_code=202)
async def interest_click(code: str, request: Request, body: Optional[ClickIn] = None, svc: InterestService = Depends(get_service)):
    try:
        return await svc.record_click(code, _ip(request), body.anon_id if body else None)
    except InterestError as e:
        raise _http(e)


@public_router.post("/interest/{code}")
async def interest_tap(code: str, request: Request, body: Optional[InterestIn] = None, svc: InterestService = Depends(get_service)):
    b = body or InterestIn()
    try:
        return await svc.record_interest(code, name=b.name, phone=b.phone, note=b.note, consent=b.consent,
                                         website=b.website, anon_id=b.anon_id, ip=_ip(request))
    except InterestError as e:
        raise _http(e)


async def build_hub(svc: InterestService) -> dict:
    items = []
    for d in await svc.store.hub_items(HUB_LIMIT):
        items.append({"kind": d["kind"], "ref": d["ref"], "title": d["title"], "subtitle": d.get("subtitle", ""),
                      "image_url": d.get("image_url", ""), "interest_code": d.get("interest_code") or None,
                      "permalink": d.get("permalink") or None, "sample": bool(d.get("sample"))})
    site = site_url()
    return {
        "brand": os.environ.get("NEXT_PUBLIC_BUSINESS_NAME") or brand.NAME,
        "line": "Homes and guides for Pune buyers. Tap I am interested and we will get back to you.",
        "items": items,
        "links": {"website": site, "invite": f"{site}/request-invite",
                  "facebook": os.environ.get("HUB_FACEBOOK_URL") or None,
                  "instagram": os.environ.get("HUB_INSTAGRAM_URL") or None},
    }


def clear_hub_cache() -> None:
    _hub_cache.update(at=0.0, data=None)


@public_router.get("/hub")
async def hub(response: Response, svc: InterestService = Depends(get_service)):
    response.headers["Cache-Control"] = f"public, max-age={HUB_TTL_S}"
    if _hub_cache["data"] is not None and time.monotonic() - float(_hub_cache["at"]) < HUB_TTL_S:
        return _hub_cache["data"]
    data = await build_hub(svc)
    _hub_cache.update(at=time.monotonic(), data=data)
    return data


# ---- agent / owner ----
@router.post("/links")
async def create_link(body: LinkIn, user: User = Depends(current_active_user), svc: InterestService = Depends(get_service)):
    try:
        link = await svc.create_link(body.kind, body.ref, str(user.id), body.channel, title=body.title,
                                     locality=body.locality, image_url=body.image_url, subtitle=body.subtitle)
    except InterestError as e:
        raise _http(e)
    return svc.public_link(link)


@router.get("/links/{ref}")
async def links_for_ref(ref: str, user: User = Depends(current_active_user), svc: InterestService = Depends(get_service)):
    own = [l for l in await svc.store.links_for_ref(ref) if l["agent_id"] == str(user.id)]
    return {"links": [svc.public_link(l) | {"clicks": await svc.store.count(l["code"], "click"),
                                            "interests": await svc.store.count(l["code"], "interest")} for l in own]}
