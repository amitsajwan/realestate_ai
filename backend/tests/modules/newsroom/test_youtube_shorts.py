"""A published story goes to our YouTube channel as a Short made from its cards (docs/plan/visibility-base.md step 1): only once the
upload is set up, once per story through the publish ledger, never in a dry run, and never holding up or failing the story."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.modules.newsroom import adapters
from app.modules.newsroom.samples import SAMPLES
from app.modules.social import distribution

from ..fakes import FakeDb

NOW = datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc)
KEYS = {"YOUTUBE_UPLOAD": "on", "YOUTUBE_CLIENT_ID": "cid", "YOUTUBE_CLIENT_SECRET": "sec", "YOUTUBE_REFRESH_TOKEN": "ref"}
RING_ROAD = {**SAMPLES[0], "status": "published"}


@pytest.fixture
def set_up(monkeypatch):
    for k, v in KEYS.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def uploaded(monkeypatch):
    """youtube_short with Google answered: records each (ref, video, meta)."""
    calls = []

    async def fake(db, ref, video, meta, **kw):
        calls.append((ref, video, meta))
        return distribution.Result(external_id="vid1", permalink="https://www.youtube.com/shorts/vid1")
    monkeypatch.setattr(adapters, "youtube_short", fake)
    return calls


def with_cards(doc: dict, uploads: Path) -> dict:
    for rel in (f"news/{doc['_id']}-ig.jpg", f"news/{doc['_id']}-fb.jpg"):
        (uploads / rel).parent.mkdir(parents=True, exist_ok=True)
        (uploads / rel).write_bytes(b"jpg")
    return {**doc, "card": {"ig": f"news/{doc['_id']}-ig.jpg", "fb": f"news/{doc['_id']}-fb.jpg"}}


def renderer(log: list):
    def render(slides, dest, hook):
        log.append((list(slides), hook))
        Path(dest).write_bytes(b"mp4")
        return dest
    return render


async def test_a_story_becomes_a_short_from_its_cards_opening_on_our_headline(set_up, uploaded, tmp_path):
    drawn = []
    doc = with_cards(RING_ROAD, tmp_path)
    res = await adapters.to_youtube(FakeDb(), doc, tmp_path, renderer(drawn))
    assert res.permalink == "https://www.youtube.com/shorts/vid1"
    (slides, hook), = drawn
    assert [p.name for p in slides] == ["a1b2c3d4e5-ig.jpg", "a1b2c3d4e5-fb.jpg"] and hook
    ref, video, meta = uploaded[0]
    assert ref == "news-a1b2c3d4e5" and video == tmp_path / "news/shorts/a1b2c3d4e5.mp4"


async def test_the_video_names_the_place_and_opens_with_the_story_page(set_up):
    m = adapters.youtube_meta(RING_ROAD)
    assert "Kharadi" in m.title and "Pune" in m.title
    assert m.description.startswith("Full story with its sources: ") and "/news/a1b2c3d4e5" in m.description.splitlines()[0]
    assert "Reported by Times of India" in m.description and 'Search "Avasetu Kharadi" on Google' in m.description
    assert m.tags[:2] == ["Kharadi", "Wagholi"] and "news.google.com" not in m.description


async def test_nothing_is_drawn_or_sent_until_the_upload_is_set_up(monkeypatch, uploaded, tmp_path):
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)
    drawn = []
    assert await adapters.to_youtube(FakeDb(), with_cards(RING_ROAD, tmp_path), tmp_path, renderer(drawn)) is None
    assert drawn == [] and uploaded == []


async def test_a_story_without_its_cards_is_skipped_quietly(set_up, uploaded, tmp_path):
    drawn = []
    assert await adapters.to_youtube(FakeDb(), {**RING_ROAD, "card": {"ig": "news/gone-ig.jpg"}}, tmp_path, renderer(drawn)) is None
    assert drawn == [] and uploaded == []


async def test_a_render_failure_never_reaches_the_published_story(set_up, uploaded, tmp_path):
    def broken(slides, dest, hook):
        raise RuntimeError("ffmpeg failed")
    assert await adapters.to_youtube(FakeDb(), with_cards(RING_ROAD, tmp_path), tmp_path, broken) is None and uploaded == []


async def test_the_video_is_drawn_once_and_reused(set_up, uploaded, tmp_path):
    drawn = []
    doc = with_cards(RING_ROAD, tmp_path)
    await adapters.to_youtube(FakeDb(), doc, tmp_path, renderer(drawn))
    await adapters.to_youtube(FakeDb(), doc, tmp_path, renderer(drawn))
    assert len(drawn) == 1 and len(uploaded) == 2  # the ledger in youtube_short keeps the second from uploading again


async def test_after_publish_sends_the_short_only_when_the_story_really_went_out(set_up, monkeypatch, tmp_path):
    sent = []

    async def to_youtube(db, doc, *a, **kw):
        sent.append(doc["_id"])

    async def no_hub(*a, **kw):
        return None
    monkeypatch.setattr(adapters, "to_youtube", to_youtube)
    monkeypatch.setattr(adapters, "register_hub", no_hub)
    db = FakeDb()
    await adapters.after_publish(db, RING_ROAD, {"facebook": {"ok": True, "id": "dry-run-1", "dry_run": True}})
    await adapters.after_publish(db, RING_ROAD, {"facebook": {"ok": False, "error": "x"}, "instagram": {"ok": False, "error": "y"}})
    assert sent == []
    await adapters.after_publish(db, RING_ROAD, {"facebook": {"ok": True, "id": "1_2"}, "instagram": {"ok": False, "error": "y"}})
    assert sent == ["a1b2c3d4e5"]


async def test_the_weekly_digest_short_is_its_carousel_opening_on_the_cover_line(set_up, uploaded, tmp_path):
    rels = [f"news/digest-w1-ig-{i}.jpg" for i in (1, 2, 3)]
    for r in rels:
        (tmp_path / r).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / r).write_bytes(b"jpg")
    doc = {"_id": "digest-w1", "draft": {"format": "digest", "title": "Kharadi and Wagholi this week", "text": "x",
                                          "link": "https://avasetu.in/news"},
           "relevance": {"pillar": "digest", "areas": ["kharadi", "wagholi"]}, "card": {"ig": rels, "fb": "news/digest-w1-fb.jpg"},
           "digest": {"cover": "3 updates for Kharadi and Wagholi", "items": [{"hook": "Ring road funds approved", "source": "TOI"}]}}
    drawn = []
    await adapters.to_youtube(FakeDb(), doc, tmp_path, renderer(drawn))
    (slides, hook), = drawn
    assert [p.name for p in slides] == ["digest-w1-ig-1.jpg", "digest-w1-ig-2.jpg", "digest-w1-ig-3.jpg"]
    assert hook == "3 updates for Kharadi and Wagholi"
    meta = uploaded[0][2]
    assert meta.description.startswith("Full story with its sources: https://avasetu.in/news") and "• Ring road funds approved (TOI)" in meta.description
