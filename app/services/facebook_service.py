"""
Facebook Service
================
Handles Facebook OAuth, page management, and posting.
"""
import logging
from typing import Dict, Any
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError
from core.config import settings
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class FacebookService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_facebook_config(self, user_id: str) -> Dict[str, Any]:
        user = await self.user_repository.get_by_id(user_id)
        return {
            "connected": user.get("facebook_connected", False),
            "page_id": user.get("fb_page_id"),
            "page_name": user.get("fb_page_name"),
            "app_id": settings.FB_APP_ID
        }

    async def handle_callback(self, code: str, state: str):
        """
        Handle Facebook OAuth callback, exchange code for user token, and store it.
        """ 
        # You must implement secure retrieval/exchange according to Facebook docs
        try:
            # Exchange code for access token
            async with httpx.AsyncClient() as client:
                token_resp = await client.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
                    "client_id": settings.FB_APP_ID,
                    "client_secret": settings.FB_APP_SECRET,
                    "redirect_uri": settings.FB_REDIRECT_URI,
                    "code": code
                })
                token_data = token_resp.json()

            user_token = token_data.get("access_token")
            if not user_token:
                raise FacebookError(f"OAuth token not found in response: {token_data}")

            # Save token to user data (find user by state info, e.g., JWT user ID)
            user_id = self.extract_user_id_from_state(state)
            await self.user_repository.update_user_fields(user_id, {
                "fb_user_token": user_token,
                "facebook_connected": True,
                "fb_connected_at": datetime.utcnow()
            })

            return {"status": "success", "message": "Facebook connected!"}

        except Exception as e:
            logger.error(f"Facebook OAuth callback failed: {e}")
            raise FacebookError("Failed to connect Facebook.")

    def extract_user_id_from_state(self, state: str) -> str:
        # Implement your logic here (could decode JWT, use mapping, etc.)
        # Here, we assume state is user_id for simplicity
        return state

    async def get_user_pages(self, user_id: str):
        user = await self.user_repository.get_by_id(user_id)
        user_token = user.get("fb_user_token")
        if not user_token:
            raise FacebookError("User not connected to Facebook.")

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://graph.facebook.com/v19.0/me/accounts",
                    params={
                        "access_token": user_token,
                        "fields": "id,name,access_token"
                    }
                )
                data = resp.json()
            if "data" not in data:
                raise FacebookError(str(data))
            return data["data"]
        except Exception as e:
            logger.error(f"Facebook page fetch failed: {e}")
            raise FacebookError("Failed to fetch Facebook pages.")

    async def select_page(self, user_id: str, page_id: str):
        pages = await self.get_user_pages(user_id)
        selected = next((p for p in pages if p.get("id") == page_id), None)
        if not selected:
            raise FacebookError("Selected page not found among user pages.")

        await self.user_repository.update_user_fields(user_id, {
            "fb_page_id": selected["id"],
            "fb_page_name": selected["name"],
            "fb_page_token": selected["access_token"],
        })
        return {"status": "success", "page": selected["name"]}

    async def post_property(self, user_id: str, property_id: str):
        user = await self.user_repository.get_by_id(user_id)
        fb_page_id = user.get("fb_page_id")
        fb_page_token = user.get("fb_page_token")
        if not fb_page_id or not fb_page_token:
            raise FacebookError("User has not selected a Facebook page.")

        # Example: Get property details (implement actual fetch as appropriate)
        from app.repositories.property_repository import PropertyRepository
        property_repo = PropertyRepository()
        property_obj = await property_repo.get_by_id(property_id)
        if not property_obj:
            raise FacebookError("Property not found.")

        message = f"Check out this property: {property_obj['title']} in {property_obj['location']} for {property_obj['price']}"
        if property_obj.get("description"):
            message += f"\n\n{property_obj['description']}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://graph.facebook.com/v19.0/{fb_page_id}/feed",
                    params={
                        "message": message,
                        "access_token": fb_page_token
                    }
                )
                result = resp.json()
            if "id" not in result:
                raise FacebookError(str(result))
            return {"status": "success", "post_id": result["id"]}
        except Exception as e:
            logger.error(f"Facebook post property failed: {e}")
            raise FacebookError("Failed to post property on Facebook.")

    async def disconnect(self, user_id: str):
        await self.user_repository.disconnect_facebook(user_id)
