from datetime import datetime, timedelta, timezone

import pytest

from app.modules.calendar import library, runner
from app.modules.calendar.config import CalendarConfig
from app.modules.calendar.store import Store
from app.modules.social.config import SocialConfig
from app.modules.social.publisher import PublishError, Result

from ..fakes import FakeDb

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
CFG = CalendarConfig(enabled=True)
DRY = SocialConfig(dry_run=True)
LIVE = SocialConfig(dry_run=False, page_id="P1", ig_id="IG1", media_base_url="https://media.test", page_token="EAAB" + "x" * 30)
TOKEN = LIVE.page_token


class FakePublisher:
    def __init__(self, fail=None):
        self.posts, self.fail = [], fail

    async def publish(self, post):
        self.posts.append(post)
        if self.fail:
            raise PublishError(self.fail)
        return Result(external_id=f"ext{len(self.posts)}", permalink=f"https://fb.test/{len(self.posts)}")


class Renders:
    def __init__(self):
        self.calls = []

    def __call__(self, entry, uploads, channel):
        self.calls.append((entry.slug, channel))


def make():
    store = Store(FakeDb(), clock=lambda: NOW)
    return store, FakePublisher(), Renders()


async def add(store, slug, channel, due):
    e = library.BY_SLUG[slug]
    return await store.add(slug, channel, e.ig_caption if channel == "instagram" else e.fb_caption,
                           f"calendar/ig/{slug}.jpg" if channel == "instagram" else f"calendar/{slug}.jpg", due)


async def run(store, pub, render, social=LIVE, now=NOW, cfg=CFG):
    return await runner.run_once(store, pub, social, cfg, now, uploads=None, render=render)


async def test_publishes_only_due_items():
    store, pub, render = make()
    due = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    future = await add(store, "cost-sheet-decoded", "facebook_page", NOW + timedelta(hours=5))
    ig_due = await add(store, "myth-rera-means-safe", "instagram", NOW - timedelta(minutes=5))
    counts = await run(store, pub, render)
    assert counts["published"] == 2
    assert (await store.get(due))["status"] == "published" and (await store.get(future))["status"] == "scheduled"
    assert (await store.get(ig_due))["external_id"].startswith("ext")
    fb, ig = pub.posts
    assert fb.channel == "facebook_page" and fb.image_urls == ["https://media.test/uploads/calendar/carpet-under-rera.jpg"]
    assert ig.channel == "instagram" and ig.image_urls == ["https://media.test/uploads/calendar/ig/myth-rera-means-safe.jpg"]
    assert "http" not in ig.text and ig.text == library.BY_SLUG["myth-rera-means-safe"].ig_caption
    assert sorted(render.calls) == [("carpet-under-rera", "facebook_page"), ("myth-rera-means-safe", "instagram")]


async def test_nothing_due_publishes_nothing_and_records_status():
    store, pub, render = make()
    await add(store, "carpet-under-rera", "facebook_page", NOW + timedelta(days=1))
    assert (await run(store, pub, render))["published"] == 0 and pub.posts == []
    st = await store.get_run()
    assert st["last_run_at"] == NOW and st["last_counts"]["published"] == 0


async def test_at_most_one_post_per_channel_per_run():
    store, pub, render = make()
    a = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=3))
    b = await add(store, "cost-sheet-decoded", "facebook_page", NOW - timedelta(hours=1))
    counts = await run(store, pub, render)
    assert counts["published"] == 1 and counts["waiting"] == 1 and len(pub.posts) == 1
    assert (await store.get(a))["status"] == "published" and (await store.get(b))["status"] == "scheduled"
    await run(store, pub, render)  # the next pass takes the other one
    assert (await store.get(b))["status"] == "published"


async def test_dry_run_marks_published_with_a_fake_id_and_no_network():
    store, pub, render = make()
    i = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    counts = await run(store, pub, render, social=DRY)
    doc = await store.get(i)
    assert counts["published"] == 1 and doc["status"] == "published" and doc["external_id"].startswith("dryrun_")
    assert pub.posts == [] and render.calls == []


async def test_failure_is_sanitised_and_retried_at_most_twice():
    store, pub, render = make()
    pub.fail = f"Graph error access_token={TOKEN} and {TOKEN} bad"
    i = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    now = NOW
    for attempt in (1, 2, 3):
        counts = await run(store, pub, render, now=now)
        doc = await store.get(i)
        assert doc["attempts"] == attempt and TOKEN not in doc["error"] and "redacted" in doc["error"]
        assert counts["failed" if attempt == 3 else "retry"] == 1
        assert doc["status"] == ("failed" if attempt == 3 else "scheduled")
        now += timedelta(minutes=11)
    assert len(pub.posts) == 3
    await run(store, pub, render, now=now + timedelta(hours=1))  # a failed row is never tried again
    assert len(pub.posts) == 3
    assert any("attempt 3 failed" in h["note"] for h in (await store.get(i))["history"])


async def test_retry_waits_before_trying_again():
    store, pub, render = make()
    pub.fail = "boom"
    await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    await run(store, pub, render)
    counts = await run(store, pub, render, now=NOW + timedelta(minutes=5))
    assert len(pub.posts) == 1 and counts["waiting"] == 1
    pub.fail = None
    counts = await run(store, pub, render, now=NOW + timedelta(minutes=11))
    assert counts["published"] == 1


async def test_a_failing_channel_does_not_block_the_other():
    store, _, render = make()

    class Half(FakePublisher):
        async def publish(self, post):
            if post.channel == "instagram":
                raise PublishError("ig down")
            return await super().publish(post)

    pub = Half()
    fb = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    ig = await add(store, "myth-rera-means-safe", "instagram", NOW - timedelta(hours=1))
    await run(store, pub, render)
    assert (await store.get(fb))["status"] == "published" and (await store.get(ig))["error"] == "ig down"


async def test_unconfigured_channel_is_a_recorded_failure_not_a_crash():
    store, pub, render = make()
    i = await add(store, "myth-rera-means-safe", "instagram", NOW - timedelta(hours=1))
    await run(store, pub, render, social=SocialConfig(dry_run=False, page_id="P1", page_token="EAAB" + "y" * 30, media_base_url="https://m.test"))
    doc = await store.get(i)
    assert doc["attempts"] == 1 and "not configured" in doc["error"] and pub.posts == []


async def test_render_error_is_recorded_not_raised():
    store, pub, _ = make()

    def boom(entry, uploads, channel):
        raise OSError("disk full")

    i = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    await run(store, pub, boom)
    assert (await store.get(i))["error"] == "disk full" and pub.posts == []


async def test_posts_far_overdue_are_skipped_not_burst_out():
    store, pub, render = make()
    old = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=60))
    fresh = await add(store, "cost-sheet-decoded", "facebook_page", NOW - timedelta(hours=1))
    counts = await run(store, pub, render)
    assert (await store.get(old))["status"] == "skipped" and counts["skipped"] == 1
    assert (await store.get(fresh))["status"] == "published"


async def test_skipped_items_are_never_published():
    store, pub, render = make()
    i = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    assert await store.skip(i)
    await run(store, pub, render)
    assert pub.posts == [] and (await store.get(i))["status"] == "skipped"


async def test_loop_is_idle_unless_enabled(monkeypatch):
    import asyncio

    monkeypatch.delenv("CALENDAR_ENABLED", raising=False)
    monkeypatch.setenv("CALENDAR_INTERVAL_SECONDS", "30")
    called = []
    monkeypatch.setattr(runner, "get_database", lambda: called.append(1))
    task = asyncio.create_task(runner.loop())
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert called == []


async def test_loop_survives_a_failing_cycle(monkeypatch):
    import asyncio

    monkeypatch.setenv("CALENDAR_ENABLED", "true")
    calls = []

    def boom():
        calls.append(1)
        raise RuntimeError("db down")

    real_sleep = asyncio.sleep

    async def quick_sleep(_):
        await real_sleep(0)

    monkeypatch.setattr(runner, "get_database", boom)
    monkeypatch.setattr(runner.asyncio, "sleep", quick_sleep)
    task = asyncio.create_task(runner.loop())
    for _ in range(20):
        await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(calls) >= 2
