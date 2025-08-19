import httpx
import secrets
import logging
from urllib.parse import urlencode
from typing import Dict, List, Optional
from fastapi.responses import HTMLResponse

from core.config import settings
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError

logger = logging.getLogger(__name__)


class FacebookService:
    """Facebook integration service for OAuth and API operations"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.client_id = settings.FB_APP_ID
        self.client_secret = settings.FB_APP_SECRET
        self.redirect_uri = settings.FB_REDIRECT_URI

    async def get_facebook_config(self, user_id: str) -> Dict:
        """Get Facebook connection status and config for user"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {"connected": False, "error": "User not found"}
            
            return {
                "connected": user.get("facebook_connected", False),
                "page_id": user.get("fb_page_id"),
                "page_name": user.get("fb_page_name"),
                "user_name": user.get("fb_user_name")
            }
        except Exception as e:
            logger.error(f"Facebook config error: {e}")
            return {
                "connected": False,
                "error": "Failed to get Facebook config"
            }

    async def get_oauth_url(self, user_id: str) -> str:
        """Generate Facebook OAuth URL"""
        if not self.client_id:
            raise FacebookError("Facebook App ID not configured")
        
        # Generate secure state parameter
        state = f"{user_id}:{secrets.token_urlsafe(32)}"
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,public_profile,email",
            "response_type": "code"
        }
        
        return f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"

    async def handle_callback(self, code: str, state: str) -> HTMLResponse:
        """Handle Facebook OAuth callback"""
        try:
            # Extract user ID from state
            if ":" not in state:
                raise FacebookError("Invalid state parameter")
            
            user_id = state.split(":")[0]
            
            # Exchange code for access token
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://graph.facebook.com/v19.0/oauth/access_token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "code": code
                    }
                )
                token_data = token_response.json()

            if "access_token" not in token_data:
                raise FacebookError(f"Token exchange failed: {token_data}")

            user_token = token_data["access_token"]

            # Get user info from Facebook
            async with httpx.AsyncClient() as client:
                user_response = await client.get(
                    "https://graph.facebook.com/v19.0/me",
                    params={
                        "access_token": user_token,
                        "fields": "id,name,email"
                    }
                )
                user_info = user_response.json()

            # Update user with Facebook info
            await self.user_repository.update_facebook_info(user_id, {
                "fb_user_token": user_token,
                "fb_user_id": user_info.get("id"),
                "fb_user_name": user_info.get("name")
            })

            logger.info(f"Facebook connected successfully for user: {user_id}")

            # Return success page
            return HTMLResponse("""
            <html>
                <head><title>Facebook Connected</title></head>
                <body>
                    <h2>Facebook Connected Successfully!</h2>
                    <p>You can now close this window and return to the app.</p>
                    <script>
                        setTimeout(() => {
                            window.close();
                        }, 3000);
                    </script>
                </body>
            </html>
            """)

        except Exception as e:
            logger.error(f"Facebook callback error: {e}")
            return HTMLResponse(f"""
            <html>
                <head><title>Connection Failed</title></head>
                <body>
                    <h2>Facebook Connection Failed</h2>
                    <p>Error: {str(e)}</p>
                    <p>Please try again.</p>
                </body>
            </html>
            """, status_code=400)

    async def get_user_pages(self, user_id: str) -> List[Dict]:
        """Get user's Facebook pages"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user or not user.get("fb_user_token"):
                raise FacebookError("Facebook not connected")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.facebook.com/v19.0/me/accounts",
                    params={
                        "access_token": user["fb_user_token"],
                        "fields": "id,name,access_token"
                    }
                )
                data = response.json()

            if "data" not in data:
                raise FacebookError("Failed to fetch pages")

            return data["data"]

        except Exception as e:
            logger.error(f"Error fetching Facebook pages: {e}")
            raise FacebookError(f"Failed to fetch pages: {str(e)}")

    async def select_page(self, user_id: str, page_id: str) -> Dict:
        """Select a Facebook page for posting"""
        try:
            pages = await self.get_user_pages(user_id)
            selected_page = None
            
            for page in pages:
                if page["id"] == page_id:
                    selected_page = page
                    break
            
            if not selected_page:
                raise FacebookError("Page not found")

            # Update user with selected page info
            await self.user_repository.update_facebook_info(user_id, {
                "fb_page_id": selected_page["id"],
                "fb_page_name": selected_page["name"],
                "fb_page_token": selected_page["access_token"]
            })

            return {
                "success": True,
                "page_id": selected_page["id"],
                "page_name": selected_page["name"]
            }

        except Exception as e:
            logger.error(f"Error selecting Facebook page: {e}")
            raise FacebookError(f"Failed to select page: {str(e)}")

    async def post_property(self, user_id: str, property_id: str) -> Dict:
        """Post a property to Facebook"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user or not user.get("fb_page_token"):
                raise FacebookError("Facebook page not configured")

            # In a real implementation, you would:
            # 1. Fetch property details from property repository
            # 2. Format the post content
            # 3. Post to Facebook using the Graph API
            
            # For now, return a placeholder
            return {
                "success": True,
                "message": f"Property {property_id} posted to Facebook",
                "post_id": f"mock_post_{property_id}"
            }

        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            raise FacebookError(f"Failed to post property: {str(e)}")

    async def disconnect(self, user_id: str) -> bool:
        """Disconnect Facebook account"""
        try:
            await self.user_repository.disconnect_facebook(user_id)
            logger.info(f"Facebook disconnected for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting Facebook: {e}")
            raise FacebookError(f"Failed to disconnect: {str(e)}")