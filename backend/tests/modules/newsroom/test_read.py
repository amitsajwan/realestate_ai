"""Article reader: recorded pages, robots.txt, redirects, thresholds, politeness. No network."""
import asyncio
from dataclasses import replace
from pathlib import Path

from app.modules.newsroom.config import NewsroomConfig
from app.modules.newsroom.pipeline import run_once
from app.modules.newsroom.stages.read import RobotsCache, main_text, polite_get, read
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import Fact, Facts

from ..fakes import FakeDb
from .helpers import NOW, FakeSource, good_stages, item

PAGES = Path(__file__).parent / "fixtures" / "pages"
URL = "https://news.test/story"


def page(name):
    return (PAGES / f"{name}.html").read_text(encoding="utf-8")


def short(url=URL, text="Kharadi bypass diversion from October 1."):
    return replace(item(1), url=url, text=text)


def fetcher(pages, robots="User-agent: *\nAllow: /\n"):
    calls = []

    async def get(url):
        calls.append(url)
        if url.endswith("/robots.txt"):
            if robots is None:
                raise RuntimeError("robots down")
            return robots
        return pages[url]
    get.calls = calls
    return get


async def test_clean_article_is_appended_without_comments_nav_or_boilerplate():
    it = short()
    out = await read(it, fetcher({URL: page("clean_article")}))
    assert out is not it and out.id == it.id and out.title == it.title
    assert out.text.startswith(it.text + "\n\n")
    assert "girder launching work" in out.text and "Rs 160 crore" in out.text
    for bad in ("terrible idea", "Comments", "Subscribe", "Cookie", "Trending", "All rights reserved", "Home", "dataLayer", "not content"):
        assert bad not in out.text


async def test_nav_heavy_page_takes_the_densest_paragraph_block():
    out = await read(short(), fetcher({URL: page("nav_heavy")}))
    assert "420 hectares" in out.text and "joint measurement" in out.text
    assert "Menu:" not in out.text and "Top: A" not in out.text and "Careers" not in out.text


async def test_cookie_banner_and_popups_are_stripped():
    out = await read(short(), fetcher({URL: page("cookie_banner")}))
    assert "3 acres" in out.text and "1,200 students" in out.text
    for bad in ("cookies", "newsletter", "Sign up", "Read more", "subscriber"):
        assert bad not in out.text


async def test_paywall_teaser_leaves_the_item_unchanged():
    it = short()
    assert await read(it, fetcher({URL: page("paywall_teaser")})) is it


async def test_og_description_is_the_fallback_when_there_is_no_body():
    out = await read(short(), fetcher({URL: page("og_only")}))
    assert "Trial runs on Pune Metro line 3" in out.text and "Short fallback" not in out.text


async def test_og_description_already_in_the_text_changes_nothing():
    it = short(text="Trial runs on Pune Metro line 3 between Hinjewadi and Shivajinagar will begin next month, the project company said, "
                    "with commercial operations planned after safety certification.")
    assert await read(it, fetcher({URL: page("og_only")})) is it


def test_main_text_is_capped_and_ends_on_a_sentence():
    html = "<article>" + "".join(f"<p>Sentence number {i} about the Kharadi bypass works. It goes on for a while.</p>" for i in range(400)) + "</article>"
    t = main_text(html)
    assert len(t) <= 6000 and t.endswith(".")


def test_unclosed_and_broken_markup_does_not_raise():
    assert main_text("<article><p>Open paragraph<div><p>x</article></b></p>") != "\x00"


# ---- robots.txt ----
async def test_robots_disallow_blocks_the_page_fetch():
    get = fetcher({URL: page("clean_article")}, robots="User-agent: *\nDisallow: /\n")
    it = short()
    assert await read(it, get) is it
    assert URL not in get.calls


async def test_robots_rule_naming_our_agent_applies_and_path_rules_are_honoured():
    robots = "User-agent: AvasetuNewsroom\nDisallow: /private/\n\nUser-agent: *\nDisallow:\n"
    get = fetcher({URL: page("clean_article"), "https://news.test/private/a": page("clean_article")}, robots=robots)
    assert await read(short(), get) is not None and "girder" in (await read(short(), get)).text
    blocked = short(url="https://news.test/private/a")
    assert await read(blocked, get) is blocked


async def test_robots_fetch_error_fails_closed():
    get = fetcher({URL: page("clean_article")}, robots=None)
    it = short()
    assert await read(it, get) is it and URL not in get.calls


async def test_missing_robots_txt_404_allows():
    class NotFound(Exception):
        response = type("R", (), {"status_code": 404})()

    pages = {URL: page("clean_article")}

    async def get(url):
        if url.endswith("/robots.txt"):
            raise NotFound()
        return pages[url]
    assert "girder" in (await read(short(), get)).text


async def test_robots_is_fetched_once_per_host_and_expires():
    now = [0.0]
    cache = RobotsCache(ttl_s=100, clock=lambda: now[0])
    get = fetcher({URL: page("clean_article")})
    await read(short(), get, cache)
    await read(short(), get, cache)
    assert sum(u.endswith("/robots.txt") for u in get.calls) == 1
    now[0] = 500
    await read(short(), get, cache)
    assert sum(u.endswith("/robots.txt") for u in get.calls) == 2


# ---- skips and thresholds ----
async def test_google_news_redirect_is_skipped_without_any_request():
    get = fetcher({})
    it = short(url="https://news.google.com/rss/articles/CBMi123?oc=5")
    assert await read(it, get) is it and get.calls == []


async def test_item_with_enough_text_is_not_fetched():
    get = fetcher({URL: page("clean_article")})
    long_item = short(text="x" * 300)
    assert await read(long_item, get) is long_item and get.calls == []
    almost = short(text="x" * 299)
    assert "girder" in (await read(almost, get)).text


async def test_fetch_errors_and_non_http_urls_leave_the_item_alone():
    it = short()
    assert await read(it, fetcher({})) is it  # KeyError from the page fetch
    ftp = short(url="ftp://news.test/x")
    assert await read(ftp, fetcher({})) is ftp


# ---- politeness ----
async def test_polite_get_spaces_requests_to_the_same_host_only():
    now, sleeps = [0.0], []

    async def sleep(s):
        sleeps.append(s)
        now[0] += s

    async def get(url):
        return "ok"
    pg = polite_get(get, 2.0, clock=lambda: now[0], sleep=sleep)
    await pg("https://a.test/1")
    assert sleeps == []
    now[0] += 0.5
    await pg("https://a.test/2")
    assert sleeps == [1.5]
    await pg("https://b.test/1")  # another host: no wait
    assert sleeps == [1.5]
    now[0] += 5
    await pg("https://a.test/3")  # gap already elapsed
    assert sleeps == [1.5]


async def test_polite_get_serialises_concurrent_requests_to_one_host():
    now, sleeps = [0.0], []

    async def sleep(s):
        sleeps.append(s)
        now[0] += s

    async def get(url):
        await asyncio.sleep(0)
        return url
    pg = polite_get(get, 1.0, clock=lambda: now[0], sleep=sleep)
    assert await asyncio.gather(pg("https://a.test/1"), pg("https://a.test/2"), pg("https://a.test/3")) == \
        ["https://a.test/1", "https://a.test/2", "https://a.test/3"]
    assert sleeps == [1.0, 1.0]


# ---- pipeline wiring ----
async def _run(stages, text="Kharadi bypass diversion."):
    store = Store(FakeDb())
    it = replace(item(1), url=URL, text=text)
    seen = []
    inner = stages["extract"]

    async def extract(raw, llm):
        seen.append(raw.text)
        return await inner(raw, llm)
    stages["extract"] = extract
    counts = await run_once(store, [FakeSource([it])], stages, None, object(), NOW, NewsroomConfig())
    return store, seen, counts


async def test_pipeline_enriches_before_extract_and_persists_the_text():
    stages = good_stages()
    get = fetcher({URL: page("clean_article")})
    stages["get"] = get
    stages["read"] = lambda raw, g: read(raw, g)
    store, seen, _ = await _run(stages)
    assert "girder launching work" in seen[0]
    doc = await store.get("i1")
    assert "girder launching work" in doc["raw"]["text"] and doc["raw"]["title"] == item(1).title and doc["status"] == "pending_review"


async def test_pipeline_without_read_stage_is_unchanged():
    stages = good_stages()
    stages["get"] = fetcher({URL: page("clean_article")})
    store, seen, _ = await _run(stages)
    assert seen == ["Kharadi bypass diversion."] and stages["get"].calls == []


async def test_a_crashing_reader_never_blocks_extract():
    stages = good_stages()
    stages["get"] = fetcher({})

    async def boom(raw, g):
        raise RuntimeError("reader exploded")
    stages["read"] = boom
    store, seen, counts = await _run(stages)
    assert seen == ["Kharadi bypass diversion."] and (await store.get("i1"))["status"] == "pending_review"


def test_default_stages_registers_read_only_when_enabled(monkeypatch):
    from app.modules.newsroom.pipeline import default_stages
    monkeypatch.delenv("NEWSROOM_READ_ARTICLES", raising=False)
    assert "read" not in default_stages()
    monkeypatch.setenv("NEWSROOM_READ_ARTICLES", "true")
    assert "read" in default_stages()
