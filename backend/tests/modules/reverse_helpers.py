"""Helpers for reverse-matching / performance / actions tests (not a test module)."""
from datetime import timedelta

from .qual_helpers import Clock, listing, make  # noqa: F401


async def add_listing(db, lid, clock=None, created_days_ago=None, **kw):
    doc = listing(lid, **kw)
    if created_days_ago is not None:
        doc["created_at"] = clock() - timedelta(days=created_days_ago)
    await db.get_collection("listings").insert_one(doc)
    return doc


async def add_lead(db, clock, cid, name="Priya Sharma", agent="A1", stage="new", base=0, bhk=None, lo=None, hi=None,
                   localities=None, timeline=None, first_listing=None, source=None, phone="98765 43210",
                   message=None, follow_up_due_at=None, last_activity_days_ago=0):
    """Insert a contact directly (full control over stage, score and requirement)."""
    req = None
    if any(v is not None for v in (bhk, lo, hi, timeline)) or localities:
        req = {"bhk": bhk, "budget_min_inr": lo, "budget_max_inr": hi, "timeline": timeline, "financing": None,
               "localities": localities or [], "field_sources": {}}
    when = clock() - timedelta(days=last_activity_days_ago)
    doc = {"_id": cid, "agent_id": agent, "name": name, "phone": phone, "stage": stage, "source": source,
           "first_listing_id": first_listing, "score_base": base, "message": message, "created_at": when,
           "last_activity_at": when, "follow_up_due_at": follow_up_due_at, "requirement": req, "notes": []}
    await db.get_collection("contacts").insert_one(doc)
    return doc


async def add_view(db, clock, listing_id, anon, agent="A1"):
    await db.get_collection("events").insert_one({
        "agent_id": agent, "anon_id": anon, "contact_id": None, "type": "listing_view",
        "listing_id": listing_id, "source": None, "utm": {}, "ts": clock()})
