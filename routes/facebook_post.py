from fastapi import APIRouter, Request, Response, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from services.facebook_post_service import FacebookPostService
from services.facebook_page_service import FacebookPageService
import requests, os

router = APIRouter()

FACEBOOK_POST_URL = 'https://graph.facebook.com/v18.0/{page_id}/feed'

@router.post('/api/facebook/post')
def post_to_facebook(request: Request, db: Session = Depends(), user_id: str = Cookie(None), page_id: str = None, message: str = None, image_url: str = None):
    page = FacebookPageService.get_pages(db, user_id)
    page = next((p for p in page if p.page_id == page_id), None)
    if not page:
        raise HTTPException(status_code=404, detail='Page not found')
    resp = requests.post(FACEBOOK_POST_URL.format(page_id=page_id), data={
        'message': message,
        'access_token': page.access_token,
        'picture': image_url
    })
    post_data = resp.json()
    post_id = post_data.get('id')
    FacebookPostService.save_post(db, user_id, page_id, post_id, message, image_url)
    return {"post_id": post_id}
