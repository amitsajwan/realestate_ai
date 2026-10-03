"""Renderer geometry, margins and labels (renders three homes once)."""
import re

import pytest
from PIL import Image

from app.platform.text import PHONE
from app.modules.showcase import render, samples
from app.modules.showcase.render import FACEBOOK, GRID_SAFE_X, MARGIN, PORTRAIT, STORY

SLUGS = ["kharadi-2bhk-ready", "wagholi-2bhk-under-construction", "upper-kharadi-3bhk-ready"]


@pytest.fixture(scope="module")
def rendered():
    out = {}
    for s in SLUGS:
        h = samples.get(s)
        out[s] = {"carousel": render.render_carousel(h), "fb": render.render_facebook(h), "story": render.render_story(h)}
    return out


def all_canvases(rendered):
    for s, r in rendered.items():
        for c in r["carousel"] + r["story"] + [r["fb"]]:
            yield s, c


def test_sizes(rendered):
    for r in rendered.values():
        assert len(r["carousel"]) == 5 and all(c.img.size == PORTRAIT for c in r["carousel"])
        assert r["fb"].img.size == FACEBOOK
        assert len(r["story"]) == 5 and all(c.img.size == STORY for c in r["story"])


def test_every_image_is_labelled_as_a_sample(rendered):
    for s, c in all_canvases(rendered):
        text = " ".join(c.texts)
        assert "Sample listing" in text, s
        assert "Illustrative home, not for sale" in text, s
        assert "SAMPLE HOME" in text, s


def test_no_phone_numbers_or_urls_on_images(rendered):
    for s, c in all_canvases(rendered):
        text = " ".join(c.texts)
        assert not PHONE.search(text.replace(",", ""))
        assert not re.search(r"https?://|www\.", text)


def test_text_stays_inside_margins_and_grid_safe_zone(rendered):
    for s, r in rendered.items():
        for c in r["carousel"]:
            for b in c.boxes:
                x0, y0, x1, y1 = b
                if x1 - x0 >= c.w - 10:      # full-width plates are backgrounds, not text
                    continue
                assert x0 >= MARGIN - 4 and x1 <= c.w - MARGIN + 4, (s, b)
                assert x0 >= GRID_SAFE_X and x1 <= c.w - GRID_SAFE_X, (s, b)   # survives Instagram's 3:4 grid crop
                assert y0 >= 40 and y1 <= c.h - 40, (s, b)
        for c in r["story"]:
            for b in c.boxes:
                x0, y0, x1, y1 = b
                if x1 - x0 >= c.w - 10:
                    continue
                assert x0 >= MARGIN - 4 and x1 <= c.w - MARGIN + 4, (s, b)
                assert y0 >= 230 and y1 <= 1920 - 290, (s, b)     # clear of story app chrome
        for b in r["fb"].boxes:
            x0, y0, x1, y1 = b
            assert x0 >= 40 and x1 <= r["fb"].w - 40 and y0 >= 30 and y1 <= r["fb"].h - 30, (s, b)


def test_cover_carries_the_key_facts_in_big_type(rendered):
    for s, r in rendered.items():
        h = samples.get(s)
        cover = r["carousel"][0]
        assert f"{h.bhk} BHK" in cover.texts and f"{h.carpet_text} carpet area" in cover.texts
        assert f"{h.locality.upper()}, PUNE" in cover.texts
        assert max(b[3] - b[1] for b in cover.boxes) >= 120


def test_slide_roles(rendered):
    h = samples.get(SLUGS[0])
    c = rendered[SLUGS[0]]["carousel"]
    assert "INSIDE THE HOME" in c[1].texts and set(h.highlights) <= set(c[1].texts)
    assert "AT A GLANCE" in c[2].texts and samples.RERA_LINE in c[2].texts and "SAMPLE PRICE" in c[2].texts
    assert "WHY THIS AREA" in c[3].texts
    assert "Comment INTERESTED for details" in c[4].texts and samples.AGENTS_CTA in c[4].texts and "Link in bio" in c[4].texts


def test_cover_is_photo_led_not_flat():
    vals = list(render.slide_cover(samples.get(SLUGS[0])).img.convert("L").resize((60, 75)).getdata())
    assert max(vals) - min(vals) > 120 and len(set(vals)) > 60


def test_cover_fit_size_and_focus():
    im = Image.new("RGB", (1500, 1000), (0, 0, 0))
    im.paste((255, 255, 255), (1100, 0, 1500, 1000))
    left = render.cover_fit(im, (600, 800), (0.1, 0.5)).convert("L").getpixel((300, 400))
    right = render.cover_fit(im, (600, 800), (0.9, 0.5)).convert("L").getpixel((300, 400))
    assert render.cover_fit(im, (1080, 1350)).size == (1080, 1350)
    assert right > left


def test_write_home_files_and_sizes(tmp_path):
    files = render.write_home(samples.get(SLUGS[0]), tmp_path)
    assert [p.name for p in files["carousel"]] == ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg"]
    assert files["facebook"][0].name == "facebook.jpg" and len(files["scenes"]) == 5
    for p in files["carousel"] + files["facebook"] + files["scenes"]:
        assert p.exists() and p.stat().st_size <= 400 * 1024
    assert (tmp_path / SLUGS[0] / "scenes" / "1.jpg").exists()


def test_contact_sheet_builds():
    ims = [Image.new("RGB", (100, 130), (i * 20, 0, 0)) for i in range(5)]
    assert render.contact_sheet(ims, 3, 50).width == 3 * 50 + 4 * 14
