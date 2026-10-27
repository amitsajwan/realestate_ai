"""Reading pings, the Live panel and who the visitor is (docs/plan/site-live-presence.md D1, D2, D6)."""
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.tracking import device
from app.modules.tracking.live import build_live, visits_of
from app.modules.tracking.schemas import PingIn
from app.modules.tracking.service import TrackingService
from app.platform.geoip import Place

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


# ---- who the visitor is (plan D6): device, area, network, robots, your own browser, and the story of each visit ----------

PUNE_JIO = Place(city="Pune", region="Maharashtra", country="IN", network="Jio", robot=False)
CLOUD = Place(city="Mumbai", region="Maharashtra", country="IN", network="Google", robot=True)
ANDROID = "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36"


async def make_geo(places):
    svc, db, clock = await make()
    asked = []

    def lookup(ip):
        asked.append(ip)
        return places.get(ip)
    return TrackingService(db, now=clock, geo=lookup), db, clock, asked


def test_device_labels_name_the_phone_and_the_browser_or_app():
    assert device.label(ANDROID) == "Android phone · Chrome"
    assert device.label(BROWSER) == "iPhone · Safari"
    assert device.label(BROWSER + " Instagram 312.0.0.0") == "iPhone · Instagram app"
    assert device.label("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36 Edg/130.0") == "Windows computer · Edge"
    assert device.label("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.0 Safari/605.1.15") == "Mac · Safari"
    assert device.label(None) is None


async def test_an_event_keeps_device_area_and_network_but_never_the_ip():
    svc, db, _, asked = await make_geo({"49.36.1.1": PUNE_JIO})
    await svc.track_event(view("/", "viewI0000001"), ANDROID, "49.36.1.1")
    doc = await db.get_collection("events").find_one({})
    assert (doc["device"], doc["area"], doc["network"]) == ("Android phone · Chrome", "Pune, Maharashtra", "Jio")
    assert asked == ["49.36.1.1"] and "49.36.1.1" not in str(doc) and "robot" not in doc and "staff" not in doc


async def test_headless_browsers_are_not_recorded():
    svc, db, _, _ = await make_geo({})
    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/130.0 Safari/537.36"
    assert await svc.track_event(view("/", "viewJ0000001"), ua, "1.2.3.4") is False
    assert await db.get_collection("events").count_documents({}) == 0


async def test_a_visitor_from_a_data_centre_is_a_robot_and_left_out_of_live():
    svc, _, _, _ = await make_geo({"34.1.1.1": CLOUD, "49.36.1.1": PUNE_JIO})
    await svc.track_event(view("/", "viewK0000001", anon="anon-robot-00"), ANDROID, "34.1.1.1")
    await svc.track_event(view("/", "viewK0000002"), ANDROID, "49.36.1.1")
    live = await build_live(svc, "A1")
    assert live["now"]["count"] == 1 and live["today"]["visitors"] == 1 and len(live["today"]["stories"]) == 1
    assert live["now"]["visitors"][0]["area"] == "Pune, Maharashtra"


async def test_your_own_browser_is_you_listed_last_and_never_counted():
    svc, _, clock, _ = await make_geo({})
    await svc.track_event(view("/", "viewL0000001", anon="anon-owner-00", staff=True), ANDROID)
    clock.advance(seconds=30)
    await svc.track_event(view("/projects/x", "viewL0000002", anon="anon-owner-00"), ANDROID)  # Studio signed out: still you today
    await svc.track_event(view("/", "viewL0000003"), BROWSER)
    live = await build_live(svc, "A1")
    assert [r["who"]["label"] for r in live["now"]["visitors"]] == ["Visitor 1", "You"]
    assert live["now"]["count"] == 1 and live["today"]["visitors"] == 1 and live["today"]["pages"] == 1
    assert {s["who"]["kind"] for s in live["today"]["stories"]} == {"you", "visitor"}


async def test_a_story_says_when_from_where_on_what_and_what_they_did():
    svc, _, clock, _ = await make_geo({"49.36.1.1": PUNE_JIO})   # 12:00 UTC = 17:30 India
    await svc.track_event(view("/projects/nova-residency-mundhwa?utm_source=chatgpt.com", "viewM0000001",
                               utm={"utm_source": "chatgpt.com"}), ANDROID, "49.36.1.1")
    clock.advance(minutes=3)
    await svc.ping(ping(170, view="viewM0000001"), ANDROID)
    await svc.track_event(ev("chat_open", listing=None), ANDROID, "49.36.1.1")
    clock.advance(minutes=1)
    await svc.track_event(view("/projects/godrej-ivara-pune", "viewM0000002"), ANDROID, "49.36.1.1")
    await svc.track_event(ev("whatsapp_click", listing=None), ANDROID, "49.36.1.1")
    clock.advance(minutes=30)   # gone

    s = (await build_live(svc, "A1"))["today"]["stories"][0]
    assert (s["start"], s["end"], s["came_from"], s["landing"]) == ("17:30", "17:34", "chatgpt", "/projects/nova-residency-mundhwa")
    assert (s["device"], s["area"], s["network"], s["pages"], s["read_s"], s["here_now"]) == \
        ("Android phone · Chrome", "Pune, Maharashtra", "Jio", 2, 170, False)
    assert [(x["page"], x["at"], x["read_s"]) for x in s["steps"]] == \
        [("/projects/nova-residency-mundhwa", "17:30", 170), ("/projects/godrej-ivara-pune", "17:34", 0)]
    assert s["did"] == [{"what": "Opened the chat", "at": "17:33"}, {"what": "Tapped WhatsApp", "at": "17:34"}]


async def test_stories_list_the_newest_visit_first():
    svc, _, clock, _ = await make_geo({})
    await svc.track_event(view("/", "viewN0000001", anon="anon-early-00"), BROWSER)
    clock.advance(minutes=40)
    await svc.track_event(view("/", "viewN0000002", anon="anon-later-00"), BROWSER)
    stories = (await build_live(svc, "A1"))["today"]["stories"]
    assert [s["who"]["label"] for s in stories] == ["Visitor 2", "Visitor 1"]
