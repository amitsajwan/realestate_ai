from fastapi import APIRouter, Request, Response, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from services.facebook_auth_service import FacebookAuthService
import requests, os

router = APIRouter()

FB_APP_ID = os.getenv('FB_APP_ID')
FB_APP_SECRET = os.getenv('FB_APP_SECRET')
FB_GRAPH_API_VERSION = os.getenv('FB_GRAPH_API_VERSION', 'v19.0')
def get_redirect_uri(request: Request):
    env_uri = os.getenv('FACEBOOK_REDIRECT_URI')
    if env_uri:
        return env_uri
    return str(request.base_url) + f'api/facebook/callback'
FB_TOKEN_URL = f'https://graph.facebook.com/{FB_GRAPH_API_VERSION}/oauth/access_token'
FB_USER_URL = 'https://graph.facebook.com/me'

@router.get('/api/facebook/callback')
def facebook_callback(request: Request, response: Response, db: Session = Depends(), state: str = Cookie(None), code: str = None):
    if not FacebookAuthService.validate_state(db, state):
        raise HTTPException(status_code=401, detail='Invalid state parameter')
    redirect_uri = get_redirect_uri(request)
    token_resp = requests.get(FB_TOKEN_URL, params={
        'client_id': FB_APP_ID,
        'client_secret': FB_APP_SECRET,
        'redirect_uri': redirect_uri,
        'code': code
    })
    token_data = token_resp.json()
    access_token = token_data.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail='Token exchange failed')
    user_resp = requests.get(FB_USER_URL, params={'access_token': access_token})
    user_data = user_resp.json()
    user_id = user_data.get('id')
    FacebookAuthService.save_auth(db, user_id, access_token)
    response.set_cookie('fb_user_id', user_id, httponly=True, samesite='none', secure=True)
    return {"user_id": user_id}
