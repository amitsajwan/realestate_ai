from typing import Optional, Dict, Any
from datetime import datetime
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    """Repository for user operations"""
    
    def __init__(self):
        super().__init__("users")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            document = await self.collection.find_one({"email": email.lower()})
            return self._format_document(document) if document else None
        except Exception as e:
            logger.error(f"Get by email error: {e}")
            raise
    
    async def update_facebook_info(self, user_id: str, facebook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's Facebook information"""
        return await self.update(user_id, {
            **facebook_data,
            "facebook_connected": True,
            "fb_connected_at": datetime.utcnow()
        })
    
    async def disconnect_facebook(self, user_id: str) -> Dict[str, Any]:
        """Disconnect Facebook from user account"""
        return await self.update(user_id, {
            "facebook_connected": False,
            "fb_user_token": None,
            "fb_page_id": None,
            "fb_page_name": None,
            "fb_page_token": None,
            "fb_disconnected_at": datetime.utcnow()
        })