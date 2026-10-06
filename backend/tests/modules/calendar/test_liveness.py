"""The calendar stays honest about what is on Facebook and Instagram: no repeat posts, deleted posts leave Studio, and Post now."""
from datetime import timedelta

import httpx

from app.modules.calendar import liveness
from app.platform.meta_graph.config import SocialConfig

from .test_router import NOW, setup
from .test_runner import add, make, run

SOCIAL = SocialConfig(dry_run=False, page_id="PAGE", ig_id="IG", page_token="tok", media_base_url="https://x.test")


async def test_a_post_that_repeats_one_already_published_on_the_channel_is_held_back():
    store, pub, render = make()
    first = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(minutes=5))
    await run(store, pub, render)
    assert (await store.get(first))["status"] == "published"
    again = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(minutes=1))   # same caption, same channel
    other = await add(store, "carpet-under-rera", "instagram", NOW - timedelta(minutes=1))       # other channel: fine
    counts = await run(store, pub, render, now=NOW + timedelta(minutes=10))
    assert (await store.get(again))["status"] == "skipped" and "held back: same as carpet-under-rera" in (await store.get(again))["history"][-1]["note"]
    assert (await store.get(other))["status"] == "published" and counts["skipped"] == 1 and len(pub.posts) == 2


async def test_duplicates_older_than_the_window_are_allowed():
    store, pub, render = make()
    old = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(minutes=5))
    await run(store, pub, render)
    await store.items.update_one({"_id": old}, {"$set": {"published_at": NOW - timedelta(days=liveness.DUPLICATE_DAYS + 1)}})
    again = await add(store, "carpet-under-rera", "facebook_page", NOW)
    assert liveness.duplicate_of(await store.get(again), await store.all(), NOW) is None


async def test_a_post_deleted_on_the_platform_is_marked_removed_after_two_sightings():
    store, pub, render = make()
    row = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(minutes=5))
    await run(store, pub, render)
    answers = []

    async def gone(doc):
        answers.append(doc["_id"])
        return False

    out = await liveness.check_published(store, gone, NOW)
    assert out == {"checked": 1, "removed": 0, "unknown": 0} and (await store.get(row))["status"] == "published"
    assert (await liveness.check_published(store, gone, NOW + timedelta(minutes=10)))["checked"] == 0   # waits CONFIRM_AFTER
    out = await liveness.check_published(store, gone, NOW + liveness.CONFIRM_AFTER)
    assert out["removed"] == 1 and (await store.get(row))["status"] == "removed"
    assert await store.upcoming() == []


async def test_a_post_that_is_there_or_unknown_stays_published():
    store, pub, render = make()
    row = await add(store, "carpet-under-rera", "facebook_page", NOW - timedelta(minutes=5))
    await run(store, pub, render)

    async def flaky(doc):
        return None

    async def there(doc):
        return True

    for i, fn in enumerate((flaky, there, flaky, flaky)):
        await liveness.check_published(store, fn, NOW + liveness.CHECK_EVERY * (i + 1))
    assert (await store.get(row))["status"] == "published"


async def test_graph_exists_reads_meta_answers():
    def handler(req):
        oid = req.url.path.rsplit("/", 1)[-1]
        if oid == "gone":
            return httpx.Response(400, json={"error": {"code": 100, "message": "does not exist"}})
        if oid == "PAGE_deleted":
            return httpx.Response(400, json={"error": {"code": 10, "message": "Object does not exist, cannot be loaded due to missing permission"}})
        if oid == "perm":
            return httpx.Response(400, json={"error": {"code": 10, "message": "permission"}})
        return httpx.Response(200, json={"id": oid})

    exists = liveness.graph_exists(SOCIAL, transport=httpx.MockTransport(handler))
    assert await exists({"channel": "instagram", "external_id": "live"}) is True
    assert await exists({"channel": "instagram", "external_id": "gone"}) is False
    assert await exists({"channel": "instagram", "external_id": "perm"}) is None
    assert await exists({"channel": "facebook_page", "external_id": "OLDPAGE_123"}) is False   # an old Page we no longer manage
    assert await exists({"channel": "facebook_page", "external_id": "PAGE_123"}) is True
    assert await exists({"channel": "facebook_page", "external_id": "PAGE_deleted"}) is False   # deleted on our own Page: #10
    assert await exists({"channel": "instagram", "external_id": "perm"}) is None                # #10 on Instagram: cannot tell


def test_post_now_approves_and_makes_it_due_at_once(monkeypatch):
    import asyncio

    from app.modules.calendar import library
    monkeypatch.setenv("CALENDAR_OWNER_IDS", "OWNER")
    client, store = setup()
    e = library.BY_SLUG["carpet-under-rera"]
    loop = asyncio.new_event_loop()
    rid = loop.run_until_complete(store.add(e.slug, "instagram", e.ig_caption, "x.jpg", NOW + timedelta(days=2)))   # planned
    r = client.post(f"/calendar/items/{rid}/post-now")
    assert r.status_code == 200 and r.json()["status"] == "approved"
    doc = loop.run_until_complete(store.get(rid))
    assert doc["status"] == "approved" and doc["due_at"] == NOW
    loop.run_until_complete(store.skip(rid))
    assert client.post(f"/calendar/items/{rid}/post-now").status_code == 409
    assert client.post("/calendar/items/nope/post-now").status_code == 404


def _client(monkeypatch, **env):
    monkeypatch.setenv("CALENDAR_OWNER_IDS", "OWNER")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return setup()


def _add(store, n, channel="instagram", days=3):
    import asyncio

    from app.modules.calendar import library
    e = library.BY_SLUG["carpet-under-rera"]
    loop = asyncio.new_event_loop()
    return loop, [loop.run_until_complete(store.add(f"{e.slug}-{i}-{channel}-{days}", channel, f"{e.ig_caption} {i}", "x.jpg",
                                                    NOW + timedelta(days=days + i), status="planned")) for i in range(n)]


def test_post_now_on_many_posts_queues_them_minutes_apart_per_channel(monkeypatch):
    client, store = _client(monkeypatch, CALENDAR_POST_NOW_GAP_MINUTES="10")
    loop, ids = _add(store, 3)
    _, fb = _add(store, 1, channel="facebook_page")
    for i in ids + fb:
        assert client.post(f"/calendar/items/{i}/post-now").status_code == 200
    due = [loop.run_until_complete(store.get(i))["due_at"] for i in ids]
    assert [d - NOW for d in due] == [timedelta(0), timedelta(minutes=10), timedelta(minutes=20)]
    assert loop.run_until_complete(store.get(fb[0]))["due_at"] == NOW        # the other channel is not held up


def test_testing_pace_moves_approved_posts_to_minutes_apart_and_off_keeps_the_planned_day(monkeypatch):
    client, store = _client(monkeypatch, CALENDAR_PACE_MINUTES="15")
    loop, ids = _add(store, 3)
    for i in ids:
        r = client.post(f"/calendar/items/{i}/approve")
        assert r.status_code == 200
    due = [loop.run_until_complete(store.get(i))["due_at"] for i in ids]
    assert [d - NOW for d in due] == [timedelta(0), timedelta(minutes=15), timedelta(minutes=30)]
    monkeypatch.setenv("CALENDAR_PACE_MINUTES", "0")
    _, later = _add(store, 1, days=9)
    client.post(f"/calendar/items/{later[0]}/approve")
    assert loop.run_until_complete(store.get(later[0]))["due_at"] == NOW + timedelta(days=9)


def test_recent_lists_posted_with_link_and_failed_with_reason(monkeypatch):
    client, store = _client(monkeypatch)
    loop, ids = _add(store, 2)
    loop.run_until_complete(store.published(ids[0], "ext1", "https://instagram.test/p/1"))
    loop.run_until_complete(store.attempt_failed(ids[1], "Graph API error 4: limit reached", 3, True))
    rows = client.get("/calendar/recent?hours=24").json()
    by = {r["id"]: r for r in rows}
    assert by[ids[0]]["status"] == "published" and by[ids[0]]["permalink"] == "https://instagram.test/p/1"
    assert by[ids[1]]["status"] == "failed" and "limit reached" in by[ids[1]]["error"]


def test_retry_a_failed_post_and_move_an_approved_one_back(monkeypatch):
    client, store = _client(monkeypatch)
    loop, ids = _add(store, 2)
    loop.run_until_complete(store.attempt_failed(ids[0], "limit reached", 3, True))
    r = client.post(f"/calendar/items/{ids[0]}/retry")
    doc = loop.run_until_complete(store.get(ids[0]))
    assert r.status_code == 200 and doc["status"] == "approved" and doc["attempts"] == 0 and doc["error"] is None
    assert client.post(f"/calendar/items/{ids[0]}/retry").status_code == 409            # not failed any more
    client.post(f"/calendar/items/{ids[1]}/approve")
    assert client.post(f"/calendar/items/{ids[1]}/unapprove").json()["status"] == "planned"
    assert loop.run_until_complete(store.get(ids[1]))["status"] == "planned"
    assert client.post(f"/calendar/items/{ids[1]}/unapprove").status_code == 409
