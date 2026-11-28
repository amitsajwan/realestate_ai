"""Work hubs: companies only from a hub's own tenant list (the last list kept when it cannot be read), homes for sale near each
hub, and a place's hubs within 10 km."""
import httpx
import pytest

from app.modules.neighbourhood import hubs
from app.modules.neighbourhood.researchers import jobs
from app.modules.neighbourhood.researchers.base import Context, ViewContext
from app.modules.neighbourhood.store import Store
from tests.modules.neighbourhood.helpers import NOW, db_with, project

EON = hubs.Hub(slug="eon-it-park-kharadi", name="EON IT Park, Kharadi", place="kharadi", lat=18.551815, lon=73.951153,
               companies_url="https://eon.example/tenants", companies_pattern=r'<li class="tenant">(.*?)</li>')
PAGE = ('<ul><li class="tenant">Barclays</li><li class="tenant"><b>Credit Suisse</b></li><li class="tenant">Barclays</li>'
        '<li class="tenant">  </li><li class="tenant">Mastercard &amp; Co</li></ul>')


def test_companies_are_read_from_the_hubs_own_list_once_each():
    assert hubs.parse_companies(PAGE, EON.companies_pattern) == ["Barclays", "Credit Suisse", "Mastercard & Co"]
    assert hubs.parse_companies(PAGE, "") == []


@pytest.mark.asyncio
async def test_each_hub_is_stored_with_its_companies_and_homes_near_it(monkeypatch):
    db = await db_with(project("NEAR", pin=(18.552, 73.945), completion="2029-06-30"),
                       project("FAR", place="wagholi", pin=(18.60, 74.05)),
                       project("DONE", pin=(18.553, 73.946), completion="2020-01-31"))
    monkeypatch.setattr(jobs, "HUBS", (EON,))
    seen = []

    def handler(r: httpx.Request) -> httpx.Response:
        seen.append(str(r.url))
        return httpx.Response(200, text=PAGE)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        ctx = Context(db=db, store=Store(db), now=NOW, cfg=None, http=http)
        found = await jobs.RESEARCHER.run(ctx, "_city")
    assert seen == ["https://eon.example/tenants"]
    assert found.data["hubs"]["eon-it-park-kharadi"]["companies_count"] == 3
    stored = await Store(db).hub("eon-it-park-kharadi")
    assert stored["data"]["companies"][:2] == ["Barclays", "Credit Suisse"]
    assert stored["data"]["companies_source"]["url"] == EON.companies_url
    assert [h["slug"] for h in stored["data"]["homes_nearby"]] == ["project-near"]
    assert stored["data"]["homes_nearby"][0]["possession"] == "2029-06"


@pytest.mark.asyncio
async def test_a_tenant_page_that_fails_keeps_the_last_list_and_a_hub_without_one_has_none(monkeypatch):
    db = await db_with()
    store = Store(db)
    await store.put_hub(EON.slug, {"companies": ["Barclays"], "companies_source": {"name": "x", "read_on": "2026-08-01"}}, [], NOW)
    plain = hubs.Hub(slug="magarpatta-city", name="Magarpatta Cybercity", place="hadapsar", lat=18.513, lon=73.924)
    monkeypatch.setattr(jobs, "HUBS", (EON, plain))
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(503))) as http:
        await jobs.RESEARCHER.run(Context(db=db, store=store, now=NOW, cfg=None, http=http), "_city")
    assert (await store.hub(EON.slug))["data"]["companies"] == ["Barclays"]
    assert (await store.hub("magarpatta-city"))["data"]["companies"] == []


def test_a_place_shows_its_work_hubs_within_10_km_with_their_first_companies():
    data = {"hubs": {"eon-it-park-kharadi": {"companies": [f"C{i}" for i in range(12)]}}}
    block = jobs.RESEARCHER.present(data, ViewContext(place="kharadi", lat=18.551, lon=73.941))
    first = block["hubs"][0]
    assert first["hub_slug"] in ("eon-it-park-kharadi", "world-trade-center-kharadi")
    eon = next(h for h in block["hubs"] if h["hub_slug"] == "eon-it-park-kharadi")
    assert eon["companies"] == [f"C{i}" for i in range(8)] and eon["companies_count"] == 12
    assert all(h["km"] <= 10 for h in block["hubs"]) and "pune-airport" not in [h["hub_slug"] for h in block["hubs"]]
    assert block["page_ready"] is True
    assert jobs.RESEARCHER.present(data, ViewContext(place="baramati", lat=18.15, lon=74.58)) is None


def test_every_hub_in_the_list_stands_in_a_real_place_and_has_a_checked_position():
    from app.core import pune_places
    assert len(hubs.HUBS) >= 10
    for h in hubs.HUBS:
        assert h.place.replace("-", "_") in pune_places.BY_KEY, h.slug
        assert 18.3 < h.lat < 18.9 and 73.6 < h.lon < 74.1 and h.how, h.slug
