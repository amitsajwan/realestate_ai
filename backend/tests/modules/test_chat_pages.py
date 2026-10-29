"""The chat knows the page (owner, 2026-10-29: "For agents should be only page where we know it is agent, and elsewhere customer. Also the
bot should know what page the person is enquiring from, so it can ask the next question"). Each page kind gets its own greeting and first
question; the pages for agents greet agents, every other page treats the visitor as a buyer, and WhatsApp answers agents as before."""
from datetime import datetime

import pytest

from app.modules.chat import agent as chat_agent, engine, phrases
from app.modules.chat.service import ChatService
from app.modules.knowledge import site
from app.modules.newsroom.store import Store
from app.modules.tracking.service import TrackingService

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio
NOW = datetime(2026, 10, 29, 12, 0, 0)
ASKS = {f: phrases.say("ask_" + f) for f in ("tx", "locality", "bhk", "budget")}
IVARA = {"_id": "P52100000001", "regno": "P52100000001", "name": "GODREJ IVARA", "promoter": "Godrej Properties Limited", "locality": "kharadi",
         "page_slug": "godrej-ivara-kharadi", "completion_now": "2029-10-30", "units_total": 400, "units_booked": 100}


class PromptLLM:
    """Answers the two agent.py calls in turn and keeps what each was told."""
    def __init__(self, understand, reply):
        self.understand, self.reply, self.calls = understand, reply, []

    async def json(self, system, user):
        self.calls.append((system, user))
        return self.understand if len(self.calls) % 2 == 1 else self.reply


async def service(llm=None, agent=False, projects=()):
    db = FakeDb()
    db.get_collection("agent_public_profiles").docs += [{"slug": "avasetu", "is_public": True, "agent_id": "HOUSE"},
                                                        {"slug": "rahul", "is_public": True, "agent_id": "A1"}]
    for p in projects:
        await Store(db).projects.insert_one(dict(p))
    return ChatService(db, TrackingService(db, now=lambda: NOW), llm, now=lambda: NOW, agent=agent)


async def talk(s, msgs, context=None, sid="session-pages-abcdef12", slug="avasetu", path=None):
    return [await s.message(sid, slug, m, context=context, visit={"path": path} if path else None) for m in msgs]


# ---- a greeting and first question for each kind of page -----------------------------------------------------------------------
async def test_a_project_page_greeting_names_the_project_and_offers_its_price_sheet_plans_and_a_visit_then_asks_the_size():
    s = await service(projects=[IVARA])
    r = (await talk(s, ["hi"], context={"page": "project", "project": "godrej-ivara-kharadi"}))[0]
    assert r["reply"] == ("Asking about Godrej Ivara? I can get you its price sheet and floor plans, or set up a site visit. "
                          "Which size (BHK) are you looking for?")
    assert r["quick_replies"][:2] == ["Price sheet & floor plans", "Site visit"]
    assert ASKS["locality"] not in r["reply"]


async def test_on_a_project_page_tapping_price_sheet_hands_off_with_the_price_sheet_line_and_the_number_ask():
    s = await service(agent=True, projects=[IVARA])
    r = (await talk(s, ["hi", "Price sheet & floor plans"], context={"page": "project", "project": "godrej-ivara-kharadi"}))[-1]
    assert r["reply"].startswith("Share your mobile number and the Avasetu team will WhatsApp you today's price sheet and floor plans.")
    assert phrases.say("consent") in r["reply"] and r["quick_replies"] == ["Not now"]


async def test_on_a_project_page_tapping_site_visit_hands_off_to_fix_the_visit():
    s = await service(agent=True, projects=[IVARA])
    r = (await talk(s, ["hi", "Site visit"], context={"page": "project", "project": "godrej-ivara-kharadi"}))[-1]
    assert r["reply"].startswith("Share your mobile number and the Avasetu team will call you to fix your site visit.")
    session = await s.sessions.find_one({"_id": "session-pages-abcdef12"})
    assert session["data"]["visit_wanted"] and session["data"]["locality"] == "Kharadi"


async def test_a_project_slug_that_is_not_a_page_gets_the_general_greeting():
    s = await service()
    r = (await talk(s, ["hi"], context={"page": "project", "project": "no-such-project"}))[0]
    assert r["reply"].startswith("Hi! I am the Avasetu assistant.")


async def test_a_top_list_greets_with_its_list_and_area_and_asks_the_size_never_the_area():
    s = await service()
    r = (await talk(s, ["hi"], context={"page": "list", "locality": "kharadi", "list": "top"}))[0]
    assert r["reply"] == f"Looking at the top projects in Kharadi? {ASKS['bhk']}"
    assert ASKS["locality"] not in r["reply"] and ASKS["tx"] not in r["reply"]


async def test_an_area_projects_page_and_its_lists_never_ask_which_area():
    s = await service()
    for i, ctx in enumerate([{"page": "list", "locality": "wagholi"}, {"page": "list", "locality": "viman-nagar", "list": "new-launches"},
                             {"page": "list", "locality": "upper-kharadi", "list": "ready-to-move"}]):
        tr = await talk(s, ["hi", "3 BHK"], context=ctx, sid=f"session-pages-list-{i:04d}")
        assert all(ASKS["locality"] not in r["reply"] for r in tr), tr
    r = (await talk(s, ["hi"], context={"page": "list", "locality": "viman-nagar", "list": "new-launches"}, sid="session-pages-vn-0001"))[0]
    assert r["reply"].startswith("Looking at new launch projects in Viman Nagar?")


async def test_a_bhk_list_takes_its_size_from_the_page_and_asks_the_budget():
    s = await service()
    r = (await talk(s, ["hi"], context={"page": "list", "locality": "wagholi", "bhk": 2}))[0]
    assert r["reply"] == f"Looking at 2 BHK homes in Wagholi? {ASKS['budget']}"
    session = await s.sessions.find_one({"_id": "session-pages-abcdef12"})
    assert session["data"]["bhk"] == 2 and session["data"]["locality"] == "Wagholi"


async def test_a_list_for_a_place_we_do_not_know_gets_the_general_greeting():
    s = await service()
    r = (await talk(s, ["hi"], context={"page": "list", "locality": "atlantis"}))[0]
    assert r["reply"].startswith("Hi! I am the Avasetu assistant.")


async def test_a_builder_page_greets_with_the_builders_projects_and_offers_their_areas():
    s = await service(projects=[IVARA])
    r = (await talk(s, ["hi"], context={"page": "builder", "builder": "godrej-properties"}))[0]
    assert r["reply"] == "Looking at projects by Godrej Properties? Tell me which project, or which area you want."
    assert r["quick_replies"] == ["Kharadi"]
    r = (await talk(s, ["hi"], context={"page": "builder", "builder": "nobody-builders"}, sid="session-pages-nobody-01"))[0]
    assert r["reply"].startswith("Hi! I am the Avasetu assistant.")


async def test_a_guide_about_a_place_greets_with_the_place_and_asks_the_size():
    s = await service()
    r = (await talk(s, ["hi"], context={"page": "guide", "topic": "upper-kharadi"}))[0]
    assert r["reply"].startswith("Reading about Upper Kharadi?") and ASKS["bhk"] in r["reply"] and ASKS["locality"] not in r["reply"]
    r = (await talk(s, ["hi"], context={"page": "guide", "topic": "mhada-pune-lottery"}, sid="session-pages-guide-02"))[0]
    assert r["reply"].startswith("Hi! I am the Avasetu assistant.")


async def test_home_news_and_unknown_pages_get_the_general_buyer_greeting():
    s = await service()
    for i, ctx in enumerate([{"page": "home"}, {"page": "news"}, {"page": "other"}, {"page": "nonsense"}, None]):
        r = (await talk(s, ["hi"], context=ctx, sid=f"session-pages-home-{i:04d}"))[0]
        assert r["reply"] == phrases.say("greet") and r["quick_replies"] == ["Find a home"]


# ---- who the visitor is: agents only on the agents' pages ---------------------------------------------------------------------
async def test_im_an_agent_on_a_buyer_page_gets_only_the_agents_line_and_the_chat_stays_a_buyer_chat():
    s = await service()
    tr = await talk(s, ["hi", "I'm an agent"], context={"page": "project", "project": "x-y"})
    assert tr[1]["reply"] == "For agents, see /agents." and tr[1]["quick_replies"] == []
    r = (await talk(s, ["2 BHK in Kharadi under 90 lakh"], context={"page": "home"}))[0]
    assert "first month" not in r["reply"] and "/trial" not in r["reply"]
    for i, said in enumerate(["main agent hoon", "I am a broker", "free trial"]):
        r = (await talk(s, [said], context={"page": "home"}, sid=f"session-pages-agent-{i:03d}"))[0]
        assert r["reply"] == "For agents, see /agents.", said


async def test_im_an_agent_on_an_agents_own_site_is_a_buyer_page_too():
    s = await service()
    r = (await talk(s, ["hi", "I am an agent"], context={"page": "home", "site": "agent"}, slug="rahul", path="/agent/rahul"))[-1]
    assert r["reply"] == "For agents, see /agents."


async def test_a_buyer_page_never_offers_the_agents_answers():
    assert all(e.audience != "agent" for e in site.for_audience("buyer"))
    assert site.best("what is your pricing?", audience="buyer") is None or site.best("what is your pricing?", audience="buyer").audience != "agent"
    assert site.best("what is your pricing?").id == "agent_cost"   # WhatsApp and comment replies: unchanged
    d = engine.new_data()
    d["audience"] = "buyer"
    await engine.turn(d, "hi", None)
    t = await engine.turn(d, "do you have an app to install?", None)
    assert "No app to install" not in t.reply


async def test_the_agents_page_greets_agents_and_answers_with_the_pitch():
    s = await service()
    tr = await talk(s, ["hi", "I'm an agent", "what is avasetu?"], context={"page": "agents"}, path="/agents")
    assert tr[0]["reply"] == phrases.say("greet_agent") and tr[0]["quick_replies"] == ["Free trial", "Pricing", "How do I start?"]
    assert "first month is free" in tr[1]["reply"] and "/trial" in tr[1]["reply"]
    assert "real estate agents" in tr[2]["reply"] and "/trial" in tr[2]["reply"]
    r = (await talk(s, ["Pricing"], context={"page": "agents"}))[0]
    assert "small monthly fee" in r["reply"]


async def test_on_whatsapp_an_agent_still_hears_the_trial():
    from app.modules.whatsapp.adapters import new_chat_state
    d = new_chat_state("919822012345", "Sharad")
    assert d["audience"] is None
    t = await engine.turn(d, "I'm an agent", None)
    assert "first month is free" in t.reply and "/trial" in t.reply
    assert (await engine.turn(d, "what is avasetu?", None)).reply.startswith("Avasetu (आवास + सेतु: home + bridge) helps you find a new home")


# ---- the LLM path knows the page and whose voice it speaks in ----------------------------------------------------------------
REPLY_OK = {"reply": "Happy to help with that.", "question": "", "needs_team": False}


async def test_on_our_own_pages_the_model_is_told_the_page_and_speaks_for_our_team():
    llm = PromptLLM({"intent": "chat"}, REPLY_OK)
    s = await service(llm, agent=True, projects=[IVARA])
    await talk(s, ["hi", "thanks, looks nice"], context={"page": "project", "project": "godrej-ivara-kharadi"}, path="/projects/godrej-ivara-kharadi")
    (u_sys, u_user), (r_sys, r_user) = llm.calls[-2:]
    assert "Avasetu's own website" in u_sys and "real estate agent's site" not in u_sys
    assert "You work for our team" in r_sys and "the agent can" not in r_sys
    assert "PAGE: the page of the project Godrej Ivara; visitor: a home buyer" in u_user and "PAGE: the page of the project Godrej Ivara" in r_user


async def test_on_an_agents_own_site_the_model_speaks_for_the_agent():
    llm = PromptLLM({"intent": "chat"}, REPLY_OK)
    s = await service(llm, agent=True)
    await talk(s, ["hi", "thanks, looks nice"], context={"page": "home", "site": "agent"}, slug="rahul", path="/agent/rahul")
    _, (r_sys, _) = llm.calls[-2:]
    assert "on a Pune real estate agent's website" in r_sys and "You work for the agent" in r_sys


async def test_a_model_that_reads_an_agent_on_a_buyer_page_gets_the_agents_line_not_a_pitch():
    llm = PromptLLM({"intent": "agent"}, {"reply": "We make your website, posts and reels.", "question": "", "needs_team": False})
    s = await service(llm, agent=True)
    r = (await talk(s, ["hi", "do you work with brokers like me"], context={"page": "home"}))[-1]
    assert r["reply"] == "For agents, see /agents." and len(llm.calls) == 1


async def test_on_a_buyer_page_the_model_is_not_given_the_agents_answers():
    d = engine.new_data()
    d["audience"] = "buyer"
    assert "first month is free" not in chat_agent._knowledge(d, None)
    d["audience"] = "agent"
    assert "first month is free" in chat_agent._knowledge(d, None)


def test_every_new_page_sentence_is_written_in_all_five_languages():
    for key in ("greet_area", "greet_list", "greet_project", "greet_builder", "greet_agent", "for_agents", "ask_size", "handoff_web_sheet"):
        assert set(phrases.P[key]) == set(phrases.LANGS), key
    for key in ("sheet", "visit"):
        assert set(phrases.QUICK[key]) == set(phrases.LANGS), key
    for kind in ("all", "top", "new-launches", "ready-to-move", "bhk"):
        assert set(phrases.LIST_WHAT[kind]) == set(phrases.LANGS), kind
