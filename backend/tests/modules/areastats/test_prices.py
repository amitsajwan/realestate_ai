"""A price must fit the size its own line states (app/modules/areastats/prices.py, RATE_PER_SQFT)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import prices

NOW = datetime(2026, 10, 24, 9, 0, tzinfo=timezone.utc)


def stored(*rows):
    return {"at": NOW - timedelta(days=2), "rows": list(rows)}


def row(bhk, from_inr, quote, to_inr=None):
    return {"bhk": bhk, "from_inr": from_inr, "to_inr": to_inr, "official": False,
            "sources": [{"site": "a.example", "url": "https://a.example/p", "official": False, "quote": quote},
                        {"site": "b.example", "url": "https://b.example/p", "official": False, "quote": "other line"}]}


def test_the_sizes_a_line_states_are_read_and_rates_are_not():
    assert prices.areas_in("2 BHK 740 - 957 sq.ft ₹72 L - 1.05 Cr") == [740, 957]
    assert prices.areas_in("3 BHK | 1,250 Sq. Ft. | ₹ 1.25 Cr") == [1250]
    assert prices.areas_in("2BHK 650sqft 75L") == [650]
    assert prices.areas_in("4 BHK 2,244 square feet") == [2244]
    assert prices.areas_in("₹ 9,500 / sq.ft for 2 BHK") == []
    assert prices.areas_in("Rs 12,000 sq ft onwards") == []
    assert prices.areas_in("Township on 1,25,000 sq ft of land") == []


def test_a_price_too_high_for_its_size_is_refused_when_read():
    # "9.6 Cr" for a 750 sq ft 2 BHK is ₹1.28 lakh a sq ft: a misread unit or another project's line
    line = "2 BHK 750 sq ft ₹ 9.6 Cr"
    got = prices.row_ok({"size": "2 BHK", "from_inr": 96_000_000, "from_quote": line}, f"Prices\n{line}\nContact")
    assert got is None


def test_a_price_too_low_for_its_size_is_refused_when_read():
    line = "3 BHK 1,400 sq ft ₹ 25 L"   # ₹1,786 a sq ft: a booking amount or a typo
    assert prices.row_ok({"size": "3 BHK", "from_inr": 2_500_000, "from_quote": line}, line) is None


def test_a_price_that_fits_its_size_is_kept():
    line = "2 BHK 740 - 957 sq.ft ₹72 L - 1.05 Cr"
    got = prices.row_ok({"size": "2 BHK", "from_inr": 7_200_000, "to_inr": 10_500_000, "from_quote": line}, line)
    assert got is not None
    assert (got["from_inr"], got["to_inr"]) == (7_200_000, 10_500_000)


def test_the_highest_price_is_checked_against_the_largest_size():
    # ₹72 L for 740 sq ft is fine, ₹10.5 Cr for 957 sq ft is not
    line = "2 BHK 740 - 957 sq.ft ₹72 L - 10.5 Cr"
    assert prices.row_ok({"size": "2 BHK", "from_inr": 7_200_000, "to_inr": 105_000_000, "from_quote": line}, line) is None


def test_a_line_without_a_size_is_not_checked():
    line = "2 BHK starting ₹ 96 L"
    assert prices.row_ok({"size": "2 BHK", "from_inr": 9_600_000, "from_quote": line}, line) is not None


def test_a_plot_is_not_checked_against_its_area():
    assert prices.rate_ok({"bhk": "Plot", "from_inr": 2_000_000}, "Plot 2,000 sq ft ₹ 20 L")


def test_a_stored_price_read_before_the_check_leaves_the_pages():
    good = row("2 BHK", 9_600_000, "2 BHK 750 sq ft ₹ 96 L")
    bad = row("3 BHK", 96_000_000, "3 BHK 1,100 sq ft ₹ 9.6 Cr")
    shown = prices.public(stored(good, bad), NOW)
    assert [r["bhk"] for r in shown["rows"]] == ["2 BHK"]
    assert prices.price_from({"prices": stored(good, bad)}, NOW) == 9_600_000


def test_a_project_whose_only_price_fails_shows_none():
    bad = row("3 BHK", 96_000_000, "3 BHK 1,100 sq ft ₹ 9.6 Cr")
    assert prices.public(stored(bad), NOW) is None
    assert prices.price_from({"prices": stored(bad)}, NOW) is None


def test_pages_get_the_size_the_lowest_price_is_for_when_its_line_states_it():
    shown = prices.public(stored(row("2 BHK", 7_200_000, "2 BHK 740 - 957 sq.ft ₹72 L - 1.05 Cr", 10_500_000),
                                 row("3 BHK", 12_000_000, "3 BHK from ₹ 1.2 Cr")), NOW)
    assert [(r["bhk"], r["sqft"]) for r in shown["rows"]] == [("2 BHK", 740), ("3 BHK", None)]


def test_the_check_is_made_on_the_picked_sites_line_not_the_other_one():
    # the first source is the price shown; the second only backs it, so its line says nothing about this amount
    r = row("2 BHK", 9_600_000, "2 BHK from ₹ 96 L")
    r["sources"][1]["quote"] = "2 BHK 300 sq ft ₹ 96 L"
    assert prices.public(stored(r), NOW)["rows"][0]["bhk"] == "2 BHK"
