"""Joining Avasetu is open and free for Pune agents (owner, 2026-11-27): no post, reel or caption an agent can see still offers
a trial, a free month or a place among the "first 20". The LinkedIn recruiting post says "open and free"; our own posts must not
contradict it. The WhatsApp keyword TRIAL stays (old QR codes say it), so only the offer words are banned, not the word itself."""
import inspect
import re

import pytest

from app.modules.calendar import adapters as calendar_adapters
from app.modules.calendar.library import ENTRIES
from app.modules.marketing.brand_posts import POSTS
from app.modules.marketing.text_posts import TEXT_POSTS
from app.modules.reels import agent_reels, flow_reels, transform_reels

OFFER = re.compile(r"free[\s-]trial|month free|first 20|ek mahina|founding offer|ट्रायल|पायलट|इन्विटेशन|आमंत्रण", re.I)


def test_brand_and_text_posts_offer_no_trial():
    for post in POSTS + TEXT_POSTS:
        assert not OFFER.search(repr(post)), post["slug"]


def test_calendar_entries_offer_no_trial():
    for entry in ENTRIES:
        assert not OFFER.search(repr(entry)), entry.slug
    assert not OFFER.search(calendar_adapters.PITCH_CAPTION_BODY)


@pytest.mark.parametrize("module", [agent_reels, flow_reels, transform_reels])
@pytest.mark.parametrize("channel", ["facebook_page", "instagram"])
def test_agent_reel_captions_offer_no_trial(module, channel):
    for code in module.BY_CODE:
        assert not OFFER.search(module.caption(code, channel)), code


@pytest.mark.parametrize("module", [agent_reels, transform_reels, calendar_adapters])
def test_reel_frames_offer_no_trial(module):
    """The closing frames are drawn from literals in the module; reading the source avoids drawing a video in a test."""
    assert not OFFER.search(inspect.getsource(module))
