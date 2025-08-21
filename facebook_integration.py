#!/usr/bin/env python3
"""
Enhanced Facebook Integration for PropertyAI
============================================

This module provides comprehensive Facebook integration including:
- OAuth flow for connecting Facebook accounts
- Page management and selection
- Long-term token storage and refresh
- AI-powered content posting
- Property listing automation
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
        self.base_url = "https://graph.facebook.com/v19.0"
        
        # Initialize encryption for token storage
        self._setup_encryption()
        
        # Create Facebook tables if they don't exist
        self._create_facebook_tables()
    
    def _setup_encryption(self):
        """Setup encryption for secure token storage"""
        # Generate or load encryption key
        key_file = "facebook_key.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
        
        self.cipher = Fernet(key)
    
    def _create_facebook_tables(self):
        """Create Facebook-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Facebook connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facebook_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                fb_user_id VARCHAR(255),
                fb_user_name VARCHAR(255),
                fb_user_token TEXT,  -- Encrypted
                fb_page_id VARCHAR(255),
                fb_page_name VARCHAR(255),
                fb_page_token TEXT,  -- Encrypted
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
                engagement_data TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Facebook page tokens table for long-term storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facebook_page_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                page_id VARCHAR(255),
                page_name VARCHAR(255),
                access_token TEXT,  -- Encrypted
                token_type VARCHAR(50) DEFAULT 'page',
                expires_at TIMESTAMP,
                permissions TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        return self.cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token for use"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    def get_oauth_url(self, user_id: str, redirect_uri: str) -> str:
        """Generate Facebook OAuth URL"""
        if not self.client_id:
            raise Exception("Facebook App ID not configured")
        
        # Generate secure state parameter
        state = f"{user_id}:{secrets.token_urlsafe(32)}"
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,public_profile,email",
            "response_type": "code"
        }
        
        return f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
    
    async def handle_oauth_callback(self, code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle Facebook OAuth callback and exchange code for tokens"""
        try:
            # Extract user ID from state
            if ":" not in state:
                raise Exception("Invalid state parameter")
            
            user_id = state.split(":")[0]
            
            # Exchange code for access token
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    f"{self.base_url}/oauth/access_token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": redirect_uri,
                        "code": code
                    }
                )
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
            self._save_facebook_connection(
                user_id=int(user_id),
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
    
    def _save_facebook_connection(self, user_id: int, fb_user_id: str, fb_user_name: str, 
                                fb_user_token: str, token_expires_at: Optional[datetime] = None):
        """Save Facebook connection to database"""
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
    
    async def get_user_pages(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's Facebook pages"""
        try:
            # Get user's Facebook token
            user_token = self._get_user_facebook_token(user_id)
            if not user_token:
                raise Exception("Facebook not connected")

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
            raise Exception(f"Failed to fetch pages: {str(e)}")
    
    def _get_user_facebook_token(self, user_id: int) -> Optional[str]:
        """Get user's Facebook token from database"""
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
            if not page_token:
                raise Exception("No Facebook page connected")
            
            # Generate AI content for the property
            ai_content = await self._generate_property_content(property_data)
            
            # Post to Facebook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{page_id or self._get_connected_page_id(user_id)}/feed",
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
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_page_token(self, user_id: int, page_id: Optional[str] = None) -> Optional[str]:
        """Get page access token"""
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
    
    def _get_connected_page_id(self, user_id: int) -> Optional[str]:
        """Get connected page ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fb_page_id FROM facebook_connections 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    async def _generate_property_content(self, property_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI-powered content for property posting"""
        # This can be enhanced with actual AI integration
        title = property_data.get("title", "Amazing Property")
        price = property_data.get("price", "Contact for price")
        location = property_data.get("location", "Mumbai")
        bedrooms = property_data.get("bedrooms", 2)
        bathrooms = property_data.get("bathrooms", 2)
        area = property_data.get("area", "1500 sq ft")
        
        message = f"""🏠 {title}

💰 Price: {price}
📍 Location: {location}
🛏️ {bedrooms} Bedrooms | 🚿 {bathrooms} Bathrooms
📏 Area: {area}

✨ Discover your dream home! This stunning property offers the perfect blend of comfort and luxury.

#RealEstate #Property #Mumbai #Home #Investment #LuxuryLiving"""

        return {
            "message": message,
            "hashtags": ["#RealEstate", "#Property", "#Mumbai", "#Home", "#Investment", "#LuxuryLiving"]
        }
    
    def _save_facebook_post(self, user_id: int, post_id: str, message: str, property_id: Optional[int] = None):
        """Save Facebook post to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO facebook_posts 
            (user_id, post_id, message, property_id, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, post_id, message, property_id, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_facebook_status(self, user_id: int) -> Dict[str, Any]:
        """Get user's Facebook connection status"""
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
                "connected_at": result[4]
            }
        else:
            return {
                "connected": False
            }

# Global instance
facebook_integration = FacebookIntegration()
