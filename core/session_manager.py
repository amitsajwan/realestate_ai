"""
Simple in-memory session manager for demo purposes.
This is a simplified version that doesn't rely on Redis.
"""

import json
from typing import Dict, Optional
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    async def get_redis(self):
        # No Redis, just return self
        return self
    
    async def create_session(self, client_id: str, user_id: str, session_data: dict = None) -> str:
        """Create a new session for a client"""
        session = {
            "client_id": client_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "data": session_data or {},
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        # Store session
        self.sessions[f"session:{client_id}"] = json.dumps(session)
        
        return client_id
    
    async def get_session(self, client_id: str) -> Optional[dict]:
        """Get session data for a client"""
        session_key = f"session:{client_id}"
        session_data = self.sessions.get(session_key)
        
        if not session_data:
            return None
        
        # Check if session is expired
        session = json.loads(session_data)
        expires_at = datetime.fromisoformat(session["expires_at"])
        if expires_at < datetime.utcnow():
            # Delete expired session
            del self.sessions[session_key]
            return None
        
        return session
    
    async def update_session(self, client_id: str, data: dict):
        """Update session data"""
        session = await self.get_session(client_id)
        
        if not session:
            return False
        
        session["data"].update(data)
        session["last_activity"] = datetime.utcnow().isoformat()
        session["expires_at"] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        # Update session
        self.sessions[f"session:{client_id}"] = json.dumps(session)
        
        return True
    
    async def delete_session(self, client_id: str):
        """Delete a session"""
        session_key = f"session:{client_id}"
        if session_key in self.sessions:
            del self.sessions[session_key]
    
    async def extend_session(self, client_id: str):
        """Extend session expiration"""
        session = await self.get_session(client_id)
        
        if not session:
            return False
        
        session["last_activity"] = datetime.utcnow().isoformat()
        session["expires_at"] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        # Update session
        self.sessions[f"session:{client_id}"] = json.dumps(session)
        
        return True

# Global session manager instance
session_manager = SessionManager()
