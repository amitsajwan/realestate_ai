"""Messenger / Instagram DMs read with where the person came from (2026-10-18): the comment that opened the chat, a shared reel, a link's ref,
a code typed alone, a project or guide named in the message; agents get the agent answer and never a buyer lead."""
import pytest

from app.modules.whatsapp import adapters
from app.modules.whatsapp.dms import UNDERSTAND, parse

from ..fakes import FakeDb
from .test_dms import IG, IGSID, PAGE, cfg, event, make

pytestmark = pytest.mark.asyncio

MHADA = {"_id": "cal-mhada", "slug": "mhada-pune-lottery-2026", "external_id": "18199779892378889", "caption": "MHADA Pune lottery 2026: how to apply",
         "reply_facts": ["The homes in this MHADA Pune board lottery are only in Pune city, Pimpri-Chinchwad and PMRDA.",
                         "Other districts such as Nashik come under other MHADA boards with their own lotteries.",
                         "The last date to apply online is 22 October 2026."],
         "reply_faq": [{"q": "Is it in Nashik?", "a": "No. Nashik has its own MHADA board."}], "creative": {"audience": "buyers"}}


class FakeLLM:
    """Answers only the 'who and what' question; every other call fails, so answers come from our facts by the rules."""
    def __init__(self, who="other", need="question"):
        self.who, self.need, self.calls = who, need, []

    async def json(self, system, user):
        self.calls.append(system[:40])
        if system == UNDERSTAND:
            return {"who": self.who, "need": self.need, "about": "test"}
        return None


def test_parse_keeps_where_they_came_from():
    reel = event(None, attachments=[{"type": "ig_reel", "payload": {"reel_video_id": "18199779892378889", "title": "MHADA lottery"}}])
    m = parse(reel)
    assert m["media"] and m["refs"]["media_ids"] == ["18199779892378889"] and m["refs"]["shared_title"] == "MHADA lottery"
    story = event("Is it in Nashik?")
    story["message"]["reply_to"] = {"story": {"id": "st1", "url": "https://cdn/x"}}
    assert parse(story)["refs"]["reply_to_story"] is True
    opened = {"sender": {"id": "u1"}, "recipient": {"id": PAGE}, "timestamp": 1, "referral": {"ref": "ykyattg", "source": "SHORTLINK"}}
    assert parse(opened)["kind"] == "referral" and parse(opened)["refs"]["ref"] == "ykyattg"


def test_a_code_typed_alone_is_found_and_words_are_not():
    assert adapters.codes_in("about zy4wad2 - when will metro start?") == ["zy4wad2"]
    assert adapters.codes_in("interested in buying a flat in kharadi") == []


async def test_a_dm_after_a_comment_is_answered_from_that_posts_sheet():
    db = FakeDb()
    db.get_collection("content_calendar").docs.append(MHADA)
    db.get_collection("engage_comments").docs.append({"_id": "c1", "dm_recipient": IGSID, "calendar_id": "cal-mhada", "text": "नाशिक मध्ये आहे का",
                                                      "processed_at": None})
    svc, db, _, _ = make(c=cfg(), db=db)
    svc.llm = FakeLLM("other", "question")
    m = parse(event("When is the last date?", sender=IGSID, recipient=IG))
    assert await svc.claim("instagram", m)
    r = await svc.handle("instagram", m)
    c = await db.get_collection("dm_conversations").find_one({"_id": f"instagram:{IGSID}"})
    assert c["context"]["kind"] == "calendar" and c["context"]["came_from"].startswith("commented on our post")
    assert "22 October 2026" in r["reply"] and "buy or rent" not in r["reply"].lower()


async def test_a_question_with_no_origin_finds_our_guide_post():
    db = FakeDb()
    db.get_collection("content_calendar").docs.append(MHADA)
    found = await adapters.guide_for(db, "MHADA lottery apply last date")
    assert found and found["ref"] == "cal-mhada"
    assert await adapters.guide_for(db, "2 BHK in Kharadi under 90 lakh") is None


async def test_an_agent_gets_the_agent_answer_and_no_buyer_lead():
    svc, db, _, _ = make()
    svc.llm = FakeLLM("agent", "question")
    m = parse(event("I am a property agent in Wagholi. How can I list my properties?"))
    assert await svc.claim("messenger", m)
    r = await svc.handle("messenger", m)
    assert r["reply"] and "buy or rent" not in r["reply"].lower()
    assert not db.get_collection("contacts").docs                      # an agent is not a buyer lead
    kinds = [n.get("kind") for n in db.get_collection("notifications").docs]
    assert "dm_agent" in kinds
