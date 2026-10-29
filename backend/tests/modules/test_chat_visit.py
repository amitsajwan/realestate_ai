"""The chat uses the pages this visitor read in this visit (owner, 2026-10-29: "the website chat should use the pages this visitor read
during this visit, so it greets and asks the right next question, and the lead card shows what they read"). The pages come from our own
record of this browser's views (tracking.visits), each checked against our records; agents' pages keep their own greeting."""
from datetime import datetime, timedelta

import pytest

from app.modules.chat import engine, phrases, visit
from app.modules.chat.service import ChatService
from app.modules.newsroom.store import Store
from app.modules.tracking import visits
from app.modules.tracking.service import TrackingService

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio
NOW = datetime(2026, 10, 29, 12, 0, 0)
ANON = "anon-visitor-0001"
SID = "session-visit-abcdef12"
ASKS = {f: phrases.say("ask_" + f) for f in ("tx", "locality", "bhk", "budget")}
IVARA = {"_id": "P52100000001", "regno": "P52100000001", "name": "GODREJ IVARA", "promoter": "Godrej Properties Limited", "locality": "kharadi",
         "page_slug": "godrej-ivara-kharadi", "completion_now": "2029-10-30", "units_total": 400, "units_booked": 100}
CAMELOT = {"_id": "P52100000002", "regno": "P52100000002", "name": "LODHA CAMELOT", "promoter": "Lodha Developers Limited", "locality": "kharadi",
           "page_slug": "lodha-camelot", "completion_now": "2030-06-30", "units_total": 600, "units_booked": 200}


class PromptLLM:
    """Answers the two agent.py calls in turn and keeps what each was told."""
    def __init__(self, understand, reply):
        self.understand, self.reply, self.calls = understand, reply, []

    async def json(self, system, user):
        self.calls.append((system, user))
        return self.understand if len(self.calls) % 2 == 1 else self.reply


async def service(llm=None, agent=False):
    db = FakeDb()
    db.get_collection("agent_public_profiles").docs += [{"slug": "avasetu", "is_public": True, "agent_id": "HOUSE"}]
    for p in (IVARA, CAMELOT):
        await Store(db).projects.insert_one(dict(p))
    return ChatService(db, TrackingService(db, now=lambda: NOW), llm, now=lambda: NOW, agent=agent), db


def read(db, *pages, anon=ANON, agent_id="HOUSE"):
    """Page views: (path, minutes before NOW)."""
    events = db.get_collection("events")
    for path, ago in pages:
        events.docs.append({"_id": f"ev{len(events.docs)}", "agent_id": agent_id, "anon_id": anon, "type": "page_view", "path": path,
                            "ts": NOW - timedelta(minutes=ago)})


async def talk(s, msgs, context=None, path="/", anon=ANON, sid=SID):
    return [await s.message(sid, "avasetu", m, context=context, visit={"anon_id": anon, "path": path}) for m in msgs]


async def session(s):
    return await s.sessions.find_one({"_id": SID})


# ---- the greeting and the first question ------------------------------------------------------------------------------------
async def test_a_visitor_who_read_two_projects_is_offered_both_price_sheets_on_the_home_page():
    s, db = await service()
    read(db, ("/projects/godrej-ivara-kharadi", 20), ("/projects/lodha-camelot?src=ig", 10), ("/", 1))
    r = (await talk(s, ["hi"], context={"page": "home"}))[0]
    assert r["reply"] == ("You were looking at Lodha Camelot and Godrej Ivara. Want their price sheets and floor plans, "
                          "or help comparing them?")
    assert r["quick_replies"] == ["Lodha Camelot price sheet", "Godrej Ivara price sheet", "Compare them"]


async def test_a_visitor_who_read_one_project_is_offered_its_price_sheet_on_the_enquire_page():
    s, db = await service()
    read(db, ("/projects/godrej-ivara-kharadi", 5), ("/enquire", 1))
    r = (await talk(s, ["hello"], context={"page": "other"}, path="/enquire"))[0]
    assert r["reply"] == "You were looking at Godrej Ivara. Want its price sheet and floor plans?"
    assert r["quick_replies"] == ["Godrej Ivara price sheet"]


async def test_on_a_project_page_the_other_projects_read_are_named_with_a_price_sheet_reply_each():
    s, db = await service()
    read(db, ("/projects/lodha-camelot", 8), ("/projects/godrej-ivara-kharadi", 1))
    r = (await talk(s, ["hi"], context={"page": "project", "project": "godrej-ivara-kharadi"}, path="/projects/godrej-ivara-kharadi"))[0]
    assert r["reply"] == ("Asking about Godrej Ivara? I can get you its price sheet and floor plans, or set up a site visit. "
                          "You also looked at Lodha Camelot. Want its price sheet too?")
    assert r["quick_replies"] == ["Price sheet & floor plans", "Site visit", "Lodha Camelot price sheet"]


async def test_a_project_page_read_alone_keeps_its_own_greeting():
    s, db = await service()
    read(db, ("/projects/godrej-ivara-kharadi", 1))
    r = (await talk(s, ["hi"], context={"page": "project", "project": "godrej-ivara-kharadi"}, path="/projects/godrej-ivara-kharadi"))[0]
    assert r["reply"].endswith("Which size (BHK) are you looking for?")


async def test_tapping_a_read_projects_price_sheet_hands_off_and_tells_the_team_which():
    s, db = await service(agent=True)
    read(db, ("/projects/godrej-ivara-kharadi", 20), ("/projects/lodha-camelot", 10))
    r = (await talk(s, ["hi", "Lodha Camelot price sheet"], context={"page": "home"}))[-1]
    assert r["reply"].startswith(phrases.say("handoff_web_sheet", team="Avasetu"))
    assert phrases.say("consent") in r["reply"]
    data = (await session(s))["data"]
    assert data["sheets_for"] == ["Lodha Camelot"]
    assert "Wants price sheets for Lodha Camelot." in engine.summary(data)


async def test_compare_them_hands_off_both_price_sheets_to_compare():
    s, db = await service(agent=True)
    read(db, ("/projects/godrej-ivara-kharadi", 20), ("/projects/lodha-camelot", 10))
    r = (await talk(s, ["hi", "Compare them"], context={"page": "home"}))[-1]
    assert r["reply"].startswith(phrases.say("handoff_web_compare", team="Avasetu"))
    data = (await session(s))["data"]
    assert "Wants price sheets for Lodha Camelot and Godrej Ivara, to compare them." in engine.summary(data)


async def test_areas_read_earlier_are_not_asked_again():
    s, db = await service()
    read(db, ("/projects/area/wagholi/2-bhk", 15), ("/news", 2))
    tr = await talk(s, ["hi", "I want to buy"], context={"page": "news"}, path="/news")
    assert tr[0]["reply"] == f"Still looking at 2 BHK homes in Wagholi? {ASKS['budget']}"
    assert all(ASKS["locality"] not in r["reply"] and ASKS["bhk"] not in r["reply"] for r in tr), tr
    data = (await session(s))["data"]
    assert (data["locality"], data["locality_src"], data["bhk"], data["bhk_src"]) == ("Wagholi", "history", 2, "history")


async def test_an_area_or_size_the_buyer_states_replaces_the_one_read_earlier():
    s, db = await service()
    read(db, ("/projects/area/wagholi/2-bhk", 15))
    await talk(s, ["hi", "Actually 3 BHK in Kharadi"], context={"page": "home"})
    data = (await session(s))["data"]
    assert (data["locality"], data["bhk"]) == ("Kharadi", 3)


async def test_the_page_they_are_on_wins_over_an_area_read_earlier():
    s, db = await service()
    read(db, ("/projects/area/wagholi", 15), ("/projects/area/kharadi/top", 1))
    r = (await talk(s, ["hi"], context={"page": "list", "locality": "kharadi", "list": "top"}, path="/projects/area/kharadi/top"))[0]
    assert r["reply"].startswith("Looking at the top projects in Kharadi?")
    assert (await session(s))["data"]["locality"] == "Kharadi"


# ---- whose pages, which visit ------------------------------------------------------------------------------------------------
async def test_pages_from_another_visitor_or_an_old_visit_are_never_used():
    s, db = await service()
    read(db, ("/projects/godrej-ivara-kharadi", 5), ("/projects/lodha-camelot", 4), anon="anon-someone-else")   # another browser
    read(db, ("/projects/lodha-camelot", 3), agent_id="OTHER-SITE")                                             # another site
    read(db, ("/projects/godrej-ivara-kharadi", 300))                                                          # hours ago
    read(db, ("/projects/lodha-camelot", 95), ("/projects/area/wagholi/2-bhk", 90))                           # a visit that ended
    r = (await talk(s, ["hi"], context={"page": "home"}))[0]
    assert r["reply"] == phrases.say("greet")
    assert (await session(s))["data"]["history"] == []


async def test_without_a_browser_id_nothing_is_read():
    s, db = await service()
    read(db, ("/projects/lodha-camelot", 3), anon="chat-" + SID)
    r = (await talk(s, ["hi"], context={"page": "home"}, anon=None))[0]
    assert r["reply"] == phrases.say("greet")


async def test_a_visit_is_the_views_since_the_last_half_hour_gap():
    db = FakeDb()
    read(db, ("/projects/a-old", 80), ("/projects/b-new", 40), ("/projects/c-new", 20), ("/projects/b-new", 10), ("/", 2))
    assert await visits.pages_this_visit(db, "HOUSE", ANON, NOW) == ["/projects/c-new", "/projects/b-new", "/"]
    read(db, *((f"/projects/p-{i}", 1) for i in range(15)))
    assert len(await visits.pages_this_visit(db, "HOUSE", ANON, NOW)) == visits.MAX_PAGES


async def test_agent_pages_ignore_buyer_history():
    s, db = await service()
    read(db, ("/projects/godrej-ivara-kharadi", 20), ("/projects/lodha-camelot", 10), ("/agents", 1))
    r = (await talk(s, ["hi"], context={"page": "agents"}, path="/agents"))[0]
    assert r["reply"] == phrases.say("greet_agent")
    assert (await session(s))["data"]["history"] == []


async def test_unknown_slugs_studio_and_agents_pages_are_left_out_of_what_they_read():
    s, db = await service()
    read(db, ("/projects/no-such-project", 9), ("/studio/leads", 8), ("/agents", 7), ("/agent/rahul", 6), ("/projects/area/atlantis", 5),
         ("/builders/nobody-builders", 4), ("/", 1))
    r = (await talk(s, ["hi"], context={"page": "home"}))[0]
    assert r["reply"] == phrases.say("greet")
    assert (await session(s))["data"]["history"] == []


def test_paths_are_read_like_the_widget_reads_them():
    assert visit.read_path("/projects/area/kharadi/top/2-bhk") == {"kind": "list", "slug": "kharadi", "list": "top", "bhk": 2}
    assert visit.read_path("/check/godrej-ivara-kharadi") == {"kind": "project", "slug": "godrej-ivara-kharadi"}
    assert visit.read_path("/3-bhk/wagholi?src=fb") == {"kind": "list", "slug": "wagholi", "list": "all", "bhk": 3}
    assert visit.read_path("/guides/upper-kharadi") == {"kind": "area", "slug": "upper-kharadi"}
    for p in ("/", "/agents", "/agent/rahul/listings/L1", "/studio", "/projects/upcoming", "/news/x"):
        assert visit.read_path(p) is None, p


# ---- the model and the lead ------------------------------------------------------------------------------------------------
async def test_the_model_is_told_what_they_read_earlier_in_this_visit():
    llm = PromptLLM({"intent": "question"}, {"reply": "Both are in Kharadi.", "question": "", "needs_team": False})
    s, db = await service(llm=llm, agent=True)
    read(db, ("/projects/godrej-ivara-kharadi", 20), ("/projects/area/kharadi/top", 10), ("/", 1))
    await talk(s, ["which of these is closer to the IT park?"], context={"page": "home"})
    assert "EARLIER IN THIS VISIT THEY READ: Godrej Ivara (Kharadi), Kharadi top list" in llm.calls[0][1]
    assert "EARLIER IN THIS VISIT THEY READ: Godrej Ivara (Kharadi), Kharadi top list" in llm.calls[1][1]


async def test_the_model_is_told_nothing_else_when_they_read_nothing_else():
    llm = PromptLLM({"intent": "question"}, {"reply": "Kharadi is in east Pune.", "question": "", "needs_team": False})
    s, db = await service(llm=llm, agent=True)
    await talk(s, ["where is kharadi?"], context={"page": "home"})
    assert "EARLIER IN THIS VISIT THEY READ: nothing else" in llm.calls[0][1]


async def test_the_lead_keeps_the_pages_read():
    s, db = await service()
    read(db, ("/projects/godrej-ivara-kharadi", 20), ("/projects/lodha-camelot", 10), ("/projects/area/kharadi/top", 5), ("/", 1))
    tr = await talk(s, ["hi", "call me on 9822012345", "yes"], context={"page": "home"})
    assert tr[-1]["lead_created"]
    lead = db.get_collection("contacts").docs[0]
    assert lead["pages_read"] == [{"label": "Godrej Ivara", "path": "/projects/godrej-ivara-kharadi"},
                                  {"label": "Lodha Camelot", "path": "/projects/lodha-camelot"},
                                  {"label": "Kharadi top list", "path": "/projects/area/kharadi/top"}]
    detail = await TrackingService(db, now=lambda: NOW).lead_detail("HOUSE", lead["_id"])
    assert [p["label"] for p in detail["pages_read"]] == ["Godrej Ivara", "Lodha Camelot", "Kharadi top list"]
    note = next(n for n in db.get_collection("notifications").docs if n["kind"] == "new_chat_lead")
    assert "Read: Godrej Ivara → Lodha Camelot → Kharadi top list." in note["summary"]


async def test_a_public_enquiry_form_cannot_set_the_pages_read():
    from app.modules.tracking.schemas import InquiryIn
    assert "pages_read" not in InquiryIn.model_fields


def test_every_visit_sentence_is_written_in_all_five_languages():
    for key in ("also_one", "also_two", "seen_one", "seen_two", "seen_area", "handoff_web_compare"):
        assert set(phrases.P[key]) == set(phrases.LANGS), key
    assert set(phrases.QUICK["compare"]) == set(phrases.LANGS)
    assert set(phrases.QUICK_FOR["sheet_for"]) == set(phrases.LANGS)
