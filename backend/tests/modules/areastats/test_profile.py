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


def _logo() -> bytes:
    im = Image.new("RGB", (1200, 800), "white")
    im.paste((10, 40, 90), (300, 250, 900, 550))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=90)
    return out.getvalue()


def test_a_logo_or_a_blank_tile_is_no_photo_but_a_render_is():
    assert profile.picture(_logo(), "photo") is None
    assert profile.picture(_jpeg("tower", (1600, 900)), "photo") is not None


def test_a_plan_on_white_is_still_taken_as_a_plan():
    assert profile.picture(_logo(), "plan") is not None


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


async def test_pictures_on_other_sites_pages_are_not_downloaded_and_the_stored_ones_stay(tmp_path):
    # pages never show a picture copied from another site (pages.shown_pictures), so a portal's are not fetched any more
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb
    portal = "https://www.squareyards.com/pune-residential-property/godrej-ivara/123/project"
    raw = "<p>Godrej Ivara P52100012345: 2 and 3 BHK homes in Upper Kharadi, Pune.</p>" + \
        "".join(f'<img src="https://img.squareyards.com/godrej-ivara-{k}.jpg" alt="Godrej Ivara {k}">' for k in ("tower", "pool"))
    asked = []

    async def search(q):
        return [{"type": "organic", "position": 1, "link": portal, "title": "Godrej Ivara Upper Kharadi Pune",
                 "snippet": "Godrej Ivara by Godrej Properties, 2 and 3 BHK in Upper Kharadi"}]

    async def page(url):
        return raw if url == portal else None

    async def image(url):
        asked.append(url)
        return _jpeg(url, (1600, 900))

    async def nothing_drawn(prompt):
        return None
    stored = [_photo(IVARA[0], source="web")]
    doc = {"_id": "P52100012345", "regno": "P52100012345", "name": "Godrej Ivara", "promoter": "Godrej Properties Ltd",
           "locality": "upper_kharadi", "completion_now": "2032-12-16", "profile": {"highlights": [], "photos": stored}}
    step, fields = await profile.gather(Store(FakeDb()), doc, None, NOW, fetch=page, image=image, search=search,
                                        media_dir=tmp_path / "project_media", draw=nothing_drawn)
    assert any(r["url"] == portal for r in fields["profile"]["read"])   # the portal page was read, for its words
    assert asked == []
    assert fields["profile"]["photos"] == stored   # never thrown away (seo-system.md section 8b)


async def test_highlights_are_read_from_pages_naming_the_whole_project_and_not_from_its_namesake(monkeypatch, tmp_path):
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb
    line = "Pristine O2 World has a rooftop pool."
    pages_by_url = {"https://a.example/p": f"<p>Pristine O2 World in Wagholi, Pune. RERA registered. {line}</p>",
                    "https://b.example/p": f"<p>Pristine O2 World in Baner, Pune. RERA registered. {line}</p>"}

    async def stored(store, d, name, search, now):
        assert name == "Pristine O2 World Part 3"   # the search stays under the exact name
        return [{"type": "organic", "position": n + 1, "link": u, "title": "Pristine O2 World", "snippet": ""}
                for n, u in enumerate(pages_by_url)]

    async def page(url):
        return pages_by_url.get(url)

    async def nothing_drawn(prompt):
        return None
    asked = []

    async def highlights(llm, src, name, text, regno=""):
        asked.append((src["url"], name))
        return [], "0 highlights"
    monkeypatch.setattr(profile.webfacts, "results_for", stored)
    monkeypatch.setattr(profile, "read_highlights", highlights)
    doc = {"_id": "P1", "regno": "P1", "name": "Pristine O2 World Part 3", "promoter": "Logipark Warehousing LLP",
           "locality": "wagholi", "pune_place": "wagholi", "pune_place_name": "Wagholi", "completion_now": "2032-12-16"}
    _, fields = await profile.gather(Store(FakeDb()), doc, object(), NOW, fetch=page, media_dir=tmp_path / "m", draw=nothing_drawn)
    assert asked == [("https://a.example/p", "Pristine O2 World")]
    assert [r["why"] for r in fields["profile"]["read"] if r["url"].startswith("https://b")] == ["page names another project of that name"]


def test_only_the_builders_own_site_keeps_its_link_on_a_highlight():
    portal = {"topic": "open_space", "text": "Six towers", "official": False,
              "sources": [{"site": "housiey.com", "url": "https://housiey.com/p", "quote": "6 towers"},
                          {"site": "magicbricks.com", "url": "https://magicbricks.com/p", "quote": "Has six towers"}]}
    builder = {"topic": "amenities", "text": "A clubhouse", "official": True,
               "sources": [{"site": "builder.com", "url": "https://builder.com/p", "quote": "A clubhouse"}]}
    shown = profile.public({"at": datetime(2026, 11, 2, tzinfo=timezone.utc), "highlights": [portal, builder]})["highlights"]
    assert [s["url"] for s in shown[0]["sources"]] == [None, None]
    assert shown[1]["sources"][0]["url"] == "https://builder.com/p"


SIX = "Limited open space; six towers occupy a 1.5-acre site"


def highlight(text, *quotes, official=False):
    return {"topic": "open_space", "text": text, "official": official,
            "sources": [{"site": f"site{i}.com", "url": f"https://site{i}.com", "quote": q} for i, q in enumerate(quotes)]}


def test_a_second_site_counts_only_if_its_sentence_says_what_the_bullet_says():
    assert profile.backed(SIX, "Limited open space with 6 towers on a 1.5-acre site")
    assert not profile.backed(SIX, "It occupies an area of 1 Acre.")
    assert not profile.backed("2 towers with basement parking", "The project consists of 3 towers.")
    assert not profile.backed("Swimming pool, gym and a clubhouse", "This locality has essential amenities.")


def test_a_bullet_only_one_site_holds_says_one_site_and_keeps_its_wording():
    h = highlight(SIX, "6 towers on a 1.5-acre site, limited open space", "It occupies an area of 1 Acre.")
    shown = profile.shown_highlights({"highlights": [h]})
    assert shown[0]["text"] == SIX and [s["site"] for s in shown[0]["sources"]] == ["site0.com"]
    assert h["sources"][1]["site"] == "site1.com"   # the record keeps both readings


def test_a_builders_own_highlight_keeps_its_source():
    h = highlight("A clubhouse", "A clubhouse", official=True)
    assert profile.shown_highlights({"highlights": [h]})[0]["sources"] == h["sources"]


FILED = {"building_totals": {"towers": 11}, "buildings": [{"name": "A", "floors": 43}, {"name": "D", "floors": 38}]}


def test_mahareras_buildings_hide_a_bullet_they_prove_wrong():
    assert profile.contradicts("11 towers, each with 43 floors", FILED)
    assert profile.contradicts("9 towers on 12 acres", FILED)
    assert profile.contradicts("Five towers of 30 floors each", FILED)


def test_a_builders_habitable_floors_are_not_called_wrong_but_its_tower_count_can_be():
    assert not profile.contradicts("Each wing has 18 habitable floors", FILED, official=True)
    assert profile.contradicts("9 towers", FILED, official=True)


def test_more_towers_than_this_registration_may_be_the_whole_project():
    assert not profile.contradicts("Fourteen towers across phases", FILED)
    assert not profile.contradicts("14 towers across phases", FILED)
    assert not profile.contradicts("A tower with 43 floors", FILED)
    assert not profile.contradicts("11 towers, each with 43 floors", {"buildings": [{"floors": 43}, {"floors": 43}]})
    assert not profile.contradicts("2 towers", None)


def test_a_hidden_bullet_leaves_the_page_and_the_writers_facts_but_not_the_record():
    stored = {"at": datetime(2026, 11, 2, tzinfo=timezone.utc), "highlights": [highlight("11 towers, each with 43 floors", "x", "y")]}
    assert profile.public(stored, doc=FILED)["highlights"] == [] and profile.lines(stored, FILED) == []
    assert len(stored["highlights"]) == 1


RIVERDALE = {"locality": "wagholi", "pune_place_name": "Wagholi", "building_totals": {"towers": 3},
             "buildings": [{"name": "A1", "floors": 28}, {"name": "A2", "floors": 28}, {"name": "A3", "floors": 28}]}


def test_a_line_that_sits_the_project_in_another_area_is_not_shown_even_from_the_builder():
    assert profile.contradicts("Located in the greenest pocket of Kharadi", RIVERDALE, official=True)
    assert profile.contradicts("Nestled in the heart of Kharadi", RIVERDALE)


def test_a_line_naming_another_area_as_a_neighbour_or_beside_our_own_place_stays():
    assert not profile.contradicts("Located near Kharadi IT parks", RIVERDALE)
    assert not profile.contradicts("Located in Wagholi, close to Kharadi", RIVERDALE)
    assert not profile.contradicts("10 minutes from Kharadi", RIVERDALE)
    assert not profile.contradicts("Located in Kharadi", {"locality": "upper_kharadi", "pune_place_name": "Upper Kharadi"})
    assert not profile.contradicts("Located in Kharadi", None)


def test_floors_each_taller_than_any_filed_tower_are_not_shown_but_the_builder_may_count_its_own():
    assert profile.contradicts("There are 6 towers with 30 floors each", RIVERDALE)
    assert not profile.contradicts("There are 6 towers with 28 floors each", RIVERDALE)
    assert not profile.contradicts("There are 6 towers with 30 floors each", RIVERDALE, official=True)
