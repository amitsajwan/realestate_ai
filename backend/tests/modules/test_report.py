from datetime import datetime, timedelta

import pytest

from app.modules.report.service import ReportService

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio
NOW = datetime(2026, 9, 30, 12, 0, 0)
AGO = lambda **k: NOW - timedelta(**k)  # noqa: E731


def listing(_id, agent="A1", photos=1, **over):
    return {"_id": _id, "agent_id": agent, "status": "live", "title": f"Listing {_id}", "published_at": AGO(days=2), "freshness_confirmed_at": AGO(days=2),
            "media": [{"url": "u", "kind": "image"}] * photos, **over}


def make():
    db = FakeDb()
    db.get_collection("agent_public_profiles").docs.append({"agent_id": "A1", "slug": "rahul"})
    return ReportService(db, now=lambda: NOW), db


def view(agent, listing_id, anon, when, typ="listing_view"):
    return {"agent_id": agent, "type": typ, "listing_id": listing_id, "anon_id": anon, "ts": when}


async def test_numbers_come_only_from_the_last_seven_days_and_only_this_agents_data():
    svc, db = make()
    db.get_collection("listings").docs += [listing("L1"), listing("L2"), listing("X1", agent="A2")]
    ev = db.get_collection("events").docs
    ev += [view("A1", "L1", "a", AGO(days=1)), view("A1", "L1", "b", AGO(days=2)), view("A1", "L2", "a", AGO(days=3)),
           view("A1", "L1", "old", AGO(days=20)), view("A2", "X1", "z", AGO(days=1)), {"agent_id": "A1", "type": "page_view", "anon_id": "c", "ts": AGO(days=1)}]
    db.get_collection("contacts").docs += [
        {"_id": "c1", "agent_id": "A1", "created_at": AGO(days=1), "last_activity_at": AGO(days=1), "stage": "new", "first_listing_id": "L1", "score_base": 40,
         "requirement": {"budget_max_inr": 9_000_000}},
        {"_id": "c2", "agent_id": "A1", "created_at": AGO(days=30), "last_activity_at": AGO(days=30), "stage": "new", "score_base": 0}]
    r = await svc.weekly("A1")
    n = r["numbers"]
    assert n["listing_views"] == 3 and n["visitors"] == 3 and n["new_enquiries"] == 1 and n["qualified_enquiries"] == 1 and n["live_listings"] == 2
    assert r["top_listing"] == {"listing_id": "L1", "title": "Listing L1", "views": 2, "enquiries": 1}


async def test_tips_are_concrete_and_only_appear_when_they_apply():
    svc, db = make()
    db.get_collection("listings").docs += [listing("L1", photos=0), listing("L2", photos=0), listing("L3", freshness_confirmed_at=AGO(days=30), published_at=AGO(days=30))]
    db.get_collection("contacts").docs.append({"_id": "c1", "agent_id": "A1", "created_at": AGO(days=3), "last_activity_at": AGO(days=3), "stage": "new", "score_base": 0})
    db.get_collection("engage_comments").docs.append({"_id": "k1", "agent_id": "A1", "processed_at": AGO(hours=5), "intent": "question", "needs_human": True, "status": "needs_human"})
    kinds = {t["kind"]: t for t in (await svc.weekly("A1"))["todo"]}
    assert kinds["photos"]["count"] == 2 and kinds["freshness"]["count"] == 1 and kinds["followup"]["count"] == 1 and kinds["answer"]["count"] == 1
    svc2, db2 = make()
    db2.get_collection("listings").docs.append(listing("L1"))
    db2.get_collection("events").docs.append(view("A1", "L1", "a", AGO(days=1)))
    todo = (await svc2.weekly("A1"))["todo"]
    assert [t["kind"] for t in todo] == ["share"]  # a live listing with photos but no enquiries: share it
    svc3, _ = make()
    assert [t["kind"] for t in (await svc3.weekly("A1"))["todo"]] == ["post"]


async def test_chat_and_facebook_activity_are_counted_and_the_share_text_has_no_phone_number():
    svc, db = make()
    db.get_collection("listings").docs.append(listing("L1"))
    db.get_collection("engage_comments").docs += [{"_id": "k1", "agent_id": "A1", "processed_at": AGO(days=1), "intent": "interested"},
                                                  {"_id": "k2", "agent_id": "A1", "processed_at": AGO(days=1), "intent": "spam"}]
    db.get_collection("chat_sessions").docs += [{"_id": "s1", "agent_slug": "rahul", "updated_at": AGO(days=1), "messages": [1, 2], "lead_created": True},
                                                {"_id": "s2", "agent_slug": "other", "updated_at": AGO(days=1), "messages": [1]}]
    r = await svc.weekly("A1")
    assert r["numbers"]["facebook_interest"] == 1 and r["numbers"]["chats"] == 1 and r["numbers"]["chat_leads"] == 1
    import re
    assert not re.search(r"\d{10}", r["share_text"]) and "/agent/rahul" in r["share_text"]
