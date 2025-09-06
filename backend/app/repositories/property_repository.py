from typing import List, Dict, Any
from app.repositories.base_repository import BaseRepository
from app.schemas.unified_property import PropertyDocument, PropertyCreate, PropertyUpdate


class PropertyRepository(BaseRepository):
    """Repository for property operations"""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.debug("PropertyRepository initialized")
        super().__init__("properties")
    
    async def find_by_agent(self, agent_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        self.logger.debug(f"Finding properties for agent: {agent_id}, skip: {skip}, limit: {limit}")
        """Find properties by agent ID"""
        return await self.find({"agent_id": agent_id}, skip=skip, limit=limit)
    
    async def find_active_properties(self, agent_id: str = None) -> List[Dict[str, Any]]:
        self.logger.info(f"Finding active properties for agent: {agent_id}")
        """Find active properties"""
        query = {"status": "active"}
        if agent_id:
            query["agent_id"] = agent_id
        return await self.find(query)
    
    async def get_property_stats(self, agent_id: str) -> Dict[str, int]:
        self.logger.info(f"Getting property stats for agent: {agent_id}")
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