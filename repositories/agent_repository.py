"""
Simple in-memory agent repository for demo purposes.
This is a simplified version that doesn't rely on Redis.
"""

import json
from typing import Optional, List, Dict
from datetime import datetime
import uuid
from cryptography.fernet import Fernet
import base64
import os

from models.agent import AgentProfile, FacebookPage, FacebookOAuthState
from core.config import settings

class AgentRepository:
    def __init__(self):
        self.agent_profiles = {}
        self.facebook_pages = {}
        self.oauth_states = {}
        # Generate a proper Fernet key from SECRET_KEY
        key_material = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        self.cipher_suite = Fernet(base64.urlsafe_b64encode(key_material))
        
        # Add a demo agent
        demo_id = "demo-user-1"
        demo_agent = AgentProfile(
            user_id=demo_id,
            username="demo",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            profile_image_url="https://randomuser.me/api/portraits/men/1.jpg",
            bio="I'm a demo real estate agent in Mumbai with 5 years of experience.",
            specialization="Luxury Apartments",
            areas_served=["Mumbai", "Pune"],
            languages=["English", "Hindi", "Marathi"],
            facebook_connected=True
        )
        self.agent_profiles[demo_id] = demo_agent
        
        # Add a demo Facebook page
        demo_page = FacebookPage(
            page_id="demo-page-1",
            user_id=demo_id,
            name="Mumbai Luxury Properties",
            access_token="fake-token",
            category="Real Estate",
            connected_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.facebook_pages["demo-page-1"] = demo_page
    
    async def create_agent_profile(self, user_id: str, username: str) -> AgentProfile:
        now = datetime.utcnow()
        
        profile = AgentProfile(
            user_id=user_id,
            username=username,
            created_at=now,
            updated_at=now
        )
        
        self.agent_profiles[user_id] = profile
        
        return profile
    
    async def get_agent_profile(self, user_id: str) -> Optional[AgentProfile]:
        return self.agent_profiles.get(user_id)
    
    async def update_agent_profile(self, user_id: str, updates: dict) -> Optional[AgentProfile]:
        profile = await self.get_agent_profile(user_id)
        if not profile:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.utcnow()
        
        # Update in memory
        self.agent_profiles[user_id] = profile
        
        return profile
    
    async def connect_facebook_page(self, user_id: str, page_data: dict) -> Optional[AgentProfile]:
        """Connect a Facebook Page to the agent's profile"""
        profile = await self.get_agent_profile(user_id)
        if not profile:
            return None
        
        # Encrypt the page access token
        encrypted_token = self.cipher_suite.encrypt(page_data['access_token'].encode()).decode()
        
        facebook_page = FacebookPage(
            page_id=page_data['id'],
            user_id=user_id,
            name=page_data['name'],
            access_token=encrypted_token,
            category=page_data.get('category'),
            connected_at=datetime.utcnow()
        )
        
        # Store page
        self.facebook_pages[page_data['id']] = facebook_page
        
        # Update profile
        profile.facebook_connected = True
        profile.facebook_url = f"https://facebook.com/{page_data['id']}"
        profile.updated_at = datetime.utcnow()
        
        # Update in memory
        self.agent_profiles[user_id] = profile
        
        return profile
    
    async def get_page_access_token(self, user_id: str) -> Optional[str]:
        """Get decrypted page access token for posting"""
        # Find the page associated with this user
        for page in self.facebook_pages.values():
            if page.user_id == user_id:
                encrypted_token = page.access_token
                try:
                    return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
                except Exception:
                    return None
        return None
    
    async def store_oauth_state(self, state: str, user_id: str) -> FacebookOAuthState:
        """Store OAuth state for CSRF protection"""
        oauth_state = FacebookOAuthState(
            state=state,
            user_id=user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow().replace(minute=datetime.utcnow().minute + 10)  # 10 min expiry
        )
        
        # Store in memory
        self.oauth_states[state] = oauth_state
        
        return oauth_state
    
    async def verify_oauth_state(self, state: str) -> Optional[FacebookOAuthState]:
        """Verify and consume OAuth state"""
        oauth_state = self.oauth_states.get(state)
        
        if not oauth_state:
            return None
        
        # Delete after use (one-time)
        del self.oauth_states[state]
        
        # Check if expired
        if oauth_state.expires_at < datetime.utcnow():
            return None
        
        return oauth_state
    
    async def get_agent_by_username(self, username: str) -> Optional[AgentProfile]:
        """Get agent profile by username"""
        for profile in self.agent_profiles.values():
            if profile.username == username:
                return profile
        return None
    
    async def get_facebook_pages(self, user_id: str) -> List[FacebookPage]:
        """Get all Facebook pages connected to the user"""
        return [page for page in self.facebook_pages.values() if page.user_id == user_id]

# Dependency to get agent repository
async def get_agent_repository() -> AgentRepository:
    return AgentRepository()
