"""Lead board (inbox/board.py): agents see the owner's open leads without name or number, ask for one with an offer, and the owner
gives it to one of them (owner, 2026-10-31)."""
from datetime import datetime, timedelta

from app.modules.inbox.board import PREVIEW, LeadBoard, ref_of
from app.modules.inbox.service import InboxError, InboxService

from .fakes import FakeDb
from .test_lead_handover import FakeWhatsApp

NOW = datetime(2026, 10, 31, 6, 0)
OWNER, HD, STAVAN = "OWNER", "HD", "STAVAN"


def lead(_id, ago=timedelta(days=2), **kw):
    return {"_id": _id, "agent_id": OWNER, "name": "Rahul Thombare", "phone": "+919876500001", "stage": "contacted", "channel": "form",
            "message": "About Site visit: MANSHA PHASE-II (MahaRERA P52100028315): call me on 9876500001", "source": "google",
            "first_touch": {"enquiry_page": "/projects/mansha-phase-ii-wagholi", "referrer": "https://www.google.com/"},
            "created_at": NOW - ago, "last_activity_at": NOW - ago, "score_base": 25,
            "requirement": {"bhk": 2.0, "budget_max_inr": 7500000, "timeline": "1_3_months", "financing": "home_loan",
                            "localities": [], "source": "stated"},
            "calls": [{"ts": NOW - ago + timedelta(hours=1), "outcome": "answered"}], **kw}


async def setup(*leads):
    db = FakeDb()
    await db.get_collection("projects").insert_one({"_id": "P52100028315", "regno": "P52100028315", "name": "MANSHA PHASE-II",
                                                    "locality": "wagholi", "page_slug": "mansha-phase-ii-wagholi"})
    for p in ({"agent_id": HD, "slug": "house-deal", "phone": "+919921900001", "branding_data": {"business_name": "House Deal"}},
              {"agent_id": STAVAN, "slug": "stavan", "phone": "+919921900002", "agent_name": "Stavan"},
              {"agent_id": OWNER, "slug": "avasetu", "phone": "+919767900001"}):
        await db.get_collection("agent_public_profiles").insert_one(p)
    for c in leads:
        await db.get_collection("contacts").insert_one(c)
    wa = FakeWhatsApp()
    return db, LeadBoard(db, InboxService(db, wa, now=lambda: NOW), [OWNER], now=lambda: NOW), wa


async def test_an_agent_sees_what_the_buyer_wants_but_never_their_name_number_or_words():
    db, board, _ = await setup(lead("rahul"))
    items = (await board.cards(HD))["items"]
    assert len(items) == 1
    c = items[0]
    assert (c["project"], c["areas"], c["bhk"], c["budget"], c["when"], c["paying"], c["wants"]) == (
        "Mansha Phase-II", ["Wagholi"], "2 BHK", "under 75L", "1-3 months", "Home loan", "A site visit")
    assert c["age"] == "Came in 2 days ago" and c["came_from"] == "Google search" and c["genuine"] == "called"
    assert "Picked up our call" in c["signals"] and "Told us their budget, BHK, when themselves" in c["signals"]
    shown = repr(c)
    for secret in ("Rahul", "Thombare", "98765", "rahul", "call me"):
        assert secret not in shown, secret


async def test_every_lead_shows_except_won_deals_tests_and_bare_comments():
    _, board, _ = await setup(lead("ok"), lead("won", stage="won"), lead("lost", stage="lost"),
                              lead("given", agent_id=STAVAN, passed_by=OWNER, passed_to=STAVAN, handover={"by": "board"}),
                              lead("old", ago=timedelta(days=40)), lead("test", name="claude test"), lead("nonum", phone=""),
                              lead("hello", phone="", message="", requirement=None, source="instagram_comment"))
    cards = {c["ref"]: c for c in (await board.cards(HD))["items"]}
    assert set(cards) == {ref_of(i) for i in ("ok", "lost", "given", "old", "nonum")}
    assert all("stage" not in c for c in cards.values())   # no follow-up state on a card: only what sells the lead
    assert cards[ref_of("nonum")]["genuine"] == "called"   # picked up our call, number or not


async def test_a_number_we_know_keeps_any_lead_off_even_a_passed_one_but_a_passed_lead_is_not_dropped_by_its_name():
    db, board, _ = await setup(lead("agentnum", agent_id=HD, passed_by=OWNER, passed_to=HD, phone="+919921900002"),
                               lead("office", phone="9822000111"), lead("mine", phone="+91 97679 71656"),
                               lead("hd", agent_id=HD, passed_by=OWNER, passed_to=HD, phone="+919876500003", name="test buyer"))
    await db.get_collection("agent_public_profiles").update_one({"agent_id": HD}, {"$set": {"branding_data.office_phone": "+91 98220 00111"}})
    assert [c["ref"] for c in (await board.cards(OWNER))["items"]] == [ref_of("hd")]


async def test_offers_are_sealed_and_the_owner_gives_the_lead_to_one_agent():
    db, board, wa = await setup(lead("rahul"))
    ref = ref_of("rahul")
    await board.ask(HD, ref, "fee", 2000)
    await board.ask(STAVAN, ref, "share", 25, "I work Wagholi daily")
    seen = (await board.cards(HD))["items"][0]
    assert seen["asked"] == 2 and seen["mine"]["offer"] == "₹2,000 for the lead" and "asks" not in seen and "lead_id" not in seen
    mine = (await board.cards(OWNER))["items"][0]
    assert [(a["agent_name"], a["offer"]) for a in mine["asks"]] == [("House Deal", "₹2,000 for the lead"),
                                                                     ("Stavan", "25% of the brokerage on closing")]
    alert = await db.get_collection("notifications").find_one({"agent_id": OWNER, "kind": "lead_asked"})
    assert "House Deal asked for the lead (2 BHK · Mansha Phase-II): ₹2,000 for the lead." == alert["summary"]

    r = await board.give(OWNER, ref, STAVAN)
    assert r["passed_to"] == "Stavan" and wa.sent[0][0] == "919921900002"
    moved = await db.get_collection("contacts").find_one({"_id": "rahul"})
    assert moved["agent_id"] == STAVAN and moved["handover"]["by"] == "board"
    assert len((await board.cards(HD))["items"]) == 1   # still on the board, now with Stavan
    closed = await db.get_collection("notifications").find_one({"agent_id": HD, "kind": "lead_ask_closed"})
    assert closed is not None


async def test_view_as_an_agent_shows_what_any_agent_reads_and_nothing_of_the_owner():
    _, board, _ = await setup(lead("rahul"), lead("saket", agent_id=HD, passed_by=OWNER, passed_to=HD))
    await board.ask(HD, ref_of("rahul"), "fee", 2000)
    view = await board.cards(PREVIEW)
    assert view["preview"] is True and view["owner"] is False and len(view["items"]) == 2
    assert all("lead_id" not in c and "asks" not in c and "holder" not in c and c["mine"] is None for c in view["items"])


async def test_the_owner_cannot_ask_and_a_lead_goes_only_to_an_agent_who_asked():
    _, board, _ = await setup(lead("rahul"))
    for call in (board.ask(OWNER, ref_of("rahul")), board.give(OWNER, ref_of("rahul"), HD)):
        try:
            await call
            assert False, "should be refused"
        except InboxError as e:
            assert e.status_code in (404, 409)


async def test_a_lead_from_a_team_or_agent_number_is_a_test_and_the_owner_removes_any_other():
    db, board, _ = await setup(lead("buyer"), lead("ours", phone="+919767900001"), lead("signin", phone="+919800000009"),
                               lead("tried", phone="+919800000010"))
    await db.get_collection("users").insert_one({"_id": "u1", "phone": "9800000009"})   # an older sign-in stored without +91
    assert {c["ref"] for c in (await board.cards(OWNER))["items"]} == {ref_of("buyer"), ref_of("tried")}
    await board.ask(HD, ref_of("tried"))
    await board.remove(OWNER, ref_of("tried"))
    assert [c["ref"] for c in (await board.cards(HD))["items"]] == [ref_of("buyer")]
    assert (await db.get_collection("lead_asks").find_one({"_id": "tried:HD"}))["status"] == "removed"
    try:
        await board.remove(HD, ref_of("buyer"))
        assert False, "an agent removed a lead"
    except InboxError as e:
        assert e.status_code == 403


async def test_a_lead_passed_before_reads_as_open_and_giving_it_moves_it_from_the_agent_who_has_it():
    db, board, _ = await setup(lead("saket", agent_id=HD, passed_by=OWNER, passed_to=HD, passed_at=NOW - timedelta(days=1),
                                    handover={"by": "owner"}))
    for agent in (HD, STAVAN):   # nothing says it was shared, to anyone but the owner
        seen = (await board.cards(agent))["items"][0]
        assert "lead_id" not in seen and "holder" not in seen and "with_agent" not in seen
    assert "holder" not in (await board.cards(OWNER))["items"][0]   # the owner's card says nothing of it either
    await board.ask(HD, ref_of("saket"))
    alert = await db.get_collection("notifications").find_one({"kind": "lead_asked"})
    assert alert["agent_id"] == OWNER   # the owner hears of the ask, not the agent holding it
    await board.ask(STAVAN, ref_of("saket"), "fee", 1500)
    r = await board.give(OWNER, ref_of("saket"), STAVAN)
    moved = await db.get_collection("contacts").find_one({"_id": "saket"})
    assert r["passed_to"] == "Stavan" and moved["agent_id"] == STAVAN and moved["passed_by"] == OWNER



async def test_the_card_tells_what_they_read_on_how_many_days_from_which_device_and_city():
    db, board, _ = await setup(lead("rahul"))
    ev = db.get_collection("events")
    for i, (path, day, read) in enumerate([("/projects/mansha-phase-ii-wagholi?src=fb", 0, 240), ("/projects/area/wagholi/2-bhk", 0, 60),
                                           ("/projects/mansha-phase-ii-wagholi", 2, 120), ("/projects/ivy-estate-wagholi", 2, 10),
                                           ("/enquire", 2, 5)]):
        await ev.insert_one({"_id": f"e{i}", "contact_id": "rahul", "type": "page_view", "path": path, "read_s": read,
                             "ts": NOW - timedelta(days=3 - day, minutes=10 - i), "device": "Android phone · Chrome", "area": "Wagholi, Maharashtra"})
    await ev.insert_one({"_id": "w", "contact_id": "rahul", "type": "whatsapp_click", "ts": NOW - timedelta(days=1)})
    c = (await board.cards(HD))["items"][0]
    a = c["activity"]
    assert [(p["label"], p["minutes"]) for p in a["pages"]] == [("Mansha Phase-II", 6), ("Wagholi projects (2 BHK)", 1), ("Ivy Estate Wagholi", 0)]
    assert (a["visits"], a["days"], a["device"], a["city"], a["projects_seen"]) == (2, 2, "Phone", "Wagholi", 2)
    assert "Came back on 2 different days" in c["signals"] and "Compared 2 projects" in c["signals"] and "Tapped WhatsApp" in c["signals"]
    assert c["caution"] is None


async def test_an_enquiry_from_a_signed_in_studio_browser_is_a_test():
    db, board, _ = await setup(lead("ours"), lead("buyer", phone="+919876500002"))
    await db.get_collection("events").insert_one({"_id": "s", "contact_id": "ours", "type": "page_view", "path": "/", "ts": NOW, "staff": True})
    assert [c["ref"] for c in (await board.cards(HD))["items"]] == [ref_of("buyer")]


async def test_giving_a_lead_to_the_agent_who_already_has_it_leaves_it_with_them():
    db, board, wa = await setup(lead("saket", agent_id=HD, passed_by=OWNER, passed_to=HD, handover={"by": "owner"}))
    await board.ask(HD, ref_of("saket"))
    r = await board.give(OWNER, ref_of("saket"), HD)
    kept = await db.get_collection("contacts").find_one({"_id": "saket"})
    assert r["passed_to"] == "House Deal" and kept["agent_id"] == HD and kept["handover"]["by"] == "board" and wa.sent == []


async def test_a_reply_to_our_whatsapp_is_a_reply_not_a_conversation_with_us():
    db, board, _ = await setup(lead("vikram", calls=[]))
    await db.get_collection("whatsapp_conversations").insert_one({"_id": "P:919876500001", "wa_id": "919876500001", "lead_id": "vikram",
        "agent_id": OWNER, "messages": [{"role": "agent", "sent_by": "auto", "text": "Namaste", "ts": NOW - timedelta(days=1)},
                                        {"role": "user", "text": "Yes", "ts": NOW - timedelta(days=1)},
                                        {"role": "user", "text": "Katraj", "ts": NOW - timedelta(days=1)}]})
    c = (await board.cards(HD))["items"][0]
    assert c["genuine"] == "replied" and "Replied to us on WhatsApp (2 messages)" in c["signals"]
