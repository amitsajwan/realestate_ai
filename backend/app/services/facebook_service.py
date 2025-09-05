import httpx
import secrets
import logging
from urllib.parse import urlencode
from typing import Any, Dict, List, Optional
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta

from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError

logger = logging.getLogger(__name__)


class FacebookService:
    """Facebook integration service for OAuth and API operations"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        import os
        self.client_id = os.getenv("FB_APP_ID", settings.FB_APP_ID)
        self.client_secret = os.getenv("FB_APP_SECRET", settings.FB_APP_SECRET)
        self.graph_api_version = os.getenv("FB_GRAPH_API_VERSION", getattr(settings, "FB_GRAPH_API_VERSION", "v19.0"))
        # Use NGROK_BASE_URL for OAuth callback - supports external Facebook callbacks
        base_url = os.getenv("NGROK_BASE_URL", settings.NGROK_BASE_URL)
        self.redirect_uri = f"{base_url}/api/v1/facebook/callback"

    def get_test_page_config(self):
        import os
        return {
            "page_id": os.getenv("FB_PAGE_ID", getattr(settings, "FB_PAGE_ID", None)),
            "page_token": os.getenv("FB_PAGE_TOKEN", getattr(settings, "FB_PAGE_TOKEN", None)),
        }

    def is_test_user(self, user):
        # Define logic for test user (by email, id, or env)
        return user and (user.get("email", "").endswith("@example.com") or user.get("is_test", False))

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
            "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,ads_management,public_profile,email",
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
                        "redirect_uri": self.redirect_uri,
                        "client_secret": self.client_secret,
                        "code": code
                    }
                )
                token_json = token_response.json()
                user_token = token_json.get("access_token")
                if not user_token:
                    raise FacebookError("Failed to obtain access token")
                user_response = await client.get(
                    "https://graph.facebook.com/v19.0/me",
                    params={
                        "access_token": user_token,
                        "fields": "id,name,email"
                    }
                )
                user_info = user_response.json()

            # Get user's ad accounts
            ad_accounts = await self.get_user_ad_accounts(user_token)
            ad_account_info = {}
            if ad_accounts:
                ad_account_info = {
                    "fb_ad_account_id": ad_accounts[0].get("account_id") if ad_accounts[0].get("account_id") else ad_accounts[0].get("id"),
                    "fb_business_id": ad_accounts[0].get("account_id", "").split("_")[0] if ad_accounts[0].get("account_id") else None
                }

            # Update user with Facebook info
            await self.user_repository.update_facebook_info(user_id, {
                "fb_user_token": user_token,
                "fb_user_id": user_info.get("id"),
                "fb_user_name": user_info.get("name"),
                **ad_account_info
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

    async def get_user_ad_accounts(self, user_token: str) -> List[Dict]:
        """Get user's Facebook ad accounts"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.facebook.com/v19.0/me/adaccounts",
                    params={
                        "access_token": user_token,
                        "fields": "account_id,name,currency,account_status,spend_cap"
                    }
                )
                data = response.json()

            if "data" not in data:
                logger.warning("Failed to fetch ad accounts - no data field")
                return []

            return data["data"]
        except Exception as e:
            logger.error(f"Error fetching Facebook ad accounts: {e}")
            return []

    # ---- Stubs for promotion optimization and history ----
    async def optimize_campaign(self, user_id: str, campaign_id: str, strategy: str, amount: Optional[float] = None, notes: Optional[str] = None) -> Dict:
        """Stub: apply an optimization strategy to a campaign.
        In production, this would call Facebook Marketing API and persist changes.
        """
        logger.info(f"[STUB] optimize_campaign user={user_id} campaign={campaign_id} strategy={strategy} amount={amount}")
        applied = strategy
        message = "Optimization suggestion recorded. No live ad changes were made in development mode."
        suggestions = {
            "next_steps": [
                "Increase budget by 10% during peak hours",
                "Narrow location to top-performing cities",
                "Test a video creative for higher engagement"
            ]
        }
        return {
            "success": True,
            "campaign_id": campaign_id,
            "applied_strategy": applied,
            "message": message,
            "suggestions": suggestions,
        }

    async def get_promotion_history(self, user_id: str, property_id: str) -> List[Dict]:
        """Stub: return a minimal promotion history list for a property.
        In production, fetch from DB and/or Facebook API.
        """
        logger.info(f"[STUB] get_promotion_history user={user_id} property={property_id}")
        now = datetime.utcnow()
        return [
            {
                "campaign_id": "23851234567890123",
                "property_id": property_id,
                "status": "PAUSED",
                "created_at": now - timedelta(days=2),
                "last_updated": now - timedelta(hours=6),
                "spend": 1250.0,
                "impressions": 9200,
                "clicks": 180,
            }
        ]

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
            # Separate raise statement for clarity
            raise FacebookError(f"Failed to disconnect: {str(e)}")

    async def create_promotion_campaign(self, user_id: str, post_id: str, budget: float, duration: int, location: str) -> Dict[str, Any]:
        """Create a Facebook ad campaign for post promotion"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user or not user.get("fb_ad_account_id"):
                raise FacebookError("Facebook ad account not configured")

            ad_account_id = user["fb_ad_account_id"]
            access_token = user["fb_user_token"]

            # Create campaign
            campaign_data = {
                "name": f"Property Promotion - {post_id[:8]}",
                "objective": "POST_ENGAGEMENT",
                "status": "PAUSED",  # Start paused so user can review
                "special_ad_categories": ["HOUSING"],
                "access_token": access_token
            }

            async with httpx.AsyncClient() as client:
                campaign_response = await client.post(
                    f"https://graph.facebook.com/v19.0/act_{ad_account_id}/campaigns",
                    json=campaign_data
                )

                if campaign_response.status_code != 200:
                    raise FacebookError(f"Failed to create campaign: {campaign_response.text}")

                campaign_result = campaign_response.json()
                campaign_id = campaign_result.get("id")

            logger.info(f"Campaign created: {campaign_id}")

            # Create ad set
            ad_set_data = {
                "name": f"Property Ad Set - {post_id[:8]}",
                "campaign_id": campaign_id,
                "daily_budget": int(budget * 100),  # Convert to cents
                "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
                "end_time": (datetime.now() + timedelta(days=duration)).strftime("%Y-%m-%dT%H:%M:%S%z"),
                "targeting": {
                    "geo_locations": {
                        "countries": ["IN"],  # India
                        "regions": [{"key": self._get_location_key(location)}] if location else []
                    },
                    "age_min": 18,
                    "age_max": 65
                },
                "status": "PAUSED",
                "access_token": access_token
            }

            ad_set_response = await client.post(
                f"https://graph.facebook.com/v19.0/act_{ad_account_id}/adsets",
                json=ad_set_data
            )

            if ad_set_response.status_code != 200:
                raise FacebookError(f"Failed to create ad set: {ad_set_response.text}")

            ad_set_result = ad_set_response.json()
            ad_set_id = ad_set_result.get("id")

            logger.info(f"Ad set created: {ad_set_id}")

            # Create ad creative
            creative_data = {
                "name": f"Property Creative - {post_id[:8]}",
                "object_story_id": post_id,
                "access_token": access_token
            }

            creative_response = await client.post(
                f"https://graph.facebook.com/v19.0/act_{ad_account_id}/adcreatives",
                json=creative_data
            )

            if creative_response.status_code != 200:
                raise FacebookError(f"Failed to create creative: {creative_response.text}")

            creative_result = creative_response.json()
            creative_id = creative_result.get("id")

            # Create ad
            ad_data = {
                "name": f"Property Ad - {post_id[:8]}",
                "adset_id": ad_set_id,
                "creative": {
                    "creative_id": creative_id
                },
                "status": "PAUSED",
                "access_token": access_token
            }

            ad_response = await client.post(
                f"https://graph.facebook.com/v19.0/act_{ad_account_id}/ads",
                json=ad_data
            )

            if ad_response.status_code != 200:
                raise FacebookError(f"Failed to create ad: {ad_response.text}")

            ad_result = ad_response.json()
            ad_id = ad_result.get("id")

            logger.info(f"Ad created: {ad_id}")

            return {
                "campaign_id": campaign_id,
                "ad_set_id": ad_set_id,
                "ad_id": ad_id,
                "creative_id": creative_id,
                "status": "PAUSED"
            }

        except Exception as e:
            logger.error(f"Error creating promotion campaign: {e}")
            raise FacebookError(f"Failed to create promotion: {str(e)}")

    async def get_promotion_status(self, user_id: str, campaign_id: str) -> Dict[str, Any]:
        """Get promotion analytics for a campaign"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user or not user.get("fb_user_token"):
                raise FacebookError("Facebook not connected")

            access_token = user["fb_user_token"]

            # Get campaign insights
            async with httpx.AsyncClient() as client:
                insights_response = await client.get(
                    f"https://graph.facebook.com/v19.0/{campaign_id}/insights",
                    params={
                        "fields": "impressions,reach,frequency,clicks,spend,actions",
                        "time_range": {"since": "2024-01-01", "until": "2024-12-31"},
                        "access_token": access_token
                    }
                )

                if insights_response.status_code != 200:
                    logger.warning(f"Failed to get insights: {insights_response.text}")
                    return self._get_empty_insights()

                insights_data = insights_response.json()

                if not insights_data.get("data"):
                    return self._get_empty_insights()

                insights = insights_data["data"][0]

                # Get campaign status
                campaign_response = await client.get(
                    f"https://graph.facebook.com/v19.0/{campaign_id}",
                    params={
                        "fields": "status",
                        "access_token": access_token
                    }
                )

                campaign_status = "UNKNOWN"
                if campaign_response.status_code == 200:
                    campaign_data = campaign_response.json()
                    campaign_status = campaign_data.get("status", "UNKNOWN")

                # Parse actions for engagement metrics
                actions = insights.get("actions", [])
                engaged_users = 0
                for action in actions:
                    if action.get("action_type") in ["post_engagement", "page_engagement", "link_click"]:
                        engaged_users += int(action.get("value", 0))

                return {
                    "campaign_id": campaign_id,
                    "status": campaign_status,
                    "impressions": int(insights.get("impressions", 0)),
                    "reach": int(insights.get("reach", 0)),
                    "frequency": float(insights.get("frequency", 0)),
                    "clicks": int(insights.get("clicks", 0)),
                    "spend": float(insights.get("spend", 0)),
                    "engaged_users": engaged_users,
                    "last_updated": datetime.now()
                }

        except Exception as e:
            logger.error(f"Error getting promotion status: {e}")
            return self._get_empty_insights()

    def _get_location_key(self, location: str) -> str:
        """Get Facebook location key for targeting"""
        # This is a simplified mapping - in production, you'd use Facebook's location search API
        location_mapping = {
            "delhi": "1109",  # Delhi region key
            "mumbai": "1118",  # Mumbai region key
            "bangalore": "1110",  # Karnataka region key
            "chennai": "1124",  # Tamil Nadu region key
            "kolkata": "1121",  # West Bengal region key
            "pune": "1117",  # Maharashtra region key
            "hyderabad": "1112",  # Telangana region key
            "ahmedabad": "1107",  # Gujarat region key
        }

        # Default to Delhi if location not found
        return location_mapping.get(location.lower(), "1109")

    def _get_empty_insights(self) -> Dict[str, Any]:
        """Return empty insights structure"""
        return {
            "campaign_id": None,
            "status": "UNKNOWN",
            "impressions": 0,
            "reach": 0,
            "frequency": 0.0,
            "clicks": 0,
            "spend": 0.0,
            "engaged_users": 0,
            "last_updated": None
        }