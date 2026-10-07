"""GET /engage/comments: the signed-in agent's Facebook and Instagram comment activity (interest on their listings). Read-only, owner scoped."""
from typing import List

from fastapi import APIRouter, Depends

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

router = APIRouter()

SAFE = ("channel", "post_id", "listing_id", "from_name", "text", "intent", "language", "status", "reply", "needs_human", "reason", "created_time", "permalink")


def _state(d) -> dict:
    if not d:
        return {"ok": True, "reconnect": False, "checked_at": None}
    return {"ok": bool(d.get("ok")), "reconnect": bool(d.get("reconnect")), "checked_at": d.get("checked_at")}


@router.get("/status")
async def status(user: User = Depends(current_active_user)) -> dict:
    """Is the Meta connection working? `reconnect` means the token was rejected and the owner must reconnect (scripts/meta_connect.ps1).
    Top-level fields are Facebook's; `instagram` is present once that channel has been checked."""
    coll = get_database().get_collection("engage_status")
    out = _state(await coll.find_one({"_id": "facebook"}))
    ig = await coll.find_one({"_id": "instagram"})
    if ig:
        out["instagram"] = _state(ig)
    return out


@router.get("/comments")
async def my_comments(limit: int = 50, user: User = Depends(current_active_user)) -> List[dict]:
    limit = max(1, min(limit, 100))
    docs = await get_database().get_collection("engage_comments").find(
        {"agent_id": str(user.id), "reason": {"$not": {"$regex": "^own comment"}}}).sort("processed_at", -1).limit(limit).to_list(limit)  # our own comments are noise
    return [{"id": d["_id"], **{k: d.get(k) for k in SAFE}, "channel": d.get("channel") or "facebook"} for d in docs]
