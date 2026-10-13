"""Studio → Newsroom → Insights → System (docs/plan/insights-and-seo.md O6). Here, not in a module: it reads the worker's loop list."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.models.user import User
from app.modules.areastats import owner
from app.modules.newsroom.router import get_store, owner_only
from app.modules.newsroom.store import Store

router = APIRouter()


@router.get("/insights/system")
async def insights_system(user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    """Every background loop's last good cycle and failure, the register's report and Serper credits left."""
    from app.worker import expected_intervals
    return await owner.system(store, datetime.now(timezone.utc), expected_intervals())
