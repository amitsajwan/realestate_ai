"""Which highlights a page shows (areastats.profile.shown_highlights)."""
import httpx

from app.modules.areastats import profile, webfacts


def _h(text):
    return {"topic": "amenities", "text": text, "official": True, "sources": [{"site": "a.com", "quote": text}]}


def test_empty_marketing_lines_are_not_shown_and_stay_on_the_record():
    kept = {"highlights": [_h("Layouts planned for natural light, ventilation and daily comfort"), _h("Covered parking"), _h("Over 35 amenities"), _h("2.48 acres")]}
    assert [h["text"] for h in profile.shown_highlights(kept)] == ["Covered parking", "Over 35 amenities", "2.48 acres"]
    assert len(kept["highlights"]) == 4


def test_a_picture_from_another_kind_of_site_is_not_the_builders():
    assert profile.foreign_picture("https://theholidaysplanner.com/wp-content/agra.webp", "empyreanlandmarks.com")


def test_the_builders_own_site_a_picture_host_and_a_site_sharing_its_name_are():
    assert not profile.foreign_picture("https://empyreanlandmarks.com/images/a.jpg", "empyreanlandmarks.com")
    assert not profile.foreign_picture("https://cdn.empyreanlandmarks.com/a.jpg", "empyreanlandmarks.com")
    assert not profile.foreign_picture("https://godrej.blob.core.windows.net/a.jpg", "godrejproperties.com")
    assert not profile.foreign_picture("https://iamkohinoor.com/a.jpg", "kohinoorpune.com")


def _redirects_to_travel(request):
    if request.url.host == "builder.com":
        return httpx.Response(302, headers={"location": "https://holidays.com/"})
    return httpx.Response(200, headers={"content-type": "text/html"}, text="<p>Agra</p>")


async def test_a_page_that_sends_us_to_another_site_is_not_read():
    assert await webfacts.fetch_page("https://builder.com/gallery", httpx.MockTransport(_redirects_to_travel)) is None


async def test_a_page_moving_within_its_own_site_is_read():
    def moved(request):
        if request.url.host == "builder.com":
            return httpx.Response(301, headers={"location": "https://www.builder.com/gallery"})
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<p>Homes</p>")
    assert await webfacts.fetch_page("https://builder.com/gallery", httpx.MockTransport(moved)) == "<p>Homes</p>"


async def test_a_picture_address_that_sends_us_to_another_site_is_not_saved():
    def image(request):
        if request.url.host == "builder.com":
            return httpx.Response(302, headers={"location": "https://holidays.com/agra.jpg"})
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"x")
    assert await profile.fetch_bytes("https://builder.com/pool.jpg", httpx.MockTransport(image)) is None


def test_a_saved_picture_from_another_site_is_not_shown():
    bad = {"path": "a.webp", "source": "builder", "site": "builder.com", "image_url": "https://holidays.com/agra.jpg"}
    good = {"path": "b.webp", "source": "builder", "site": "builder.com", "image_url": "https://builder.com/pool.jpg"}
    assert [p["url"] for p in profile.public({"highlights": [], "photos": [bad, good], "plans": []})["photos"]] == ["/uploads/b.webp"]
