"""The chat speaks first, offers the home plan, names an area's hot projects and speaks Marathi too (owner, 2026-11-06, docs/plan/chat-reach.md)."""
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.modules.chat import engine, phrases, plan
from app.modules.chat.projects import project_cards
from app.modules.chat.service import ChatService
from app.modules.newsroom.store import Store
from app.modules.tracking.service import TrackingService

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio
NOW = datetime(2026, 11, 6, 12, 0, 0)
ANON = "anon-visitor-0001"
SID = "session-reach-abcdef12"
PLAN = "/home-plan/result?work=kharadi&budget=under-75l&bhk=2&movein=by-2027&kids=school&elders=1"
FRONTEND = Path(__file__).resolve().parents[3] / "frontend" / "lib" / "site"


def priced(*rows):
    return {"at": NOW, "rows": [{"bhk": b, "from_inr": p, "sources": [{"site": "a.test", "quote": f"{b} from {p}"}]} for b, p in rows]}


def project(n, slug, name, **kw):
    return {"_id": f"P5210000000{n}", "regno": f"P5210000000{n}", "name": name, "promoter": "Builder Limited", "locality": "kharadi", "page_slug": slug,
            "completion_now": "2029-10-30", "units_total": 400, "units_booked": 100, **kw}


IVARA = project(1, "godrej-ivara-kharadi", "GODREJ IVARA", hot_score=40)
CAMELOT = project(2, "lodha-camelot", "LODHA CAMELOT", hot_score=30)


class Scripted:
    """Answers the two agent.py calls in turn."""
    def __init__(self, intent="answer", reply="Here you go.", **read):
        self.u, self.r = {"intent": intent, **read}, {"reply": reply, "question": "", "needs_team": False}
        self.calls = []

    async def json(self, system, user):
        self.calls.append((system, user))
        return self.u if len(self.calls) % 2 == 1 else self.r


async def service(*projects, llm=None, agent=False):
    db = FakeDb()
    db.get_collection("agent_public_profiles").docs += [{"slug": "avasetu", "is_public": True, "agent_id": "HOUSE"}]
    for p in projects:
        await Store(db).projects.insert_one(dict(p))
    return ChatService(db, TrackingService(db, now=lambda: NOW), llm, now=lambda: NOW, agent=agent), db


def read(db, *pages, anon=ANON):
    events = db.get_collection("events")
    for path, ago in pages:
        events.docs.append({"_id": f"ev{len(events.docs)}", "agent_id": "HOUSE", "anon_id": anon, "type": "page_view", "path": path,
                            "ts": NOW - timedelta(minutes=ago)})


async def note(s, seconds, context=None, path="/"):
    return await s.nudge(SID, "avasetu", context or {"page": "home"}, {"anon_id": ANON, "path": path}, seconds)


async def say(s, text, context=None, path="/"):
    return await s.message(SID, "avasetu", text, context=context or {"page": "home"}, visit={"anon_id": ANON, "path": path})


async def session(s):
    return await s.sessions.find_one({"_id": SID})


# ---- the plan's answers ----------------------------------------------------------------------------------------------------
def test_the_chat_reads_a_plans_answers_from_its_address():
    p = plan.read(PLAN)
    assert (p["bhk"], p["budget"], p["work"], p["east"]) == (2, "under-75l", "kharadi", True)
    assert p["label"] == "Home plan: 2 BHK, Under ₹75 L, works in Kharadi"


def test_an_unfinished_plan_or_another_page_is_no_plan():
    assert plan.read("/home-plan/result?work=kharadi") is None
    assert plan.read("/home-plan?work=kharadi&budget=under-75l&bhk=2") is None
    assert plan.read("/home-plan/result?work=mars&budget=under-75l&bhk=2") is None


@pytest.mark.skipif(not FRONTEND.is_dir(), reason="frontend sources are not on this machine")
def test_the_chats_budgets_and_offices_are_the_sites():
    budgets = re.findall(r"key: '([^']+)', label: '([^']+)', min: ([\d_]+), max: ([\d_]+|Infinity)", (FRONTEND / "finder.ts").read_text(encoding="utf-8"))
    want = [(k, label, int(lo.replace("_", "")), None if hi == "Infinity" else int(hi.replace("_", ""))) for k, label, lo, hi in budgets]
    assert want == list(plan.BUDGETS)
    work = (FRONTEND / "homeplan.ts").read_text(encoding="utf-8")
    block = work[work.index("export const WORK"):work.index("] as const")]
    assert set(re.findall(r"key: '([^']+)'", block)) == set(plan.WORK)


async def test_a_buyer_who_made_a_plan_is_not_asked_size_or_budget_again_and_is_offered_its_prices():
    s, db = await service(IVARA)
    read(db, (PLAN, 3), ("/", 1))
    r = await say(s, "hi")
    assert r["reply"] == "Your home plan: 2 BHK, Under ₹75 L. Want today's prices for these picks from our team?"
    assert r["quick_replies"] == ["Today's prices for my plan"]
    d = (await session(s))["data"]
    assert (d["bhk"], d["budget_max"], d["locality"], d["budget_min"]) == (2, 7_500_000, "Kharadi", None)


async def test_tapping_the_plans_prices_asks_the_number_and_tells_the_team_what_for():
    s, db = await service(IVARA, llm=Scripted(), agent=True)
    read(db, (PLAN, 3))
    r = await say(s, "Today's prices for my plan")
    assert "today's prices for your plan" in r["reply"]
    d = (await session(s))["data"]
    assert d["asked"] == "phone" and "Wants today's prices for their home plan." in engine.summary(d)


async def test_a_plan_outlives_the_visit_it_was_made_in():
    s, db = await service(IVARA)
    read(db, (PLAN, 3))
    await say(s, "hi")
    db.get_collection("events").docs.clear()
    await say(s, "hello there")
    d = (await session(s))["data"]
    assert d["plan"]["bhk"] == 2 and any(i["kind"] == "plan" for i in d["history"])


async def test_what_they_say_replaces_what_the_plan_said():
    s, db = await service(IVARA)
    read(db, (PLAN, 3))
    await say(s, "hi")
    await say(s, "3 BHK")
    assert (await session(s))["data"]["bhk"] == 3


# ---- the note beside the chat button --------------------------------------------------------------------------------------
async def test_a_finished_plan_gets_a_word_soon_after():
    s, db = await service(IVARA)
    read(db, (PLAN, 1))
    assert await note(s, 10) is None
    n = await note(s, 30)
    assert n["key"] == "plan" and n["quick"] == ["Today's prices for my plan"] and n["link"] is None


async def test_someone_comparing_two_projects_is_offered_both_sheets_and_the_home_plan():
    s, db = await service(IVARA, CAMELOT)
    read(db, ("/projects/godrej-ivara-kharadi", 6), ("/projects/lodha-camelot", 1))
    assert await note(s, 60) is None
    n = await note(s, 90)
    assert n["text"] == "Comparing Lodha Camelot and Godrej Ivara? I can get you both price sheets, side by side."
    assert n["quick"] == ["Compare them"] and n["link"]["url"] == "/home-plan"


async def test_the_project_page_they_are_on_counts_as_one_of_the_two():
    s, db = await service(IVARA, CAMELOT, llm=Scripted(), agent=True)
    here = {"page": "project", "project": "lodha-camelot"}
    read(db, ("/projects/godrej-ivara-kharadi", 6), ("/projects/lodha-camelot", 1))
    n = await note(s, 90, here, "/projects/lodha-camelot")
    assert n["key"] == "compare"
    r = await say(s, "Compare them", here, "/projects/lodha-camelot")
    assert "both price sheets" in r["reply"]
    assert (await session(s))["data"]["sheets_for"] == ["Lodha Camelot", "Godrej Ivara"]


async def test_someone_reading_an_area_is_offered_its_hot_projects():
    s, db = await service(IVARA)
    ctx = {"page": "area", "locality": "kharadi"}
    read(db, ("/localities/kharadi", 3))
    n = await note(s, 120, ctx, "/localities/kharadi")
    assert n["key"] == "hot" and n["quick"] == ["Hot projects in Kharadi"]


async def test_tapping_the_hot_note_shows_them_with_no_greeting_first():
    s, db = await service(IVARA, llm=Scripted(intent="homes"), agent=True)
    ctx = {"page": "area", "locality": "kharadi"}
    read(db, ("/localities/kharadi", 3))
    await note(s, 120, ctx, "/localities/kharadi")
    r = await say(s, "Hot projects in Kharadi", ctx, "/localities/kharadi")
    assert [c["title"] for c in r["cards"]] == ["Godrej Ivara"]


async def test_any_long_stay_in_east_pune_gets_the_home_plan():
    s, db = await service()
    read(db, ("/", 4))
    assert await note(s, 120) is None
    n = await note(s, 180)
    assert n["key"] == "try_plan" and n["link"]["label"] == "Try the home plan" and n["quick"] == []


async def test_one_note_a_day_however_many_times_the_widget_asks():
    s, db = await service()
    assert await note(s, 180)
    assert await note(s, 180) is None


async def test_no_note_on_an_agents_site_or_the_agents_pages_or_to_a_buyer_who_gave_a_number():
    s, _ = await service()
    assert await note(s, 180, {"page": "home", "site": "agent"}, "/agent/rahul") is None
    assert await note(s, 180, {"page": "agents"}, "/agents") is None
    await s.sessions.insert_one({"_id": SID, "agent_slug": "avasetu", "data": {**engine.new_data(localise=True), "lead_done": True, "phone": "+919000000000"},
                                 "messages": [], "hits": [], "created_at": NOW})
    assert await note(s, 180) is None


async def test_a_note_nobody_answered_is_not_a_chat_and_one_they_answered_starts_it():
    s, _ = await service()
    n = await note(s, 180)
    assert (await session(s))["messages"] == [] and await s.conversations("HOUSE") == []
    await say(s, "hi")
    got = await session(s)
    assert got["messages"][0] == {"role": "bot", "text": n["text"], "ts": NOW} and got["data"]["nudge_key"] == "try_plan"
    assert "nudge" not in got["data"]


# ---- the home plan in the chat --------------------------------------------------------------------------------------------
async def test_a_buyer_shown_projects_is_offered_the_plan_once_with_what_we_know_ticked():
    llm = Scripted(locality="Kharadi", bhk=2, budget_max_inr=9_000_000)
    s, _ = await service(IVARA, llm=llm, agent=True)
    r = await say(s, "2 bhk in Kharadi under 90 lakh")
    assert r["cards"] and phrases.say("try_plan") in r["reply"]
    assert r["link"] == {"label": "Try the home plan", "url": "/home-plan?bhk=2&budget=75l-1cr"}
    assert (await say(s, "any others?"))["link"] is None


async def test_nobody_with_a_plan_or_on_another_side_of_pune_is_offered_it():
    assert not plan.can_offer({"plan": {"bhk": 2}, "audience": "buyer", "page": {"site": "house"}}, "web")
    assert not plan.can_offer({"locality": "Hinjawadi", "audience": "buyer", "page": {"site": "house"}}, "web")
    assert not plan.can_offer({"locality": "Kharadi", "audience": "buyer", "page": {"site": "agent"}}, "web")
    assert plan.can_offer({"locality": "Wagholi"}, "message")


# ---- hot projects -----------------------------------------------------------------------------------------------------------
async def test_naming_an_area_shows_its_hot_projects_before_any_size_or_budget():
    llm = Scripted(locality="Kharadi")
    s, _ = await service(CAMELOT, IVARA, llm=llm, agent=True)
    r = await say(s, "Kharadi")
    assert [c["title"] for c in r["cards"]] == ["Godrej Ivara", "Lodha Camelot"]
    assert all(c["hot"] for c in r["cards"])
    assert "HOT" in llm.calls[1][1]


async def test_asking_for_good_projects_shows_them():
    llm = Scripted(intent="question")
    s, _ = await service(IVARA, llm=llm, agent=True)
    r = await say(s, "any good projects in this area?", {"page": "area", "locality": "kharadi"}, "/localities/kharadi")
    assert r["cards"]


async def test_a_project_page_keeps_to_its_project_until_they_ask():
    llm = Scripted(intent="question")
    s, _ = await service(IVARA, CAMELOT, llm=llm, agent=True)
    here = {"page": "project", "project": "lodha-camelot"}
    assert not (await say(s, "what is the possession date?", here, "/projects/lodha-camelot"))["cards"]
    r = await say(s, "any other popular projects?", here, "/projects/lodha-camelot")
    assert [c["title"] for c in r["cards"]] == ["Godrej Ivara"]


async def test_no_mhada_project_goes_on_a_card_however_hot():
    s, db = await service(project(3, "vanaya-n", "VENKATESH VANAYA - WING N (MHADA)- PHASE 8", hot_score=57), IVARA)
    assert [c["title"] for c in await project_cards(db, {"localities": ["Kharadi"]}, NOW)] == ["Godrej Ivara"]


async def test_a_sold_out_or_nearly_sold_project_is_not_suggested():
    s, db = await service(project(3, "gone", "ALL BOOKED", hot_score=90, units_booked=400), project(4, "few", "NINE LEFT", hot_score=80, units_booked=391), IVARA)
    assert [c["title"] for c in await project_cards(db, {"localities": ["Kharadi"]}, NOW)] == ["Godrej Ivara"]


async def test_a_published_price_fits_first_and_one_over_budget_or_another_size_is_left_out():
    fits = project(3, "fits", "FITS", hot_score=26, prices=priced(("2 BHK", 7_000_000), ("3 BHK", 11_000_000)))
    dear = project(4, "dear", "TOO DEAR", hot_score=60, prices=priced(("2 BHK", 12_000_000)))
    threes = project(5, "threes", "ONLY THREES", hot_score=60, prices=priced(("3 BHK", 7_000_000)))
    s, db = await service(fits, dear, threes, IVARA)
    cards = await project_cards(db, {"localities": ["Kharadi"], "bhk": 2.0, "budget_max_inr": 7_500_000}, NOW)
    assert [c["title"] for c in cards] == ["Fits", "Godrej Ivara"]
    assert cards[0]["price_text"].startswith("from ₹") and cards[0]["priced"] and cards[0]["price_note"]
    assert cards[1]["price_text"] is None


async def test_the_owners_banner_picks_lead_for_a_buyer_who_has_said_nothing():
    pick = project(3, "pick", "PICK", hot_score=1)
    s, db = await service(pick, IVARA)
    await db.get_collection("site_settings").insert_one({"_id": "spotlight", "auto": True, "items": [{"slug": "pick", "area": None, "note": "New tower", "until": None}]})
    cards = await project_cards(db, {"localities": ["Kharadi"]}, NOW)
    assert cards[0]["title"] == "Pick" and cards[0]["fact"] == "New tower" and cards[0]["hot"]
    assert (await project_cards(db, {"localities": ["Kharadi"], "bhk": 2.0}, NOW))[0]["title"] == "Godrej Ivara"


# ---- language ---------------------------------------------------------------------------------------------------------------
def test_a_buyer_can_choose_hindi_or_marathi_in_either_script():
    assert phrases.asked_language("मराठी") == "mr" and phrases.asked_language("मराठीत बोला") == "mr"
    assert phrases.asked_language("हिंदी") == "hi" and phrases.asked_language("Hindi mein") == "hinglish"
    assert phrases.asked_language("marathi madhe bola") == "mr_latn" and phrases.asked_language("English") == "en"
    assert phrases.asked_language("hi") is None and phrases.asked_language("is marathi spoken in wagholi?") is None


async def test_choosing_marathi_after_the_greeting_greets_again_in_marathi_and_keeps_it():
    s, _ = await service(llm=Scripted(), agent=True)
    await say(s, "hi")
    r = await say(s, "मराठी")
    assert r["reply"] == phrases.say("greet", "mr")
    assert (await session(s))["data"]["lang"] == "mr"


async def test_choosing_a_language_in_the_middle_of_a_chat_just_says_so():
    s, _ = await service(llm=Scripted(intent="question"), agent=True)
    await say(s, "hi")
    await say(s, "tell me about stamp duty please")
    await say(s, "and registration charges here")
    assert (await say(s, "हिंदी"))["reply"] == phrases.say("lang_ok", "hi")
