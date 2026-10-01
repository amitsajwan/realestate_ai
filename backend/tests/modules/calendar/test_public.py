from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.calendar import public
from app.modules.calendar.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://media.example.com/")
    public.clear_cache()
    yield
    public.clear_cache()


def setup():
    clock = {"t": NOW}
    store = Store(FakeDb(), clock=lambda: clock["t"])
    app = FastAPI()
    app.include_router(public.router, prefix="/public")
    app.dependency_overrides[public.get_store] = lambda: store
    return TestClient(app), store, clock


async def post(store, clock, slug, channel, caption, *, when, kind="post", link="https://fb.example/p", images=None, status="published"):
    id = await store.add(slug, channel, caption, (images or ["calendar/x.jpg"])[0], NOW, kind=kind, status="approved", images=images)
    clock["t"] = when
    if status == "published":
        await store.published(id, "ext", link)
    elif status != "approved":
        await store._move(id, status, "t")
    return id


async def test_only_published_newest_first_with_fields():
    c, store, clock = setup()
    await post(store, clock, "a", "facebook_page", "Old one\nBody", when=NOW - timedelta(days=5), link="https://fb/1")
    await post(store, clock, "b", "instagram", "New one\n\nBody text #pune #kharadi\nhttps://x.y/z", when=NOW, link="https://ig/2",
               images=["posts/b/1.jpg", "posts/b/2.jpg"])
    for st in ("approved", "planned", "scheduled", "failed", "skipped"):
        await post(store, clock, "z" + st, "facebook_page", "Hidden " + st, when=NOW, status=st)
    r = c.get("/public/posts")
    assert r.status_code == 200 and "max-age=60" in r.headers["cache-control"]
    data = r.json()
    assert [p["title"] for p in data] == ["New one", "Old one"]
    p = data[0]
    assert p["channel"] == "instagram" and p["permalink"] == "https://ig/2" and p["sample"] is False
    assert p["image_url"] == "https://media.example.com/uploads/posts/b/1.jpg"
    assert p["excerpt"] == "New one Body text" and p["published_at"].startswith("2026-10-10")
    assert not any("Hidden" in x["title"] for x in data)


async def test_same_item_on_two_channels_shows_once_with_both_links():
    c, store, clock = setup()
    await post(store, clock, "reel1", "instagram", "Reel caption", when=NOW, kind="reel", link="https://ig/r")
    await post(store, clock, "reel1", "facebook_page", "Reel caption fb", when=NOW + timedelta(hours=1), kind="reel", link="https://fb/r")
    data = c.get("/public/posts").json()
    assert len(data) == 1
    assert data[0]["channel"] == "facebook" and data[0]["permalink"] == "https://fb/r"
    assert {x["channel"]: x["url"] for x in data[0]["links"]} == {"facebook": "https://fb/r", "instagram": "https://ig/r"}


async def test_same_slug_far_apart_is_not_merged_and_showcase_is_sample():
    c, store, clock = setup()
    await post(store, clock, "s", "facebook_page", "Home one", when=NOW - timedelta(days=30), kind="showcase", link="https://fb/1")
    await post(store, clock, "s", "facebook_page", "Home again", when=NOW, kind="showcase", link="https://fb/2")
    data = c.get("/public/posts").json()
    assert len(data) == 2 and all(p["sample"] for p in data)


async def test_excerpt_strips_tags_links_footer_and_phones_and_is_short():
    c, store, clock = setup()
    cap = "Heading line\n" + "word " * 120 + "\nCall +91 98765 43210 or 9876543210\nPUNE Property · https://34-180-39-243.sslip.io\n#a #b"
    await post(store, clock, "l", "facebook_page", cap, when=NOW)
    p = c.get("/public/posts").json()[0]
    assert len(p["excerpt"]) <= 220 and p["excerpt"].endswith("…")
    assert "#" not in p["excerpt"] and "http" not in p["excerpt"]
    assert not any(ch.isdigit() for ch in p["excerpt"])


async def test_missing_permalink_is_never_shown_and_limit_applies():
    c, store, clock = setup()
    await post(store, clock, "n", "facebook_page", "No link", when=NOW, link=None)
    for i in range(5):
        await post(store, clock, f"k{i}", "facebook_page", f"P{i}", when=NOW - timedelta(days=i), link=f"https://fb/{i}")
    assert len(c.get("/public/posts?limit=3").json()) == 3
    assert all(p["title"] != "No link" for p in c.get("/public/posts?limit=50").json())


async def test_no_image_base_gives_null_and_cache_holds(monkeypatch):
    c, store, clock = setup()
    monkeypatch.delenv("PUBLIC_MEDIA_BASE_URL")
    await post(store, clock, "a", "facebook_page", "First", when=NOW)
    assert c.get("/public/posts").json()[0]["image_url"] is None
    await post(store, clock, "b", "facebook_page", "Second", when=NOW + timedelta(minutes=1), link="https://fb/b")
    assert len(c.get("/public/posts").json()) == 1   # cached
    public.clear_cache()
    assert len(c.get("/public/posts").json()) == 2
