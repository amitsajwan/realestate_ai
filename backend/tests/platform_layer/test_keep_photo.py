"""platform.media.keep_photo (2026-11-17): the one way a picture for a public page is stored: sized, upright, without EXIF."""
import io

import pytest
from PIL import Image

from app.platform.media import PhotoError, drop_photo, keep_photo


def photo(w, h, orientation=None) -> bytes:
    im = Image.new("RGB", (w, h), (200, 100, 50))
    out = io.BytesIO()
    if orientation:
        exif = Image.Exif()
        exif[0x0112] = orientation
        exif[0x010F] = "PhoneMaker"   # a phone writes its make, and often where it stood
        im.save(out, "JPEG", exif=exif.tobytes())
    else:
        im.save(out, "JPEG")
    return out.getvalue()


def test_a_kept_photo_is_sized_turned_upright_and_saved_without_exif(tmp_path):
    out = keep_photo(photo(2400, 1200, orientation=6), "area_photos/kharadi", "abc", root=tmp_path)
    # orientation 6 is a phone held upright: the stored photo stands tall
    assert out == {"url": "/uploads/area_photos/kharadi/abc.webp", "small_url": "/uploads/area_photos/kharadi/abc-small.webp",
                   "width": 800, "height": 1600}
    big = Image.open(tmp_path / "area_photos" / "kharadi" / "abc.webp")
    assert big.size == (800, 1600) and not big.info.get("exif")
    assert Image.open(tmp_path / "area_photos" / "kharadi" / "abc-small.webp").size == (320, 640)


def test_what_is_not_a_photo_too_small_or_badly_named_is_refused(tmp_path):
    with pytest.raises(PhotoError):
        keep_photo(b"nope", "x", "a", root=tmp_path)
    with pytest.raises(PhotoError):
        keep_photo(photo(500, 300), "x", "a", min_side=800, root=tmp_path)
    with pytest.raises(PhotoError):
        keep_photo(photo(900, 900), "../etc", "a", root=tmp_path)
    assert not list(tmp_path.rglob("*.webp"))


def test_drop_photo_removes_both_sizes(tmp_path):
    keep_photo(photo(900, 900), "x", "a", root=tmp_path)
    assert len(list(tmp_path.rglob("*.webp"))) == 2
    drop_photo("x", "a", root=tmp_path)
    assert not list(tmp_path.rglob("*.webp"))
