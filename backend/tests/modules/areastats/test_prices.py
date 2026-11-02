"""A price must fit the size its own line states (app/modules/areastats/prices.py, RATE_PER_SQFT)."""
import asyncio
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


# Price history (docs/plan/seo-system.md 8b): the sites show only today's price, so each change is kept, dated.

def test_a_first_price_is_kept_dated_in_the_price_history():
    out = prices.history({}, [row("2 BHK", 6_900_000, "2 BHK 69 L")], NOW)
    assert out == {"price_history": [{"at": NOW, "bhk": "2 BHK", "from_inr": 6_900_000, "to_inr": None, "official": False,
                                      "sites": ["a.example", "b.example"]}]}


def test_an_unchanged_price_adds_no_reading():
    first = prices.history({}, [row("2 BHK", 6_900_000, "2 BHK 69 L")], NOW)
    assert prices.history(first, [row("2 BHK", 6_900_000, "2 BHK 69 L")], NOW + timedelta(days=30)) == {}


def test_a_changed_price_adds_a_reading_and_keeps_the_earlier_ones():
    doc = prices.history({}, [row("2 BHK", 6_900_000, "2 BHK 69 L"), row("3 BHK", 9_500_000, "3 BHK 95 L")], NOW)
    later = NOW + timedelta(days=60)
    out = prices.history(doc, [row("2 BHK", 7_200_000, "2 BHK 72 L"), row("3 BHK", 9_500_000, "3 BHK 95 L")], later)
    assert [(h["bhk"], h["from_inr"], h["at"]) for h in out["price_history"]] == [
        ("2 BHK", 6_900_000, NOW), ("3 BHK", 9_500_000, NOW), ("2 BHK", 7_200_000, later)]


def test_a_round_that_finds_no_price_removes_no_reading():
    doc = prices.history({}, [row("2 BHK", 6_900_000, "2 BHK 69 L")], NOW)
    assert prices.history(doc, [], NOW + timedelta(days=30)) == {}


def test_the_price_history_drops_only_its_oldest_readings_past_the_limit():
    doc = {"price_history": [{"at": NOW, "bhk": "2 BHK", "from_inr": 6_000_000 + i, "to_inr": None, "official": False, "sites": []}
                             for i in range(prices.PRICE_HISTORY)]}
    out = prices.history(doc, [row("2 BHK", 9_000_000, "2 BHK 90 L")], NOW)["price_history"]
    assert len(out) == prices.PRICE_HISTORY
    assert out[0]["from_inr"] == 6_000_001 and out[-1]["from_inr"] == 9_000_000


class _Budgeted:
    budgeted = True


def _reading_sites(monkeypatch, read):
    """gather with two property sites that both name the project; `read` gives each site's price readings."""
    src = [{"site": s, "url": f"https://{s}/p", "official": False} for s in ("a.example", "b.example")]

    async def results_for(*a, **k):
        return []

    async def fetch(url):
        return "<html>page</html>"

    async def read_prices(llm, s, name, text):
        return read(s), "ok"
    monkeypatch.setattr(prices.webfacts, "results_for", results_for)
    monkeypatch.setattr(prices.webfacts, "sources_for", lambda *a, **k: src)
    monkeypatch.setattr(prices.webfacts, "about_project", lambda *a, **k: (True, None))
    monkeypatch.setattr(prices.webfacts, "page_text", lambda raw: "2 BHK 69 L")
    monkeypatch.setattr(prices, "read_prices", read_prices)
    return fetch


def _site_price(s):
    return [{"bhk": "2 BHK", "from_inr": 6_900_000, "to_inr": None, "official": False, "site": s["site"], "url": s["url"],
             "quote": "2 BHK 69 L"}]


async def test_a_round_that_reads_a_price_stores_it_in_the_history(monkeypatch):
    fetch = _reading_sites(monkeypatch, _site_price)
    doc = {"_id": "P1", "regno": "P1", "name": "Project One"}
    _, fields = await prices.gather(None, doc, _Budgeted(), NOW, fetch=fetch, allow_search=False)
    assert fields["prices"]["rows"][0]["from_inr"] == 6_900_000
    assert [(h["bhk"], h["from_inr"]) for h in fields["price_history"]] == [("2 BHK", 6_900_000)]


async def test_last_good_prices_kept_while_sites_are_down_add_no_reading(monkeypatch):
    fetch = _reading_sites(monkeypatch, lambda s: [])
    kept = {"at": NOW - timedelta(days=3), "rows": [row("2 BHK", 6_900_000, "2 BHK 69 L")]}
    doc = {"_id": "P1", "regno": "P1", "name": "Project One", "prices": kept,
           "price_history": [{"at": NOW - timedelta(days=3), "bhk": "2 BHK", "from_inr": 6_900_000}]}
    _, fields = await prices.gather(None, doc, _Budgeted(), NOW, fetch=fetch, allow_search=False)
    assert fields["prices"]["rows"] == kept["rows"]
    assert "price_history" not in fields


def _project(name, **kw):
    return {"_id": "P1", "regno": "P1", "name": name, "promoter": "Logipark Warehousing LLP", "pune_place": "upper_kharadi",
            "pune_place_name": "Upper Kharadi", "locality": "wagholi", **kw}


class _Llm:
    budgeted = True

    def __init__(self, answers):
        self.answers, self.asked = answers, []

    async def json(self, system, user):
        self.asked.append(user)
        return self.answers


def _gather(monkeypatch, doc, pages_by_url, results, llm):
    async def stored(store, d, name, search, now):
        return results

    async def fetch(url):
        return pages_by_url.get(url)
    monkeypatch.setattr(prices.webfacts, "results_for", stored)
    return asyncio.run(prices.gather(None, doc, llm, NOW, fetch=fetch, allow_search=False))


def _result(link, title):
    return {"type": "organic", "link": link, "title": title, "snippet": "", "position": 1}


TWO_BHK = "2 BHK 750 sq ft ₹ 80 L"


def test_a_page_naming_the_whole_project_prices_one_registration_of_it(monkeypatch):
    page = f"<html><body>Pristine O2 World in Wagholi, Pune. RERA registered.\n{TWO_BHK}</body></html>"
    llm = _Llm({"prices": [{"size": "2 BHK", "from_inr": 8_000_000, "from_quote": TWO_BHK}]})
    urls = {"https://a.example/p": page, "https://b.example/p": page}
    results = [_result("https://a.example/p", "Pristine O2 World, Wagholi"), _result("https://b.example/p", "Pristine O2 World Pune")]
    st, fields = _gather(monkeypatch, _project("Pristine O2 World Part 3"), urls, results, llm)
    assert st["ok"]
    assert [r["bhk"] for r in fields["prices"]["rows"]] == ["2 BHK"]
    assert "Project: Pristine O2 World\n" in llm.asked[0]


def test_a_page_with_the_shorter_name_elsewhere_gives_no_price(monkeypatch):
    # the same words, another builder in another part of Pune
    page = f"<html><body>Pristine O2 World in Baner, Pune. RERA registered.\n{TWO_BHK}</body></html>"
    llm = _Llm({"prices": [{"size": "2 BHK", "from_inr": 8_000_000, "from_quote": TWO_BHK}]})
    st, fields = _gather(monkeypatch, _project("Pristine O2 World Part 3"), {"https://a.example/p": page},
                         [_result("https://a.example/p", "Pristine O2 World, Baner")], llm)
    assert not st["ok"]
    assert fields["prices"]["read"][0]["why"] == "page names another project of that name"
    assert llm.asked == []


def _web(monkeypatch, doc, urls, results, llm):
    async def stored(store, d, name, search, now):
        return results

    async def fetch(url):
        return urls.get(url)

    async def no_search(q):
        return []
    monkeypatch.setattr(prices.webfacts, "results_for", stored)
    return asyncio.run(prices.webfacts.gather(None, doc, llm, NOW, fetch=fetch, search=no_search))


TOWERS = "Pristine O2 World has 5 towers on 10 acres."
FACTS = {"facts": [{"key": "towers", "value": 5, "quote": TOWERS}]}


def test_web_facts_are_read_from_pages_naming_the_whole_project(monkeypatch):
    page = f"<html><body>Pristine O2 World in Wagholi, Pune. RERA registered.\n{TOWERS}</body></html>"
    urls = {"https://a.example/p": page, "https://b.example/p": page}
    results = [_result("https://a.example/p", "Pristine O2 World, Wagholi"), _result("https://b.example/p", "Pristine O2 World Pune")]
    st, fields = _web(monkeypatch, _project("Pristine O2 World Part 3"), urls, results, _Llm(FACTS))
    assert st["ok"] and [f["key"] for f in fields["web_facts"]["facts"]] == ["towers"]
    assert fields["web_facts"]["name"] == "Pristine O2 World"


def test_web_facts_refuse_a_page_with_the_shorter_name_elsewhere(monkeypatch):
    page = f"<html><body>Pristine O2 World in Baner, Pune. RERA registered.\n{TOWERS}</body></html>"
    llm = _Llm(FACTS)
    st, fields = _web(monkeypatch, _project("Pristine O2 World Part 3"), {"https://a.example/p": page},
                      [_result("https://a.example/p", "Pristine O2 World, Baner")], llm)
    assert not st["ok"] and llm.asked == []
    assert fields["web_facts"]["read"][0]["why"] == "page names another project of that name"

