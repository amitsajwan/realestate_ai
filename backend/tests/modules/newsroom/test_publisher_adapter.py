from datetime import timedelta
from urllib.parse import parse_qs

import httpx
import pytest

from app.modules.newsroom.adapters import SocialPublisher
from app.platform.meta_graph.config import SocialConfig
from app.platform.meta_graph.publisher import PublishError

from .helpers import NOW

TOKEN = "EAAB" + "x" * 30
REAL = SocialConfig(dry_run=False, page_id="123", page_token=TOKEN)


def make(handler, cfg=REAL):
    seen = []

    def h(req):
        seen.append(req)
        return handler(req)
    return SocialPublisher(cfg, transport=httpx.MockTransport(h), clock=lambda: NOW), seen


async def test_dry_run_makes_no_network_call():
    p, seen = make(lambda r: httpx.Response(500), SocialConfig(dry_run=True))
    assert (await p.publish("hi", None, None)).startswith("dry-run-") and seen == []


async def test_posts_message_and_link_now():
    p, seen = make(lambda r: httpx.Response(200, json={"id": "123_9"}))
    assert await p.publish("hello", "https://x.test/a", None) == "123_9"
    req = seen[0]
    assert str(req.url) == "https://graph.facebook.com/v23.0/123/feed"
    form = parse_qs(req.content.decode())
    assert form["message"] == ["hello"] and form["link"] == ["https://x.test/a"] and "published" not in form


async def test_scheduled_post_sets_unpublished_and_time():
    p, seen = make(lambda r: httpx.Response(200, json={"id": "1"}))
    when = NOW + timedelta(hours=3)
    await p.publish("hello", None, when)
    form = parse_qs(seen[0].content.decode())
    assert form["published"] == ["false"] and form["scheduled_publish_time"] == [str(int(when.timestamp()))] and "link" not in form


@pytest.mark.parametrize("delta", [timedelta(minutes=5), timedelta(days=31)])
async def test_schedule_outside_window_is_refused_without_a_call(delta):
    p, seen = make(lambda r: httpx.Response(200, json={"id": "1"}))
    with pytest.raises(PublishError):
        await p.publish("x", None, NOW + delta)
    assert seen == []


async def test_graph_error_is_sanitised():
    body = {"error": {"code": 190, "message": f"Invalid token {TOKEN} access_token={TOKEN}"}}
    p, _ = make(lambda r: httpx.Response(400, json=body))
    with pytest.raises(PublishError) as e:
        await p.publish("x", None, None)
    assert TOKEN not in str(e.value) and "190" in str(e.value)


async def test_timeout_and_unconfigured():
    def boom(r):
        raise httpx.ReadTimeout("slow")
    p, _ = make(boom)
    with pytest.raises(PublishError):
        await p.publish("x", None, None)
    p2, _ = make(lambda r: httpx.Response(200, json={"id": "1"}), SocialConfig(dry_run=False))
    with pytest.raises(PublishError):
        await p2.publish("x", None, None)
