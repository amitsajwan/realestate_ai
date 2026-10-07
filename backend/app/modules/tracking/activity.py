"""GET /inbox/listings/{id}/activity: what happened on ONE property (contract: docs/contracts/activity.md section 1).

Owner scoped. Bounds: the MAX_EVENTS newest events of this listing and the agent's MAX_CONTACTS leads (same cap as
performance). Counting rules are shared with performance.py (tally_enquiry / tally_deal). Visitors are anonymous:
they appear as "Visitor N"; anon ids, IPs and user agents never leave the server."""
from datetime import timedelta
from typing import Dict, Optional

from . import outcomes
from .performance import MAX_CONTACTS, blank_counts, tally_deal, tally_enquiry
from .service import TrackingError
from .today import IST

MAX_EVENTS = 5000
DAYS = 14
MAX_FEED, MAX_PEOPLE = 100, 10
FEED_TYPES = {"listing_view": "view", "whatsapp_click": "whatsapp_click", "call_click": "call_click",
              "share": "share", "inquiry": "enquiry"}
SOURCE_NAMES = {"whatsapp": "WhatsApp", "instagram": "Instagram", "facebook": "Facebook"}


def ist_date(ts):
    """Calendar date in India for a stored (naive UTC) datetime."""
    return (ts + IST).date()


def _text(kind: str, who: str, source: Optional[str]) -> str:
    if kind == "view":
        src = source if source and source.lower() != "direct" else None
        return f"{who} viewed this" + (f" from {SOURCE_NAMES.get(src.lower(), src)}" if src else "")
    return {"whatsapp_click": f"{who} tapped WhatsApp", "call_click": f"{who} tapped Call",
            "share": f"{who} shared this listing", "enquiry": f"{who} sent an enquiry"}[kind]


class _Identity:
    """Who an event belongs to: the lead when known, else a stable 'Visitor N' (numbered by first appearance)."""

    def __init__(self, contacts: list):
        self.by_id = {c["_id"]: c for c in contacts}
        self.by_anon = {a: c for c in contacts for a in c.get("anon_ids") or []}
        self.numbers: Dict[str, int] = {}

    def lead(self, e: dict) -> Optional[dict]:
        return self.by_id.get(e.get("contact_id")) or self.by_anon.get(e.get("anon_id"))

    def who(self, e: dict) -> dict:
        c = self.lead(e)
        if c:
            return {"kind": "lead", "label": c["name"], "lead_id": c["_id"]}
        key = e.get("anon_id")
        if key is None:
            return {"kind": "visitor", "label": "A visitor"}
        n = self.numbers.setdefault(key, len(self.numbers) + 1)
        return {"kind": "visitor", "label": f"Visitor {n}"}


def _daily(now, events: list, enquiries: list) -> list:
    today = ist_date(now)
    days = {today - timedelta(days=DAYS - 1 - i): {"views": 0, "enquiries": 0} for i in range(DAYS)}
    for e in events:
        if e["type"] == "listing_view" and ist_date(e["ts"]) in days:
            days[ist_date(e["ts"])]["views"] += 1
    for c in enquiries:
        if ist_date(c["created_at"]) in days:
            days[ist_date(c["created_at"])]["enquiries"] += 1
    return [{"date": d.isoformat(), **v} for d, v in days.items()]


def _people(svc, leads: list) -> list:
    rows = [svc._view(c) for c in leads]
    rows.sort(key=lambda v: v["last_activity_at"], reverse=True)
    rows.sort(key=lambda v: -v["score"])  # stable: hottest first, ties most recent first
    return [{"lead_id": v["id"], "name": v["name"], "temperature": v["temperature"], "score": v["score"],
             "requirement_line": v["requirement_line"], "last_activity_at": v["last_activity_at"]}
            for v in rows[:MAX_PEOPLE]]


async def build_activity(svc, agent_id: str, listing_id: str, limit: int = 50) -> dict:
    listing = await svc._own_listing(agent_id, listing_id)
    if not listing:
        raise TrackingError("Listing not found", 404)
    now = svc.now()
    limit = max(1, min(limit, MAX_FEED))
    events = await svc.events.find({"agent_id": agent_id, "listing_id": listing_id, "type": {"$in": list(FEED_TYPES)}}) \
        .sort("ts", -1).limit(MAX_EVENTS).to_list(MAX_EVENTS)
    contacts = await svc.contacts.find({"agent_id": agent_id}).to_list(MAX_CONTACTS)
    ident = _Identity(contacts)

    counts = blank_counts()
    by_source: Dict[str, dict] = {}
    visitors, clicks = set(), {"whatsapp_click": 0, "call_click": 0, "share": 0}
    for e in events:
        if e["type"] == "listing_view":
            counts["views"] += 1
            if e.get("anon_id"):
                visitors.add(e["anon_id"])
            row = by_source.setdefault(e.get("source") or "direct", {"views": 0, "enquiries": 0})
            row["views"] += 1
        elif e["type"] in clicks:
            clicks[e["type"]] += 1
    enquiries = [c for c in contacts if c.get("first_listing_id") == listing_id]
    for c in enquiries:
        tally_enquiry(counts, c, now)
    for c in contacts:
        if outcomes.attributed_listing(c) == listing_id:
            tally_deal(counts, c)
    for src, n in counts["by_source"].items():
        by_source.setdefault(src, {"views": 0, "enquiries": 0})["enquiries"] = n

    for e in sorted(events, key=lambda d: d["ts"]):  # number visitors in the order they first appeared
        ident.who(e)
    feed = []
    for e in events[:limit]:  # newest first
        kind, who = FEED_TYPES[e["type"]], ident.who(e)
        feed.append({"ts": e["ts"], "type": kind, "who": who, "source": e.get("source"),
                     "text": _text(kind, who["label"], e.get("source"))})

    people = {c["_id"]: c for c in enquiries}
    for lead in map(ident.lead, events):
        if lead:
            people[lead["_id"]] = lead
    return {
        "listing": {"id": listing["_id"], "title": listing.get("title"), "status": listing.get("status"),
                    "price_inr": listing.get("price_inr")},
        "totals": {"views": counts["views"], "unique_visitors": len(visitors), "enquiries": counts["enquiries"],
                   "qualified": counts["qualified"], "site_visits": counts["site_visits"], "deals": counts["deals"],
                   "whatsapp_clicks": clicks["whatsapp_click"], "call_clicks": clicks["call_click"],
                   "shares": clicks["share"]},
        "by_source": by_source,
        "daily": _daily(now, events, enquiries),
        "feed": feed,
        "people": _people(svc, list(people.values())),
    }
