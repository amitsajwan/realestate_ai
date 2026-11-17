"""Area photo routes. `router` is mounted at /area-photos (bearer auth: any signed-in agent; publishing is the owner's),
`public_router` at /public (no auth).

  GET   /area-photos?area=<key|slug>     an area's photos, every status, in the page's order, and whether you may publish
  POST  /area-photos                     upload one photo (multipart: file, area, caption, taken_on, credit, kind, licence,
                                         source_url); it waits as `pending`
  PATCH /area-photos/{id}                change caption, credit, date, kind, licence or link (the owner: any; an agent: his own
                                         while it waits)
  POST  /area-photos/{id}/publish        (owner) show it on the area guide
  POST  /area-photos/{id}/hide           (owner) take it off the guide
  PUT   /area-photos/order               (owner) {area, ids}: the order photos show in
  GET   /public/areas/{slug}/photos      the live photos for /localities/<slug>, with who took them, when, and any licence

Who is the owner: superusers, and the operator console's check passed in by app/wiring.py (CONCIERGE_OWNER_IDS), as for the
photo quality review and the radar; this module sits below the console and does not import it.
"""
import logging
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.platform import media

from .service import AreaPhotos, PhotoRefused, view

log = logging.getLogger(__name__)

router = APIRouter()
public_router = APIRouter()
CACHE_SECONDS = 300

_hooks: Dict[str, Any] = {"is_operator": lambda user: False}


def configure(is_operator: Callable[[User], bool]) -> None:
    _hooks["is_operator"] = is_operator


def is_admin(user: User) -> bool:
    return bool(getattr(user, "is_superuser", False)) or bool(_hooks["is_operator"](user))


async def admin_only(user: User = Depends(current_active_user)) -> User:
    if is_admin(user):
        return user
    raise HTTPException(403, "Only the owner can publish, hide or reorder area photos")


def get_service() -> AreaPhotos:
    return AreaPhotos(get_database())


async def _run(coro):
    try:
        return await coro
    except PhotoRefused as e:
        raise HTTPException(e.status_code, str(e))


class EditIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    caption: Optional[str] = Field(None, max_length=400)
    credit: Optional[str] = Field(None, max_length=200)
    taken_on: Optional[str] = Field(None, max_length=10)
    kind: Optional[str] = Field(None, max_length=10)
    licence: Optional[str] = Field(None, max_length=20)
    source_url: Optional[str] = Field(None, max_length=600)


class OrderIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    area: str = Field(..., min_length=1, max_length=40)
    ids: List[str] = Field(..., max_length=200)


def _studio(d: dict, user: User) -> dict:
    admin = is_admin(user)
    mine = d.get("created_by") == str(user.id)
    return {**view(d), "mine": mine, "can_edit": admin or (mine and d["status"] == "pending")}


@router.get("")
async def list_photos(area: str, user: User = Depends(current_active_user), svc: AreaPhotos = Depends(get_service)) -> dict:
    try:
        a = svc.area(area)
    except PhotoRefused as e:
        raise HTTPException(e.status_code, str(e))
    docs = await svc.list_area(a.key)
    return {"area": {"key": a.key, "name": a.name, "slug": a.slug}, "items": [_studio(d, user) for d in docs],
            "can_publish": is_admin(user)}


@router.post("", status_code=201)
async def upload_photo(file: UploadFile = File(...), area: str = Form(...), caption: str = Form(""), taken_on: str = Form(""),
                       credit: str = Form(""), kind: str = Form(""), licence: str = Form(""), source_url: str = Form(""),
                       user: User = Depends(current_active_user), svc: AreaPhotos = Depends(get_service)) -> dict:
    body = await file.read(media.MAX_PHOTO_BYTES + 1)
    facts = {"caption": caption, "taken_on": taken_on, "credit": credit, "kind": kind, "licence": licence, "source_url": source_url}
    d = await _run(svc.add(area, facts, body, (file.content_type or "").lower(), str(user.id)))
    return _studio(d, user)


@router.put("/order")
async def reorder(body: OrderIn, user: User = Depends(admin_only), svc: AreaPhotos = Depends(get_service)) -> dict:
    docs = await _run(svc.reorder(body.area, body.ids, str(user.id)))
    return {"items": [_studio(d, user) for d in docs]}


@router.patch("/{pid}")
async def edit_photo(pid: str, body: EditIn, user: User = Depends(current_active_user),
                     svc: AreaPhotos = Depends(get_service)) -> dict:
    d = await _run(svc.edit(pid, body.model_dump(exclude_none=True), str(user.id), is_admin(user)))
    return _studio(d, user)


@router.post("/{pid}/publish")
async def publish(pid: str, user: User = Depends(admin_only), svc: AreaPhotos = Depends(get_service)) -> dict:
    return _studio(await _run(svc.set_status(pid, "live", str(user.id))), user)


@router.post("/{pid}/hide")
async def hide(pid: str, user: User = Depends(admin_only), svc: AreaPhotos = Depends(get_service)) -> dict:
    return _studio(await _run(svc.set_status(pid, "hidden", str(user.id))), user)


@public_router.get("/areas/{slug}/photos")
async def public_photos(slug: str, response: Response, svc: AreaPhotos = Depends(get_service)) -> dict:
    out = await svc.public(slug)
    if out is None:
        raise HTTPException(404, "Unknown area")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out
