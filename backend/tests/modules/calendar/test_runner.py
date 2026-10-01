import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.modules.calendar import library, runner
from app.modules.calendar.config import CalendarConfig
from app.modules.calendar.store import Store
from app.modules.social.config import SocialConfig
from app.modules.social.publisher import PublishError, Result

from ..fakes import FakeDb

UPLOADS = Path(tempfile.mkdtemp(prefix="cal-uploads-"))
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
    """Stub reel composer: records the rows it was asked to render and returns a path."""

    def __init__(self):
        self.calls = []

    def __call__(self, doc, uploads):
        self.calls.append(doc["slug"])
        rel = f"calendar/reels/{doc['slug']}.mp4"
        (UPLOADS / rel).parent.mkdir(parents=True, exist_ok=True)
        (UPLOADS / rel).write_bytes(b"mp4")
        return rel


def make():
    store = Store(FakeDb(), clock=lambda: NOW)
    return store, FakePublisher(), Renders()


async def add(store, slug, channel, due, status="approved", **kw):
    e = library.BY_SLUG[slug]
    rel = f"calendar/ig/{slug}.jpg" if channel == "instagram" else f"calendar/{slug}.jpg"
    (UPLOADS / rel).parent.mkdir(parents=True, exist_ok=True)
    (UPLOADS / rel).write_bytes(b"jpg")
    return await store.add(slug, channel, e.ig_caption if channel == "instagram" else e.fb_caption, rel, due, status=status, **kw)


async def run(store, pub, render, social=LIVE, now=NOW, cfg=CFG, **kw):
    return await runner.run_once(store, pub, social, cfg, now, uploads=UPLOADS, render_reel=render, **kw)


async def test_publishes_only_due_items():
    store, pub, render = make()
    due = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1))
    future = await add(store, "cost-sheet-decoded", "facebook_page", NOW + timedelta(hours=5))
    ig_due = await add(store, "myth-rera-means-safe", "instagram", NOW - timedelta(minutes=5))
    counts = await run(store, pub, render)
    assert counts["published"] == 2
    assert (await store.get(due))["status"] == "published" and (await store.get(future))["status"] == "approved"
    assert (await store.get(ig_due))["external_id"].startswith("ext")
    fb, ig = pub.posts
    assert fb.channel == "facebook_page" and fb.image_urls == ["https://media.test/uploads/calendar/carpet-under-rera.jpg"]
    assert ig.channel == "instagram" and ig.image_urls == ["https://media.test/uploads/calendar/ig/myth-rera-means-safe.jpg"]
    assert "http" not in ig.text and ig.text == library.BY_SLUG["myth-rera-means-safe"].ig_caption


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
    assert (await store.get(a))["status"] == "published" and (await store.get(b))["status"] == "approved"
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
        assert doc["status"] == ("failed" if attempt == 3 else "approved")
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


# ---- approval gate, kinds, carousels, reels -------------------------------------------------------------------------------------------
async def test_planned_items_are_never_published_even_when_due():
    store, pub, render = make()
    i = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1), status="planned")
    j = await add(store, "myth-rera-means-safe", "instagram", NOW - timedelta(hours=1), status="planned")
    for social in (LIVE, DRY):
        counts = await run(store, pub, render, social=social)
        assert counts["published"] == 0
    assert pub.posts == [] and (await store.get(i))["status"] == "planned" and (await store.get(j))["status"] == "planned"


async def test_approving_makes_it_publishable_and_legacy_scheduled_rows_still_publish():
    store, pub, render = make()
    i = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(hours=1), status="planned")
    k = await add(store, "cost-sheet-decoded", "instagram", NOW - timedelta(hours=1), status="scheduled")
    assert await store.approve(i) and not await store.approve(i)  # only planned rows can be approved, once
    counts = await run(store, pub, render)
    assert counts["published"] == 2 and {(await store.get(x))["status"] for x in (i, k)} == {"published"}


async def test_skipped_and_failed_rows_cannot_be_approved():
    store, pub, render = make()
    i = await add(store, "carpet-under-rera", "facebook_page", NOW + timedelta(hours=1), status="planned")
    assert await store.skip(i) and not await store.approve(i)


async def test_instagram_carousel_goes_as_multi_image_and_facebook_gets_the_first_image():
    store, pub, render = make()
    for rel in ("calendar/w1/a-1.jpg", "calendar/w1/a-2.jpg", "calendar/w1/a-3.jpg"):
        (UPLOADS / rel).parent.mkdir(parents=True, exist_ok=True)
        (UPLOADS / rel).write_bytes(b"x")
    imgs = ["calendar/w1/a-1.jpg", "calendar/w1/a-2.jpg", "calendar/w1/a-3.jpg"]
    for ch in ("instagram", "facebook_page"):
        await store.add("carousel-test", ch, "caption", imgs[0], NOW - timedelta(hours=1), images=imgs, status="approved")
    await run(store, pub, render)
    by = {p.channel: p for p in pub.posts}
    assert by["instagram"].image_urls == [f"https://media.test/uploads/{p}" for p in imgs]
    assert by["facebook_page"].image_urls == [f"https://media.test/uploads/{imgs[0]}"]


async def test_missing_image_file_is_a_recorded_failure():
    store, pub, render = make()
    i = await store.add("ghost", "instagram", "c", "calendar/none.jpg", NOW - timedelta(hours=1), status="approved")
    await run(store, pub, render)
    assert "missing" in (await store.get(i))["error"] and pub.posts == []


async def test_showcase_rows_go_through_the_showcase_publisher():
    store, pub, render = make()
    i = await store.add("kharadi-2bhk-ready", "instagram", "sample caption", "showcase/kharadi-2bhk-ready/1.jpg", NOW - timedelta(hours=1),
                        kind="showcase", status="approved")
    seen = []

    async def fake_showcase(doc, social, publisher, uploads):
        seen.append((doc["slug"], doc["channel"], doc["caption"]))
        return Result("show1", "https://ig.test/p/1")

    await run(store, pub, render, publish_showcase=fake_showcase)
    assert seen == [("kharadi-2bhk-ready", "instagram", "sample caption")] and (await store.get(i))["external_id"] == "show1" and pub.posts == []


async def reel_row(store, channel, due, status="approved", video=None, key="reel-w1-tip"):
    return await store.add(key, channel, "reel caption", "", due, kind="reel", status=status, video=video,
                           creative={"template": "tip", "reel_key": key, "ref": "red-flags-in-ads"}, week=1)


async def test_reel_is_prerendered_two_hours_before_and_shared_by_both_channels():
    store, pub, render = make()
    ig = await reel_row(store, "instagram", NOW + timedelta(hours=1, minutes=30))
    fb = await reel_row(store, "facebook_page", NOW + timedelta(hours=1))
    far = await reel_row(store, "instagram", NOW + timedelta(hours=5), key="reel-w2-tour")
    planned = await reel_row(store, "instagram", NOW + timedelta(hours=1), status="planned", key="reel-w3-pitch")
    n = await runner.prerender_reels(store, NOW, UPLOADS, render)
    assert n == 1 and render.calls == ["reel-w1-tip"]  # one render for the two rows of one reel
    assert (await store.get(ig))["video"] == (await store.get(fb))["video"] == "calendar/reels/reel-w1-tip.mp4"
    assert not (await store.get(far)).get("video") and not (await store.get(planned)).get("video")
    assert await runner.prerender_reels(store, NOW, UPLOADS, render) == 0  # nothing left to do


async def test_reel_render_failure_is_logged_and_does_not_raise():
    store, _, _ = make()
    await reel_row(store, "instagram", NOW + timedelta(minutes=30))

    def boom(doc, uploads):
        raise RuntimeError("ffmpeg missing")

    assert await runner.prerender_reels(store, NOW, UPLOADS, boom) == 0


async def test_reel_publish_uses_the_prerendered_video_and_renders_late_if_needed():
    store, pub, render = make()
    ready = await reel_row(store, "instagram", NOW - timedelta(hours=1), video="calendar/reels/reel-w1-tip.mp4")
    late = await reel_row(store, "facebook_page", NOW - timedelta(hours=1), key="reel-w9-tip")
    sent = []

    async def fake_reel(doc, social, uploads):
        sent.append((doc["channel"], doc["video"], doc["caption"]))
        return Result("reel1", None)

    counts = await run(store, pub, render, publish_reel=fake_reel)
    assert counts["published"] == 2 and render.calls == ["reel-w9-tip"]
    assert ("instagram", "calendar/reels/reel-w1-tip.mp4", "reel caption") in sent and pub.posts == []
    assert (await store.get(late))["video"] == "calendar/reels/reel-w9-tip.mp4" and (await store.get(ready))["status"] == "published"


async def test_dry_run_publishes_nothing_for_any_kind_and_does_not_render():
    store, pub, render = make()
    r = await reel_row(store, "instagram", NOW - timedelta(hours=1))
    s = await store.add("kharadi-2bhk-ready", "facebook_page", "c", "x.jpg", NOW - timedelta(hours=1), kind="showcase", status="approved")

    async def never(*a, **k):
        raise AssertionError("must not be called in a dry run")

    counts = await run(store, pub, render, social=DRY, publish_reel=never, publish_showcase=never)
    assert counts["published"] == 2 and render.calls == [] and pub.posts == []
    assert (await store.get(r))["external_id"].startswith("dryrun_")
