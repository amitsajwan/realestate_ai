"""Answer gaps (knowledge/gaps.py): unanswered questions grouped per home and topic, the agent told once, the gap closed by itself."""
from datetime import datetime, timedelta, timezone

from app.modules.knowledge import gaps
from app.modules.knowledge.grounding import listing_grounding

from ..fakes import FakeDb

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
LISTING = {"_id": "L1", "agent_id": "A1", "title": "2 BHK in Kharadi", "transaction": "sale", "property_type": "apartment",
           "price_inr": 8_500_000, "city": "Pune", "locality": "Kharadi", "bhk": 2, "carpet_sqft": 1100, "status": "live", "about": {}}


async def _db():
    db = FakeDb()
    await db.get_collection("listings").insert_one(dict(LISTING))
    return db


async def _comment(db, id, text, at, gaps_=None, missing=None):
    await db.get_collection("engage_comments").insert_one({"_id": id, "channel": "facebook", "intent": "question", "needs_human": True,
                                                           "listing_id": "L1", "agent_id": "A1", "text": text, "processed_at": at,
                                                           "gaps": gaps_ or [], "missing": missing})


def _make(db, listing):
    sent = []

    async def notify(db_, agent_id, kind, summary, ref):
        sent.append((agent_id, kind, summary, ref))
    clock = {"now": NOW}

    async def grounding_for(subject):
        return listing_grounding(listing["doc"])
    return gaps.Gaps(db, notify, clock=lambda: clock["now"], grounding_for=grounding_for), sent, clock


def test_old_records_map_their_labels_back_to_topics():
    assert gaps.topics_of(None, "the parking details; the maintenance figure") == ["parking", "maintenance"]
    assert gaps.topics_of(None, "the exact distance or travel time") == ["commute"]
    assert gaps.topics_of(["water"], "ignored when structured gaps exist") == ["water"]
    assert gaps.topics_of(None, "is the society pet friendly") == ["other"]


async def test_asked_twice_the_agent_is_told_once_and_the_gap_closes_itself_when_the_fact_is_added():
    db = await _db()
    listing = {"doc": dict(LISTING)}
    g, sent, clock = _make(db, listing)
    await _comment(db, "c1", "Is there parking?", NOW - timedelta(days=2), ["parking"])
    assert (await g.refresh())["notified"] == 0                         # one ask: not yet
    await _comment(db, "c2", "parking milega kya?", NOW - timedelta(hours=3), None, "the parking details")   # an older record
    counts = await g.refresh()
    assert counts == {"open": 1, "answered": 0, "notified": 1}
    agent, kind, text, ref = sent[0]
    assert (agent, kind, ref["listing_id"]) == ("A1", "answer_gap", "L1")
    assert "asked 2 times about the parking details" in text and "2 BHK in Kharadi" in text and "parking milega kya?" in text
    assert (await g.refresh())["notified"] == 0                         # not again every cycle
    # the agent adds the parking detail: the next cycle sees the home now answers it and closes the gap; nobody ticks anything
    listing["doc"] = {**LISTING, "about": {"parking": "One covered slot"}}
    assert (await g.refresh())["answered"] == 1
    row = await db.get_collection("answer_gaps").find_one({"topic": "parking"})
    assert row["status"] == "answered" and row["count"] == 2
    # the old asks do not reopen it
    assert (await g.refresh()) == {"open": 0, "answered": 0, "notified": 0}


async def test_chat_and_whatsapp_questions_count_too_and_a_free_question_closes_by_the_faq():
    db = await _db()
    listing = {"doc": dict(LISTING)}
    g, sent, _ = _make(db, listing)
    gap = {"q": "Is the society pet friendly?", "topics": ["other"]}
    await db.get_collection("chat_sessions").insert_one({"_id": "s1", "agent_slug": "a", "updated_at": NOW - timedelta(hours=1),
                                                         "data": {"gaps": [gap], "page": {"kind": "listing", "listing_id": "L1", "agent_id": "A1"}}})
    await db.get_collection("whatsapp_conversations").insert_one({"_id": "w1", "agent_id": "A1", "updated_at": NOW - timedelta(hours=2),
                                                                  "context": {"listing_id": "L1"}, "data": {"gaps": [gap]}})
    assert (await g.refresh())["notified"] == 1
    assert "about \"2 BHK in Kharadi\"" in sent[0][2] and "FAQ" in sent[0][2]
    row = await db.get_collection("answer_gaps").find_one({"topic": "other"})
    assert row["channels"] == ["chat", "whatsapp"]
    listing["doc"] = {**LISTING, "about": {"faq": [{"q": "Are pets allowed in the society?", "a": "Yes, the society is pet friendly."}]}}
    assert (await g.refresh())["answered"] == 1


async def test_renotified_only_when_the_count_doubles_and_a_week_passed_and_old_asks_are_ignored():
    db = await _db()
    g, sent, clock = _make(db, {"doc": dict(LISTING)})
    await _comment(db, "old", "water?", NOW - timedelta(days=40), ["water"])                  # older than GAP_DAYS: ignored
    for i in range(2):
        await _comment(db, f"a{i}", "How is the water supply?", NOW - timedelta(hours=i + 1), ["water"])
    await g.refresh()
    for i in range(2):
        await _comment(db, f"b{i}", "Water ki supply kaisi hai?", NOW + timedelta(days=1, hours=i), ["water"])
    clock["now"] = NOW + timedelta(days=2)
    await g.refresh()
    assert len(sent) == 1                                                # doubled, but a week has not passed
    clock["now"] = NOW + timedelta(days=8)
    await g.refresh()
    assert len(sent) == 2 and "asked 4 times" in sent[1][2]


async def test_themes_sum_what_buyers_keep_asking_by_topic_and_area():
    db = await _db()
    g, _, _ = _make(db, {"doc": dict(LISTING)})
    for i in range(3):
        await _comment(db, f"m{i}", "maintenance?", NOW - timedelta(hours=i + 1), ["maintenance"])
    await g.refresh()
    assert await gaps.themes(db, now=NOW) == [{"topic": "maintenance", "area": "Kharadi", "asks": 3}]
