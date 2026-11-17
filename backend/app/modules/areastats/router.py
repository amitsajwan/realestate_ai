"""`GET /public/areas/{slug}/stats` (mounted at /api/v1/public, no auth): one area's MahaRERA facts for its locality page.

404 for an area we do not cover. Short public caching: the numbers change a few times a day at most."""
from datetime import datetime
from typing import Any, Callable, Dict

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.newsroom.store import Store

from .pages import date_moves
from .service import CACHE_SECONDS, IST, SOURCE, all_area_stats, area_stats

public_router = APIRouter()
router = APIRouter()   # Studio: mounted at /area-pictures, owner-only (approve/refuse the AI judge's picks)


def get_db():
    return get_database()


@public_router.get("/areas/stats")
async def public_all_area_stats(response: Response, db=Depends(get_db)) -> dict:
    """Every area we cover, in menu order: the Pune MahaRERA tracker page (frontend/app/pune-maharera-tracker)."""
    areas = await all_area_stats(db)
    # each area's possession dates that moved, for the tracker's report (pages.date_moves), from the shared load public pages read
    docs = await Store(db).shared_projects()
    today = datetime.now(IST).date()
    for a in areas:
        a["date_moves"] = date_moves([d for d in docs if d.get("locality") == a["area"]["key"]], today)
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return {"as_of": max((a["as_of"] for a in areas), default=None), "areas": areas, "source": SOURCE}


@public_router.get("/areas/{slug}/stats")
async def public_area_stats(slug: str, response: Response, db=Depends(get_db)) -> dict:
    out = await area_stats(db, slug)
    if out is None:
        raise HTTPException(status_code=404, detail="Unknown area")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


# ---- our own project pages (docs/plan/project-pages.md) -------------------------------------------------------------------
from typing import Optional  # noqa: E402

from . import pages  # noqa: E402


@public_router.get("/register/projects/{slug}")
async def public_project_page(slug: str, response: Response, db=Depends(get_db)) -> dict:
    out = await pages.project_page(db, slug)
    if out is None:
        raise HTTPException(status_code=404, detail="Unknown project")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


@public_router.get("/register/by-regno/{regno}")
async def public_project_by_regno(regno: str, db=Depends(get_db)) -> dict:
    out = await pages.page_for(db, regno)
    if out is None:
        raise HTTPException(status_code=404, detail="Not in the register")
    return {k: out[k] for k in ("slug", "path", "indexable")}


@public_router.get("/register/web-facts/{regno}")
async def public_web_facts(regno: str, response: Response, db=Depends(get_db)) -> dict:
    """What the builder's site and the sites ranking for the project say, checked (areastats.webfacts): for agent-listed pages."""
    out = await pages.web_facts_for(db, regno)
    if out is None:
        raise HTTPException(status_code=404, detail="No web facts")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


@public_router.get("/register/profile/{regno}")
async def public_profile(regno: str, response: Response, db=Depends(get_db)) -> dict:
    """Highlights, the builder's pictures and floor plans (areastats.profile): for agent-listed pages."""
    out = await pages.profile_for(db, regno)
    if out is None:
        raise HTTPException(status_code=404, detail="No profile")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


@public_router.get("/register/projects")
async def public_project_list(response: Response, area: Optional[str] = None, all: bool = False, limit: int = 2000,
                              place: Optional[str] = None, db=Depends(get_db)) -> list:
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await pages.listing(db, area=area, only_indexable=not all, limit=max(1, min(limit, 20000)), place=place)


@public_router.get("/register/search")
async def public_project_search(response: Response, q: str = "", limit: int = 20, db=Depends(get_db)) -> list:
    """Projects by what a buyer typed: {slug, name, marketed_name, regno, promoter, area, place_name, completion_now, units_total,
    units_booked, checked, checks_total, active, months_later}, best match first."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await pages.search(db, q, limit=max(1, min(limit, 50)))


@public_router.get("/register/places")
async def public_places(response: Response, db=Depends(get_db)) -> list:
    """Every Pune place with projects in the register: {key, slug, name, zone, projects, indexable}, in zone order."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await pages.places(db)


# ---- internal links and builder pages (docs/plan/rank-loop.md R5, R6) -------------------------------------------------------
from . import areamap, hubs, landmarks  # noqa: E402


@public_router.get("/register/active")
async def public_active(response: Response, area: Optional[str] = None, place: Optional[str] = None, limit: int = hubs.ACTIVE,
                        db=Depends(get_db)) -> list:
    """"Most active projects" for an area (key or slug) or a Pune place: [{slug, name, fact, source}]; never a score."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await hubs.active(db, area=area, place=place, limit=max(1, min(limit, 20)))


@public_router.get("/register/map")
async def public_area_map(area: str, response: Response, db=Depends(get_db)) -> dict:
    """An area's most active projects on its street map (areamap.py): only checked positions, homes only. 404: no map yet."""
    out = await areamap.public(db, area)
    if out is None:
        raise HTTPException(status_code=404, detail="No map for this area")
    # the landmarks and metro stations inside the map's frame, drawn as small icons apart from the numbered pins
    out["landmarks"] = landmarks.on_map(tuple(out["box"]))
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


@public_router.get("/areas/{slug}/landmarks")
async def public_area_landmarks(slug: str, response: Response) -> dict:
    """"Landmarks near <area>": the nearest metro stations and the places buyers know, with straight-line distances from the
    middle of the area (landmarks.py). 404 for an area we do not cover. Hand-checked data, so it can be cached as long as the
    other public answers."""
    out = landmarks.public(slug)
    if out is None:
        raise HTTPException(status_code=404, detail="Unknown area")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


@public_router.get("/register/near/{area_slug}/{slug}")
async def public_near_guide(area_slug: str, slug: str, response: Response, db=Depends(get_db)) -> list:
    """Project pages near a neighbourhood guide: [{slug, name, km, fact, source}], nearest first."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await hubs.near_projects(db, area_slug, slug)


@public_router.get("/builders")
async def public_builders(response: Response, all: bool = False, db=Depends(get_db)) -> list:
    """Builders with a page: [{slug, name, projects, indexable, page_updated}] (the sitemap, the builders index)."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await hubs.builders(db, only_indexable=not all)


@public_router.get("/builders/{slug}")
async def public_builder(slug: str, response: Response, db=Depends(get_db)) -> dict:
    out = await hubs.builder_page(db, slug)
    if out is None:
        raise HTTPException(status_code=404, detail="Unknown builder")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


# ---- the hot projects banner on every public page (spotlight.py) -------------------------------------------------------------
from . import spotlight  # noqa: E402


@public_router.get("/register/spotlight")
async def public_spotlight(response: Response, area: Optional[str] = None, db=Depends(get_db)) -> list:
    """The banner for a page (on an area's pages, that area first): [{slug, name, area, area_slug, note, fact, source, picked}]."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await spotlight.public(db, area=area)


# ---- an upcoming project MahaRERA has not registered yet (upcoming.py): its own noindex page --------------------------------------
from . import upcoming  # noqa: E402


@public_router.get("/register/upcoming")
async def public_upcoming_list(response: Response, db=Depends(get_db)) -> list:
    """The coming-soon band and /projects/upcoming: builder, place and home types of each live project, nothing more."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await upcoming.briefs(db)


@public_router.get("/register/upcoming/{slug}")
async def public_upcoming(slug: str, response: Response, db=Depends(get_db)) -> dict:
    """An upcoming project's page: facts with their sources, no prices, and its builder's registered projects; 404 unless it is live."""
    u = await upcoming.get(db, slug)
    if not u:
        raise HTTPException(status_code=404, detail="Upcoming project not found")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return {**u, "builder_projects": await upcoming.builder_projects(db, u)}


# ---- the area from above (pictures.py), the owner's first-pair review and the public then-and-now pair ---------------------
from app.core.areas import get as areas_get  # noqa: E402

from . import pictures  # noqa: E402

_hooks: Dict[str, Any] = {"is_operator": lambda user: False}


def configure(is_operator: Callable[[User], bool]) -> None:
    _hooks["is_operator"] = is_operator


def is_admin(user: User) -> bool:
    return bool(getattr(user, "is_superuser", False)) or bool(_hooks["is_operator"](user))


async def owner_only(user: User = Depends(current_active_user)) -> User:
    if is_admin(user):
        return user
    raise HTTPException(403, "Only the owner can approve or refuse an area picture")


def get_pictures() -> pictures.AreaPictures:
    return pictures.AreaPictures(get_database())


class DecideIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    live: bool


@public_router.get("/areas/{slug}/pictures")
async def public_area_pictures(slug: str, response: Response, svc: pictures.AreaPictures = Depends(get_pictures)) -> dict:
    """The area's live then-and-now pair (or more): {area, pictures: [{year, captured_on, src, width, height, credit}]}."""
    out = await svc.public(slug)
    if out is None:
        raise HTTPException(status_code=404, detail="Unknown area")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


@router.get("")
async def list_pictures(area: str, user: User = Depends(owner_only), svc: pictures.AreaPictures = Depends(get_pictures)) -> dict:
    a = areas_get(area)
    if a is None:
        raise HTTPException(404, "Unknown area")
    docs = await svc.list_area(a.key)
    return {"area": {"key": a.key, "name": a.name, "slug": a.slug}, "trusted": await svc.trusted(),
            "items": [pictures.studio_view(d) for d in docs]}


@router.post("/{pid}/decide")
async def decide_picture(pid: str, body: DecideIn, user: User = Depends(owner_only),
                         svc: pictures.AreaPictures = Depends(get_pictures)) -> dict:
    try:
        d = await svc.decide(pid, body.live, str(user.id))
    except ValueError as e:
        raise HTTPException(404, str(e))
    return pictures.studio_view(d)
