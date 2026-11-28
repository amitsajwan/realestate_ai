"""The place profile: homes MahaRERA shows finished by year, the checked places nearby (never a place of worship) and plain
sentences built from those numbers by code."""
import re

import pytest

from app.modules.neighbourhood.researchers import profile
from app.modules.neighbourhood.researchers.base import Context, ViewContext
from app.modules.neighbourhood.store import Store
from tests.modules.neighbourhood.helpers import NOW, db_with, project

WORSHIP = re.compile(r"temple|mandir|church|mosque|masjid|gurudwara|dargah", re.I)


async def _kharadi():
    return await db_with(project("A", pin=(18.550, 73.940), completion="2019-05-31", homes=200),
                         project("B", pin=(18.552, 73.942), completion="2019-12-31", homes=100),
                         project("C", pin=(18.551, 73.941), completion="2023-03-31", homes=150),
                         project("D", completion="2012-03-31", homes=90),       # before 2015
                         project("E", completion="2029-03-31", homes=400))      # still being built


@pytest.mark.asyncio
async def test_homes_finished_by_year_since_2015_and_nearby_places_from_checked_lists():
    db = await _kharadi()
    found = await profile.RESEARCHER.run(Context(db=db, store=Store(db), now=NOW, cfg=None), "kharadi")
    assert found.data["finished_by_year"] == [{"year": 2019, "homes": 300}, {"year": 2023, "homes": 150}]
    assert found.data["home_mix"] == []
    names = [n["name"] for n in found.data["nearby"]]
    assert "EON IT Park, Kharadi" in names and not any(WORSHIP.search(n) for n in names)
    block = profile.RESEARCHER.present(found.data, ViewContext(place="kharadi"))
    kinds = {n["kind"] for n in block["nearby"]}
    assert kinds <= {"it_park", "office", "college", "hospital", "government", "defence", "industrial", "market", "transport"}
    assert all(n["km"] <= 10 for n in block["nearby"]) and max(sum(1 for n in block["nearby"] if n["kind"] == k) for k in kinds) <= 3
    assert block["lines"][0] == "MahaRERA shows 450 homes in Kharadi finished since 2015, the most in 2019 (300)."
    assert any(line.startswith("The nearest large hospital we list is") for line in block["lines"])
    assert 2 <= len(block["lines"]) <= 4 and block["page_ready"] is True


def test_the_lines_say_the_biggest_home_size_when_a_mix_is_known():
    lines = profile.lines_of("Wagholi", [{"label": "2 BHK", "share": 0.58}, {"label": "1 BHK", "share": 0.3}], [], [], 2)
    assert lines == ["Most homes being built here are 2 BHK (58%).", "2 work hubs within 10 km."]


def test_a_profile_with_too_little_to_say_is_hidden():
    assert profile.RESEARCHER.present({"finished_by_year": [], "nearby": [], "centre": None}, ViewContext(place="moshi")) is None


def test_on_a_pinned_project_distances_are_from_its_pin():
    data = {"centre": [18.551, 73.941], "finished_by_year": [{"year": 2020, "homes": 10}],
            "nearby": [{"kind": "it_park", "name": "EON IT Park, Kharadi", "lat": 18.551815, "lon": 73.951153}]}
    at_pin = profile.RESEARCHER.present(data, ViewContext(place="kharadi", lat=18.5518, lon=73.9511, project={}))
    assert at_pin["nearby"][0]["km"] == 0.0 and at_pin["measured_from"] == "pin"


def test_a_place_on_two_lists_is_named_once():
    near = profile.nearby_of(18.566, 73.912)   # Viman Nagar: the airport is a hub and a landmark
    airports = [n for n in near if "Airport" in n["name"]]
    assert [a["name"] for a in airports] == ["Pune Airport (Lohegaon)"]
