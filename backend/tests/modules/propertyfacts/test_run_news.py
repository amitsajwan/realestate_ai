"""Agents hear when their posts wait for approval and when they go out: one message per post, with the links."""
from datetime import datetime

import pytest

from app.modules.propertyfacts import run_news

from ..fakes import FakeDb

NOW = datetime(2026, 11, 7, 12, 0)
AGENT, OWNER = "a1", "owner"


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

    async def tell(phone, params):
        out.append((phone, params))
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
