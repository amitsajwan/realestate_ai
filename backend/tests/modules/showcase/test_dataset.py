"""The demo agent's sample homes: believable, credited, light, free of personal data; and nothing plans or posts them."""
import re
from pathlib import Path

import pytest
from PIL import Image

from app.platform.text import PHONE
from app.modules.showcase import samples
from app.modules.showcase.samples import HOMES, ICON_LABELS, PHOTO_DIR

ROOT = Path(__file__).resolve().parents[4]
CREDITS = (ROOT / "docs" / "brand" / "photo-credits.md").read_text(encoding="utf-8")


def test_nine_distinct_homes_across_the_three_areas():
    assert len(HOMES) == 9
    assert len({h.slug for h in HOMES}) == 9
    assert {h.locality for h in HOMES} == {"Kharadi", "Upper Kharadi", "Wagholi"}
    for area in ("Kharadi", "Upper Kharadi", "Wagholi"):
        assert sum(h.locality == area for h in HOMES) == 3
    assert {h.bhk for h in HOMES} == {2, 3}
    assert any(h.ready for h in HOMES) and any(not h.ready for h in HOMES)
    assert len({(h.locality, h.bhk, h.carpet_sqft, h.price_inr) for h in HOMES}) == 9


@pytest.mark.parametrize("h", HOMES, ids=lambda h: h.slug)
def test_home_is_realistic(h):
    lo, hi = (600, 900) if h.bhk == 2 else (900, 1200)
    assert lo <= h.carpet_sqft <= hi
    assert 1 <= h.floor <= h.total_floors
    assert 4_000_000 <= h.price_inr <= 20_000_000
    assert 6_000 <= h.price_inr / h.carpet_sqft <= 16_000
    assert h.ready == h.possession.startswith("Ready")
    assert h.ready or re.search(r"(Dec|Jun) 20(27|28)$", h.possession)
    assert all(a in ICON_LABELS for a in h.amenities) and len(h.amenities) >= 4
    assert len(h.highlights) == 3
    assert 2 <= len(h.photos) <= 4
    assert h.exterior and len(h.interiors) >= 1
    assert h.price_text.startswith("₹")


def test_no_phone_numbers_or_personal_names_in_dataset_text():
    blob = " ".join(str(v) for h in HOMES for v in (h.title, h.highlights, h.possession, h.furnishing, h.price_text, h.amenities))
    assert not PHONE.search(blob)
    assert not re.search(r"@|\+91|\bMr\b|\bMrs\b|\bShri\b", blob)


def test_sample_home_posting_is_gone():
    import importlib.util
    for mod in ("render", "captions", "publish", "plan", "icons"):
        assert importlib.util.find_spec(f"app.modules.showcase.{mod}") is None, mod
    scripts = ROOT / "backend" / "scripts"
    for name in ("showcase_admin.py", "post_samples.py", "make_voiced_reels.py", "post_voiced_reels.py"):
        assert not (scripts / name).exists(), name


def test_photo_files_exist_small_and_credited():
    files = {p.file: p for h in HOMES for p in h.photos}
    assert len(files) >= 20
    total = 0
    for name, p in files.items():
        assert p.path.exists(), name
        total += p.path.stat().st_size
        with Image.open(p.path) as im:
            assert max(im.size) <= 1500 and min(im.size) >= 700
        assert name in CREDITS, f"{name} has no credit row"
        assert p.photographer in CREDITS and p.source_url in CREDITS
        assert p.source_url.startswith("https://unsplash.com/photos/")
    assert total < 6 * 1024 * 1024
    assert {f.name for f in PHOTO_DIR.glob("*.jpg")} == set(files), "unused or missing photo files"


def test_get_unknown_slug_lists_known():
    with pytest.raises(KeyError, match="kharadi-2bhk-ready"):
        samples.get("nope")
