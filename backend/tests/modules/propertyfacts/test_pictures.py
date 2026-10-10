"""Card pictures: one ranked pool of photos, video stills and brochure pages."""
import json

from PIL import Image, ImageDraw

from app.modules.propertyfacts import pictures


def _scene(path, seed, paper=False):
    im = Image.new("RGB", (320, 240), (250, 250, 250) if paper else (60 + seed * 30, 150 - seed * 10, 90 + seed * 20))
    d = ImageDraw.Draw(im)
    for k in range(12):
        x = (k * 37 * (seed + 1)) % 300
        d.rectangle([x, (k * 23) % 200, x + 20, (k * 23) % 200 + 30], fill=(20 * k % 255, 200 - 10 * k, 40 + 15 * seed) if not paper else (30, 30, 30))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return str(path)


def test_rank_prefers_places_and_drops_near_duplicates(tmp_path):
    a = _scene(tmp_path / "images" / "a.jpg", 1)
    dup = str(tmp_path / "images" / "dup.jpg")
    Image.open(a).resize((300, 225)).save(dup)
    page = _scene(tmp_path / "brochure" / "page00.jpg", 2, paper=True)
    presenter = _scene(tmp_path / "frames" / "frame00.jpg", 3)
    site = _scene(tmp_path / "frames" / "frame01.jpg", 4)
    (tmp_path / "frames" / "shots.json").write_text(json.dumps({
        "frame00.jpg": {"what": "presenter talking to camera", "score": 7, "person_on_screen": True},
        "frame01.jpg": {"what": "plot boundary stones and road", "score": 7}}))
    out = pictures.rank([presenter, page, a, site, dup], own=[a, dup], notes=pictures.shot_notes(tmp_path / "frames"))
    assert set(out[:2]) == {a, site} and dup not in out
    assert out.index(site) < out.index(presenter) and out.index(site) < out.index(page)


def test_rank_never_fails_on_a_bad_file(tmp_path):
    bad = tmp_path / "x.jpg"
    bad.write_bytes(b"not a jpeg")
    good = _scene(tmp_path / "images" / "g.jpg", 1)
    assert pictures.rank([str(bad), good]) == [good, str(bad)]
    assert pictures.walkthrough_pictures([str(bad), good]) == [good]
