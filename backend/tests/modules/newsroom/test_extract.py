import json
from datetime import datetime, timezone
from pathlib import Path

from app.modules.newsroom.stages.extract import MAX_FACTS, extract
from app.modules.newsroom.types import RawItem

NOW = datetime(2026, 9, 30, tzinfo=timezone.utc)
PUB = datetime(2026, 9, 27, 6, tzinfo=timezone.utc)
DIR = Path(__file__).parent / "fixtures" / "articles"


class FakeLlm:
    def __init__(self, reply=None, boom=False):
        self.reply, self.boom, self.calls = reply, boom, []

    async def json(self, system, user):
        self.calls.append((system, user))
        if self.boom:
            raise RuntimeError("down")
        return self.reply

    async def text(self, system, user, timeout=None):
        return None


def metro() -> RawItem:
    d = json.loads((DIR / "metro_line3.json").read_text(encoding="utf-8"))
    return RawItem(id=d["id"], source="t", url=d["url"], title=d["title"], text=d["text"], published_at=PUB, fetched_at=NOW)


Q1 = "Pune Metro Line 3 between Hinjewadi and Shivajinagar is 78 per cent complete"
Q2 = "Officials said 18 of the 23 stations have their structures ready."
Q3 = "PMRDA has set a revised trial date of December 2026."


async def test_good_facts_kept_with_as_of():
    llm = FakeLlm({"facts": [{"text": "Metro Line 3 is 78 per cent complete", "quote": Q1},
                             {"text": "18 of 23 stations have structures ready", "quote": Q2}]})
    f = await extract(metro(), llm)
    assert [x.quote for x in f.facts] == [Q1, Q2]
    assert f.as_of == PUB
    sys_prompt = llm.calls[0][0].lower()
    assert "prediction" in sys_prompt and "opinion" in sys_prompt and "exactly as written" in sys_prompt


async def test_as_of_falls_back_to_fetched_at():
    it = metro()
    it = RawItem(**{**it.__dict__, "published_at": None})
    f = await extract(it, FakeLlm({"facts": [{"text": "78 per cent complete", "quote": Q1}]}))
    assert f.as_of == NOW


async def test_invented_quote_discarded():
    llm = FakeLlm({"facts": [{"text": "Line 3 will open in March", "quote": "The line will open to the public in March 2027."},
                             {"text": "78 per cent complete", "quote": Q1}]})
    f = await extract(metro(), llm)
    assert [x.quote for x in f.facts] == [Q1]


async def test_all_invented_returns_none():
    llm = FakeLlm({"facts": [{"text": "Fares will be Rs 30", "quote": "Fares will be capped at Rs 30 per trip."}]})
    assert await extract(metro(), llm) is None


async def test_numbers_that_differ_from_quote_discarded():
    llm = FakeLlm({"facts": [{"text": "Metro Line 3 is 87 per cent complete", "quote": Q1},
                             {"text": "19 of 23 stations are ready", "quote": Q2},
                             {"text": "Trials set for December 2026", "quote": Q3}]})
    f = await extract(metro(), llm)
    assert [x.quote for x in f.facts] == [Q3]


async def test_altered_quote_number_discarded():
    # quote looks real but a digit was changed, so it is not a substring
    llm = FakeLlm({"facts": [{"text": "88 per cent complete", "quote": Q1.replace("78", "88")}]})
    assert await extract(metro(), llm) is None


async def test_whitespace_normalised_quote_accepted():
    messy = "  Officials said 18 of  the 23\nstations have their structures ready.  "
    f = await extract(metro(), FakeLlm({"facts": [{"text": "18 of 23 stations ready", "quote": messy}]}))
    assert f.facts[0].quote == Q2


async def test_quote_from_title_accepted():
    title = "Pune Metro Line 3 Hinjewadi-Shivajinagar work 78 per cent complete"
    f = await extract(metro(), FakeLlm({"facts": [{"text": "Work on Line 3 is 78 per cent complete", "quote": title}]}))
    assert f and f.facts[0].quote == title


async def test_junk_responses_return_none():
    for reply in (None, {}, {"facts": "lots"}, {"facts": None}, ["x"], "text", {"facts": [1, "a", None]},
                  {"facts": [{"text": "x"}]}, {"facts": [{"text": 5, "quote": 6}]},
                  {"facts": [{"text": "t", "quote": ""}]}, {"facts": [{"text": "", "quote": Q1}]}):
        assert await extract(metro(), FakeLlm(reply)) is None, reply


async def test_llm_exception_returns_none():
    assert await extract(metro(), FakeLlm(boom=True)) is None


async def test_cap_and_dedupe():
    text = " ".join(f"Sentence number {i} says the fund is {i} crore." for i in range(10))
    it = RawItem(id="c", source="t", url="u", title="T", text=text, published_at=PUB, fetched_at=NOW)
    facts = [{"text": f"Fund is {i} crore", "quote": f"Sentence number {i} says the fund is {i} crore."} for i in range(10)]
    facts.insert(1, dict(facts[0]))
    f = await extract(it, FakeLlm({"facts": facts}))
    assert len(f.facts) == MAX_FACTS == 6
    assert len({x.quote for x in f.facts}) == 6


async def test_short_quote_rejected():
    assert await extract(metro(), FakeLlm({"facts": [{"text": "Pune", "quote": "Pune"}]})) is None


async def test_comma_number_formats_match():
    it = RawItem(id="r", source="t", url="u", title="T", text="The estimated cost of the package is Rs 1,450 crore.",
                 published_at=PUB, fetched_at=NOW)
    ok = await extract(it, FakeLlm({"facts": [{"text": "Cost is Rs 1450 crore", "quote": "The estimated cost of the package is Rs 1,450 crore."}]}))
    assert ok is not None
