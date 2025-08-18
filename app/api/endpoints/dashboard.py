from fastapi import APIRouter, Depends, Request
from services.dashboard_service import DashboardService
from utils.db_client import get_db_client

router = APIRouter()

@router.get("/dashboard/metrics")
async def dashboard_metrics(request: Request, db=Depends(get_db_client)):
    agent_id = request.session.get("agent_id")
    svc = DashboardService(db)
    metrics = svc.fetch_metrics(agent_id)
    return metrics

@router.get("/dashboard/lead-stats")
async def dashboard_lead_stats(request: Request, db=Depends(get_db_client)):
    agent_id = request.session.get("agent_id")
    svc = DashboardService(db)
    stats = svc.fetch_lead_stats(agent_id)
    return stats
