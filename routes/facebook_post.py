from fastapi import APIRouter, Request, Cookie, HTTPException
from services.facebook_post_service import FacebookPostService
from services.facebook_page_service import FacebookPageService
import requests, os

router = APIRouter()

FACEBOOK_POST_URL = 'https://graph.facebook.com/v18.0/{page_id}/feed'

@router.post('/api/facebook/post')
def post_to_facebook(request: Request, user_id: str = Cookie(None), page_id: str = None, message: str = None, image_url: str = None):
    """Fixed Facebook post endpoint - removed db dependency"""

    # Fix: Call get_pages with only user_id parameter
    pages = FacebookPageService.get_pages(user_id)
    page = next((p for p in pages if p['page_id'] == page_id), None)

    if not page:
        raise HTTPException(status_code=404, detail='Page not found')

    resp = requests.post(FACEBOOK_POST_URL.format(page_id=page_id), data={
        'message': message,
        'access_token': page['access_token'],
        'picture': image_url
    })

    post_data = resp.json()
    post_id = post_data.get('id')

    # Fix: Call save_post with correct parameters
    FacebookPostService.save_post(user_id, page_id, post_id, message, image_url)

    return {"post_id": post_id}
