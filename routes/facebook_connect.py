from fastapi import APIRouter, Request, Cookie, HTTPException
from services.facebook_page_service import FacebookPageService
from services.facebook_auth_service import FacebookAuthService
import requests, os

router = APIRouter()

FACEBOOK_PAGES_URL = 'https://graph.facebook.com/v18.0/me/accounts'

@router.get('/api/facebook/pages')
def get_facebook_pages(request: Request, user_id: str = Cookie(None)):
    """Fixed Facebook pages endpoint - removed db dependency"""

    # Fix: Call get_auth with only user_id parameter
    auth = FacebookAuthService.get_auth(user_id)
    if not auth:
        raise HTTPException(status_code=401, detail='User not authenticated')

    resp = requests.get(FACEBOOK_PAGES_URL, params={'access_token': auth['access_token']})
    pages = resp.json().get('data', [])

    for page in pages:
        # Fix: Call save_page with correct parameters
        FacebookPageService.save_page(user_id, page['id'], page['name'], page['access_token'])

    return {"pages": pages}
