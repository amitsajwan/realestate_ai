"""Which places research runs for, where each is measured from, and which record a project page stands for."""
import pytest

from app.modules.neighbourhood import places
from tests.modules.neighbourhood.helpers import db_with, project


@pytest.mark.asyncio
async def test_places_in_search_come_first_then_the_busiest(monkeypatch):
    async def fake_places(db):
        return [{"slug": "moshi", "indexable": 0, "current": 90, "projects": 900},
                {"slug": "kharadi", "indexable": 4, "current": 30, "projects": 280},
                {"slug": "wagholi", "indexable": 9, "current": 60, "projects": 340}]
    monkeypatch.setattr(places.pages, "places", fake_places)
    assert await places.all_places(None) == ["wagholi", "kharadi", "moshi"]


@pytest.mark.asyncio
async def test_a_place_with_three_pins_is_measured_from_their_middle_and_an_outlier_barely_moves_it():
    db = await db_with(project("A", pin=(18.550, 73.940)), project("B", pin=(18.552, 73.942)),
                       project("C", pin=(18.551, 73.941)), project("D", pin=(18.700, 73.900)), project("E"))
    lat, lon, how = await places.centre_how(db, "kharadi")
    assert (lat, lon) == (18.5515, 73.9405) and "4 projects" in how


@pytest.mark.asyncio
async def test_a_covered_area_with_few_pins_uses_its_checked_middle():
    db = await db_with(project("A", place="wagholi", pin=(18.58, 73.98)), project("B", place="wagholi"))
    lat, lon, how = await places.centre_how(db, "wagholi")
    assert "pins" not in how and abs(lat - 18.58) < 0.1


@pytest.mark.asyncio
async def test_a_place_with_no_position_at_all_has_no_centre():
    db = await db_with(project("A", place="moshi"))
    assert await places.centre(db, "moshi") is None


@pytest.mark.asyncio
async def test_a_project_is_found_by_its_page_slug_or_an_old_one_with_its_place_slug_and_pin():
    db = await db_with(project("A", place="viman_nagar", pin=(18.56, 73.91), old_slugs=["old-a"]), project("B"))
    got = await places.project(db, "old-a")
    assert got["_id"] == "A" and got["place"] == "viman-nagar" and got["pin"] == (18.56, 73.91)
    plain = await places.project(db, "project-b")
    assert plain["pin"] is None and plain["place"] == "kharadi"
    assert await places.project(db, "nope") is None
