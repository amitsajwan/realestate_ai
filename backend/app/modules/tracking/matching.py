"""Transparent rule-based buyer <-> listing matching. Never an "AI %": points per dimension, reasons listed.

Weights (sum 100): property type 10, BHK 25, budget 40, locality 25. A dimension the buyer said nothing about
earns half credit (neutral, no reason listed). A different transaction (sale vs rent) excludes the listing."""
import re
from typing import List, Optional

from .requirement import bhk_text, budget_text, fmt_inr

W_TYPE, W_BHK, W_BUDGET, W_LOCALITY = 10, 25, 40, 25
MIN_PCT = 40
MAX_MATCHES = 3
LIVE = ["live", "under_offer"]


def _budget_credit(price: int, lo: Optional[int], hi: Optional[int]):
    """-> (fraction, reason|None)."""
    txt = budget_text(lo, hi)
    lo_v, hi_v = lo or 0, hi if hi is not None else float("inf")
    if lo_v <= price <= hi_v:
        return 1.0, f"Price {fmt_inr(price)} is within budget {txt}"
    if price > hi_v and price <= hi_v * 1.1:
        return 0.5, f"Price {fmt_inr(price)} is slightly above budget {txt}"
    if price < lo_v and price >= lo_v * 0.9:
        return 0.5, f"Price {fmt_inr(price)} is slightly below budget {txt}"
    return 0.0, None


def match_listing(req: dict, listing: dict, transaction: str = "sale", ref_type: Optional[str] = None):
    """-> (pct, reasons) or None when the listing cannot fit at all (different transaction)."""
    if (listing.get("transaction") or "sale") != transaction:
        return None
    reasons: List[str] = []
    pts = 0.0
    # property type
    if ref_type:
        if listing.get("property_type") == ref_type:
            pts += W_TYPE
            reasons.append(f"Same property type ({ref_type})")
    else:
        pts += W_TYPE / 2
    # bhk
    want = req.get("bhk")
    have = listing.get("bhk")
    if not want:
        pts += W_BHK / 2
    elif have is not None:
        if float(have) == float(want):
            pts += W_BHK
            reasons.append(f"{bhk_text(want)} matches")
        elif abs(float(have) - float(want)) <= 1:
            pts += W_BHK * 0.4
            reasons.append(f"{bhk_text(have)} (you asked for {bhk_text(want)})")
    # budget
    lo, hi = req.get("budget_min_inr"), req.get("budget_max_inr")
    price = listing.get("price_inr")
    if lo is None and hi is None:
        pts += W_BUDGET / 2
    elif isinstance(price, int):
        frac, why = _budget_credit(price, lo, hi)
        pts += W_BUDGET * frac
        if why:
            reasons.append(why)
    # locality
    locs = [l.lower() for l in (req.get("localities") or [])]
    if not locs:
        pts += W_LOCALITY / 2
    elif (listing.get("locality") or "").lower() in locs:
        pts += W_LOCALITY
        reasons.append(f"In {listing['locality']}")
    return int(round(pts)), reasons


def has_signal(req: Optional[dict]) -> bool:
    return bool(req) and bool(req.get("bhk") or req.get("budget_min_inr") is not None
                              or req.get("budget_max_inr") is not None or req.get("localities"))


def top_matches(req: Optional[dict], listings: List[dict], transaction: str = "sale",
                ref_type: Optional[str] = None, limit: int = MAX_MATCHES) -> List[dict]:
    """Top live listings scoring >= 40, best first (ties: cheaper first, then id for determinism)."""
    if not has_signal(req):
        return []
    scored = []
    for l in listings:
        if l.get("status") not in LIVE:
            continue
        res = match_listing(req, l, transaction, ref_type)
        if res is None or res[0] < MIN_PCT:
            continue
        scored.append((res[0], res[1], l))
    scored.sort(key=lambda s: (-s[0], s[2].get("price_inr") or 0, str(s[2].get("_id"))))
    return [{"listing_id": l.get("id") or l.get("_id"), "title": l.get("title"), "price_inr": l.get("price_inr"),
             "locality": l.get("locality"), "match_pct": pct, "reasons": reasons}
            for pct, reasons, l in scored[:limit]]


def match_context(contact: dict, by_id: dict):
    """-> (transaction, ref_type) for scoring a lead against listings: taken from the listing they enquired
    about, else guessed from the message (rent words) and defaulting to sale."""
    ref = by_id.get(contact.get("first_listing_id"))
    if ref:
        return ref.get("transaction") or "sale", ref.get("property_type")
    text = (contact.get("last_message") or contact.get("message") or "").lower()
    return ("rent" if re.search(r"\b(rent|rental|kiraya|kiraye)\b", text) else "sale"), None
