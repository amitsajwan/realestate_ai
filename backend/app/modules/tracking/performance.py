"""GET /inbox/performance: per-listing views, enquiries and funnel. Aggregated in Python, owner scoped.

Bounds per agent: MAX_LISTINGS listings, MAX_CONTACTS leads and the MAX_EVENTS most recent listing_view events."""
from typing import Dict

from . import outcomes, scoring

MAX_LISTINGS, MAX_CONTACTS, MAX_EVENTS = 500, 5000, 50000
VISIT_STAGES = ("site_visit", "negotiating", "won")


def is_qualified(contact: dict, temperature: str) -> bool:
    req = contact.get("requirement") or {}
    has_budget = req.get("budget_min_inr") is not None or req.get("budget_max_inr") is not None
    return temperature in ("warm", "hot") or has_budget or bool(req.get("timeline"))


def blank_counts() -> dict:
    return {"views": 0, "unique_visitors": 0, "enquiries": 0, "qualified": 0, "site_visits": 0, "by_source": {},
            "deals": 0, "deal_value_inr": 0, "deals_by_source": {}}


def tally_enquiry(s: dict, c: dict, now) -> None:
    """Count one lead against the listing it first enquired about (shared with the per-listing activity view)."""
    s["enquiries"] += 1
    value = scoring.score(c.get("score_base", 0), c["last_activity_at"], now)
    if is_qualified(c, scoring.temperature(value)):
        s["qualified"] += 1
    if c["stage"] in VISIT_STAGES:
        s["site_visits"] += 1
    src = c.get("source") or "direct"
    s["by_source"][src] = s["by_source"].get(src, 0) + 1


def tally_deal(s: dict, c: dict) -> None:
    """Count a won deal (caller already decided it belongs to this listing)."""
    o = c.get("outcome")
    if o and o.get("result") == "won":
        s["deals"] += 1
        s["deal_value_inr"] += o.get("deal_price_inr") or 0
        src = c.get("source") or "direct"
        s["deals_by_source"][src] = s["deals_by_source"].get(src, 0) + 1


async def build_performance(svc, agent_id: str) -> dict:
    now = svc.now()
    listings = await svc.listings.find({"agent_id": agent_id}).to_list(MAX_LISTINGS)
    events = await svc.events.find({"agent_id": agent_id, "type": "listing_view"}) \
        .sort("ts", -1).limit(MAX_EVENTS).to_list(MAX_EVENTS)
    contacts = await svc.contacts.find({"agent_id": agent_id}).to_list(MAX_CONTACTS)
    stats: Dict[str, dict] = {
        l["_id"]: {"listing_id": l["_id"], "title": l.get("title"), "price_inr": l.get("price_inr"),
                   "status": l.get("status"), **blank_counts()}
        for l in listings}
    visitors: Dict[str, set] = {lid: set() for lid in stats}
    for e in events:
        lid = e.get("listing_id")
        if lid in stats:
            stats[lid]["views"] += 1
            if e.get("anon_id"):
                visitors[lid].add(e["anon_id"])
    for lid, seen in visitors.items():
        stats[lid]["unique_visitors"] = len(seen)
    for c in contacts:
        s = stats.get(c.get("first_listing_id"))
        if s is None:
            continue
        tally_enquiry(s, c, now)
    for c in contacts:  # deals are attributed to the listing the deal was on (else the one first enquired about)
        s = stats.get(outcomes.attributed_listing(c))
        if s is not None:
            tally_deal(s, c)
    items = sorted(stats.values(), key=lambda s: (-s["enquiries"], -s["views"], s["listing_id"]))
    return {"items": items}
