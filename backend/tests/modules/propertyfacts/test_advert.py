"""AR-3: which MahaRERA project registration a property's ads may print (propertyfacts.advert), and that campaign cards carry it."""
import asyncio

import pytest
from PIL import Image

from app.modules.marketing.maharera import HOME_URL
from app.modules.propertyfacts import advert, campaign
from app.modules.propertyfacts.facts import Fact, Reading, sheet

from ..fakes import FakeDb
from ..qr_helpers import decode

REG = "P52100076768"
VIEW = "https://maharerait.maharashtra.gov.in/public/project/view/40123"


def facts(listing_rera=None, maharera_rera=None, url=VIEW):
    rs = [Reading("project_name", "Gulmohar City", "listing"), Reading("locality", "Ranjangaon", "listing")]
    if listing_rera:
        rs.append(Reading("rera_no", listing_rera, "listing"))
    if maharera_rera:
        rs += [Reading("rera_no", maharera_rera, "maharera", url), Reading("maharera_url", url, "maharera", url)]
    return sheet(rs)


def kit(status, rera=None):
    return {"status": "done", "facts": [], "registration": {"status": status, "rera_no": rera}}


def test_maharera_record_gives_the_project_page():
    reg = advert.trusted({}, facts(maharera_rera=REG))
    assert (reg.regno, reg.url) == (REG, VIEW)
    reg = advert.trusted({"rera_no": REG}, facts(REG, REG), kit("exempt"))   # MahaRERA's own record outranks an "exempt" answer
    assert (reg.regno, reg.url) == (REG, VIEW)


def test_the_listing_number_is_trusted_and_leads_to_the_maharera_site():
    for doc, f in (({"rera_no": REG}, None), ({}, facts(listing_rera=REG)), ({"rera_no": "p 52100 076768"}, facts())):
        reg = advert.trusted(doc, f)
        assert (reg.regno, reg.url) == (REG, HOME_URL)


@pytest.mark.parametrize("status,want", [("verified", REG), ("registered_by_agent", REG), ("unverified", None),
                                         ("unknown", None), ("exempt", None)])
def test_brochure_kit_status_decides_without_a_listing_number(status, want):
    reg = advert.trusted({}, facts(), kit(status, REG if status != "unknown" else None))
    assert (reg.regno if reg else None) == want


def test_exempt_answer_drops_the_listing_number():
    assert advert.trusted({"rera_no": REG}, facts(listing_rera=REG), kit("exempt")) is None


def test_never_the_agents_number_a_conflict_or_a_sample():
    assert advert.trusted({"rera_no": "A51700012345"}, None, kit("registered_by_agent", "A51700012345")) is None
    assert advert.trusted({"rera_no": REG}, facts(listing_rera=REG, maharera_rera="P52100099999")) is None   # MahaRERA disagrees
    assert advert.trusted({"rera_no": REG, "title": "Sample 2 BHK"}) is None
    assert advert.trusted({}, None, None) is None


def test_for_listing_reads_the_kit_the_sheet_and_the_register():
    async def run():
        db = FakeDb()
        doc = {"_id": "L1", "project_name": "Gulmohar City", "locality": "Ranjangaon", "rera_no": REG}
        assert (await advert.for_listing(db, doc)).url == HOME_URL
        await db.get_collection("projects").insert_one({"_id": REG, "source_url": VIEW})   # our MahaRERA register knows its page
        assert (await advert.for_listing(db, doc)).url == VIEW
        await db.get_collection("brochures").insert_one({"_id": "k1", "listing_id": "L1", "uploaded_at": 1, **kit("exempt")})
        assert await advert.for_listing(db, doc) is None
        db2 = FakeDb()   # a kept fact sheet with MahaRERA's record
        await db2.get_collection("property_facts").insert_one({"_id": REG, "facts": [
            {"key": "rera_no", "value": REG, "level": "official", "readings": [{"source": "maharera", "value": REG, "url": VIEW}]},
            {"key": "maharera_url", "value": VIEW, "level": "official", "readings": [{"source": "maharera", "value": VIEW}]}]})
        assert (await advert.for_listing(db2, {"_id": "L2", "rera_no": REG})).url == VIEW
    asyncio.run(run())


# ---- the campaign ------------------------------------------------------------------------------------------------------------
def test_campaign_briefs_carry_the_registration_and_drop_it_when_exempt():
    from app.modules.creative.models import CardBrand

    from .test_campaign import gulmohar
    agent = CardBrand("House Deal", "Call / WhatsApp +91 99219 93099", phone="+91 99219 93099")
    f = gulmohar()
    f["rera_no"] = Fact("rera_no", REG, "official", [Reading("rera_no", REG, "listing")])   # only the agent's listing says it
    briefs = campaign.plan(f, card_brand=agent)
    assert briefs and all(b.maharera and b.maharera.regno == REG for _, b in briefs)
    assert all(b.card_brand.rera == REG for _, b in briefs)
    exempt = campaign.plan(f, card_brand=agent, kit=kit("exempt"))
    assert exempt and all(b.maharera is None and b.card_brand.rera == "" for _, b in exempt)   # no badge, no registration line


async def test_campaign_cards_show_a_qr_that_scans(tmp_path):
    from .test_campaign import gulmohar
    f = gulmohar()
    packs = await campaign.make(f, tmp_path, kit=None)
    assert len(packs) >= 10
    want = advert.trusted({}, f).url
    for aid, p in packs:
        first, last = p.images[0], p.images[-1]   # the card (or a carousel's cover) and the closing slide
        for path in {first, last}:
            with Image.open(path) as im:
                got = decode(im)
            assert got == want, (aid, p.design.get("layout"), path)
