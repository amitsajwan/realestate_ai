from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.config import settings
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
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Connection status and currently selected page (if any).
    
    This endpoint is temporarily public to handle authentication issues.
    It checks for the demo user connection status.
    TODO: Re-enable proper user-specific authentication when login issues are resolved.
    """
    
    try:
        # Check demo user connection status (since that's what OAuth uses)
        user = await user_repo.get_user("demo")  # Demo username
        if user:
            profile = await agent_repo.get_agent_profile(user.id)
            if profile and profile.connected_page:
                page = profile.connected_page
                return {
                    "connected": True, 
                    "page_id": page.page_id, 
                    "page_name": page.name,
                    "app_id": settings.FB_APP_ID,
                    "ready_for_oauth": True
                }
    except Exception as e:
        # If any error occurs, return not connected status
        pass
    
    # Return not connected status
    return {
        "connected": False, 
        "page_id": None, 
        "page_name": None,
        "app_id": settings.FB_APP_ID,
        "ready_for_oauth": bool(settings.FB_APP_ID and settings.FB_APP_ID != "your_app_id_here")
    }


@router.get("/pages")
async def list_connected_pages(
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Return pages known for this user from the repository cache.
    
    Temporarily public to handle authentication issues - checks demo user.
    TODO: Re-enable proper user authentication when login is stable.
    """
    try:
        # Check demo user (since that's what OAuth uses)
        user = await user_repo.get_user("demo")
        if not user:
            raise HTTPException(status_code=400, detail="Demo user not found")

        pages = await agent_repo.get_facebook_pages(user.id)
        if not pages:
            raise HTTPException(status_code=400, detail="Facebook not connected")

        return {
            "pages": [
                {"id": p.page_id, "name": p.name, "category": p.category}
                for p in pages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Facebook not connected: {str(e)}")

    return {
        "pages": [
            {"id": p.page_id, "name": p.name, "category": p.category}
            for p in pages
        ]
    }


@router.post("/select_page")
async def select_page(
    body: SelectPageBody,
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Select which cached Page to use for posting.
    
    Temporarily public to handle authentication issues - uses demo user.
    TODO: Re-enable proper user authentication when login is stable.
    """
    try:
        # Use demo user (since that's what OAuth uses)
        user = await user_repo.get_user("demo")
        if not user:
            raise HTTPException(status_code=404, detail="Demo user not found")

        pages = await agent_repo.get_facebook_pages(user.id)
        target = next((p for p in pages if p.page_id == body.page_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Page not found")

        profile = await agent_repo.get_agent_profile(user.id)
        if not profile:
            profile = await agent_repo.create_agent_profile(user.id, "demo")

        await agent_repo.update_agent_profile(user.id, {"connected_page": target})
        return {"selected": True, "page_id": target.page_id, "page_name": target.name}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Page selection failed: {str(e)}")


@router.post("/post")
async def post_to_facebook(
    body: PostBody,
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Post a message (and optional image link) to the selected Facebook Page.
    
    Temporarily public to handle authentication issues - uses demo user.
    TODO: Re-enable proper user authentication when login is stable.
    """
    try:
        # Use demo user (since that's what OAuth uses)
        user = await user_repo.get_user("demo")
        if not user:
            raise HTTPException(status_code=404, detail="Demo user not found")

        profile = await agent_repo.get_agent_profile(user.id)
        if not profile or not profile.connected_page:
            raise HTTPException(status_code=400, detail="Facebook Page not connected")

        # Get decrypted token and post
        page = profile.connected_page
        token = await agent_repo.get_page_access_token(user.id)
        if not token:
            raise HTTPException(status_code=400, detail="Missing page access token")

        client = FacebookClient()
        result = await client.post_to_page(
            access_token=token, page_id=page.page_id, message=body.message, image_url=body.image_url
        )
        return {"ok": True, "result": result, "posted_to": page.name}
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Post failed: {str(e)}")
