"""What the site reads: the place and project views in the shapes of frontend/lib/site/research.ts, the hub pages, and the chat's
passages."""
from datetime import timedelta

import pytest

from app.modules.neighbourhood import views
from app.modules.neighbourhood.store import Store
from tests.modules.neighbourhood.helpers import NOW, db_with, project

COMMUTE = {"rows": [{"hub": "EON IT Park, Kharadi", "hub_slug": "eon-it-park-kharadi", "km": 3.2, "am": [8, 12], "pm": [9, 14]},
                    {"hub": "Pune Airport (Lohegaon)", "hub_slug": "pune-airport", "km": 9.0, "am": [20, 30], "pm": [22, 35]},
                    {"hub": "Magarpatta Cybercity", "hub_slug": "magarpatta-city", "km": 8.0, "am": [18, 28], "pm": [20, 33]}]}
SRC = [{"name": "Google Maps (Routes API), typical weekday traffic", "read_on": "2026-11-20"}]


async def _kharadi():
    db = await db_with(project("A", pin=(18.550, 73.940)), project("B", pin=(18.552, 73.942)), project("C", pin=(18.551, 73.941)))
    await Store(db).put("commute", "kharadi", COMMUTE, SRC, NOW - timedelta(days=8))
    return db


@pytest.mark.asyncio
async def test_a_place_view_has_the_contract_fields_and_each_block_says_if_it_is_page_ready():
    db = await _kharadi()
    out = await views.area_view(db, "kharadi", NOW)
    assert set(out) == {"place", "place_name", "blocks", "changes", "pages"}
    assert out["place_name"] == "Kharadi" and out["pages"] == {"schools": False, "commute": True, "rent": False}
    block = out["blocks"]["commute"]
    assert block["page_ready"] is True and block["sources"] == SRC and block["updated"] == "2026-11-20"
    assert set(block["rows"][0]) >= {"hub", "km", "am", "pm"}


@pytest.mark.asyncio
async def test_a_project_view_is_measured_from_its_pin_and_names_its_place():
    db = await _kharadi()
    out = await views.project_view(db, "project-a", NOW)
    assert set(out) == {"slug", "place", "place_name", "pinned", "blocks", "changes"}
    assert out["pinned"] is True and out["place"] == "kharadi"
    assert "pin_km" in out["blocks"]["commute"]["rows"][0]


@pytest.mark.asyncio
async def test_a_hub_page_has_drive_times_from_every_place_that_measured_it():
    db = await _kharadi()
    await Store(db).put_hub("eon-it-park-kharadi", {"companies": [], "homes_nearby": [{"slug": "project-a", "name": "Project A",
                                                                                       "km": 1.1}]}, [], NOW)
    page = await views.hub_view(db, "eon-it-park-kharadi")
    assert page["commute_from"] == [{"place": "kharadi", "name": "Kharadi", "am": [8, 12], "pm": [9, 14]}]
    assert page["companies"] == [] and page["kind"] == "it_park" and page["updated"] == "2026-11-28"
    assert "Project A" in page["summary"] and "Kharadi" in page["summary"]
    assert set(page) >= {"slug", "name", "place", "kind", "summary", "companies", "commute_from", "homes_nearby", "changes",
                         "sources", "updated"}
    assert await views.hub_view(db, "nowhere") is None
    assert len(await views.hubs_view(db)) >= 10


@pytest.mark.asyncio
async def test_the_chat_gets_one_short_passage_per_kind_of_fact_for_each_place():
    db = await _kharadi()
    got = await views.knowledge_passages(db)
    assert [p["id"] for p in got] == ["research:kharadi:commute"]
    p = got[0]
    assert p["title"] == "Kharadi: drive times to work" and p["url"].endswith("/projects/area/kharadi")
    assert "EON IT Park, Kharadi 8 to 12 min at 9 am" in p["text"] and p["area"] == "kharadi"


def test_passages_say_each_block_the_way_its_page_does():
    rent = {"month": "2026-11", "rows": [{"bhk": "2 BHK", "low": 22000, "median": 25000, "high": 30000, "listings": 40}]}
    assert views.passage_lines("rent", rent, "Kharadi") == [
        "Asked rent in Kharadi in 2026-11, from listings (not what was paid): 2 BHK Rs 22,000 to Rs 30,000 a month "
        "(median Rs 25,000, 40 listings)."]
    schools = {"total_within_km": {"km": 3, "count": 14, "by_board": {"CBSE": 9, "ICSE": 5}}}
    assert views.passage_lines("schools", schools, "Kharadi") == [
        "14 schools on the official board lists within 3 km of the Kharadi centre (CBSE 9, ICSE 5)."]
    assert views.passage_lines("jobs", {}, "Kharadi") == []


@pytest.mark.asyncio
async def test_the_sitemap_lists_only_the_place_sub_pages_that_are_page_ready():
    db = await _kharadi()
    await Store(db).put("commute", "wagholi", {"rows": COMMUTE["rows"][:2]}, SRC, NOW)   # two hubs: not a page yet
    assert await views.ready_pages(db, NOW) == [{"place": "kharadi", "kind": "commute", "updated": "2026-11-20"}]


@pytest.mark.asyncio
async def test_a_hub_is_ready_with_three_companies_or_drive_times_from_three_places():
    db = await _kharadi()
    cards = {c["slug"]: c for c in await views.hubs_view(db)}
    assert cards["eon-it-park-kharadi"]["ready"] is False and cards["eon-it-park-kharadi"]["updated"] == ""
    for place in ("wagholi", "viman-nagar"):
        await Store(db).put("commute", place, COMMUTE, SRC, NOW)
    await Store(db).put_hub("magarpatta-city", {"companies": ["A", "B", "C"]}, [], NOW)
    cards = {c["slug"]: c for c in await views.hubs_view(db)}
    assert cards["eon-it-park-kharadi"]["ready"] is True and cards["magarpatta-city"]["updated"] == "2026-11-28"
    assert (await views.hub_view(db, "eon-it-park-kharadi"))["page_ready"] is True
    assert (await views.hub_view(db, "chakan-midc"))["page_ready"] is False
