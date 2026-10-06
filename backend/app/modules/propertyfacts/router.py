"""Property facts routes.

`public_router` (mounted at /api/v1/public, no auth): `GET /property-facts`, the verified facts we keep for a property, for its
listing page; by MahaRERA number, else by project + locality; 404 when we have none.
`router` (mounted at /api/v1/listings, bearer auth, owner only): `POST /{listing_id}/campaign` starts marketing a listing
(step 1 facts and page, then step 2 posts; see jobs.py), `GET /{listing_id}/campaign` its latest run,
`POST /{listing_id}/campaign/calendar` sends its posts to the approval calendar (schedule.py),
`PATCH /{listing_id}/campaign/posts/{angle}` saves an edited caption, `POST .../posts/{angle}/redo` remakes it with a note."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import jobs

from .public import view
from .store import FactsStore

CACHE_SECONDS = 600
public_router = APIRouter()
router = APIRouter()


def get_db():
    return get_database()


@public_router.get("/property-facts")
async def public_property_facts(response: Response, rera: Optional[str] = None, project: Optional[str] = None,
                                locality: Optional[str] = None, db=Depends(get_db)) -> dict:
    out = view(await FactsStore(db).find(rera or "", project or "", locality or ""))
    if out is None:
        raise HTTPException(status_code=404, detail="No facts kept for this property")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


class EditIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    caption: str


class RedoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = ""


class StartIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    again: bool = False


def get_runs() -> jobs.MarketingRuns:
    return jobs.default_runs()


def start_worker() -> None:
    jobs.ensure_worker()


@router.post("/{listing_id}/campaign", status_code=202)
async def start_marketing(listing_id: str, request: Request, body: Optional[StartIn] = None,
                          user: User = Depends(current_active_user), runs: jobs.MarketingRuns = Depends(get_runs),
                          _w: None = Depends(start_worker)) -> dict:
    try:
        doc, created = await runs.create(str(user.id), listing_id, (body or StartIn()).again)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url)), "created": created}


@router.get("/{listing_id}/campaign")
async def get_marketing_run(listing_id: str, request: Request, user: User = Depends(current_active_user),
                            runs: jobs.MarketingRuns = Depends(get_runs), _w: None = Depends(start_worker)) -> dict:
    try:
        doc = await runs.latest(str(user.id), listing_id)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url))}


@router.post("/{listing_id}/campaign/calendar")
async def send_to_calendar(listing_id: str, request: Request, user: User = Depends(current_active_user),
                           runs: jobs.MarketingRuns = Depends(get_runs)) -> dict:
    """The finished run's posts become planned rows in the approval calendar (one a day, Instagram and Facebook)."""
    try:
        doc = await runs.to_calendar(str(user.id), listing_id)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url))}


@router.patch("/{listing_id}/campaign/posts/{angle}")
async def edit_post(listing_id: str, angle: str, body: EditIn, request: Request, user: User = Depends(current_active_user),
                    runs: jobs.MarketingRuns = Depends(get_runs)) -> dict:
    """Save the agent's caption for one post; `problems` are the checks' warnings (the text is kept as written)."""
    try:
        doc, problems = await runs.edit_post(str(user.id), listing_id, angle, body.caption)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url)), "problems": problems, "synced": doc.get("synced", 0)}


@router.post("/{listing_id}/campaign/posts/{angle}/redo")
async def redo_post(listing_id: str, angle: str, body: RedoIn, request: Request, user: User = Depends(current_active_user),
                    runs: jobs.MarketingRuns = Depends(get_runs)) -> dict:
    """Make one post again with the agent's note, from the kept facts, under every check."""
    try:
        doc = await runs.redo_post(str(user.id), listing_id, angle, body.note)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url)), "synced": doc.get("synced", 0)}
