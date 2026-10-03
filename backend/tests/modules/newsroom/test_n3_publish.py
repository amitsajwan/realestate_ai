"""Publishing an approved item to the Page (photo post) and Instagram (image post): captions, partial failure, dry run, cap, scheduling."""
from datetime import timedelta
from urllib.parse import parse_qs

import httpx
import pytest

from app.modules.newsroom import captions, digest
from app.modules.newsroom.adapters import SocialPublisher
from app.modules.newsroom.config import NewsroomConfig
from app.modules.newsroom.pipeline import run_once
from app.modules.newsroom.samples import SAMPLES, make_doc
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import CheckResult
from app.platform.meta_graph.config import SocialConfig

from ..fakes import FakeDb
from .helpers import NOW

TOKEN = "EAAB" + "x" * 30
REAL = SocialConfig(dry_run=False, page_id="123", ig_id="456", media_base_url="https://media.test", page_token=TOKEN)
CFG = NewsroomConfig(enabled=True, daily_cap=2)


class Graph:
    """A fake Graph API that records every call; `fail` makes the calls whose path contains the text answer with an error."""

    def __init__(self, fail=()):
        self.calls, self.fail = [], fail

    def __call__(self, req: httpx.Request) -> httpx.Response:
        path = req.url.path
        self.calls.append((req.method, path, parse_qs(req.content.decode()) if req.content else dict(req.url.params)))
        if any(f in path for f in self.fail):
            return httpx.Response(400, json={"error": {"code": 190, "message": f"denied {TOKEN}"}})
        if path.endswith("/photos"):
            return httpx.Response(200, json={"id": "ph1", "post_id": "123_77"})
        if path.endswith("/feed"):
            return httpx.Response(200, json={"id": "123_88"})
        if path.endswith("/media"):
            return httpx.Response(200, json={"id": f"c{len(self.calls)}"})
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "ig77"})
        if req.method == "GET" and "status_code" in str(req.url):
            return httpx.Response(200, json={"status_code": "FINISHED"})
        return httpx.Response(200, json={"permalink": "https://www.instagram.com/p/abc/"})


def publisher(graph, cfg=REAL, checker=None, render=None):
    return SocialPublisher(cfg, transport=httpx.MockTransport(graph), checker=checker, render=render, db=FakeDb())


def story(status="approved", n=0, **kw):
    return {**make_doc(f"s{n:09d}", f"Metro corridor 2B Ramwadi to Wagholi approved, not running yet {n}",
                       ["Metro corridor 2B from Ramwadi to Wagholi has been approved.", "The line is not running yet."],
                       "infrastructure", ["wagholi"], "The Indian Express"), "status": status, **kw}


async def test_both_channels_publish_with_their_own_captions_and_our_link():
    g = Graph()
    res = await publisher(g).publish_item(story())
    assert res["facebook"]["ok"] and res["facebook"]["id"] == "123_77" and res["instagram"]["ok"] and res["instagram"]["id"] == "ig77"
    fb = next(c for c in g.calls if c[1].endswith("/photos"))
    assert fb[2]["url"] == ["https://media.test/uploads/news/s000000000-fb.jpg"] and fb[2]["published"] == ["true"]
    fb_text = fb[2]["caption"][0]
    assert "Read more: https://site.test/news/s000000000" in fb_text and "news.google.com" not in fb_text and fb_text.endswith("https://site.test")
    ig = next(c for c in g.calls if c[1].endswith("/media") and "caption" in c[2])
    assert ig[2]["image_url"] == ["https://media.test/uploads/news/s000000000-ig.jpg"]
    ig_text = ig[2]["caption"][0]
    assert "http" not in ig_text and "www." not in ig_text and "link in our bio" in ig_text
    assert len([t for t in ig_text.split() if t.startswith("#")]) <= 8
    assert res["card"]["variant"] in ("photo", "headline", "figure")


async def test_facebook_failure_does_not_block_instagram():
    res = await publisher(Graph(fail=("/photos",))).publish_item(story())
    assert res["facebook"]["ok"] is False and "[redacted]" in res["facebook"]["error"] and TOKEN not in res["facebook"]["error"]
    assert res["instagram"]["ok"] is True


async def test_instagram_failure_does_not_block_facebook():
    res = await publisher(Graph(fail=("/media",))).publish_item(story())
    assert res["facebook"]["ok"] is True and res["instagram"]["ok"] is False and res["instagram"]["error"]


async def test_instagram_not_configured_is_skipped_not_failed():
    g = Graph()
    res = await publisher(g, SocialConfig(dry_run=False, page_id="123", media_base_url="https://media.test", page_token=TOKEN)).publish_item(story())
    assert res["facebook"]["ok"] and res["instagram"]["skipped"] and not any("/456/" in c[1] for c in g.calls)


async def test_dry_run_makes_no_network_call_and_returns_fake_ids():
    g = Graph()
    res = await publisher(g, SocialConfig(dry_run=True, ig_id="456")).publish_item(story())
    assert g.calls == [] and res["facebook"]["id"].startswith("dry-run-") and res["instagram"]["id"].startswith("dry-run-")


async def test_a_caption_that_fails_the_check_blocks_only_that_channel():
    def checker(d, facts, raw):  # fails only for the Instagram caption (the one without a URL)
        return CheckResult(ok="https://" in d.text, problems=["no link"])
    res = await publisher(Graph(), checker=checker).publish_item(story())
    assert res["facebook"]["ok"] and not res["instagram"]["ok"] and "no link" in res["instagram"]["error"]


async def test_card_failure_falls_back_to_a_text_post_with_our_link_and_skips_instagram():
    def broken(doc, uploads):
        raise RuntimeError("no fonts")
    g = Graph()
    res = await publisher(g, render=broken).publish_item(story())
    feed = next(c for c in g.calls if c[1].endswith("/feed"))
    assert res["facebook"]["ok"] and feed[2]["link"] == ["https://site.test/news/s000000000"]
    assert not res["instagram"]["ok"] and "image" in res["instagram"]["error"]


async def test_digest_goes_to_instagram_as_a_carousel_and_to_facebook_as_one_photo():
    g = Graph()
    dg = {**digest.sample_digest(SAMPLES), "status": "approved"}
    res = await publisher(g).publish_item(dg)
    assert res["facebook"]["ok"] and res["instagram"]["ok"]
    items = [c for c in g.calls if c[1].endswith("/media") and "is_carousel_item" in c[2]]
    assert len(items) == 8 and any(c[2].get("media_type") == ["CAROUSEL"] for c in g.calls)
    assert len([c for c in g.calls if c[1].endswith("/photos")]) == 1


# ---- through the pipeline -------------------------------------------------------------------------------------------------------------

async def seed(store, *docs):
    for i, d in enumerate(docs):
        await store.items.insert_one({**d, "created_at": NOW + timedelta(seconds=i)})


async def test_pipeline_partial_failure_is_recorded_per_channel_and_item_is_published():
    store = Store(FakeDb())
    await seed(store, story())
    c = await run_once(store, [], {}, publisher(Graph(fail=("/photos",))), object(), NOW, CFG)
    d = await store.get("s000000000")
    assert d["status"] == "published" and c["published"] == 1
    ch = d["publish"]["channels"]
    assert ch["facebook"]["ok"] is False and ch["instagram"]["ok"] is True and d["publish"]["platform_id"] == "ig77"
    assert "facebook failed" in d["history"][-1]["note"] and d["card"]["fb"].endswith("-fb.jpg")


async def test_pipeline_all_channels_failing_marks_the_item_failed_safely():
    store = Store(FakeDb())
    await seed(store, story())
    await run_once(store, [], {}, publisher(Graph(fail=("/photos", "/media"))), object(), NOW, CFG)
    d = await store.get("s000000000")
    assert d["status"] == "failed" and TOKEN not in d["history"][-1]["note"]


async def test_pipeline_respects_the_daily_cap_and_dry_run():
    store = Store(FakeDb())
    await seed(store, story(n=1), story(n=2), story(n=3))
    pub = publisher(Graph(), SocialConfig(dry_run=True, ig_id="456"))
    c = await run_once(store, [], {}, pub, object(), NOW, NewsroomConfig(daily_cap=2))
    assert c["published"] == 2 and c["capped"] == 1
    assert (await store.get("s000000003"))["status"] == "approved"
    d = await store.get("s000000001")
    assert d["publish"]["channels"]["facebook"]["dry_run"] is True


async def test_pipeline_waits_for_a_scheduled_time_then_posts_on_both_channels_together():
    store = Store(FakeDb())
    await seed(store, story(publish={"platform_id": None, "scheduled_for": NOW + timedelta(hours=3)}))
    g = Graph()
    c = await run_once(store, [], {}, publisher(g), object(), NOW, CFG)
    assert c["waiting"] == 1 and c["published"] == 0 and g.calls == [] and (await store.get("s000000000"))["status"] == "approved"
    c = await run_once(store, [], {}, publisher(g), object(), NOW + timedelta(hours=3, minutes=1), CFG)
    assert c["published"] == 1 and (await store.get("s000000000"))["status"] == "published"


async def test_pipeline_runs_the_after_publish_hook_and_survives_its_failure():
    store, seen = Store(FakeDb()), []

    async def after(db, doc, channels):
        seen.append((doc["_id"], sorted(channels)))
        raise RuntimeError("hub down")
    await seed(store, story())
    await run_once(store, [], {"after_publish": after}, publisher(Graph()), object(), NOW, CFG)
    assert seen == [("s000000000", ["facebook", "instagram"])] and (await store.get("s000000000"))["status"] == "published"


async def test_the_hub_item_is_a_news_post_with_an_interest_link(monkeypatch):
    from app.modules.newsroom import adapters
    monkeypatch.setenv("INTEREST_OWNER_AGENT_ID", "agent1")
    got = {}

    async def fake_url(db, **kw):
        got["link"] = kw
        return "https://site.test/i/CODE123"

    async def fake_upsert(db, kind, ref, title, image_url, subtitle, code, permalink, sample=False):
        got["hub"] = (kind, ref, title, image_url, subtitle, code, permalink)
    import app.modules.interest.service as svc
    monkeypatch.setattr(svc, "interest_url", fake_url)
    monkeypatch.setattr(svc, "upsert_hub_item", fake_upsert)
    await adapters.register_hub(object(), {**story(), "card": {"fb": "news/x-fb.jpg"}}, "https://www.facebook.com/p/1")
    assert got["hub"][0] == "post" and got["hub"][1] == "news-s000000000" and got["hub"][4] == "NEWS" and got["hub"][5] == "CODE123"
    assert got["hub"][3] == "https://media.test/uploads/news/x-fb.jpg" and got["hub"][6] == "https://www.facebook.com/p/1"
    await adapters.register_hub(None, story())  # no database: silently nothing
    await adapters.register_hub(object(), {**story(), "draft": {**story()["draft"], "format": "digest"}})  # the digest is not a hub item


async def test_captions_are_what_gets_sent():
    g = Graph()
    doc = story()
    await publisher(g).publish_item(doc)
    sent = {c[1].split("/")[-1]: c[2] for c in g.calls if "caption" in c[2]}
    texts = captions.build(doc)
    assert sent["photos"]["caption"] == [texts["facebook"]] and sent["media"]["caption"] == [texts["instagram"]]


async def test_an_item_published_twice_is_posted_once_per_channel(monkeypatch):
    """A retry of an item whose posts already went out (e.g. saving 'published' failed) posts nothing new."""
    monkeypatch.delenv("PUBLISH_LEDGER", raising=False)
    g, db = Graph(), FakeDb()
    pub = SocialPublisher(REAL, transport=httpx.MockTransport(g), db=db)
    first = await pub.publish_item(story())
    posts = [c for c in g.calls if c[1].endswith(("/photos", "/media_publish"))]
    again = await pub.publish_item(story())
    assert [c for c in g.calls if c[1].endswith(("/photos", "/media_publish"))] == posts and len(posts) == 2
    assert again["facebook"]["id"] == first["facebook"]["id"] and again["instagram"]["id"] == first["instagram"]["id"]
