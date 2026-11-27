"""The live listings of one MahaRERA project. Several agents may sell a project and its page shows one, so which one must not be an accident
of who edited last (owner, 2026-11-06, docs/plan/listing-flow.md): the most complete listing leads, and the newest breaks a tie."""
from typing import Dict, Iterable, List, Optional, Tuple

from . import homes

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


async def live_for_projects(db, regnos: Iterable[str]) -> Dict[str, List[dict]]:
    """{regno: its live listings} for many projects in one read: the cards of other projects on a page."""
    wanted = list(dict.fromkeys(r for r in regnos if r))
    if not wanted:
        return {}
    out: Dict[str, List[dict]] = {}
    for x in await db.get_collection("listings").find({"rera_no": {"$in": wanted}, "status": {"$in": list(LIVE_STATES)}}).to_list(2000):
        out.setdefault(x["rera_no"], []).append(x)
    return out


def card_price(listing: Optional[dict]) -> Tuple[Optional[int], Optional[str]]:
    """(lowest price, "3, 4 BHK") of a listing as a project card says it, the price its own page leads with (the sheet's lowest,
    else the listing's price); (None, None) for a rent, which is not a sale price, or without a price."""
    if not listing or listing.get("transaction") == "rent":
        return None, None
    low = homes.from_price(listing)
    if not low:
        return None, None
    nums = list(dict.fromkeys(r["label"][:-4] for r in homes.rows(listing) if r["label"].endswith(" BHK")))
    return int(low), (", ".join(nums) + " BHK") if nums else None
