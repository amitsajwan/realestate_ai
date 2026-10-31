"""Lead board (inbox/board.py): agents see the owner's open leads without name or number, ask for one with an offer, and the owner
gives it to one of them (owner, 2026-10-31)."""
from datetime import datetime, timedelta

from app.modules.inbox.board import LeadBoard, ref_of
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
    assert c["age"] == "Came in 2 days ago" and c["came_from"] == "Google search" and c["genuine"] == "talked"
    assert "Picked up our call" in c["signals"] and "Told us their budget, BHK, when themselves" in c["signals"]
    shown = repr(c)
    for secret in ("Rahul", "Thombare", "98765", "rahul", "call me"):
        assert secret not in shown, secret


async def test_won_given_from_the_board_old_test_and_numberless_leads_stay_off_the_board():
    _, board, _ = await setup(lead("ok"), lead("won", stage="won"), lead("given", agent_id=STAVAN, passed_by=OWNER, passed_to=STAVAN,
                                                                          handover={"by": "board"}), lead("old", ago=timedelta(days=40)),
                              lead("test", name="claude test"), lead("nonum", phone=""))
    assert [c["ref"] for c in (await board.cards(HD))["items"]] == [ref_of("ok")]


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
    assert (await board.cards(HD))["items"] == []
    closed = await db.get_collection("notifications").find_one({"agent_id": HD, "kind": "lead_ask_closed"})
    assert closed is not None


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


async def test_a_lead_passed_before_is_on_the_board_for_others_and_giving_it_moves_it_from_the_agent_who_has_it():
    db, board, _ = await setup(lead("saket", agent_id=HD, passed_by=OWNER, passed_to=HD, passed_at=NOW - timedelta(days=1),
                                    handover={"by": "owner"}))
    assert (await board.cards(HD))["items"] == []   # House Deal has it already
    seen = (await board.cards(STAVAN))["items"][0]
    assert seen["with_agent"] is True and "holder" not in seen
    assert (await board.cards(OWNER))["items"][0]["holder"] == "House Deal"
    await board.ask(STAVAN, ref_of("saket"), "fee", 1500)
    r = await board.give(OWNER, ref_of("saket"), STAVAN)
    moved = await db.get_collection("contacts").find_one({"_id": "saket"})
    assert r["passed_to"] == "Stavan" and moved["agent_id"] == STAVAN and moved["passed_by"] == OWNER
    assert (await board.cards(STAVAN))["items"] == [] and (await board.cards(OWNER))["items"] == []
