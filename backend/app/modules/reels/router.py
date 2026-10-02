"""Listing reel routes for the agent. `router` is mounted by the integrator at prefix /listings (bearer auth, owner scoped):

  POST /listings/{listing_id}/reel  {lang: en|hi|mr, again?: bool}  -> 202 {job, created}
  GET  /listings/{listing_id}/reel                                  -> {jobs: {lang: job}}  (latest job per language)

Two segments ending in "reel", so they cannot shadow "/{listing_id}" or the marketing routes. Both start the render worker
in this process if it is not running yet (listing_reel.ensure_worker), so no lifespan wiring is required.
"""
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.core.auth_backend import current_active_user
from app.core.config import settings
from app.core.database import get_database
from app.models.user import User

from . import listing_reel
from .listing_reel import ReelJobError, ReelJobs, job_out

router = APIRouter()


class ReelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lang: Literal["en", "hi", "mr"] = "en"
    again: bool = False


def get_jobs() -> ReelJobs:
    from app.modules.ai_listing.llm import default_llm
    return ReelJobs(get_database(), Path(settings.upload_directory), llm_factory=default_llm)


def start_worker() -> None:
    listing_reel.ensure_worker()


def _http(e: ReelJobError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{listing_id}/reel", status_code=202)
async def make_reel(listing_id: str, request: Request, body: Optional[ReelIn] = None, user: User = Depends(current_active_user),
                    jobs: ReelJobs = Depends(get_jobs), _w: None = Depends(start_worker)):
    body = body or ReelIn()
    try:
        doc, created = await jobs.create(str(user.id), listing_id, body.lang, body.again)
    except ReelJobError as e:
        raise _http(e)
    return {"job": job_out(doc, str(request.base_url)), "created": created}


@router.get("/{listing_id}/reel")
async def get_reels(listing_id: str, request: Request, user: User = Depends(current_active_user),
                    jobs: ReelJobs = Depends(get_jobs), _w: None = Depends(start_worker)):
    try:
        latest = await jobs.latest(str(user.id), listing_id)
    except ReelJobError as e:
        raise _http(e)
    return {"jobs": {lang: job_out(d, str(request.base_url)) for lang, d in latest.items()}}
