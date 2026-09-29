"""Recommended actions for GET /inbox/today (max 6, ordered by priority then recency)."""
from datetime import timedelta

from . import requirement as reqmod
from .followup import listing_label
from .requirement import bhk_text, budget_text
from .reverse import rank_buyers
from .summary import CLOSED

MAX_ACTIONS = 6
NEW_LISTING_DAYS = 3


def _detail(req: dict, temperature: str) -> str:
    req = req or {}
    bits = [bhk_text(req.get("bhk")), budget_text(req.get("budget_min_inr"), req.get("budget_max_inr"))]
    return ", ".join([b for b in bits if b] + [f"{temperature} buyer"])


async def _packed_ids(svc, listing_ids: list) -> set:
    """Listing ids that already have a marketing pack (collection owned by the marketing module; read only)."""
    if not listing_ids:
        return set()
    packs = await svc.db.get_collection("marketing_packs").find({"_id": {"$in": listing_ids}}).to_list(len(listing_ids))
    return {p["_id"] for p in packs}


async def build_actions(svc, agent_id: str, rows: list, listings: list, now) -> list:
    """rows: [(contact, score, temperature)] for all of the agent's leads."""
    found = []  # (priority, recency datetime (newest first), action)
    called = set()
    for c, _, temp in rows:
        if c["stage"] == "new" and temp == "hot":
            called.add(c["_id"])
            found.append((1, c["last_activity_at"], {
                "type": "call", "title": f"Call {c['name']}",
                "detail": _detail(reqmod.public(c.get("requirement")), "hot"), "priority": 1, "lead_id": c["_id"]}))
    for c, _, _ in rows:
        due = c.get("follow_up_due_at")
        if c["_id"] in called or c["stage"] in CLOSED or not due or due >= now:
            continue
        days = (now - due).days
        detail = "Follow-up overdue" + (f" by {days} day{'s' if days != 1 else ''}" if days >= 1 else "")
        found.append((1, c["last_activity_at"], {
            "type": "follow_up", "title": f"Follow up with {c['name']}", "detail": detail, "priority": 1,
            "lead_id": c["_id"]}))
    live = [l for l in listings if l.get("status") == "live"]
    contacts = [r[0] for r in rows]
    for l in live:
        created = l.get("created_at")
        if not created or created < now - timedelta(days=NEW_LISTING_DAYS):
            continue
        n = len(rank_buyers(svc, l, contacts, listings))
        if n:
            found.append((2, created, {
                "type": "send_property",
                "title": f"Send {listing_label(l) or 'the new property'} to {n} matching buyer{'s' if n != 1 else ''}",
                "detail": "Their budget, BHK and area fit this property", "priority": 2,
                "listing_id": l["_id"], "buyer_count": n}))
    packed = await _packed_ids(svc, [l["_id"] for l in live])
    for l in live:
        if l["_id"] not in packed:
            found.append((3, l.get("created_at") or now, {
                "type": "create_marketing",
                "title": f"Create marketing for {listing_label(l) or 'your new property'}",
                "detail": "Get a ready-to-share post and WhatsApp message", "priority": 3, "listing_id": l["_id"]}))
    found.sort(key=lambda f: (f[0], -f[1].timestamp(), f[2].get("lead_id") or f[2].get("listing_id")))
    return [f[2] for f in found[:MAX_ACTIONS]]
