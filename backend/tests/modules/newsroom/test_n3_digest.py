"""The weekly digest builder: which stories, how many, when, once a week, and that it passes the same check as a story."""
from datetime import datetime, timedelta, timezone

from app.modules.newsroom import captions, codec, digest, runner
from app.modules.newsroom.samples import AS_OF, SAMPLES, make_doc
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import CheckResult

from ..fakes import FakeDb

SUNDAY_EVENING = datetime(2026, 10, 4, 12, 30, tzinfo=timezone.utc)  # 18:00 IST


def published(docs, status="published"):
    return [{**d, "status": status} for d in docs]


def ok_checker(d, f, r):
    return CheckResult(ok=True)


async def stored(docs, status="published", at=AS_OF):
    store = Store(FakeDb())
    for i, d in enumerate(docs):
        await store.items.insert_one({**d, "status": status, "updated_at": at, "published_at": at, "created_at": at + timedelta(seconds=i)})
    return store


def test_due_only_on_sunday_from_18_ist():
    assert digest.is_due(SUNDAY_EVENING) and digest.is_due(SUNDAY_EVENING + timedelta(hours=5))
    assert not digest.is_due(SUNDAY_EVENING - timedelta(minutes=1))
    assert not digest.is_due(SUNDAY_EVENING - timedelta(days=1)) and not digest.is_due(SUNDAY_EVENING + timedelta(hours=11))  # Saturday, Monday 00:00 IST+


def test_week_id_is_stable_within_a_week_and_changes_across_weeks():
    assert digest.week_id(SUNDAY_EVENING) == digest.week_id(SUNDAY_EVENING - timedelta(days=5)) != digest.week_id(SUNDAY_EVENING + timedelta(days=7))


def test_needs_at_least_two_stories_and_takes_at_most_five():
    now = SUNDAY_EVENING
    assert digest.compose(published(SAMPLES[:1]), now) is None
    assert digest.compose([], now) is None
    two = digest.compose(published(SAMPLES[:2]), now)
    assert two and len(two["digest"]["items"]) == 2
    many = digest.compose(published(SAMPLES), now)
    assert 2 <= len(many["digest"]["items"]) <= 5


def test_only_approved_scheduled_or_published_recent_stories_count():
    now = SUNDAY_EVENING
    docs = [{**SAMPLES[0], "status": "approved", "_id": "a"}, {**SAMPLES[1], "status": "scheduled", "_id": "b"},
            {**SAMPLES[2], "status": "pending_review", "_id": "c"}, {**SAMPLES[3], "status": "rejected", "_id": "d"},
            {**SAMPLES[4], "status": "dropped", "_id": "e"}, {**SAMPLES[5], "status": "published", "_id": "old",
                                                              "published_at": now - timedelta(days=9), "updated_at": now - timedelta(days=9)}]
    got = digest.compose(docs, now)
    assert [i["id"] for i in got["digest"]["items"]] == ["a", "b"]


def test_at_most_two_per_pillar_and_most_important_pillar_first():
    infra = [{**make_doc(f"i{n}", f"Road work number {n} starts near Kharadi", [f"Road work {n} starts."], "infrastructure", ["kharadi"], "PMC"), "status": "published"}
             for n in range(4)]
    rules = {**SAMPLES[4], "status": "published"}
    got = digest.compose(infra + [rules], SUNDAY_EVENING)["digest"]["items"]
    pillars = [i["pillar"] for i in got]
    assert pillars.count("infrastructure") == 2 and pillars == ["infrastructure", "infrastructure", "rules_money"]


def test_the_digest_is_a_pending_review_item_with_title_stories_tip_and_as_of():
    doc = digest.compose(published(SAMPLES), SUNDAY_EVENING)
    assert doc["status"] == "pending_review" and doc["_id"] == digest.week_id(SUNDAY_EVENING)
    d = doc["draft"]
    assert d["format"] == "digest" and d["title"] == "Kharadi and Wagholi this week" and "Buyer tip:" in d["text"] and "As of 4 Oct 2026." in d["text"]
    assert doc["digest"]["tip"] in d["text"] and doc["relevance"]["areas"] == ["kharadi", "wagholi"]
    assert all(s["source"] for s in doc["digest"]["items"]) and d["source_names"]


def test_tip_is_evergreen_without_figures_names_or_predictions():
    import re
    for t in digest.TIPS:
        assert not re.search(r"\d|₹|will |guarantee|price", t) and len(t.split()) <= 26


async def test_build_creates_one_checked_pending_item_per_week_with_cards():
    store = await stored(SAMPLES)
    made = []
    doc = await digest.build(store, SUNDAY_EVENING, check, render=lambda d: made.append(d["_id"]) or {"fb": "news/x-fb.jpg", "ig": ["news/x-ig-1.jpg"]})
    assert doc and (await store.get(doc["_id"]))["status"] == "pending_review" and doc["check"]["ok"] is True and made == [doc["_id"]]
    assert (await store.get(doc["_id"]))["card"]["fb"] == "news/x-fb.jpg"
    assert await digest.build(store, SUNDAY_EVENING + timedelta(hours=2), check) is None  # same week: no second digest
    assert len([d for d in store.items.docs if d["_id"].startswith("digest-")]) == 1


async def test_build_passes_the_real_check_and_the_final_captions_pass_it_too():
    doc = digest.compose(published(SAMPLES), SUNDAY_EVENING)
    res = check(codec.draft(doc), codec.facts(doc), codec.raw_item(doc), now=SUNDAY_EVENING)
    assert res.ok, res.problems
    assert await captions.verify(doc, lambda d, f, r: check(d, f, r, now=SUNDAY_EVENING)) == {"facebook": [], "instagram": []}


async def test_build_does_nothing_with_one_story_or_a_failing_check():
    assert await digest.build(await stored(SAMPLES[:1]), SUNDAY_EVENING, ok_checker) is None
    store = await stored(SAMPLES)
    assert await digest.build(store, SUNDAY_EVENING, lambda d, f, r: CheckResult(ok=False, problems=["x"])) is None
    assert not [d for d in store.items.docs if d["_id"].startswith("digest-")]


async def test_a_card_failure_still_leaves_the_digest_for_review():
    store = await stored(SAMPLES)

    def broken(doc):
        raise RuntimeError("no fonts")
    doc = await digest.build(store, SUNDAY_EVENING, ok_checker, render=broken)
    assert doc and "card" not in doc and (await store.get(doc["_id"]))["status"] == "pending_review"


async def test_runner_builds_only_on_sunday_evening():
    store = await stored(SAMPLES)
    stages = {"check": ok_checker}
    counts = {}
    await runner._weekly_digest(store, stages, SUNDAY_EVENING - timedelta(days=1), counts)
    assert counts == {} and not [d for d in store.items.docs if d["_id"].startswith("digest-")]
    await runner._weekly_digest(store, stages, SUNDAY_EVENING, counts)
    assert counts["digest"] == 1 and [d for d in store.items.docs if d["_id"].startswith("digest-")]
    again = {}
    await runner._weekly_digest(store, stages, SUNDAY_EVENING + timedelta(hours=3), again)
    assert again["digest"] == 0
