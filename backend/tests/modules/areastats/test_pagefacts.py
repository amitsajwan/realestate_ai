"""The project page's v2 figures (docs/plan/project-page-v2.md, the contract): ₹ per sq ft per size, the area's rate, recent
bookings, distance to work hubs, the scope of a web count, the compare list's prices and sizes, and the extension-only date."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import pagefacts, pages, prices
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)
FULL = {"promoter": "Rohan Builders", "completion_now": "2029-10-30", "completion_at_registration": "2029-10-30",
        "units_total": 416, "units_booked": 244, "last_modified": "2026-09-28", "pincode": "412207", "news": []}


def priced(*rows):
    """A stored `prices` record: rows of (bhk, from_inr, the line it was read from)."""
    return {"at": NOW - timedelta(days=3), "rows": [
        {"bhk": bhk, "from_inr": inr, "to_inr": None, "official": True,
         "sources": [{"site": "builder.example", "url": "https://builder.example/", "official": True, "quote": quote}]}
        for bhk, inr, quote in rows]}


async def seeded(*docs):
    db = FakeDb()
    store = Store(db)
    for regno, name, extra in docs:
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": name, "locality": "wagholi",
                                         "page_slug": name.lower().replace(" ", "-"), **FULL, **extra})
    return db


# ---- prices.rows[].per_sqft ----------------------------------------------------------------------------------------------

def test_a_price_row_gives_its_rate_per_sqft_only_when_its_line_states_the_size():
    shown = prices.public(priced(("2 BHK", 7_200_000, "2 BHK 740 sq.ft ₹72 L"), ("3 BHK", 12_000_000, "3 BHK from ₹ 1.2 Cr")), NOW)
    assert [(r["bhk"], r["sqft"], r["per_sqft"]) for r in shown["rows"]] == [("2 BHK", 740, 9730), ("3 BHK", None, None)]


# ---- area_rate ---------------------------------------------------------------------------------------------------------

async def test_the_area_rate_is_the_median_of_three_other_projects_each_counted_once():
    db = await seeded(
        ("P1", "Our Project", {"prices": priced(("2 BHK", 20_000_000, "2 BHK 1,000 sq ft ₹ 2 Cr"))}),    # its own rate is left out
        ("P2", "Peer Two", {"prices": priced(("2 BHK", 7_000_000, "2 BHK 1,000 sq ft ₹ 70 L"),
                                             ("3 BHK", 9_000_000, "3 BHK 1,000 sq ft ₹ 90 L"))}),       # 8,000 (its median)
        ("P3", "Peer Three", {"prices": priced(("2 BHK", 6_000_000, "2 BHK 1,000 sq ft ₹ 60 L"))}),       # 6,000
        ("P4", "Peer Four", {"prices": priced(("2 BHK", 10_000_000, "2 BHK 1,000 sq ft ₹ 1 Cr"))}),       # 10,000
        ("P5", "Peer Five", {"prices": priced(("2 BHK", 9_000_000, "2 BHK from ₹ 90 L"))}),               # no size: no rate
        ("P6", "Tower B", {"cluster_primary": "P2", "prices": priced(("2 BHK", 4_000_000, "2 BHK 1,000 sq ft ₹ 40 L"))}),
        ("P7", "Far Away", {"locality": "baner", "prices": priced(("2 BHK", 4_000_000, "2 BHK 1,000 sq ft ₹ 40 L"))}))
    page = await pages.project_page(db, "our-project", now=NOW)
    assert page["area_rate"] == {"place": "Wagholi", "per_sqft": 8000, "projects": 3}
    assert page["prices"]["rows"][0]["per_sqft"] == 20000


async def test_the_area_rate_uses_the_pune_place_when_the_record_has_one():
    rate = lambda inr: {"prices": priced(("2 BHK", inr, f"2 BHK 1,000 sq ft ₹ {inr // 100_000} L"))}
    place = {"locality": None, "pune_place": "ravet", "pune_place_name": "Ravet"}
    db = await seeded(("P1", "Our Project", place), *[(f"P{i}", f"Peer {i}", {**place, **rate(6_000_000 + i * 100_000)})
                                                      for i in (2, 3, 4)])
    page = await pages.project_page(db, "our-project", now=NOW)
    assert page["area_rate"] == {"place": "Ravet", "per_sqft": 6300, "projects": 3}


async def test_no_area_rate_from_fewer_than_three_other_projects():
    db = await seeded(("P1", "Our Project", {}),
                      ("P2", "Peer Two", {"prices": priced(("2 BHK", 7_000_000, "2 BHK 1,000 sq ft ₹ 70 L"))}),
                      ("P3", "Peer Three", {"prices": priced(("2 BHK", 6_000_000, "2 BHK 1,000 sq ft ₹ 60 L"))}))
    assert (await pages.project_page(db, "our-project", now=NOW))["area_rate"] is None


def test_area_rate_needs_a_place():
    shown = {"rows": [{"per_sqft": 8000}]}
    assert pagefacts.area_rate(None, [shown] * 3) is None
    assert pagefacts.area_rate("Wagholi", [shown] * 3) == {"place": "Wagholi", "per_sqft": 8000, "projects": 3}


# ---- sales -------------------------------------------------------------------------------------------------------------

def reading(days_ago, n):
    return {"at": NOW - timedelta(days=days_ago), "booked": n}


def test_sales_are_homes_booked_since_the_oldest_reading_inside_ninety_days():
    doc = {"booked_history": [reading(200, 100), reading(80, 120), reading(40, 130), reading(0, 150)]}
    assert pagefacts.sales(doc) == {"booked": 30, "days": 80, "since": (NOW - timedelta(days=80)).date().isoformat()}


def test_no_sales_from_one_reading_readings_too_close_or_too_old_or_no_rise():
    assert pagefacts.sales({}) is None
    assert pagefacts.sales({"booked_history": [reading(0, 150)]}) is None
    assert pagefacts.sales({"booked_history": [reading(10, 140), reading(0, 150)]}) is None     # under 14 days apart
    assert pagefacts.sales({"booked_history": [reading(120, 100), reading(0, 150)]}) is None    # the only start is too old
    assert pagefacts.sales({"booked_history": [reading(60, 150), reading(0, 148)]}) is None     # a cancellation, not sales
    assert pagefacts.sales({"booked_history": [reading(30, 150), reading(0, 150)]}) is None


async def test_the_page_shows_sales_from_its_booked_history():
    db = await seeded(("P1", "Our Project", {"booked_history": [reading(60, 200), reading(0, 244)]}))
    page = await pages.project_page(db, "our-project", now=NOW)
    assert page["sales"] == {"booked": 44, "days": 60, "since": "2026-08-21"}


# ---- commute -----------------------------------------------------------------------------------------------------------

def test_commute_lists_the_nearest_hubs_within_25_km_nearest_first():
    got = pagefacts.commute({"lat": 18.5532, "lon": 73.9497})   # at EON IT Park
    assert got[0] == {"name": "EON IT Park, Kharadi", "km": 0.0}
    assert got[1]["name"] == "World Trade Center, Kharadi" and len(got) == 4
    assert [g["km"] for g in got] == sorted(g["km"] for g in got) and all(g["km"] <= 25 for g in got)
    far = pagefacts.commute({"lat": 18.98, "lon": 73.40})        # beyond every hub
    assert far == []


def test_no_commute_without_a_checked_position():
    assert pagefacts.commute(None) == []


async def test_the_page_gives_commute_only_from_a_checked_map_position():
    geo = {"geo": {"lat": 18.5290, "lon": 73.8745, "located_from": "pincode"}}
    checked = {"enrichment": {"steps": {"places": {"ok": True}}}}
    db = await seeded(("P1", "Our Project", {**geo, **checked}), ("P2", "Unchecked", geo))
    page = await pages.project_page(db, "our-project", now=NOW)
    assert page["commute"][0] == {"name": "Pune Railway Station", "km": 0.0}
    assert (await pages.project_page(db, "unchecked", now=NOW))["commute"] == []


# ---- web_facts scope ---------------------------------------------------------------------------------------------------

def fact(key, value):
    return {"key": key, "label": key, "value": value, "text": str(value), "official": True, "sources": []}


async def test_a_web_count_larger_than_the_registrations_is_the_whole_projects():
    web = {"at": NOW, "facts": [fact("towers", 5), fact("homes_total", 249), fact("floors", 24), fact("architect", "Hafeez")]}
    db = await seeded(("P1", "Park Eden Phase I", {"building_totals": {"towers": 2}, "units_total": 249, "web_facts": web}))
    page = await pages.project_page(db, "park-eden-phase-i", now=NOW)
    assert [(f["key"], f["scope"]) for f in page["web_facts"]["facts"]] == [
        ("towers", "project"), ("homes_total", "registration"), ("floors", None), ("architect", None)]


def test_a_smaller_web_count_or_no_maharera_count_has_no_scope():
    web = {"facts": [fact("towers", 1), fact("homes_total", 300)]}
    got = pagefacts.with_scope(web, {"towers": 2, "units_total": None})
    assert [f["scope"] for f in got["facts"]] == [None, None]
    assert pagefacts.with_scope(None, {}) is None


# ---- same_area price_from and bhk --------------------------------------------------------------------------------------

async def test_compared_projects_show_their_lowest_price_and_sizes():
    db = await seeded(("P1", "Our Project", {}),
                      ("P2", "Sized", {"prices": priced(("2 BHK", 7_000_000, "2 BHK from ₹ 70 L"),
                                                        ("3 BHK", 9_000_000, "3 BHK from ₹ 90 L"))}),
                      ("P3", "Overall Only", {"prices": priced(("All homes", 8_000_000, "Homes from ₹ 80 L"))}),
                      ("P4", "Unpriced", {}))
    page = await pages.project_page(db, "our-project", now=NOW)
    got = {s["slug"]: (s["price_from"], s["bhk"]) for s in page["same_area"]}
    assert got == {"sized": (7_000_000, "2, 3 BHK"), "overall-only": (8_000_000, None), "unpriced": (None, None)}


def test_sizes_label_puts_a_studio_first():
    assert pagefacts.sizes_label({"rows": [{"bhk": "1 RK"}, {"bhk": "1 BHK"}, {"bhk": "2 BHK"}]}) == "1 RK, 1, 2 BHK"
    assert pagefacts.sizes_label({"rows": [{"bhk": "Plot"}]}) is None
    assert pagefacts.sizes_label(None) is None


# ---- extension_only ----------------------------------------------------------------------------------------------------

def test_a_date_moved_only_by_mahareras_2026_extension_is_extension_only():
    base = {"registered_on": "2024-05-01", "completion_at_registration": "2028-06-30"}
    assert pages.extension_only({**base, "completion_now": "2028-10-30"})
    assert not pages.extension_only({**base, "completion_now": "2029-06-30"})          # the builder moved it too
    assert not pages.extension_only({**base, "completion_now": "2028-06-30"})          # not changed
    assert not pages.extension_only({**base, "registered_on": "2026-09-01", "completion_now": "2028-10-30"})   # after the order
    assert not pages.extension_only({"completion_now": "2028-10-30"})


async def test_the_page_says_whether_the_change_is_the_extension_only():
    db = await seeded(("P1", "Our Project", {"registered_on": "2024-05-01", "completion_at_registration": "2028-06-30",
                                             "completion_now": "2028-10-30"}))
    assert (await pages.project_page(db, "our-project", now=NOW))["extension_only"] is True
