"""GET /engage/status: is the Meta connection working. (The comments themselves are in the Inbox, /conversations, since 2026-10-17.)"""
from fastapi import APIRouter, Depends

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

router = APIRouter()


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
