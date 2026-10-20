"""A post's code sent to us alone (or with "interested / info / price list", or the website button's prefilled text) gets that post's price
lines and page at once (whatsapp.brain card), never "comment INFO" (2026-10-20); a reel gets its listing post's full price table."""
from datetime import datetime

import pytest

from app.modules.knowledge.grounding import post_grounding
from app.modules.whatsapp.brain import card_facts

from ..fakes import FakeDb
from .test_dm_origin import FakeLLM
from .test_dms import IG, IGSID, event, make

pytestmark = pytest.mark.asyncio

CAPTION = ("Godrej Ivara, Upper Kharadi: 2, 3 & 4 BHK from ₹1.20 Cr onwards.\nHomes and prices.\n• 2 BHK · 730 sq ft carpet · ₹1.20 Cr.\n"
           "• 3 BHK · 890 sq ft carpet · ₹1.44 Cr.\nPayment plan: 20:20:30:30.\nPossession: Aug 2032 (the builder's date).\n"
           "MahaRERA: PR1260002502426.\nPrices as the builder gives them; ask us for today's price sheet before you book.\n"
           "Comment INFO and we will send you the price sheet and floor plans.\nWhatsApp: +91 98342 56406.")


def db_with_campaign() -> FakeDb:
    db = FakeDb()
    cal = db.get_collection("content_calendar").docs
    cal.append({"_id": "r1", "slug": "campaign-L1-listing", "kind": "post", "channel": "instagram", "caption": CAPTION, "status": "published",
                "listing_id": "L1", "campaign_run": "run1", "published_at": datetime(2026, 10, 19, 17, 40)})
    cal.append({"_id": "r2", "slug": "campaign-L1-room1", "kind": "reel", "channel": "instagram", "status": "published", "listing_id": "L1",
                "caption": "Step into green serenity.\nGodrej Ivara, Upper Kharadi: from ₹1.20 Cr.", "campaign_run": "run1", "published_at": datetime(2026, 10, 19, 17, 10)})
    db.get_collection("marketing_runs").docs.append({"_id": "run1", "page_url": "https://avasetu.test/projects/godrej-ivara-pune"})
    links = db.get_collection("interest_links").docs
    links.append({"_id": "prcxy23", "code": "prcxy23", "kind": "post", "ref": "campaign-L1-listing", "channel": "instagram", "agent_id": "OWNER",
                  "title": "Godrej Ivara, Upper Kharadi: 2, 3 & 4 BHK from ₹1.20 Cr onwards"})
    links.append({"_id": "rzzky45", "code": "rzzky45", "kind": "post", "ref": "campaign-L1-room1", "channel": "instagram", "agent_id": "OWNER",
                  "title": "Step into green serenity"})
    return db


async def ask(svc, text):
    m = parse_event(text)
    assert await svc.claim("instagram", m)
    return await svc.handle("instagram", m)


def parse_event(text):
    from app.modules.whatsapp.dms import parse
    return parse(event(text, sender=IGSID, recipient=IG))


def test_a_posts_own_asks_are_not_facts():
    facts = post_grounding("p", CAPTION).facts
    assert not [f for f in facts if "Comment INFO" in f or "WhatsApp" in f] and any("₹1.44 Cr" in f for f in facts)


def test_card_lines_keep_prices_and_the_caution_but_not_a_bare_heading():
    lines = card_facts(post_grounding("p", CAPTION).facts)
    assert "Homes and prices." not in lines and any("before you book" in x for x in lines) and any("PR1260002502426" in x for x in lines)
    assert card_facts(["Upper Kharadi uses PIN 412207.", "Compare prices before paying a token."]) == []   # a guide: no card


@pytest.mark.parametrize("text", ["prcxy23", "INFO prcxy23", "Hi, I am interested in prcxy23",
                                  "Hi, I am interested in Godrej Ivara, Upper Kharadi: 2, 3 & 4 BHK from ₹1.20 Cr onwards (ref prcxy23)"])
async def test_the_code_gets_the_price_list_page_and_the_team_sends_floor_plans(text):
    svc, db, _, _ = make(db=db_with_campaign())
    svc.llm = FakeLLM("buyer", "question")
    r = await ask(svc, text)
    assert "₹1.44 Cr" in r["reply"] and "20:20:30:30" in r["reply"] and "https://avasetu.test/projects/godrej-ivara-pune" in r["reply"]
    assert "comment info" not in r["reply"].lower() and "Floor plans: our team will send them" in r["reply"]
    conv = (await db.get_collection("dm_conversations").find({}).to_list(5))[0]
    assert conv["data"]["needs_human"] and "floor plans" in conv["data"]["questions"][-1]


async def test_a_reel_code_gets_its_listing_posts_full_table_under_the_project_name():
    svc, db, _, _ = make(db=db_with_campaign())
    svc.llm = FakeLLM("buyer", "question")
    r = await ask(svc, "rzzky45")
    assert "₹1.44 Cr" in r["reply"] and not r["reply"].startswith("Step into green serenity")


# ---- the project's word (owner 2026-10-20: 'send IVARA', simpler than a code) ----------------------------------------------------------
def with_listings(db, *more):
    db.get_collection("listings").docs.append({"_id": "L1", "project_name": "Godrej Ivara", "title": "Godrej Ivara, Upper Kharadi",
                                               "status": "live", "agent_id": "AG1"})
    db.get_collection("listings").docs.extend(more)
    return db


@pytest.mark.parametrize("text", ["IVARA", "ivara", "Ivara price list", "Godrej Ivara", "GODREJ"])
async def test_the_projects_word_gets_the_same_price_list(text):
    svc, db, _, _ = make(db=with_listings(db_with_campaign()))
    svc.llm = FakeLLM("buyer", "question")
    r = await ask(svc, text)
    assert "₹1.44 Cr" in r["reply"] and "https://avasetu.test/projects/godrej-ivara-pune" in r["reply"]
    conv = (await db.get_collection("dm_conversations").find({}).to_list(5))[0]
    assert conv["context"]["listing_id"] is None and conv["context"]["code"] == "prcxy23" and conv["agent_id"] == "AG1"


async def test_a_word_two_projects_share_asks_which():
    other = {"_id": "L2", "project_name": "Kumar Ivara", "title": "Kumar Ivara, Wagholi", "status": "live", "agent_id": "AG2"}
    svc, db, _, _ = make(db=with_listings(db_with_campaign(), other))
    svc.llm = FakeLLM("buyer", "question")
    r = await ask(svc, "IVARA")
    assert "GODREJ IVARA" in r["reply"] and "KUMAR IVARA" in r["reply"] and "₹" not in r["reply"]


async def test_a_builders_name_shared_by_two_projects_names_neither():
    other = {"_id": "L2", "project_name": "Godrej Woods", "title": "Godrej Woods", "status": "live", "agent_id": "AG2"}
    svc, db, _, _ = make(db=with_listings(db_with_campaign(), other))
    svc.llm = FakeLLM("buyer", "question")
    r = await ask(svc, "GODREJ")
    assert "₹1.44 Cr" not in r["reply"]
