"""Owner-only Admin home endpoints, mounted at /admin (bearer auth).

Closed by default, like the concierge: only superusers and ids in CONCIERGE_OWNER_IDS get in (403 otherwise).
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.core import brand
from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.concierge import config as concierge_config
from app.modules.concierge.router import get_service as get_concierge, limiter
from app.modules.concierge.service import ConciergeError

from app.platform import controls
from . import health
from .service import AdminError, AdminService

router = APIRouter()


async def owner_only(user: User = Depends(current_active_user)) -> User:
    if getattr(user, "is_superuser", False) or str(user.id) in concierge_config.owner_ids():
        return user
    raise HTTPException(403, f"Only the {brand.NAME} owner can open Admin")


def get_service() -> AdminService:
    return AdminService(get_database())


def get_ai_ping():
    return health.default_ai_ping


class ControlsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    posting_paused: Optional[bool] = None
    comments_paused: Optional[bool] = None
    news_paused: Optional[bool] = None


def _agent_view(a: dict) -> dict:
    keep = ("id", "name", "label", "slug", "mobile", "site_url", "progress", "listing_count", "consent_given", "last_activity", "checklist")
    return {k: a.get(k) for k in keep}


async def _seo_rows(svc: AdminService) -> list:
    from app.modules.areastats.searchconsole import key as gsc_key
    from app.modules.seo.indexnow import key as indexnow_key
    marks = {d["_id"]: d for d in await svc.c("newsroom_status").find({"_id": {"$in": ["indexnow", "gsc_coverage", "gsc_pages"]}}).to_list(3)}
    from app.modules.communities.discover import COLLECTION as COMMUNITIES
    from app.modules.communities.runner import enabled as articles_on
    hoods = await svc.c(COMMUNITIES).find({}).to_list(None)
    held = sorted((d for d in hoods if not d.get("published") and d.get("write_notes")), key=lambda d: d.get("written_at"), reverse=True)
    articles = {"found": len(hoods), "published": sum(1 for d in hoods if d.get("published")),
                "last_note": f"{held[0]['name']}: {held[0]['write_notes'][0]}" if held else None}
    return health.seo_rows(indexnow_on=indexnow_key() is not None, gsc_on=gsc_key() is not None, indexnow=marks.get("indexnow"),
                           coverage=marks.get("gsc_coverage"), pages=marks.get("gsc_pages"), articles_on=articles_on(),
                           articles=articles)


@router.get("/overview")
async def overview(user: User = Depends(owner_only), svc: AdminService = Depends(get_service), concierge=Depends(get_concierge),
                   ai_ping=Depends(get_ai_ping)) -> dict:
    from app.modules.calendar.config import load as load_calendar
    from app.modules.engage.config import load as load_engage
    from app.modules.newsroom.config import load as load_newsroom
    from app.platform.meta_graph.config import load as load_social
    from app.modules.whatsapp.config import load as load_wa
    from app.modules.whatsapp.dm_config import load as load_dm
    ctl = await svc.controls()
    cal_run, news_run = await svc.run_status("calendar_status"), await svc.run_status("newsroom_status")
    rows = health.build_health(social=load_social(), wa=load_wa(), engage=load_engage(), calendar=load_calendar(), newsroom=load_newsroom(),
                               meta=await svc.meta_status(), cal_run=cal_run, news_run=news_run, controls=ctl,
                               ai=await health.ai_status(ai_ping), dm=load_dm())
    rows += await _seo_rows(svc)
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "counts": await svc.counts(),
        "waiting": await svc.waiting(),
        "invite_requests": await svc.invite_requests(),
        "agents": [_agent_view(a) for a in await concierge.list_agents()],
        "health": rows,
        "controls": ctl,
    }


@router.get("/controls")
async def get_controls(user: User = Depends(owner_only), svc: AdminService = Depends(get_service)) -> dict:
    return await svc.controls()


@router.post("/controls")
async def set_controls(body: ControlsIn, user: User = Depends(owner_only), svc: AdminService = Depends(get_service)) -> dict:
    limiter.check(str(user.id), "admin-controls", 30, 60.0)
    return await controls.set_controls(svc.db, body.model_dump(exclude_none=True), str(user.id), svc.now())


@router.get("/invite-requests")
async def invite_requests(user: User = Depends(owner_only), svc: AdminService = Depends(get_service)) -> dict:
    return {"items": await svc.invite_requests()}


@router.get("/trial-signups")
async def trial_signups(user: User = Depends(owner_only), svc: AdminService = Depends(get_service)) -> dict:
    return {"items": await svc.trial_signups()}


async def _run(coro):
    try:
        return await coro
    except (AdminError, ConciergeError) as e:
        raise HTTPException(e.status_code, getattr(e, "detail", None) or str(e))


@router.post("/invite-requests/{id}/invite")
async def invite(id: str, user: User = Depends(owner_only), svc: AdminService = Depends(get_service), concierge=Depends(get_concierge)) -> dict:
    limiter.check(str(user.id), "invite", 10, 3600.0)  # the same budget as Add agent
    return await _run(svc.invite(id, str(user.id), concierge))


@router.post("/invite-requests/{id}/dismiss")
async def dismiss(id: str, user: User = Depends(owner_only), svc: AdminService = Depends(get_service)) -> dict:
    return await _run(svc.dismiss(id, str(user.id)))


# ---- hot projects banner on the public site (areastats/spotlight.py) ---------------------------------------------------------
from app.modules.areastats import spotlight  # noqa: E402


class SpotlightItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str
    area: Optional[str] = None
    note: Optional[str] = None
    until: Optional[str] = None


class SpotlightIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto: bool = True
    items: list[SpotlightItemIn] = []


@router.get("/spotlight")
async def get_spotlight(user: User = Depends(owner_only), svc: AdminService = Depends(get_service)) -> dict:
    """The owner's picks, plus what the strip shows right now on pages with no area (to check the result)."""
    return {**await spotlight.get_config(svc.db), "preview": await spotlight.public(svc.db)}


@router.put("/spotlight")
async def put_spotlight(body: SpotlightIn, user: User = Depends(owner_only), svc: AdminService = Depends(get_service)) -> dict:
    limiter.check(str(user.id), "admin-spotlight", 30, 60.0)
    try:
        cfg = await spotlight.set_config(svc.db, body.model_dump(), str(user.id), svc.now())
    except spotlight.SpotlightError as e:
        raise HTTPException(400, str(e))
    return {**cfg, "preview": await spotlight.public(svc.db)}
