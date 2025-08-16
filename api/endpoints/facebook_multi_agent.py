"""
Updated Facebook OAuth endpoint with multi-agent support
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from typing import Dict, Optional
import secrets
import urllib.parse

from core.multi_agent_config import get_facebook_config, get_agent_settings
from repositories.user_repository import get_user_repository, UserRepository
from core.dependencies import get_current_user

router = APIRouter()

# In-memory state storage for OAuth (in production, use Redis)
oauth_states: Dict[str, Dict] = {}

@router.get("/config/{agent_id}")
async def facebook_config_for_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get Facebook configuration for a specific agent"""
    
    # Get agent-specific Facebook config
    fb_config = get_facebook_config(agent_id)
    
    if not fb_config.get("fb_app_id"):
        raise HTTPException(
            status_code=404, 
            detail=f"No Facebook configuration found for agent: {agent_id}"
        )
    
    # Check if user already has Facebook token for this agent
    user_data = await user_repo.get_user_by_id(current_user["sub"])
    facebook_pages = user_data.get("facebook_pages", {}).get(agent_id, [])
    
    return {
        "app_id": fb_config["fb_app_id"],
        "is_connected": len(facebook_pages) > 0,
        "pages": facebook_pages,
        "agent_info": {
            "agent_id": agent_id,
            "agent_name": get_agent_settings(agent_id).agent_name if get_agent_settings(agent_id) else agent_id
        }
    }

@router.get("/connect/{agent_id}")
async def facebook_connect_for_agent(
    agent_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Initiate Facebook OAuth for a specific agent"""
    
    # Get agent-specific Facebook config
    fb_config = get_facebook_config(agent_id)
    
    if not fb_config.get("fb_app_id") or not fb_config.get("fb_app_secret"):
        raise HTTPException(
            status_code=400,
            detail=f"Facebook app not configured for agent: {agent_id}"
        )
    
    # Generate OAuth state with agent context
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": current_user["sub"],
        "agent_id": agent_id,
        "redirect_uri": f"{request.base_url}api/facebook/callback"
    }
    
    # Build Facebook OAuth URL with agent-specific app ID
    facebook_oauth_url = (
        f"https://www.facebook.com/v{fb_config['fb_graph_api_version']}/dialog/oauth"
        f"?client_id={fb_config['fb_app_id']}"
        f"&redirect_uri={urllib.parse.quote(f'{request.base_url}api/facebook/callback')}"
        f"&scope=pages_show_list,pages_manage_posts,pages_read_engagement"
        f"&state={state}"
    )
    
    return RedirectResponse(url=facebook_oauth_url)

@router.get("/callback")
async def facebook_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Handle Facebook OAuth callback with multi-agent support"""
    
    if error:
        raise HTTPException(status_code=400, detail=f"Facebook OAuth error: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")
    
    # Retrieve OAuth state
    oauth_data = oauth_states.pop(state, None)
    if not oauth_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    
    agent_id = oauth_data["agent_id"]
    user_id = oauth_data["user_id"]
    
    # Get agent-specific Facebook config
    fb_config = get_facebook_config(agent_id)
    
    try:
        # Exchange code for access token using agent's app credentials
        import httpx
        
        token_url = f"https://graph.facebook.com/v{fb_config['fb_graph_api_version']}/oauth/access_token"
        token_data = {
            "client_id": fb_config["fb_app_id"],
            "client_secret": fb_config["fb_app_secret"],
            "redirect_uri": f"{request.base_url}api/facebook/callback",
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=token_data)
            token_response = response.json()
            
            if "access_token" not in token_response:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to get access token: {token_response}"
                )
            
            access_token = token_response["access_token"]
            
            # Get user's Facebook pages
            pages_url = f"https://graph.facebook.com/v{fb_config['fb_graph_api_version']}/me/accounts"
            pages_response = await client.get(
                pages_url, 
                params={"access_token": access_token}
            )
            pages_data = pages_response.json()
            
            if "data" not in pages_data:
                raise HTTPException(
                    status_code=400, 
                    detail="Failed to retrieve Facebook pages"
                )
            
            # Store Facebook integration data with agent context
            facebook_pages = [
                {
                    "id": page["id"],
                    "name": page["name"],
                    "access_token": page["access_token"],
                    "agent_id": agent_id
                }
                for page in pages_data["data"]
            ]
            
            # Update user with agent-specific Facebook data
            await user_repo.update_facebook_integration(
                user_id, 
                facebook_pages, 
                agent_id=agent_id
            )
            
        # Redirect back to agent-specific dashboard
        dashboard_url = f"/agents/{agent_id}/dashboard" if agent_id != "default" else "/dashboard"
        return RedirectResponse(url=dashboard_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Facebook integration failed: {str(e)}"
        )

@router.post("/post/{agent_id}")
async def post_to_facebook_for_agent(
    agent_id: str,
    post_data: dict,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Post content to Facebook for a specific agent"""
    
    # Get user's Facebook pages for this agent
    user_data = await user_repo.get_user_by_id(current_user["sub"])
    agent_facebook_pages = user_data.get("facebook_pages", {}).get(agent_id, [])
    
    if not agent_facebook_pages:
        raise HTTPException(
            status_code=400, 
            detail=f"No Facebook pages connected for agent: {agent_id}"
        )
    
    # Get the selected page (or use first available)
    page_id = post_data.get("page_id")
    selected_page = None
    
    for page in agent_facebook_pages:
        if page["id"] == page_id:
            selected_page = page
            break
    
    if not selected_page:
        selected_page = agent_facebook_pages[0]  # Use first page as default
    
    # Get agent settings for personalization
    agent_settings = get_agent_settings(agent_id)
    agent_name = agent_settings.agent_name if agent_settings else agent_id
    
    try:
        import httpx
        
        # Get Facebook config for API version
        fb_config = get_facebook_config(agent_id)
        
        # Post to Facebook
        post_url = f"https://graph.facebook.com/v{fb_config['fb_graph_api_version']}/{selected_page['id']}/feed"
        
        # Customize message with agent branding
        message = post_data.get("message", "")
        if agent_settings and agent_settings.agent_brand:
            message += f"\n\n- {agent_settings.agent_brand}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                post_url,
                data={
                    "message": message,
                    "access_token": selected_page["access_token"]
                }
            )
            
            result = response.json()
            
            if "id" in result:
                return {
                    "success": True,
                    "post_id": result["id"],
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "page_name": selected_page["name"]
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Facebook API error: {result}"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post to Facebook: {str(e)}"
        )
