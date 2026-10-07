"""Project routes. `router` is mounted at /agentprojects (bearer auth, owner only), `public_router` at /public (no auth).

Owner: PUT /agents/{agent_id}/projects/{slug}, GET /agents/{agent_id}/projects, POST /agents/{agent_id}/projects/{slug}/check.
Public: GET /agents/{agent_slug}/projects, GET /agents/{agent_slug}/projects/{slug}.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_database
from app.models.user import User
from app.modules.concierge.router import owner_only, writer

from .schemas import SLUG, CatalogPage, CatalogProject, OwnerProject, ProjectIn, PublicProject, PublicProjectPage
from .service import ProjectError, ProjectService

router = APIRouter()
public_router = APIRouter()


def get_service() -> ProjectService:
    return ProjectService(get_database())


def _http(e: ProjectError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


def _slug(slug: str) -> str:
    if not SLUG.match(slug):
        raise HTTPException(422, "slug must be lowercase words joined by '-'")
    return slug


@router.put("/agents/{agent_id}/projects/{slug}", response_model=OwnerProject)
async def upsert_project(agent_id: str, slug: str, body: ProjectIn, user: User = Depends(writer("write", 60)),
                         svc: ProjectService = Depends(get_service)):
    try:
        return await svc.upsert(agent_id, _slug(slug), body)
    except ProjectError as e:
        raise _http(e)


@router.get("/agents/{agent_id}/projects")
async def list_projects(agent_id: str, user: User = Depends(owner_only), svc: ProjectService = Depends(get_service)):
    return {"items": [p.model_dump(mode="json") for p in await svc.list_for_owner(agent_id)]}


@router.post("/agents/{agent_id}/projects/{slug}/check", response_model=OwnerProject)
async def check_project(agent_id: str, slug: str, user: User = Depends(writer("check", 30)),
                        svc: ProjectService = Depends(get_service)):
    try:
        return await svc.check_maharera(agent_id, _slug(slug))
    except ProjectError as e:
        raise _http(e)


@public_router.get("/projects", response_model=CatalogPage)
async def catalog(locality: str = "", svc: ProjectService = Depends(get_service)):
    """Avasetu's shared project pages: one per MahaRERA registration, with the agents who handle it."""
    items = await svc.catalog(locality or None)
    return CatalogPage(items=items, total=len(items))


@public_router.get("/projects/{slug}", response_model=CatalogProject)
async def catalog_project(slug: str, svc: ProjectService = Depends(get_service)):
    try:
        return await svc.catalog_get(_slug(slug))
    except ProjectError as e:
        raise _http(e)


@public_router.get("/sitemap/projects")
async def sitemap_projects(svc: ProjectService = Depends(get_service)):
    """Indexable project pages, for the website's sitemap.xml."""
    return {"items": await svc.sitemap_entries()}


@public_router.get("/agents/{agent_slug}/projects", response_model=PublicProjectPage)
async def public_projects(agent_slug: str, svc: ProjectService = Depends(get_service)):
    try:
        items = await svc.public_list(agent_slug)
    except ProjectError as e:
        raise _http(e)
    return PublicProjectPage(items=items, total=len(items))


@public_router.get("/agents/{agent_slug}/projects/{slug}", response_model=PublicProject)
async def public_project(agent_slug: str, slug: str, svc: ProjectService = Depends(get_service)):
    try:
        return await svc.public_get(agent_slug, slug)
    except ProjectError as e:
        raise _http(e)
