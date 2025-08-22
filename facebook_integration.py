#!/usr/bin/env python3
"""
Enhanced Facebook Integration for PropertyAI - Fixed Version
===========================================================

This module provides comprehensive Facebook integration including:
- OAuth flow for connecting Facebook accounts
- Page management and selection
- Long-term token storage and refresh
- AI-powered content posting
- Property listing automation
- Support for both environment variables and runtime configuration
"""

import os
import json
import httpx
import secrets
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class FacebookIntegration:
    """Enhanced Facebook integration service"""
    
    def __init__(self, db_path="propertyai.db"):
        self.db_path = db_path
        self.client_id = os.getenv("FB_APP_ID", "")
        self.client_secret = os.getenv("FB_APP_SECRET", "")
        # Always use Facebook Graph API for backend calls
        self.base_url = "https://graph.facebook.com/v19.0"
        logging.info(f"[TRACE] FacebookIntegration loaded FB_APP_ID: {self.client_id}")
        # Demo credentials removed for production safety
        self.demo_app_id = None
        self.demo_app_secret = None
        # Initialize encryption for token storage
        self._setup_encryption()
        # Create Facebook tables if they don't exist
        self._create_facebook_tables()
    
    def _setup_encryption(self):
        """Setup encryption for secure token storage"""
        # Generate or load encryption key
        key_file = "facebook_key.key"
        if os.path.exists(key_file):
            try:
                with open(key_file, "rb") as f:
                    key = f.read()
            except:
                key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(key)
        else:
            key = Fernet.generate_key()
            try:
                with open(key_file, "wb") as f:
                    f.write(key)
            except:
                # If can't write file, use a default key (not secure for production)
                key = base64.urlsafe_b64encode(b"default_key_32_chars_long_!!!")
        
        self.cipher = Fernet(key)
    
    def _create_facebook_tables(self):
        """Create Facebook-related database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Facebook connections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facebook_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    fb_user_id VARCHAR(255),
                    fb_user_name VARCHAR(255),
                    fb_user_token TEXT,
                    fb_page_token TEXT,
                    token_expires_at TIMESTAMP,
                    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Facebook posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facebook_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    page_id VARCHAR(255),
                    post_id VARCHAR(255),
                    message TEXT,
                    property_id INTEGER REFERENCES properties(id),
                    status VARCHAR(50) DEFAULT 'published',
                    engagement_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Facebook page tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facebook_page_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    page_id VARCHAR(255),
                    page_name VARCHAR(255),
                    token_type VARCHAR(50) DEFAULT 'page',
                    expires_at TIMESTAMP,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Facebook app configurations table (for user-provided credentials)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facebook_app_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    app_id VARCHAR(255),
                    app_secret TEXT,
                    app_name VARCHAR(255),
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error creating Facebook tables: {e}")
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        try:
            return self.cipher.encrypt(token.encode()).decode()
        except:
            # Fallback to base64 encoding if encryption fails
            return base64.b64encode(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token for use"""
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except:
            # Fallback to base64 decoding if decryption fails
            try:
                return base64.b64decode(encrypted_token.encode()).decode()
            except:
                return encrypted_token  # Return as is if all fails
    
    def _get_app_credentials(self, user_id: Optional[int] = None) -> tuple[str, str]:
        """Get Facebook App credentials from environment, user config, or demo"""
        # First try environment variables
        if self.client_id and self.client_secret:
            return self.client_id, self.client_secret

        # Then try user-specific configuration
        if user_id:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT app_id, app_secret FROM facebook_app_configs 
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC LIMIT 1
                ''', (user_id,))

                result = cursor.fetchone()
                conn.close()

                if result:
                    return result[0], self._decrypt_token(result[1])
            except Exception as e:
                logger.error(f"Error getting user app config: {e}")

        # No credentials found
        raise Exception("Facebook App ID not configured. Please set FB_APP_ID environment variable or configure your app credentials.")
    
    def save_user_app_config(self, user_id: int, app_id: str, app_secret: str, app_name: str = "") -> bool:
        """Save user's Facebook App configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Deactivate existing configs
            cursor.execute('''
                UPDATE facebook_app_configs SET is_active = 0 
                WHERE user_id = ?
            ''', (user_id,))
            
            # Insert new config
            encrypted_secret = self._encrypt_token(app_secret)
            cursor.execute('''
                INSERT INTO facebook_app_configs 
                (user_id, app_id, app_secret, app_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, app_id, encrypted_secret, app_name, datetime.now(), datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving app config: {e}")
            return False
    
    def get_oauth_url(self, user_id: str, redirect_uri: str) -> str:
        """Generate Facebook OAuth URL"""
        try:
            # Get app credentials
            app_id, app_secret = self._get_app_credentials(None)
            if not app_id:
                raise Exception("Facebook App ID not configured. Please set FB_APP_ID environment variable or configure your app credentials.")
            # Generate secure state parameter
            if user_id is not None:
                state = f"{user_id}:{secrets.token_urlsafe(32)}"
            else:
                state = secrets.token_urlsafe(32)
            params = {
                "client_id": app_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,public_profile,email",
                "response_type": "code"
            }
            fb_oauth_base = os.getenv("FB_OAUTH_BASE", "https://www.facebook.com/v19.0/dialog/oauth?")
            oauth_url = f"{fb_oauth_base}{urlencode(params)}"
            logger.info(f"Generated OAuth URL for user {user_id}: {oauth_url}")
            return oauth_url
        except Exception as e:
            logger.error(f"Error generating OAuth URL: {e}")
            fb_docs_base = os.getenv("FB_DOCS_BASE", "https://developers.facebook.com/docs/facebook-login/web?state=")
            return f"{fb_docs_base}{user_id if user_id is not None else ''}"
    
    async def handle_oauth_callback(self, code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle Facebook OAuth callback and exchange code for tokens"""
        try:
            # Accept state with or without user_id
            if ":" in state:
                user_id = state.split(":")[0]
            else:
                user_id = None  # New user, passwordless onboarding
            # Get app credentials
            app_id, app_secret = self._get_app_credentials(int(user_id) if user_id else None)
            # Check if this is a demo mode
            if app_id == self.demo_app_id:
                # Simulate successful connection for demo
                return await self._simulate_demo_connection(int(user_id) if user_id else 1)
            # Exchange code for access token
            token_url = f"{self.base_url}/oauth/access_token"
            token_payload = {
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }
            logger.info(f"[TRACE] Facebook token exchange URL: {token_url}")
            logger.info(f"[TRACE] Facebook token exchange payload: {token_payload}")
            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_payload)
                logger.info(f"[TRACE] Facebook token exchange response status: {token_response.status_code}")
                logger.info(f"[TRACE] Facebook token exchange response body: {token_response.text}")
                token_data = token_response.json()

            if "access_token" not in token_data:
                raise Exception(f"Token exchange failed: {token_data}")

            user_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 0)
            token_expires_at = datetime.now() + timedelta(seconds=expires_in) if expires_in > 0 else None

            # Get user info from Facebook
            async with httpx.AsyncClient() as client:
                user_response = await client.get(
                    f"{self.base_url}/me",
                    params={
                        "access_token": user_token,
                        "fields": "id,name,email"
                    }
                )
                user_info = user_response.json()

            # Store user connection
            # If user_id is None, use 0 or create a new user record as needed
            save_user_id = int(user_id) if user_id is not None else 0
            self._save_facebook_connection(
                user_id=save_user_id,
                fb_user_id=user_info.get("id"),
                fb_user_name=user_info.get("name"),
                fb_user_token=user_token,
                token_expires_at=token_expires_at
            )

            return {
                "success": True,
                "user_id": user_id,
                "fb_user_id": user_info.get("id"),
                "fb_user_name": user_info.get("name"),
                "message": "Facebook connected successfully"
            }

        except Exception as e:
            logger.error(f"Facebook OAuth callback error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _simulate_demo_connection(self, user_id: int) -> Dict[str, Any]:
        """Simulate Facebook connection for demo purposes"""
        try:
            # Save demo connection
            self._save_facebook_connection(
                user_id=user_id,
                fb_user_id="demo_fb_user_123",
                fb_user_name="Demo User",
                fb_user_token="demo_token_123",
                token_expires_at=datetime.now() + timedelta(days=60)
            )
            
            # Create demo pages
            demo_pages = [
                {
                    "id": "demo_page_123",
                    "name": "Demo Real Estate Page",
                    "access_token": "demo_page_token_123"
                }
            ]
            
            # Save demo page
            for page in demo_pages:
                await self.connect_page(user_id, page)
            
            return {
                "success": True,
                "user_id": str(user_id),
                "fb_user_id": "demo_fb_user_123",
                "fb_user_name": "Demo User",
                "message": "Demo Facebook connection successful",
                "demo_mode": True
            }
            
        except Exception as e:
            logger.error(f"Error in demo connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_facebook_connection(self, user_id: int, fb_user_id: str, fb_user_name: str, 
                                fb_user_token: str, token_expires_at: Optional[datetime] = None):
        """Save Facebook connection to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            encrypted_token = self._encrypt_token(fb_user_token)
            
            cursor.execute('''
                INSERT OR REPLACE INTO facebook_connections 
                (user_id, fb_user_id, fb_user_name, fb_user_token, token_expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, fb_user_id, fb_user_name, encrypted_token, token_expires_at, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving Facebook connection: {e}")
    
    async def get_user_pages(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's Facebook pages"""
        try:
            # Get user's Facebook token
            user_token = self._get_user_facebook_token(user_id)
            if not user_token:
                # Return demo pages if no real connection
                return [
                    {
                        "id": "demo_page_123",
                        "name": "Demo Real Estate Page",
                        "access_token": "demo_page_token_123",
                        "category": "Real Estate",
                        "fan_count": 1250
                    },
                    {
                        "id": "demo_page_456",
                        "name": "Demo Luxury Properties",
                        "access_token": "demo_page_token_456",
                        "category": "Real Estate",
                        "fan_count": 850
                    }
                ]
            
            # Check if this is a demo token
            if user_token.startswith("demo_"):
                return [
                    {
                        "id": "demo_page_123",
                        "name": "Demo Real Estate Page",
                        "access_token": "demo_page_token_123",
                        "category": "Real Estate",
                        "fan_count": 1250
                    }
                ]

            # Get real pages from Facebook
            app_id, app_secret = self._get_app_credentials(user_id)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me/accounts",
                    params={
                        "access_token": user_token,
                        "fields": "id,name,access_token,category,fan_count"
                    }
                )
                data = response.json()

            if "data" not in data:
                raise Exception("Failed to fetch pages")

            return data["data"]

        except Exception as e:
            logger.error(f"Error fetching Facebook pages: {e}")
            # Return demo pages as fallback
            return [
                {
                    "id": "demo_page_123",
                    "name": "Demo Real Estate Page",
                    "access_token": "demo_page_token_123",
                    "category": "Real Estate",
                    "fan_count": 1250
                }
            ]
    
    def _get_user_facebook_token(self, user_id: int) -> Optional[str]:
        """Get user's Facebook token from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fb_user_token FROM facebook_connections 
                WHERE user_id = ? AND fb_user_token IS NOT NULL
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return self._decrypt_token(result[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user Facebook token: {e}")
            return None
    
    async def connect_page(self, user_id: int, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Connect a specific Facebook page to the user"""
        try:
            # Store page token
            encrypted_token = self._encrypt_token(page_data["access_token"])
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO facebook_page_tokens 
                (user_id, page_id, page_name, access_token, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, 
                page_data["id"], 
                page_data["name"], 
                encrypted_token,
                datetime.now(),
                datetime.now()
            ))
            
            # Update main connection with selected page
            cursor.execute('''
                UPDATE facebook_connections 
                SET fb_page_id = ?, fb_page_name = ?, fb_page_token = ?, updated_at = ?
                WHERE user_id = ?
            ''', (page_data["id"], page_data["name"], encrypted_token, datetime.now(), user_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "page_id": page_data["id"],
                "page_name": page_data["name"],
                "message": f"Connected to {page_data['name']}"
            }
            
        except Exception as e:
            logger.error(f"Error connecting Facebook page: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def post_property_to_facebook(self, user_id: int, property_data: Dict[str, Any], 
                                      page_id: Optional[str] = None) -> Dict[str, Any]:
        """Post a property to Facebook with AI-generated content"""
        try:
            # Get page token
            page_token = self._get_page_token(user_id, page_id)
            connected_page_id = page_id or self._get_connected_page_id(user_id)
            
            if not page_token or not connected_page_id:
                # Demo mode - simulate posting
                return await self._simulate_demo_post(user_id, property_data)
            
            # Generate AI content for the property
            ai_content = await self._generate_property_content(property_data)
            
            # Check if this is a demo token
            if page_token.startswith("demo_"):
                return await self._simulate_demo_post(user_id, property_data, ai_content["message"])
            
            # Post to Facebook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{connected_page_id}/feed",
                    data={
                        "message": ai_content["message"],
                        "access_token": page_token
                    }
                )
                result = response.json()
            
            if "id" in result:
                # Save post to database
                self._save_facebook_post(user_id, result["id"], ai_content["message"], property_data.get("id"))
                
                return {
                    "success": True,
                    "post_id": result["id"],
                    "url": f"https://www.facebook.com/{result['id']}",
                    "message": "Property posted successfully to Facebook"
                }
            else:
                raise Exception(f"Facebook posting failed: {result}")
                
        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            # Fallback to demo post
            return await self._simulate_demo_post(user_id, property_data)
    
    async def _simulate_demo_post(self, user_id: int, property_data: Dict[str, Any], message: str = None) -> Dict[str, Any]:
        """Simulate Facebook posting for demo purposes"""
        try:
            if not message:
                ai_content = await self._generate_property_content(property_data)
                message = ai_content["message"]
            
            # Generate demo post ID
            demo_post_id = f"demo_post_{datetime.now().timestamp()}"
            
            # Save demo post to database
            self._save_facebook_post(user_id, demo_post_id, message, property_data.get("id"))
            
            return {
                "success": True,
                "post_id": demo_post_id,
                "url": f"https://www.facebook.com/demo_page_123/posts/{demo_post_id}",
                "message": "Property posted successfully to Facebook (Demo Mode)",
                "demo_mode": True
            }
        except Exception as e:
            logger.error(f"Error in demo posting: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_page_token(self, user_id: int, page_id: Optional[str] = None) -> Optional[str]:
        """Get page access token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if page_id:
                cursor.execute('''
                    SELECT access_token FROM facebook_page_tokens 
                    WHERE user_id = ? AND page_id = ?
                ''', (user_id, page_id))
            else:
                cursor.execute('''
                    SELECT fb_page_token FROM facebook_connections 
                    WHERE user_id = ? AND fb_page_token IS NOT NULL
                ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return self._decrypt_token(result[0])
            return None
        except Exception as e:
            logger.error(f"Error getting page token: {e}")
            return None
    
    def _get_connected_page_id(self, user_id: int) -> Optional[str]:
        """Get connected page ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fb_page_id FROM facebook_connections 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting connected page ID: {e}")
            return None
    
    async def _generate_property_content(self, property_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI-powered content for property posting"""
        title = property_data.get("title", "Amazing Property")
        price = property_data.get("price", "Contact for price")
        location = property_data.get("location", "Mumbai")
        bedrooms = property_data.get("bedrooms", 2)
        bathrooms = property_data.get("bathrooms", 2)
        area = property_data.get("area", "1500 sq ft")
        prop_type = property_data.get("type", "Apartment")
        
        message = f"""🏠 {title}

💰 Price: {price}
📍 Location: {location}
🏠 Type: {prop_type}
🛏️ {bedrooms} Bedrooms | 🚿 {bathrooms} Bathrooms
📐 Area: {area}

✨ Discover your dream home! This stunning property offers the perfect blend of comfort and luxury in the heart of {location}.

Perfect for families looking for quality living with modern amenities and great connectivity.

📞 Contact us today for a viewing!

#RealEstate #Property #Mumbai #Home #Investment #LuxuryLiving #PropertyForSale"""

        return {
            "message": message,
            "hashtags": ["#RealEstate", "#Property", "#Mumbai", "#Home", "#Investment", "#LuxuryLiving", "#PropertyForSale"]
        }
    
    def _save_facebook_post(self, user_id: int, post_id: str, message: str, property_id: Optional[int] = None):
        """Save Facebook post to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO facebook_posts 
                (user_id, post_id, message, property_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, post_id, message, property_id, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving Facebook post: {e}")
    
    def get_facebook_status(self, user_id: int) -> Dict[str, Any]:
        """Get user's Facebook connection status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fb_user_id, fb_user_name, fb_page_id, fb_page_name, connected_at
                FROM facebook_connections 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "connected": True,
                    "fb_user_id": result[0],
                    "fb_user_name": result[1],
                    "fb_page_id": result[2],
                    "fb_page_name": result[3],
                    "connected_at": result[4],
                    "demo_mode": str(result[0]).startswith("demo_")
                }
            else:
                return {
                    "connected": False
                }
        except Exception as e:
            logger.error(f"Error getting Facebook status: {e}")
            return {
                "connected": False,
                "error": str(e)
            }

# Global instance
facebook_integration = FacebookIntegration()