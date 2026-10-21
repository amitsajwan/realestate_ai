"""Instagram buyers' way on (2026-10-20): the caption's WhatsApp line with the post's code, and the /go cards (one per listing, reels too,
an Instagram copy over the Facebook one, no recruitment posts)."""
import pytest

from app.modules.calendar import adapters

from ..fakes import FakeDb

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PUBLIC_NUMBER", "919834256406")
    monkeypatch.setenv("INTEREST_OWNER_AGENT_ID", "OWNER")
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://media.test")
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://site.test")


def row(slug="campaign-L1-listing", channel="instagram", caption="Godrej Ivara: 2 BHK ₹1.20 Cr.", **kw):
    return {"_id": f"{slug}-{channel}", "slug": slug, "channel": channel, "kind": "post", "caption": caption, "images": ["p/1.jpg"],
            "creative": {"audience": "buyers"}, "tags": {"audience": "buyers"}, **kw}


async def test_instagram_caption_sends_buyers_to_whatsapp_with_the_posts_code():
    db = FakeDb()
    out = (await adapters.with_interest(db, row()))["caption"]
    code = db.get_collection("interest_links").docs[0]["code"]
    assert f"Price list and floor plans on WhatsApp: send {code} to +91 98342 56406." in out
    assert "Tap the link in our bio and press" not in out and "http" not in out
    guide = (await adapters.with_interest(db, row("upper-kharadi-names", caption="Upper Kharadi vs Kharadi Annex: the names.")))["caption"]
    assert "Questions? WhatsApp +91 98342 56406 and send" in guide and "price list" not in guide.lower()


async def test_facebook_keeps_its_tap_links():
    out = (await adapters.with_interest(FakeDb(), row(channel="facebook_page")))["caption"]
    assert "One tap tells us: https://" in out and "send " not in out


async def test_one_go_card_per_listing_newest_post_and_instagram_wins():
    db = FakeDb()
    db.get_collection("listings").docs.append({"_id": "L1", "title": "Godrej Ivara, Upper Kharadi", "locality": "Upper Kharadi", "status": "live"})
    await adapters.register_hub(db, row(listing_id="L1"), "https://instagram.test/p/1")
    await adapters.register_hub(db, row("campaign-L1-room1", "facebook_page", listing_id="L1"), "https://facebook.test/r/2")
    cards = db.get_collection("hub_items").docs
    assert len(cards) == 1 and cards[0]["_id"] == "listing:L1" and cards[0]["permalink"] == "https://instagram.test/p/1"   # FB did not replace IG
    await adapters.register_hub(db, row("campaign-L1-room1", "instagram", listing_id="L1", kind="reel", images=[], video="c/r1.mp4"),
                                "https://instagram.test/reel/3")
    card = db.get_collection("hub_items").docs[0]
    assert len(db.get_collection("hub_items").docs) == 1 and card["slug"] == "campaign-L1-room1" and card["title"] == "Godrej Ivara, Upper Kharadi"
    assert card["image_url"] == "https://media.test/uploads/c/r1-cover.jpg" and card["subtitle"] == "Upper Kharadi"
    code = card["interest_code"]
    assert db.get_collection("interest_links").docs[-1]["channel"] == "instagram" and code


async def test_recruitment_posts_and_reels_without_a_picture_make_no_card(tmp_path):
    db = FakeDb()
    await adapters.register_hub(db, row("agent-buyer-summary"))   # a library post with pillar "agent"
    await adapters.register_hub(db, row("reel-x", kind="reel", images=[], video="c/x.mp4"), "", tmp_path)   # no cover drawn
    assert db.get_collection("hub_items").docs == []


async def test_a_stopped_topic_gets_no_card():
    db = FakeDb()
    await adapters.register_hub(db, row("mhada-areas-mr-20261019", caption="MHADA Pune Lottery 2026: Lohegaon"))
    assert db.get_collection("hub_items").docs == []


async def test_a_listings_instagram_caption_asks_for_its_word():
    db = FakeDb()
    db.get_collection("listings").docs.append({"_id": "L1", "project_name": "Godrej Ivara", "status": "live"})
    out = (await adapters.with_interest(db, row(listing_id="L1")))["caption"]
    assert "Price list and floor plans on WhatsApp: send IVARA to +91 98342 56406." in out


async def test_a_home_card_names_its_project():
    db = FakeDb()
    db.get_collection("listings").docs.append({"_id": "L2", "title": "3 BHK for sale in Kharadi", "project_name": "Lodha Camelot", "status": "live"})
    await adapters.register_hub(db, row("campaign-L2-listing", listing_id="L2"), "https://instagram.test/p/9")
    assert db.get_collection("hub_items").docs[0]["title"] == "Lodha Camelot · 3 BHK for sale in Kharadi"
