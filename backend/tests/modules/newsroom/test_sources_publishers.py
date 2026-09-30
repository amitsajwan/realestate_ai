"""Publisher feeds. Fixtures fixtures/sources/publisher_*.xml are real feed captures (HTTP GET, 2026-09-30),
trimmed to the first few items and with item bodies dropped; see docs/handoff/N2a-publishers.md. No network."""
from pathlib import Path
from typing import Dict

import pytest

from app.modules.newsroom.sources import build_sources
from app.modules.newsroom.sources.google_news import parse_google_feed
from app.modules.newsroom.sources.publishers import (NATIONAL_FEEDS, PUBLISHER_FEEDS, PublishersSource, clean_summary,
                                                     is_relevant)
from app.modules.newsroom.sources.rss import parse_feed
from app.modules.newsroom.types import RawItem

pytestmark = pytest.mark.asyncio
FIX = Path(__file__).parent / "fixtures" / "sources"
URL = {(n, u): u for n, u in PUBLISHER_FEEDS}
HT_PUNE, TOI_PUNE, IE_PUNE, PUNEKAR, _, PMRDA = PUBLISHER_FEEDS[:6]
ET_REALTY, HINDU_RE, NEWS18_PUNE = PUBLISHER_FEEDS[7], PUBLISHER_FEEDS[8], PUBLISHER_FEEDS[9]


def read(name: str) -> str:
    return (FIX / f"publisher_{name}.xml").read_text(encoding="utf-8")


def fake_get(pages: Dict[str, str]):
    async def get(url: str) -> str:
        if url not in pages:
            raise RuntimeError("boom")
        return pages[url]
    return get


def raw(title: str, text: str = "") -> RawItem:
    return RawItem(id="x", source="s", url="https://e.com/a", title=title, text=text, published_at=None, fetched_at=None)


def test_feed_list_is_curated_pairs_with_real_publisher_urls():
    assert len(PUBLISHER_FEEDS) >= 8
    for name, url in PUBLISHER_FEEDS:
        assert name and url.startswith("https://") and "news.google.com" not in url
    assert all(u in {x for _, x in PUBLISHER_FEEDS} for u in NATIONAL_FEEDS)


@pytest.mark.parametrize("fixture,feed", [("ht_pune", HT_PUNE), ("toi_pune", TOI_PUNE), ("ie_pune", IE_PUNE),
                                          ("punekar", PUNEKAR), ("et_realty", ET_REALTY), ("thehindu_re", HINDU_RE),
                                          ("news18_pune", NEWS18_PUNE)])
def test_real_captures_parse_with_publisher_url_name_and_date(fixture, feed):
    items = parse_feed(read(fixture), feed[0])
    assert len(items) >= 4
    for it in items:
        assert it.source == feed[0]
        assert it.url.startswith("https://") and "news.google.com" not in it.url
        assert it.title and it.published_at is not None and it.published_at.tzinfo is not None


def test_toi_iso_dates_and_empty_summaries_are_handled():
    items = parse_feed(read("toi_pune"), "Times of India")
    assert all(i.published_at.year == 2026 for i in items)  # ISO 8601 pubDate with +05:30 offset
    assert items[0].published_at.utcoffset().total_seconds() == 0  # normalised to UTC


def test_clean_summary_drops_wordpress_tail_and_empty_equal_to_title():
    t = "Pune: Mundhwa Could Become Business Hub"
    raw_text = "Pune, 17th September 2026: Mundhwa is emerging... The post " + t + " appeared first on Punekar News."
    assert clean_summary(raw_text, t) == "Pune, 17th September 2026: Mundhwa is emerging..."
    assert clean_summary("The post x appeared first on Y", t) == t
    assert clean_summary("", t) == t


def test_relevance_area_corridor_and_real_estate_words():
    assert is_relevant(raw("Kharadi office demand rises"))
    assert is_relevant(raw("Ring road", "pune ring road land acquisition"))
    assert is_relevant(raw("New home sales in Pune decline 6%"))
    assert not is_relevant(raw("School bus hits scooter in Ghorpadi"))
    assert not is_relevant(raw("Gold price today"))
    assert not is_relevant(raw("Fuel bill", "The plotting of votes"))  # whole words only


def test_national_feeds_need_a_pune_hint():
    mumbai = raw("Mumbai real estate: executive buys sea-facing apartment")
    assert is_relevant(mumbai) and not is_relevant(mumbai, national=True)
    assert is_relevant(raw("Pune flat prices rise"), national=True)
    assert is_relevant(raw("Wagholi project launched"), national=True)
    assert not is_relevant(raw("Budget speech"), national=True)


async def test_fetch_keeps_real_urls_and_filters_whole_city_feed():
    pages = {HT_PUNE[1]: read("ht_pune"), PUNEKAR[1]: read("punekar"), ET_REALTY[1]: read("et_realty"),
             PMRDA[1]: read("pmrda")}
    items = await PublishersSource().fetch(fake_get(pages))
    titles = [i.title for i in items]
    assert any("Hinjewadi-Shivajinagar Metro" in t for t in titles)  # HT Pune, corridor/metro
    assert any("sub-registrar office at PMC" in t for t in titles)  # ET Realty, national feed with Pune hint
    assert not any("Nashik" in t or "Panchkula" in t or "Gurugram" in t for t in titles)
    assert not any("Lulla Nagar" in t for t in titles)  # city news with no real-estate or area word
    assert all("news.google.com" not in i.url for i in items)
    assert {i.source for i in items} <= {"Hindustan Times", "Punekar News", "ET Realty", "PMRDA"}
    assert len({i.id for i in items}) == len(items)
    hj = next(i for i in items if "Hinjewadi-Shivajinagar" in i.title)
    assert hj.text.startswith("PMRDA has taken up") and hj.url.startswith("https://www.hindustantimes.com/")


async def test_prefilter_can_be_disabled_and_failing_feed_is_skipped():
    pages = {HT_PUNE[1]: read("ht_pune")}
    all_items = await PublishersSource([HT_PUNE, TOI_PUNE], prefilter=False).fetch(fake_get(pages))
    assert len(all_items) == 6
    none = await PublishersSource([TOI_PUNE]).fetch(fake_get({}))
    assert none == []
    garbage = await PublishersSource([HT_PUNE]).fetch(fake_get({HT_PUNE[1]: "<html>not a feed"}))
    assert garbage == []


async def test_duplicate_article_across_feeds_kept_once():
    pages = {PUNEKAR[1]: read("punekar"), PUBLISHER_FEEDS[4][1]: read("punekar")}
    items = await PublishersSource([PUNEKAR, PUBLISHER_FEEDS[4]], prefilter=False).fetch(fake_get(pages))
    assert len(items) == 5


def test_registry_knows_publishers():
    srcs = build_sources(["google_news", "publishers", "Publishers"])
    assert [s.name for s in srcs] == ["google_news", "publishers"]


def test_google_news_source_prefers_publisher_name_and_keeps_url():
    xml = ("<rss><channel><item><title>Kharadi metro plan - Hindustan Times</title>"
           "<link>https://news.google.com/rss/articles/CBMiabc</link><pubDate>Tue, 30 Sep 2026 10:00:00 GMT</pubDate>"
           "<source url=\"https://www.hindustantimes.com\">Hindustan Times</source></item></channel></rss>")
    (it,) = parse_google_feed(xml)
    assert it.source == "Hindustan Times" and it.title == "Kharadi metro plan"
    assert it.url == "https://news.google.com/rss/articles/CBMiabc"
