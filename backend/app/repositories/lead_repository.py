from typing import List, Dict, Any
from app.repositories.base_repository import BaseRepository


class LeadRepository(BaseRepository):
    """Repository for lead operations"""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.debug("LeadRepository initialized")
        super().__init__("leads")
    
    async def find_by_agent(self, agent_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        self.logger.debug(f"Finding leads for agent: {agent_id}, skip: {skip}, limit: {limit}")
        """Find leads by agent ID"""
        return await self.find({"agent_id": agent_id}, skip=skip, limit=limit)
    
    async def get_lead_stats(self, agent_id: str) -> Dict[str, int]:
        self.logger.info(f"Getting lead stats for agent: {agent_id}")
        """Get lead statistics for an agent"""
        query = {"agent_id": agent_id}
        total = await self.collection.count_documents(query)
        
        hot_leads = await self.collection.count_documents({**query, "status": "hot"})
        warm_leads = await self.collection.count_documents({**query, "status": "warm"})
        cold_leads = await self.collection.count_documents({**query, "status": "cold"})
        new_leads = await self.collection.count_documents({**query, "status": "new"})
        
        return {
            "total": total,
            "hot": hot_leads,
            "warm": warm_leads,
            "cold": cold_leads,
            "new": new_leads
        }