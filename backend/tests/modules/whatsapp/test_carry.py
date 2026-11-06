"""What a buyer told us on the website goes with them to WhatsApp (owner, 2026-11-06: "chat means WhatsApp also, and context should be kept").
A WhatsApp chat used to start empty, so a buyer who had given their size and budget was asked again."""
from datetime import timedelta
from urllib.parse import unquote

import pytest

from app.modules.chat import carry, engine
from app.modules.chat.service import ChatService
from app.modules.newsroom.store import Store
from app.modules.tracking.service import TrackingService

from ..fakes import FakeDb
from .helpers import BUYER, NOW, PID, make, say

pytestmark = pytest.mark.asyncio
PHONE = "+" + BUYER
PLAN = "/home-plan/result?work=kharadi&budget=under-75l&bhk=2&movein=by-2027&kids=school&elders=1"
IVARA = {"_id": "P52100000001", "regno": "P52100000001", "name": "GODREJ IVARA", "promoter": "Godrej Properties Limited", "locality": "kharadi",
         "page_slug": "godrej-ivara-kharadi", "completion_now": "2029-10-30", "units_total": 400, "units_booked": 100}


class Prompted:
    def __init__(self):
        self.calls = []

    async def json(self, system, user):
        self.calls.append((system, user))
        return {"intent": "question"} if len(self.calls) % 2 == 1 else {"reply": "Sure.", "question": "", "needs_team": False}

    async def text(self, system, user, **kw):
        return "Sure."


async def conv_of(db):
    return await db.get_collection("whatsapp_conversations").find_one({"_id": f"{PID}:{BUYER}"})


async def website_session(db, ref="ab12cd34", **data):
    await db.get_collection("chat_sessions").insert_one({
        "_id": "websession0001", "agent_slug": "avasetu", "wa_ref": ref, "messages": [], "hits": [], "created_at": NOW,
        "data": {**engine.new_data(localise=True), "locality": "Wagholi", "bhk": 2, "budget_max": 7_500_000, "questions": ["Is it RERA approved?"],
                 "read": [{"kind": "project", "name": "Godrej Ivara", "label": "Godrej Ivara", "path": "/projects/godrej-ivara-kharadi"}], **data}})


async def website_lead(db, **kw):
    await db.get_collection("contacts").insert_one({
        "_id": "lead1", "agent_id": "OWNER", "name": "Priya", "phone": PHONE, "anon_ids": ["browser-0001", "whatsapp:" + BUYER], "last_activity_at": NOW,
        "requirement": {"bhk": 3, "budget_min_inr": None, "budget_max_inr": 15_000_000, "localities": ["Kharadi"]}, **kw})


def test_the_chats_reference_is_found_and_taken_out_of_what_the_buyer_said():
    text = "Hi Avasetu, I am looking for a home: 2 BHK. (chat ab12cd34)"
    assert carry.ref_in(text) == "ab12cd34"
    assert carry.without_ref(text) == "Hi Avasetu, I am looking for a home: 2 BHK."
    assert carry.ref_in("Hi, 2 BHK please") is None


async def test_continue_on_whatsapp_carries_the_chat_across_and_nothing_is_asked_again():
    svc, db, _, _ = make(llm=Prompted())
    await website_session(db)
    await say(svc, "Hi Avasetu, I am looking for a home: 2 BHK in Wagholi. (chat ab12cd34)")
    d = (await conv_of(db))["data"]
    assert (d["locality"], d["bhk"], d["budget_max"]) == ("Wagholi", 2, 7_500_000)
    prompt = svc.llm.calls[-1][1]
    assert "EARLIER IN THIS VISIT THEY READ: Godrej Ivara" in prompt and "asked on our website: Is it RERA approved?" in prompt


async def test_the_language_of_the_website_chat_comes_too():
    svc, db, _, _ = make(llm=Prompted())
    await website_session(db, lang="mr")
    await say(svc, "Hi Avasetu, I am looking for a home. (chat ab12cd34)")
    assert (await conv_of(db))["language"] == "mr"


async def test_a_website_lead_writing_on_whatsapp_keeps_their_requirement_and_what_they_read():
    svc, db, _, _ = make(llm=Prompted())
    await Store(db).projects.insert_one(dict(IVARA))
    await website_lead(db)
    db.get_collection("events").docs += [
        {"_id": "e1", "agent_id": "OWNER", "anon_id": "browser-0001", "type": "page_view", "path": "/projects/godrej-ivara-kharadi", "ts": NOW - timedelta(days=2)},
        {"_id": "e2", "agent_id": "OWNER", "anon_id": "browser-0001", "type": "page_view", "path": PLAN, "ts": NOW - timedelta(days=2)},
        {"_id": "e3", "agent_id": "OWNER", "anon_id": "someone-else", "type": "page_view", "path": "/projects/lodha-camelot", "ts": NOW}]
    await say(svc, "what are the prices?")
    d = (await conv_of(db))["data"]
    assert (d["locality"], d["bhk"], d["budget_max"]) == ("Kharadi", 3, 15_000_000)
    assert d["plan"]["bhk"] == 2
    prompt = svc.llm.calls[-1][1]
    assert "Godrej Ivara" in prompt and "Home plan: 2 BHK" in prompt and "camelot" not in prompt.lower()


async def test_what_they_said_on_whatsapp_is_never_replaced():
    d = {**engine.new_data(), "bhk": 3, "locality": "Baner", "budget_max": 20_000_000}
    carry.apply(d, {"bhk": 2, "locality": "Wagholi", "budget_max": 7_500_000, "budget_min": None, "read": [], "questions": []})
    assert (d["bhk"], d["locality"], d["budget_max"]) == (3, "Baner", 20_000_000)


def test_a_plan_read_on_the_website_is_named_once():
    label = "Home plan: 2 BHK, Under ₹75 L, works in Kharadi"
    d = engine.new_data()
    carry.apply(d, {"plan": {"label": label}, "read": ["Godrej Ivara", label], "questions": []})
    assert d["carried_read"] == ["Godrej Ivara", label]


async def test_someone_we_have_never_met_starts_a_clean_chat_and_it_is_looked_up_once():
    svc, db, _, _ = make(llm=Prompted())
    await say(svc, "what are the prices?")
    d = (await conv_of(db))["data"]
    assert d["carried"] is True and not d.get("carried_read")


async def test_a_lead_with_no_number_is_nobody():
    db = FakeDb()
    db.get_collection("contacts").docs.append({"_id": "anon", "agent_id": "A", "phone": "", "requirement": {"bhk": 2}})
    assert await carry.from_lead(db, "") is None


async def test_the_websites_whatsapp_link_names_the_chat_it_came_from(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PUBLIC_NUMBER", "919834256406")
    db = FakeDb()
    s = ChatService(db, TrackingService(db, now=lambda: NOW), None, now=lambda: NOW)
    url = unquote(await s.whatsapp_url({**engine.new_data(), "bhk": 2.0}, None, "ab12cd34"))
    assert url.endswith("I am looking for a home: 2 BHK. (chat ab12cd34)")


async def test_a_session_found_by_its_reference_gives_what_the_buyer_said():
    db = FakeDb()
    await website_session(db)
    found = await carry.session_by_ref(db, "ab12cd34")
    assert (found["locality"], found["budget_max"], found["project"]) == ("Wagholi", 7_500_000, "Godrej Ivara")
    assert await carry.session_by_ref(db, "ffffffff") is None


async def test_marathi_as_our_follow_up_invites_stays_marathi_on_whatsapp():
    svc, db, _, _ = make(llm=Prompted())
    await say(svc, "Marathi")
    conv = await conv_of(db)
    assert conv["language"] == "mr_latn"
    assert any(m["text"].startswith("Nakki, aata Marathit boluya.") for m in conv["messages"] if m["role"] == "bot")


async def test_the_home_plan_goes_as_a_link_in_a_whatsapp_message(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in")
    class Unsure(Prompted):
        async def json(self, system, user):
            if system.startswith("You are"):
                return {"reply": "Happy to help you choose.", "question": "", "needs_team": False}
            return {"intent": "suggest", "who": "buyer", "need": "homes"}
    svc, db, _, _ = make(llm=Unsure())
    await say(svc, "not sure which project, you suggest")
    conv = await conv_of(db)
    assert any("Try the home plan: https://avasetu.in/home-plan" in m["text"] for m in conv["messages"] if m["role"] == "bot")
