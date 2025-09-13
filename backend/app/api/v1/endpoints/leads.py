"""
Leads Endpoints
===============
Handles lead creation, retrieval, update, deletion, and statistics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List

from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.services.lead_service import LeadService
from app.repositories.lead_repository import LeadRepository

from app.core.exceptions import NotFoundError
from app.core.auth_backend import get_current_user_id

router = APIRouter()


def get_lead_service() -> LeadService:
    """Provide lead service with repository."""
    lead_repo = LeadRepository()
    return LeadService(lead_repo)


@router.get("/", response_model=List[LeadResponse])
async def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_id: str = Depends(get_current_user_id),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Get list of leads for the current agent."""
    return await lead_service.get_leads(agent_id, skip, limit)


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    agent_id: str = Depends(get_current_user_id),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Create a new lead."""
    return await lead_service.create_lead(lead_data, agent_id)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    agent_id: str = Depends(get_current_user_id),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Get detailed info about a specific lead."""
    try:
        return await lead_service.get_lead(lead_id, agent_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    agent_id: str = Depends(get_current_user_id),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Update lead information."""
    try:
        return await lead_service.update_lead(lead_id, lead_data, agent_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    agent_id: str = Depends(get_current_user_id),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Delete a lead."""
    try:
        success = await lead_service.delete_lead(lead_id, agent_id)
        if success:
            return {"message": "Lead deleted successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete lead")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stats/summary")
async def get_lead_stats(
    agent_id: str = Depends(get_current_user_id),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Get lead statistics summary for dashboard."""
    return await lead_service.get_lead_stats(agent_id)
