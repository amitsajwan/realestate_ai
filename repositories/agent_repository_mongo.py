"""
Mongo-backed AgentRepository implementation for real users.
Uses Fernet encryption for page access tokens.
"""
from __future__ import annotations
from typing import Optional, List
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet

from models.agent import AgentProfile, FacebookPage, FacebookOAuthState
from core.config import settings


class AgentRepositoryMongo:
    def __init__(self):
        # Lazy import to avoid forcing Mongo on environments that don't need it
        from db_adapter import get_db_connection
        self.db = get_db_connection()
        key_material = settings.SECRET_KEY.encode()[:32].ljust(32, b"0")
        self.cipher = Fernet(base64.urlsafe_b64encode(key_material))

    # --- Profiles ---
    async def create_agent_profile(self, user_id: str, username: str) -> AgentProfile:
        now = datetime.utcnow()
        profile = AgentProfile(
            user_id=user_id,
            username=username,
            created_at=now,
            updated_at=now,
        )
        self.db.agent_profiles.update_one(
            {"user_id": user_id},
            {"$set": profile.model_dump()},
            upsert=True,
        )
        return profile

    async def get_agent_profile(self, user_id: str) -> Optional[AgentProfile]:
        doc = self.db.agent_profiles.find_one({"user_id": user_id})
        if not doc:
            return None
        # Convert connected_page if present
        cp = doc.get("connected_page")
        connected_page = FacebookPage(**cp) if cp else None
        return AgentProfile(
            user_id=doc["user_id"],
            username=doc.get("username", ""),
            brand_name=doc.get("brand_name"),
            tagline=doc.get("tagline"),
            bio=doc.get("bio"),
            website=doc.get("website"),
            email=doc.get("email"),
            phone=doc.get("phone"),
            location=doc.get("location"),
            facebook_url=doc.get("facebook_url"),
            instagram_url=doc.get("instagram_url"),
            linkedin_url=doc.get("linkedin_url"),
            connected_page=connected_page,
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )

    async def update_agent_profile(self, user_id: str, updates: dict) -> Optional[AgentProfile]:
        updates = {k: v for k, v in updates.items() if v is not None}
        updates["updated_at"] = datetime.utcnow()
        self.db.agent_profiles.update_one({"user_id": user_id}, {"$set": updates}, upsert=True)
        return await self.get_agent_profile(user_id)

    # --- Pages ---
    async def connect_facebook_page(self, user_id: str, page_data: dict) -> Optional[AgentProfile]:
        token_enc = self.cipher.encrypt(page_data["access_token"].encode()).decode()
        page = FacebookPage(
            page_id=page_data["id"],
            user_id=user_id,
            name=page_data["name"],
            access_token=token_enc,
            category=page_data.get("category"),
            connected_at=datetime.utcnow(),
        )
        self.db.facebook_pages.update_one(
            {"page_id": page.page_id},
            {"$set": page.model_dump()},
            upsert=True,
        )
        await self.update_agent_profile(
            user_id,
            {
                "facebook_connected": True,
                "facebook_url": f"https://facebook.com/{page.page_id}",
                "connected_page": page.model_dump(),
            },
        )
        return await self.get_agent_profile(user_id)

    async def get_page_access_token(self, user_id: str) -> Optional[str]:
        prof = await self.get_agent_profile(user_id)
        if not prof or not prof.connected_page:
            return None
        try:
            return self.cipher.decrypt(prof.connected_page.access_token.encode()).decode()
        except Exception:
            return None

    async def get_connected_page(self, user_id: str) -> Optional[FacebookPage]:
        prof = await self.get_agent_profile(user_id)
        return prof.connected_page if prof else None

    async def get_facebook_pages(self, user_id: str) -> List[FacebookPage]:
        cur = self.db.facebook_pages.find({"user_id": user_id})
        return [FacebookPage(**d) for d in cur]

    # --- OAuth State ---
    async def store_oauth_state(self, state: str, user_id: str) -> FacebookOAuthState:
        now = datetime.utcnow()
        oauth_state = FacebookOAuthState(
            state=state,
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(minutes=10),
        )
        self.db.oauth_states.update_one(
            {"state": state},
            {"$set": oauth_state.model_dump()},
            upsert=True,
        )
        return oauth_state

    async def verify_oauth_state(self, state: str) -> Optional[FacebookOAuthState]:
        doc = self.db.oauth_states.find_one({"state": state})
        if not doc:
            return None
        self.db.oauth_states.delete_one({"state": state})
        try:
            if doc["expires_at"] < datetime.utcnow():
                return None
        except Exception:
            pass
        return FacebookOAuthState(**doc)

    async def get_agent_by_username(self, username: str) -> Optional[AgentProfile]:
        doc = self.db.agent_profiles.find_one({"username": username})
        if not doc:
            return None
        return await self.get_agent_profile(doc["user_id"])
