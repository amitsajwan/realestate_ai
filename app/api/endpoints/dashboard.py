from fastapi import APIRouter, Depends, Request
from app.services.dashboard_service import DashboardService
from app.core.database import get_database

router = APIRouter()

async def get_dashboard_service():
    """Get dashboard service instance"""
    db = await get_database()
    return DashboardService(db)

@router.get("/dashboard/metrics")
async def dashboard_metrics(
    request: Request, 
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get dashboard metrics"""
    # For now, get agent_id from session or use a default
    # In production, this should come from authenticated user
    agent_id = request.session.get("agent_id", "default_agent")
    
    metrics = dashboard_service.fetch_metrics(agent_id)
    return metrics

@router.get("/dashboard/lead-stats")
async def dashboard_lead_stats(
    request: Request, 
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get dashboard lead statistics"""
    # For now, get agent_id from session or use a default
    # In production, this should come from authenticated user
    agent_id = request.session.get("agent_id", "default_agent")
    
    stats = dashboard_service.fetch_lead_stats(agent_id)
    return stats