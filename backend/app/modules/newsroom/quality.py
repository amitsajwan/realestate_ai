"""What the quality review checks for a news post; passed to the quality route by app/wiring.py."""
from fastapi import HTTPException

from app.modules.photoquality import targets

from .config import load
from .store import ITEMS


async def review_target(item_id: str, user, db) -> tuple:
    """(image paths, context) of a news item. Only the newsroom owner (or a superuser) may review it."""
    if not (getattr(user, "is_superuser", False) or str(user.id) in load().owner_ids):
        raise HTTPException(403, "Only the owner can review news posts")
    doc = await db.get_collection(ITEMS).find_one({"_id": item_id})
    if not doc:
        raise HTTPException(404, "Item not found")
    return targets.news_target(doc)
