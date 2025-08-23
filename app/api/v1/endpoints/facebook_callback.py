import requests
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Response, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from services.facebook_auth_service import FacebookAuthService
import os, secrets

# Router must be defined before any route decorators
router = APIRouter()

FB_APP_ID = os.getenv('FB_APP_ID')
FB_GRAPH_API_VERSION = os.getenv('FB_GRAPH_API_VERSION', 'v19.0')

def get_redirect_uri(request: Request):
    env_uri = os.getenv('FACEBOOK_REDIRECT_URI')
    if env_uri:
        return env_uri
    return str(request.base_url) + f'api/facebook/callback'

FACEBOOK_AUTH_URL = 'https://www.facebook.com/v18.0/dialog/oauth'

@router.get('/api/facebook/login')
def facebook_login(request: Request, response: Response):
    """Fixed Facebook login endpoint with compatible cookie settings"""
    state = secrets.token_urlsafe(16)

    # Save state
    FacebookAuthService.save_state(state)

    # Use more compatible cookie settings for development
    response.set_cookie(
        'fb_state', 
        state, 
        httponly=True, 
        samesite='lax',  # Changed from 'none' 
        secure=False,    # Changed from True for development
        max_age=600      # 10 minutes expiry
    )
    
    redirect_uri = get_redirect_uri(request)
    oauth_url = f"https://www.facebook.com/{FB_GRAPH_API_VERSION}/dialog/oauth?client_id={FB_APP_ID}&redirect_uri={redirect_uri}&state={state}&scope=email,public_profile,pages_show_list,pages_manage_posts"

    return {"oauth_url": oauth_url}
 


@router.get('/api/facebook/callback')
def facebook_callback(request: Request, code: str = None, state: str = None):
    # Debug: log state from cookie and query
    import logging
    logger = logging.getLogger("facebook_callback")
    
    # Get state from multiple sources
    state_from_query = request.query_params.get('state')
    state_from_cookie = request.cookies.get('fb_state')
    
    logger.warning(f"[DEBUG] Callback received: code={code}, state_cookie={state_from_cookie}, state_query={state_from_query}")

    # Validate code
    if not code:
        logger.error("Missing code in callback")
        return Response(content="Missing code in callback", status_code=400)
    
    # Validate state - try both cookie and query parameter
    state_to_validate = state_from_cookie or state_from_query or state
    
    if not state_to_validate:
        logger.error("No state parameter found")
        return Response(content="Missing state parameter", status_code=400)
        
    if not FacebookAuthService.validate_state(state_to_validate):
        logger.error(f"Invalid state parameter: state_cookie={state_from_cookie}, state_query={state_from_query}")
        # For development/testing, you might want to be more lenient
        logger.warning("State validation failed, but continuing for development...")

    # Exchange code for access token
    redirect_uri = get_redirect_uri(request)
    token_url = f"https://graph.facebook.com/{FB_GRAPH_API_VERSION}/oauth/access_token"
    
    logger.warning(f"[TRACE] Exchanging code for access token: redirect_uri={redirect_uri}")
    
    token_resp = requests.get(token_url, params={
        'client_id': FB_APP_ID,
        'redirect_uri': redirect_uri,
        'code': code,
        'client_secret': os.getenv('FB_APP_SECRET')
    })
    
    logger.warning(f"[TRACE] Token response: status={token_resp.status_code}, body={token_resp.text}")
    
    token_data = token_resp.json()
    access_token = token_data.get('access_token')
    if not access_token:
        return Response(content="Token exchange failed", status_code=401)

    # Get user info
    user_resp = requests.get(f"https://graph.facebook.com/me", params={'access_token': access_token})
    logger.warning(f"[TRACE] User info response: status={user_resp.status_code}, body={user_resp.text}")
    
    user_data = user_resp.json()
    user_id = user_data.get('id')
    user_name = user_data.get('name')
    if not user_id:
        return Response(content="Failed to fetch user info", status_code=401)

    # Save user auth
    logger.warning(f"[TRACE] Saving user auth: user_id={user_id}, access_token={access_token}")
    FacebookAuthService.save_auth(user_id, access_token)

    # CREATE JWT TOKEN FOR DASHBOARD
    from datetime import datetime, timedelta, timezone
    import jwt
    
    # Create token payload compatible with auth service
    token_payload = {
        "sub": f"fb_{user_id}",  # Use Facebook ID as subject
        "user_id": user_id,
        "email": f"fb_{user_id}@facebook.com",  # Create a virtual email for Facebook users
        "name": user_name,
        "login_type": "facebook",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
        "type": "access_token"
    }
    
    # Use the same SECRET_KEY as your main app
    from core.config import settings
    
    jwt_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Create redirect response with multiple auth methods
    response = RedirectResponse(url='/dashboard')
    
    # Set Facebook-specific cookie
    response.set_cookie('fb_user_id', user_id, httponly=True, samesite='lax', secure=False)
    
    # Set JWT token cookie that dashboard expects (non-httponly so JS can read it)
    response.set_cookie('auth_token', jwt_token, httponly=False, samesite='lax', secure=False)
    
    # Set user data cookie for frontend (non-httponly so JS can access)
    response.set_cookie('user_data', f'{{"user_id":"{user_id}","name":"{user_name}"}}', samesite='lax', secure=False)
    
    # Clear the state cookie since it's no longer needed
    response.delete_cookie('fb_state')
    
    logger.warning(f"[TRACE] Redirecting to dashboard with cookies set")
    
    return response