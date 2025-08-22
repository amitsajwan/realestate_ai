from fastapi import APIRouter, Request, Response, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from services.facebook_auth_service import FacebookAuthService
import os, secrets

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
def facebook_login(request: Request, response: Response, db: Session = Depends()):
    state = secrets.token_urlsafe(16)
    FacebookAuthService.save_state(db, state)
    response.set_cookie('fb_state', state, httponly=True, samesite='none', secure=True)
    redirect_uri = get_redirect_uri(request)
    oauth_url = f"https://www.facebook.com/{FB_GRAPH_API_VERSION}/dialog/oauth?client_id={FB_APP_ID}&redirect_uri={redirect_uri}&state={state}&scope=email,public_profile,pages_show_list,pages_manage_posts"
    return {"oauth_url": oauth_url}
