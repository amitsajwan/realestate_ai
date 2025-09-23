from fastapi import APIRouter, Depends, Request
from app.services.dashboard_service import DashboardService
from app.core.database import get_database
from app.core.auth_backend import current_active_user
from app.models.user import User

router = APIRouter()

async def get_dashboard_service():
    """Get dashboard service instance"""
    db = get_database()
    return DashboardService(db)

@router.get("/dashboard/metrics")
async def dashboard_metrics(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(current_active_user)
):
    """Get dashboard metrics"""
    # Use the authenticated user's ID
    agent_id = str(current_user.id)
    
    metrics = await dashboard_service.fetch_metrics(agent_id)
    return metrics

@router.get("/dashboard/lead-stats")
async def dashboard_lead_stats(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(current_active_user)
):
    """Get dashboard lead statistics"""
    # Use the authenticated user's ID
    agent_id = str(current_user.id)
    
    stats = await dashboard_service.fetch_lead_stats(agent_id)
    return stats