"""about suggestion + extraction from the agent's words: golden cases, no invention, area guide only from the seed."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.ai_listing import router as r
from app.modules.ai_listing.about import extract_about, sanitise_llm_about, suggest_about
from app.modules.ai_listing.area_seed import AREA_SEED
from app.modules.ai_listing.service import AIListingService
from app.modules.listings.about import About

# (text, expected subset of the extracted about)
GOLDEN = [
    ("2 BHK Kharadi, 1 covered parking, lift, gym, 24x7 water, full power backup, maintenance 3000 per month, school nearby",
     dict(parking="1 covered parking", water="24x7 water supply", power_backup="Full power backup",
          maintenance="Maintenance ₹3,000 per month", amenities_has=["Lift", "Gym"], nearby_has=[("school", "School nearby")])),
    ("3BHK east facing corner flat, gated society, near Podar school, borewell water, 2 car parking",
     dict(highlights_has=["East facing", "Corner flat", "Gated society"], society="Gated society",
          water="Borewell water", parking="2 car parking", nearby_has=[("school", "Podar school")])),
    ("Flat hai Wagholi mein, parking milegi, paani 24 ghante, lift aur generator backup hai, school paas mein hai, maintenance 2500 mahina",
     dict(parking="Parking available", water="24x7 water supply", power_backup="Power backup available",
          maintenance="Maintenance ₹2,500 per month", amenities_has=["Parking", "Lift"], nearby_has=[("school", "School nearby")])),
    ("बाणेर में २ बीएचके, पार्किंग, लिफ्ट, जिम, गार्डन, स्विमिंग पूल",
     dict(amenities_has=["Parking", "Lift", "Gym", "Garden", "Swimming pool"])),
    ("2 BHK ready to move, vastu compliant, well maintained, quiet society, open terrace, lake view",
     dict(highlights_has=["Ready to move", "Vastu compliant", "Well maintained", "Open terrace", "Lake view"])),
    ("Maintenance Rs 4k per month, tanker water, backup for lift and common areas",
     dict(maintenance="Maintenance ₹4,000 per month", water="Tanker water",
          power_backup="Power backup for lifts and common areas")),
    ("Rohan Heights Upper Kharadi, hospital nearby, market nearby, co-operative housing society",
     dict(nearby_has=[("hospital", "Hospital nearby"), ("market", "Market nearby")], society="Co-operative housing society")),
]


@pytest.mark.parametrize("text,exp", GOLDEN)
def test_golden_extraction(text, exp):
    got = extract_about(text)
    for k, v in exp.items():
        if k.endswith("_has"):
            field = k[:-4]
            if field == "nearby":
                have = [(n["type"], n["name"]) for n in got.get("nearby", [])]
                assert all(x in have for x in v), (text, have)
            else:
                assert all(x in got.get(field, []) for x in v), (text, got)
        else:
            assert got.get(k) == v, (text, k, got)
    About.model_validate({k: v for k, v in got.items()})  # the extraction always fits the stored shape


@pytest.mark.parametrize("text", ["", "   ", "asdf qwerty", "2 BHK in Baner 85 lakh", "😀😀", "\x00\x01"])
def test_nothing_found_means_nothing_returned(text):
    got = extract_about(text)
    for k in ("highlights", "amenities", "nearby", "water", "power_backup", "maintenance", "parking", "society"):
        assert not got.get(k), (text, k)


def test_no_phone_number_leaks_into_about():
    got = extract_about("Near Podar school 9876543210 call me, 2 car parking")
    assert "9876543210" not in str(got)


def test_draft_gets_about_and_stays_valid():
    svc = AIListingService()
    import asyncio
    res = asyncio.run(svc.from_text("2 BHK for sale in Kharadi Pune, 85 lakh, 1100 sq ft carpet, 1 covered parking, lift, school nearby, 24x7 water"))
    about = res.draft["about"]
    assert about["parking"] == "1 covered parking" and about["water"] == "24x7 water supply"
    assert "Lift" in about["amenities"] and about["nearby"][0]["name"] == "School nearby"
    assert "about" not in res.missing
    About.model_validate(about)


def test_draft_without_about_words_has_no_about_key():
    import asyncio
    res = asyncio.run(AIListingService().from_text("2 BHK for sale in Baner Pune, 85 lakh, 1100 sq ft carpet"))
    assert "about" not in res.draft


# ---- LLM proposals must be traceable ----------------------------------------------------------------------------

class FakeLlm:
    def __init__(self, about):
        self.about, self.calls = about, 0

    async def extract(self, text, city_hint=None):
        return None

    async def translate(self, facts, en):
        return None

    async def json(self, system, user):
        self.calls += 1
        return self.about


TEXT = "2 BHK in Wagholi, society has a nice rooftop garden walkway and kids cricket net, parking for 2 cars"


@pytest.mark.asyncio
async def test_llm_proposals_are_kept_only_when_traceable():
    llm = FakeLlm({
        "highlights": ["Rooftop garden walkway", "Kids cricket net", "Five star spa", "Guaranteed 20 percent appreciation"],
        "amenities": ["Garden", "Helipad"],
        "water": "Water from the Mula river", "parking": "Parking for 2 cars",
        "nearby": [{"type": "school", "name": "Harvard School"}, {"type": "park", "name": "garden walkway"}],
    })
    res = await suggest_about("Wagholi", None, 2, TEXT, llm)
    hl = [i["text"] for i in res["highlights"]]
    assert "Rooftop garden walkway" in hl and "Kids cricket net" in hl
    assert "Five star spa" not in hl and not any("appreciation" in h for h in hl)
    assert [a["text"] for a in res["amenities"]] == ["Parking", "Garden"]  # Helipad is not in the vocabulary nor in the text
    assert res["fields"]["parking"]["text"] == "Parking available"  # deterministic wins
    assert "water" not in res["fields"]
    assert all(n["name"] != "Harvard School" for n in res["nearby"])


def test_sanitise_llm_rejects_junk():
    assert sanitise_llm_about(None, "x") == {} and sanitise_llm_about("str", "x") == {}
    assert sanitise_llm_about({"highlights": ["call 98765 43210"]}, "call 98765 43210 today") == {}
    assert sanitise_llm_about({"highlights": ["see http://x.com"]}, "see http://x.com") == {}


# ---- suggestion: every item traceable to the agent text or the area seed -----------------------------------------

def _traceable(res, text):
    low = text.lower()
    seed_text = {c["text"] for a in AREA_SEED.values() for c in a["connectivity"]}
    seed_names = {n["name"] for a in AREA_SEED.values() for n in a["nearby"]}
    for key in ("highlights", "amenities", "connectivity"):
        for it in res[key]:
            if it["source"] == "area_guide":
                assert it["text"] in seed_text
            else:
                assert it["source"] == "agent"
    for n in res["nearby"]:
        assert n["source"] in ("agent", "area_guide")
        if n["source"] == "area_guide":
            assert n["name"] in seed_names
    for k, v in res["fields"].items():
        assert v["source"] == "agent"
    assert low  # text was given


@pytest.mark.asyncio
@pytest.mark.parametrize("loc", ["Kharadi", "Upper Kharadi", "upper-kharadi", "Wagholi"])
async def test_suggest_marks_sources_and_uses_seed_for_known_areas(loc):
    text = "2 BHK, lift, gym, 1 covered parking, school nearby, maintenance 3000 per month"
    res = await suggest_about(loc, "Rohan Heights", 2, text, FakeLlm(None))
    assert res["area_known"] and res["connectivity"]
    assert all(c["source"] == "area_guide" for c in res["connectivity"])
    assert {a["text"] for a in res["amenities"]} == {"Lift", "Gym", "Parking"}
    assert all(a["source"] == "agent" for a in res["amenities"])
    assert res["project_name"] == "Rohan Heights"
    _traceable(res, text)


@pytest.mark.asyncio
async def test_unknown_area_gets_no_area_facts_and_empty_text_gets_no_agent_items():
    res = await suggest_about("Baner", None, 2, "", None)
    assert not res["area_known"] and res["connectivity"] == [] and res["amenities"] == [] and res["highlights"] == []
    res = await suggest_about("Kharadi", None, None, "", None)
    assert res["area_known"] and res["amenities"] == [] and all(n["source"] == "area_guide" for n in res["nearby"])


def test_metro_wording_is_approved_not_running_and_no_prices_or_predictions():
    for key, area in AREA_SEED.items():
        for c in area["connectivity"]:
            low = c["text"].lower()
            if "metro" in low:
                assert "approved" in low and "not running" in low, (key, c)
            assert "₹" not in c["text"] and "rs " not in low and "will " not in low and "appreciat" not in low
            assert c["source_url"].startswith("https://")
        for n in area["nearby"]:
            assert n["source_url"].startswith("https://") and "minute" not in n["name"].lower()


def test_seed_is_valid_about_content():
    for area in AREA_SEED.values():
        About.model_validate({"connectivity": [c["text"] for c in area["connectivity"]],
                              "nearby": [{"type": n["type"], "name": n["name"]} for n in area["nearby"]]})


# ---- endpoint -----------------------------------------------------------------------------------------------------

def _client(llm=None):
    app = FastAPI()
    app.include_router(r.router, prefix="/api/v1/listings")
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="u1")
    app.dependency_overrides[r.get_llm] = lambda: llm
    return TestClient(app)


def test_endpoint_requires_auth():
    route = next(x for x in r.router.routes if x.path == "/ai/about-suggest")
    assert current_active_user in [d.call for d in route.dependant.dependencies]


def test_endpoint_returns_a_tagged_draft_and_persists_nothing():
    res = _client(FakeLlm({"highlights": ["Totally invented luxury"]})).post(
        "/api/v1/listings/ai/about-suggest",
        json={"locality": "Kharadi", "bhk": 2, "description": "2 BHK, lift, 1 covered parking, school nearby"})
    assert res.status_code == 200
    b = res.json()
    assert b["area_known"] is True and b["area_name"] == "Kharadi"
    assert {"highlights", "amenities", "nearby", "connectivity", "fields"} <= set(b)
    assert all(h["text"] != "Totally invented luxury" for h in b["highlights"])
    assert any(c["source"] == "area_guide" and "not running" in c["text"] for c in b["connectivity"])
    assert b["fields"]["parking"] == {"text": "1 covered parking", "source": "agent"}


def test_endpoint_works_without_llm_and_validates_input():
    c = _client(None)
    assert c.post("/api/v1/listings/ai/about-suggest", json={"description": "lift"}).status_code == 200
    assert c.post("/api/v1/listings/ai/about-suggest", json={"description": "x" * 7000}).status_code == 422
