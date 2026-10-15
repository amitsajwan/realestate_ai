"""Number of the week: candidates from the register, the relatability gate, the drawn reel and the planned rows."""
import asyncio
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.core import areas
from app.modules.calendar import area_reels, number_reels as nr
from app.modules.calendar.schedule import IST
from app.modules.calendar.store import Store
from app.modules.newsroom.store import PROJECTS

from ..fakes import FakeDb

TODAY = date(2026, 10, 15)          # a Thursday in the festive season
NOW = datetime(2026, 10, 15, 6, 0, tzinfo=timezone.utc)
WAGHOLI = areas.get("wagholi")


def proj(i, area="wagholi", now="2027-06-30", first="2027-06-30", total=200, booked=120, history=None, **kw):
    return {"_id": f"P5210000{i:04d}", "name": f"Test Homes {i}", "locality": area, "project_type": "Residential",
            "registered_on": "2023-01-10", "completion_at_registration": first, "completion_now": now,
            "units_total": total, "units_booked": booked, "booked_history": history or [],
            "details_checked_at": datetime(2026, 10, 14, 4, 0, tzinfo=timezone.utc), **kw}


def run(c):
    return asyncio.run(c)


# ---- candidates --------------------------------------------------------------------------------------------------------------
def test_soon_counts_projects_due_in_twelve_months_and_their_unbooked_homes():
    docs = [proj(i, now="2027-03-31") for i in range(4)] + [proj(9, now="2029-12-31")]
    c = nr.soon(docs, WAGHOLI, TODAY)
    assert c["value"] == 4 and c["stake"] == "time"
    assert "320 of their 800 homes are not yet booked" in c["facts"][1]


def test_soon_needs_a_pattern_not_one_project():
    assert nr.soon([proj(1, now="2027-03-31")], WAGHOLI, TODAY) is None


def test_moved_counts_real_moves_net_of_covid_only_where_homes_are_booked():
    docs = [proj(i, first="2026-12-31", now="2028-06-30") for i in range(3)]          # moved 18 months
    docs += [proj(10 + i, now="2028-03-31", first="2028-03-31") for i in range(3)]                                           # never moved
    docs += [proj(20, first="2026-12-31", now="2028-06-30", booked=0)]                 # nobody waiting: not counted
    c = nr.moved(docs, WAGHOLI, TODAY)
    assert c["big"] == "3 of 6" and c["stake"] == "risk" and c["strong"]
    assert "360 homes are booked" in c["facts"][2]


def test_open_and_pace_count_homes():
    hist = [{"at": NOW - timedelta(days=120), "booked": 50}, {"at": NOW - timedelta(days=10), "booked": 90}]
    docs = [proj(i, history=hist) for i in range(3)]
    assert nr.open_homes(docs, WAGHOLI, TODAY)["value"] == 240
    p = nr.pace(docs, WAGHOLI, NOW)
    assert p["value"] == 120 and p["homes"]


def test_only_pincode_matched_areas_are_used():
    docs = [proj(i, area="baner", now="2027-03-31") for i in range(6)]
    assert nr.candidates(docs, NOW, TODAY) == []


# ---- will people relate? -----------------------------------------------------------------------------------------------------
def test_relate_rewards_stake_homes_and_season_and_explains_itself():
    c = nr.open_homes([proj(i) for i in range(3)], WAGHOLI, TODAY)
    r = nr.relate(c, TODAY, {})
    assert r["score"] == 2 + 1 + 1          # choice, in homes, festive season
    assert any("festive" in x for x in r["reasons"]) and any(c["question"] in x for x in r["reasons"])


def test_a_number_shown_lately_loses_to_a_fresh_one():
    docs = [proj(i, first="2026-12-31", now="2028-06-30") for i in range(3)] + [proj(10 + i, now="2028-03-31", first="2028-03-31") for i in range(3)]
    cands = nr.candidates(docs, NOW, TODAY)
    first = nr.pick(cands, TODAY, {})
    assert first["kind"] == "moved"           # risk, a clear effect
    again = nr.pick(cands, TODAY, {"moved-wagholi": (TODAY - timedelta(days=7)).strftime("%Y%m%d")})
    assert again is None or again["kind"] != "moved"


def test_no_reel_when_nothing_reaches_the_bar():
    c = nr.pace([proj(i, history=[{"at": NOW - timedelta(days=100), "booked": 100},
                                  {"at": NOW - timedelta(days=5), "booked": 110}]) for i in range(2)], WAGHOLI, NOW)
    assert c is not None and not c["strong"]
    shown = {"pace-wagholi": "20261008", "area-wagholi": "20261014"}
    assert nr.pick([c], TODAY, shown) is None


# ---- the reel ----------------------------------------------------------------------------------------------------------------
def test_reel_wording_slides_and_captions():
    c = nr.pick(nr.candidates([proj(i, first="2026-12-31", now="2028-06-30") for i in range(3)] + [proj(10 + i, now="2028-03-31", first="2028-03-31") for i in range(3)],
                              NOW, TODAY), TODAY, {})
    reel = nr.build(c, "2026-10-14")
    text = reel.caption_ig + reel.caption_fb + " ".join(reel.script)
    assert not area_reels.wording_problems(text)
    for word in ("delayed", "stuck", "scam", "₹"):
        assert word not in text.lower()
    assert "?" in reel.caption_ig and "Source: MahaRERA public records, as of 14 Oct 2026" in reel.caption_ig
    assert reel.slides[0].big == "3 of 6"
    with tempfile.TemporaryDirectory() as d:
        assert len(area_reels.save_slides(reel, Path(d))) == 4     # drawn and checked: safe zone, contrast, nothing cut


# ---- planning ----------------------------------------------------------------------------------------------------------------
def test_autoplan_plans_next_wednesday_once_as_planned_rows_with_the_reason():
    db = FakeDb()
    col = db.get_collection(PROJECTS)
    for d in [proj(i, first="2026-12-31", now="2028-06-30") for i in range(3)] + [proj(10 + i, now="2028-03-31", first="2028-03-31") for i in range(3)]:
        run(col.insert_one(d))
    store = Store(db)
    with tempfile.TemporaryDirectory() as up:
        assert run(nr.autoplan(db, store, TODAY, Path(up), now=NOW)) == 2
        assert run(nr.autoplan(db, store, TODAY, Path(up), now=NOW)) == 0
        rows = run(store.all())
    assert {r["channel"] for r in rows} == {"instagram", "facebook_page"}
    for r in rows:
        assert r["status"] == "planned" and r["kind"] == "reel"
        assert r["slug"] == "number-moved-wagholi-20261021"
        assert r["due_at"].astimezone(IST).weekday() == nr.WEEKDAY
        assert r["creative"]["relate"]["score"] >= nr.MIN_RELATE and r["creative"]["relate"]["reasons"]


def test_results_group_number_reels_under_their_own_format():
    from app.modules.calendar import tags
    t = tags.derive({"kind": "reel", "slug": "number-moved-wagholi-20261021", "caption": "x",
                     "creative": {"template": "number", "hook_type": "number", "area": "wagholi"}})
    assert (t["format"], t["hook_type"], t["area"]) == ("number", "number", "wagholi")
