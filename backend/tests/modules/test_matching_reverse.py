"""Reverse matching (contract section 2): which of the agent's open buyers fit one property."""
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.config import settings
from app.modules.tracking.service import TrackingError

from .reverse_helpers import add_lead, make

pytestmark = pytest.mark.asyncio


async def _buyers(svc, listing_id="L1", agent="A1"):
    return await svc.matching_leads(agent, listing_id)


async def test_full_match_scores_and_shape():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"], base=20)
    out = await _buyers(svc)
    assert out["listing"] == {"id": "L1", "title": "2BHK in Baner", "price_inr": 8_500_000, "locality": "Baner",
                              "share_url": f"{settings.public_site_url}/agent/rahul/listings/L1?src=whatsapp"}
    b = out["buyers"][0]
    assert set(b) == {"lead_id", "name", "phone", "temperature", "score", "requirement_line", "match_pct",
                      "reasons", "draft"}
    assert b["match_pct"] == 95 and b["lead_id"] == "B1"  # 95: property type is neutral without a reference listing and b["temperature"] == "warm" and b["score"] == 20
    assert b["requirement_line"] == "2 BHK · 80L-90L · Baner"
    assert any("within budget" in r for r in b["reasons"]) and "In Baner" in b["reasons"]
    assert set(b["draft"]) == {"message", "whatsapp_url"}


async def test_threshold_60_and_below_excluded():
    svc, db, clock = await make()
    # bhk 2 + Baner but budget 1Cr+ (far above the 85L price): 5 + 25 + 0 + 25 = 55 -> excluded
    await add_lead(db, clock, "LOW", bhk=2, lo=10_000_000, hi=12_000_000, localities=["Baner"])
    # right BHK and budget, other locality: 5 + 25 + 40 + 0 = 70 -> included
    await add_lead(db, clock, "OK", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Wakad"])
    # wants 3 BHK: everything else fits, but a wrong bedroom count is capped at 55 -> never recommended
    await add_lead(db, clock, "BHK3", bhk=3, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    out = await _buyers(svc)
    assert [b["lead_id"] for b in out["buyers"]] == ["OK"]
    assert out["buyers"][0]["match_pct"] == 70


async def test_sorted_by_match_then_score_and_capped_at_10():
    svc, db, clock = await make()
    await add_lead(db, clock, "A", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"], base=5)      # 95
    await add_lead(db, clock, "B", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"], base=30)     # 95, hotter
    await add_lead(db, clock, "C", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"], base=0)      # 95, coldest
    await add_lead(db, clock, "D", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Wakad"], base=99)     # 70
    out = await _buyers(svc)
    assert [b["lead_id"] for b in out["buyers"]] == ["B", "A", "C", "D"]  # same 95%: hotter lead first
    for i in range(12):
        await add_lead(db, clock, f"X{i:02d}", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    assert len((await _buyers(svc))["buyers"]) == 10


async def test_excludes_closed_other_agents_no_requirement_and_other_transaction():
    svc, db, clock = await make()
    kw = dict(bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    await add_lead(db, clock, "WON", stage="won", **kw)
    await add_lead(db, clock, "LOST", stage="lost", **kw)
    await add_lead(db, clock, "OTHER", agent="A2", **kw)
    await add_lead(db, clock, "NOREQ")
    await add_lead(db, clock, "RENTER", message="looking for a flat on rent", **kw)
    await add_lead(db, clock, "NEGO", stage="negotiating", **kw)
    out = await _buyers(svc)
    assert [b["lead_id"] for b in out["buyers"]] == ["NEGO"]


async def test_rent_listing_only_matches_rent_buyers():
    svc, db, clock = await make()
    await add_lead(db, clock, "R", bhk=2, lo=30_000, hi=40_000, localities=["Baner"], message="need 2bhk for rent")
    await add_lead(db, clock, "S", bhk=2, lo=30_000, hi=40_000, localities=["Baner"])
    out = await _buyers(svc, "L6")
    assert [b["lead_id"] for b in out["buyers"]] == ["R"]


async def test_non_live_listing_has_no_buyers():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    assert (await _buyers(svc, "L5"))["buyers"] == []  # draft
    assert len((await _buyers(svc, "L4"))["buyers"]) == 1  # under_offer is still live


async def test_draft_is_personal_factual_and_wa_link():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", name="Priya Sharma", phone="+91 98765 43210", bhk=2, lo=8_000_000,
                   hi=9_000_000, localities=["Baner"])
    d = (await _buyers(svc))["buyers"][0]["draft"]
    url = f"{settings.public_site_url}/agent/rahul/listings/L1?src=whatsapp"
    assert d["message"] == f"Hi Priya, I have the 2 BHK in Baner at 85L; it fits your 80L-90L budget. Details: {url}"
    u = urlparse(d["whatsapp_url"])
    assert u.netloc == "wa.me" and u.path == "/919876543210"
    assert parse_qs(u.query)["text"] == [d["message"]]


async def test_draft_never_claims_budget_fit_when_price_is_outside():
    svc, db, clock = await make()
    # 60L-80L: price 85L is within +10% of the max (partial match, listed) but NOT inside the budget
    await add_lead(db, clock, "NEAR", bhk=2, lo=6_000_000, hi=8_000_000, localities=["Baner"])
    # no budget stated at all
    await add_lead(db, clock, "NOBUDGET", bhk=2, localities=["Baner"])
    out = await _buyers(svc)
    assert {b["lead_id"] for b in out["buyers"]} == {"NEAR", "NOBUDGET"}
    for b in out["buyers"]:
        assert "fits your" not in b["draft"]["message"] and "budget" not in b["draft"]["message"]
        assert "85L" in b["draft"]["message"]


async def test_draft_without_public_profile_skips_link():
    svc, db, clock = await make()
    db.get_collection("agent_public_profiles").docs.clear()
    await add_lead(db, clock, "B1", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    out = await _buyers(svc)
    assert out["listing"]["share_url"] is None
    assert "Details" not in out["buyers"][0]["draft"]["message"] and "http" not in out["buyers"][0]["draft"]["message"]


async def test_owner_isolation_and_unknown_listing_404():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    with pytest.raises(TrackingError) as e:
        await _buyers(svc, "L7")  # belongs to A2
    assert e.value.status_code == 404
    with pytest.raises(TrackingError) as e:
        await _buyers(svc, "nope")
    assert e.value.status_code == 404
    # A2 sees only its own leads, none of A1's
    assert (await _buyers(svc, "L7", agent="A2"))["buyers"] == []


async def test_empty_state_no_leads():
    svc, _, _ = await make()
    assert (await _buyers(svc))["buyers"] == []


async def test_buyer_who_already_enquired_about_this_property_is_not_offered_it():
    """Regression (real-Mongo run): 'send the Baner flat to 3 matching buyers' counted people who had enquired on it."""
    svc, db, clock = await make()
    await add_lead(db, clock, "SAME", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"], first_listing="L1")
    await add_lead(db, clock, "OTHER", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    assert [b["lead_id"] for b in (await _buyers(svc))["buyers"]] == ["OTHER"]


async def test_wrong_bhk_or_far_higher_budget_is_never_recommended():
    """Regression (real-Mongo run): a 4 BHK villa / Rs 2 Cr buyer and a 3 BHK buyer were offered a 2 BHK Rs 85L flat."""
    svc, db, clock = await make()
    await add_lead(db, clock, "VILLA", bhk=4, lo=None, hi=20_000_000, localities=["Baner"])
    await add_lead(db, clock, "THREE", bhk=3, lo=None, hi=13_000_000, localities=["Wakad"])
    assert (await _buyers(svc))["buyers"] == []
