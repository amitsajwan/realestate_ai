"""The MahaRERA number comes first: it finds the project's pages and proves them, and the builder is known by its whole name."""
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.modules.areastats import brands, enrich, profile, webfacts
from app.modules.newsroom.sources.maharera import _ORG
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=timezone.utc)
GERA = {"_id": "P52100052259", "regno": "P52100052259", "name": "Gera Island of Joy Project", "promoter": "Gera Developments Pvt Ltd",
        "locality": "kharadi"}


class FakeStore:
    def __init__(self):
        self.db = FakeDb()


def test_a_page_printing_the_number_is_about_the_project_whatever_name_it_uses():
    ok, _ = webfacts.about_project(GERA, "Gera Island of Joy Project", "Gera's Island of Joy, East Kharadi. MahaRERA P52100052259")
    assert ok


def test_a_page_with_another_name_and_no_number_is_still_refused():
    ok, why = webfacts.about_project(GERA, "Gera Island of Joy Project", "Gera's Island of Joy, East Kharadi, 3 BHK homes in Pune")
    assert not ok and why == "page does not name the project"


def test_a_list_of_many_projects_proves_nothing_about_one_of_them():
    many = " ".join(f"P521000{n:05d}" for n in range(9))
    assert not webfacts.prints_regno(GERA, f"P52100052259 {many}")
    assert webfacts.prints_regno(GERA, "Phases: P52100052259 P52100052260 P52100052261")


def test_another_projects_number_is_not_this_ones():
    assert not webfacts.prints_regno(GERA, "MahaRERA P52100052260")


def test_the_builders_whole_name_finds_a_domain_its_first_word_never_could():
    kate = {"promoter": "M/S KATE MOZZE ASSOCIATES", "name": "Eastern Royale"}
    assert webfacts.official("https://katemozzeassociates.com/eastern-royale/", webfacts.builder_words(kate))
    kolte = {"promoter": "Kolte Patil Developers Limited", "name": "Springshire"}
    assert webfacts.official("https://www.koltepatil.com/pune/springshire", webfacts.builder_words(kolte))
    assert webfacts.official("https://www.kolte-patil.com/pune/springshire", webfacts.builder_words(kolte))


def test_a_brands_own_site_is_known_and_a_marketers_domain_with_the_project_in_it_is_not():
    vj = {"promoter": "Vilas Javdekar Eco Homes LLP", "name": "Palladio Kharadi Central"}
    words = webfacts.builder_words(vj)
    assert webfacts.official("https://javdekars.com/projects/ongoing-projects/pkc.html", words)
    rohan = {"promoter": "Rohan Builders (India) Pvt Ltd", "name": "Rohan Abhilasha 4"}
    assert not webfacts.official("https://rohanabhilasha-wagholi.in/", webfacts.builder_words(rohan))


def test_a_project_filed_under_another_company_joins_the_brand_in_its_name():
    assert brands.of({"promoter": "MERCULUS CONSTRUWELL PVT LTD", "name": "Altamira By VTP Luxe"}).slug == "vtp-realty"


@pytest.mark.parametrize("firm", ["NIVASA BUILDCON", "Krishna Buildcon", "NG Rathi Promoters", "Choice Developments", "Yashodha Reality",
                                  "MAHALAXMI SHELTERS", "Vilas Javdekar Eco Homes", "New Dream Landmark AOP", "M/S MANGAL SHANTI DEVELOPEMENT"])
def test_firms_are_named(firm):
    assert _ORG.search(firm)


@pytest.mark.parametrize("person", ["Sarita Shishir Sinha", "YOGESH ANANDPAL GOYAL", "VIKRANT MOHAN RISWADKAR", "Sachin Vijaykumar Jadhav"])
def test_people_stay_unnamed(person):
    assert not _ORG.search(person)


def test_a_page_calling_itself_a_marketers_gives_no_pictures_even_on_the_builders_name():
    assert webfacts.marketer_page("Disclaimer: we are an authorized marketing partner of the developer")
    assert not webfacts.marketer_page("Home Projects Channel Partner Contact Us")   # a builder's menu inviting brokers


async def test_the_builders_page_printing_the_number_gives_pictures_though_its_address_has_another_name(tmp_path):
    got = []

    async def fetch(url):
        got.append(url)
        return None

    raw = '<html><body>Rohan Abhilasha 4. MahaRERA P52100080076. <img src="https://rohanbuilders.com/render.jpg"></body></html>'
    url = "https://rohanbuilders.com/homes/wagholi-new"
    src = {"url": url, "site": "rohanbuilders.com", "official": True}
    _, _, why = await profile.pictures([src], {url: raw}, "Rohan Abhilasha", "P52100080076", fetch, tmp_path)
    assert why != "no builder page for the project"
    _, _, why = await profile.pictures([src], {url: raw.replace("P52100080076", "")}, "Rohan Abhilasha", "P52100080076", fetch, tmp_path)
    assert why == "no builder page for the project"


async def test_google_is_asked_for_the_number_once_a_month_and_only_results_showing_it_count():
    store, asked = FakeStore(), []

    async def search(q):
        asked.append(q)
        return [{"type": "organic", "link": "https://site.example/a", "title": "Island of Joy P52100052259", "snippet": "", "position": 1},
                {"type": "organic", "link": "https://site.example/b", "title": "Something else", "snippet": "", "position": 2}]

    first = await webfacts.regno_results(store, GERA, search, NOW)
    assert asked == ['"P52100052259"'] and [r["link"] for r in first] == ["https://site.example/a"] and first[0]["by_regno"]
    await webfacts.regno_results(store, GERA, search, NOW + timedelta(days=29))
    assert len(asked) == 1
    await webfacts.regno_results(store, GERA, search, NOW + timedelta(days=31))
    assert len(asked) == 2


def test_a_result_found_by_the_number_is_read_though_it_uses_another_name():
    found = [{"type": "organic", "link": "https://site.example/a", "title": "Island of Joy", "snippet": "", "position": 1, "by_regno": True},
             {"type": "organic", "link": "https://other.example/b", "title": "Island of Joy", "snippet": "", "position": 2}]
    assert [s["url"] for s in webfacts.pick_sources(found, "Gera Island of Joy Project", ("gera",))] == ["https://site.example/a"]


async def test_a_page_that_failed_once_is_asked_again(monkeypatch):
    monkeypatch.setattr(webfacts, "RETRY_PAUSE", 0)
    calls = []

    def answer(request):
        calls.append(request.url)
        if len(calls) == 1:
            raise httpx.ConnectError("reset")
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<html>hello</html>")

    assert "hello" in await webfacts.fetch_page("https://builder.example/", transport=httpx.MockTransport(answer))
    assert len(calls) == 2


STEPS_OK = {k: {"ok": True, "at": NOW} for k in (*enrich.STEPS, "profile")}


def _top(**more) -> dict:
    return {"_id": "P52100056019", "regno": "P52100056019", "page_slug": "vj-indilife", "hot_score": 40, "locality": "kharadi",
            "completion_now": "2029-12-31", "enriched_at": NOW - timedelta(days=8),
            "enrichment": {"steps": STEPS_OK, "versions": dict(enrich.VERSIONS)}, **more}


def test_pictures_the_page_does_not_show_leave_a_project_unfinished():
    assert not enrich.complete(_top(profile={"photos": [{"source": "web"}, {"source": "ai"}]}))
    assert enrich.complete(_top(profile={"photos": [{"source": "builder"}]}))


def test_a_hot_project_without_photos_comes_back_after_a_week_not_every_day():
    now = NOW
    assert enrich._priority(_top(), now) is not None
    assert enrich._priority(_top(enriched_at=now - timedelta(days=2)), now) is None


def test_a_hot_project_read_by_an_older_step_is_read_again_even_while_its_text_rests():
    old = {"steps": STEPS_OK, "versions": {"web": 1, "profile": 3, "prices": 1}}
    d = _top(enrichment=old, enriched_at=NOW - timedelta(days=1), page_text="words", page_text_at=NOW - timedelta(days=1),
             prices={"rows": [{"bhk": 2}]}, promoter="X Developers")
    assert enrich._priority(d, NOW) is not None
