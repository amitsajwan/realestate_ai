"""Easy plug-in integration layer for MongoDB repositories."""
import os
from repositories.facebook_repository import FacebookRepository
from repositories.smart_property_repository import SmartPropertyRepository

# Global repository instances
_facebook_repo = None
_smart_property_repo = None

def get_facebook_repository():
    """Get Facebook repository singleton."""
    global _facebook_repo
    if _facebook_repo is None:
        _facebook_repo = FacebookRepository()
    return _facebook_repo

def get_smart_property_repository():
    """Get Smart Property repository singleton."""
    global _smart_property_repo
    if _smart_property_repo is None:
        _smart_property_repo = SmartPropertyRepository()
    return _smart_property_repo

# Feature flag for easy switching
USE_MONGODB = os.getenv("USE_MONGODB", "true").lower() == "true"

class StorageManager:
    """Unified storage manager that can switch between in-memory and MongoDB."""
    
    def __init__(self):
        self.use_mongodb = USE_MONGODB
        
        if self.use_mongodb:
            self.facebook_repo = get_facebook_repository()
            self.property_repo = get_smart_property_repository()
        else:
            # Fallback to in-memory storage
            self.facebook_connections = {}
            self.smart_properties = []
    
    async def save_facebook_connection(self, user_email: str, data: dict):
        """Save Facebook connection."""
        if self.use_mongodb:
            return await self.facebook_repo.save_connection(user_email, data)
        else:
            self.facebook_connections[user_email] = data
            return True
    
    async def get_facebook_connection(self, user_email: str):
        """Get Facebook connection."""
        if self.use_mongodb:
            return await self.facebook_repo.get_connection(user_email)
        else:
            return self.facebook_connections.get(user_email)
    
    async def create_smart_property(self, property_data: dict, user_email: str):
        """Create smart property."""
        if self.use_mongodb:
            return await self.property_repo.create_property(property_data, user_email)
        else:
            prop_id = str(len(self.smart_properties) + 1)
            property_data['id'] = prop_id
            property_data['user_email'] = user_email
            self.smart_properties.append(property_data)
            return prop_id
    
    async def get_smart_properties(self, user_email: str):
        """Get smart properties."""
        if self.use_mongodb:
            return await self.property_repo.get_properties(user_email)
        else:
            return [p for p in self.smart_properties if p.get('user_email') == user_email]

# Global storage manager instance
storage = StorageManager()
