"""Reverse matching: which of the agent's open buyers fit ONE property. Same transparent rules as lead -> listing."""
from typing import Optional

from app.core.config import settings

from . import matching, requirement as reqmod, scoring
from .followup import fits_budget, listing_label, whatsapp_url
from .requirement import budget_text, fmt_inr
from .summary import CLOSED

MIN_PCT = 60
MAX_BUYERS = 10


async def share_url(svc, agent_id: str, listing_id: str) -> Optional[str]:
    """Public site link for a listing, or None when the agent has no public profile slug."""
    profile = await svc.profiles.find_one({"agent_id": agent_id})
    if not profile or not profile.get("slug"):
        return None
    return f"{settings.public_site_url}/agent/{profile['slug']}/listings/{listing_id}?src=whatsapp"


def rank_buyers(svc, listing: dict, contacts: list, all_listings: list) -> list:
    """Open leads that fit `listing` at >= 60%, best first: [{contact, req, score, temperature, match_pct, reasons}]."""
    if listing.get("status") not in matching.LIVE:
        return []
    by_id = {l["_id"]: l for l in all_listings}
    now = svc.now()
    out = []
    for c in contacts:
        if c["stage"] in CLOSED:
            continue
        req = reqmod.public(c.get("requirement"))
        if not matching.has_signal(req):
            continue
        transaction, ref_type = matching.match_context(c, by_id)
        res = matching.match_listing(req, listing, transaction, ref_type)
        if res is None or res[0] < MIN_PCT:
            continue
        value = scoring.score(c.get("score_base", 0), c["last_activity_at"], now)
        out.append({"contact": c, "req": req, "score": value, "temperature": scoring.temperature(value),
                    "match_pct": res[0], "reasons": res[1]})
    out.sort(key=lambda b: (-b["match_pct"], -b["score"], b["contact"]["_id"]))
    return out


def buyer_draft(contact: dict, req: dict, listing: dict, url: Optional[str]) -> dict:
    """Factual message. 'fits your budget' only when the price is inside the buyer's stated budget."""
    first = (contact.get("name") or "there").split()[0]
    label = listing_label(listing) or "a new property"
    price = listing.get("price_inr")
    text = f"Hi {first}, I have {label}"
    if isinstance(price, int):
        text += f" at {fmt_inr(price)}"
    budget = budget_text(req.get("budget_min_inr"), req.get("budget_max_inr"))
    if budget and fits_budget(price, req):
        text += f"; it fits your {budget} budget"
    text += "."
    if url:
        text += f" Details: {url}"
    return {"message": text, "whatsapp_url": whatsapp_url(contact["phone"], text)}


async def matching_leads(svc, agent_id: str, listing_id: str) -> dict:
    from .service import TrackingError
    listing = await svc._own_listing(agent_id, listing_id)
    if not listing:
        raise TrackingError("Listing not found", 404)
    contacts = await svc.contacts.find({"agent_id": agent_id}).to_list(2000)
    listings = await svc._agent_listings(agent_id)
    url = await share_url(svc, agent_id, listing_id)
    buyers = []
    for b in rank_buyers(svc, listing, contacts, listings)[:MAX_BUYERS]:
        c = b["contact"]
        buyers.append({
            "lead_id": c["_id"], "name": c["name"], "phone": c["phone"], "temperature": b["temperature"],
            "score": b["score"], "requirement_line": reqmod.requirement_line(b["req"]),
            "match_pct": b["match_pct"], "reasons": b["reasons"], "draft": buyer_draft(c, b["req"], listing, url)})
    return {"listing": {"id": listing_id, "title": listing.get("title"), "price_inr": listing.get("price_inr"),
                        "locality": listing.get("locality"), "share_url": url},
            "buyers": buyers}
