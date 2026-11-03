"""The project page's v2 figures (docs/plan/project-page-v2.md, the contract): ₹ per sq ft per size, the area's rate, recent
bookings, distance to work hubs, the scope of a web count, the compare list's prices and sizes, and the extension-only date."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import pagefacts, pages, priceidea, prices
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
    geo = {"geo": {"lat": 18.5290, "lon": 73.8745, "located_from": "google"}}
    centre = {"geo": {"lat": 18.5290, "lon": 73.8745, "located_from": "pincode"}}
    checked = {"enrichment": {"steps": {"places": {"ok": True}}}}
    db = await seeded(("P1", "Our Project", {**geo, **checked}), ("P2", "Unchecked", geo), ("P3", "Pincode Centre", {**centre, **checked}))
    page = await pages.project_page(db, "our-project", now=NOW)
    assert page["commute"][0] == {"name": "Pune Railway Station", "km": 0.0}
    assert (await pages.project_page(db, "unchecked", now=NOW))["commute"] == []
    assert (await pages.project_page(db, "pincode-centre", now=NOW))["commute"] == []   # the pincode's centre is not the project


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


# ---- what changed, as we read it (docs/plan/seo-system.md 8b, H1) -----------------------------------------------------
def test_booking_readings_are_dated_oldest_first_one_per_day():
    doc = {"booked_history": [{"at": NOW - timedelta(days=60), "booked": 300}, {"at": NOW - timedelta(days=30), "booked": 312},
                              {"at": NOW - timedelta(days=30, hours=-2), "booked": 315}, {"at": NOW, "booked": 344}]}
    assert pagefacts.booked_readings(doc) == [{"on": "2026-08-21", "booked": 300}, {"on": "2026-09-20", "booked": 315},
                                              {"on": "2026-10-20", "booked": 344}]


def test_one_booking_reading_is_not_a_history():
    assert pagefacts.booked_readings({"booked_history": [{"at": NOW, "booked": 10}]}) == []
    assert pagefacts.booked_readings({}) == []


def test_a_page_shows_only_the_latest_year_of_booking_readings():
    doc = {"booked_history": [{"at": NOW - timedelta(days=30 * i), "booked": 500 - i} for i in range(20)]}
    rows = pagefacts.booked_readings(doc)
    assert len(rows) == pagefacts.READINGS_SHOWN and rows[-1] == {"on": "2026-10-20", "booked": 500}


def test_each_date_change_we_saw_is_listed_and_the_2026_order_is_named_as_mahareras():
    doc = {"registered_on": "2023-05-01", "completion_history": [
        {"from": "2028-12-31", "to": "2029-06-30", "seen_at": NOW - timedelta(days=400)},     # the builder
        {"from": "2029-06-30", "to": "2029-10-31", "seen_at": NOW - timedelta(days=80)},      # MahaRERA's 4 months
        {"from": "2029-10-31", "to": "2029-10-31", "seen_at": NOW}]}                          # no change: not a move
    assert pages.completion_moves(doc) == [
        {"seen_on": "2025-09-15", "from": "2028-12-31", "to": "2029-06-30", "blanket": False},
        {"seen_on": "2026-08-01", "from": "2029-06-30", "to": "2029-10-31", "blanket": True}]


def test_a_four_month_move_is_the_builders_on_a_project_registered_after_the_order():
    doc = {"registered_on": "2026-09-01", "completion_history": [{"from": "2029-06-30", "to": "2029-10-31", "seen_at": NOW}]}
    assert pages.completion_moves(doc)[0]["blanket"] is False


def test_the_page_carries_the_readings_and_the_moves():
    v = pages.view({"_id": "P1", **FULL, "booked_history": [{"at": NOW - timedelta(days=30), "booked": 230}, {"at": NOW, "booked": 244}],
                    "completion_history": [{"from": "2029-06-30", "to": "2029-10-30", "seen_at": NOW}]}, [])
    assert v["booked_readings"] == [{"on": "2026-09-20", "booked": 230}, {"on": "2026-10-20", "booked": 244}]
    assert [m["to"] for m in v["completion_moves"]] == ["2029-10-30"]


# ---- a builder's date changes, as we saw them (docs/plan/seo-system.md 8b, H3) -------------------------------------------
def test_a_builders_page_lists_each_date_it_filed_later_newest_first_without_mahareras_order():
    from app.modules.areastats import hubs
    one = {"_id": "P1", "page_slug": "one", "name": "ONE", "registered_on": "2023-01-01", "completion_history": [
        {"from": "2028-12-31", "to": "2029-06-30", "seen_at": NOW - timedelta(days=300)},
        {"from": "2029-06-30", "to": "2029-10-31", "seen_at": NOW - timedelta(days=80)}]}      # MahaRERA's 4 months
    two = {"_id": "P2", "page_slug": "two", "name": "TWO", "registered_on": "2024-01-01", "completion_history": [
        {"from": "2030-03-31", "to": "2030-12-31", "seen_at": NOW - timedelta(days=10)},
        {"from": "2030-12-31", "to": "2030-09-30", "seen_at": NOW - timedelta(days=5)}]}      # filed earlier: not a delay
    rows = hubs.date_moves([one, two])
    assert [(r["slug"], r["from"], r["to"]) for r in rows] == [("two", "2030-03-31", "2030-12-31"), ("one", "2028-12-31", "2029-06-30")]
    assert rows[0]["seen_on"] == "2026-10-10"


async def test_the_builder_page_carries_its_date_changes():
    from app.modules.areastats import hubs
    db = await seeded(("P1", "One", {"registered_on": "2023-01-01",
                                     "completion_history": [{"from": "2028-12-31", "to": "2029-06-30", "seen_at": NOW}]}))
    page = await hubs.builder_page(db, pages.builder_key({"promoter": FULL["promoter"], "name": "One"}))
    assert [(m["slug"], m["to"]) for m in page["date_moves"]] == [("one", "2029-06-30")]


async def test_the_builders_list_and_page_carry_the_builders_logo():
    from app.modules.areastats import hubs
    logo = {"status": "found", "path": "builder_logos/rohan-builders.png", "width": 300, "height": 90, "tone": "dark",
            "site": "rohanbuilders.com"}
    db = await seeded(("P1", "One", {"builder_logo": logo}), ("P2", "Two", {}))
    key = pages.builder_key({"promoter": FULL["promoter"], "name": "One"})
    row = next(r for r in await hubs.builders(db, only_indexable=False) if r["slug"] == key)
    assert row["logo"]["url"] == "/uploads/builder_logos/rohan-builders.png"
    assert (await hubs.builder_page(db, key))["logo"]["site"] == "rohanbuilders.com"


# ---- old addresses -----------------------------------------------------------------------------------------------------

async def test_a_page_moved_to_a_new_address_is_still_found_at_its_old_one():
    db = await seeded(("P1", "Our Project", {"page_slug": "our-project-charholi", "old_slugs": ["our-project-kharadi"]}))
    page = await pages.project_page(db, "our-project-kharadi", now=NOW)
    assert page["slug"] == "our-project-charholi"   # the frontend sends the old address there (301)


def test_a_web_fact_from_property_sites_has_no_link_and_the_builders_own_keeps_its():
    portals = [{"site": "housiey.com", "url": "https://housiey.com/p", "official": False, "quote": "12.8 acres"},
               {"site": "other.com", "url": "https://other.com/p", "official": False, "quote": "12.8 acres"}]
    builder = {"site": "builder.example", "url": "https://builder.example/", "official": True, "quote": "12.8 acres"}
    shown = pages.web_public({"facts": [{"key": "land_acres", "official": False, "sources": portals},
                                        {"key": "towers", "official": True, "sources": [builder, portals[0]]}]})["facts"]
    assert [x["url"] for x in shown[0]["sources"]] == [None, None]
    assert [x["url"] for x in shown[1]["sources"]] == ["https://builder.example/", None]
    assert portals[0]["url"] == "https://housiey.com/p"   # the record keeps it


# ---- area_compare ------------------------------------------------------------------------------------------------------

TODAY = NOW.date()


def project(regno, registered="2025-06-01", total=100, booked=50, at_reg="2029-10-30", now="2029-10-30", **extra):
    return {"_id": regno, "regno": regno, "locality": "wagholi", "promoter": "Rohan Builders", "registered_on": registered,
            "units_total": total, "units_booked": booked, "completion_at_registration": at_reg, "completion_now": now, **extra}


def test_homes_booked_is_set_against_the_median_of_projects_registered_within_a_year():
    mine = project("P0", booked=60)
    peers = [project(f"N{i}", registered="2025-01-15", booked=b) for i, b in enumerate((10, 20, 30, 40, 50, 60, 70, 80))]
    old = [project(f"O{i}", registered="2021-03-01", booked=95) for i in range(8)]   # selling for years: not comparable
    got = pages.area_compare(mine, peers + old, "Wagholi", today=TODAY)
    assert got["booked"] == {"pct": 60, "area_pct": 45, "projects": 8}


def test_a_comparison_needs_eight_projects_and_is_none_when_nothing_can_be_said():
    mine = project("P0")
    seven = [project(f"N{i}") for i in range(7)]
    assert pages.area_compare(mine, seven, "Wagholi", today=TODAY) is None
    assert pages.area_compare(mine, seven + [project("N7")], "Wagholi", today=TODAY)["booked"]["projects"] == 8
    assert pages.area_compare(mine, seven + [project("N7")], None, today=TODAY) is None


def test_finished_projects_and_offices_are_left_out_of_the_area():
    mine = project("P0")
    passed = [project(f"F{i}", at_reg="2025-12-31", now="2025-12-31") for i in range(8)]
    offices = [project(f"C{i}", project_type="Commercial") for i in range(8)]
    assert pages.area_compare(mine, passed + offices, "Wagholi", today=TODAY) is None


def test_the_date_move_is_set_against_how_many_projects_in_the_area_moved_theirs():
    # registered after MahaRERA's 2026 extension, so the months are the builder's own
    mine = project("P0", registered="2026-09-01", at_reg="2029-01-31", now="2030-03-31")          # 14 months later
    moved = [project(f"M{i}", registered="2026-09-01", at_reg="2029-01-31", now="2029-07-31") for i in range(3)]
    kept = [project(f"K{i}", registered="2026-09-01") for i in range(6)]
    got = pages.area_compare(mine, moved + kept, "Wagholi", today=TODAY)
    assert got["moved"] == {"months": 14, "area_moved": 3, "area_with_dates": 9}


def test_rates_are_never_compared_since_sites_mix_carpet_and_built_up_areas():
    got = pages.area_compare(project("P0"), [project(f"N{i}") for i in range(8)], "Wagholi", today=TODAY)
    assert set(got) == {"place", "booked", "moved"}


async def test_the_project_page_carries_the_area_comparison():
    reg = {"registered_on": "2025-06-01"}
    db = await seeded(("P1", "Our Project", reg), *[(f"P{i}", f"Peer {i}", reg) for i in range(2, 10)])
    page = await pages.project_page(db, "our-project", now=NOW)
    assert page["area_compare"] == {"place": "Wagholi", "booked": {"pct": 59, "area_pct": 59, "projects": 8},
                                    "moved": {"months": 0, "area_moved": 0, "area_with_dates": 8}}


# ---- an overall price far under the area's cheapest homes is not a home's (2026-11-03: VJ IndiLife "Homes from ₹35 L") ------


BANDS = [{"bhk": "1 BHK", "low": 6_000_000, "high": 7_000_000, "middle": 6_500_000, "projects": 4},
         {"bhk": "2 BHK", "low": 9_000_000, "high": 11_000_000, "middle": 10_000_000, "projects": 6}]


def test_the_floor_is_seventy_percent_of_the_low_end_of_the_areas_cheapest_size():
    assert priceidea.overall_floor(BANDS) == 4_200_000
    assert priceidea.overall_floor([]) is None


def test_an_overall_price_under_the_floor_is_dropped_but_sized_prices_and_fair_overall_prices_stay():
    shown = {"read_at": "2026-10-22", "rows": [{"bhk": "All homes", "from_inr": 3_500_000}]}
    assert prices.homes_only(shown, 4_200_000) is None
    assert prices.homes_only({**shown, "rows": [{"bhk": "All homes", "from_inr": 6_000_000}]}, 4_200_000)["rows"][0]["from_inr"] == 6_000_000
    assert prices.homes_only({**shown, "rows": [{"bhk": "1 RK", "from_inr": 3_000_000}]}, 4_200_000)["rows"][0]["bhk"] == "1 RK"
    assert prices.homes_only(shown, None) == shown   # no bands in the area: nothing to judge by


async def test_a_studios_onwards_price_is_not_shown_as_the_projects_homes_or_in_the_area_lists():
    one_bhk = lambda inr: {"prices": priced(("1 BHK", inr, f"1 BHK ₹ {inr // 100_000} L"))}
    db = await seeded(("P1", "VJ IndiLife", {"prices": priced(("All homes", 3_500_000, "35 Lacs* Onwards"))}),
                      *[(f"P{i}", f"Peer {i}", one_bhk(6_000_000 + i * 200_000)) for i in range(2, 6)])
    page = await pages.project_page(db, "vj-indilife", now=NOW)
    assert page["prices"] is None
    listed = {r["slug"]: r for r in await pages.listing(db, area="wagholi", only_indexable=False)}
    assert listed["vj-indilife"]["price_from"] is None and listed["vj-indilife"]["homes"] == []
    assert listed["peer-2"]["price_from"] == 6_400_000
    # with no area to judge by, the price stays
    alone = await seeded(("P1", "VJ IndiLife", {"prices": priced(("All homes", 3_500_000, "35 Lacs* Onwards"))}))
    assert (await pages.project_page(alone, "vj-indilife", now=NOW))["prices"]["rows"][0]["from_inr"] == 3_500_000
