"""GET /api/v1/listings/{listing_id}/sellers – who else markets this project.

Signed-in agents only; the listing must belong to the calling agent and carry a MahaRERA number.
A 404 with detail "no_rera" means the listing has no MahaRERA number yet.
An empty result (searched_at: null, all groups empty) means the web search has not run yet.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.areastats.sellers import sellers as _sellers

router = APIRouter()


@router.get("/{listing_id}/sellers")
async def listing_sellers(
    listing_id: str,
    current_user: User = Depends(current_active_user),
    db=Depends(get_database),
):
    """Return seller groups for the MahaRERA project behind a listing.

    - 404 "not_found"  – listing does not exist or does not belong to this agent
    - 404 "no_rera"    – listing has no MahaRERA registration number
    """
    agent_id = str(current_user.id)
    listing = await db.get_collection("listings").find_one(
        {"_id": listing_id, "agent_id": agent_id}
    )
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    regno: str | None = (listing.get("rera_no") or "").strip() or None
    if not regno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no_rera")

    return await _sellers(db, regno)
