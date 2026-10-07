"""'Still available?' rules (contract: docs/contracts/activity.md section 2).

Age is measured from freshness_confirmed_at, falling back to published_at, then created_at, in whole days:
under 21 -> fresh, 21..44 -> confirm, 45 or more -> hidden (not shown to buyers until the agent confirms).
Only live / under_offer listings are ever confirm/hidden; every other status is "fresh"."""
from datetime import datetime
from typing import Optional, Tuple

LIVE_STATUSES = ("live", "under_offer")
CONFIRM_AFTER_DAYS = 21
HIDE_AFTER_DAYS = 45


def days_since_confirmed(doc: dict, now: datetime) -> Optional[int]:
    if doc.get("status") not in LIVE_STATUSES:
        return None
    base = doc.get("freshness_confirmed_at") or doc.get("published_at") or doc.get("created_at")
    if base is None:
        return None
    return max(0, (now - base).days)


def freshness_of(doc: dict, now: datetime) -> Tuple[str, Optional[int]]:
    days = days_since_confirmed(doc, now)
    if days is None or days < CONFIRM_AFTER_DAYS:
        return "fresh", days
    return ("confirm" if days < HIDE_AFTER_DAYS else "hidden"), days


def is_hidden(doc: dict, now: datetime) -> bool:
    return freshness_of(doc, now)[0] == "hidden"
