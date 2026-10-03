import re

import pytest

from app.platform.text import HYPE, PHONE
from app.modules.marketing.text_posts import SITE, TEXT_POSTS


def rendered(p):
    return p["text"].format(link=p["link"]) if p["link"] else p["text"]


def test_slugs_are_unique_and_each_post_invites_a_reply():
    assert len({p["slug"] for p in TEXT_POSTS}) == len(TEXT_POSTS) >= 5
    for p in TEXT_POSTS:
        assert re.search(r"\?|Comment|comment|React|tell us", rendered(p)), p["slug"]


@pytest.mark.parametrize("p", TEXT_POSTS, ids=lambda p: p["slug"])
def test_no_phone_hype_prices_or_foreign_links(p):
    t = rendered(p)
    assert not PHONE.search(t) and not HYPE.search(t)
    assert not re.search(r"₹|\bRs\.?\s?\d|appreciat|will (rise|increase|double)|invest now|guarantee", t, re.I)
    for url in re.findall(r"https?://\S+", t):
        assert url.startswith(SITE), url
    if p["link"]:
        assert "{link}" in p["text"] and t.count(p["link"]) == 1  # the link is in the text once, and is also sent as the link preview
    assert len(t) <= 900


def test_metro_wording_never_promises_more_than_approval():
    t = " ".join(rendered(p) for p in TEXT_POSTS if "metro" in p["slug"]).lower()
    assert "approved is not the same as running" in t


@pytest.mark.parametrize("post", TEXT_POSTS, ids=lambda p: p["slug"])
def test_every_text_post_opens_with_a_hook(post):
    from app.platform.text import hook_problems
    assert hook_problems(post["text"]) == []
