"""Deal outcomes: what happened when an agent marked a buyer Won or Lost. Results feed performance and the home screen."""
from datetime import datetime, timedelta
from typing import Dict, Optional

LOST_REASONS = ("price", "bought_elsewhere", "not_responding", "changed_mind", "other")
RESULT_DAYS = 30


def public(outcome: Optional[dict]) -> Optional[dict]:
    if not outcome:
        return None
    return {"result": outcome.get("result"), "deal_price_inr": outcome.get("deal_price_inr"),
            "listing_id": outcome.get("listing_id"), "lost_reason": outcome.get("lost_reason"),
            "closed_at": outcome.get("closed_at")}


def build_outcome(stage: str, given, listing_id: Optional[str], now: datetime) -> Optional[dict]:
    """Stored outcome for a lead moved to won/lost (None for any other stage: moving out clears it)."""
    if stage == "won":
        return {"result": "won", "deal_price_inr": getattr(given, "deal_price_inr", None) if given else None,
                "listing_id": listing_id, "closed_at": now}
    if stage == "lost":
        return {"result": "lost", "lost_reason": getattr(given, "lost_reason", None) if given else None, "closed_at": now}
    return None


def attributed_listing(contact: dict) -> Optional[str]:
    return (contact.get("outcome") or {}).get("listing_id") or contact.get("first_listing_id")


def results(contacts: list, now: datetime) -> dict:
    """Last-30-day results for the home screen."""
    since = now - timedelta(days=RESULT_DAYS)
    won = lost = 0
    value = 0
    by_source: Dict[str, int] = {}
    reasons: Dict[str, int] = {}
    for c in contacts:
        o = c.get("outcome")
        if not o or not o.get("closed_at") or o["closed_at"] < since:
            continue
        if o.get("result") == "won":
            won += 1
            value += o.get("deal_price_inr") or 0
            src = c.get("source") or "direct"
            by_source[src] = by_source.get(src, 0) + 1
        elif o.get("result") == "lost":
            lost += 1
            if o.get("lost_reason"):
                reasons[o["lost_reason"]] = reasons.get(o["lost_reason"], 0) + 1
    top = sorted(by_source.items(), key=lambda kv: (-kv[1], kv[0]))
    return {"period_days": RESULT_DAYS, "deals_won": won, "deal_value_inr": value, "deals_lost": lost,
            "top_source": top[0][0] if top else None, "lost_reasons": reasons}
