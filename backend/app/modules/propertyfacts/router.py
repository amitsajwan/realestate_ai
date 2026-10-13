"""Property facts routes.

`public_router` (mounted at /api/v1/public, no auth): `GET /property-facts`, the verified facts we keep for a property, for its
listing page; by MahaRERA number, else by project + locality; 404 when we have none. `GET /property-facts/by-regno/{regno}`, the
same for a project's own page.
`router` (mounted at /api/v1/listings, bearer auth, owner only): `POST /{listing_id}/campaign` starts marketing a listing
(step 1 facts and page, then step 2 posts; see jobs.py), `GET /{listing_id}/campaign` its latest run,
`POST /{listing_id}/campaign/calendar` sends its posts to the approval calendar (schedule.py),
`GET /{listing_id}/campaign/results` each post's calendar state with its clicks and interests (results.py),
`PATCH /{listing_id}/campaign/posts/{angle}` saves an edited caption, `POST .../posts/{angle}/redo` remakes it with a note,
`POST /{listing_id}/campaign/boost` records that the agent boosted the master boost pair (boost.py) with its daily spend and days,
`POST /{listing_id}/campaign/boost/remake` makes only the boost pair again (in the background).
The builder's brochure (brochure.py), same auth, the agent's own listing only: `POST /{listing_id}/brochure` (multipart `file`)
reads it into a kit, `GET /{listing_id}/brochure` the kit (404 when none), `PATCH .../brochure/facts/{fact_id}` confirms, drops
or edits a fact, `POST .../brochure/registration` keeps the agent's "registered or exempt" answer, `GET .../pages/{n}.jpg` a
page's thumbnail, `PATCH .../brochure/images/{image_id}` uses or drops a plan, map or render kept from the brochure, and
`GET .../brochure/images/{image_id}.jpg` serves it."""
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import brochure, jobs
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


@public_router.get("/property-facts/by-regno/{regno}")
async def public_property_facts_by_regno(regno: str, response: Response, db=Depends(get_db)) -> dict:
    """The usable facts we keep for a MahaRERA project, for its own page (/projects/<slug>): every fact a campaign post may
    use, each block with its source (docs/plan/project-pages.md). 404 when no campaign gathered facts for it."""
    out = view(await FactsStore(db).find(regno.strip().upper()))
    if out is None:
        raise HTTPException(status_code=404, detail="No facts kept for this project")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


class EditIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    caption: str


class RedoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = ""


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    value: Any = None   # the chosen option's value, a typed MahaRERA number, or null for "not sure"


class BoostIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    daily_spend_inr: int
    days: int


class StartIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    again: bool = False
    language: Literal["en", "mr", "hi"] = "en"   # the posts' language (cards and captions)


def get_runs() -> jobs.MarketingRuns:
    return jobs.default_runs()


def start_worker() -> None:
    jobs.ensure_worker()


@router.post("/{listing_id}/campaign", status_code=202)
async def start_marketing(listing_id: str, request: Request, body: Optional[StartIn] = None,
                          user: User = Depends(current_active_user), runs: jobs.MarketingRuns = Depends(get_runs),
                          _w: None = Depends(start_worker)) -> dict:
    try:
        b = body or StartIn()
        doc, created = await runs.create(str(user.id), listing_id, b.again, b.language)
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


@router.get("/{listing_id}/campaign/results")
async def campaign_results(listing_id: str, user: User = Depends(current_active_user),
                           runs: jobs.MarketingRuns = Depends(get_runs), db=Depends(get_db)) -> dict:
    """Read only: each calendar row of the latest run (when, where, waiting/approved/posted) with its clicks and interests."""
    from .results import results
    try:
        doc = await runs.latest(str(user.id), listing_id)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    from .boost import results as boost_results
    items = await results(db, doc) if doc else []
    extra = await boost_results(db, doc, items, runs.now()) if doc else {
        "boost_results": {"clicks": 0, "interests": 0, "spend_inr": 0, "cost_per_enquiry": None}, "organic": {"clicks": 0, "interests": 0}}
    return {"items": items, **extra}


@router.post("/{listing_id}/campaign/boost")
async def mark_boosted(listing_id: str, body: BoostIn, request: Request, user: User = Depends(current_active_user),
                       runs: jobs.MarketingRuns = Depends(get_runs)) -> dict:
    """The agent boosted the pair on Meta: its daily spend and days are kept (state boosted) for the results."""
    try:
        doc = await runs.boost(str(user.id), listing_id, body.daily_spend_inr, body.days)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url))}


@router.post("/{listing_id}/campaign/boost/remake", status_code=202)
async def remake_boost(listing_id: str, request: Request, user: User = Depends(current_active_user),
                       runs: jobs.MarketingRuns = Depends(get_runs), _w: None = Depends(start_worker)) -> dict:
    """Make only the boost reel and carousel again; the worker does it (boost.state "making" until then)."""
    try:
        doc = await runs.remake_boost(str(user.id), listing_id)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url))}


@router.post("/{listing_id}/campaign/reels/remake", status_code=202)
async def remake_reels(listing_id: str, request: Request, user: User = Depends(current_active_user),
                       runs: jobs.MarketingRuns = Depends(get_runs), _w: None = Depends(start_worker)) -> dict:
    """Make only the ad reels again from the finished run's posts and pictures; the worker does it (reels_state "making")."""
    try:
        doc = await runs.remake_reels(str(user.id), listing_id)
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


@router.post("/{listing_id}/campaign/answer")
async def answer_question(listing_id: str, body: AnswerIn, request: Request, user: User = Depends(current_active_user),
                          runs: jobs.MarketingRuns = Depends(get_runs), _w: None = Depends(start_worker)) -> dict:
    """The agent's answer to one question the run asked (understand.py); the last answer lets the run make the posts."""
    try:
        doc = await runs.answer(str(user.id), listing_id, body.key, body.value)
    except jobs.RunError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"run": jobs.run_out(doc, str(request.base_url))}
# ---- the builder's brochure (brochure.py): read it, confirm its facts, answer the registration question ------------------
class FactStateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Literal["confirmed", "dropped", "pending"]
    value: Any = None


class ImageStateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Literal["confirmed", "dropped", "pending"]


class RegistrationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["registered", "exempt"]
    rera_no: Optional[str] = None


def get_brochures() -> brochure.Brochures:
    return brochure.default_brochures()


@router.post("/{listing_id}/brochure")
async def upload_brochure(listing_id: str, file: UploadFile = File(...), user: User = Depends(current_active_user),
                          kits: brochure.Brochures = Depends(get_brochures)) -> dict:
    """Read the builder's brochure (PDF, up to 40 pages and 30 MB) into the listing's kit of facts to confirm."""
    data = await file.read(brochure.MAX_BYTES + 1)
    try:
        doc = await kits.upload(str(user.id), listing_id, file.filename or "brochure.pdf", data)
    except brochure.BrochureError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return brochure.kit_out(doc)


@router.get("/{listing_id}/brochure")
async def get_brochure(listing_id: str, user: User = Depends(current_active_user),
                       kits: brochure.Brochures = Depends(get_brochures)) -> dict:
    try:
        return brochure.kit_out(await kits.get(str(user.id), listing_id))
    except brochure.BrochureError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.patch("/{listing_id}/brochure/facts/{fact_id}")
async def set_brochure_fact(listing_id: str, fact_id: str, body: FactStateIn, user: User = Depends(current_active_user),
                            kits: brochure.Brochures = Depends(get_brochures)) -> dict:
    """Confirm, drop or reopen one fact; a `value` replaces what was read (the page and quote stay, `edited` is set)."""
    try:
        doc = await kits.set_fact(str(user.id), listing_id, fact_id, body.state, body.value,
                                  has_value="value" in body.model_fields_set)
    except brochure.BrochureError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return brochure.kit_out(doc)


@router.post("/{listing_id}/brochure/registration")
async def answer_brochure_registration(listing_id: str, body: RegistrationIn, user: User = Depends(current_active_user),
                                       kits: brochure.Brochures = Depends(get_brochures)) -> dict:
    """The agent's answer to "registered on MahaRERA, or exempt?", kept on the kit."""
    try:
        doc = await kits.answer_registration(str(user.id), listing_id, body.status, body.rera_no)
    except brochure.BrochureError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return brochure.kit_out(doc)


@router.patch("/{listing_id}/brochure/images/{image_id}")
async def set_brochure_image(listing_id: str, image_id: str, body: ImageStateIn, user: User = Depends(current_active_user),
                             kits: brochure.Brochures = Depends(get_brochures)) -> dict:
    """Use (confirmed) or don't use (dropped) a floor plan, master plan, map or render kept from the brochure."""
    try:
        doc = await kits.set_image(str(user.id), listing_id, image_id, body.state)
    except brochure.BrochureError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return brochure.kit_out(doc)


@router.get("/{listing_id}/brochure/images/{image_id}.jpg")
async def brochure_image(listing_id: str, image_id: str, user: User = Depends(current_active_user),
                         kits: brochure.Brochures = Depends(get_brochures)) -> FileResponse:
    """A plan, map or render from the brochure (IMAGE_LONG_SIDE px), for the confirm screen."""
    try:
        path = await kits.image_file(str(user.id), listing_id, image_id)
    except brochure.BrochureError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, no-cache"})


@router.get("/{listing_id}/brochure/pages/{n}.jpg")
async def brochure_page(listing_id: str, n: int, user: User = Depends(current_active_user),
                        kits: brochure.Brochures = Depends(get_brochures)) -> FileResponse:
    """A page's thumbnail (pages count from 1), for the confirm screen."""
    try:
        path = await kits.page_image(str(user.id), listing_id, n)
    except brochure.BrochureError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, no-cache"})
