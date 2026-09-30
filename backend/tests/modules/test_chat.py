from datetime import datetime, timedelta

import pytest

from app.modules.chat import engine, kb
from app.modules.chat.service import ChatError, ChatService
from app.modules.tracking.service import TrackingError

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio


class FakeLLM:
    def __init__(self, reply=None):
        self.reply, self.calls = reply, 0

    async def json(self, system, user):
        self.calls += 1
        return self.reply


async def say(d, text, llm=None):
    return await engine.turn(d, text, llm)


# ---- knowledge base ------------------------------------------------------------------------------------------
def test_kb_answers_the_common_questions():
    assert kb.best("How do I check RERA?").id == "rera"
    assert kb.best("what is carpet area").id == "carpet"
    assert kb.best("is the metro running in wagholi").id in ("metro", "wagholi")
    assert kb.best("tell me about upper kharadi").id == "upper_kharadi"
    assert kb.best("blah blah nothing relevant") is None


def test_kb_never_states_prices_or_predictions():
    import re
    text = " ".join(e.answer for e in kb.ENTRIES)
    assert not re.search(r"₹|\bRs\.?\s?\d|appreciat|will (rise|increase)|invest now|guarantee|best |dream", text, re.I)
    assert "not the same as running" in kb.best("metro").answer


# ---- a whole conversation, the way a buyer would do it -----------------------------------------------------
async def test_full_journey_captures_requirement_then_phone_with_consent_and_makes_one_lead():
    d = engine.new_data()
    t = await say(d, "hi")
    assert "buy or to rent" in t.reply and t.quick == ["Buy", "Rent", "Just exploring"] and not t.lead
    t = await say(d, "Buy")
    assert d["tx"] == "buy" and "Which area" in t.reply
    t = await say(d, "Kharadi")
    assert d["locality"] == "Kharadi" and "bedrooms" in t.reply
    t = await say(d, "2 BHK")
    assert d["bhk"] == 2 and "budget" in t.reply
    t = await say(d, "80 lakh to 1.2 crore")
    assert d["budget_min"] == 8_000_000 and d["budget_max"] == 12_000_000 and "planning to move" in t.reply
    t = await say(d, "In 1-3 months")
    assert d["timeline"] == "1_3_months" and "call you" in t.reply
    t = await say(d, "Priya Sharma")
    assert d["name"] == "Priya Sharma" and "mobile number" in t.reply and engine.CONSENT in t.reply and d["consent_shown"]
    assert not t.lead
    t = await say(d, "98765 43210")
    assert t.lead and t.lead["phone"] == "+919876543210" and t.lead["name"] == "Priya Sharma"
    assert t.lead["bhk"] == 2 and t.lead["budget_min_inr"] == 8_000_000 and "Kharadi" in t.lead["message"] and "1-3-months" in t.lead["message"]
    t2 = await say(d, "thanks")
    assert t2.lead is None  # one lead per conversation


async def test_a_question_in_the_middle_is_answered_and_the_same_question_is_asked_again():
    d = engine.new_data()
    await say(d, "hello")
    await say(d, "buy")
    t = await say(d, "How do I check RERA?")
    assert "MahaRERA" in t.reply and "Which area" in t.reply and d["asked"] == "locality"
    assert d["questions"] == ["How do I check RERA?"]


async def test_one_message_can_answer_several_things():
    d = engine.new_data()
    await say(d, "hi")
    t = await say(d, "I want to buy a 3 BHK in Wagholi under 90 lakh")
    assert (d["tx"], d["locality"], d["bhk"], d["budget_max"]) == ("buy", "Wagholi", 3, 9_000_000)
    assert "Got it" in t.reply and "planning to move" in t.reply


async def test_a_number_volunteered_early_needs_a_yes_and_never_creates_a_lead_by_itself():
    d = engine.new_data()
    await say(d, "hi")
    t = await say(d, "call me on 9876543210")
    assert t.lead is None and d["pending_phone"] == "+919876543210" and d["phone"] is None
    assert "Reply YES" in t.reply and engine.CONSENT in t.reply
    t = await say(d, "yes")
    assert t.lead and t.lead["phone"] == "+919876543210"


async def test_declining_the_number_is_respected_and_not_asked_again():
    d = engine.new_data()
    for m in ("hi", "buy", "Kharadi", "2 bhk", "under 1 crore", "just looking", "Rahul"):
        await say(d, m)
    t = await say(d, "not now")
    assert "phone" in d["declined"] and not t.lead and "mobile" not in t.reply
    t = await say(d, "what is a carpet area?")
    assert "mobile" not in t.reply and not d["phone"]


async def test_a_bad_number_is_never_accepted():
    d = engine.new_data()
    for m in ("hi", "buy", "Kharadi", "2 bhk", "1 crore", "now", "Amit"):
        await say(d, m)
    t = await say(d, "12345")
    assert t.lead is None and d["phone"] is None


# ---- unknown questions, LLM, abuse, humans -------------------------------------------------------------
async def test_unknown_questions_are_not_guessed_and_go_to_a_person():
    d = engine.new_data()
    await say(d, "hi")
    t = await say(d, "Which school is nearest to Sky Heights tower B?")
    assert "do not want to guess" in t.reply and d["needs_human"] is True
    assert "mobile number" in t.reply  # a person will need a way to reply


async def test_llm_answers_only_from_the_knowledge_and_unsafe_drafts_are_rejected():
    ok = FakeLLM({"answerable": True, "answer": "Bring income proofs and ID when you talk to the bank."})
    d = engine.new_data()
    await say(d, "hi")
    t = await say(d, "What documents do I need for a bank loan?", ok)
    assert t.reply.startswith("Most buyers use a home loan") or "income proofs" in t.reply  # the vetted answer wins
    bad = FakeLLM({"answerable": True, "answer": "It costs ₹90 lakh, call 9876543210."})
    d2 = engine.new_data()
    await say(d2, "hi")
    t = await say(d2, "Does the builder offer a payment plan for loan on Ganga Heights?", bad)
    assert "9876543210" not in t.reply and "90" not in t.reply


async def test_asking_for_a_human_flags_the_chat():
    d = engine.new_data()
    await say(d, "hi")
    t = await say(d, "I want to talk to a real person")
    assert t.needs_human and "our team can take it from here" in t.reply


async def test_abuse_is_not_argued_with():
    d = engine.new_data()
    t = await say(d, "you are all fraud and liars")
    assert t.needs_human and "pass this to our team" in t.reply


# ---- service: sessions, limits, leads -------------------------------------------------------------------------
class FakeTracking:
    def __init__(self, fail=False):
        self.inquiries, self.fail = [], fail

    async def capture_inquiry(self, i):
        if self.fail:
            raise TrackingError("Too many enquiries", 429)
        self.inquiries.append(i)
        return {"received": True, "new_lead": True}


def svc(tracking=None, llm=None, clock=None):
    db = FakeDb()
    db.get_collection("agent_public_profiles").docs.append({"slug": "rahul", "is_public": True, "agent_id": "A1"})
    now = clock or (lambda: datetime(2026, 9, 30, 12, 0, 0))
    return ChatService(db, tracking or FakeTracking(), llm, now=now), db


SID = "session-abcdef123456"


async def test_service_creates_exactly_one_lead_with_consent_and_source():
    tr = FakeTracking()
    s, db = svc(tr)
    for m in ("hi", "buy", "Wagholi", "2 bhk", "50-80 lakh", "just looking", "Meera Joshi"):
        r = await s.message(SID, "rahul", m)
    assert not r["lead_created"]
    r = await s.message(SID, "rahul", "9822012345")
    assert r["lead_created"] and len(tr.inquiries) == 1
    i = tr.inquiries[0]
    assert i.consent is True and i.source == "chat" and i.agent_slug == "rahul" and i.phone == "+919822012345" and i.name == "Meera Joshi"
    assert i.anon_id.startswith("chat-") and len(db.get_collection("chat_sessions").docs) == 1
    r = await s.message(SID, "rahul", "thanks a lot")
    assert not r["lead_created"] and len(tr.inquiries) == 1


async def test_a_rate_limited_lead_still_gets_a_kind_reply():
    s, _ = svc(FakeTracking(fail=True))
    for m in ("hi", "buy", "Wagholi", "2 bhk", "1 crore", "now", "Meera"):
        await s.message(SID, "rahul", m)
    r = await s.message(SID, "rahul", "9822012345")
    assert not r["lead_created"] and "already have your details" in r["reply"]


@pytest.mark.parametrize("sid,text,slug,code", [("short", "hi", "rahul", 400), (SID, "", "rahul", 400), (SID, "x" * 501, "rahul", 400), (SID, "hi", "nobody", 404)])
async def test_bad_input_is_rejected(sid, text, slug, code):
    s, _ = svc()
    with pytest.raises(ChatError) as e:
        await s.message(sid, slug, text)
    assert e.value.status_code == code


async def test_the_hourly_limit_stops_a_flood():
    t = [datetime(2026, 9, 30, 12, 0, 0)]
    s, _ = svc(clock=lambda: t[0])
    for _ in range(60):
        await s.message(SID, "rahul", "hi there")
    r = await s.message(SID, "rahul", "hi there")
    assert "try again a little later" in r["reply"]
    t[0] += timedelta(hours=2)
    assert "try again" not in (await s.message(SID, "rahul", "hello"))["reply"]


@pytest.mark.parametrize("q,expect", [("Under 50 lakh", (None, 5_000_000)), ("50-80 lakh", (5_000_000, 8_000_000)), ("80 lakh to 1.2 crore", (8_000_000, 12_000_000)),
                                      ("1.2 to 2 crore", (12_000_000, 20_000_000)), ("Above 2 crore", (20_000_000, None))])
async def test_every_budget_quick_reply_is_understood(q, expect):
    d = engine.new_data()
    d["asked"] = "budget"
    engine.extract(d, q)
    assert (d["budget_min"], d["budget_max"]) == expect


async def test_every_quick_reply_offered_is_understood_by_the_next_step():
    for field_name in ("tx", "locality", "bhk", "timeline"):
        for q in engine.PROMPTS[field_name][1]:
            d = engine.new_data()
            d["asked"] = field_name
            new = engine.extract(d, q)
            assert field_name in new or (field_name == "tx" and q == "Just exploring"), (field_name, q)


async def test_the_agent_sees_chats_that_need_them_and_never_a_phone_number():
    s, db = svc(FakeTracking())
    await s.message(SID, "rahul", "hi")
    await s.message(SID, "rahul", "Which school is nearest to Sky Heights tower B?")
    other = "other-session-1234567"
    for m in ("hi", "buy", "Wagholi", "2 bhk", "1 crore", "now", "Meera", "9822012345"):
        await s.message(other, "rahul", m)
    rows = await s.conversations("A1")
    by_lead = {r["lead_created"]: r for r in rows}
    assert by_lead[False]["needs_human"] and "school" in by_lead[False]["questions"][0]
    assert by_lead[True]["name"] == "Meera" and not by_lead[True]["needs_human"]
    assert "9822012345" not in str(rows) and await s.conversations("NOBODY") == []


def test_timeline_acknowledgement_reads_naturally():
    d = engine.new_data()
    d["asked"] = "timeline"
    new = engine.extract(d, "In 1-3 months")
    assert "moving in 1-3 months" in engine._ack(new, d)
