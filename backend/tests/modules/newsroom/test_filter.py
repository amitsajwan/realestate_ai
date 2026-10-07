import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.modules.newsroom.stages.filter import assess, same_story
from app.modules.newsroom.types import RawItem

NOW = datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc)
DIR = Path(__file__).parent / "fixtures" / "articles"


def load(slug: str) -> tuple:
    d = json.loads((DIR / f"{slug}.json").read_text(encoding="utf-8"))
    pub = datetime.fromisoformat(d["published_at"]) if d["published_at"] else None
    return RawItem(id=d["id"], source=d["source"], url=d["url"], title=d["title"], text=d["text"],
                   published_at=pub, fetched_at=NOW), d["expect"]


SLUGS = sorted(p.stem for p in DIR.glob("*.json"))


def item(**kw) -> RawItem:
    base = dict(id="x", source="t", url="https://e.test/x", title="t", text="", published_at=NOW, fetched_at=NOW)
    base.update(kw)
    return RawItem(**base)


def test_enough_fixtures():
    assert len(SLUGS) >= 10


@pytest.mark.parametrize("slug", SLUGS)
def test_fixture_expectations(slug):
    it, exp = load(slug)
    r = assess(it, NOW)
    assert r.keep is exp["keep"], r.reason
    if exp["keep"]:
        assert r.pillar == exp["pillar"]
        assert set(exp["areas"]) <= set(r.areas)
    else:
        assert exp["reason"] in r.reason
        assert r.pillar is None


def test_kharadi_word_boundary():
    assert assess(item(title="Kharadi bypass work", text="Pune roads"), NOW).areas == ["kharadi"]
    assert not assess(item(title="Kharadigaon tales", text="about Pune"), NOW).keep
    assert not assess(item(title="Hinjewadi flyover", text="superwagholiX is a name"), NOW).keep


def test_upper_kharadi_also_counts_kharadi():
    r = assess(item(title="Upper Kharadi school", text="a new school opens"), NOW)
    assert r.keep and set(r.areas) == {"kharadi", "upper_kharadi"}


def test_corridor_needs_pune_hint():
    assert not assess(item(title="Nagar road closed", text="a road in another city"), NOW).keep
    assert assess(item(title="Nagar Road work", text="Pune civic body starts repairs"), NOW).keep


def test_missing_publish_date_uses_fetched_at():
    old = datetime(2026, 7, 1, tzinfo=timezone.utc)
    stale = item(title="Kharadi metro", text="news", published_at=None, fetched_at=old)
    assert "stale" in assess(stale, NOW).reason
    fresh = item(title="Kharadi metro", text="news", published_at=None, fetched_at=NOW)
    assert assess(fresh, NOW).keep


def test_naive_datetimes_do_not_crash():
    it = item(title="Kharadi metro", text="news", published_at=datetime(2026, 9, 29))
    assert assess(it, NOW.replace(tzinfo=None)).keep


def test_age_boundary():
    assert assess(item(title="Kharadi metro", published_at=datetime(2026, 9, 16, 9, tzinfo=timezone.utc)), NOW).keep
    assert not assess(item(title="Kharadi metro", published_at=datetime(2026, 9, 16, 8, tzinfo=timezone.utc)), NOW).keep


def test_crime_needs_to_be_the_story():
    # one passing crime word in a real infrastructure story is fine
    it = item(title="Kharadi flyover opens", text="Police said the flyover, where a man was killed last year, is safer now.")
    assert assess(it, NOW).keep


def test_same_story():
    a = "Pune Metro Line 3 Hinjewadi-Shivajinagar work 78 per cent complete"
    b = "Pune Metro Line 3: 78% work done, says PMRDA - Times of India"
    assert same_story(a, a.upper())
    assert same_story("PMRDA invites bids for Pune ring road package - Hindustan Times",
                      "PMRDA invites bids for Pune ring road package | Pune Mirror")
    assert not same_story(a, "MahaRERA registers 14 new projects in Kharadi in September")
    assert not same_story("", "anything")
    assert same_story(a, b)


def test_same_story_on_fixture_duplicates_is_honest():
    # the two metro fixtures are worded differently; if they do not match the pipeline still dedupes by id/url
    a, _ = load("metro_line3")
    b, _ = load("dup_metro")
    assert same_story(a.title, b.title)
    assert not same_story(a.title, load("ring_road")[0].title)
