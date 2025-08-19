class PropertyRepository(BaseRepository):
    def __init__(self):
        super().__init__("properties")
    
    async def find_by_agent(self, agent_id: str, skip: int = 0, limit: int = 100):
        """Find properties by agent ID"""
        return await self.find({"agent_id": agent_id}, skip=skip, limit=limit)
    
    async def find_active_properties(self, agent_id: str = None):
        """Find active properties"""
        query = {"status": "active"}
        if agent_id:
            query["agent_id"] = agent_id
        return await self.find(query)