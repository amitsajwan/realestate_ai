"""Budget pages from published prices: /projects/area/<place>/under-50-lakh (app/modules/seo/facets.py, phrases.py, grow.py)."""
from datetime import datetime, timedelta, timezone

from app.modules.seo import facets, grow, phrases
from app.modules.seo.facets import Facet

NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)


def _doc(i, rows, completion="2028-06-30", place="wagholi", name=None):
    return {"_id": f"P{i}", "regno": f"P{i}", "name": name or f"Project {i}", "page_slug": f"project-{i}", "pune_place": place,
            "promoter": f"Builder {i}", "completion_now": completion, "registered_on": "2025-03-01", "units_total": 100,
            "page_text": "Written.", "search_state": {"in": True, "at": NOW - timedelta(days=60)}, "prices": {"at": NOW - timedelta(days=3), "rows": [
                {"bhk": b, "from_inr": lo, "to_inr": None, "official": True, "sources": [{"site": "builder.in"}]} for b, lo in rows]}}


DOCS = [
    _doc(1, [("1 BHK", 3_900_000), ("2 BHK", 5_600_000)]),
    _doc(2, [("2 BHK", 4_800_000)]),
    _doc(3, [("1 BHK", 4_500_000), ("3 BHK", 11_000_000)]),
    _doc(4, [("3 BHK", 21_000_000)]),
    _doc(5, [("1 BHK", 3_000_000)], completion="2019-01-31"),   # finished long ago: not being sold
    _doc(6, [("2 BHK", 4_000_000)], place="kharadi"),
]


def test_budget_url_key_and_parse_round_trip():
    f = Facet("wagholi", "all", budget="under-50-lakh")
    assert f.path == "/projects/area/wagholi/under-50-lakh" and f.key == "wagholi|all|budget=under-50-lakh"
    assert facets.parse("wagholi", ["under-50-lakh"]) == f and facets.from_key(f.key) == f
    assert not f.is_place_page and f.kind == "all+budget" and f.parent() == Facet("wagholi")


def test_a_budget_list_stands_alone():
    assert facets.parse("wagholi", ["new-launches", "under-50-lakh"]) is None
    assert facets.parse("wagholi", ["2-bhk", "under-50-lakh"]) is None
    assert facets.parse("wagholi", ["under-40-lakh"]) is None


def test_members_are_projects_with_a_size_priced_in_the_band_cheapest_first():
    listed = facets.members(Facet("wagholi", "all", budget="under-50-lakh"), DOCS, NOW)
    assert [d["_id"] for d, _ in listed] == ["P1", "P3", "P2"]
    assert listed[0][1] == "1 BHK from ₹39 lakh"
    mid = facets.members(Facet("wagholi", "all", budget="50-lakh-to-1-crore"), DOCS, NOW)
    assert [d["_id"] for d, _ in mid] == ["P1"]   # a project with homes in two bands is on both


def test_budget_view_title_h1_answer_and_card_price():
    v = facets.facet_view(Facet("wagholi", "all", budget="under-50-lakh"), DOCS, NOW)
    assert v["title"].startswith("Flats Under 50 Lakh in Wagholi, Pune") and "3 Projects" in v["title"] and len(v["title"]) <= 62
    assert v["h1"] == "New projects with flats under 50 lakh in Wagholi, Pune"
    assert v["budget"] == "under-50-lakh" and v["budget_label"] == "under 50 lakh" and v["indexable"]
    assert v["rows"][0]["price_from"] == 3_900_000 and v["rows"][0]["budget_sizes"] == [{"bhk": 1, "from_inr": 3_900_000}]
    assert "3 projects" in v["answer"] and "₹39 lakh to ₹48 lakh" in v["answer"]


def test_budget_searches_map_to_their_page_only_when_the_band_is_ours():
    assert phrases.parse("flats under 50 lakhs in wagholi")["facet"] == Facet("wagholi", "all", budget="under-50-lakh")
    assert phrases.parse("property in kharadi 1 to 2 cr")["facet"] == Facet("kharadi", "all", budget="1-to-2-crore")
    other = phrases.parse("flats under 40 lakh in wagholi")
    assert other["facet"] is None and other["existing"]


def test_focus_areas_seed_their_budget_pages():
    keys = {f.key for f in facets.seeds(DOCS)}
    assert {f"wagholi|all|budget={b}" for b in facets.BUDGETS} <= keys


def test_a_budget_page_is_not_held_back_by_overlap_with_another_list():
    cand = {"facet": Facet("wagholi", "all", budget="under-50-lakh"), "impressions": 0, "sources": set(), "source": "seed"}
    live = [{"_id": "wagholi|top", "place": "wagholi", "regnos": ["P1", "P2", "P3"]}]
    assert grow.gate(cand, ["P1", "P2", "P3"], live)["ok"]
