"""Asked rent by flat size: the portals' pages read from saved copies, flats only, one flat listed twice counted once, outliers
out, the 10-listing gate, the Serper cap when a place's page cannot be guessed, and a failed month keeping the last good rows."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.modules.areastats import websearch
from app.modules.neighbourhood import places, rent_sources, runner
from app.modules.neighbourhood.config import Config
from app.modules.neighbourhood.researchers import Context, ViewContext
from app.modules.neighbourhood.researchers import rent
from app.modules.neighbourhood.store import Store
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 28, 9, 0, tzinfo=timezone.utc)
FIX = Path(__file__).parent / "fixtures"


def page(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def l(rent_, bhk=2, source="magicbricks", sqft=None, society="", lid=None, lat=None, lon=None):
    out = {"source": source, "id": lid or f"{source}-{rent_}-{bhk}-{sqft}-{society}", "rent": rent_, "bhk": bhk, "sqft": sqft,
           "society": society}
    if lat is not None:
        out.update({"lat": lat, "lon": lon})
    return out


# --- reading the portals -------------------------------------------------------------------------------------------------------

def test_magicbricks_gives_rent_size_area_society_and_position():
    got = rent_sources.parse_magicbricks(page("magicbricks_2bhk.html"))
    assert len(got) == 6
    first = got[0]
    assert first == {"source": "magicbricks", "id": "87576065", "rent": 46000, "bhk": 2, "sqft": 1100,
                     "society": "Sancheti Mount N Glory", "lat": 18.562867, "lon": 73.950571}
    assert all(x["bhk"] in (1, 2, 3) for x in got)       # the 4 and 5 BHK and the studio on the page are left out


def test_nobroker_gives_listings_from_its_flight_data_and_positions_only_when_exact():
    got = rent_sources.parse_nobroker(page("nobroker.html"))
    assert len(got) == 11 and got[0]["rent"] == 25000 and got[0]["bhk"] == 1 and got[0]["society"] == "NG Rathi Vrundavan"
    assert all(g["bhk"] in (1, 2, 3) for g in got)        # the 4+ BHK and the 1 RK in the saved page are out


def test_square_yards_joins_each_flat_to_its_rent():
    got = rent_sources.parse_squareyards(page("squareyards.html"))
    assert len(got) == 6
    assert got[0]["rent"] == 60000 and got[0]["bhk"] == 3 and got[0]["sqft"] == 1020
    assert got[0]["society"] == "Majestique Marbella Phase 1" and "lat" in got[0]


def test_pg_rooms_offices_and_houses_are_not_flats():
    html = page("magicbricks_2bhk.html")
    assert rent_sources.parse_magicbricks(html.replace('"Apartment"', '"Office Space"')) == []
    assert rent_sources.parse_magicbricks(html.replace('"transType": "Rent"', '"transType": "Sale"')) == []
    nb = page("nobroker.html")
    assert rent_sources.parse_nobroker(nb.replace('sharedAccomodation\\": false', 'sharedAccomodation\\": true')) == []
    assert rent_sources.NOT_A_FLAT.search("PG for working women") and rent_sources.NOT_A_FLAT.search("Furnished room")
    assert not rent_sources.NOT_A_FLAT.search("2 BHK flat with 2 bedrooms")


def test_place_words_try_the_portals_spelling_after_ours():
    assert rent_sources.place_words("hinjawadi") == ["hinjawadi", "hinjewadi"]
    assert rent_sources.place_words("upper_kharadi") == ["upper-kharadi"]


# --- counting ---------------------------------------------------------------------------------------------------------------------

def test_one_flat_on_two_portals_counts_once():
    a = l(40000, sqft=1000, society="Gera Planet Of Joy", source="magicbricks")
    b = l(40000, sqft=1010, society="Gera Planet of Joy Phase 2", source="nobroker")
    c = l(40000, sqft=1300, society="Gera Planet Of Joy", source="squareyards")   # another flat: 300 sq ft bigger
    d = l(40000, source="squareyards")                                            # nothing to go on but rent: kept
    assert rent_sources.dedupe([a, b, c, d]) == [a, c, d]
    assert rent_sources.dedupe([a, dict(a)]) == [a]                               # the same id twice on one portal


def test_rents_far_from_the_sizes_median_are_dropped():
    kept = rent_sources.without_outliers([l(r) for r in (30000, 32000, 35000, 36000, 5000, 200000)])
    assert sorted(x["rent"] for x in kept) == [30000, 32000, 35000, 36000]


def test_rows_give_quartiles_rounded_and_counts_by_source():
    listings = [l(20000 + 1000 * i, source="magicbricks" if i % 2 else "nobroker") for i in range(11)]
    rows = rent_sources.rows(listings + [l(15000, bhk=1)])
    two = next(r for r in rows if r["bhk"] == "2 BHK")
    assert two == {"bhk": "2 BHK", "low": 22500, "median": 25000, "high": 27500, "listings": 11,
                   "by_source": {"nobroker": 6, "magicbricks": 5}}
    assert next(r for r in rows if r["bhk"] == "1 BHK")["listings"] == 1


def test_yield_is_a_years_median_rent_over_the_median_asking_price_and_never_absurd():
    rows = [{"bhk": "2 BHK", "median": 30000}, {"bhk": "3 BHK", "median": 40000}, {"bhk": "1 BHK", "median": 20000}]
    out = rent.with_yield(rows, {"2 BHK": 9_000_000, "3 BHK": 200_000})
    assert out[0]["yield_pct"] == 4.0
    assert "yield_pct" not in out[1] and "yield_pct" not in out[2]


# --- what a page shows ------------------------------------------------------------------------------------------------------------

def row(bhk, n):
    return {"bhk": bhk, "low": 20000, "median": 25000, "high": 30000, "listings": n, "by_source": {"magicbricks": n}}


def test_a_size_with_fewer_than_10_listings_is_not_shown_and_none_hides_the_block():
    assert rent.RESEARCHER.present({"month": "2026-11", "rows": [row("1 BHK", 9)]}, ViewContext(place="kharadi")) is None
    block = rent.RESEARCHER.present({"month": "2026-11", "rows": [row("1 BHK", 9), row("2 BHK", 10)]},
                                    ViewContext(place="kharadi"))
    assert block == {"month": "2026-11", "rows": [{"bhk": "2 BHK", "low": 20000, "median": 25000, "high": 30000, "listings": 10}],
                     "page_ready": False}


def test_the_rent_page_is_ready_with_two_sizes_shown():
    block = rent.RESEARCHER.present({"month": "2026-11", "rows": [row("2 BHK", 12), row("3 BHK", 10)]}, ViewContext(place="x"))
    assert block["page_ready"] is True


def test_a_project_page_says_how_many_listings_are_near_its_pin():
    pts = [[2, 30000, 18.55 + i * 0.001, 73.94] for i in range(12)] + [[2, 30000, 18.70, 73.94]]
    data = {"month": "2026-11", "rows": [row("2 BHK", 13)], "points": pts}
    near = rent.RESEARCHER.present(data, ViewContext(place="kharadi", lat=18.555, lon=73.94, project={"slug": "p"}))
    assert near["within_km"] == 2.0 and near["listings_within_km"] == 12 and near["rows"][0]["listings"] == 13
    far = rent.RESEARCHER.present(data, ViewContext(place="kharadi", lat=18.80, lon=73.94, project={"slug": "p"}))
    assert "within_km" not in far
    assert "within_km" not in rent.RESEARCHER.present(data, ViewContext(place="kharadi", lat=18.555, lon=73.94))


# --- a run --------------------------------------------------------------------------------------------------------------------

class Portals:
    def __init__(self, pages):
        self.pages, self.asked = pages, []

    async def __call__(self, url):
        self.asked.append(url)
        return self.pages.get(url)


@pytest.fixture
def quiet(monkeypatch):
    async def none_agents(db, place):
        return []

    async def no_prices(db, place):
        return {}
    monkeypatch.setattr(rent, "agent_rents", none_agents)
    monkeypatch.setattr(rent, "sale_prices", no_prices)
    rent._searches.update({"cycle": None, "spent": 0})


def ctx(db, now=NOW, **cfg):
    return Context(db=db, store=Store(db), now=now, cfg=Config(**{"serper_key": "s", "rent_searches_per_run": 10, **cfg}))


def kharadi_pages(word="kharadi"):
    return {rent_sources.magicbricks_url(word, 2): page("magicbricks_2bhk.html"),
            rent_sources.nobroker_url(word): page("nobroker.html"),
            rent_sources.squareyards_url(word): page("squareyards.html")}


@pytest.mark.asyncio
async def test_a_run_reads_the_three_portals_and_keeps_the_words_that_worked(quiet, monkeypatch):
    web = Portals(kharadi_pages())
    monkeypatch.setattr(rent, "fetch", web)
    found = await rent.RESEARCHER.run(ctx(FakeDb()), "kharadi")
    two = next(r for r in found.data["rows"] if r["bhk"] == "2 BHK")
    assert set(two["by_source"]) == {"magicbricks", "nobroker", "squareyards"}
    assert found.data["month"] == "2026-11" and found.data["words"] == {"magicbricks": "kharadi", "nobroker": "kharadi",
                                                                         "squareyards": "kharadi"}
    assert [s["name"] for s in found.sources] == ["MagicBricks rent listings", "NoBroker rent listings",
                                                  "Square Yards rent listings"]
    assert all(s["read_on"] == "2026-11-28" for s in found.sources)
    assert found.data["points"] and all(len(p) == 4 for p in found.data["points"])


@pytest.mark.asyncio
async def test_a_place_the_portals_spell_otherwise_is_found_by_its_alias_without_a_search(quiet, monkeypatch):
    web = Portals(kharadi_pages("hinjewadi"))
    monkeypatch.setattr(rent, "fetch", web)
    called = []
    monkeypatch.setattr(websearch, "serper", lambda key, transport=None: called.append(key))
    found = await rent.RESEARCHER.run(ctx(FakeDb()), "hinjawadi")
    assert found.data["words"]["magicbricks"] == "hinjewadi" and not called
    assert rent_sources.magicbricks_url("hinjawadi", 1) in web.asked


@pytest.mark.asyncio
async def test_a_page_no_guess_finds_costs_one_search_within_the_cycles_cap(quiet, monkeypatch):
    web = Portals(kharadi_pages("kharadi-east"))
    monkeypatch.setattr(rent, "fetch", web)
    searched = []

    def serper(key, transport=None):
        async def search(q):
            searched.append(q)
            return [{"link": "https://www.magicbricks.com/flats-for-rent-in-kharadi-east-pune-pppfr"},
                    {"link": "https://www.nobroker.in/flats-for-rent-in-kharadi-east_pune"},
                    {"link": "https://www.squareyards.com/rent/property-for-rent-in-kharadi-east-pune"}]
        return search
    monkeypatch.setattr(websearch, "serper", serper)
    found = await rent.RESEARCHER.run(ctx(FakeDb(), rent_searches_per_run=1), "khr")
    assert searched == ["flats for rent in Khr Pune"]
    assert found.data["words"] == {"magicbricks": "kharadi-east", "nobroker": "kharadi-east", "squareyards": "kharadi-east"}
    with pytest.raises(RuntimeError):            # the cycle's one search is spent: the next place finds nothing
        await rent.RESEARCHER.run(ctx(FakeDb(), rent_searches_per_run=1), "other")
    assert len(searched) == 1


@pytest.mark.asyncio
async def test_agents_rent_listings_count_and_yield_comes_from_area_prices(monkeypatch):
    rent._searches.update({"cycle": None, "spent": 0})
    monkeypatch.setattr(rent, "fetch", Portals({}))

    async def agents(db, place):
        return [l(30000 + 500 * i, source="avasetu", lid=str(i)) for i in range(10)]

    async def prices(db, place):
        return {"2 BHK": 9_000_000}
    monkeypatch.setattr(rent, "agent_rents", agents)
    monkeypatch.setattr(rent, "sale_prices", prices)
    found = await rent.RESEARCHER.run(ctx(FakeDb(), serper_key=""), "kharadi")
    assert found.data["rows"][0]["by_source"] == {"avasetu": 10}
    assert found.data["rows"][0]["yield_pct"] == round(found.data["rows"][0]["median"] * 12 / 9_000_000 * 100, 1)
    assert [s["name"] for s in found.sources] == ["Avasetu agents' rent listings",
                                                  "Asking prices of new projects (Avasetu project pages)"]


@pytest.mark.asyncio
async def test_a_month_no_portal_answers_keeps_the_last_good_rows(quiet, monkeypatch):
    db = FakeDb()

    async def all_places(db_):
        return ["kharadi"]
    monkeypatch.setattr(places, "all_places", all_places)
    monkeypatch.setattr(runner, "REGISTRY", (rent.RESEARCHER,))
    monkeypatch.setattr(rent, "fetch", Portals(kharadi_pages()))
    await runner.run_once(db, NOW, http=object(), cfg=Config(serper_key=""))
    good = (await Store(db).get("rent", "kharadi"))["data"]["rows"]
    monkeypatch.setattr(rent, "fetch", Portals({}))
    counts = await runner.run_once(db, NOW + timedelta(days=31), http=object(), cfg=Config(serper_key=""))
    doc = await Store(db).get("rent", "kharadi")
    assert counts["rent"]["failed"] == 1 and doc["ok"] is False and doc["data"]["rows"] == good
