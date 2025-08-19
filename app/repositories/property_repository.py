from typing import List, Dict, Any
from app.repositories.base_repository import BaseRepository


class PropertyRepository(BaseRepository):
    """Repository for property operations"""
    
    def __init__(self):
        super().__init__("properties")
    
    async def find_by_agent(self, agent_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Find properties by agent ID"""
        return await self.find({"agent_id": agent_id}, skip=skip, limit=limit)
    
    async def find_active_properties(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """Find active properties"""
        query = {"status": "active"}
        if agent_id:
            query["agent_id"] = agent_id
        return await self.find(query)
    
    async def get_property_stats(self, agent_id: str) -> Dict[str, int]:
        """Get property statistics for an agent"""
        query = {"agent_id": agent_id}
        total = await self.collection.count_documents(query)
        active = await self.collection.count_documents({**query, "status": "active"})
        sold = await self.collection.count_documents({**query, "status": "sold"})
        pending = await self.collection.count_documents({**query, "status": "pending"})
        
        return {
            "total": total,
            "active": active,
            "sold": sold,
            "pending": pending
        }