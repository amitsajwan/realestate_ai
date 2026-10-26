"""Reading pings and the Live panel (docs/plan/site-live-presence.md D1, D2)."""
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.tracking.live import build_live, visits_of
from app.modules.tracking.schemas import PingIn

from .test_tracking import BROWSER, ev, make

pytestmark = pytest.mark.asyncio
VIEW = "view0000000001"


def ping(seconds, view=VIEW, anon="anon-visitor-1", slug="rahul"):
    return PingIn(agent_slug=slug, anon_id=anon, view_id=view, seconds=seconds)


def view(path, view_id, anon="anon-visitor-1", **kw):
    return ev("page_view", listing=None, anon=anon, view_id=view_id, path=path, **kw)


async def _the_view(db, view_id=VIEW):
    return await db.get_collection("events").find_one({"view_id": view_id})


async def test_a_ping_raises_the_reading_time_and_never_lowers_it():
    svc, db, clock = await make()
    await svc.track_event(view("/projects/godrej-ivara-pune", VIEW), BROWSER)
    assert (await _the_view(db))["read_s"] == 0
    clock.advance(seconds=30)
    assert await svc.ping(ping(30), BROWSER) is True
    clock.advance(seconds=30)
    await svc.ping(ping(12), BROWSER)  # a late beacon from an older tick must not shrink the time
    doc = await _the_view(db)
    assert doc["read_s"] == 30 and doc["last_seen"] == clock()


async def test_reading_time_is_capped_at_half_an_hour():
    svc, db, clock = await make()
    await svc.track_event(view("/guides/mhada-pune-lottery", VIEW), BROWSER)
    clock.advance(minutes=50)
    await svc.ping(ping(50 * 60), BROWSER)
    assert (await _the_view(db))["read_s"] == 30 * 60


async def test_a_ping_only_reaches_its_own_recent_view_and_never_makes_one():
    svc, db, clock = await make()
    await svc.track_event(view("/", VIEW), BROWSER)
    assert await svc.ping(ping(30, anon="anon-visitor-2"), BROWSER) is False   # another browser
    assert await svc.ping(ping(30, slug="priya"), BROWSER) is False            # another agent's site
    assert await svc.ping(ping(30, view="view0000000099"), BROWSER) is False   # a view never recorded
    assert await svc.ping(ping(30), "Googlebot/2.1") is False
    clock.advance(hours=3)
    assert await svc.ping(ping(30), BROWSER) is False                          # too old
    assert await db.get_collection("events").count_documents({}) == 1
    assert (await _the_view(db))["read_s"] == 0


async def test_a_view_without_a_view_id_is_stored_as_before():
    svc, db, _ = await make()
    await svc.track_event(ev("listing_view"), BROWSER)
    doc = await db.get_collection("events").find_one({})
    assert "view_id" not in doc and "read_s" not in doc and "last_seen" not in doc


def test_a_view_id_must_be_a_short_plain_token():
    with pytest.raises(ValidationError):
        ping(10, view="x")
    with pytest.raises(ValidationError):
        ping(10, view="../../etc/passwd")


async def test_live_shows_who_is_here_now_with_their_pages_in_order():
    svc, _, clock = await make()
    await svc.track_event(view("/projects/godrej-ivara-pune?src=ig_ivara", "viewA0000001", source="ig_ivara"), BROWSER)
    clock.advance(minutes=2)
    await svc.track_event(view("/projects/lodha-camelot", "viewA0000002"), BROWSER)
    clock.advance(seconds=40)
    await svc.ping(ping(40, view="viewA0000002"), BROWSER)
    clock.advance(seconds=20)

    live = await build_live(svc, "A1")
    assert live["now"]["count"] == 1
    v = live["now"]["visitors"][0]
    assert v["who"] == {"kind": "visitor", "label": "Visitor 1"}
    assert v["page"] == "/projects/lodha-camelot" and v["reading"] is True
    assert v["pages"] == 2 and v["minutes"] == 3 and v["came_from"] == "ig_ivara"
    assert [j["page"] for j in v["journey"]] == ["/projects/godrej-ivara-pune", "/projects/lodha-camelot"]
    assert v["journey"][1]["read_s"] == 40
    assert "anon_id" not in str(live)


async def test_a_visitor_quiet_for_five_minutes_has_left():
    svc, _, clock = await make()
    await svc.track_event(view("/", "viewB0000001"), BROWSER)
    clock.advance(minutes=4)
    assert (await build_live(svc, "A1"))["now"]["count"] == 1
    clock.advance(minutes=2)
    assert (await build_live(svc, "A1"))["now"]["count"] == 0


async def test_an_open_tab_without_pings_is_here_but_not_reading():
    svc, _, clock = await make()
    await svc.track_event(view("/", "viewC0000001"), BROWSER)
    clock.advance(minutes=3)
    v = (await build_live(svc, "A1"))["now"]["visitors"][0]
    assert v["reading"] is False


async def test_a_known_lead_is_named_and_others_stay_anonymous():
    svc, db, clock = await make()
    await db.get_collection("contacts").insert_one({"_id": "C1", "agent_id": "A1", "name": "Rahul T", "anon_ids": ["anon-lead-000"]})
    await svc.track_event(view("/projects/godrej-ivara-pune", "viewD0000001", anon="anon-lead-000"), BROWSER)
    await svc.track_event(view("/", "viewD0000002", anon="anon-other-00"), BROWSER)
    rows = (await build_live(svc, "A1"))["now"]["visitors"]
    assert {r["who"]["label"] for r in rows} == {"Rahul T", "Visitor 2"}
    assert next(r for r in rows if r["who"]["kind"] == "lead")["who"]["lead_id"] == "C1"


async def test_an_instagram_in_app_visit_says_instagram_not_direct():
    svc, _, _ = await make()
    ua = BROWSER + " Instagram 312.0.0.0"
    await svc.track_event(view("/projects/godrej-ivara-pune", "viewE0000001"), ua)
    assert (await build_live(svc, "A1"))["now"]["visitors"][0]["came_from"] == "instagram"


async def test_live_is_owner_scoped():
    svc, _, _ = await make()
    await svc.track_event(view("/", "viewF0000001", slug="priya"), BROWSER)
    live = await build_live(svc, "A1")
    assert live["now"]["count"] == 0 and live["today"]["visitors"] == 0


async def test_busiest_visitor_comes_first():
    svc, _, clock = await make()
    await svc.track_event(view("/", "viewG0000001", anon="anon-light-00"), BROWSER)
    for i in range(3):
        await svc.track_event(view(f"/projects/p{i}", f"viewG000001{i}", anon="anon-heavy-00"), BROWSER)
        clock.advance(seconds=30)
    rows = (await build_live(svc, "A1"))["now"]["visitors"]
    assert [r["pages"] for r in rows] == [3, 1]


def test_visits_split_where_the_visitor_was_away_over_half_an_hour():
    t = datetime(2026, 1, 1, 10, 0)
    views = [{"ts": t}, {"ts": t + timedelta(minutes=10), "last_seen": t + timedelta(minutes=20)},
             {"ts": t + timedelta(minutes=45)}, {"ts": t + timedelta(minutes=90)}]
    assert [len(v) for v in visits_of(views)] == [3, 1]


async def test_today_counts_visits_reading_time_top_pages_and_where_they_left():
    svc, _, clock = await make()   # 12:00 UTC = 17:30 in India
    # yesterday in India (before 18:30 UTC of the day before): not counted
    clock.advance(hours=-18)
    await svc.track_event(view("/old", "viewH0000000", anon="anon-yday-000"), BROWSER)
    clock.advance(hours=18)
    # visitor 1: two pages, read 60 s and 20 s, then left
    await svc.track_event(view("/projects/godrej-ivara-pune?utm_source=google", "viewH0000001"), BROWSER)
    await svc.ping(ping(60, view="viewH0000001"), BROWSER)
    clock.advance(minutes=1)
    await svc.track_event(view("/projects/lodha-camelot", "viewH0000002"), BROWSER)
    await svc.ping(ping(20, view="viewH0000002"), BROWSER)
    # visitor 2: one page, no pings (an old page, or left at once)
    await svc.track_event(view("/projects/godrej-ivara-pune", "viewH0000003", anon="anon-visitor-2"), BROWSER)
    clock.advance(minutes=20)
    # visitor 3: still here
    await svc.track_event(view("/guides/upper-kharadi", "viewH0000004", anon="anon-visitor-3"), BROWSER)

    today = (await build_live(svc, "A1"))["today"]
    assert today["date"] == "2026-01-01"
    assert (today["visitors"], today["visits"], today["pages"], today["one_page_visits"]) == (3, 3, 4, 2)
    assert today["avg_read_s"] == 40
    assert today["top_pages"][0] == {"page": "/projects/godrej-ivara-pune", "views": 2, "avg_read_s": 60}
    assert {r["page"]: r["visits"] for r in today["left_from"]} == {"/projects/lodha-camelot": 1, "/projects/godrej-ivara-pune": 1}
