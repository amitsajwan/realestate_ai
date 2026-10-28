"""A call logged on a lead (Studio home's call list and the lead screen): what it does to the stage and the follow-up date."""
from datetime import timedelta

import pytest

from app.modules.tracking.schemas import StageUpdate

from .reverse_helpers import add_lead, make

pytestmark = pytest.mark.asyncio


async def _due(db, cid):
    return (await db.get_collection("contacts").find_one({"_id": cid}))["follow_up_due_at"]


async def test_an_answered_call_on_an_overdue_follow_up_moves_the_follow_up_on():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", stage="contacted", follow_up_due_at=clock() - timedelta(days=3))
    await svc.update_stage("A1", "B1", StageUpdate(call="answered"))
    assert await _due(db, "B1") == clock() + timedelta(days=2)


async def test_an_answered_call_keeps_a_follow_up_that_is_still_ahead():
    svc, db, clock = await make()
    ahead = clock() + timedelta(days=5)
    await add_lead(db, clock, "B1", stage="contacted", follow_up_due_at=ahead)
    await svc.update_stage("A1", "B1", StageUpdate(call="answered"))
    assert await _due(db, "B1") == ahead


async def test_an_answered_call_on_a_new_lead_makes_it_contacted_with_a_follow_up():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1")
    out = await svc.update_stage("A1", "B1", StageUpdate(call="answered"))
    assert out["stage"] == "contacted" and await _due(db, "B1") == clock() + timedelta(days=2)


async def test_no_answer_tries_again_tomorrow_even_when_overdue():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", stage="contacted", follow_up_due_at=clock() - timedelta(days=3))
    await svc.update_stage("A1", "B1", StageUpdate(call="no_answer"))
    assert await _due(db, "B1") == clock() + timedelta(days=1)


async def test_a_date_given_with_the_call_wins():
    svc, db, clock = await make()
    await add_lead(db, clock, "B1", stage="contacted", follow_up_due_at=clock() - timedelta(days=3))
    when = clock() + timedelta(days=7)
    await svc.update_stage("A1", "B1", StageUpdate(call="answered", follow_up_at=when))
    assert await _due(db, "B1") == when
