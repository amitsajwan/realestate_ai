#!/usr/bin/env python3
"""
Facebook Integration Router with MongoDB Persistence
====================================================
Handles Facebook OAuth, page management, and posting
"""

import logging
import httpx
import secrets
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

from app.utils import verify_token
from app.core.database import db  # <- make sure Mongo client is initialized in app.core.database

logger = logging.getLogger(__name__)
router = APIRouter()

class FacebookIntegration:
    """Facebook integration service"""

    def __init__(self):
        from app.config import settings
        self.client_id = settings.FB_APP_ID
        self.client_secret = settings.FB_APP_SECRET
        self.base_url = "https://graph.facebook.com/v19.0"
        self.redirect_uri = settings.get_facebook_callback_url()

        # In-memory state only (DB used for tokens)
        self.oauth_states = {}

        logger.info(f"Facebook Integration initialized with APP_ID: {self.client_id}")

    # ---------------- STATE MGMT ---------------- #
    def generate_oauth_state(self) -> str:
        """Generate secure OAuth state"""
        state = secrets.token_urlsafe(32)
        self.oauth_states[state] = {
            'created_at': datetime.utcnow(),
            'used': False
        }
        return state

    def verify_oauth_state(self, state: str) -> bool:
        """Verify OAuth state and mark as used"""
        if state in self.oauth_states:
            state_data = self.oauth_states[state]
            if datetime.utcnow() - state_data['created_at'] > timedelta(minutes=10):
                del self.oauth_states[state]
                return False
            if not state_data['used']:
                state_data['used'] = True
                return True
        return False

    # ---------------- OAUTH ---------------- #
    def get_oauth_url(self, user_id: str = None) -> Dict[str, Any]:
        """Generate Facebook OAuth URL"""
        state = self.generate_oauth_state()

        if not self.client_id or self.client_id == "":
            logger.info("🔄 DEMO MODE: Generating demo OAuth URL")
            demo_callback_url = f"{self.redirect_uri}?code=demo_code_{int(time.time())}&state={state}"
            return {"oauth_url": demo_callback_url, "state": state, "expires_in": 600, "demo_mode": True}

        logger.info("🔄 REAL MODE: Generating Facebook OAuth URL")
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': 'pages_manage_posts,pages_read_engagement,pages_show_list',
            'response_type': 'code'
        }

        print(params)
        if user_id:
            params['state'] = f"{state}_{user_id}"

        oauth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
        return {"oauth_url": oauth_url, "state": state, "expires_in": 600, "demo_mode": False}

    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for token"""
        try:
            if not self.verify_oauth_state(state):
                return {"success": False, "error": "Invalid or expired OAuth state"}

            user_id = None
            if "_" in state:
                state, user_id = state.split("_", 1)

            # DEMO MODE
            if not self.client_id or self.client_id == "":
                demo_access_token = f"demo_fb_token_{int(time.time())}"
                demo_pages = [{
                    'id': 'demo_page_123',
                    'name': 'Demo Real Estate Page',
                    'category': 'Real Estate',
                    'access_token': demo_access_token
                }]
                # Save to DB
                await db.facebook_users.update_one(
                    {"user_id": user_id or "demo_user"},
                    {"$set": {"token": demo_access_token, "expires_at": datetime.utcnow() + timedelta(hours=2)}},
                    upsert=True
                )
                for page in demo_pages:
                    await db.facebook_pages.update_one(
                        {"page_id": page["id"]},
                        {"$set": {**page, "user_id": user_id or "demo_user"}},
                        upsert=True
                    )
                return {"success": True, "access_token": demo_access_token, "pages": demo_pages,
                        "message": "DEMO MODE: Facebook connected (simulated)"}

            # REAL MODE
            token_params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'code': code
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/oauth/access_token", params=token_params)
                if resp.status_code != 200:
                    return {"success": False, "error": f"Facebook error: {resp.status_code}"}

                token_data = resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    return {"success": False, "error": "No access token from Facebook"}

                # Save user token
                await db.facebook_users.update_one(
                    {"user_id": user_id or "unknown"},
                    {"$set": {"token": access_token, "expires_at": datetime.utcnow() + timedelta(hours=2)}},
                    upsert=True
                )

                pages = await self.get_user_pages(access_token, user_id)
                return {"success": True, "access_token": access_token, "pages": pages,
                        "message": "Facebook account connected"}

        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return {"success": False, "error": str(e)}

    # ---------------- PAGES ---------------- #
    async def get_user_pages(self, access_token: str, user_id: str = None) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/me/accounts", params={"access_token": access_token})
                if resp.status_code != 200:
                    return []
                data = resp.json()
                pages = data.get("data", [])

                for page in pages:
                    await db.facebook_pages.update_one(
                        {"page_id": page["id"]},
                        {"$set": {**page, "user_id": user_id or "unknown"}},
                        upsert=True
                    )
                return pages
        except Exception as e:
            logger.error(f"get_user_pages error: {e}")
            return []

    async def post_to_page(self, page_id: str, message: str, user_id: str = None) -> Dict[str, Any]:
        try:
            page = await db.facebook_pages.find_one({"page_id": page_id})
            if not page:
                return {"success": False, "error": "Page not found or not connected"}

            if page_id.startswith("demo_"):
                demo_post_id = f"demo_post_{int(time.time())}"
                return {"success": True, "post_id": demo_post_id,
                        "message": "DEMO MODE: Posted successfully", "facebook_result": {"id": demo_post_id}}

            post_data = {"message": message, "access_token": page["access_token"]}
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.base_url}/{page_id}/feed", data=post_data)
                if resp.status_code == 200:
                    result = resp.json()
                    return {"success": True, "post_id": result.get("id"), "facebook_result": result}
                else:
                    return {"success": False, "error": f"Facebook error {resp.status_code}", "details": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Init
fb_integration = FacebookIntegration()

# ---------------- ROUTES ---------------- #
@router.get("/facebook/oauth")
async def facebook_oauth(request: Request):
    try:
        oauth_data = fb_integration.get_oauth_url()
        return JSONResponse(content={"success": True, "oauth_url": oauth_data["oauth_url"],
                                     "state": oauth_data["state"], "expires_in": oauth_data["expires_in"]})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.get("/facebook/callback")
async def facebook_callback(code: str, state: str, request: Request):
    result = await fb_integration.handle_oauth_callback(code, state)
    from app.config import settings
    if result.get("success"):
        # Create JWT
        from app.routers.auth import create_access_token, create_user_from_facebook
        user_data = await create_user_from_facebook(result["access_token"], result.get("pages", []))
        user_id = user_data.get("user_id")
        email = user_data.get("email", f"fb_user_{user_id}")
        jwt = create_access_token({"sub": email, "user_id": user_id, "email": email, "facebook_connected": True})
        return RedirectResponse(url=f"{settings.get_oauth_dashboard_url()}?auth=success&token={jwt}")
    else:
        return RedirectResponse(url=f"{settings.get_oauth_login_url()}?error=oauth_failed&message={result.get('error')}")

@router.post("/facebook/post")
async def post_to_facebook(request: Request):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return JSONResponse(status_code=401, content={"success": False, "error": "Missing token"})
        user_data = verify_token(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"success": False, "error": "Invalid token"})

        body = await request.json()
        page_id, message = body.get("page_id"), body.get("message")
        if not page_id or not message:
            return JSONResponse(status_code=400, content={"success": False, "error": "Missing params"})

        result = await fb_integration.post_to_page(page_id, message, user_data.get("user_id"))
        if result.get("success"):
            return JSONResponse(content={"success": True, "post_id": result["post_id"], "page_id": page_id})
        else:
            return JSONResponse(status_code=400, content={"success": False, "error": result.get("error")})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.get("/facebook/pages")
async def get_facebook_pages(request: Request):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return JSONResponse(status_code=401, content={"success": False, "error": "Missing token"})
        user_data = verify_token(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"success": False, "error": "Invalid token"})

        pages = await db.facebook_pages.find({"user_id": user_data["user_id"]}).to_list(100)
        return JSONResponse(content={"success": True, "pages": pages})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.get("/facebook/config")
async def facebook_config():
    try:
        is_demo = not fb_integration.client_id or fb_integration.client_id == ""
        return JSONResponse(content={"connected": True, "demo_mode": is_demo,
                                     "app_id": fb_integration.client_id if not is_demo else "DEMO_MODE"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
