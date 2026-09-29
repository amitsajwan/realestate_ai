"""Helpers for activity tests (not a test module)."""
from datetime import datetime, timedelta

from .reverse_helpers import add_lead, add_view, make  # noqa: F401


async def add_event(db, clock, type_, anon="anon-1", listing="L1", source=None, ts=None, agent="A1", contact_id=None):
    await db.get_collection("events").insert_one({
        "agent_id": agent, "anon_id": anon, "contact_id": contact_id, "type": type_, "listing_id": listing,
        "source": source, "utm": {}, "ts": ts or clock()})


def ago(clock, **kw) -> datetime:
    return clock() - timedelta(**kw)


async def activity(svc, listing="L1", agent="A1", limit=50):
    return await svc.listing_activity(agent, listing, limit)
