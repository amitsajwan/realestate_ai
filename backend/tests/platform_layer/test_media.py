"""Pinned output of the media record helpers: which upload URLs are ours, enhanced-copy names, the URL shown publicly.

Recorded from the code before it moved into the platform (MODERNIZATION step 2); a move must not change a single output.
"""
import pytest

from app.modules.photoquality.store import _local_path as upload_path
from app.modules.photoquality.store import display_url, enhanced_name, is_enhanced_name, public_media


@pytest.mark.parametrize("url, path", [
    ("/uploads/images/a.jpg", "/uploads/images/a.jpg"),
    ("https://x.in/uploads/images/a.jpg", "/uploads/images/a.jpg"),
    ("/uploads/images/../etc", None),
    ("/uploads/images/.hidden", None),
    ("/uploads/other/a.jpg", None),
    ("http://[bad", None),
    ("", None),
    (None, None),
    (123, None),
    ("/uploads/images/a b.jpg", None),
    ("/uploads/images/a..b.jpg", None),
])
def test_upload_path(url, path):
    assert upload_path(url) == path


@pytest.mark.parametrize("name, enhanced, enhanced_as", [
    ("a.jpg", False, "a-enh.jpg"),
    ("a-enh.jpg", True, "a-enh-enh.jpg"),
    ("a-enh.png", True, "a-enh-enh.jpg"),
    ("a.enh.jpg", False, "a.enh-enh.jpg"),
    ("photo.webp", False, "photo-enh.jpg"),
])
def test_enhanced_names(name, enhanced, enhanced_as):
    assert is_enhanced_name(name) is enhanced
    assert enhanced_name(name) == enhanced_as


ENH = "/uploads/images/a-enh.jpg"


@pytest.mark.parametrize("record, shown", [
    ({"url": "/uploads/images/a.jpg"}, "/uploads/images/a.jpg"),
    ({"url": "/uploads/images/a.jpg", "enhanced_url": ENH, "use_enhanced": True}, ENH),
    ({"url": "/uploads/images/a.jpg", "enhanced_url": ENH, "use_enhanced": False}, "/uploads/images/a.jpg"),
    ({"url": "https://x.in/uploads/images/a.jpg", "enhanced_url": ENH, "use_enhanced": True}, "https://x.in/uploads/images/a-enh.jpg"),
    ({"url": "https://cdn.com/a.jpg", "enhanced_url": "https://evil.com/x.jpg", "use_enhanced": True}, "https://cdn.com/a.jpg"),
    ({"url": "https://cdn.com/a.jpg", "enhanced_url": ENH, "use_enhanced": True}, ENH),
    ({}, ""),
])
def test_display_url(record, shown):
    assert display_url(record) == shown


def test_public_media_keeps_only_the_shown_url():
    class Model:
        def model_dump(self):
            return {"url": "/uploads/images/m.jpg", "kind": "video", "order": 2}

    media = [{"url": "/uploads/images/a.jpg", "enhanced_url": ENH, "use_enhanced": True, "quality": {"score": 1}, "order": 1},
             Model(), "junk", {"url": "u"}]
    assert public_media(media) == [
        {"url": ENH, "kind": "image", "order": 1},
        {"url": "/uploads/images/m.jpg", "kind": "video", "order": 2},
        {"url": "u", "kind": "image", "order": 0},
    ]
    assert public_media(None) == []
