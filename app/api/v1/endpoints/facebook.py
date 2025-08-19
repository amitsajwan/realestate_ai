from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse

from app.dependencies import get_current_user, get_current_user_id
from app.services.facebook_service import FacebookService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError

import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_facebook_service() -> FacebookService:
    user_repo = UserRepository()
    return FacebookService(user_repo)

@router.get("/config")
async def get_facebook_config(
    current_user = Depends(get_current_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Get Facebook connection status and config"""
    try:
        config = await facebook_service.get_facebook_config(current_user.id)
        return config
    except Exception as e:
        logger.error(f"Facebook config error: {e}")
        return {
            "connected": False,
            "page_id": None,
            "page_name": None,
            "error": "Failed to get Facebook config"
        }

@router.get("/login")
async def facebook_login_redirect(
    current_user = Depends(get_current_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Initiate Facebook OAuth flow"""
    try:
        oauth_url = await facebook_service.get_oauth_url(current_user.id)
        return RedirectResponse(oauth_url)
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/callback")
async def facebook_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Handle Facebook OAuth callback"""
    if error:
        return HTMLResponse(
            f"<h2>Facebook Authentication Error</h2><p>{error}</p>",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    return await facebook_service.handle_callback(code, state)

@router.get("/pages")
async def get_facebook_pages(
    current_user = Depends(get_current_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Get user's Facebook pages"""
    try:
        pages = await facebook_service.get_user_pages(current_user.id)
        return {"pages": pages}
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/select-page")
async def select_facebook_page(
    page_data: dict,
    current_user = Depends(get_current_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Select a Facebook page for posting"""
    page_id = page_data.get("page_id")
    if not page_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page_id is required"
        )
    
    try:
        result = await facebook_service.select_page(current_user.id, page_id)
        return result
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/post-property/{property_id}")
async def post_property_to_facebook(
    property_id: str,
    current_user = Depends(get_current_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Post a property to Facebook"""
    try:
        result = await facebook_service.post_property(current_user.id, property_id)
        return result
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/disconnect")
async def disconnect_facebook(
    current_user = Depends(get_current_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Disconnect Facebook account"""
    try:
        await facebook_service.disconnect(current_user.id)
        return {"message": "Facebook disconnected successfully"}
    except Exception as e:
        logger.error(f"Facebook disconnect error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Facebook"
        )
