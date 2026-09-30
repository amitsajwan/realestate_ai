"""GET /report/weekly (agent auth)."""
from fastapi import APIRouter, Depends

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from .service import ReportService

router = APIRouter()


@router.get("/weekly")
async def weekly(user: User = Depends(current_active_user)):
    return await ReportService(get_database()).weekly(str(user.id))
