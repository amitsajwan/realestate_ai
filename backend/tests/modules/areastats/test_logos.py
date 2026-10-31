"""Builder logos: the builder's own logo is picked from its home page (not a project's, not a partner's), checked to be a logo and
not a photo, drawn from SVG without reading outside files, and stored once per builder on every one of its projects."""
import io
import random
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw

from app.modules.areastats import logos, pages
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)
PAGE = {"registered_on": "2024-01-10", "completion_now": "2029-10-30", "project_type": "Residential", "locality": "kharadi",
        "news": [], "in_register": True}


def png(size=(300, 80), background=(255, 255, 255, 255), ink=(20, 40, 120, 255)) -> bytes:
    im = Image.new("RGBA", size, background)
    d = ImageDraw.Draw(im)
    w, h = size
    d.rectangle((w // 8, h // 4, w // 2, 3 * h // 4), fill=ink)
    d.ellipse((w // 2 + 10, h // 4, w // 2 + 10 + h // 2, 3 * h // 4), fill=ink)
    out = io.BytesIO()
    im.save(out, "PNG")
    return out.getvalue()


def photo(size=(1200, 600)) -> bytes:
    rnd = random.Random(7)
    im = Image.new("RGB", size)
    im.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)) for _ in range(size[0] * size[1])])
    out = io.BytesIO()
    im.save(out, "JPEG")
    return out.getvalue()


HOME = """<html><head>
<script type="application/ld+json">{"@type": "WebSite", "name": "Kolte Patil"}</script>
<link rel="apple-touch-icon" href="/touch.png">
</head><body>
<img height="1" width="1" src="https://www.facebook.com/tr?id=1">
<header><a class="brand"><img src="/img/24k-logo-home.png" alt="24K Sound of Joy"></a>
<img src="/img/menu.svg" alt="menu"></header>
<img src="/img/kolte-patil-official.jpg" alt="Kolte-Patil Developers Ltd. Official Logo">
<img src="/_next/image?url=%2Fimg%2Fhero-banner.jpg&amp;w=3840&amp;q=75" alt="Kolte Patil homes">
<img src="/img/rera-logo.png" alt="MahaRERA">
</body></html>"""


def test_the_builders_own_logo_comes_before_a_projects_and_the_touch_icon_comes_last():
    got = logos.candidates(HOME, "https://www.koltepatil.com/", ["Kolte Patil"])
    assert got[0] == "https://www.koltepatil.com/img/kolte-patil-official.jpg"
    assert got[-1] == "https://www.koltepatil.com/touch.png"
    assert "https://www.koltepatil.com/img/24k-logo-home.png" in got
    assert not any("rera" in u or "facebook" in u or "menu" in u for u in got)


def test_a_logo_in_the_structured_data_is_tried_first():
    raw = '<script type="application/ld+json">{"@type": "Organization", "logo": {"url": "/brand.png"}}</script>' + HOME
    assert logos.candidates(raw, "https://www.koltepatil.com/", ["Kolte Patil"])[0] == "https://www.koltepatil.com/brand.png"


def test_the_builders_name_in_the_sites_address_does_not_make_a_photo_a_candidate_and_next_images_are_read_at_source():
    raw = ('<img alt="Panchshil" srcSet="/_next/image?url=%2Fassets%2Fpanchshil-logo.png&amp;w=256&amp;q=75 1x">'
           '<img alt="Residential" src="/_next/image?url=https%3A%2F%2Fwww.panchshil.com%2Fasset%2Fresidential.webp&amp;w=3840">')
    assert logos.candidates(raw, "https://panchshil.com/", ["Panchshil Realty"]) == ["https://panchshil.com/assets/panchshil-logo.png"]


def test_a_flat_logo_is_kept_trimmed_and_a_photo_or_a_tiny_favicon_is_not():
    im = logos.logo_picture(png())
    assert im is not None and im.size[0] < 300 and logos.tone(im) == "dark"   # the white margin is trimmed away
    assert logos.logo_picture(photo()) is None
    assert logos.logo_picture(png((48, 48))) is None
    assert logos.logo_picture(b"not a picture") is None


def test_white_lettering_on_transparency_is_shown_on_the_dark_band():
    im = logos.logo_picture(png(background=(0, 0, 0, 0), ink=(255, 255, 255, 255)))
    assert im is not None and logos.tone(im) == "light"


def test_an_svg_logo_is_drawn_as_a_picture_without_reading_outside_files(monkeypatch):
    svg = (b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           b'width="200" height="50" viewBox="0 0 200 50"><script>alert(1)</script>'
           b'<image xlink:href="file:///etc/secret.png" width="200" height="50"/>'
           b'<rect x="10" y="10" width="80" height="30" fill="#123456"/><circle cx="140" cy="25" r="15" fill="#123456"/></svg>')
    assert logos.is_svg(svg)
    drawn = []
    real = logos.resvg_py.svg_to_bytes
    monkeypatch.setattr(logos.resvg_py, "svg_to_bytes", lambda **kw: drawn.append(kw["svg_string"]) or real(**kw))
    im = logos.logo_picture(svg)
    assert im is not None and im.size[0] > im.size[1]
    assert "secret" not in drawn[0] and "<script" not in drawn[0] and "<rect" in drawn[0]


class Web:
    """The builder's home page and its pictures; counts what was read."""

    def __init__(self, pages_, pictures):
        self.pages, self.pictures, self.read = pages_, pictures, []

    async def page(self, url):
        self.read.append(url)
        return self.pages.get(url)

    async def fetch(self, url):
        self.read.append(url)
        return self.pictures.get(url)


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, name, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": name, "page_slug": name.lower().replace(" ", "-"),
                                         **PAGE, **extra})
    return db, store


async def test_one_logo_is_read_per_builder_and_every_one_of_its_projects_shows_it(tmp_path):
    official = {"profile": {"read": [{"site": "koltepatil.com", "url": "https://www.koltepatil.com/pune/life-republic",
                                      "official": True, "ok": True}]}}
    db, store = await seeded(("P1", "Kolte Patil Life Republic", {"promoter": "Kolte Patil Developers Ltd", **official}),
                             ("P2", "Kolte Patil Ivy Estate", {"promoter": "Kolte Patil Developers Ltd"}),
                             ("P3", "Sai Heights", {"promoter": "Sai Constructions"}))
    web = Web({"https://koltepatil.com/": HOME},
              {"https://koltepatil.com/img/kolte-patil-official.jpg": png(), "https://koltepatil.com/touch.png": png((180, 180))})
    got = await logos.refresh(store, NOW, page=web.page, fetch=web.fetch, search=None, logo_dir=tmp_path / "builder_logos")
    assert got == {"found": 1, "none": 0, "searched": 0}   # Sai Constructions: no site on record and no search today
    p1, p2, p3 = [await store.project(r) for r in ("P1", "P2", "P3")]
    assert p1["builder_logo"]["status"] == "found" and p2["builder_logo"] == p1["builder_logo"] and "builder_logo" not in p3
    assert p1["builder_logo"]["image_url"] == "https://koltepatil.com/img/kolte-patil-official.jpg"
    assert (tmp_path / "builder_logos" / "kolte-patil.png").exists()
    shown = pages.track_record(p2, [p1, p2, p3])["logo"]
    assert shown["url"].endswith("builder_logos/kolte-patil.png") and shown["tone"] == "dark" and shown["site"] == "koltepatil.com"
    assert pages.track_record(p3, [p1, p2, p3])["logo"] is None
    assert await logos.refresh(store, NOW + timedelta(hours=2), page=web.page, fetch=web.fetch, search=None) is None   # once a day


async def test_a_builder_without_a_site_on_record_is_searched_once_and_only_its_own_domain_counts(tmp_path):
    db, store = await seeded(("P1", "Nyati Elysia", {"promoter": "Nyati Builders Pvt Ltd"}),
                             ("P2", "Sai Heights", {"promoter": "Sai Constructions"}))
    queries = []

    async def search(q):
        queries.append(q)
        if "Nyati" in q:
            return [{"link": "https://www.nyati-homes-pune.in/nyati", "title": "Nyati Group projects", "position": 1},
                    {"link": "https://nyatigroup.com/", "title": "Nyati Group: builders in Pune", "position": 2}]
        return [{"link": "https://www.magicbricks.com/sai", "title": "Sai Constructions", "position": 1}]
    web = Web({"https://nyatigroup.com/": '<img src="/images/logo/logo.png" alt="Nyati Group Logo">'},
              {"https://nyatigroup.com/images/logo/logo.png": png()})
    got = await logos.refresh(store, NOW, page=web.page, fetch=web.fetch, search=search, logo_dir=tmp_path)
    assert got == {"found": 1, "none": 1, "searched": 2}
    assert (await store.project("P1"))["builder_logo"]["site"] == "nyatigroup.com"
    sai = (await store.project("P2"))["builder_logo"]
    assert sai["status"] == "none" and sai["why"] == "no site of the builder found"
    # nothing found is tried again after RETRY_DAYS, a found logo is not read again before REFRESH_DAYS
    later = NOW + timedelta(days=logos.RETRY_DAYS + 1)
    queries.clear()
    assert await logos.refresh(store, later, page=web.page, fetch=web.fetch, search=search, logo_dir=tmp_path) == \
        {"found": 0, "none": 1, "searched": 1}
    assert len(queries) == 1 and "sai constructions" in queries[0]
