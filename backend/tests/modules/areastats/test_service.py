"""Area stats (the W1 contract in docs/plan/pune-areas.md): counts from the project register, nothing guessed."""
from datetime import date, datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.areastats import router as area_router
from app.modules.areastats import service
from app.modules.areastats.service import area_stats

from ..fakes import FakeDb

READ_AT = datetime(2026, 10, 4, 3, 0, tzinfo=timezone.utc)  # 4 Oct IST
TODAY = date(2026, 10, 5)


def rec(n, locality="wagholi", completion=None, updated="2026-09-20", units=None, booked=None, promoter="Rohan Builders",
        checked_at=READ_AT):
    regno = f"PR12600026{n:05d}"
    d = {"_id": regno, "regno": regno, "name": f"Project {n}", "promoter": promoter, "pincode": "412207", "locality": locality,
         "last_modified": updated, "source": "MahaRERA", "source_url": f"https://maharerait.maharashtra.gov.in/public/project/view/{n}",
         "checked_at": checked_at, "news": []}
    if completion is not None:
        d.update(completion_now=completion, units_total=units, units_booked=booked, details_ok=True)
    return d


async def db_with(*docs):
    db = FakeDb()
    for d in docs:
        await db.get_collection("projects").insert_one(d)
    return db


async def test_empty_area_has_zero_projects_and_no_guesses():
    db = await db_with(rec(1, "kharadi"))
    out = await area_stats(db, "lohegaon", TODAY)
    assert out == {"area": {"key": "lohegaon", "name": "Lohegaon", "slug": "lohegaon", "tier": "affordable"},
                   "as_of": "2026-10-04", "projects": 0, "completing": [], "units_total": None, "units_booked": None,
                   "recent": [], "source": "MahaRERA public records"}


async def test_as_of_is_today_when_the_register_is_empty():
    out = await area_stats(FakeDb(), "baner", TODAY)
    assert out["as_of"] == "2026-10-05" and out["projects"] == 0 and out["area"]["tier"] == "it"


async def test_completing_counts_by_year_and_drops_years_before_as_of():
    db = await db_with(rec(1, completion="2025-12-31", units=10, booked=10), rec(2, completion="2026-03-31", units=20, booked=5),
                       rec(3, completion="2027-06-30", units=30, booked=0), rec(4, completion="2027-12-31", units=40, booked=12),
                       rec(5, completion="2029-10-30", units=50, booked=1), rec(6, "kharadi", completion="2028-01-01"))
    out = await area_stats(db, "wagholi", TODAY)
    assert out["projects"] == 5
    # 2025 is before as_of (2026-10-04) and is left out; 2026 stays (the year of as_of, even for a date already passed)
    assert out["completing"] == [{"year": 2026, "projects": 1}, {"year": 2027, "projects": 2}, {"year": 2029, "projects": 1}]
    assert out["units_total"] == 150 and out["units_booked"] == 28


async def test_units_are_null_unless_known_for_every_project():
    db = await db_with(rec(1, completion="2027-01-01", units=100, booked=40), rec(2, completion="2027-01-01", units=None, booked=None),
                       rec(3))  # never read from the project API
    out = await area_stats(db, "wagholi", TODAY)
    assert out["units_total"] is None and out["units_booked"] is None
    assert out["completing"] == [{"year": 2027, "projects": 2}]  # a project without a date is not counted in a year
    zero = await db_with(rec(1, completion="2027-01-01", units=0, booked=0))
    assert (await area_stats(zero, "wagholi", TODAY))["units_total"] is None  # 0 homes is MahaRERA not saying


async def test_recent_is_newest_first_at_most_five():
    docs = [rec(i, updated=f"2026-09-{10 + i:02d}") for i in range(1, 8)] + [rec(20, updated="")]
    docs[2].update(completion_now="2029-10-30", promoter="")
    out = await area_stats(await db_with(*docs), "wagholi", TODAY)
    assert [r["updated"] for r in out["recent"]] == ["2026-09-17", "2026-09-16", "2026-09-15", "2026-09-14", "2026-09-13"]
    assert out["projects"] == 8
    first = out["recent"][0]
    assert first == {"name": "Project 7", "regno": "PR1260002600007", "promoter": "Rohan Builders", "completion": None,
                     "updated": "2026-09-17", "url": "https://maharerait.maharashtra.gov.in/public/project/view/7"}
    three = next(r for r in (await area_stats(await db_with(*docs[:5]), "wagholi", TODAY))["recent"] if r["name"] == "Project 3")
    assert three["completion"] == "2029-10-30" and three["promoter"] is None  # a person, or not given: never named


async def test_key_or_slug_and_unknown_area():
    db = await db_with(rec(1, "upper_kharadi"))
    assert (await area_stats(db, "upper-kharadi", TODAY))["projects"] == 1
    assert (await area_stats(db, "upper_kharadi", TODAY))["area"]["slug"] == "upper-kharadi"
    assert await area_stats(db, "viman-nagar", TODAY) is None
    assert await area_stats(db, "", TODAY) is None


async def test_records_no_longer_in_an_area_are_not_counted():
    db = await db_with(rec(1, None), rec(2, "lohegaon"))
    assert (await area_stats(db, "lohegaon", TODAY))["projects"] == 1


async def test_naive_dates_from_mongo_are_utc():
    db = await db_with(rec(1, checked_at=datetime(2026, 10, 3, 20, 0)))  # 4 Oct 01:30 IST
    assert (await area_stats(db, "wagholi", TODAY))["as_of"] == "2026-10-04"


async def test_cached_for_a_short_while_and_copies_are_handed_out():
    db = await db_with(rec(1))
    first = await area_stats(db, "wagholi")
    await db.get_collection("projects").insert_one(rec(2))
    again = await area_stats(db, "wagholi")
    assert first["projects"] == again["projects"] == 1  # from the cache
    again["recent"].clear()
    assert len((await area_stats(db, "wagholi"))["recent"]) == 1  # a caller's change never reaches the cache
    service.clear_cache()
    assert (await area_stats(db, "wagholi"))["projects"] == 2


# --- the public endpoint --------------------------------------------------------------------------------------------------

def client(db):
    app = FastAPI()
    app.include_router(area_router.public_router, prefix="/public")
    app.dependency_overrides[area_router.get_db] = lambda: db
    return TestClient(app)


async def test_endpoint_returns_the_contract_and_404_for_unknown_areas():
    db = await db_with(rec(1, "keshav_nagar", completion="2027-05-31", units=12, booked=3))
    c = client(db)
    r = c.get("/public/areas/keshav-nagar/stats")
    assert r.status_code == 200 and r.headers["cache-control"] == f"public, max-age={service.CACHE_SECONDS}"
    body = r.json()
    assert set(body) == {"area", "as_of", "projects", "completing", "units_total", "units_booked", "recent", "source"}
    assert body["area"] == {"key": "keshav_nagar", "name": "Keshav Nagar", "slug": "keshav-nagar", "tier": "affordable"}
    assert body["projects"] == 1 and body["units_total"] == 12 and body["units_booked"] == 3
    assert set(body["recent"][0]) == {"name", "regno", "promoter", "completion", "updated", "url"}
    assert c.get("/public/areas/mundhwa/stats").status_code == 404
