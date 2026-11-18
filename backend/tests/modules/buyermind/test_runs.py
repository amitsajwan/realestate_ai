"""When the buyer mind thinks: in the background on new leads and buyer replies (inbox.followups step 5, BUYER_MIND on), and
by hand from Studio's lead page (works with BUYER_MIND off, once per 2 minutes a lead). Nothing here sends a message."""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user, get_user_manager
from app.modules.buyermind import config
from app.modules.buyermind import router as mind_routes
from app.modules.buyermind.service import BuyerMind, TooSoon
from app.modules.inbox import followups
from app.modules.inbox.service import InboxError

from ..fakes import FakeDb
from .test_buyermind import AGENT, LEAD, NOW, card

ON = config.Settings(enabled=True, effort="low", max_rounds=2)
OFF = config.Settings(enabled=False, effort="low", max_rounds=2)
ANSWER = {"buyer": "2 BHK buyer", "draft": "Namaste Rahul ji, our team is getting the floor plans for you. Avasetu team",
          "temperature": "hot", "when": "today", "confidence": "medium"}


class Model:
    def __init__(self):
        self.calls = 0

    async def step(self, messages, tools=None, json_mode=False, effort=None, timeout=None):
        self.calls += 1
        return {"content": json.dumps(ANSWER)}


class Clock:
    def __init__(self, t=NOW):
        self.t = t

    def __call__(self):
        return self.t


def mind(db, model, settings, clock=None):
    async def read_lead(agent_id, lead_id):
        if (agent_id, lead_id) != (AGENT, LEAD):
            raise InboxError("Lead not found", 404)
        return {"card": card(), "project": None}

    async def nothing(_):
        return None
    return BuyerMind(db, model, read_lead, nothing, nothing, settings=settings, now=clock or Clock())


async def test_in_the_background_it_thinks_only_when_something_happened_since_its_last_brief():
    db, model, clock = FakeDb(), Model(), Clock()
    m = mind(db, model, ON, clock)
    assert await m.think_if_due(AGENT, LEAD, NOW - timedelta(minutes=5)) == "thought"
    clock.t = NOW + timedelta(minutes=10)
    assert await m.think_if_due(AGENT, LEAD, NOW - timedelta(minutes=5)) == "fresh"        # nothing new since
    assert await m.think_if_due(AGENT, LEAD, NOW + timedelta(minutes=8)) == "thought"      # the buyer wrote again
    assert model.calls == 2
    assert await mind(db, model, OFF).think_if_due(AGENT, LEAD, NOW + timedelta(hours=1)) == "off" and model.calls == 2


async def test_by_hand_it_works_with_the_switch_off_but_not_twice_in_two_minutes():
    db, clock = FakeDb(), Clock()
    m = mind(db, Model(), OFF, clock)
    view = await m.think_by_hand(AGENT, LEAD)
    assert view["brief"]["draft"].startswith("Namaste Rahul ji") and view["at"] == NOW.isoformat() + "Z"
    assert view["profile"]["said"]["Home"] == "2 BHK" and view["outcome"] == "done"
    clock.t = NOW + timedelta(seconds=30)
    try:
        await m.think_by_hand(AGENT, LEAD)
        raise AssertionError("expected TooSoon")
    except TooSoon as e:
        assert e.wait_s == 91
    clock.t = NOW + timedelta(minutes=3)
    assert (await m.think_by_hand(AGENT, LEAD))["at"] == clock.t.isoformat() + "Z"


async def test_another_agents_lead_shows_nothing():
    db = FakeDb()
    await mind(db, Model(), OFF).think(AGENT, LEAD)
    assert await mind(db, Model(), OFF).view("SOMEONE-ELSE", LEAD) == {"brief": None, "at": None, "outcome": None, "lookups": [],
                                                                       "profile": None}


# ---- inbox.followups step 5 -------------------------------------------------------------------------------------------

def lead(_id, stage="new", ago=timedelta(minutes=10), **kw):
    return {"_id": _id, "agent_id": AGENT, "name": _id, "phone": None, "stage": stage, "created_at": NOW - ago, **kw}


async def test_the_loop_thinks_about_new_leads_and_replies_newest_first_and_skips_the_rest():
    db = FakeDb()
    contacts = db.get_collection("contacts")
    for c in (lead("new-old", ago=timedelta(hours=5)), lead("new-fresh"), lead("called", stage="contacted"),
              lead("won", stage="won"), lead("too-old", ago=timedelta(days=20))):
        await contacts.insert_one(c)
    asked = []

    async def think(db_, agent_id, lead_id, since):
        asked.append((lead_id, since))
        return "thought"
    assert await followups.fresh_briefs(db, NOW, think) == 2
    assert asked == [("new-fresh", NOW - timedelta(minutes=10)), ("new-old", NOW - timedelta(hours=5))]


async def test_the_loop_stops_at_its_cap_on_an_off_switch_and_goes_on_after_a_failure(monkeypatch):
    db = FakeDb()
    for i in range(9):
        await db.get_collection("contacts").insert_one(lead(f"l{i}", ago=timedelta(minutes=10 + i)))
    seen = []

    async def flaky(db_, agent_id, lead_id, since):
        seen.append(lead_id)
        if lead_id == "l0":
            raise RuntimeError("model down")
        return "thought"
    assert await followups.fresh_briefs(db, NOW, flaky) == followups.BRIEFS_PER_CYCLE
    assert seen[0] == "l0" and len(seen) == followups.BRIEFS_PER_CYCLE + 1

    async def off(*_):
        seen.append("off")
        return "off"
    seen.clear()
    assert await followups.fresh_briefs(db, NOW, off) == 0 and seen == ["off"]

    t = {"now": NOW}

    async def slow(db_, agent_id, lead_id, since):
        t["now"] += timedelta(minutes=1, seconds=10)
        return "thought"
    assert await followups.fresh_briefs(db, NOW, slow, clock=lambda: t["now"]) == 2   # no new brief after 2 minutes


async def test_with_nothing_wired_the_loop_reads_nothing(monkeypatch):
    monkeypatch.setattr(followups, "_think", None)
    assert await followups.fresh_briefs(FakeDb(), NOW) == 0


def test_wiring_connects_the_loop_only_with_the_switch_on(monkeypatch):
    from app import wiring
    monkeypatch.setenv("BUYER_MIND", "true")
    wiring.wire()
    assert followups._think is wiring._brief_lead
    monkeypatch.delenv("BUYER_MIND")
    wiring.wire()
    assert followups._think is None


# ---- routes -----------------------------------------------------------------------------------------------------------

def client(m, user_id=AGENT):
    app = FastAPI()
    app.include_router(mind_routes.router, prefix="/buyer-mind")
    app.dependency_overrides[mind_routes.get_mind] = lambda: m
    if user_id:
        app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id=user_id)
    else:
        app.dependency_overrides[get_user_manager] = lambda: SimpleNamespace()   # no token: never asked about a user
    return TestClient(app)


def test_routes_show_and_think_for_the_agents_own_lead_only():
    m = mind(FakeDb(), Model(), OFF)
    c = client(m)
    assert c.get(f"/buyer-mind/leads/{LEAD}").json()["brief"] is None
    r = c.post(f"/buyer-mind/leads/{LEAD}/think")
    assert r.status_code == 200 and r.json()["brief"]["temperature"] == "hot"
    assert c.post(f"/buyer-mind/leads/{LEAD}/think").status_code == 429
    assert c.get(f"/buyer-mind/leads/{LEAD}").json()["brief"]["draft"]
    assert client(m, "SOMEONE-ELSE").post(f"/buyer-mind/leads/{LEAD}/think").status_code == 404


def test_routes_need_a_signed_in_agent():
    assert client(mind(FakeDb(), Model(), OFF), user_id=None).get(f"/buyer-mind/leads/{LEAD}").status_code == 401
