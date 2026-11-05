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


def _result(link, position=1, title="Rose Court Pune"):
    return {"link": link, "title": title, "snippet": "", "position": position}


def test_sites_that_never_give_anything_are_not_tried():
    got = webfacts.pick_sources([_result("https://www.housing.com/rose", 1), _result("https://99acres.com/rose", 2), _result("https://housiey.com/rose", 3)], "Rose Court", "rose")
    assert [x["site"] for x in got] == ["housiey.com"]


async def test_a_project_missing_its_builders_site_gets_one_search_for_it():
    from datetime import datetime, timezone
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb
    store, now, asked = Store(FakeDb()), datetime(2026, 11, 5, tzinfo=timezone.utc), []

    async def search(q):
        asked.append(q)
        return [_result("https://roselandmarks.com/rose-court"), _result("https://portal.com/rose")]
    doc = {"_id": "P1", "regno": "P1", "promoter": "Rose Landmarks LLP"}
    got = await webfacts.builder_results(store, doc, "Rose Court", search, now, [_result("https://portal.com/rose")])
    assert [r["link"] for r in got] == ["https://roselandmarks.com/rose-court"] and "Rose Landmarks LLP" in asked[0]
    again = await webfacts.builder_results(store, doc, "Rose Court", search, now, [_result("https://portal.com/rose")])
    assert again == got and len(asked) == 1


async def test_no_search_when_the_builders_site_is_already_found_or_the_builder_unknown():
    from datetime import datetime, timezone
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb
    store, now = Store(FakeDb()), datetime(2026, 11, 5, tzinfo=timezone.utc)

    async def search(q):
        raise AssertionError("no search")
    doc = {"_id": "P1", "regno": "P1", "promoter": "Rose Landmarks LLP"}
    assert await webfacts.builder_results(store, doc, "Rose Court", search, now, [_result("https://roselandmarks.com/")]) == []
    assert await webfacts.builder_results(store, {"_id": "P2"}, "Rose Court", search, now, []) == []


def test_health_warns_before_search_credits_run_out():
    from app.modules.admin import health
    assert health.search_row(True, 2000)["status"] == health.OK
    assert health.search_row(True, 100)["status"] == health.WARN
    assert health.search_row(True, -20)["status"] == health.BAD
    assert health.search_row(False, None)["status"] == health.WARN


async def test_credits_are_read_from_the_account(monkeypatch):
    from app.modules.areastats import websearch
    monkeypatch.setenv("SERPER_API_KEY", "k")
    assert await websearch.credits(httpx.MockTransport(lambda r: httpx.Response(200, json={"balance": 2130}))) == 2130
    assert await websearch.credits(httpx.MockTransport(lambda r: httpx.Response(403, json={}))) is None
