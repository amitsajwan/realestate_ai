"""On the ground (areastats/sitevisits.py): a person's dated, signed note from the site, the one thing on a project page no
program can make. Checked by rules before it is saved, kept append-only, shown while it is recent."""
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.core.auth_backend import current_active_user
from app.modules.admin import router as ar
from app.modules.admin.service import AdminService
from app.modules.areastats import pages, sitevisits

from ..fakes import FakeDb

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)
TODAY = NOW.date()
NOTE = ("The approach from the Kharadi bypass is a two-lane road, about 9 m wide, with no footpath for the last 400 m. "
        "Tower A has its slab up to the 21st floor and tower B to the 14th; the clubhouse is still a pit. The towers on the east "
        "side stand about 12 m apart, so the lower flats there face the next tower. At 6 pm the gate road backs up behind the "
        "school buses. The sample flat is on the ground floor and matches the carpet areas on the price sheet.")
REC = {"_id": "PR1260002502426", "regno": "PR1260002502426", "page_slug": "godrej-ivara-pune", "name": "GODREJ IVARA"}


async def seeded(doc=None):
    db = FakeDb()
    await db.get_collection("projects").insert_one(dict(doc or REC))
    return db


async def record(db):
    return await db.get_collection("projects").find_one({"_id": REC["_id"]})


def test_a_note_needs_enough_words_and_no_phone_link_hype_or_price_talk():
    assert sitevisits.problems(NOTE, TODAY, TODAY) == []
    short = sitevisits.problems("Nice site, good road.", TODAY, TODAY)
    assert short and short[0].startswith("Write at least 60 words")
    found = " ".join(sitevisits.problems(NOTE + " Call 9876543210 or see example.com. The best project; prices will rise.", TODAY, TODAY))
    assert "phone numbers" in found and "web addresses" in found and '"best"' in found and "prices may do" in found


def test_a_visit_day_in_the_future_or_over_a_year_old_is_refused():
    assert sitevisits.problems(NOTE, TODAY + timedelta(days=1), TODAY) == ["The visit day is in the future"]
    assert "moved on" in sitevisits.problems(NOTE, TODAY - timedelta(days=400), TODAY)[0]


async def test_a_note_is_found_by_regno_or_page_address_and_kept_append_only():
    db = await seeded()
    await sitevisits.add(db, "pr1260002502426", NOTE, date(2026, 11, 18), None, "OWNER", NOW)
    await sitevisits.add(db, "https://avasetu.in/projects/godrej-ivara-pune/", NOTE + " Second look.", date(2026, 11, 19), "Rahul, House Deal", "OWNER", NOW + timedelta(hours=1))
    visits = (await record(db))["site_visits"]
    assert [v["visited_on"] for v in visits] == ["2026-11-18", "2026-11-19"]
    assert visits[0]["by"] == "Avasetu team" and visits[1]["by"] == "Rahul, House Deal"   # a note without a name is the team's own
    with pytest.raises(sitevisits.VisitError, match="No project"):
        await sitevisits.add(db, "P00000000000", NOTE, TODAY, None, "OWNER", NOW)


async def test_the_page_shows_the_newest_visit_and_a_withdrawn_one_stays_on_the_record():
    db = await seeded()
    await sitevisits.add(db, REC["_id"], NOTE, date(2026, 11, 18), None, "OWNER", NOW)
    await sitevisits.add(db, REC["_id"], NOTE + " Later.", date(2026, 11, 19), None, "OWNER", NOW + timedelta(hours=1))
    doc = await record(db)
    assert sitevisits.public(doc, TODAY)["visited_on"] == "2026-11-19"
    await sitevisits.withdraw(db, REC["_id"], (NOW + timedelta(hours=1)).isoformat(), "OWNER", NOW + timedelta(hours=2))
    doc = await record(db)
    assert len(doc["site_visits"]) == 2 and doc["site_visits"][1]["withdrawn"] is True
    assert sitevisits.public(doc, TODAY) == {"visited_on": "2026-11-18", "by": "Avasetu team", "text": NOTE}


def test_a_visit_over_a_year_old_leaves_the_page():
    doc = {**REC, "site_visits": [{"visited_on": "2026-11-18", "by": "House Deal", "text": NOTE, "at": NOW}]}
    assert sitevisits.public(doc, date(2027, 11, 19)) is None


def test_a_shown_visit_dates_the_page_and_goes_out_in_its_view():
    doc = {**REC, "page_text_at": NOW - timedelta(days=10),
           "site_visits": [{"visited_on": TODAY.isoformat(), "by": "House Deal", "text": NOTE, "at": NOW}]}
    assert pages.page_updated(doc) == NOW.isoformat()
    assert pages.view(doc, [])["site_visit"] == {"visited_on": TODAY.isoformat(), "by": "House Deal", "text": NOTE}
    assert pages.view(REC, [])["site_visit"] is None


async def test_the_owner_saves_and_lists_visits_through_the_admin_routes():
    db = await seeded()
    app = FastAPI()
    app.include_router(ar.router, prefix="/admin")
    app.dependency_overrides[ar.get_service] = lambda: AdminService(db, now=lambda: NOW)
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="OWNER", is_superuser=True)
    ar.limiter.hits.clear()
    c = TestClient(app)
    bad = c.post("/admin/site-visits", json={"project": REC["_id"], "visited_on": "2026-11-19", "text": "Too short."})
    assert bad.status_code == 422 and "at least 60 words" in bad.json()["detail"]
    ok = c.post("/admin/site-visits", json={"project": "godrej-ivara-pune", "visited_on": "2026-11-19", "text": NOTE})
    assert ok.status_code == 200
    assert [(x["slug"], x["visited_on"], x["withdrawn"]) for x in ok.json()["items"]] == [("godrej-ivara-pune", "2026-11-19", False)]
    off = c.post("/admin/site-visits/withdraw", json={"project": REC["_id"], "at": ok.json()["items"][0]["at"]})
    assert off.status_code == 200 and off.json()["items"][0]["withdrawn"] is True
