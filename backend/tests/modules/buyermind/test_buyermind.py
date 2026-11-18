"""The buyer mind's Lead Brief and buyer profile (docs/plan/buyer-mind.md steps 2-3). The case is Rahul's from 22 Oct: floor
plans of Fiore Phase 2A asked for at 22:15, 2 BHK, Rs 50-80 L, moving in 3-6 months, home loan; the project is due in 2027."""
import json
from datetime import datetime, timedelta

from app.modules.buyermind import brief as briefs
from app.modules.buyermind import config, profile, tools
from app.modules.buyermind.service import BuyerMind
from app.modules.inbox import handover

from ..fakes import FakeDb

NOW = datetime(2026, 10, 22, 17, 0)
AGENT, LEAD, SLUG = "OWNER", "rahul", "puraniks-abitante-fiore-2a-ravet"
SETTINGS = config.Settings(enabled=True, effort="medium", max_rounds=4)

RAHUL = {"_id": LEAD, "agent_id": AGENT, "name": "Rahul Thombare", "phone": "+919822000001", "channel": "form",
         "message": "Floor plans: Puraniks Abitante Fiore Phase 2A", "source": "google",
         "first_touch": {"landing": f"/projects/{SLUG}", "enquiry_page": f"/projects/{SLUG}"},
         "created_at": NOW - timedelta(minutes=5), "notes": [],
         "requirement": {"bhk": 2.0, "budget_min_inr": 5000000, "budget_max_inr": 8000000, "timeline": "3_6_months",
                         "financing": "home_loan", "localities": []}}

PAGE = {"marketed_name": "Puraniks Abitante Fiore Phase 2A", "slug": SLUG, "area": {"name": "Ravet"}, "promoter": "Puraniks Builders Ltd",
        "stage": "Under construction", "homes": True, "regno": "P52100012345", "units_total": 120, "units_booked": 80,
        "completion_now": "2027-12-31", "project": None,
        "prices": {"read_at": "2026-10-20", "rows": [{"bhk": "2 BHK", "from_inr": 6800000, "to_inr": 7400000, "official": True,
                                                       "sources": [{"site": "puraniks.com"}]}]},
        "same_area": [{"name": "Kohinoor Ravet Ready", "slug": "kohinoor-ravet-ready", "price_from": 6200000, "stage": "Completed"}],
        "home_sizes": [{"bhk": "2 BHK", "low": 690, "high": 740, "kind": "carpet"}], "faq": [{"q": "x"}]}


def card():
    return handover.card(RAHUL, {"slug": SLUG, "name": "Puraniks Abitante Fiore Phase 2A", "area": "Ravet", "regno": "P52100012345"})


def call(id_, name, **args):
    return {"id": id_, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


class Model:
    def __init__(self, *script):
        self.script, self.sent = list(script), []

    async def step(self, messages, tools=None, json_mode=False, effort=None, timeout=None):
        self.sent.append(messages)
        return self.script.pop(0) if self.script else None


def mind(model, db=None, page=PAGE):
    async def read_lead(agent_id, lead_id):
        assert (agent_id, lead_id) == (AGENT, LEAD)
        return {"card": card(), "project": {"slug": SLUG}}

    async def project(slug):
        return page if slug == SLUG else None

    async def area_search(q):
        return []
    return BuyerMind(db or FakeDb(), model, read_lead, project, area_search, settings=SETTINGS, now=lambda: NOW)


GOOD = {"buyer": "2 BHK buyer, Rs 50-80 L, home loan, researching late at night",
        "implied": ["Serious: asked for plans, not a brochure"], "unknown": ["which floor"],
        "asked_for": "floor plans", "can_answer": "no",
        "flags": ["Possession is due 2027-12-31, after the 3-6 months he wants"],
        "alternatives": [{"slug": "kohinoor-ravet-ready", "name": "Kohinoor Ravet Ready", "why": "completed, ₹62 Lakh"},
                         {"slug": "made-up-towers", "name": "Made Up", "why": "x"}],
        "price_idea": "2 BHK from ₹68 Lakh to ₹74 Lakh on puraniks.com, read 2026-10-20, indicative",
        "next_step": "Call tomorrow morning", "when": "tomorrow", "temperature": "hot",
        "draft": "Namaste Rahul ji, thank you for asking about Fiore Phase 2A. Our team is getting its floor plans for you. "
                 "2 BHK homes there are listed from ₹68 Lakh on the builder's site. Possession is due in December 2027; "
                 "if you need to move sooner, we can show you completed homes in Ravet too. Avasetu team",
        "why": "He wants plans and to move within 6 months; the project is due 2027.", "confidence": "medium"}


async def test_the_mind_looks_up_the_project_and_the_brief_keeps_what_the_facts_carry():
    db = FakeDb()
    model = Model({"content": "", "tool_calls": [call("c1", "project_facts", slug=SLUG)]}, {"content": json.dumps(GOOD)})
    doc = await mind(model, db).think(AGENT, LEAD)
    b = doc["brief"]
    assert doc["outcome"] == "done" and doc["lookups"] == [{"tool": "project_facts", "arguments": {"slug": SLUG}, "ok": True}]
    assert b["by"] == "mind" and b["draft"].startswith("Namaste Rahul ji") and b["temperature"] == "hot" and b["when"] == "tomorrow"
    assert b["flags"] == [GOOD["flags"][0]] and b["price_idea"] == GOOD["price_idea"]
    assert [a["slug"] for a in b["alternatives"]] == ["kohinoor-ravet-ready"]
    assert b["problems"] == ["alternative dropped, never looked up: made-up-towers"]
    stored = await db.get_collection("lead_briefs").find_one({"_id": LEAD})
    assert stored["brief"] == b and stored["agent_id"] == AGENT
    prof = await db.get_collection("buyer_profiles").find_one({"_id": LEAD})
    assert prof["implied"] == GOOD["implied"] and prof["temperature"] == "hot" and "which floor" in prof["unknown"]
    assert prof["said"]["Budget"] and "Phone" not in prof["said"]


async def test_the_buyers_phone_never_reaches_the_model():
    model = Model({"content": json.dumps(GOOD)})
    await mind(model).think(AGENT, LEAD)
    prompt = json.dumps(model.sent[0])
    assert "9822000001" not in prompt and "Rahul Thombare" in prompt and "3-6 months" in prompt


async def test_a_draft_with_a_price_no_lookup_gave_is_dropped_and_the_rest_kept():
    invented = {**GOOD, "draft": "Namaste Rahul ji, 2 BHK homes at Fiore start at ₹59 Lakh. Avasetu team",
                "price_idea": "around ₹59 Lakh", "flags": ["Booked 95 of 120"]}
    model = Model({"tool_calls": [call("c1", "project_facts", slug=SLUG)]}, {"content": json.dumps(invented)})
    b = (await mind(model).think(AGENT, LEAD))["brief"]
    assert b["draft"] is None and b["price_idea"] is None and b["flags"] == []
    assert any(p.startswith("draft dropped") and "59" in p for p in b["problems"])
    assert b["buyer"] == GOOD["buyer"] and b["next_step"] == GOOD["next_step"]


async def test_a_draft_that_sells_is_dropped():
    hype = {**GOOD, "draft": "Rahul ji, Fiore is the best choice, your dream home at ₹68 Lakh! Avasetu team"}
    model = Model({"tool_calls": [call("c1", "project_facts", slug=SLUG)]}, {"content": json.dumps(hype)})
    b = (await mind(model).think(AGENT, LEAD))["brief"]
    assert b["draft"] is None and "hype word" in b["problems"][-1]


async def test_with_no_model_the_brief_comes_from_the_card():
    doc = await mind(Model()).think(AGENT, LEAD)
    b = doc["brief"]
    assert doc["outcome"] == "failed" and b["by"] == "rules" and b["draft"] is None and b["when"] == "today"
    assert "2 BHK" in b["buyer"] and b["asked_for"]
    db = FakeDb()
    await mind(None, db).think(AGENT, LEAD)
    prof = await db.get_collection("buyer_profiles").find_one({"_id": LEAD})
    assert prof["implied"] == [] and prof["said"]["Home"]


def test_a_project_of_several_registrations_gives_the_whole_projects_figures():
    scoped = {**PAGE, "project": {"registrations": 3, "regnos": ["P1", "P2", "P3"], "units_total": 745, "units_booked": 400,
                                  "booked_of": 700, "completion_first": "2027-06-30", "completion_last": "2029-12-31",
                                  "completion_passed": False}}
    s = tools.project_summary(scoped)
    assert s["whole_project"]["units_total"] == 745 and s["whole_project"]["completion_last"] == "2029-12-31"
    assert "registration" not in s and "120" not in json.dumps(s)
    one = tools.project_summary(PAGE)
    assert one["registration"] == {"regno": "P52100012345", "units_total": 120, "units_booked": 80, "completion_now": "2027-12-31"}


def test_prices_are_given_as_the_buyer_reads_them_so_the_draft_can_be_checked():
    s = tools.project_summary(PAGE)
    assert s["prices"]["rows"][0] == {"bhk": "2 BHK", "from": "₹68 Lakh", "to": "₹74 Lakh", "builder_site": True, "sources": ["puraniks.com"]}
    assert s["same_area"][0]["price_from"] == "₹62 Lakh" and "faq" not in s


async def test_a_missing_project_is_told_to_the_model():
    project_facts = tools.tools(lambda s: _none(), lambda q: _empty())[0]
    assert "error" in await project_facts.run(slug="/projects/nowhere")


async def _none():
    return None


async def _empty():
    return []


def test_the_profile_keeps_said_apart_from_implied():
    p = profile.build(LEAD, AGENT, card(), {"implied": ["Family", "Family", ""], "unknown": ["floor"], "buyer": "b"}, NOW)
    assert p["implied"] == ["Family"] and p["unknown"][-1] == "floor" and p["said"]["Wants"]
    assert set(p["said"]) <= set(profile.SAID_LINES)


def test_settings_are_off_by_default_and_bounded(monkeypatch):
    monkeypatch.delenv("BUYER_MIND", raising=False)
    monkeypatch.setenv("BUYER_MIND_ROUNDS", "99")
    monkeypatch.setenv("BUYER_MIND_EFFORT", "max")
    s = config.load()
    assert not s.enabled and s.max_rounds == 10 and s.effort == "medium"
