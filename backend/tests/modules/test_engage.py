from datetime import datetime, timedelta

import pytest

from app.modules.engage.brain import decide, valid_reply
from app.modules.engage.config import EngageConfig
from app.modules.engage.graph import EngageGraphError
from app.modules.engage.service import EngageService, with_source

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio

LINK = "https://site.test/agent/rahul/listings/L1?src=facebook_comment#enquire"
FACTS = "2 BHK apartment for sale in Baner, Pune\n₹85 Lakh\n1,100 sq ft\nReady to move\nAmenities: Gym, Lift"
NOW = datetime(2026, 9, 30, 12, 0, 0)


class FakeLLM:
    def __init__(self, reply=None):
        self.reply, self.calls = reply, 0

    async def json(self, system, user):
        self.calls += 1
        return self.reply


# ---- brain -------------------------------------------------------------------------------------------------
async def test_plain_interested_comment_gets_the_template_with_the_link_and_no_llm_call():
    llm = FakeLLM()
    d = await decide("INTERESTED", "Priya Sharma", FACTS, LINK, llm)
    assert d.intent == "interested" and LINK in d.reply and d.reply.startswith("Thanks Priya!") and llm.calls == 0


@pytest.mark.parametrize("text", ["Earn money from home click here", "dm me on whatsapp me for loan offer", "check www.spam.example"])
async def test_spam_is_never_answered(text):
    d = await decide(text, "x", FACTS, LINK, FakeLLM())
    assert d.intent == "spam" and d.reply is None and not d.needs_human


async def test_abuse_goes_to_a_person_without_a_reply():
    d = await decide("this is a fake fraud", "x", FACTS, LINK, FakeLLM())
    assert d.intent == "complaint" and d.reply is None and d.needs_human


async def test_question_answered_from_post_facts_gets_the_drafted_reply_plus_our_link():
    llm = FakeLLM({"intent": "question", "language": "en", "answerable": True, "reply": "It is a 2 BHK with 1,100 sq ft, ready to move."})
    d = await decide("Is it ready to move?", "Amit", FACTS, LINK, llm)
    assert d.intent == "question" and not d.needs_human and "ready to move" in d.reply and d.reply.endswith(LINK)


@pytest.mark.parametrize("draft", [
    "It is 2 BHK and costs ₹90 Lakh.",                       # a number the post did not state
    "Call 9876543210 for more.",                              # phone number
    "It is the perfect home for you.",                        # hype
    "See https://evil.example/x for details.",                # a link we did not add
    "x" * 400,                                                # too long
])
async def test_unsafe_llm_drafts_fall_back_to_the_template_and_a_person(draft):
    llm = FakeLLM({"intent": "question", "language": "en", "answerable": True, "reply": draft})
    d = await decide("Tell me more?", "Amit", FACTS, LINK, llm)
    assert d.needs_human and "Our team will reply" in d.reply and draft not in d.reply


async def test_question_the_post_cannot_answer_is_flagged_for_a_person():
    llm = FakeLLM({"intent": "question", "language": "en", "answerable": False, "reply": ""})
    d = await decide("Which school is nearby?", "A", FACTS, LINK, llm)
    assert d.needs_human and d.reason == "not answerable from post facts" and LINK in d.reply


async def test_marathi_and_hindi_comments_get_matching_language_templates():
    d = await decide("माहिती पाहिजे", "राहुल", FACTS, LINK, FakeLLM({"intent": "interested", "language": "mr"}))
    assert d.language == "mr" and "धन्यवाद" in d.reply and LINK in d.reply
    d2 = await decide("इंटरेस्टेड", "x", FACTS, LINK, FakeLLM({"intent": "interested", "language": "hi"}))
    assert d2.intent == "interested"


async def test_without_an_llm_keywords_still_work_and_unclear_comments_go_to_a_person():
    d = await decide("price?", "Amit", FACTS, LINK, None)
    assert d.intent == "interested" and LINK in d.reply
    d2 = await decide("hmm ok then what about the neighbours", "Amit", FACTS, LINK, None)
    assert d2.needs_human and d2.reply is None


def test_valid_reply_rules():
    assert valid_reply("It is ready to move, 1,100 sq ft.", FACTS, LINK)
    assert not valid_reply("", FACTS, LINK) and not valid_reply("Costs 95 lakh", FACTS, LINK)


def test_with_source_puts_the_source_before_the_fragment():
    assert with_source("https://a.test/x#enquire") == "https://a.test/x?src=facebook_comment#enquire"
    assert with_source("https://a.test/x?a=1") == "https://a.test/x?a=1&src=facebook_comment"


# ---- service -----------------------------------------------------------------------------------------------
class FakeGraph:
    def __init__(self, posts):
        self.posts, self.replies, self.fail = posts, [], False

    async def recent_posts_with_comments(self):
        return self.posts

    async def reply(self, comment_id, text):
        if self.fail:
            raise EngageGraphError("(#200) permission denied")
        self.replies.append((comment_id, text))
        return f"r{len(self.replies)}"


def comment(cid, text, who="u1", name="Priya Sharma", parent=None, when=NOW - timedelta(minutes=5)):
    c = {"id": cid, "message": text, "from": {"id": who, "name": name}, "created_time": when.strftime("%Y-%m-%dT%H:%M:%S+0000")}
    if parent:
        c["parent"] = {"id": parent}
    return c


def post(comments, pid="PAGE_P1", message="Welcome to PUNE Property"):
    return {"id": pid, "message": message, "comments": {"data": comments}}


def make(posts, dry_run=False, llm=None, **cfg):
    db = FakeDb()
    conf = EngageConfig(enabled=True, dry_run=dry_run, page_id="PAGE", site_url="https://site.test", landing_url="https://site.test/agent/rahul#enquire", **cfg)
    g = FakeGraph(posts)
    return EngageService(db, g, llm, conf, now=lambda: NOW), g, db


async def test_dry_run_records_what_it_would_say_and_posts_nothing():
    svc, g, db = make([post([comment("C1", "INTERESTED")])], dry_run=True)
    assert await svc.run_once() == {"dry_run": 1}
    doc = db.get_collection("engage_comments").docs[0]
    assert doc["status"] == "dry_run" and "site.test/agent/rahul" in doc["reply"] and g.replies == []


async def test_live_mode_replies_once_and_never_twice_to_the_same_comment():
    svc, g, db = make([post([comment("C1", "INTERESTED")])])
    assert await svc.run_once() == {"replied": 1}
    assert await svc.run_once() == {}
    assert len(g.replies) == 1 and g.replies[0][0] == "C1" and db.get_collection("engage_comments").docs[0]["reply_id"] == "r1"


async def test_own_comments_threaded_replies_and_old_comments_are_ignored():
    posts = [post([comment("C1", "Thanks! details", who="PAGE"), comment("C2", "INTERESTED", parent="C1"),
                   comment("C3", "INTERESTED", when=NOW - timedelta(days=30))])]
    svc, g, db = make(posts)
    assert await svc.run_once() == {"ignored": 3} and g.replies == []


async def test_a_person_gets_at_most_two_replies_a_day():
    svc, g, db = make([post([comment(f"C{i}", "INTERESTED", who="same") for i in range(3)])])
    assert await svc.run_once() == {"replied": 2, "capped": 1} and len(g.replies) == 2


async def test_hourly_cap_stops_replies_and_leaves_the_rest_for_the_next_cycle():
    svc, g, db = make([post([comment(f"C{i}", "INTERESTED", who=f"u{i}") for i in range(5)])], max_replies_per_hour=2)
    assert await svc.run_once() == {"replied": 2}
    assert await svc.run_once() == {}  # still capped within the hour
    assert len(g.replies) == 2 and db.get_collection("engage_comments").docs.__len__() == 2


async def test_graph_errors_are_recorded_and_do_not_crash():
    svc, g, db = make([post([comment("C1", "INTERESTED")])])
    g.fail = True
    assert await svc.run_once() == {"failed": 1}
    assert "permission denied" in db.get_collection("engage_comments").docs[0]["error"]


async def test_questions_needing_a_person_are_queued_not_answered_publicly_with_guesses():
    llm = FakeLLM({"intent": "question", "language": "en", "answerable": False, "reply": ""})
    svc, g, db = make([post([comment("C1", "Which school is nearby?")])], llm=llm)
    await svc.run_once()
    doc = db.get_collection("engage_comments").docs[0]
    assert doc["needs_human"] and "Our team will reply" in doc["reply"] and not any("school" in r[1].lower() for r in g.replies)


async def test_listing_posts_link_to_the_listing_page_and_record_the_agent():
    svc, g, db = make([post([comment("C1", "INTERESTED")], pid="PAGE_555")])
    db.get_collection("publications").docs.append({"_id": "P1", "channel": "facebook_page", "external_id": "555", "listing_id": "L1"})
    db.get_collection("listings").docs.append({"_id": "L1", "agent_id": "A1", "transaction": "sale", "property_type": "apartment", "price_inr": 8_500_000,
                                               "city": "Pune", "locality": "Baner", "bhk": 2, "carpet_sqft": 1100, "title": "x"})
    db.get_collection("agent_public_profiles").docs.append({"agent_id": "A1", "slug": "rahul"})
    await svc.run_once()
    doc = db.get_collection("engage_comments").docs[0]
    assert doc["listing_id"] == "L1" and doc["agent_id"] == "A1"
    assert "https://site.test/agent/rahul/listings/L1?src=facebook_comment#enquire" in g.replies[0][1]
    assert [d["_id"] for d in await svc.recent("A1")] == ["C1"] and await svc.recent("A2") == []


async def test_page_level_posts_belong_to_the_configured_owner():
    svc, g, db = make([post([comment("C1", "INTERESTED")])], owner_agent_id="OWNER")
    await svc.run_once()
    assert db.get_collection("engage_comments").docs[0]["agent_id"] == "OWNER" and [d["_id"] for d in await svc.recent("OWNER")] == ["C1"]


@pytest.mark.parametrize("text", ["hi", "Hello", "hey!!", "hello you there", "Namaste"])
async def test_a_plain_greeting_gets_a_friendly_reply_without_an_llm_call(text):
    llm = FakeLLM()
    d = await decide(text, "Amit Sharma", FACTS, LINK, llm)
    assert d.intent == "greeting" and "INTERESTED" in d.reply and not d.needs_human and llm.calls == 0
    assert d.reply.startswith(("Hello Amit!", "नमस्ते"))


async def test_greetings_from_the_page_itself_are_still_ignored():
    svc, g, db = make([post([comment("C1", "hi", who="PAGE")])])
    assert await svc.run_once() == {"ignored": 1} and g.replies == []
