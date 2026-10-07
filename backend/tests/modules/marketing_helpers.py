"""Shared fixtures for the marketing tests (kept out of fakes.py, which other streams own)."""
from app.modules.marketing.facts import Facts

PROFILE = {"agent_id": "A1", "slug": "rahul", "agent_name": "Rahul Sharma", "phone": "9876543210", "is_public": True}
SHARE = "https://site.test/agent/rahul/listings/{id}?src=whatsapp"

BASE = {"_id": "L1", "agent_id": "A1", "status": "live", "transaction": "sale", "property_type": "apartment",
        "title": "x", "price_inr": 8500000, "city": "Pune", "locality": "Baner", "bhk": 2, "carpet_sqft": 1100,
        "possession": "ready", "rera_no": "P52100012345", "amenities": ["Gym", "Swimming pool", "Clubhouse"],
        "floor": 5, "total_floors": 12, "furnishing": "semi", "media": []}


def listing(**over) -> dict:
    d = {**BASE, **over}
    return {k: v for k, v in d.items() if v != "__drop__"}


def facts(**over) -> Facts:
    d = listing(**over)
    return Facts.from_docs(d, PROFILE, SHARE.format(id=d["_id"]))


VARIANTS = {
    "sale_ready_full": {},
    "sale_uc_no_amen": {"possession": "under_construction", "amenities": [], "rera_no": None, "carpet_sqft": None,
                        "price_inr": 12500000, "_id": "L2"},
    "rent_cheap": {"transaction": "rent", "price_inr": 45000, "bhk": 1, "possession": None, "_id": "L3"},
    "luxury_villa": {"property_type": "villa", "price_inr": 250000000, "bhk": 5, "locality": "Koregaon Park",
                     "_id": "L4"},
    "plot_min": {"property_type": "plot", "bhk": None, "amenities": [], "rera_no": None, "carpet_sqft": None,
                 "super_built_up_sqft": 2400, "possession": None, "floor": None, "total_floors": None,
                 "furnishing": None, "price_inr": 4500000, "_id": "L5"},
}
