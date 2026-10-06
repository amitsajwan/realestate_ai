"""Our own page for every register project: stable slugs, facts-only paragraph, noindex until the details are in, the lookup."""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.areastats import pages
from app.modules.areastats import router as ar
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

READ = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)
FULL = {"promoter": "Rohan Builders", "completion_now": "2029-10-30", "completion_at_registration": "2028-12-31", "units_total": 416,
        "units_booked": 244, "details_checked_at": READ, "details_ok": True, "last_modified": "2026-09-28",
        "source_url": "https://maharerait.maharashtra.gov.in/public/project/view/80076"}


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, name, locality, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": name, "locality": locality, "pincode": "412207", "news": [], **extra})
    return db, store


async def test_slugs_are_readable_given_once_and_unique():
    db, store = await seeded(("P1", "Rohan Abhilasha 4", "wagholi", {}), ("P2", "Rohan Abhilasha 4", "wagholi", {}),
                             ("P3", "Wagholi Heights", "wagholi", {}), ("P4", "Far Away", None, {}))
    assert await pages.assign_all(store) == 3   # P4 is not ours and not watched: no page
    assert (await store.project("P1"))["page_slug"] == "rohan-abhilasha-4-wagholi"
    assert (await store.project("P2"))["page_slug"] == "rohan-abhilasha-4-wagholi-p2"   # clash: registration number's tail
    assert (await store.project("P3"))["page_slug"] == "wagholi-heights"               # the area word is not repeated
    await store.set_project("P1", name="Renamed Later")
    assert await pages.assign_all(store) == 0 and (await store.project("P1"))["page_slug"] == "rohan-abhilasha-4-wagholi"


async def test_the_paragraph_says_only_what_the_record_says():
    db, store = await seeded(("P52100080076", "Rohan Abhilasha 4", "wagholi", FULL))
    text = pages.paragraph(await store.project("P52100080076"))
    assert text.startswith("Rohan Abhilasha 4 is a project by Rohan Builders in Wagholi, Pune, registered with MahaRERA as P52100080076.")
    assert "filed completion date is 30 Oct 2029; at registration it was 31 Dec 2028" in text
    assert "244 of 416 homes were booked when we read the record on 3 Oct 2026" in text
    assert "₹" not in text and "lakh" not in text and "best" not in text.lower()
    thin = pages.paragraph({"_id": "P9", "name": "New One", "locality": "baner"})
    assert thin.startswith("New One is a project in Baner, Pune") and "booked" not in thin and "completion" not in thin


async def test_only_pages_with_real_facts_are_indexable():
    assert pages.indexable(FULL)
    assert not pages.indexable({**FULL, "units_total": None})
    assert not pages.indexable({**FULL, "completion_now": None})
    assert not pages.indexable({**FULL, "units_booked": 500})   # more booked than built: something is wrong, keep it out


async def test_page_for_and_the_public_api():
    db, store = await seeded(("P52100080076", "Rohan Abhilasha 4", "wagholi", FULL), ("P2", "Kesnand Greens", "wagholi", {**FULL, "completion_now": "2029-03-31"}),
                             ("P3", "Thin One", "wagholi", {}), ("GULM", "Gulmohar City", None, {"watched_by": ["agent_projects"]}),
                             ("NOTOURS", "Somewhere", None, {}))
    hit = await pages.page_for(db, "p52100080076")
    assert hit == {"slug": "rohan-abhilasha-4-wagholi", "path": "/projects/rohan-abhilasha-4-wagholi",
                   "url": hit["url"], "indexable": True} and hit["url"].endswith("/projects/rohan-abhilasha-4-wagholi")
    assert (await pages.page_for(db, "GULM"))["slug"] == "gulmohar-city-pune" and await pages.page_for(db, "NOTOURS") is None
    await pages.assign_all(store)

    app = FastAPI()
    app.include_router(ar.public_router, prefix="/public")
    app.dependency_overrides[ar.get_db] = lambda: db
    c = TestClient(app)
    page = c.get("/public/register/projects/rohan-abhilasha-4-wagholi").json()
    assert page["area"] == {"key": "wagholi", "slug": "wagholi", "name": "Wagholi"} and page["units_booked"] == 244
    assert page["details_read_at"] == "2026-10-03" and page["indexable"] and page["maharera_url"].endswith("/80076")
    assert [s["slug"] for s in page["same_area"]] == ["kesnand-greens-wagholi"]   # thin pages are not suggested
    assert c.get("/public/register/projects/thin-one-wagholi").json()["indexable"] is False
    assert c.get("/public/register/projects/nope").status_code == 404
    assert c.get("/public/register/by-regno/GULM").json() == {"slug": "gulmohar-city-pune", "path": "/projects/gulmohar-city-pune", "indexable": False}
    assert c.get("/public/register/by-regno/NOTOURS").status_code == 404
    assert [p["slug"] for p in c.get("/public/register/projects?area=wagholi").json()] == ["kesnand-greens-wagholi", "rohan-abhilasha-4-wagholi"] or \
        sorted(p["slug"] for p in c.get("/public/register/projects?area=wagholi").json()) == ["kesnand-greens-wagholi", "rohan-abhilasha-4-wagholi"]
    assert len(c.get("/public/register/projects?all=true").json()) == 4


async def test_zero_booked_after_completion_means_not_reported_and_the_page_says_the_date_passed():
    past = {**FULL, "completion_now": "2023-12-29", "completion_at_registration": "2022-12-30", "units_total": 1185, "units_booked": 0}
    assert pages.booked(past) is None and not pages.indexable(past)
    text = pages.paragraph({**past, "_id": "P1", "name": "Ivy Estate-Nia", "locality": "wagholi", "regno": "P1"})
    assert "0 of 1185" not in text and "bookings were not reported" in text and "occupancy certificate (OC)" in text
    future_new = {**FULL, "units_booked": 0}   # a new project with nothing sold yet: 0 is a real number
    assert pages.booked(future_new) == 0 and pages.indexable(future_new)
