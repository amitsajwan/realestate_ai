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
    """Fixed Facebook login endpoint - removed db dependency since save_state doesn't use it"""
    state = secrets.token_urlsafe(16)

    # Fix: Call save_state with only the state parameter
    FacebookAuthService.save_state(state)

    response.set_cookie('fb_state', state, httponly=True, samesite='none', secure=True)
    redirect_uri = get_redirect_uri(request)
    oauth_url = f"https://www.facebook.com/{FB_GRAPH_API_VERSION}/dialog/oauth?client_id={FB_APP_ID}&redirect_uri={redirect_uri}&state={state}&scope=email,public_profile,pages_show_list,pages_manage_posts"

    return {"oauth_url": oauth_url}

@router.get('/api/facebook/callback')
def facebook_callback(request: Request, code: str = None, state: str = Cookie(None)):
    # Debug: log state from cookie and query
    import logging
    logger = logging.getLogger("facebook_callback")
    logger.warning(f"[DEBUG] Callback received: code={code}, state_cookie={state}, state_query={request.query_params.get('state')}")

    # Validate state
    if not code:
        logger.error("Missing code in callback")
        return Response(content="Missing code in callback", status_code=400)
    if not state or not FacebookAuthService.validate_state(state):
        logger.error(f"Invalid state parameter: state_cookie={state}, state_query={request.query_params.get('state')}")
        return Response(content="Invalid state parameter (possible CSRF or expired session)", status_code=400)

    # Exchange code for access token
    redirect_uri = get_redirect_uri(request)
    token_url = f"https://graph.facebook.com/{FB_GRAPH_API_VERSION}/oauth/access_token"
    token_resp = requests.get(token_url, params={
        'client_id': FB_APP_ID,
        'redirect_uri': redirect_uri,
        'code': code,
        'client_secret': os.getenv('FB_APP_SECRET')
    })
    token_data = token_resp.json()
    access_token = token_data.get('access_token')
    if not access_token:
        return Response(content="Token exchange failed", status_code=401)

    # Get user info
    user_resp = requests.get(f"https://graph.facebook.com/me", params={'access_token': access_token})
    user_data = user_resp.json()
    user_id = user_data.get('id')
    if not user_id:
        return Response(content="Failed to fetch user info", status_code=401)

    # Save user auth
    FacebookAuthService.save_auth(user_id, access_token)

    # Set user_id cookie and redirect to dashboard
    response = RedirectResponse(url='/dashboard')
    response.set_cookie('fb_user_id', user_id, httponly=True, samesite='none', secure=True)
    return response
