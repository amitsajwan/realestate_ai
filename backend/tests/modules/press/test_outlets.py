"""Who to pitch: the Serper cap is respected, only allowed outlets are kept, an email is kept only when the page
prints it (never guessed), and robots.txt is honoured for the one article fetch per result. No network: httpx is
stubbed throughout."""
from datetime import datetime, timezone

import httpx
import pytest

from app.modules.areastats import webfacts
from app.modules.press import outlets
from app.modules.press.config import Config

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)


async def none_fetch(url):
    return None


def test_queries_for_never_exceeds_the_cap():
    for cap in (1, 3, 10, 25):
        qs = outlets.queries_for(NOW, cap)
        assert len(qs) <= cap and len(qs) > 0


def test_queries_rotate_by_month():
    nov = outlets.queries_for(NOW, 10)
    dec = outlets.queries_for(datetime(2026, 12, 17, tzinfo=timezone.utc), 10)
    assert nov != dec


async def test_only_allowed_outlets_are_kept_and_duplicates_dropped():
    results = [
        {"title": "A", "link": "https://hindustantimes.com/a", "snippet": "", "date": "1 day ago"},
        {"title": "B", "link": "https://not-an-outlet.example/b", "snippet": "", "date": ""},
        {"title": "A again", "link": "https://hindustantimes.com/a", "snippet": "", "date": "1 day ago"},
    ]

    async def search(q):
        return results
    cfg = Config(serper_cap=1)
    out = await outlets.find_journalists(cfg, NOW, search=search, fetch=none_fetch)
    assert [j["url"] for j in out] == ["https://hindustantimes.com/a"]
    assert out[0]["outlet"] == "Hindustan Times"


async def test_a_quota_error_stops_the_month_without_raising():
    calls = []

    async def search(q):
        calls.append(q)
        if len(calls) == 2:
            request = httpx.Request("POST", "https://google.serper.dev/search")
            raise httpx.HTTPStatusError("quota", request=request, response=httpx.Response(429, request=request))
        return []
    out = await outlets.find_journalists(Config(serper_cap=5), NOW, search=search, fetch=none_fetch)
    assert out == [] and len(calls) == 2


BYLINE_HTML = (
    '<html><body><p>By Priya Sharma</p><p>Contact her at priya.sharma@example-news.in for tips.</p>'
    '<a href="/contact">Contact us</a></body></html>'
)
NO_BYLINE_HTML = "<html><body><p>A story about Pune housing, no byline here.</p></body></html>"
MAILTO_HTML = '<html><body>By Raj Mehta<br><a href="mailto:raj.mehta@example-news.in">write to Raj</a></body></html>'


async def test_byline_and_printed_email_are_kept():
    async def search(q):
        return [{"title": "Kharadi housing story", "link": "https://hindustantimes.com/kharadi", "snippet": "", "date": ""}]

    async def fetch(url):
        return BYLINE_HTML
    out = await outlets.find_journalists(Config(serper_cap=1), NOW, search=search, fetch=fetch)
    assert out[0]["name"] == "Priya Sharma"
    assert out[0]["email"] == "priya.sharma@example-news.in"
    assert out[0]["contact_page"] == "https://hindustantimes.com/contact"


async def test_mailto_link_is_kept_as_the_email():
    async def search(q):
        return [{"title": "Kharadi housing story", "link": "https://hindustantimes.com/kharadi2", "snippet": "", "date": ""}]

    async def fetch(url):
        return MAILTO_HTML
    out = await outlets.find_journalists(Config(serper_cap=1), NOW, search=search, fetch=fetch)
    assert out[0]["email"] == "raj.mehta@example-news.in"


async def test_no_email_is_ever_guessed_when_the_page_shows_none():
    async def search(q):
        return [{"title": "Kharadi housing story", "link": "https://hindustantimes.com/none", "snippet": "", "date": ""}]

    async def fetch(url):
        return NO_BYLINE_HTML
    out = await outlets.find_journalists(Config(serper_cap=1), NOW, search=search, fetch=fetch)
    assert out[0]["name"] is None and out[0]["email"] is None and out[0]["contact_page"] is None


async def test_no_article_page_at_all_still_yields_the_candidate_with_no_personal_details():
    async def search(q):
        return [{"title": "Kharadi housing story", "link": "https://hindustantimes.com/down", "snippet": "", "date": ""}]

    async def fetch(url):
        return None
    out = await outlets.find_journalists(Config(serper_cap=1), NOW, search=search, fetch=fetch)
    assert out[0]["name"] is None and out[0]["email"] is None


@pytest.fixture
def fresh_robots(monkeypatch):
    monkeypatch.setattr(webfacts, "_robots", {})


async def test_fetch_article_honours_robots_txt(fresh_robots):
    def answer(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<p>hi</p>")
    transport = httpx.MockTransport(answer)
    assert await outlets.fetch_article("https://example.com/story", transport) is None


async def test_fetch_article_sends_the_avasetubot_user_agent(fresh_robots):
    seen = {}

    def answer(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        seen["ua"] = request.headers.get("user-agent")
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<p>hi</p>")
    transport = httpx.MockTransport(answer)
    await outlets.fetch_article("https://example.com/story", transport)
    assert seen["ua"] == outlets.UA
