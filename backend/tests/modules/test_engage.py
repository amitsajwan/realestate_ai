import dataclasses
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


def post(comments, pid="PAGE_P1", message="Welcome to Avasetu"):
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
    # not in our facts: the reply says so plainly (no invented school, no bare brush-off) and a person is asked as well
    assert doc["needs_human"] and "I do not have details of nearby schools" in doc["reply"] and "Our team will reply" not in doc["reply"]
    assert doc["missing"] == "details of nearby schools" and doc["answer_basis"] == []


LISTING = {"_id": "L1", "agent_id": "A1", "transaction": "sale", "property_type": "apartment", "price_inr": 8_500_000, "city": "Pune", "locality": "Kharadi", "bhk": 2,
           "carpet_sqft": 1100, "floor": 7, "total_floors": 20, "possession": "ready", "status": "live", "title": "x",
           "about": {"maintenance": "3 rupees per sq ft per month", "nearby": [{"type": "school", "name": "City School", "minutes": 8}]}}


def with_listing(comments):
    svc, g, db = make([post(comments, pid="PAGE_555")])
    db.get_collection("publications").docs.append({"_id": "P1", "channel": "facebook_page", "external_id": "555", "listing_id": "L1"})
    db.get_collection("listings").docs.append(dict(LISTING))
    db.get_collection("agent_public_profiles").docs.append({"agent_id": "A1", "slug": "rahul"})
    return svc, g, db


async def test_a_question_about_a_listing_post_is_answered_from_the_listing_with_the_real_link():
    svc, g, db = with_listing([comment("C1", "What is the carpet area?"), comment("C2", "maintenance kitna hai", who="u2"), comment("C3", "Is there a clubhouse?", who="u3")])
    await svc.run_once()
    by = {d["_id"]: d for d in db.get_collection("engage_comments").docs}
    assert "1,100 sq ft" in by["C1"]["reply"] and by["C1"]["needs_human"] is False and by["C1"]["status"] == "replied"
    assert by["C1"]["reply"].endswith("https://site.test/agent/rahul/listings/L1?src=facebook_comment#enquire") and "{interest_url}" not in by["C1"]["reply"]
    assert by["C1"]["answer_basis"] == ["The carpet area is 1,100 sq ft."]
    assert "3 rupees per sq ft per month" in by["C2"]["reply"] and by["C2"]["language"] == "hi"
    # the clubhouse is not in the facts: said plainly, the agent is asked, and the gap is recorded for the owner
    assert by["C3"]["needs_human"] and "I do not have the amenities for this home" in by["C3"]["reply"] and by["C3"]["missing"] == "the amenities"
    assert [r[0] for r in g.replies] == ["C1", "C2", "C3"]


async def test_a_question_on_an_evergreen_calendar_post_uses_the_posts_own_verified_text():
    svc, g, db = make([post([comment("C1", "Does a RERA number mean I can relax?")], pid="PAGE_777", message="x")])
    db.get_collection("content_calendar").docs.append({"_id": "CAL1", "slug": "myth-rera-means-safe", "kind": "post", "channel": "facebook_page", "external_id": "PAGE_777",
                                                      "caption": "", "status": "published"})
    await svc.run_once()
    doc = db.get_collection("engage_comments").docs[0]
    assert doc["intent"] == "question" and doc["status"] == "replied" and "RERA" in doc["reply"] and "forward" not in doc["reply"].lower()


async def test_a_question_on_a_sample_home_post_says_it_is_a_sample_and_never_that_it_is_available():
    svc, g, db = make([post([comment("C1", "Is it available?"), comment("C2", "price?", who="u2")], pid="PAGE_888", message="Sample listing")])
    db.get_collection("content_calendar").docs.append({"_id": "CAL2", "slug": "kharadi-2bhk-ready", "kind": "showcase", "channel": "facebook_page", "external_id": "888",
                                                      "caption": "", "status": "published"})
    await svc.run_once()
    by = {d["_id"]: d for d in db.get_collection("engage_comments").docs}
    assert "sample home" in by["C1"]["reply"] and by["C1"]["needs_human"] is False and "tell us your budget" in by["C1"]["reply"]
    assert "sample price figure is ₹98 Lakh" in by["C2"]["reply"]


async def test_the_interest_url_function_supplies_the_link():
    svc, g, db = with_listing([comment("C1", "Which floor is it on?")])
    svc.interest_url = lambda ctx, channel: f"https://site.test/i/ab12cd?c={channel}"
    await svc.run_once()
    assert g.replies[0][1].endswith("https://site.test/i/ab12cd?c=facebook") and "floor 7 of 20" in g.replies[0][1]


async def test_the_caps_and_dry_run_still_apply_to_grounded_answers():
    svc, g, db = with_listing([comment("C1", "Price?"), comment("C2", "Which floor?"), comment("C3", "carpet area?")])
    svc.cfg = dataclasses.replace(svc.cfg, dry_run=True)
    counts = await svc.run_once()
    assert counts == {"dry_run": 2, "capped": 1} and g.replies == []


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


async def test_a_question_the_llm_labels_other_still_gets_a_holding_reply_and_a_place_in_the_queue():
    llm = FakeLLM({"intent": "other", "language": "en", "answerable": False, "reply": ""})
    d = await decide("what is location", None, FACTS, LINK, llm)
    assert d.intent == "question" and d.needs_human and "Our team will reply" in d.reply and LINK in d.reply
    d2 = await decide("where is it located", None, FACTS, LINK, None)  # no LLM at all
    assert d2.intent == "question" and d2.needs_human and d2.reply


async def test_chatter_that_is_not_a_question_is_left_alone():
    d = await decide("ok nice", None, FACTS, LINK, FakeLLM({"intent": "other", "language": "en"}))
    assert d.intent == "other" and d.reply is None and not d.needs_human


async def test_unknown_commenters_share_a_per_post_limit_instead_of_being_unlimited():
    posts = [post([{"id": f"C{i}", "message": "INTERESTED", "created_time": (NOW - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+0000")} for i in range(8)])]
    svc, g, db = make(posts)
    res = await svc.run_once()
    assert res == {"replied": 6, "capped": 2} and len(g.replies) == 6


async def test_only_ids_restricts_a_cycle_to_exactly_those_comments():
    svc, g, db = make([post([comment("C1", "INTERESTED", who="u1"), comment("C2", "INTERESTED", who="u2")])])
    assert await svc.run_once(only_ids={"C2"}) == {"replied": 1}
    assert [r[0] for r in g.replies] == ["C2"] and [d["_id"] for d in db.get_collection("engage_comments").docs] == ["C2"]


async def test_a_rejected_facebook_token_is_recorded_so_the_app_can_ask_for_a_reconnect():
    svc, g, db = make([post([comment("C1", "INTERESTED")])])

    async def boom():
        raise EngageGraphError("token invalid", 190)
    g.recent_posts_with_comments = boom
    assert await svc.run_once() == {"error": 1}
    st = db.get_collection("engage_status").docs[0]
    assert st["ok"] is False and st["reconnect"] is True and st["code"] == 190
    g2 = FakeGraph([post([])])
    svc.graph = g2
    await svc.run_once()
    assert db.get_collection("engage_status").docs[0]["ok"] is True and db.get_collection("engage_status").docs[0]["reconnect"] is False


async def test_other_facebook_errors_do_not_ask_for_a_reconnect():
    svc, g, db = make([post([])])

    async def boom():
        raise EngageGraphError("temporary", 2)
    g.recent_posts_with_comments = boom
    await svc.run_once()
    assert db.get_collection("engage_status").docs[0]["reconnect"] is False


async def test_interest_on_our_agent_promo_goes_to_the_pilot_signup():
    """Live 2026-10-04: an agent asked 'is it free, how can I use this' under the promo and got the old buyer landing link."""
    svc, g, db = make([post([comment("C1", "INTERESTED")], pid="PAGE_900", message="Pune property agents: stop chasing comments")])
    db.get_collection("content_calendar").docs.append({"_id": "CALP", "slug": "promo-v2-group", "kind": "post", "channel": "facebook_page",
                                                      "external_id": "PAGE_900", "caption": "", "status": "published",
                                                      "creative": {"source": "promo_agents_v2"}})
    await svc.run_once()
    doc = db.get_collection("engage_comments").docs[0]
    assert "https://site.test/pilot" in doc["reply"] and "agent/rahul" not in doc["reply"]


async def test_a_question_on_a_project_post_is_answered_from_the_project_record():
    """Live 2026-10-04: 'where is project located' under Rohan Abhilasha got 'I do not have the location'."""
    svc, g, db = make([post([comment("C1", "where is project located")], pid="PAGE_910", message="Rohan Abhilasha 4, Wagholi: 74 L")])
    db.get_collection("content_calendar").docs.append({"_id": "CALR", "slug": "hd-rohan-abhilasha", "kind": "post", "channel": "facebook_page",
                                                      "external_id": "PAGE_910", "caption": "", "status": "published", "agent_id": "HD",
                                                      "creative": {"source": "agentprojects"}})
    db.get_collection("agent_public_profiles").docs.append({"agent_id": "HD", "slug": "house-deal", "agent_name": "Sharad",
                                                           "branding_data": {"business_name": "House Deal"}})
    db.get_collection("agent_projects").docs.append({
        "_id": "P1", "agent_id": "HD", "slug": "rohan-abhilasha", "name": "Rohan Abhilasha 4", "builder": "Rohan Builders",
        "locality": "Wagholi", "address": "Lohegaon-Wagholi Road, Wagholi, Pune 412207", "rera_no": "P52100080076",
        "configurations": [{"label": "2 BHK", "bhk": 2, "carpet_sqft": 688, "price_inr": 7400000, "source": "agent"}],
        "rera": {"regno": "P52100080076", "completion_now": "2029-10-30", "units_total": 416, "units_booked": 244, "checked_at": "2026-10-03"}})
    ctx = await svc._base_context({"id": "PAGE_910", "message": "Rohan Abhilasha 4, Wagholi: 74 L"}, "facebook")
    assert "Lohegaon-Wagholi Road" in ctx["facts"] and "about 172 not yet booked" in ctx["facts"]
    assert ctx["link"].startswith("https://site.test/agent/house-deal/projects/rohan-abhilasha")


# ---- private replies: comment -> DM asking for WhatsApp number -> phone on the lead ------------------------------------
class DmGraph(FakeGraph):
    def __init__(self, posts):
        super().__init__(posts)
        self.dms, self.convs, self.dm_fail = [], [], False

    async def private_reply(self, comment_id, text):
        if self.dm_fail:
            raise EngageGraphError("(#10) This message is sent outside of allowed window or the app lacks pages_messaging")
        self.dms.append((comment_id, text))
        return f"psid-{comment_id}"

    async def inbox(self, limit=25):
        return self.convs


def make_dm(posts, dry_run=False, **cfg):
    db = FakeDb()
    conf = EngageConfig(enabled=True, dry_run=dry_run, page_id="PAGE", site_url="https://site.test", owner_agent_id="OWNER",
                        landing_url="https://site.test/agent/rahul#enquire", private_reply=True, **cfg)
    g = DmGraph(posts)
    return EngageService(db, g, None, conf, now=lambda: NOW), g, db


async def test_an_interested_commenter_also_gets_one_private_message_asking_for_whatsapp_and_budget():
    svc, g, db = make_dm([post([comment("C1", "INTERESTED")], message="Rohan Abhilasha 4, Wagholi: 2 BHK from 74 L")])
    await svc.run_once()
    assert len(g.replies) == 1 and len(g.dms) == 1
    cid, text = g.dms[0]
    assert cid == "C1" and text.startswith("Hi Priya, thanks for your comment on Rohan Abhilasha 4") and "WhatsApp number" in text
    assert "budget" in text and "site.test/agent/rahul" in text
    lead = db.get_collection("contacts").docs[0]
    assert lead["phone"] == "" and lead["dm"] == {"channel": "facebook", "id": "psid-C1"}


async def test_private_messages_are_off_by_default_and_only_recorded_in_dry_run():
    svc, g, db = make([post([comment("C1", "INTERESTED")])])
    await svc.run_once()
    assert not hasattr(g, "dms") and "dm_status" not in db.get_collection("engage_comments").docs[0]
    svc, g, db = make_dm([post([comment("C1", "INTERESTED")])], dry_run=True)
    await svc.run_once()
    doc = db.get_collection("engage_comments").docs[0]
    assert g.dms == [] and doc["dm_status"] == "dry_run" and "WhatsApp number" in doc["dm"]


async def test_one_private_message_per_person_and_none_for_praise_or_spam():
    svc, g, db = make_dm([post([comment("C1", "INTERESTED"), comment("C2", "price?"), comment("C3", "Earn money click here", who="u9")])])
    await svc.run_once()
    assert [c for c, _ in g.dms] == ["C1"]
    assert db.get_collection("engage_comments").docs[1]["dm_status"] == "skipped"


async def test_a_refused_private_message_is_recorded_and_the_public_reply_still_goes_out():
    svc, g, db = make_dm([post([comment("C1", "INTERESTED")])])
    g.dm_fail = True
    assert await svc.run_once() == {"replied": 1}
    doc = db.get_collection("engage_comments").docs[0]
    assert doc["dm_status"] == "failed" and "pages_messaging" in doc["dm_error"] and len(g.replies) == 1


async def test_agents_asking_under_our_promo_get_the_pilot_message():
    svc, g, db = make_dm([post([comment("C1", "INTERESTED")], pid="PAGE_900", message="Pune property agents: stop chasing comments")])
    db.get_collection("content_calendar").docs.append({"_id": "CALP", "slug": "promo-v2-group", "kind": "post", "channel": "facebook_page",
                                                      "external_id": "PAGE_900", "caption": "", "status": "published",
                                                      "creative": {"source": "promo_agents_v2"}})
    await svc.run_once()
    text = g.dms[0][1]
    assert "pilot is free" in text and "areas you work in" in text and "https://site.test/pilot" in text


async def test_a_number_written_back_in_the_dm_becomes_the_leads_phone_with_what_they_said():
    svc, g, db = make_dm([post([comment("C1", "INTERESTED")])])
    await svc.run_once()
    g.convs = [{"participants": {}, "messages": {"data": [  # newest first, as Meta returns them
        {"message": "budget 80 lakh, buying in 3 months", "from": {"id": "psid-C1"}},
        {"message": "my whatsapp 98765 43210", "from": {"id": "psid-C1"}},
        {"message": "Hi Priya, thanks...", "from": {"id": "PAGE"}}]}}]
    assert await svc.run_once() == {"dm_phone": 1}
    lead = db.get_collection("contacts").docs[0]
    assert lead["phone"] == "+919876543210" and lead["consent"]["how"] == "shared their number in a facebook message"
    assert lead["last_message"] == "Facebook message: “my whatsapp 98765 43210\nbudget 80 lakh, buying in 3 months”"
    assert await svc.run_once() == {}  # already has a phone: not touched again


async def test_a_dm_without_a_valid_mobile_leaves_the_lead_waiting():
    svc, g, db = make_dm([post([comment("C1", "INTERESTED")])])
    await svc.run_once()
    g.convs = [{"messages": {"data": [{"message": "call me on 12345", "from": {"id": "psid-C1"}}]}}]
    assert await svc.run_once() == {}
    assert db.get_collection("contacts").docs[0]["phone"] == ""
