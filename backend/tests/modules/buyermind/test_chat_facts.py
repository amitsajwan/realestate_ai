"""WhatsApp and DM replies say what the buyer mind checked for the lead (docs/plan/buyer-mind.md step 4, owner 2026-11-18: "handle as
much as we can with our agents"). Only what the checks held to a lookup reaches the buyer: the problems to tell them, the published
price range and the projects it looked up; never what it read into them, never its draft, never a stale or unsure brief."""
from datetime import datetime, timedelta

from app import wiring
from app.modules.buyermind import chat_facts
from app.modules.chat import agent as chat_agent
from app.modules.whatsapp import adapters
from app.modules.whatsapp.brain import ChatBrain

from ..fakes import FakeDb

NOW = datetime(2026, 10, 23, 10, 0)
BRIEF = {"by": "mind", "confidence": "medium", "draft": "Namaste Rahul ji, a draft for the agent", "implied": ["Family: asked about schools"],
         "flags": ["Possession is due 2027-12-31, after the 3-6 months he wants"],
         "price_idea": "2 BHK from ₹68 Lakh to ₹74 Lakh on puraniks.com, read 2026-10-20, indicative",
         "alternatives": [{"slug": "kohinoor-ravet-ready", "name": "Kohinoor Ravet Ready", "why": "completed, ₹62 Lakh"}]}
PRICE_REPLY = "2 BHK homes are listed from ₹68 Lakh to ₹74 Lakh on the builder's website as of 20 Oct 2026, indicative."


async def db_with(brief=BRIEF, at=NOW - timedelta(days=1), lead="L"):
    db = FakeDb()
    await db.get_collection("lead_briefs").insert_one({"_id": lead, "agent_id": "OWNER", "at": at, "brief": brief})
    return db


async def test_the_chat_gets_the_checked_findings_in_plain_words_and_nothing_else():
    facts = await chat_facts(await db_with(), "L", NOW)
    assert facts == ["To tell them: Possession is due 31 December 2027, after the 3-6 months he wants",
                     "Published prices (indicative, not a quote): 2 BHK from ₹68 Lakh to ₹74 Lakh on puraniks.com, read 20 October 2026, indicative",
                     "Other projects in the area our team looked up for them: Kohinoor Ravet Ready"]
    said = " ".join(facts)
    assert "schools" not in said and "draft" not in said and "₹62" not in said   # a reading, the draft, an unchecked "why"


async def test_no_findings_without_a_lead_or_from_a_brief_that_is_rules_only_unsure_or_stale():
    assert await chat_facts(await db_with(), None, NOW) == []
    assert await chat_facts(await db_with(), "other-lead", NOW) == []
    assert await chat_facts(await db_with({**BRIEF, "by": "rules"}), "L", NOW) == []
    assert await chat_facts(await db_with({**BRIEF, "confidence": "low"}), "L", NOW) == []
    assert await chat_facts(await db_with(at=NOW - timedelta(days=8)), "L", NOW) == []


class Model:
    """The chat agent's two calls: understand, then the reply."""
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    async def json(self, system, user):
        self.calls.append(user)
        return {"intent": "question"} if len(self.calls) == 1 else {"reply": self.reply, "question": "", "needs_team": False}


async def test_a_price_the_mind_checked_may_be_said_and_the_same_price_without_it_is_refused():
    facts = await chat_facts(await db_with(), "L", NOW)
    d = adapters.new_chat_state("+919822000001", "Rahul")
    d["checked_for_them"] = facts
    model = Model(PRICE_REPLY)
    t = await chat_agent.turn(d, "What are the prices?", model, None, history=[], channel="message")
    assert t.reply == PRICE_REPLY and not t.needs_human
    assert "Checked for this buyer by our team" in model.calls[1] and "₹68 Lakh" in model.calls[1]
    bare = adapters.new_chat_state("+919822000001", "Rahul")
    t = await chat_agent.turn(bare, "What are the prices?", Model(PRICE_REPLY), None, history=[], channel="message")
    assert t.reply != PRICE_REPLY and t.needs_human   # no checked price: not said, the team takes it


async def test_the_whatsapp_brain_reads_the_leads_findings_each_turn_and_drops_them_when_gone(monkeypatch):
    db = await db_with(at=datetime.utcnow() - timedelta(hours=1))   # the brain reads with the clock: a fresh brief
    monkeypatch.setattr(adapters, "_brief_facts", chat_facts)
    brain = ChatBrain()
    brain.db, brain.llm = db, Model(PRICE_REPLY)
    conv = {"data": adapters.new_chat_state("+919822000001", "Rahul"), "lead_id": "L", "context": None, "agent_id": None, "messages": []}
    reply = await brain._buyer_answer(conv, "What are the prices?", "en")
    assert "₹68 Lakh" in reply and conv["data"]["checked_for_them"][1].startswith("Published prices")
    await db.get_collection("lead_briefs").delete_one({"_id": "L"})
    brain.llm = Model("We will check.")
    await brain._buyer_answer(conv, "And the possession?", "en")
    assert "checked_for_them" not in conv["data"]


async def test_a_failing_read_never_stops_the_reply(monkeypatch):
    async def broken(db, lead_id):
        raise RuntimeError("db down")
    monkeypatch.setattr(adapters, "_brief_facts", broken)
    assert await adapters.brief_facts(FakeDb(), "L") == []
    monkeypatch.setattr(adapters, "_brief_facts", None)
    assert await adapters.brief_facts(FakeDb(), "L") == []


def test_wiring_gives_whatsapp_the_buyer_minds_findings():
    wiring.wire()
    assert adapters._brief_facts is chat_facts
