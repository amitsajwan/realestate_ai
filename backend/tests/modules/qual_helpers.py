"""Shared setup for qualification tests (not a test module)."""
from datetime import datetime, timedelta

from app.modules.tracking.schemas import EventIn, InquiryIn
from app.modules.tracking.service import TrackingService

from .listings_fakes import ListingsDb  # adds $in/$ne on top of fakes.FakeDb

BROWSER = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile Safari/604.1"


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 12, 0, 0)

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


def listing(lid, agent="A1", title=None, locality="Baner", bhk=2, price=8_500_000, status="live",
            transaction="sale", ptype="apartment"):
    return {"_id": lid, "id": lid, "agent_id": agent, "status": status, "transaction": transaction,
            "property_type": ptype, "title": title or f"{bhk}BHK in {locality} {lid}", "price_inr": price,
            "city": "Pune", "locality": locality, "bhk": bhk, "carpet_sqft": 900}


def standard_listings():
    return [
        listing("L1", title="2BHK in Baner", price=8_500_000),
        listing("L2", locality="Wakad", price=7_000_000),
        listing("L3", bhk=3, price=15_000_000),
        listing("L4", price=8_800_000, status="under_offer"),
        listing("L5", status="draft"),
        listing("L6", transaction="rent", price=35_000),
        listing("L7", agent="A2", price=8_500_000),
    ]


async def make(with_listings=True, polish=None):
    db, clock = ListingsDb(), Clock()
    profiles = db.get_collection("agent_public_profiles")
    await profiles.insert_one({"slug": "rahul", "agent_id": "A1", "is_public": True})
    await profiles.insert_one({"slug": "priya", "agent_id": "A2", "is_public": True})
    if with_listings:
        for l in standard_listings():
            await db.get_collection("listings").insert_one(l)
    return TrackingService(db, now=clock, polish=polish), db, clock


def ev(type_, listing_id="L1", anon="anon-visitor-1", slug="rahul"):
    return EventIn(agent_slug=slug, anon_id=anon, type=type_, listing_id=listing_id)


def inquiry(**kw):
    base = dict(agent_slug="rahul", anon_id="anon-visitor-1", name="Amit Kumar", phone="98765 43210",
                message=None, consent=True, listing_id="L1", source="whatsapp")
    base.update(kw)
    return InquiryIn(**base)


async def lead_id(svc, agent="A1", idx=0):
    return (await svc.list_leads(agent))[idx]["id"]
