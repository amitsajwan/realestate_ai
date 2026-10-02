"""The post-upload step (original kept, -enh copy beside it, idempotent) and which copy pages and cards show."""
from datetime import datetime
from pathlib import Path

import cv2
import pytest
from pydantic import ValidationError

from app.modules.listings.schemas import ListingCreate, PublicListing
from app.modules.marketing.images import first_photo_url
from app.modules.photoquality import store
from app.modules.photoquality.analysis import load_bgr

from .test_analysis_enhance import ROOM, darken


@pytest.fixture
def dark_upload(tmp_path):
    p = tmp_path / "images" / "abc123.jpg"
    p.parent.mkdir()
    cv2.imwrite(str(p), darken(load_bgr(ROOM)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    return p


def test_process_keeps_original_and_writes_enhanced_copy(dark_upload):
    before = dark_upload.read_bytes()
    res = store.process_file(dark_upload)
    assert dark_upload.read_bytes() == before
    enh = dark_upload.with_name("abc123-enh.jpg")
    assert enh.is_file() and res["enhanced_url"] == "/uploads/images/abc123-enh.jpg"
    q = res["quality"]
    assert "dark" in q["issues"] and q["enhanced_score"] > q["score"] and res["use_enhanced"] is True
    assert set(q) >= {"score", "issues", "tips", "width", "height"}


def test_process_is_idempotent_and_cached(dark_upload, monkeypatch):
    first = store.process_file(dark_upload)
    monkeypatch.setattr(store, "enhance", lambda *a, **k: (_ for _ in ()).throw(AssertionError("not cached")))
    assert store.process_file(dark_upload) == first


def test_good_photo_does_not_default_to_enhanced(tmp_path):
    p = tmp_path / "good.jpg"
    p.write_bytes(Path(ROOM).read_bytes())
    res = store.process_file(p)
    assert res["quality"]["issues"] == [] and res["use_enhanced"] is False and res["enhanced_url"]


def test_process_skips_enhanced_files_and_junk(tmp_path):
    p = tmp_path / "x-enh.jpg"
    p.write_bytes(Path(ROOM).read_bytes())
    assert store.process_file(p) == {}
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    assert store.process_file(bad) == {}
    assert store.process_file(tmp_path / "missing.jpg") == {}


def test_display_url_rules():
    m = {"url": "http://api.x/uploads/images/a.jpg", "enhanced_url": "/uploads/images/a-enh.jpg", "use_enhanced": True}
    assert store.display_url(m) == "http://api.x/uploads/images/a-enh.jpg"
    assert store.display_url({**m, "use_enhanced": False}) == m["url"]
    # a foreign enhanced url never wins: only our own /uploads/images path is used
    assert store.display_url({"url": "/uploads/images/a.jpg", "enhanced_url": "/etc/passwd", "use_enhanced": True}) == "/uploads/images/a.jpg"


def test_media_schema_accepts_quality_and_rejects_foreign_enhanced_url():
    body = ListingCreate(media=[{"url": "/uploads/images/a.jpg", "kind": "image", "order": 0,
                                 "quality": {"score": 61, "issues": ["dark"], "tips": ["Take it again with the lights on."], "enhanced_score": 88},
                                 "enhanced_url": "/uploads/images/a-enh.jpg", "use_enhanced": True}])
    assert body.media[0].quality.score == 61
    with pytest.raises(ValidationError):
        ListingCreate(media=[{"url": "/uploads/images/a.jpg", "enhanced_url": "https://x.example/a.jpg"}])
    with pytest.raises(ValidationError):
        ListingCreate(media=[{"url": "/uploads/images/a.jpg", "enhanced_url": "/uploads/images/other.jpg"}])
    # old records without the new fields still validate
    assert ListingCreate(media=[{"url": "https://x/a.jpg"}]).media[0].use_enhanced is None


def test_public_listing_and_cards_use_the_chosen_copy():
    now = datetime(2026, 1, 1)
    media = [{"url": "/uploads/images/a.jpg", "kind": "image", "order": 0, "enhanced_url": "/uploads/images/a-enh.jpg",
              "use_enhanced": True, "quality": {"score": 50, "issues": ["dark"]}},
             {"url": "/uploads/images/b.jpg", "kind": "image", "order": 1, "enhanced_url": "/uploads/images/b-enh.jpg", "use_enhanced": False}]
    pub = PublicListing.model_validate({"id": "L1", "status": "live", "title": "t", "description": {"en": "d"}, "media": media,
                                        "created_at": now, "updated_at": now, "agent": {"slug": "s"}})
    dumped = pub.model_dump()["media"]
    assert [m["url"] for m in dumped] == ["/uploads/images/a-enh.jpg", "/uploads/images/b.jpg"]
    assert "quality" not in dumped[0] and "enhanced_url" not in dumped[0]
    assert first_photo_url(media) == "/uploads/images/a-enh.jpg"
    assert first_photo_url([{**media[0], "use_enhanced": False}]) == "/uploads/images/a.jpg"


async def test_upload_hook_adds_quality(dark_upload, monkeypatch):
    from app.api.v1.endpoints import uploads
    res = await uploads._photo_quality(dark_upload)
    assert res["quality"]["score"] < res["quality"]["enhanced_score"]
    monkeypatch.setenv("PHOTO_QUALITY", "off")
    assert await uploads._photo_quality(dark_upload) == {}
