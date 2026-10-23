"""Ask AI prompts are steps: each says which of the agent's AIs suits it, what to paste back and what Studio does with it.
The order is the sequence: research comes first when we hold few facts."""
from datetime import datetime, timezone

from app.modules.listings.askai import gather, prompts

from .fakes import FakeDb

FIELDS = ("id", "title", "use", "text", "best", "best_note", "paste", "after")
AIS = {"ChatGPT", "Claude", "Gemini"}
LISTING = {"title": "3 BHK flat in Kharadi", "project_name": "Kumar Pinnacle", "locality": "Kharadi", "city": "Pune",
           "bhk": 3, "price_inr": 8500000, "carpet_sqft": 1050}
SHEET = {"facts": [{"key": k, "value": v, "usable": True} for k, v in
                   [("rera_no", "P52100053635"), ("possession_date", "2027-12-31"), ("units_total", 148),
                    ("land_area", "1.2 acres"), ("towers", 4), ("approved_by", "PMC")]
                   if v]}


def test_every_step_says_how_to_use_it():
    for p in prompts(LISTING, SHEET, None):
        for field in FIELDS:
            assert field in p, f"{p.get('id')} has no {field}"
        assert p["best"] in AIS
        assert p["text"].strip()


def test_the_plan_is_step_one_when_we_hold_facts():
    out = prompts(LISTING, SHEET, None)
    assert [p["id"] for p in out] == ["plan", "facts", "faq"]
    assert not any(p.get("hint") for p in out)


def test_research_becomes_step_one_when_we_hold_almost_nothing():
    out = prompts({"title": "Plot in Ranjangaon", "locality": "Ranjangaon", "city": "Pune"}, None, None)
    assert out[0]["id"] == "facts"
    assert "first" in out[0]["hint"]
    assert out[1]["id"] == "plan"


def test_the_plan_prompt_still_asks_for_the_parts_the_reader_splits():
    plan = next(p for p in prompts(LISTING, SHEET, None) if p["id"] == "plan")["text"]
    for heading in ("HEADLINE:", "PICTURES:", "CAPTIONS:", "REEL:", "STILL MISSING:"):
        assert heading in plan


async def test_gather_reads_the_checked_sheet_by_number_and_its_published_web_facts():
    """Ask AI's two sources: the property-facts sheet and the project page's web facts (passed in by app/wiring.py)."""
    db = FakeDb()
    await db.get_collection("property_facts").insert_one({"_id": "P52100012345", "rera_no": "P52100012345", "facts": {"possession": "Dec 2027"}})
    await db.get_collection("projects").insert_one({"_id": "P52100012345", "web_facts": {"at": datetime(2026, 10, 1, tzinfo=timezone.utc),
        "facts": [{"key": "towers", "label": "Towers", "value": 4, "text": "4 towers", "official": False, "sources": ["x.test"]}]}})
    sheet, web = await gather(db, {"rera_no": "P52100012345", "project_name": "Sky Heights", "locality": "Baner"})
    assert sheet["facts"] == {"possession": "Dec 2027"}
    assert web == {"read_at": "2026-10-01", "facts": [{"key": "towers", "label": "Towers", "value": 4, "text": "4 towers", "official": False,
                                                       "sources": ["x.test"]}]}
    assert await gather(FakeDb(), {"project_name": "Unknown"}) == (None, None)   # nothing known: no sources, no error
