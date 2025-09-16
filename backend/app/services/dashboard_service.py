from datetime import datetime

class DashboardService:
    def __init__(self, db):
        self.db = db

    async def fetch_metrics(self, agent_id):
        listings = await self.db.properties.count_documents({"agent_id": agent_id, "status": "active"})
        leads = await self.db.leads.count_documents({"agent_id": agent_id})
        gen_ai_pages = await self.db.properties.count_documents({"agent_id": agent_id, "ai_landing": True})
        whatsapp_contacts = await self.db.whatsapp_logs.count_documents({"agent_id": agent_id})
        return {
            "active_listings": listings,
            "total_leads": leads,
            "ai_pages": gen_ai_pages,
            "whatsapp_engagement": whatsapp_contacts
        }

    async def fetch_lead_stats(self, agent_id):
        new_leads = await self.db.leads.count_documents({
            "agent_id": agent_id,
            "created_at": {"$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)}
        })
        conversions = await self.db.leads.count_documents({
            "agent_id": agent_id,
            "status": "converted"
        })
        return {"new_leads": new_leads, "conversions": conversions}
