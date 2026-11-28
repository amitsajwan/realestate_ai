"""What MahaRERA shows being built around a place: one row per project page, homes over the parts still being built, and a
project's own 2 km circle on its page when its pin has enough projects around it."""
import pytest

from app.modules.neighbourhood.researchers import being_built
from app.modules.neighbourhood.researchers.base import Context, ViewContext
from app.modules.neighbourhood.store import Store
from tests.modules.neighbourhood.helpers import NOW, db_with, project


def _ctx(db):
    return Context(db=db, store=Store(db), now=NOW, cfg=None)


async def _area():
    return await db_with(
        project("A", pin=(18.550, 73.940), homes=300, completion="2029-06-30"),
        project("B", pin=(18.552, 73.942), homes=120, completion="2027-03-31"),
        project("C", pin=(18.551, 73.941), homes=80, completion="2030-12-31"),
        project("D", homes=50, completion="2028-01-31"),                                   # filed here, no pin
        project("OLD", pin=(18.551, 73.940), homes=500, completion="2024-01-31"),          # finished
        project("FAR", place="wagholi", pin=(18.580, 73.980), homes=999),                  # another place, far
        project("NEXT", place="viman_nagar", pin=(18.556, 73.935), homes=60, completion="2028-08-31"),   # next door, pinned
        project("OFF", homes=40, building_totals={"units_residential": 0, "units_other": 40}),            # offices only
    )


@pytest.mark.asyncio
async def test_projects_being_built_in_and_around_a_place_with_their_homes_and_due_years():
    db = await _area()
    found = await being_built.RESEARCHER.run(_ctx(db), "kharadi")
    block = being_built.RESEARCHER.present(found.data, ViewContext(place="kharadi", now=NOW))
    assert block["projects"] == 5 and block["homes"] == 300 + 120 + 80 + 50 + 60
    assert (block["due_from"], block["due_to"]) == (2027, 2030)
    assert [b["slug"] for b in block["biggest"]] == ["project-a", "project-b", "project-c"]
    assert block["biggest"][0] == {"slug": "project-a", "name": "Project A", "homes": 300, "due": "2029-06"}
    assert block["measured_from"] == "place" and block["page_ready"] is True and block["within_km"] == 2.0


@pytest.mark.asyncio
async def test_registrations_of_one_project_are_one_row_on_its_primary_page():
    db = await db_with(project("T1", pin=(18.55, 73.94), homes=100, cluster_id="c", completion="2028-01-31"),
                       project("T2", homes=150, cluster_id="c", cluster_primary="T1", completion="2030-05-31"),
                       project("X", pin=(18.551, 73.941)), project("Y", pin=(18.552, 73.942)))
    found = await being_built.RESEARCHER.run(_ctx(db), "kharadi")
    t1 = next(r for r in found.data["rows"] if r[0] == "project-t1")
    assert t1[2] == 250 and t1[3] == "2030-05" and len(found.data["rows"]) == 3


@pytest.mark.asyncio
async def test_on_a_pinned_project_the_count_is_around_its_pin_without_itself():
    db = await _area()
    found = await being_built.RESEARCHER.run(_ctx(db), "kharadi")
    view = ViewContext(place="kharadi", lat=18.551, lon=73.941, project={"page_slug": "project-c"}, now=NOW)
    block = being_built.RESEARCHER.present(found.data, view)
    assert block["measured_from"] == "pin" and "project-c" not in [b["slug"] for b in block["biggest"]]
    assert block["projects"] == 3   # A, B and NEXT are pinned within 2 km; D has no pin


def test_too_few_projects_hide_the_block_and_a_finished_one_drops_out_between_reads():
    rows = [["a", "A", 10, "2026-10", 18.5, 73.9, 1], ["b", "B", 10, "2027-01", None, None, 1],
            ["c", "C", 10, "2028-01", None, None, 1]]
    assert being_built.RESEARCHER.present({"rows": rows, "centre": None}, ViewContext(place="kharadi", now=NOW)) is None
    assert being_built.RESEARCHER.present({"rows": rows, "centre": None}, ViewContext(place="kharadi"))["projects"] == 3


@pytest.mark.asyncio
async def test_a_place_with_nothing_being_built_stores_nothing():
    db = await db_with(project("OLD", completion="2020-01-31"))
    assert await being_built.RESEARCHER.run(_ctx(db), "kharadi") is None
