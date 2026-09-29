from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from app.modules.marketing import images as im
from app.modules.marketing.images import (MARGIN, MAX_BYTES, fit_text, first_photo_url, local_upload_path, render,
                                          render_all)

from .marketing_helpers import VARIANTS, facts

KINDS = ["cover", "facts", "amenities", "cta", "status"]


@pytest.fixture
def up(tmp_path):
    (tmp_path / "images").mkdir()
    return tmp_path


def put_photo(up: Path, name="a1.jpg", color=(200, 30, 30), size=(1600, 900)) -> str:
    Image.new("RGB", size, color).save(up / "images" / name)
    return f"http://testserver/uploads/images/{name}"


def media(url):
    return [{"url": url, "kind": "image", "order": 0}]


def test_all_cards_written_with_expected_sizes(up):
    out = render_all(facts(), [], up, "L1")
    assert list(out) == KINDS
    for kind in KINDS:
        p = up / "marketing" / "L1" / f"{kind}.jpg"
        assert p.is_file() and p.stat().st_size < 400 * 1024
        with Image.open(p) as i:
            assert i.size == ((1080, 1920) if kind == "status" else (1080, 1080)) and i.format == "JPEG"
        assert out[kind]["path"] == f"/uploads/marketing/L1/{kind}.jpg"


def test_amenities_card_only_when_listing_has_amenities_and_stale_removed(up):
    render_all(facts(), [], up, "L1")
    assert (up / "marketing/L1/amenities.jpg").exists()
    out = render_all(facts(amenities=[]), [], up, "L1")  # regenerate after amenities were removed
    assert "amenities" not in out and not (up / "marketing/L1/amenities.jpg").exists()


def test_local_upload_is_shown_brightly_with_a_scrim_only_behind_the_text(up):
    url = put_photo(up)
    render_all(facts(), media(url), up, "L1")
    render_all(facts(_id="L2"), [], up, "L2")
    with Image.open(up / "marketing/L1/cover.jpg") as a, Image.open(up / "marketing/L2/cover.jpg") as b:
        r, g, bl = a.getpixel((900, 200))
        assert r > 2.5 * g and r > 150          # the photo is clearly visible in the upper part (not buried)...
        r_low, g_low, _ = a.getpixel((900, 1040))
        assert r_low < 110                       # ...and darkened near the bottom where the text sits, so it stays legible
        r2, g2, _ = b.getpixel((900, 200))
        assert r2 < 2.5 * g2                    # fallback is a calm gradient, not the photo


def test_info_cards_show_the_photo_as_a_header_strip_and_story_uses_top_half(up):
    url = put_photo(up)
    render_all(facts(), media(url), up, "L1")
    for kind in ("facts", "amenities", "cta"):
        with Image.open(up / f"marketing/L1/{kind}.jpg") as im:
            r, g, _ = im.getpixel((900, 100))
            assert r > 2.5 * g and r > 150, kind      # header strip
            r2, g2, _ = im.getpixel((900, 900))
            assert r2 < 2.5 * g2, kind                # the panel below is the calm brand gradient
    with Image.open(up / "marketing/L1/status.jpg") as im:
        r, g, _ = im.getpixel((900, 400))
        assert r > 2.5 * g and r > 150


def test_first_photo_is_the_one_used(up):
    put_photo(up, "second.jpg", (30, 200, 30))
    url = put_photo(up, "first.jpg", (200, 30, 30))
    m = [{"url": "http://x/uploads/images/second.jpg", "kind": "image", "order": 1},
         {"url": url, "kind": "image", "order": 0}]
    assert first_photo_url(m).endswith("first.jpg")
    assert first_photo_url([{"url": "v.mp4", "kind": "video", "order": 0}]) is None


@pytest.mark.parametrize("url", [
    "https://evil.example/uploads/images/../../etc/passwd",
    "http://169.254.169.254/latest/meta-data",
    "https://example.com/photo.jpg",
    "/uploads/images/../secret.jpg",
    "/uploads/images/..%2Fsecret.jpg",
    "/uploads/images/%2e%2e/secret.jpg",
    "/uploads/images/sub/secret.jpg",
    "/uploads/documents/secret.jpg",
    "//uploads/images/secret.jpg",
    "../secret.jpg", "secret.jpg", "/secret.jpg", "/etc/passwd", "C:\\secret.jpg", "file:///etc/passwd",
    "/uploads/images/..\\secret.jpg", "/uploads/images/", "/uploads/images/.hidden", "", None,
])
def test_hostile_inputs_never_resolve_or_open(up, monkeypatch, url):
    (up / "secret.jpg").write_bytes(b"x")
    Image.new("RGB", (10, 10)).save(up / "images" / "ok.jpg")
    assert local_upload_path(url, up) is None
    opened = []
    real = Image.open
    monkeypatch.setattr(im.Image, "open", lambda *a, **k: opened.append(a[0]) or real(*a, **k))
    render_all(facts(), media(url or "x"), up, "L9")
    assert opened == []  # nothing was read (only the rendered cards get written, never opened)


def test_remote_host_with_upload_like_path_only_reads_local_file(up):
    url = put_photo(up).replace("testserver", "elsewhere.example")
    assert local_upload_path(url, up) == (up / "images" / "a1.jpg").resolve()  # path component decides; no fetch
    assert local_upload_path("http://x/uploads/images/missing.jpg", up) is None


def test_symlink_escape_rejected(up, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "s.jpg"
    Image.new("RGB", (5, 5)).save(outside)
    link = up / "images" / "link.jpg"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    assert local_upload_path("/uploads/images/link.jpg", up) is None


def test_unsafe_listing_id_rejected(up):
    for bad in ("../x", "a/b", "", "a b"):
        with pytest.raises(ValueError):
            render_all(facts(), [], up, bad)


def test_corrupt_or_huge_source_falls_back(up):
    (up / "images" / "bad.jpg").write_bytes(b"not an image")
    out = render_all(facts(), media("/uploads/images/bad.jpg"), up, "L1")
    assert (up / "marketing/L1/cover.jpg").exists() and "cover" in out


def test_file_size_limit_with_noisy_photo(up):
    Image.effect_noise((1600, 1200), 90).convert("RGB").save(up / "images" / "n.jpg")
    render_all(facts(), media("/uploads/images/n.jpg"), up, "L1")
    for k in KINDS:
        assert (up / "marketing/L1" / f"{k}.jpg").stat().st_size <= 400 * 1024
    assert MAX_BYTES <= 400 * 1024


LONG = dict(locality="Very Long Locality Name Near The Old Railway Station Road", city="Pimpri-Chinchwad",
            project_name="Extraordinarily Long Project Name Residency Phase Two Wing C",
            amenities=["Swimming pool with kids area", "Landscaped garden and jogging track", "Covered car parking",
                       "24x7 power backup", "Clubhouse with indoor games", "CCTV security", "Lift", "Gym", "Extra"],
            rera_no="P" + "5" * 40, possession="Dec 2027 (phase 2, tower C)")


@pytest.mark.parametrize("over", [{}, LONG, VARIANTS["plot_min"], VARIANTS["luxury_villa"], VARIANTS["rent_cheap"]])
@pytest.mark.parametrize("kind", KINDS)
def test_text_stays_inside_safe_margins(kind, over):
    if kind == "amenities" and not facts(**over).amenities:
        pytest.skip("no amenities card")
    card = render(kind, facts(**over), None)
    w, h = card.size
    assert card.boxes
    for x0, y0, x1, y1 in card.boxes:
        assert x0 >= MARGIN - 4 and x1 <= w - MARGIN + 4, (kind, (x0, x1))
        assert y0 >= card.top - 6 and y1 <= card.bottom + 6, (kind, (y0, y1), card.top, card.bottom)


def test_fit_text_wraps_shrinks_and_ellipsizes():
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    font, lines = fit_text(d, "Rs 1.25 Cr", 900, 1, 120)
    assert len(lines) == 1 and d.textlength(lines[0], font=font) <= 900
    font, lines = fit_text(d, "word " * 60, 500, 2, 40, 24)
    assert len(lines) == 2 and lines[-1].endswith("…") and all(d.textlength(x, font=font) <= 500 for x in lines)
    font, lines = fit_text(d, "W" * 200, 300, 2, 40, 24)  # an unbreakable word is split by characters
    assert all(d.textlength(x, font=font) <= 300 for x in lines) and len(lines) <= 2
    font, lines = fit_text(d, "Big title wraps", 300, 3, 60, 20)
    assert len(lines) <= 3 and all(d.textlength(x, font=font) <= 300 for x in lines)


def test_palette_is_deterministic():
    assert im.palette_for("Rahul|Baner") == im.palette_for("Rahul|Baner")
    assert len({im.palette_for(str(i)) for i in range(40)}) > 1


def test_non_latin_agent_name_is_not_drawn_as_boxes():
    assert im.latin("राहुल Sharma") == "Sharma"


@pytest.mark.parametrize("over", [{}, LONG, VARIANTS["luxury_villa"], VARIANTS["rent_cheap"]])
@pytest.mark.parametrize("kind", KINDS)
def test_text_stays_inside_safe_margins_with_a_photo_header(kind, over):
    """Regression (visual review): with a photo the facts card cut off its last row (RERA) at the bottom edge.
    The photo layouts differ from the no-photo ones, so they need their own bounds check."""
    if kind == "amenities" and not facts(**over).amenities:
        pytest.skip("no amenities card")
    photo = Image.new("RGB", (1600, 1200), (150, 190, 225))
    card = render(kind, facts(**over), photo)
    w, h = card.size
    assert card.boxes
    for x0, y0, x1, y1 in card.boxes:
        assert x0 >= MARGIN - 4 and x1 <= w - MARGIN + 4, (kind, (x0, x1))
        assert y0 >= card.top - 6 and y1 <= card.bottom + 6, (kind, (y0, y1), card.top, card.bottom)


def test_every_fact_row_is_drawn_on_the_facts_card_with_a_photo():
    full = facts(rera_no="P52100012345", furnishing="semi", possession="ready", floor=3, total_floors=12, carpet_sqft=1100)
    card = render("facts", full, Image.new("RGB", (1600, 1200), (150, 190, 225)))
    rows = len([1 for _ in im._facts_rows(full)])
    assert rows >= 6
    # one label box + one value box per row + the title
    assert len(card.boxes) >= 2 * rows + 1
