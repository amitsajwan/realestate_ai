"""The cover card and the campaign posts use the listing's best photo (the ranked hero), not just the first upload."""
from types import SimpleNamespace

from PIL import Image

from app.modules.marketing.images import cover_photo_path, photo_paths, render_all
from app.modules.propertyfacts.jobs import MarketingRuns

from .marketing_helpers import facts
from .photo_helpers import blurred, save, scene


def media(*names):
    return [{"url": f"http://testserver/uploads/images/{n}.jpg", "kind": "image", "order": i} for i, n in enumerate(names)]


def put(up):
    d = up / "images"
    save(d, "blur.jpg", blurred(scene(4)))
    save(d, "tall.jpg", scene(6, (900, 1200)))
    save(d, "a.jpg", scene(1))
    return up


def test_cover_photo_skips_a_blurry_first_upload_and_prefers_landscape(tmp_path):
    up = put(tmp_path)
    m = media("blur", "tall", "a")
    assert [p.stem for p in photo_paths(m, up)] == ["blur", "tall", "a"]
    assert cover_photo_path(m, up).stem == "a"
    assert cover_photo_path(media("blur"), up).stem == "blur"     # the only photo is still used
    assert cover_photo_path([], up) is None
    assert cover_photo_path([{"url": "https://x.test/a.jpg", "kind": "image"}], up) is None


def test_the_cover_card_is_drawn_from_the_hero(tmp_path, monkeypatch):
    from app.modules.marketing import images as im
    up = put(tmp_path)
    seen = []
    real = im._load_source
    monkeypatch.setattr(im, "_load_source", lambda p: seen.append(p) or real(p))
    render_all(facts(), media("blur", "tall", "a"), up, "L1")
    assert [p.stem for p in seen] == ["a", "tall"]        # the hero first (the cover); the next ranked photo for the other cards
    with Image.open(up / "marketing" / "L1" / "cover.jpg") as c:
        assert c.size == (1080, 1080)


def test_campaign_posts_use_the_hero(tmp_path):
    up = put(tmp_path)
    runs = SimpleNamespace(uploads_dir=up)
    assert MarketingRuns._photo(runs, {"media": media("blur", "tall", "a")}) == str(up.resolve() / "images" / "a.jpg")
    assert MarketingRuns._photo(runs, {"media": []}) == "none"
