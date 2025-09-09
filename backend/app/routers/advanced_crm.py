#!/usr/bin/env python3
"""
Advanced CRM Router
==================
Enhanced CRM endpoints with lead management, analytics, and team collaboration
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.lead import (
    LeadCreate, LeadUpdate, LeadResponse, LeadStats, LeadSearchFilters,
    LeadSearchResult, LeadStatus, LeadUrgency, LeadSource
)
from app.schemas.analytics import AnalyticsFilter, DashboardMetrics, AnalyticsPeriod
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamInvitation
from app.services.lead_management_service import LeadManagementService
from app.services.analytics_service import AnalyticsService
from app.services.team_management_service import TeamManagementService
from app.core.database import get_database
from app.utils import verify_token

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to get services
async def get_lead_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> LeadManagementService:
    return LeadManagementService(db)

async def get_analytics_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AnalyticsService:
    return AnalyticsService(db)

async def get_team_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> TeamManagementService:
    return TeamManagementService(db)

# Lead Management Endpoints
@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    request: Request,
    lead_service: LeadManagementService = Depends(get_lead_service)
):
    """Create a new lead with automatic scoring"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        agent_id = user_info.get("user_id")
        team_id = user_info.get("team_id")
        
        if not agent_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Create lead
        lead = await lead_service.create_lead(lead_data, agent_id, team_id)
        
        return lead
        
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads", response_model=LeadSearchResult)
async def search_leads(
    request: Request,
    status: Optional[LeadStatus] = Query(None),
    urgency: Optional[LeadUrgency] = Query(None),
    source: Optional[LeadSource] = Query(None),
    search_term: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    lead_service: LeadManagementService = Depends(get_lead_service)
):
    """Search leads with filters"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        agent_id = user_info.get("user_id")
        
        if not agent_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Build filters
        filters = LeadSearchFilters(
            status=status,
            urgency=urgency,
            source=source,
            search_term=search_term
        )
        
        # Search leads
        result = await lead_service.search_leads(filters, agent_id, page, per_page)
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    request: Request,
    lead_service: LeadManagementService = Depends(get_lead_service)
):
    """Get lead by ID"""
    try:
        # Verify token
        user_info = await verify_token(request)
        if not user_info.get("user_id"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get lead
        lead = await lead_service.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return lead
        
    except Exception as e:
        logger.error(f"Error getting lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    update_data: LeadUpdate,
    request: Request,
    lead_service: LeadManagementService = Depends(get_lead_service)
):
    """Update lead"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        agent_id = user_info.get("user_id")
        
        if not agent_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Update lead
        lead = await lead_service.update_lead(lead_id, update_data, agent_id)
        
        return lead
        
    except Exception as e:
        logger.error(f"Error updating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/stats", response_model=LeadStats)
async def get_lead_stats(
    request: Request,
    lead_service: LeadManagementService = Depends(get_lead_service)
):
    """Get lead statistics"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        agent_id = user_info.get("user_id")
        team_id = user_info.get("team_id")
        
        if not agent_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get stats
        stats = await lead_service.get_lead_stats(agent_id, team_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting lead stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@router.get("/analytics/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    request: Request,
    period: AnalyticsPeriod = Query(AnalyticsPeriod.THIS_MONTH),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive dashboard metrics"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        agent_id = user_info.get("user_id")
        team_id = user_info.get("team_id")
        
        if not agent_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date).date()
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date).date()
        
        # Build filters
        filters = AnalyticsFilter(
            period=period,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        # Get metrics
        metrics = await analytics_service.get_dashboard_metrics(agent_id, team_id, filters)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Team Management Endpoints
@router.post("/teams", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    request: Request,
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Create a new team"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        user_id = user_info.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Create team
        team = await team_service.create_team(team_data, user_id)
        
        return team
        
    except Exception as e:
        logger.error(f"Error creating team: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    request: Request,
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Get team by ID"""
    try:
        # Verify token
        user_info = await verify_token(request)
        if not user_info.get("user_id"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get team
        team = await team_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return team
        
    except Exception as e:
        logger.error(f"Error getting team: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    update_data: TeamUpdate,
    request: Request,
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Update team"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        user_id = user_info.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Update team
        team = await team_service.update_team(team_id, update_data, user_id)
        
        return team
        
    except Exception as e:
        logger.error(f"Error updating team: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teams/{team_id}/invite")
async def invite_member(
    team_id: str,
    invitation: TeamInvitation,
    request: Request,
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Invite member to team"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        user_id = user_info.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Invite member
        result = await team_service.invite_member(team_id, invitation, user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error inviting member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teams/invitations/{invitation_token}/accept")
async def accept_invitation(
    invitation_token: str,
    request: Request,
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Accept team invitation"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        user_id = user_info.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Accept invitation
        team = await team_service.accept_invitation(invitation_token, user_id)
        
        return team
        
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/teams/{team_id}/members/{member_id}")
async def remove_member(
    team_id: str,
    member_id: str,
    request: Request,
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Remove member from team"""
    try:
        # Verify token and get user info
        user_info = await verify_token(request)
        user_id = user_info.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Remove member
        success = await team_service.remove_member(team_id, member_id, user_id)
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}/stats")
async def get_team_stats(
    team_id: str,
    request: Request,
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Get team statistics"""
    try:
        # Verify token
        user_info = await verify_token(request)
        if not user_info.get("user_id"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get stats
        stats = await team_service.get_team_stats(team_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting team stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}/audit-logs")
async def get_audit_logs(
    team_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    team_service: TeamManagementService = Depends(get_team_service)
):
    """Get team audit logs"""
    try:
        # Verify token
        user_info = await verify_token(request)
        if not user_info.get("user_id"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get audit logs
        logs = await team_service.get_audit_logs(team_id, limit, offset)
        
        return logs
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))