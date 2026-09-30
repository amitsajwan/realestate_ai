"""GET /engage/comments: the signed-in agent's Facebook comment activity (interest on their listings). Read-only, owner scoped."""
from typing import List

from fastapi import APIRouter, Depends

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

router = APIRouter()

SAFE = ("post_id", "listing_id", "from_name", "text", "intent", "language", "status", "reply", "needs_human", "reason", "created_time", "permalink")


@router.get("/status")
async def status(user: User = Depends(current_active_user)) -> dict:
    """Is the Facebook connection working? `reconnect` means the token was rejected and the owner must reconnect (scripts/meta_connect.ps1)."""
    d = await get_database().get_collection("engage_status").find_one({"_id": "facebook"})
    if not d:
        return {"ok": True, "reconnect": False, "checked_at": None}
    return {"ok": bool(d.get("ok")), "reconnect": bool(d.get("reconnect")), "checked_at": d.get("checked_at")}


@router.get("/comments")
async def my_comments(limit: int = 50, user: User = Depends(current_active_user)) -> List[dict]:
    limit = max(1, min(limit, 100))
    docs = await get_database().get_collection("engage_comments").find({"agent_id": str(user.id)}).sort("processed_at", -1).limit(limit).to_list(limit)
    return [{"id": d["_id"], **{k: d.get(k) for k in SAFE}} for d in docs]
