#!/usr/bin/env python3
"""
Clean Facebook Integration Router
================================
Handles Facebook OAuth, page management, and posting
"""

import logging
import httpx
import secrets
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

router = APIRouter()

# Import shared utilities
from app.utils import verify_token

class FacebookIntegration:
    """Facebook integration service"""
    
    def __init__(self):
        from app.config import settings
        self.client_id = settings.FB_APP_ID
        self.client_secret = settings.FB_APP_SECRET
        self.base_url = "https://graph.facebook.com/v19.0"
        self.redirect_uri = settings.get_facebook_callback_url()
        
        # In-memory storage for OAuth states and tokens (use database in production)
        self.oauth_states = {}
        self.user_tokens = {}
        self.page_tokens = {}
        
        logger.info(f"Facebook Integration initialized with APP_ID: {self.client_id}")
    
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
            # Clean up old states (older than 10 minutes)
            if datetime.utcnow() - state_data['created_at'] > timedelta(minutes=10):
                del self.oauth_states[state]
                return False
            
            if not state_data['used']:
                state_data['used'] = True
                return True
        
        return False
    
    def get_oauth_url(self, user_id: str = None) -> Dict[str, Any]:
        """Generate Facebook OAuth URL"""
        state = self.generate_oauth_state()
        
        # DEMO MODE: Skip Facebook OAuth and simulate success
        if not self.client_id or self.client_id == "":
            logger.info("🔄 DEMO MODE: Generating demo OAuth URL")
            
            # Create a demo callback URL that will trigger our demo mode
            demo_callback_url = f"{self.redirect_uri}?code=demo_code_{int(time.time())}&state={state}"
            
            return {
                'oauth_url': demo_callback_url,
                'state': state,
                'expires_in': 600,  # 10 minutes
                'demo_mode': True
            }
        
        # REAL MODE: Actual Facebook OAuth
        logger.info("🔄 REAL MODE: Generating Facebook OAuth URL")
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': 'pages_manage_posts,pages_read_engagement,pages_show_list',
            'response_type': 'code'
        }
        
        if user_id:
            params['state'] = f"{state}_{user_id}"
        
        oauth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
        
        return {
            'oauth_url': oauth_url,
            'state': state,
            'expires_in': 600,  # 10 minutes
            'demo_mode': False
        }
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for token"""
        try:
            if not self.verify_oauth_state(state):
                return {
                    'success': False,
                    'error': 'Invalid or expired OAuth state'
                }
            
            # Extract user_id from state if present
            user_id = None
            if '_' in state:
                state, user_id = state.split('_', 1)
            
            # DEMO MODE: Simulate successful OAuth for testing
            if not self.client_id or self.client_id == "":
                logger.info("🔄 DEMO MODE: Simulating Facebook OAuth success")
                
                # Generate demo access token
                demo_access_token = f"demo_fb_token_{int(time.time())}"
                
                # Demo pages for testing
                demo_pages = [
                    {
                        'id': 'demo_page_123',
                        'name': 'Demo Real Estate Page',
                        'category': 'Real Estate',
                        'access_token': demo_access_token
                    }
                ]
                
                # Store demo user token
                if user_id:
                    self.user_tokens[user_id] = {
                        'token': demo_access_token,
                        'expires_at': datetime.utcnow() + timedelta(hours=2),
                        'created_at': datetime.utcnow()
                    }
                
                # Store demo page tokens
                for page in demo_pages:
                    self.page_tokens[page['id']] = {
                        'token': page['access_token'],
                        'name': page['name'],
                        'category': page['category'],
                        'access_token': demo_access_token
                    }
                
                return {
                    'success': True,
                    'access_token': demo_access_token,
                    'pages': demo_pages,
                    'message': 'DEMO MODE: Facebook account connected successfully (simulated)'
                }
            
            # REAL MODE: Actual Facebook OAuth
            logger.info("🔄 REAL MODE: Processing actual Facebook OAuth")
            
            # Exchange code for access token
            token_params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'code': code
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/oauth/access_token",
                    params=token_params
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data.get('access_token')
                    
                    if access_token:
                        # Store user token
                        if user_id:
                            self.user_tokens[user_id] = {
                                'token': access_token,
                                'expires_at': datetime.utcnow() + timedelta(hours=2),
                                'created_at': datetime.utcnow()
                            }
                        
                        # Get user pages
                        pages = await self.get_user_pages(access_token)
                        
                        return {
                            'success': True,
                            'access_token': access_token,
                            'pages': pages,
                            'message': 'Facebook account connected successfully'
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Failed to get access token'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Facebook API error: {response.status_code}'
                    }
                    
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_user_pages(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's Facebook pages"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me/accounts",
                    params={'access_token': access_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pages = data.get('data', [])
                    
                    # Store page tokens
                    for page in pages:
                        page_id = page.get('id')
                        page_token = page.get('access_token')
                        if page_id and page_token:
                            self.page_tokens[page_id] = {
                                'token': page_token,
                                'name': page.get('name', ''),
                                'category': page.get('category', ''),
                                'access_token': access_token
                            }
                    
                    return pages
                else:
                    logger.error(f"Failed to get pages: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting user pages: {e}")
            return []
    
    async def post_to_page(self, page_id: str, message: str, user_id: str = None) -> Dict[str, Any]:
        """Post message to Facebook page"""
        try:
            page_token_data = self.page_tokens.get(page_id)
            if not page_token_data:
                return {
                    'success': False,
                    'error': 'Page not found or not connected'
                }
            
            # Check if this is a demo page
            if page_id.startswith('demo_'):
                # Simulate successful posting for demo pages
                import time
                demo_post_id = f"demo_post_{int(time.time())}"
                
                logger.info(f"🎭 DEMO MODE: Simulating successful Facebook post to {page_id}")
                logger.info(f"📝 Message: {message[:100]}...")
                
                return {
                    'success': True,
                    'post_id': demo_post_id,
                    'message': 'DEMO MODE: Posted to Facebook successfully (simulated)',
                    'facebook_result': {
                        'id': demo_post_id,
                        'status': 'published',
                        'demo_mode': True
                    }
                }
            
            # REAL MODE: Actual Facebook API call
            page_token = page_token_data['token']
            
            # Prepare post data
            post_data = {
                'message': message,
                'access_token': page_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{page_id}/feed",
                    data=post_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    post_id = result.get('id')
                    
                    return {
                        'success': True,
                        'post_id': post_id,
                        'message': 'Posted to Facebook successfully',
                        'facebook_result': result
                    }
                else:
                    error_data = response.json()
                    return {
                        'success': False,
                        'error': f'Facebook API error: {response.status_code}',
                        'details': error_data
                    }
                    
        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize Facebook integration
fb_integration = FacebookIntegration()

@router.get("/facebook/oauth")
async def facebook_oauth(request: Request):
    """Start Facebook OAuth flow - Public endpoint"""
    try:
        oauth_data = fb_integration.get_oauth_url()
        
        return JSONResponse(content={
            "success": True,
            "oauth_url": oauth_data['oauth_url'],
            "state": oauth_data['state'],
            "expires_in": oauth_data['expires_in']
        })
        
    except Exception as e:
        logger.error(f"Facebook OAuth error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )

@router.get("/facebook/callback")
async def facebook_callback(code: str, state: str, request: Request):
    """Handle Facebook OAuth callback and create user session"""
    try:
        logger.info(f"🔄 Facebook OAuth callback received - code: {code[:10]}..., state: {state[:10]}...")
        
        # Handle OAuth callback
        result = await fb_integration.handle_oauth_callback(code, state)
        
        if result.get('success'):
            # Extract user info from Facebook response
            access_token = result.get('access_token')
            pages = result.get('pages', [])
            
            # Create or get user from Facebook data
            from app.routers.auth import create_access_token, create_user_from_facebook
            
            # Create user session
            user_data = await create_user_from_facebook(access_token, pages)
            user_id = user_data.get('user_id')
            email = user_data.get('email', f"fb_user_{user_id}")
            
            # Generate JWT token
            token_data = {
                "sub": email,
                "user_id": user_id,
                "email": email,
                "type": "access_token",
                "facebook_connected": True
            }
            
            access_token_jwt = create_access_token(token_data)
            
            # Store Facebook connection data
            fb_integration.user_tokens[user_id] = {
                'token': access_token,
                'user_id': user_id,
                'email': email,
                'pages': pages,
                'connected_at': datetime.utcnow()
            }
            
            logger.info(f"✅ Facebook OAuth successful for user: {email}")
            
            # Redirect to dashboard with success message
            from app.config import settings
            dashboard_url = f"{settings.get_oauth_dashboard_url()}?auth=success&token={access_token_jwt}"
            
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=dashboard_url)
        else:
            logger.error(f"❌ Facebook OAuth failed: {result.get('error')}")
            # Redirect to login with error
            from app.config import settings
            login_url = f"{settings.get_oauth_login_url()}?error=oauth_failed&message={result.get('error')}"
            
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=login_url)
        
    except Exception as e:
        logger.error(f"Facebook callback error: {e}")
        # Redirect to login with error
        from app.config import settings
        login_url = f"{settings.get_oauth_login_url()}?error=callback_error&message={str(e)}"
        
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=login_url)

@router.post("/facebook/post")
async def post_to_facebook(request: Request):
    """Post content to Facebook page"""
    try:
        # Verify user token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "No authorization token provided"}
            )
        
        # Parse request body
        body = await request.json()
        page_id = body.get('page_id')
        message = body.get('message')
        language = body.get('language', 'English')
        
        if not page_id or not message:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing page_id or message"}
            )
        
        # Decode JWT token to get user info
        try:
            from app.utils import verify_token
            user_data = verify_token(token)
            if not user_data:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": "Invalid token"}
                )
            
            user_id = user_data.get('user_id')
            if not user_id:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": "User ID not found in token"}
                )
                
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Token verification failed"}
            )
        
        # Post to Facebook
        result = await fb_integration.post_to_page(page_id, message, user_id)
        
        if result.get('success'):
            logger.info(f"✅ Facebook post successful for user {user_id} on page {page_id}")
            return JSONResponse(content={
                "success": True,
                "post_id": result.get('post_id'),
                "message": f"Successfully posted to Facebook in {language}",
                "language": language,
                "page_id": page_id
            })
        else:
            logger.error(f"❌ Facebook post failed for user {user_id}: {result.get('error')}")
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": result.get('error')}
            )
            
    except Exception as e:
        logger.error(f"Facebook posting error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/facebook/pages")
async def get_facebook_pages(request: Request):
    """Get user's Facebook pages"""
    try:
        # Verify user token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "No authorization token provided"}
            )
        
        # Decode JWT token to get user info
        try:
            from app.utils import verify_token
            user_data = verify_token(token)
            if not user_data:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": "Invalid token"}
                )
            
            user_id = user_data.get('user_id')
            if not user_id:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": "User ID not found in token"}
                )
                
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Token verification failed"}
            )
        
        # Get user's Facebook pages from stored data
        user_fb_data = fb_integration.user_tokens.get(user_id, {})
        pages = user_fb_data.get('pages', [])
        
        # If no pages found, try to get them from Facebook API
        if not pages and user_fb_data.get('access_token'):
            try:
                pages = await fb_integration.get_user_pages(user_fb_data['access_token'])
                # Update stored data
                user_fb_data['pages'] = pages
                fb_integration.user_tokens[user_id] = user_fb_data
            except Exception as e:
                logger.error(f"Error fetching pages from Facebook API: {e}")
        
        return JSONResponse(content={
            "success": True,
            "pages": pages
        })
        
    except Exception as e:
        logger.error(f"Error getting Facebook pages: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/facebook/posts")
async def get_facebook_posts(request: Request):
    """Get user's Facebook posting history"""
    try:
        # Verify user token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "No authorization token provided"}
            )
        
        # Get user's posting history (simplified for demo)
        # In production, this would query a database
        demo_posts = [
            {
                "id": "demo_post_1",
                "message": "Beautiful 2BHK apartment in prime location! 🏠✨",
                "created_time": "2024-01-20T10:00:00Z",
                "language": "English",
                "page_id": "demo_page_1"
            },
            {
                "id": "demo_post_2", 
                "message": "अद्भुत 2BHK अपार्टमेंट प्राइम लोकेशन में! 🏠✨",
                "created_time": "2024-01-19T15:30:00Z",
                "language": "Hindi",
                "page_id": "demo_page_1"
            }
        ]
        
        return JSONResponse(content={
            "success": True,
            "posts": demo_posts
        })
        
    except Exception as e:
        logger.error(f"Error getting Facebook posts: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/facebook/config")
async def facebook_config():
    """Get Facebook configuration status"""
    try:
        is_demo_mode = not fb_integration.client_id or fb_integration.client_id == ""
        connected = True  # Always connected in demo mode or with real credentials
        
        return JSONResponse(content={
            "connected": connected,
            "demo_mode": is_demo_mode,
            "app_id": fb_integration.client_id if not is_demo_mode else "DEMO_MODE",
            "message": "DEMO MODE: Facebook integration simulated for testing" if is_demo_mode else "Facebook credentials configured",
            "features": {
                "oauth": True,
                "page_management": True,
                "posting": is_demo_mode,  # Demo mode can simulate posting
                "webhooks": False  # TODO: Implement webhook handling
            }
        })
        
    except Exception as e:
        logger.error(f"Facebook config error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )
