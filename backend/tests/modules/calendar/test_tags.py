"""Tags on every calendar row (calendar/tags.py): derived from what the row holds, fixed vocabulary, 'unknown' when not known."""
import asyncio
from datetime import datetime, timezone

import pytest

from app.modules.calendar import tags
from app.modules.calendar.store import Store

from ..fakes import FakeDb

DUE = datetime(2026, 10, 12, 4, 30, tzinfo=timezone.utc)
KEYS = {"schema", "audience", "kind", "format", "pillar", "hook_type", "hook", "cta", "area", "language"}


@pytest.mark.parametrize("hook,expected", [
    ("Guess the price of this 2 BHK in Wagholi", "price_reveal"),
    ("This looks like a ₹1Cr apartment… wait for the price.", "price_reveal"),
    ("Myth: carpet area and super built-up are the same", "myth"),
    ("The site-visit mistake most Kharadi buyers make", "mistake"),
    ("STOP! Check these 3 things before buying", "mistake"),
    ("Which would you choose: Kharadi or Wagholi?", "question"),
    ("3 site visits before you pay a token", "number"),
    ("Pune Property of the Week", "statement"),
    ("", "unknown"),
])
def test_hook_type_is_read_from_the_words(hook, expected):
    assert tags.hook_type(hook) == expected


def test_the_writers_own_hook_type_wins():
    assert tags.hook_type("Is ₹50 lakh enough?", "price_reveal") == "price_reveal"


def test_a_reel_row_gets_format_cta_area_and_audience():
    row = {"kind": "reel", "slug": "reel-w1-tip", "caption": "Buying in Wagholi? Check this first.\n\nSave this for later.",
           "creative": {"role": "reel", "source": "plan", "template": "tip", "script": ["Comment *INTERESTED* for details"]}}
    t = tags.derive(row)
    assert set(t) >= KEYS and t["schema"] == tags.TAGS_SCHEMA
    assert (t["format"], t["cta"], t["area"], t["audience"], t["hook_type"]) == ("tip", "INTERESTED", "wagholi", "buyers", "question")


def test_agent_reels_trend_reels_and_campaign_reels_have_their_own_format():
    agent = tags.derive({"kind": "reel", "slug": "agent-reel-a1", "caption": "x", "creative": {"source": "agent_reels", "template": "agent",
                                                                                              "role": "agent"}})
    trend = tags.derive({"kind": "reel", "slug": "trend-x", "caption": "x", "creative": {
        "source": "trend_reels", "experiment": "EXP-001", "variant": "B", "hook_type": "question", "engine": "PRICE_REVEAL",
        "locality": "kharadi", "price_band": "50L"}})
    listing = tags.derive({"kind": "reel", "slug": "l", "caption": "x", "creative": {"source": "campaign", "role": "listing"}})
    assert (agent["format"], agent["audience"]) == ("agent_ad", "agents")
    assert (trend["format"], trend["experiment"], trend["variant"], trend["engine"], trend["price_band"], trend["area"]) == (
        "trend", "EXP-001", "B", "PRICE_REVEAL", "50L", "kharadi")
    assert listing["format"] == "listing"


def test_post_formats_and_unknowns():
    assert tags.derive({"kind": "post", "slug": "s", "caption": "", "creative": {"format": "poll"}})["format"] == "poll"
    assert tags.derive({"kind": "post", "slug": "s", "caption": "", "creative": {"slides": 5}})["format"] == "carousel"
    assert tags.derive({"kind": "showcase", "slug": "s", "caption": "", "creative": {}})["format"] == "showcase"
    t = tags.derive({"kind": "post", "slug": "s", "caption": "", "creative": {}})
    assert (t["format"], t["pillar"], t["hook_type"], t["area"], t["cta"]) == ("unknown", "unknown", "unknown", "unknown", "none")


def test_render_facts_survive_a_new_derivation():
    t = tags.derive({"kind": "reel", "slug": "s", "caption": "", "tags": {"duration_s": 12.4, "render": "v"}, "creative": {}})
    assert (t["duration_s"], t["render"]) == (12.4, "v")


async def test_every_row_written_through_the_store_is_tagged_and_older_rows_are_backfilled():
    db = FakeDb()
    store = Store(db)
    id = await store.add("reel-w1-tour", "instagram", "Guess the price of this 2 BHK in Kharadi", "", DUE, kind="reel",
                         creative={"template": "tour", "role": "reel"})
    row = await store.get(id)
    assert row["tags"]["format"] == "tour" and row["tags"]["hook_type"] == "price_reveal" and row["tags"]["area"] == "kharadi"
    # a row from before tags existed
    await db.get_collection("content_calendar").insert_one({"_id": "old", "slug": "old", "kind": "post", "channel": "instagram",
                                                            "caption": "Myth: ready to move means no risk", "creative": {"format": "myth-vs-fact"},
                                                            "due_at": DUE, "status": "published"})
    assert await store.backfill_tags() == 1
    assert (await store.get("old"))["tags"]["format"] == "myth-vs-fact"
    assert await store.backfill_tags() == 0   # safe to run again


async def test_rendering_records_length_and_look_and_a_carousel_sent_as_a_reel_says_so():
    store = Store(FakeDb())
    reel = await store.add("reel-w1-tip", "instagram", "x", "", DUE, kind="reel", creative={"template": "tip"})
    await store.set_video(reel, "calendar/reels/x.mp4", {"duration_s": 14.2, "render": "2026-10-07-smooth"})
    t = (await store.get(reel))["tags"]
    assert (t["duration_s"], t["render"], t["format"]) == (14.2, "2026-10-07-smooth", "tip") and "published_as" not in t
    post = await store.add("carousel", "facebook_page", "x", "a.jpg", DUE, kind="post", images=["a.jpg", "b.jpg"], creative={"slides": 2})
    await store.set_video(post, "calendar/slidereels/c.mp4", {})
    t = (await store.get(post))["tags"]
    assert (t["format"], t["published_as"]) == ("carousel", "reel")


def test_cta_needs_the_keyword_in_capitals_and_a_myth_card_has_a_myth_hook():
    row = {"kind": "post", "slug": "s", "caption": "Your comment becomes a lead.\n\nComment AGENT to join.", "creative": {}}
    assert tags.derive(row)["cta"] == "AGENT"
    assert tags.derive({**row, "caption": "Every comment becomes a lead."})["cta"] == "none"
    myth = {"kind": "post", "slug": "s", "caption": "It has a RERA number, so I can relax", "creative": {"format": "myth-vs-fact"}}
    assert tags.derive(myth)["hook_type"] == "myth"
