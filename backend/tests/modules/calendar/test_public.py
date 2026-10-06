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
    assert p["excerpt"] == "Body text"  # the title line is not repeated and p["published_at"].startswith("2026-10-10")
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
    cap = "Heading line\n" + "word " * 120 + "\nCall +91 98765 43210 or 9876543210\nPUNE Property · https://avasetu.in\n#a #b"
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


def test_a_reel_card_uses_its_cover_or_first_slide(tmp_path, monkeypatch):
    from app.modules.calendar import config as cal_config
    from app.modules.calendar import public
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://avasetu.in")
    monkeypatch.setattr(cal_config, "uploads_dir", lambda: tmp_path)
    (tmp_path / "agentprojects" / "hd").mkdir(parents=True)
    doc = {"kind": "reel", "images": [], "video": "agentprojects/hd/amco.mp4"}
    assert public._image_url(doc) is None
    (tmp_path / "agentprojects" / "hd" / "amco-1.jpg").write_bytes(b"x")
    assert public._image_url(doc) == "https://avasetu.in/uploads/agentprojects/hd/amco-1.jpg"
    (tmp_path / "agentprojects" / "hd" / "amco-cover.jpg").write_bytes(b"x")
    assert public._image_url(doc).endswith("/amco-cover.jpg")


def test_feed_hides_taken_down_posts_and_shows_a_story_once():
    from datetime import datetime, timezone
    from app.modules.calendar import public
    t = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
    row = lambda slug, kind, cap, **kw: {"_id": slug + kind, "slug": slug, "kind": kind, "channel": "facebook_page", "caption": cap,  # noqa: E731
                                         "status": "published", "permalink": "https://fb/" + slug + kind, "published_at": t, "due_at": t, **kw}
    docs = [row("hd-amco", "post", "AMCO Equa, Wagholi"), row("hd-amco-reel", "reel", "AMCO Equa, Wagholi"),
            row("old-tip", "post", "Read your cost sheet", hidden_from_feed=True), row("hd-anshul-reel", "reel", "Anshul Medora")]
    out = public.build(docs, 10)
    assert [(o["kind"], o["title"]) for o in out] == [("post", "AMCO Equa, Wagholi"), ("reel", "Anshul Medora")]



def test_feed_card_carries_all_slides_our_page_and_no_repeated_title(monkeypatch):
    from datetime import datetime, timezone
    from app.modules.calendar import public
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://avasetu.in")
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in")
    t = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
    cap = "AMCO Equa, Wagholi: 59.99 L.\n\nThe lowest starting price of the five.\n\nListed by House Deal."
    ig = {"_id": "a", "slug": "hd-amco", "kind": "post", "channel": "instagram", "status": "published", "permalink": "https://ig/p/1",
          "published_at": t, "due_at": t, "caption": cap + " Every fact: link in our bio.", "images": [f"hd/amco-{k}.jpg" for k in range(1, 6)]}
    fb = {**ig, "_id": "b", "channel": "facebook_page", "permalink": "https://fb/1", "images": ["hd/amco-1.jpg"],
          "caption": cap + " Every fact: https://avasetu.in/projects/amco-equa\n\nInterested? https://avasetu.in/i/abc"}
    (card,) = public.build([ig, fb], 5)
    assert card["title"] == "AMCO Equa, Wagholi: 59.99 L."
    assert card["excerpt"].startswith("The lowest starting price") and "AMCO Equa, Wagholi" not in card["excerpt"]
    assert len(card["images"]) == 5 and card["images"][0] == "https://avasetu.in/uploads/hd/amco-1.jpg"
    assert card["site_url"] == "https://avasetu.in/projects/amco-equa"


# ---- a page per post: slug, area, audience, filter, one post ----

T0 = datetime(2026, 10, 1, 9, tzinfo=timezone.utc)


def _row(id, slug, caption, *, channel="facebook_page", kind="post", at=T0, **kw):
    return {"_id": id, "slug": slug, "kind": kind, "channel": channel, "caption": caption, "status": "published",
            "permalink": f"https://x/{id}", "published_at": at, "due_at": at, **kw}


def test_slugify_is_lower_case_words_and_hyphens_cut_at_a_word():
    assert public.slugify("AMCO Equa, Wagholi: 59.99 L.") == "amco-equa-wagholi-59-99-l"
    assert public.slugify("Wagholi: 41 projects in MahaRERA records") == "wagholi-41-projects-in-maharera-records"
    long = public.slugify("word " * 40)
    assert len(long) <= public.SLUG_WORDS_MAX and long.endswith("word") and "--" not in long
    assert public.slugify("…!!") == "post"


def test_slug_is_stable_across_runs_and_new_posts():
    a = _row("aaaaaa111", "p1", "Wagholi: 41 projects in MahaRERA records\nBody")
    first = public.build([a], 10)[0]["slug"]
    assert first == "wagholi-41-projects-in-maharera-records"
    later = _row("bbbbbb222", "p2", "Wagholi: 41 projects in MahaRERA records\nAgain", at=T0 + timedelta(days=9))
    out = public.build([later, a], 10)
    assert {o["id"]: o["slug"] for o in out} == {"aaaaaa111": first, "bbbbbb222": first + "-bbbbbb"}
    assert public.build([a, later], 10) == out  # input order does not matter


def test_fb_and_ig_copies_share_one_slug_named_by_the_earliest_copy():
    ig = _row("ig1234567", "hd-x", "Kharadi homes from 70 L\nlink in bio", channel="instagram")
    fb = _row("fb7654321", "hd-x", "Kharadi homes: 70 L onwards\nhttps://x", at=T0 + timedelta(hours=3))
    only_ig = public.build([ig], 5)[0]
    both = public.build([ig, fb], 5)
    assert len(both) == 1 and both[0]["title"] == "Kharadi homes: 70 L onwards"  # Facebook leads the card
    assert both[0]["slug"] == only_ig["slug"] == "kharadi-homes-from-70-l"     # but the address never moved


def test_area_from_row_else_caption_else_none_and_audience():
    out = public.build([
        _row("a1", "s1", "Read your cost sheet before you pay", area="hinjawadi", at=T0),
        _row("a2", "s2", "Upper Kharadi: new launches", at=T0 - timedelta(days=1)),
        _row("a3", "s3", "How to read a MahaRERA page", at=T0 - timedelta(days=2)),
        _row("a4", "promo-agents-1", "Agents: list your projects free", at=T0 - timedelta(days=3)),
        _row("a5", "s5", "Join us", creative={"source": "agent_reels"}, at=T0 - timedelta(days=4)),
    ], 10)
    assert [o["area"] for o in out] == ["hinjawadi", "upper_kharadi", None, None, None]
    assert [o["audience"] for o in out] == ["buyers", "buyers", "buyers", "agents", "agents"]


async def test_area_filter_and_one_post_by_slug_with_full_text(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://avasetu.in")
    c, store, clock = setup()
    cap = ("Wagholi: 41 projects in MahaRERA records\n\nListed or updated this month. #WagholiPune\n"
           "Every fact: https://avasetu.in/localities/wagholi\nInterested? https://avasetu.in/i/abc\n"
           "See also https://evil.example/x for more\nCall +91 98765 43210\nAvasetu · https://avasetu.in")
    await post(store, clock, "w", "facebook_page", cap, when=NOW, link="https://fb/w")
    await post(store, clock, "k", "facebook_page", "Kharadi update\nBody", when=NOW - timedelta(days=1), link="https://fb/k")
    assert [p["area"] for p in c.get("/public/posts?area=wagholi").json()] == ["wagholi"]
    assert [p["area"] for p in c.get("/public/posts?area=kharadi").json()] == ["kharadi"]
    assert c.get("/public/posts?area=keshav-nagar").json() == [] and c.get("/public/posts?area=nowhere").json() == []
    assert all("text" not in p and "_text" not in p for p in c.get("/public/posts").json())
    r = c.get("/public/posts/wagholi-41-projects-in-maharera-records")
    assert r.status_code == 200
    p = r.json()
    assert p["slug"] == "wagholi-41-projects-in-maharera-records" and p["area"] == "wagholi" and p["audience"] == "buyers"
    assert p["text"].startswith("Wagholi: 41 projects in MahaRERA records\n\nListed or updated this month.")
    assert "https://avasetu.in/localities/wagholi" in p["text"]
    assert "#" not in p["text"] and "/i/abc" not in p["text"] and "Interested" not in p["text"]
    assert "evil.example" not in p["text"] and "98765" not in p["text"] and "Avasetu ·" not in p["text"]
    assert c.get("/public/posts/no-such-post").status_code == 404


async def test_a_suffixed_address_always_finds_its_post():
    c, store, clock = setup()
    id = await post(store, clock, "a", "facebook_page", "Same words\nOne", when=NOW)
    p = c.get(f"/public/posts/same-words-{id[:6]}").json()
    assert p["slug"] == "same-words" and p["id"] == id


def test_a_reel_hidden_behind_its_post_leaves_its_address_to_the_post():
    reel = _row("r1", "hd-amco-reel", "AMCO Equa, Wagholi", kind="reel", at=T0)
    assert public.build([reel], 5)[0]["slug"] == "amco-equa-wagholi"
    later = _row("p1", "hd-amco", "AMCO Equa, Wagholi", at=T0 + timedelta(days=1))
    (only,) = public.build([reel, later], 5)
    assert only["kind"] == "post" and only["slug"] == "amco-equa-wagholi"


async def test_limit_goes_up_to_500():
    c, store, clock = setup()
    for i in range(3):
        await post(store, clock, f"k{i}", "facebook_page", f"P{i}", when=NOW - timedelta(days=i), link=f"https://fb/{i}")
    assert len(c.get("/public/posts?limit=500").json()) == 3
    assert len({p["slug"] for p in c.get("/public/posts?limit=500").json()}) == 3
