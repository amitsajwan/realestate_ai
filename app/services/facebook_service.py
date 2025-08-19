import httpx
import secrets
from urllib.parse import urlencode
from fastapi.responses import HTMLResponse

class FacebookService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.client_id = settings.FB_APP_ID
        self.client_secret = settings.FB_APP_SECRET
        self.redirect_uri = settings.FB_REDIRECT_URI

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
