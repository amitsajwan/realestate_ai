
# ===== app/repositories/lead_repository.py =====
class LeadRepository(BaseRepository):
    def __init__(self):
        super().__init__("leads")
    
    async def find_by_agent(self, agent_id: str, skip: int = 0, limit: int = 100):
        """Find leads by agent ID"""
        return await self.find({"agent_id": agent_id}, skip=skip, limit=limit)
