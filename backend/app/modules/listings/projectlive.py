"""The live listings of one MahaRERA project. Several agents may sell a project and its page shows one, so which one must not be an accident
of who edited last (owner, 2026-11-06, docs/plan/listing-flow.md): the most complete listing leads, and the newest breaks a tie."""
from typing import List, Optional

LIVE_STATES = ("live", "under_offer")


def completeness(listing: dict) -> tuple:
    """Priced home types, then photos, then whether it has a price at all, then how recent it is."""
    rows = [c for c in listing.get("configurations") or [] if isinstance(c, dict) and c.get("price_inr")]
    photos = [m for m in listing.get("media") or [] if isinstance(m, dict) and (m.get("kind") or "image") == "image"]
    return len(rows), len(photos), bool(listing.get("price_inr")), str(listing.get("updated_at") or "")


async def live_for_project(db, regno: str) -> List[dict]:
    return await db.get_collection("listings").find({"rera_no": regno, "status": {"$in": list(LIVE_STATES)}}).to_list(200)


def best(listings: List[dict]) -> Optional[dict]:
    return max(listings, key=completeness) if listings else None
