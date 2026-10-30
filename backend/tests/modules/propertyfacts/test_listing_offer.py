"""The offer on a project page (propertyfacts.router.with_sheet): a listing's own page shows its own sheet and photos.

2026-10-30: a listing of a MahaRERA project now renders the whole project page; with two live listings of the same project the
offer was always the latest one's, so one agent's page would show the other agent's prices and pictures."""
from datetime import datetime

from app.modules.propertyfacts.router import with_sheet

from ..fakes import FakeDb

REG = "PR1260002502426"


async def setup():
    db = FakeDb()
    for agent, slug in (("HD", "house-deal"), ("AV", "avasetu")):
        await db.get_collection("agent_public_profiles").insert_one(
            {"agent_id": agent, "slug": slug, "is_public": True, "phone": "+919921900001", "branding_data": {"business_name": slug}})
    for doc in (
        {"_id": "hd", "agent_id": "HD", "rera_no": REG, "status": "live", "price_inr": 12000000, "updated_at": datetime(2026, 10, 1),
         "media": []},
        {"_id": "av", "agent_id": "AV", "rera_no": REG, "status": "live", "price_inr": 12900000, "updated_at": datetime(2026, 10, 20),
         "media": []},
    ):
        await db.get_collection("listings").insert_one(doc)
    return db


def facts():
    return {"maharera": {"rera_no": REG}, "offer": {"price_inr": 1}}


async def test_a_listings_page_shows_its_own_agent_not_the_projects_latest_listing():
    db = await setup()
    assert (await with_sheet(db, facts(), "hd"))["offer"]["agent"]["slug"] == "house-deal"
    assert (await with_sheet(db, facts()))["offer"]["agent"]["slug"] == "avasetu"          # the project page: the latest
    assert (await with_sheet(db, facts(), "gone"))["offer"]["agent"]["slug"] == "avasetu"  # an unknown id falls back


async def test_the_offer_gives_the_agents_office_line_when_they_set_one():
    db = await setup()
    await db.get_collection("agent_public_profiles").update_one(
        {"agent_id": "HD"}, {"$set": {"branding_data": {"business_name": "House Deal", "office_phone": "+917447212121"}}})
    assert (await with_sheet(db, facts(), "hd"))["offer"]["agent"]["phone"] == "+917447212121"
