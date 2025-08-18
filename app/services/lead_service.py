"""
Lead Service
============
Business logic for lead management.
"""
from typing import List
from datetime import datetime

from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class LeadService:
    """Service layer for lead-related business logic."""

    def __init__(self, lead_repository: LeadRepository):
        self.lead_repository = lead_repository

    async def create_lead(self, lead_data: LeadCreate, agent_id: str) -> LeadResponse:
        lead_dict = lead_data.model_dump()
        lead_dict.update({
            "agent_id": agent_id,
            "status": "new",
            "score": 75,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        lead = await self.lead_repository.create(lead_dict)
        logger.info(f"Lead created for agent {agent_id}: {lead['id']}")
        return LeadResponse(**lead)

    async def get_leads(self, agent_id: str, skip: int = 0, limit: int = 100) -> List[LeadResponse]:
        query = {"agent_id": agent_id}
        leads = await self.lead_repository.find(query, skip=skip, limit=limit)
        return [LeadResponse(**lead) for lead in leads]

    async def get_lead(self, lead_id: str, agent_id: str) -> LeadResponse:
        lead = await self.lead_repository.get_by_id(lead_id)
        if not lead or lead.get("agent_id") != agent_id:
            raise NotFoundError("Lead not found")
        return LeadResponse(**lead)

    async def update_lead(self, lead_id: str, lead_data: LeadUpdate, agent_id: str) -> LeadResponse:
        existing_lead = await self.lead_repository.get_by_id(lead_id)
        if not existing_lead or existing_lead.get("agent_id") != agent_id:
            raise NotFoundError("Lead not found")

        update_data = lead_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        updated_lead = await self.lead_repository.update(lead_id, update_data)
        return LeadResponse(**updated_lead)

    async def delete_lead(self, lead_id: str, agent_id: str) -> bool:
        existing_lead = await self.lead_repository.get_by_id(lead_id)
        if not existing_lead or existing_lead.get("agent_id") != agent_id:
            raise NotFoundError("Lead not found")
        return await self.lead_repository.delete(lead_id)

    async def get_lead_stats(self, agent_id: str) -> dict:
        leads = await self.lead_repository.find({"agent_id": agent_id})
        total = len(leads)
        hot_leads = len([l for l in leads if l.get("status") == "hot"])
        warm_leads = len([l for l in leads if l.get("status") == "warm"])
        cold_leads = len([l for l in leads if l.get("status") == "cold"])

        conversion_rate = (hot_leads / total * 100) if total > 0 else 0

        return {
            "total": total,
            "hot": hot_leads,
            "warm": warm_leads,
            "cold": cold_leads,
            "conversion_rate": conversion_rate,
        }
