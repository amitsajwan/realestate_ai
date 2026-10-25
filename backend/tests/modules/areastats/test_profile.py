"""Near-duplicate photos in a project profile (areastats.profile): one render saved twice shows once."""
import io
import random
from datetime import datetime, timezone

from PIL import Image

from app.modules.areastats import profile

NOW = datetime(2026, 10, 25, 9, 0, tzinfo=timezone.utc)
# the eight photos on /projects/godrej-ivara-pune (2026-10-25); the 2nd and 5th are the same pool render, 17 bits apart
IVARA = ["1701086a6a6ff73f", "9d0e0e4d29202c29", "5251626343a382a0", "0b0b92929a2b3b1f",
         "cc1d0e0e4929202c", "91e48e8b35061a58", "e87071a7a22a36de", "986ae7c647c7c383"]


def _photo(h: str, width: int = 1600, height: int = 900, source: str = "builder") -> dict:
    return {"path": f"project_media/pr1260002502426/{h}.webp", "width": width, "height": height, "alt": "", "source": source}


def test_the_same_render_saved_twice_shows_once_and_different_pictures_all_stay():
    kept = profile.distinct_photos([_photo(h) for h in IVARA])
    assert [p["path"].rsplit("/", 1)[-1][:16] for p in kept] == [h for h in IVARA if h != "cc1d0e0e4929202c"]


def test_the_larger_copy_stays_in_the_first_copys_place():
    kept = profile.distinct_photos([_photo(IVARA[0]), _photo(IVARA[1], 1200, 675), _photo(IVARA[2]), _photo(IVARA[4], 1600, 900)])
    assert [p["path"].rsplit("/", 1)[-1][:16] for p in kept] == [IVARA[0], IVARA[4], IVARA[2]]


def test_the_builders_copy_beats_a_larger_copy_from_another_site():
    kept = profile.distinct_photos([_photo(IVARA[1], 1600, 900, "web"), _photo(IVARA[4], 1200, 675, "builder")])
    assert [p["source"] for p in kept] == ["builder"]


def test_pictures_not_named_by_their_hash_are_never_merged():
    brochure = [{"path": f"brochures/x/page-{i}.webp", "width": 1600, "height": 900, "source": "brochure"} for i in range(3)]
    assert profile.distinct_photos(brochure) == brochure


def _jpeg(pattern: str, size: tuple) -> bytes:
    rnd = random.Random(pattern)
    cells = Image.new("L", (12, 8))
    cells.putdata([rnd.randrange(256) for _ in range(96)])
    out = io.BytesIO()
    cells.resize(size, Image.BILINEAR).convert("RGB").save(out, "JPEG", quality=90)
    return out.getvalue()


async def test_the_builders_site_showing_one_render_small_and_large_saves_only_the_large_one(tmp_path):
    base = "https://www.godrejproperties.com/pune/residential/godrej-ivara"
    files = {f"{base}/pool-small.jpg": _jpeg("pool", (1000, 563)), f"{base}/tower.jpg": _jpeg("tower", (1600, 900)),
             f"{base}/pool-large.jpg": _jpeg("pool", (1600, 900))}
    raw = "".join(f'<img src="{u}" alt="Godrej Ivara {u.rsplit("/", 1)[-1][:-4]}">' for u in files)

    async def fetch(url):
        return files.get(url)

    photos, plans, _ = await profile.pictures([{"url": base, "official": True, "site": "godrejproperties.com"}], {base: raw},
                                              "Godrej Ivara", "PR1260002502426", fetch, tmp_path / "project_media")
    assert [p["image_url"].rsplit("/", 1)[-1] for p in photos] == ["pool-large.jpg", "tower.jpg"]
    assert photos[0]["width"] == 1600 and not plans
    assert sorted(f.name for f in (tmp_path / "project_media" / "pr1260002502426").iterdir()) == \
        sorted(p["path"].rsplit("/", 1)[-1] for p in photos)


def test_a_stored_profile_with_both_copies_shows_one_on_the_page_and_keeps_its_plans():
    stored = {"at": NOW, "highlights": [], "photos": [_photo(h) for h in IVARA],
              "plans": [_photo(IVARA[1]), _photo(IVARA[4])]}
    shown = profile.public(stored)
    assert len(shown["photos"]) == 7
    assert not any("cc1d0e0e4929202c" in p["url"] for p in shown["photos"])
    assert len(shown["plans"]) == 2   # floor plans look alike to a dHash: only the photo rule is wider


async def test_without_a_model_the_builders_pictures_are_still_taken_and_the_highlights_stay(tmp_path):
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb
    base = "https://www.godrejproperties.com/pune/residential/godrej-ivara"
    files = {f"{base}/tower.jpg": _jpeg("tower", (1600, 900)), f"{base}/pool.jpg": _jpeg("pool", (1600, 900))}
    raw = "<p>Godrej Ivara, 2 and 3 BHK homes in Upper Kharadi, Pune.</p>" + \
        "".join(f'<img src="{u}" alt="Godrej Ivara {u.rsplit("/", 1)[-1][:-4]}">' for u in files)

    async def page(url):
        return raw if url == base else None

    async def image(url):
        return files.get(url)

    async def nothing_drawn(prompt):
        return None
    kept = [{"topic": "clubhouse", "text": "A clubhouse", "official": True, "sources": []}]
    doc = {"_id": "PR1260002502426", "regno": "PR1260002502426", "name": "Godrej Ivara", "locality": "upper_kharadi",
           "completion_now": "2032-12-16", "builder_pages": [base], "profile": {"highlights": kept}}
    step, fields = await profile.gather(Store(FakeDb()), doc, None, NOW, fetch=page, image=image,
                                        media_dir=tmp_path / "project_media", draw=nothing_drawn)
    shown = fields["profile"]
    assert sorted(p["image_url"].rsplit("/", 1)[-1] for p in shown["photos"]) == ["pool.jpg", "tower.jpg"]
    assert shown["highlights"] == kept and step["ok"]
    assert "highlights not read: no LLM key" in step["checked"]
