"""Agents hear when their posts wait for approval and when they go out: one message per post, with the links."""
from datetime import datetime, timedelta

import pytest

from app.modules.propertyfacts import run_news

from ..fakes import FakeDb

NOW = datetime(2026, 11, 7, 12, 0)
AGENT, OWNER = "a1", "owner"
templates = []


class Calendar:
    def __init__(self, db, rows):
        self.db, self.rows = db, rows

    async def all(self):
        return self.rows


def row(channel, status="published", link="https://x/p", **kw):
    return {"slug": "campaign-L1-listing", "agent_id": AGENT, "listing_id": "L1", "campaign_run": "r1", "channel": channel,
            "status": status, "permalink": link, **kw}


@pytest.fixture
def sent():
    out = []
    templates.clear()

    async def tell(db, phone, name, template, params, text, about):
        out.append((phone, params))
        templates.append(template)
    run_news.configure(lambda: OWNER, tell)
    yield out
    run_news.configure(lambda: "", None)


async def db_with_agent():
    db = FakeDb()
    await db.get_collection("listings").insert_one({"_id": "L1", "project_name": "KP Supernova"})
    await db.get_collection("agent_public_profiles").insert_one({"agent_id": AGENT, "agent_name": "Kausar Patanwala", "phone": "+919967464952"})
    return db


async def test_a_finished_run_tells_the_owner_to_approve_and_the_agent_it_waits(sent):
    db = await db_with_agent()
    await run_news.ready(db, AGENT, {"_id": "L1", "project_name": "KP Supernova"}, 1, 1, NOW)
    notes = await db.get_collection("notifications").find({}).to_list(5)
    told = {n["agent_id"]: n for n in notes}
    assert told[OWNER]["kind"] == "agent_posts_ready" and told[OWNER]["ref"]["screen"] == "/studio/content"
    assert "1 post and 1 reel" in told[OWNER]["summary"] and "approves them" in told[AGENT]["summary"]


async def test_the_owners_own_run_tells_only_the_owner(sent):
    db = await db_with_agent()
    await run_news.ready(db, OWNER, {"_id": "L1"}, 1, 0, NOW)
    assert [n["kind"] for n in await db.get_collection("notifications").find({}).to_list(5)] == ["posts_waiting_approval"]


async def test_one_message_with_both_links_once_every_channel_has_finished(sent):
    db = await db_with_agent()
    first = row("instagram", link="https://ig/p")
    store = Calendar(db, [first, row("facebook_page", status="approved", link=None)])
    assert not await run_news.posted(store, first)
    second = row("facebook_page", link="https://fb/p")
    store.rows = [first, second]
    assert await run_news.posted(store, second)
    assert sent == [("919967464952", ["Kausar", "KP Supernova", "https://ig/p", "https://fb/p"])]
    assert not await run_news.posted(store, first)   # the other channel's call adds nothing
    assert len(sent) == 1


async def test_a_channel_that_failed_says_so_and_the_other_link_still_goes(sent):
    db = await db_with_agent()
    good = row("instagram", link="https://ig/p")
    assert await run_news.posted(Calendar(db, [good, row("facebook_page", status="failed", link=None)]), good)
    assert sent[0][1][2:] == ["https://ig/p", run_news.NOT_POSTED]


async def test_the_owners_page_posts_and_calendar_rows_outside_a_campaign_say_nothing(sent):
    db = await db_with_agent()
    assert not await run_news.posted(Calendar(db, []), row("instagram", agent_id=OWNER))
    plain = row("instagram")
    plain.pop("campaign_run")
    assert not await run_news.posted(Calendar(db, [plain]), plain)
    assert sent == []


async def test_an_agent_with_no_mobile_still_gets_the_studio_alert(sent):
    db = await db_with_agent()
    await db.get_collection("agent_public_profiles").update_one({"agent_id": AGENT}, {"$set": {"phone": ""}})
    good = row("instagram")
    assert await run_news.posted(Calendar(db, [good]), good)
    assert sent == [] and await db.get_collection("notifications").count_documents({"kind": "post_live"}) == 1


def test_only_an_indian_mobile_is_sent_to():
    assert run_news.mobile("+91 99674 64952") == "919967464952" and run_news.mobile("9967464952") == "919967464952"
    assert run_news.mobile("02012345678") == "" and run_news.mobile(None) == ""


async def posted_two_days_ago(db, slug="campaign-L1-listing"):
    await db.get_collection(run_news.LEDGER).insert_one({"_id": f"a1:{slug}", "agent_id": AGENT, "listing_id": "L1", "slug": slug,
                                                         "at": NOW - timedelta(hours=49), "asked_at": None})


async def test_two_days_after_posting_the_agent_gets_the_numbers_and_the_question(sent):
    db = await db_with_agent()
    await posted_two_days_ago(db)
    await db.get_collection("content_metrics").insert_one({"_id": "m1", "post_id": "r1", "at": NOW, "metrics": {"views": 1240, "likes": 9}})
    store = Calendar(db, [row("instagram", _id="r1")])
    assert await run_news.results_due(store, NOW) == 1
    assert templates == [run_news.RESULTS_TEMPLATE]
    assert sent[0][1] == ["Kausar", "KP Supernova", "1,240 views, 0 enquiries"]
    assert await run_news.results_due(store, NOW) == 0   # asked once


async def test_a_post_younger_than_two_days_is_not_asked_about(sent):
    db = await db_with_agent()
    await db.get_collection(run_news.LEDGER).insert_one({"_id": "x", "agent_id": AGENT, "listing_id": "L1", "at": NOW - timedelta(hours=20), "asked_at": None})
    assert await run_news.results_due(Calendar(db, []), NOW) == 0 and sent == []


async def test_a_listings_posts_bring_one_question_not_one_each(sent):
    db = await db_with_agent()
    await posted_two_days_ago(db)
    await posted_two_days_ago(db, "campaign-L1-reel")
    assert await run_news.results_due(Calendar(db, []), NOW) == 1
    assert len(sent) == 1


async def test_with_no_numbers_yet_the_message_says_so_and_invents_none(sent):
    db = await db_with_agent()
    await posted_two_days_ago(db)
    await run_news.results_due(Calendar(db, []), NOW)
    assert sent[0][1][2] == "views are not in yet, 0 enquiries"


async def test_the_owner_can_ask_by_hand_about_the_latest_post(sent):
    db = await db_with_agent()
    await posted_two_days_ago(db)
    assert await run_news.ask_by_hand(Calendar(db, []), "919967464952")
    assert not await run_news.ask_by_hand(Calendar(db, []), "919000000000")
