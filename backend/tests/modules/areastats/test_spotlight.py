"""The hot projects banner: the owner's picks first (area picks on that area's pages), then hot projects; only live indexable pages."""
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.areastats import router as ar
from app.modules.areastats import spotlight, upcoming
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.utc)
PAGE = {"promoter": "Some Builder", "completion_now": "2029-10-30"}
UPCOMING = {"slug": "esbee-upper-kharadi", "name": "Esbee Upper Kharadi", "builder": "Esbee Realty", "area": "upper_kharadi",
            "summary": "An upcoming project the builder has announced and MahaRERA has not registered yet.",
            "note": "2 & 3 BHK · coming soon", "sources": [{"name": "Builder's blog", "read_on": "2026-10-23"}]}


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, slug, locality, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": slug.replace("-", " ").title(), "locality": locality,
                                         "page_slug": slug, "news": [], **PAGE, **extra})
    return db


async def world():
    return await seeded(("P1", "camelot-kharadi", "kharadi", {"hot_score": 80}),
                        ("P2", "quiet-kharadi", "kharadi", {}),
                        ("P3", "busy-wagholi", "wagholi", {"hot_score": 60}),
                        ("P4", "cold-wagholi", "wagholi", {"hot_score": 5}),
                        ("P5", "thin-baner", "baner", {"hot_score": 90, "completion_now": None}))   # noindex: never shown


async def test_with_no_picks_the_strip_is_the_hot_indexable_projects():
    db = await world()
    got = await spotlight.public(db, now=NOW)
    assert [e["slug"] for e in got] == ["camelot-kharadi", "busy-wagholi"]   # cold and noindex ones left out
    assert got[0]["fact"] and got[0]["source"] == "MahaRERA" and got[0]["picked"] is False and "hot_score" not in got[0]
    assert got[0]["regnos"] == ["P1"]


async def test_an_areas_pages_show_its_own_hot_projects_first():
    db = await world()
    assert [e["slug"] for e in await spotlight.public(db, area="wagholi", now=NOW)] == ["busy-wagholi", "camelot-kharadi"]


async def test_picks_come_first_area_picks_only_on_their_area_and_end_on_their_date():
    db = await world()
    await spotlight.set_config(db, {"auto": True, "items": [
        {"slug": "quiet-kharadi", "area": "kharadi", "note": "Tower C launched"},
        {"slug": "/projects/cold-wagholi/", "note": "Possession this month"},
        {"slug": "busy-wagholi", "until": "2026-10-01"},   # ended
    ]}, "owner", NOW)
    on_kharadi = await spotlight.public(db, area="kharadi", now=NOW)
    assert [e["slug"] for e in on_kharadi] == ["quiet-kharadi", "cold-wagholi", "camelot-kharadi", "busy-wagholi"]
    assert on_kharadi[0]["note"] == "Tower C launched" and on_kharadi[0]["picked"] is True
    elsewhere = await spotlight.public(db, area="baner", now=NOW)
    assert elsewhere[0]["slug"] == "cold-wagholi" and "quiet-kharadi" not in [e["slug"] for e in elsewhere]


async def test_auto_off_shows_only_the_picks():
    db = await world()
    await spotlight.set_config(db, {"auto": False, "items": [{"slug": "quiet-kharadi"}]}, "owner", NOW)
    assert [e["slug"] for e in await spotlight.public(db, now=NOW)] == ["quiet-kharadi"]


@pytest.mark.parametrize("item,word", [({"slug": "no-such-page"}, "No project page"), ({"slug": "thin-baner"}, "not in search"),
                                       ({"slug": "quiet-kharadi", "area": "mumbai"}, "area"),
                                       ({"slug": "quiet-kharadi", "until": "next week"}, "not a date")])
async def test_settings_that_would_show_a_broken_link_are_refused(item, word):
    db = await world()
    with pytest.raises(spotlight.SpotlightError, match=word):
        await spotlight.set_config(db, {"items": [item]}, "owner", NOW)


async def test_the_public_endpoint_serves_the_strip_with_a_cache_header():
    db = await world()
    app = FastAPI()
    app.include_router(ar.public_router, prefix="/api/v1/public")
    app.dependency_overrides[ar.get_db] = lambda: db
    r = TestClient(app).get("/api/v1/public/register/spotlight", params={"area": "wagholi"})
    assert r.status_code == 200 and r.json()[0]["slug"] == "busy-wagholi" and "max-age" in r.headers["cache-control"]


async def test_a_picked_upcoming_project_shows_as_not_registered_and_auto_never_adds_one():
    db = await world()
    await upcoming.put(db, UPCOMING, NOW)
    await upcoming.put(db, {**UPCOMING, "slug": "other-upcoming"}, NOW)
    await spotlight.set_config(db, {"auto": True, "items": [{"slug": "/projects/upcoming/esbee-upper-kharadi/"}]}, "owner", NOW)
    got = await spotlight.public(db, now=NOW)
    assert [e["slug"] for e in got] == ["upcoming/esbee-upper-kharadi", "camelot-kharadi", "busy-wagholi"]
    assert got[0]["fact"] == "coming soon, not yet registered with MahaRERA" and got[0]["note"] == "2 & 3 BHK · coming soon"
    assert got[0]["area"] == "Upper Kharadi" and got[0]["regnos"] == [] and got[0]["picked"] is True


async def test_a_hidden_or_unknown_upcoming_project_cannot_be_picked_and_drops_off_the_strip():
    db = await world()
    with pytest.raises(spotlight.SpotlightError, match="No upcoming project"):
        await spotlight.set_config(db, {"items": [{"slug": "upcoming/esbee-upper-kharadi"}]}, "owner", NOW)
    await upcoming.put(db, UPCOMING, NOW)
    await spotlight.set_config(db, {"items": [{"slug": "upcoming/esbee-upper-kharadi"}]}, "owner", NOW)
    await upcoming.put(db, {**UPCOMING, "status": "hidden"}, NOW)
    assert "upcoming/esbee-upper-kharadi" not in [e["slug"] for e in await spotlight.public(db, now=NOW)]
