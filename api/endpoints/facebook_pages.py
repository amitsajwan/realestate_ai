from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_user
from repositories.agent_repository import AgentRepository, get_agent_repository
from repositories.user_repository import UserRepository, get_user_repository
from services.facebook_client import FacebookClient


router = APIRouter()


class SelectPageBody(BaseModel):
    page_id: str


class PostBody(BaseModel):
    message: str
    image_url: str | None = None


@router.get("/config")
async def get_facebook_config(
    current_user: dict = Depends(get_current_user),
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Connection status and currently selected page (if any)."""
    user = await user_repo.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await agent_repo.get_agent_profile(user.id)
    if not profile or not profile.connected_page:
        return {"connected": False, "page_id": None, "page_name": None}

    page = profile.connected_page
    return {"connected": True, "page_id": page.page_id, "page_name": page.name}


@router.get("/pages")
async def list_connected_pages(
    current_user: dict = Depends(get_current_user),
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Return pages known for this user from the repository cache.

    If the user hasn't completed OAuth yet, return 400 to indicate not connected.
    """
    user = await user_repo.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pages = await agent_repo.get_facebook_pages(user.id)
    if not pages:
        raise HTTPException(status_code=400, detail="Facebook not connected")

    return {
        "pages": [
            {"id": p.page_id, "name": p.name, "category": p.category}
            for p in pages
        ]
    }


@router.post("/select_page")
async def select_page(
    body: SelectPageBody,
    current_user: dict = Depends(get_current_user),
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Select which cached Page to use for posting."""
    user = await user_repo.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pages = await agent_repo.get_facebook_pages(user.id)
    target = next((p for p in pages if p.page_id == body.page_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Page not found")

    profile = await agent_repo.get_agent_profile(user.id)
    if not profile:
        profile = await agent_repo.create_agent_profile(user.id, user.username)

    await agent_repo.update_agent_profile(user.id, {"connected_page": target})
    return {"selected": True, "page_id": target.page_id, "page_name": target.name}


@router.post("/post")
async def post_to_facebook(
    body: PostBody,
    current_user: dict = Depends(get_current_user),
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Post a message (and optional image link) to the selected Facebook Page."""
    user = await user_repo.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await agent_repo.get_agent_profile(user.id)
    if not profile or not profile.connected_page:
        raise HTTPException(status_code=400, detail="Facebook Page not connected")

    # Decrypt token and post
    page = profile.connected_page
    token = await agent_repo.get_page_access_token(user.id)
    if not token:
        raise HTTPException(status_code=400, detail="Missing page access token")

    client = FacebookClient()
    try:
        result = await client.post_to_page(
            access_token=token, page_id=page.page_id, message=body.message, image_url=body.image_url
        )
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
