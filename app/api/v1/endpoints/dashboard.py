"""
Dashboard Endpoints
===================
Provides analytics and summary data for the user dashboard.
"""
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user_id
from app.services.dashboard_service import DashboardService
from app.repositories.user_repository import UserRepository

router = APIRouter()


def get_dashboard_service() -> DashboardService:
    user_repo = UserRepository()
    return DashboardService(user_repo)


@router.get("/summary")
async def get_user_summary(
    user_id: str = Depends(get_current_user_id),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get summary stats for the user dashboard,
    such as counts of leads, properties, hot leads, and Facebook connection status.
    """
    return await dashboard_service.get_user_summary(user_id)
