"""The month's press story: registrations, booked homes, date moves and trackers, from fake register data (fixed NOW,
no network)."""
from datetime import datetime, timedelta, timezone

from app.modules.newsroom import trackers
from app.modules.press.facts import build_story

from ..fakes import FakeDb

NOW = datetime(2026, 11, 17, 6, 0, tzinfo=timezone.utc)  # 11:30 IST


def rec(n, locality="kharadi", registered="2026-11-05", completion_now=None, completion_at_reg=None, units=None, booked=None):
    regno = f"PR12600026{n:05d}"
    d = {"_id": regno, "regno": regno, "name": f"Project {n}", "locality": locality, "registered_on": registered}
    if completion_now:
        d["completion_now"] = completion_now
    if completion_at_reg:
        d["completion_at_registration"] = completion_at_reg
    if units is not None:
        d["units_total"] = units
    if booked is not None:
        d["units_booked"] = booked
    return d


async def db_with(*docs):
    db = FakeDb()
    for d in docs:
        await db.get_collection("projects").insert_one(d)
    return db


async def test_registrations_last_month_and_year_to_date_per_area():
    db = await db_with(rec(1, "kharadi", "2026-10-05"), rec(2, "kharadi", "2026-11-02"), rec(3, "wagholi", "2026-01-15"))
    story = await build_story(db, NOW)
    assert story["month"] == "2026-11"
    kharadi = next(f for f in story["facts"] if f["topic"] == "registrations" and f["area"] == "kharadi")
    assert "1 new MahaRERA project" in kharadi["text"] and "October 2026" in kharadi["text"] and "2 so far in 2026" in kharadi["text"]
    assert kharadi["source"] and kharadi["as_of"] == "2026-11-17"


async def test_an_area_with_no_registrations_gets_no_fact():
    db = await db_with(rec(1, "kharadi", "2025-01-01"))  # before this year: no last-month, no YTD
    story = await build_story(db, NOW)
    assert not any(f["topic"] == "registrations" and f["area"] == "kharadi" for f in story["facts"])


async def test_area_with_most_registrations_this_year_is_a_headline_fact():
    db = await db_with(*(rec(i, "kharadi", "2026-02-01") for i in range(1, 6)), rec(6, "wagholi", "2026-02-01"))
    story = await build_story(db, NOW)
    top = next(f for f in story["headline_facts"] if f["topic"] == "top_area")
    assert top["area"] == "kharadi" and "Kharadi" in top["text"] and "5" in top["text"]


async def test_homes_booked_only_when_known_for_every_project_in_the_area():
    db = await db_with(rec(1, "kharadi", units=100, booked=40), rec(2, "kharadi", units=None, booked=None))
    story = await build_story(db, NOW)
    assert not any(f["topic"] == "booked" and f["area"] == "kharadi" for f in story["facts"])

    db2 = await db_with(rec(1, "kharadi", units=100, booked=40), rec(2, "kharadi", units=50, booked=10))
    story2 = await build_story(db2, NOW)
    booked = next(f for f in story2["facts"] if f["topic"] == "booked" and f["area"] == "kharadi")
    assert "50 of 150 homes" in booked["text"]


async def test_date_moves_fact_counts_only_projects_still_being_built_with_both_dates():
    db = await db_with(
        rec(1, "kharadi", completion_now="2027-06-01", completion_at_reg="2026-01-01"),   # 5 months later: moved
        rec(2, "kharadi", completion_now="2027-02-01", completion_at_reg="2027-01-01"),    # 1 month later: not moved
    )
    story = await build_story(db, NOW)
    moves = next(f for f in story["facts"] if f["topic"] == "date_moves" and f["area"] is None)
    assert "1 of 2" in moves["text"] and "50%" in moves["text"]
    assert any(f["topic"] == "date_moves" and f["area"] is None for f in story["headline_facts"])
    area_move = next(f for f in story["facts"] if f["topic"] == "date_moves" and f["area"] == "kharadi")
    assert "1 of 2" in area_move["text"]


async def test_no_date_moves_fact_when_nothing_has_both_dates():
    db = await db_with(rec(1, "kharadi", completion_now="2027-06-01"))  # no completion_at_registration
    story = await build_story(db, NOW)
    assert not any(f["topic"] == "date_moves" for f in story["facts"])


async def test_tracker_fact_only_when_its_line_is_fresh_enough():
    last = trackers.definitions()["pune-metro-line-3"]["history"][-1]["date"]
    fresh_now = datetime.fromisoformat(last) + timedelta(days=5, hours=6)
    story = await build_story(FakeDb(), fresh_now.replace(tzinfo=timezone.utc))
    assert any(f["topic"] == "tracker" and "Metro Line 3" in f["text"] for f in story["facts"])

    stale_now = datetime.fromisoformat(last) + timedelta(days=200, hours=6)
    story2 = await build_story(FakeDb(), stale_now.replace(tzinfo=timezone.utc))
    assert not any(f["topic"] == "tracker" for f in story2["facts"])


async def test_then_and_now_pictures_are_never_guessed():
    """areastats.pictures does not exist yet: the story simply has no picture fact, never a guess."""
    db = await db_with(rec(1, "kharadi"))
    story = await build_story(db, NOW)
    assert not any(f["topic"] == "pictures" for f in story["facts"])
