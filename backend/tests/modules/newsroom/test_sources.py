"""Source plugins: google_news, rss, registry. Fixtures: google_news_kharadi.xml is the real feed structure
(headline, link, pubDate, source captured 2026-09-30; descriptions and two broken entries added to match the
live description format and exercise skipping); generic_rss.xml and generic_atom.xml are hand-written samples."""
from pathlib import Path

import pytest

from app.modules.newsroom import policy
from app.modules.newsroom.sources import build_sources
from app.modules.newsroom.sources._util import canonical_url, item_id, strip_html
from app.modules.newsroom.sources.google_news import GoogleNewsSource, build_queries, feed_url, parse_google_feed
from app.modules.newsroom.sources.rss import RssSource, parse_feed

pytestmark = pytest.mark.asyncio
FIX = Path(__file__).parent / "fixtures" / "sources"


def read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_canonical_url_strips_tracking_and_fragment():
    a = canonical_url("https://Example.com/a?id=7&utm_source=x&utm_medium=y#top")
    assert a == "https://example.com/a?id=7"
    assert item_id("https://example.com/a?id=7") == item_id("https://example.com/a?id=7&utm_campaign=z#f")


def test_strip_html_handles_escaped_markup():
    assert strip_html("&lt;p&gt;Hello &lt;b&gt;there&lt;/b&gt; &amp;amp; you&lt;/p&gt;&nbsp;") == "Hello there & you"
    assert strip_html(None) == ""


def test_queries_come_from_policy_and_are_unique():
    qs = build_queries()
    assert "Kharadi" in qs and "Wagholi" in qs and "PMRDA" in qs or "pmrda" in [q.lower() for q in qs]
    assert len({q.lower() for q in qs}) == len(qs)
    assert "Pune metro Kharadi" in qs
    for words in policy.AREA_KEYWORDS.values():
        for w in words:
            assert w in qs
    url = feed_url("Pune ring road")
    assert url.startswith("https://news.google.com/rss/search?q=") and "hl=en-IN&gl=IN&ceid=IN:en" in url
    assert "%22Pune+ring+road%22" in url and f"when%3A{policy.MAX_AGE_DAYS}d" in url


def test_google_parse_real_structure():
    items = parse_google_feed(read("google_news_kharadi.xml"))
    assert len(items) == 3  # empty-title and link-less entries skipped
    first = items[0]
    assert first.title == "Pune advances INR 90.5 crore land acquisition for two Kharadi DP roads"
    assert first.source == "Prop News Time"
    assert first.url.startswith("https://news.google.com/rss/articles/") and "<" not in first.text
    assert first.published_at.isoformat() == "2026-09-28T03:01:29+00:00"
    assert first.id == item_id(first.url) and len(first.id) == 40
    second = items[1]
    assert second.title.endswith("Warje Malwadi | Hindustan Times")  # only Google's " - Publisher" suffix is removed
    assert "utm_source" not in second.url and "#" not in second.url


async def test_google_fetch_dedupes_across_queries_and_survives_errors():
    calls = []

    async def get(url):
        calls.append(url)
        if len(calls) == 2:
            raise RuntimeError("network down")
        return read("google_news_kharadi.xml") if len(calls) != 3 else "<not xml"

    src = GoogleNewsSource(queries=["Kharadi", "Wagholi", "PMRDA", "Pune ring road"])
    items = await src.fetch(get)
    assert len(calls) == 4
    assert len(items) == 3 and len({i.id for i in items}) == 3


async def test_rss_parse_and_fetch():
    items = parse_feed(read("generic_rss.xml"), "PMRDA")
    assert [i.title for i in items] == ["PMRDA invites objections on ring road alignment", "Item with no date"]
    assert items[0].url == "https://civic.example.org/news/ring-road?id=7"
    assert items[0].text == "The authority has published the draft alignment & invites objections."
    assert items[0].published_at.isoformat() == "2026-09-29T04:30:00+00:00"
    assert items[1].published_at is None and items[0].source == "PMRDA"

    atom = parse_feed(read("generic_atom.xml"), "Metro")
    assert len(atom) == 1 and atom[0].url == "https://atom.example.org/metro-3"
    assert atom[0].published_at.isoformat() == "2026-09-27T08:30:00+00:00"
    assert parse_feed("garbage", "x") == [] and parse_feed("", "x") == []

    async def get(url):
        if "bad" in url:
            raise RuntimeError("boom")
        return read("generic_rss.xml")

    got = await RssSource([("A", "https://a.example/feed"), ("B", "https://bad.example/feed"),
                           ("C", "https://a.example/feed2")]).fetch(get)
    assert len(got) == 2 and all(i.source == "A" for i in got)  # same links under C are de-duplicated
    assert await RssSource().fetch(get) == []


def test_registry():
    srcs = build_sources(["google_news", "maharera", "rss", "unknown", "google_news"])
    assert [s.name for s in srcs] == ["google_news", "maharera", "rss"]
    assert build_sources([]) == []
    rss = build_sources(["rss"], rss_feeds=[("PMC", "https://pmc.example/rss")])[0]
    assert rss.feeds == [("PMC", "https://pmc.example/rss")]
