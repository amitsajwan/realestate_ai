"""
Facebook Endpoints
==================
Handles Facebook OAuth, page management, posting, and disconnect.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse

from typing import Optional

from app.dependencies import get_current_user, get_current_user_id
from app.services.facebook_service import FacebookService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError, AuthenticationError

import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8003")
FB_REDIRECT_URI = f"{BASE_URL}/api/v1/facebook/callback"


def get_facebook_service() -> FacebookService:
    user_repo = UserRepository()
    return FacebookService(user_repo)


@router.get("/config")
async def facebook_config(current_user=Depends(get_current_user)):
    """Get Facebook connection status and config."""
    try:
        facebook_service = get_facebook_service()
        config = await facebook_service.get_facebook_config(current_user.id)
        return config
    except Exception as e:
        logger.error(f"Facebook config error: {e}")
        return {"connected": False, "page_id": None, "page_name": None, "app_id": FB_APP_ID}


@router.get("/login")
async def facebook_login(token: str = Query(...)):
    """Initiate Facebook OAuth login flow."""
    if not FB_APP_ID or not FB_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook App not configured."
        )
    params = {
        "client_id": FB_APP_ID,
        "redirect_uri": FB_REDIRECT_URI,
        "state": token,
        "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,pages_manage_metadata,public_profile,email",
        "response_type": "code"
    }
    oauth_url = "https://www.facebook.com/v20.0/dialog/oauth?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(oauth_url)


@router.get("/callback")
async def facebook_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """Handle Facebook OAuth callback."""
    if error:
        return HTMLResponse(f"Facebook authentication failed: {error}")
    if not code or not state:
        return HTMLResponse("Missing code or state.", status_code=status.HTTP_400_BAD_REQUEST)
    
    facebook_service = get_facebook_service()
    return await facebook_service.handle_callback(code, state)


@router.get("/pages")
async def facebook_pages(current_user=Depends(get_current_user)):
    """Get Facebook pages accessible to the user."""
    facebook_service = get_facebook_service()
    try:
        pages = await facebook_service.get_user_pages(current_user.id)
        return pages
    except FacebookError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/select_page")
async def facebook_select_page(request: Request, current_user=Depends(get_current_user)):
    """Select Facebook page to post on."""
    data = await request.json()
    page_id = data.get("page_id")
    if not page_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing page_id")
    
    facebook_service = get_facebook_service()
    try:
        result = await facebook_service.select_page(current_user.id, page_id)
        return result
    except FacebookError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/post_property/{property_id}")
async def facebook_post_property(property_id: str, current_user=Depends(get_current_user)):
    """Post a specific property to the selected Facebook page."""
    facebook_service = get_facebook_service()
    try:
        result = await facebook_service.post_property(current_user.id, property_id)
        return result
    except FacebookError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/disconnect")
async def facebook_disconnect(current_user=Depends(get_current_user)):
    """Disconnect Facebook page from user account."""
    facebook_service = get_facebook_service()
    try:
        await facebook_service.disconnect(current_user.id)
        return {"status": "success", "message": "Facebook disconnected successfully."}
    except Exception as e:
        logger.error(f"Facebook disconnect error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disconnect Facebook.")


