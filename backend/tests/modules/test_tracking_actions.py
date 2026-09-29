"""Recommended actions on GET /inbox/today (contract section 4)."""
from datetime import timedelta

import pytest

from .reverse_helpers import add_lead, add_listing, make

pytestmark = pytest.mark.asyncio


async def _actions(svc, agent="A1"):
    return (await svc.today(agent))["actions"]


async def test_existing_today_fields_unchanged_and_actions_empty_when_nothing_to_do():
    svc, _, _ = await make(with_listings=False)
    t = await svc.today("A1")
    assert set(t) == {"counts", "hot_buyers", "follow_ups", "actions", "headline"}
    assert t["actions"] == [] and t["headline"] == "You're all caught up."


async def test_call_for_hot_uncontacted_buyer():
    svc, db, clock = await make(with_listings=False)
    await add_lead(db, clock, "B1", name="Priya Sharma", base=40, bhk=2, lo=8_000_000, hi=12_000_000)
    await add_lead(db, clock, "B2", name="Contacted Hot", base=40, stage="contacted")   # already contacted
    await add_lead(db, clock, "B3", name="Cold New", base=5)                            # not hot
    await add_lead(db, clock, "B4", name="Other Agent", base=40, agent="A2")
    assert await _actions(svc) == [{"type": "call", "title": "Call Priya Sharma", "detail": "2 BHK, 80L-1.2Cr, hot buyer",
                                    "priority": 1, "lead_id": "B1"}]


async def test_call_detail_without_requirement():
    svc, db, clock = await make(with_listings=False)
    await add_lead(db, clock, "B1", name="Sam", base=40)
    assert (await _actions(svc))[0]["detail"] == "hot buyer"


async def test_follow_up_only_when_overdue_and_open():
    svc, db, clock = await make(with_listings=False)
    now = clock()
    await add_lead(db, clock, "O1", name="Overdue Ann", stage="contacted", follow_up_due_at=now - timedelta(days=2, hours=1))
    await add_lead(db, clock, "T1", name="Later Today", stage="contacted", follow_up_due_at=now + timedelta(hours=3))
    await add_lead(db, clock, "W1", name="Won Wes", stage="won", follow_up_due_at=now - timedelta(days=5))
    await add_lead(db, clock, "L1x", name="Lost Lou", stage="lost", follow_up_due_at=now - timedelta(days=5))
    acts = await _actions(svc)
    assert acts == [{"type": "follow_up", "title": "Follow up with Overdue Ann",
                     "detail": "Follow-up overdue by 2 days", "priority": 1, "lead_id": "O1"}]


async def test_lead_that_is_hot_new_and_overdue_gets_one_action():
    svc, db, clock = await make(with_listings=False)
    await add_lead(db, clock, "B1", base=40, follow_up_due_at=clock() - timedelta(days=1))
    assert [a["type"] for a in await _actions(svc)] == ["call"]


async def test_send_property_for_recent_live_listing_with_matches():
    svc, db, clock = await make(with_listings=False)
    await add_listing(db, "N1", clock, created_days_ago=1, title="2BHK in Baner", price=8_500_000)
    for i in range(3):
        await add_lead(db, clock, f"B{i}", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    await db.get_collection("marketing_packs").insert_one({"_id": "N1"})
    acts = await _actions(svc)
    assert acts == [{"type": "send_property", "title": "Send the 2 BHK in Baner to 3 matching buyers",
                     "detail": "Their budget, BHK and area fit this property", "priority": 2,
                     "listing_id": "N1", "buyer_count": 3}]


async def test_send_property_singular_and_rules():
    svc, db, clock = await make(with_listings=False)
    await add_listing(db, "OLD", clock, created_days_ago=4)          # too old
    await add_listing(db, "DRAFT", clock, created_days_ago=0, status="draft")
    await add_listing(db, "NOMATCH", clock, created_days_ago=0, locality="Kothrud", bhk=4, price=50_000_000)
    await add_listing(db, "NEW", clock, created_days_ago=2, title="x")
    for lid in ("OLD", "DRAFT", "NOMATCH", "NEW"):
        await db.get_collection("marketing_packs").insert_one({"_id": lid})
    await add_lead(db, clock, "B1", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"])
    acts = await _actions(svc)
    assert [(a["type"], a["listing_id"], a["buyer_count"]) for a in acts] == [("send_property", "NEW", 1)]
    assert acts[0]["title"] == "Send the 2 BHK in Baner to 1 matching buyer"


async def test_create_marketing_when_no_pack_present_vs_absent():
    svc, db, clock = await make(with_listings=False)
    await add_listing(db, "P1", clock, created_days_ago=10, locality="Wakad", bhk=3)
    await add_listing(db, "P2", clock, created_days_ago=10)
    await add_listing(db, "D1", clock, created_days_ago=10, status="draft")
    await add_listing(db, "U1", clock, created_days_ago=10, status="under_offer")
    acts = await _actions(svc)  # marketing_packs collection missing entirely
    assert sorted(a["listing_id"] for a in acts) == ["P1", "P2"]
    assert all(a["type"] == "create_marketing" and a["priority"] == 3 for a in acts)
    assert "Create marketing for the 3 BHK in Wakad" in [a["title"] for a in acts]
    await db.get_collection("marketing_packs").insert_one({"_id": "P1", "listing_id": "P1"})
    acts = await _actions(svc)
    assert [a["listing_id"] for a in acts] == ["P2"]
    await db.get_collection("marketing_packs").insert_one({"_id": "P2"})
    assert await _actions(svc) == []


async def test_ordering_and_cap_of_six():
    svc, db, clock = await make(with_listings=False)
    await add_listing(db, "N1", clock, created_days_ago=1)
    for i in range(4):
        await add_listing(db, f"M{i}", clock, created_days_ago=20 + i)
    await add_lead(db, clock, "M", bhk=2, lo=8_000_000, hi=9_000_000, localities=["Baner"], stage="contacted")
    await add_lead(db, clock, "H1", name="Older Hot", base=40, last_activity_days_ago=1)
    await add_lead(db, clock, "H2", name="Newer Hot", base=40)
    await add_lead(db, clock, "F1", name="Due", stage="contacted", follow_up_due_at=clock() - timedelta(days=1),
                   last_activity_days_ago=2)
    acts = await _actions(svc)
    assert len(acts) == 6
    assert [a["priority"] for a in acts] == sorted(a["priority"] for a in acts)
    assert [a["lead_id"] for a in acts[:3]] == ["H2", "H1", "F1"]  # newest activity first
    assert {a["type"] for a in acts[:3]} == {"call", "follow_up"}
    assert acts[3]["type"] == "send_property" and acts[3]["listing_id"] == "N1"
    assert [a["type"] for a in acts[4:]] == ["create_marketing"] * 2
    # recency: newest listing first among equal priority
    assert [a["listing_id"] for a in acts[4:]] == ["N1", "M0"]


async def test_recency_within_priority():
    svc, db, clock = await make(with_listings=False)
    await add_lead(db, clock, "H1", name="Older Hot", base=40, last_activity_days_ago=1)
    await add_lead(db, clock, "H2", name="Newer Hot", base=40)
    assert [a["lead_id"] for a in await _actions(svc)] == ["H2", "H1"]


async def test_actions_are_owner_scoped():
    svc, db, clock = await make(with_listings=False)
    await add_listing(db, "A2L", clock, created_days_ago=1, agent="A2")
    await add_lead(db, clock, "B1", base=40, agent="A2")
    assert await _actions(svc) == []
    assert len(await _actions(svc, "A2")) == 2
