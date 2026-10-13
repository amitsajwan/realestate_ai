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


async def test_indexable_needs_a_date_and_a_promoter_or_pincode():
    assert pages.indexable(FULL)
    assert pages.indexable({**FULL, "units_total": None, "units_booked": None})   # bookings optional
    assert pages.indexable({**FULL, "completion_now": "2015-01-01"})               # finished projects stay in
    assert pages.indexable({**FULL, "promoter": None, "pincode": "412207"})
    assert not pages.indexable({**FULL, "completion_now": None})
    assert not pages.indexable({**FULL, "promoter": None, "pincode": None})


async def test_page_updated_is_our_own_change_never_maharera():
    assert pages.page_updated({"last_modified": "2026-09-28"}) is None
    assert pages.page_updated({**FULL, "enriched_at": datetime(2026, 10, 5, tzinfo=timezone.utc)}) == "2026-10-05"
    assert pages.page_updated(FULL) == "2026-10-03"


async def test_marketed_name_and_aliases():
    doc = {"name": "Geras World of Joy M", "promoter": "Gera Developments Pvt. Ltd."}
    marketed, aliases = pages.names(doc)
    assert marketed == "Gera World of Joy M"
    assert aliases == ["Gera World of Joy M", "Gera World of Joy", "Gera's World of Joy M", "Gera's World of Joy",
                       "Geras World of Joy M"]
    # conservative: no promoter match, no stripping
    assert pages.names({"name": "Kumars Park II", "promoter": "Rohan Builders"}) == ("Kumars Park II", ["Kumars Park II", "Kumars Park"])
    assert pages.names({"name": "Rohan Abhilasha 4", "promoter": "Rohan Builders"})[1] == ["Rohan Abhilasha 4"]
    assert pages.names({**doc, "marketed_name_override": "World of Joy"})[0] == "World of Joy"


async def test_search_ranking_and_same_promoter():
    pages.clear_search_cache()
    gera = {**FULL, "promoter": "Gera Developments"}
    db, store = await seeded(("P52100012345", "Geras World of Joy M", "wagholi", gera),
                             ("P52100099999", "Joy Homes", "wagholi", FULL),
                             ("P52100055555", "Geras Island of Joy", "wagholi", gera))
    await pages.assign_all(store)
    app = FastAPI()
    app.include_router(ar.public_router, prefix="/public")
    app.dependency_overrides[ar.get_db] = lambda: db
    c = TestClient(app)
    get = lambda q: [r["regno"] for r in c.get("/public/register/search", params={"q": q}).json()]
    assert get("P52100012345") == ["P52100012345"]
    assert get("12345")[0] == "P52100012345"
    assert get("gera world")[0] == "P52100012345"                    # alias startswith
    assert get("joy") == ["P52100099999", "P52100055555", "P52100012345"]   # startswith 60 beats contains 50
    assert get("joy gera")[:2] and set(get("joy gera")) == {"P52100012345", "P52100055555"}   # all words
    assert get("j") == [] and get("  ") == []
    row = c.get("/public/register/search", params={"q": "World of Joy"}).json()[0]
    assert set(row) == {"slug", "name", "marketed_name", "regno", "promoter", "area", "place_name", "completion_now",
                        "units_total", "units_booked", "checked", "checks_total", "active"}
    assert row["marketed_name"] == "Gera World of Joy M" and row["area"] == "wagholi"
    page = c.get(f"/public/register/projects/{row['slug']}").json()
    assert [s["name"] for s in page["same_promoter"]] == ["Geras Island of Joy"] and "Gera's World of Joy" in page["aliases"]
    item = c.get("/public/register/projects").json()[0]
    assert {"marketed_name", "units_total", "units_booked", "page_updated"} <= set(item)
    pages.clear_search_cache()


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
    assert pages.booked(past) is None and pages.indexable(past)
    text = pages.paragraph({**past, "_id": "P1", "name": "Ivy Estate-Nia", "locality": "wagholi", "regno": "P1"})
    assert "0 of 1185" not in text and "bookings were not reported" in text and "occupancy certificate (OC)" in text
    future_new = {**FULL, "units_booked": 0}   # a new project with nothing sold yet: 0 is a real number
    assert pages.booked(future_new) == 0 and pages.indexable(future_new)


def test_a_page_is_dated_by_its_last_change():
    from datetime import datetime, timezone
    doc = {"last_modified": "2026-09-01", "details_checked_at": datetime(2026, 10, 3, tzinfo=timezone.utc), "details_ok": True}
    assert pages.page_updated(doc) == "2026-10-03"
    assert pages.page_updated({**doc, "page_text_at": datetime(2026, 10, 12, tzinfo=timezone.utc)}) == "2026-10-12"
    assert pages.page_updated({**doc, "details_ok": False}) is None          # a failed read changed nothing; MahaRERA's own date never counts
    assert pages.page_updated({}) is None
