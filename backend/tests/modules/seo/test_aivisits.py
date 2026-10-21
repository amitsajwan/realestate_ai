"""AI search visits: fetchers that read our pages for AI answers, and people who come from AI answers (app/modules/seo/aivisits.py)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.seo import aivisits

from ..fakes import FakeDb

NOW = datetime(2026, 10, 21, 9, 0, tzinfo=timezone.utc)
CHATGPT_USER = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
OAI_SEARCH = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot"
GPTBOT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.1; +https://openai.com/gptbot"
CHROME = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36"


@pytest.mark.parametrize("ua,ref,utm,want", [
    (CHATGPT_USER, None, None, ("answer", "ChatGPT")),
    (OAI_SEARCH, None, None, ("search", "ChatGPT search")),
    (GPTBOT, None, None, ("training", "OpenAI training")),
    ("Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)", None, None, ("search", "Bing")),
    ("Mozilla/5.0 (compatible; PerplexityBot/1.0)", None, None, ("search", "Perplexity")),
    ("Mozilla/5.0 (compatible; Perplexity-User/1.0)", None, None, ("answer", "Perplexity")),
    (CHROME, None, "chatgpt.com", ("referral", "ChatGPT")),
    (CHROME, "https://www.perplexity.ai/search/flats-in-lohegaon", None, ("referral", "Perplexity")),
    (CHROME, "https://copilot.microsoft.com/", None, ("referral", "Copilot")),
    (CHROME, "https://gemini.google.com/app", None, ("referral", "Gemini")),
])
def test_classify(ua, ref, utm, want):
    hit = aivisits.classify(ua, ref, utm)
    assert (hit["group"], hit["agent"]) == want


@pytest.mark.parametrize("ua,ref,utm", [(CHROME, "https://www.google.com/", None), (CHROME, None, None), (CHROME, None, "instagram"),
                                        (CHROME, "https://notchatgpt.com/", None)])
def test_ordinary_visitors_are_not_counted(ua, ref, utm):
    assert aivisits.classify(ua, ref, utm) is None


async def test_record_and_summary():
    db = FakeDb()
    for _ in range(3):
        await aivisits.record(db, CHATGPT_USER, None, "/projects/area/lohegaon/2-bhk", None, NOW)
    await aivisits.record(db, CHROME, None, "/projects/sky-one?utm_source=chatgpt.com", "chatgpt.com", NOW)
    await aivisits.record(db, OAI_SEARCH, None, "/projects/sky-one", None, NOW - timedelta(days=10))
    await aivisits.record(db, CHROME, "https://www.google.com/", "/projects/sky-one", None, NOW)       # not ours to count
    assert await aivisits.record(db, CHATGPT_USER, None, "/x<script>", None, NOW) is None             # not a path

    s = await aivisits.summary(db, NOW)
    by = {(a["group"], a["agent"]): a for a in s["agents"]}
    assert by[("answer", "ChatGPT")]["week"] == 3 and by[("answer", "ChatGPT")]["kinds"] == {"area list": 3}
    assert by[("search", "ChatGPT search")] == {"group": "search", "agent": "ChatGPT search", "week": 0, "total": 1, "kinds": {"project": 1}}
    assert s["answer_pages"] == [{"path": "/projects/area/lohegaon/2-bhk", "count": 3}]
    assert s["referral_pages"] == [{"path": "/projects/sky-one", "count": 1}]
    assert [a["group"] for a in s["agents"]] == ["answer", "referral", "search"]
    assert aivisits.week_line(s) == ("AI search, 7 days: 3 pages read for AI answers, 1 visits from AI answers, "
                                     "0 search-crawler reads.")


async def test_paths_with_dots_are_kept_as_written():
    db = FakeDb()
    await aivisits.record(db, CHATGPT_USER, None, "/llms.txt", None, NOW)
    assert (await aivisits.summary(db, NOW))["answer_pages"] == [{"path": "/llms.txt", "count": 1}]
