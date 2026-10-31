"""The rounded price idea (app/modules/areastats/priceidea.py, prices.ideas/starts, pricing.no_seen)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import priceidea, prices, pricing

NOW = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)


def seen(bhk, from_inr, to_inr=None, site="a.example", quote=None):
    return {"bhk": bhk, "from_inr": from_inr, "to_inr": to_inr, "site": site, "url": f"https://{site}/p",
            "quote": quote or f"{bhk} from {from_inr}"}


def agreed(bhk, from_inr):
    return {"bhk": bhk, "from_inr": from_inr, "to_inr": None, "official": False,
            "sources": [{"site": "a.example", "url": "https://a.example/p", "official": False, "quote": f"{bhk} line"},
                        {"site": "b.example", "url": "https://b.example/p", "official": False, "quote": "other"}]}


def test_one_price_becomes_a_rounded_band_never_the_site_figure():
    assert priceidea.band(23_400_000) == (22_000_000, 26_000_000)        # ₹2.34 Cr -> about ₹2.2 - 2.6 Cr
    assert priceidea.band(7_250_000) == (7_000_000, 8_000_000)           # ₹72.5 L -> about ₹70 - 80 L
    assert priceidea.band(27_700_000, 45_000_000) == (26_000_000, 45_000_000)


def test_a_size_one_site_prices_is_an_idea_and_a_published_size_is_not():
    p = {"at": NOW - timedelta(days=2), "rows": [agreed("4 BHK", 27_700_000)],
         "seen": [seen("3 BHK", 23_400_000), seen("4 BHK", 27_700_000), seen("3 BHK", 24_000_000, 26_000_000, site="b.example")]}
    assert prices.ideas(p, NOW) == [{"bhk": "3 BHK", "from_inr": 23_400_000, "to_inr": 26_000_000}]
    assert prices.starts(p, NOW) == {"3 BHK": 23_400_000, "4 BHK": 27_700_000}


def test_an_old_reading_and_a_price_too_high_for_its_size_give_no_idea():
    assert prices.ideas({"at": NOW - timedelta(days=60), "rows": [], "seen": [seen("2 BHK", 7_000_000)]}, NOW) == []
    bad = seen("2 BHK", 96_000_000, quote="2 BHK 750 sq ft ₹9.6 Cr")
    assert prices.ideas({"at": NOW, "rows": [], "seen": [bad]}, NOW) == []


def test_the_area_band_needs_three_projects_and_a_far_off_project_price_is_dropped():
    starts = [{"2 BHK": 6_500_000, "3 BHK": 9_000_000}, {"2 BHK": 7_200_000}, {"2 BHK": 8_000_000, "3 BHK": 9_500_000}]
    area = priceidea.area_bands(starts)
    assert [a["bhk"] for a in area] == ["2 BHK"]
    assert area[0]["projects"] == 3 and area[0]["low"] <= 6_500_000 and area[0]["high"] >= 7_600_000
    rows = priceidea.project_bands([{"bhk": "2 BHK", "from_inr": 30_000_000, "to_inr": None},
                                    {"bhk": "3 BHK", "from_inr": 9_000_000, "to_inr": None}], area)
    assert [r["bhk"] for r in rows] == ["3 BHK"]     # ₹3 Cr for a 2 BHK where the middle is ₹72 L is a misread


def test_upper_kharadi_and_wagholi_prices_read_before_seen_are_due_once_more():
    base = {"_id": "P1", "regno": "P1", "name": "P", "page_slug": "p", "promoter": "B", "completion_now": "2028-06-30",
            "registered_on": "2025-01-01", "units_total": 100, "units_booked": 10}
    read = {"at": NOW - timedelta(days=3), "rows": [], "read": [{"site": "a.example", "ok": True}]}
    d = {**base, "pune_place": "wagholi", "prices": read, "prices_tried_at": NOW - timedelta(days=3)}
    assert pricing.priority(d, NOW) is not None
    assert pricing.priority({**d, "pune_place": "baner"}, NOW) is None
    assert pricing.priority({**d, "prices": {**read, "seen": []}}, NOW) is None
    # a read tried since that failed (no `prices` written) waits its normal turn instead of coming up every round
    assert pricing.priority({**d, "prices_tried_at": NOW - timedelta(hours=1)}, NOW) is None
