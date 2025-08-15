from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
import requests
import secrets
import urllib.parse
from typing import List

from core.config import settings
from core.dependencies import get_current_user
from repositories.agent_repository import AgentRepository, get_agent_repository
from repositories.user_repository import UserRepository, get_user_repository

router = APIRouter()

@router.get("/connect")
async def initiate_facebook_connect(
    current_user: dict = Depends(get_current_user),
    agent_repo: AgentRepository = Depends(get_agent_repository)
):
    """Initiate Facebook OAuth flow for Page connection"""
    
    # Generate CSRF state
    state = secrets.token_urlsafe(32)
    
    # Store state with user_id
    await agent_repo.store_oauth_state(state, current_user["username"])
    
    # Facebook OAuth URL
    params = {
        "client_id": settings.FB_APP_ID,
        "redirect_uri": f"{settings.BASE_URL}/api/facebook/callback",
        "scope": "pages_show_list,pages_read_engagement,pages_manage_posts",
        "response_type": "code",
        "state": state
    }
    
    oauth_url = f"https://www.facebook.com/v{settings.FB_GRAPH_API_VERSION}/dialog/oauth?" + \
                urllib.parse.urlencode(params)
    
    return {"oauth_url": oauth_url, "state": state}

@router.get("/callback")
async def facebook_oauth_callback(
    code: str,
    state: str,
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Handle Facebook OAuth callback and connect Page"""
    
    # Verify state
    oauth_state = await agent_repo.verify_oauth_state(state)
    if not oauth_state:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    # Get user
    user = await user_repo.get_user(oauth_state.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    try:
        # Exchange code for access token
        token_response = requests.post("https://graph.facebook.com/v18.0/oauth/access_token", data={
            "client_id": settings.FB_APP_ID,
            "client_secret": settings.FB_APP_SECRET,
            "redirect_uri": f"{settings.BASE_URL}/api/facebook/callback",
            "code": code,
        }, timeout=30)
        
        token_data = token_response.json()
        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        user_access_token = token_data["access_token"]
        
        # Get user's Pages
        pages_response = requests.get(
            f"https://graph.facebook.com/v{settings.FB_GRAPH_API_VERSION}/me/accounts",
            params={
                "access_token": user_access_token,
                "fields": "id,name,access_token,category"
            },
            timeout=30
        )
        
        pages_data = pages_response.json()
        if "data" not in pages_data or not pages_data["data"]:
            raise HTTPException(status_code=400, detail="No Pages found for this account")
        
        # For now, connect the first Page (in production, let user choose)
        first_page = pages_data["data"][0]
        
        # Create or update agent profile
        profile = await agent_repo.get_agent_profile(user.id)
        if not profile:
            profile = await agent_repo.create_agent_profile(user.id, user.username)
        
        # Connect the Page
        await agent_repo.connect_facebook_page(user.id, first_page)
        
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?connected=true",
            status_code=302
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")

@router.get("/status")
async def facebook_connection_status(
    current_user: dict = Depends(get_current_user),
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get Facebook Page connection status"""
    
    user = await user_repo.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = await agent_repo.get_agent_profile(user.id)
    if not profile or not profile.connected_page:
        return {"connected": False, "page": None}
    
    return {
        "connected": True,
        "page": {
            "id": profile.connected_page.page_id,
            "name": profile.connected_page.name,
            "category": profile.connected_page.category,
            "connected_at": profile.connected_page.connected_at.isoformat()
        }
    }

@router.post("/disconnect")
async def disconnect_facebook_page(
    current_user: dict = Depends(get_current_user),
    agent_repo: AgentRepository = Depends(get_agent_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Disconnect Facebook Page"""
    
    user = await user_repo.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await agent_repo.update_agent_profile(user.id, {
        "connected_page": None,
        "facebook_url": None
    })
    
    return {"status": "disconnected"}
