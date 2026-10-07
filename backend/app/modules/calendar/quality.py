"""What the quality review checks for a calendar post; passed to the quality route by app/wiring.py."""
from fastapi import HTTPException

from app.modules.photoquality import targets

from .config import load
from .store import COLLECTION


async def review_target(item_id: str, user, db) -> tuple:
    """(image paths, context) of a calendar post. Only the calendar owner (or a superuser) may review it."""
    if not (getattr(user, "is_superuser", False) or str(user.id) in load().owner_ids):
        raise HTTPException(403, "Only the owner can review calendar posts")
    doc = await db.get_collection(COLLECTION).find_one({"_id": item_id})
    if not doc:
        raise HTTPException(404, "Item not found")
    return targets.calendar_target(doc)
