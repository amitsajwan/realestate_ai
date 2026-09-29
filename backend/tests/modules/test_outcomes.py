"""Deal outcomes (contract docs/contracts/outcomes.md): won/lost results, clearing, attribution and results."""
from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.modules.tracking.schemas import OutcomeIn, StageUpdate
from app.modules.tracking.service import TrackingError

from .reverse_helpers import add_lead, make

pytestmark = pytest.mark.asyncio


async def _setup():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"], first_listing="L1", source="instagram")
    return svc, db, clock


async def test_won_with_price_and_listing_stores_outcome_and_suggests_sold():
    svc, db, clock = await _setup()
    out = await svc.update_stage("A1", "B1", StageUpdate(stage="won", outcome=OutcomeIn(deal_price_inr=8_400_000)))
    assert out["stage"] == "won"
    assert out["outcome"]["result"] == "won" and out["outcome"]["deal_price_inr"] == 8_400_000
    assert out["outcome"]["listing_id"] == "L1"  # defaults to the listing they enquired about
    assert out["suggest_listing_status"] == {"listing_id": "L1", "status": "sold"}
    assert out["outcome"]["closed_at"] == clock()


async def test_won_without_any_outcome_still_works_and_price_is_never_guessed():
    svc, db, _ = await _setup()
    out = await svc.update_stage("A1", "B1", StageUpdate(stage="won"))
    assert out["outcome"]["deal_price_inr"] is None and out["outcome"]["listing_id"] == "L1"


async def test_lost_with_reason():
    svc, db, _ = await _setup()
    out = await svc.update_stage("A1", "B1", StageUpdate(stage="lost", outcome=OutcomeIn(lost_reason="price")))
    assert out["outcome"] == {**out["outcome"], "result": "lost", "lost_reason": "price", "deal_price_inr": None, "listing_id": None}
    assert "suggest_listing_status" not in out


async def test_reopening_clears_the_outcome():
    svc, db, _ = await _setup()
    await svc.update_stage("A1", "B1", StageUpdate(stage="won", outcome=OutcomeIn(deal_price_inr=8_400_000)))
    out = await svc.update_stage("A1", "B1", StageUpdate(stage="contacted"))
    assert out["outcome"] is None and out["stage"] == "contacted"


async def test_listing_must_be_the_agents_own():
    svc, db, _ = await _setup()
    with pytest.raises(TrackingError) as e:
        await svc.update_stage("A1", "B1", StageUpdate(stage="won", outcome=OutcomeIn(listing_id="NOPE")))
    assert e.value.status_code == 422


def test_outcome_only_with_won_or_lost_and_matching_fields():
    with pytest.raises(ValidationError):
        StageUpdate(stage="contacted", outcome=OutcomeIn(deal_price_inr=1))
    with pytest.raises(ValidationError):
        StageUpdate(stage="lost", outcome=OutcomeIn(deal_price_inr=1))
    with pytest.raises(ValidationError):
        StageUpdate(stage="won", outcome=OutcomeIn(lost_reason="price"))
    with pytest.raises(ValidationError):
        OutcomeIn(deal_price_inr=0)


async def test_performance_attributes_deals_and_by_source():
    svc, db, _ = await _setup()
    await svc.update_stage("A1", "B1", StageUpdate(stage="won", outcome=OutcomeIn(deal_price_inr=8_400_000)))
    items = {i["listing_id"]: i for i in (await svc.performance("A1"))["items"]}
    assert items["L1"]["deals"] == 1 and items["L1"]["deal_value_inr"] == 8_400_000
    assert items["L1"]["deals_by_source"] == {"instagram": 1}


async def test_today_results_last_30_days_only():
    svc, db, clock = await make()
    await add_lead(db, clock, "W1", first_listing="L1", source="instagram", bhk=2)
    await add_lead(db, clock, "W2", first_listing="L1", source="instagram", bhk=2)
    await add_lead(db, clock, "W3", first_listing="L1", source="whatsapp", bhk=2)
    await add_lead(db, clock, "LO", first_listing="L1", source="facebook", bhk=2)
    await svc.update_stage("A1", "W1", StageUpdate(stage="won", outcome=OutcomeIn(deal_price_inr=8_000_000)))
    await svc.update_stage("A1", "W2", StageUpdate(stage="won", outcome=OutcomeIn(deal_price_inr=9_000_000)))
    await svc.update_stage("A1", "LO", StageUpdate(stage="lost", outcome=OutcomeIn(lost_reason="price")))
    clock.advance(days=40)  # an old win falls out of the 30-day window
    await svc.update_stage("A1", "W3", StageUpdate(stage="won", outcome=OutcomeIn(deal_price_inr=5_000_000)))
    r = (await svc.today("A1"))["results"]
    assert r["period_days"] == 30 and r["deals_won"] == 1 and r["deal_value_inr"] == 5_000_000
    assert r["top_source"] == "whatsapp" and r["deals_lost"] == 0 and r["lost_reasons"] == {}
    clock.advance(days=-40)


async def test_today_results_counts_recent_wins_top_source_and_lost_reasons():
    svc, db, clock = await make()
    for cid, src in (("W1", "instagram"), ("W2", "instagram"), ("W3", "whatsapp")):
        await add_lead(db, clock, cid, first_listing="L1", source=src, bhk=2)
        await svc.update_stage("A1", cid, StageUpdate(stage="won", outcome=OutcomeIn(deal_price_inr=8_000_000)))
    await add_lead(db, clock, "LO", first_listing="L1", source="facebook", bhk=2)
    await svc.update_stage("A1", "LO", StageUpdate(stage="lost", outcome=OutcomeIn(lost_reason="price")))
    r = (await svc.today("A1"))["results"]
    assert r["deals_won"] == 3 and r["deal_value_inr"] == 24_000_000 and r["top_source"] == "instagram"
    assert r["deals_lost"] == 1 and r["lost_reasons"] == {"price": 1}


async def test_empty_results_for_a_new_agent():
    svc, db, clock = await make()
    r = (await svc.today("A1"))["results"]
    assert r == {"period_days": 30, "deals_won": 0, "deal_value_inr": 0, "deals_lost": 0, "top_source": None, "lost_reasons": {}}


async def test_other_agent_cannot_close_my_lead():
    svc, db, _ = await _setup()
    with pytest.raises(TrackingError) as e:
        await svc.update_stage("A2", "B1", StageUpdate(stage="won"))
    assert e.value.status_code == 404
