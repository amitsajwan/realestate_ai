"""Draft stage: facts in, safe plain draft out. Fake Llm, no network."""
from datetime import datetime, timezone

import pytest

from app.modules.newsroom import policy
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.stages.draft import draft, template_draft
from app.modules.newsroom.types import Fact, Facts, RawItem, Relevance

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 9, 20, tzinfo=timezone.utc)
PUB = datetime(2026, 9, 12, tzinfo=timezone.utc)
URL = "https://example.com/ring-road"
SECRET = "SECRET-RAW-ARTICLE-SENTENCE about unrelated things"
ITEM = RawItem("r1", "pune_mirror", URL, "Ring road land survey begins",
               "PMRDA said on 12 September that the survey of land for the Pune ring road near Wagholi has begun. "
               "The road will be 65 km long. " + SECRET, PUB, PUB)
FACTS = Facts([Fact("The land survey for the Pune ring road near Wagholi has begun.", "the survey of land for the Pune ring road near Wagholi has begun"),
               Fact("The planned road is 65 km long.", "The road will be 65 km long.")], PUB)
REL = Relevance(True, "infrastructure", ["wagholi"])
GOOD = {"title": "Ring road survey starts near Wagholi", "what": "PMRDA has started surveying land for the Pune ring road near Wagholi. The planned road is 65 km long.",
        "why": "If you are looking at homes in Wagholi, this may become part of your daily commute picture in time.",
        "check": "Look at the official notice for the latest status.", "question": "Would a ring road change where you look for a home?"}


class FakeLlm:
    def __init__(self, reply=None, boom=False):
        self.reply, self.boom, self.calls = reply, boom, []

    async def json(self, system, user):
        self.calls.append((system, user))
        if self.boom:
            raise RuntimeError("down")
        return self.reply

    async def text(self, system, user, timeout=None):
        raise AssertionError("draft must use json()")


def ok(d):
    r = check(d, FACTS, ITEM, now=NOW)
    assert r.ok, (r.problems, d.text)


async def test_post_shape_and_passes_check():
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm(GOOD))
    assert d.format == "post" and d.link == URL and d.source_names == ["Pune Mirror"]
    lines = d.text.split("\n\n")
    assert lines[-1] == "#Pune #Avasetu #Wagholi"
    assert lines[-2].endswith("?")
    assert "Our view:" in d.text and "Source: Pune Mirror, as of 12 Sep 2026" in d.text and URL in d.text
    assert len(d.text) <= policy.POST_MAX_CHARS
    ok(d)


async def test_llm_sees_facts_only_never_the_raw_article():
    llm = FakeLlm(GOOD)
    await draft(ITEM, FACTS, REL, "post", llm)
    system, user = llm.calls[0]
    assert "land survey for the Pune ring road" in user and "65 km" in user
    assert "SECRET" not in user and ITEM.text not in user and URL not in user
    assert "no phone numbers" in system and "no predictions" in system


async def test_article_shape():
    d = await draft(ITEM, FACTS, REL, "article", FakeLlm(GOOD))
    assert d.format == "article" and d.title == GOOD["title"]
    assert "Why it may matter:" in d.text and "This is our view" in d.text and "What to check:" in d.text
    assert "as of 12 Sep 2026" in d.text and d.text.endswith(policy.DISCLAIMER)
    ok(d)


async def test_llm_returns_none_falls_back_to_the_plain_template():
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm(None))
    assert d is not None and d.format == "post"
    ok(d)


async def test_llm_raises_falls_back_to_the_plain_template():
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm(boom=True))
    assert d is not None
    ok(d)


@pytest.mark.parametrize("reply", [{}, {"what": "x"}, {"why": "y"}, ["not", "a", "dict"]])
async def test_unusable_llm_reply_falls_back_to_the_plain_template(reply):
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm(reply))
    assert d is not None
    ok(d)


async def test_no_facts_gives_none():
    assert await draft(ITEM, Facts([], PUB), REL, "post", FakeLlm(GOOD)) is None


async def test_missing_question_is_replaced_so_post_still_asks():
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm({**GOOD, "question": "Tell us what you think."}))
    assert "Does this change how you look at homes in Wagholi?" in d.text
    ok(d)


async def test_llm_urls_are_stripped_so_the_link_is_ours():
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm({**GOOD, "what": GOOD["what"] + " http://evil.example/x"}))
    assert "evil.example" not in d.text


async def test_too_long_post_drops_the_check_line_first():
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm({**GOOD, "check": "Verify things. " * 60}))
    assert len(d.text) <= policy.POST_MAX_CHARS and "What to check" not in d.text


async def test_template_fallback_when_no_llm():
    d = await draft(ITEM, FACTS, REL, "post", None)
    assert d is not None and d.text.split("\n\n")[-1].startswith("#Pune")
    assert "land survey" in d.text and "?" in d.text
    ok(d)


async def test_template_fallback_article_passes_check():
    d = template_draft(ITEM, FACTS, REL, "article")
    assert d.format == "article" and d.title
    ok(d)


async def test_template_with_two_areas_and_no_areas():
    d = template_draft(ITEM, FACTS, Relevance(True, "infrastructure", ["kharadi", "upper_kharadi"]), "post")
    assert "#Kharadi #UpperKharadi" in d.text and "Kharadi or Upper Kharadi" in d.text
    assert "Pune?" in template_draft(ITEM, FACTS, Relevance(True, "infrastructure", []), "post").text


async def test_template_without_facts_is_none():
    assert template_draft(ITEM, Facts([], PUB), REL) is None


async def test_invented_claim_from_llm_is_caught_by_check():
    d = await draft(ITEM, FACTS, REL, "post", FakeLlm({**GOOD, "what": "The Pune ring road near Wagholi will cost 9,000 crore."}))
    assert not check(d, FACTS, ITEM, now=NOW).ok
