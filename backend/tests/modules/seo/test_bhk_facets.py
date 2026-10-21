"""Size pages from published prices: /projects/area/<place>/2-bhk (app/modules/seo/facets.py, phrases.py, grow.py)."""
from datetime import datetime, timedelta, timezone

from app.modules.seo import facets, grow, phrases
from app.modules.seo.facets import Facet

NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)


def _doc(i, rows, completion="2028-06-30", registered="2025-03-01", place="lohegaon"):
    return {"_id": f"P{i}", "regno": f"P{i}", "name": f"Project {i}", "page_slug": f"project-{i}", "pune_place": place,
            "promoter": f"Builder {i}", "completion_now": completion, "registered_on": registered, "units_total": 100,
            "prices": {"at": NOW - timedelta(days=3), "rows": [
                {"bhk": b, "from_inr": lo, "to_inr": hi, "official": i % 2 == 0,
                 "sources": [{"site": "builder.in" if i % 2 == 0 else "site-a.com"}] + ([] if i % 2 == 0 else [{"site": "site-b.com"}])}
                for b, lo, hi in rows]}}


DOCS = [
    _doc(1, [("2 BHK", 7_800_000, 8_500_000), ("3 BHK", 11_000_000, None)]),
    _doc(2, [("2.5 BHK", 6_900_000, None)]),
    _doc(3, [("2 BHK", 9_100_000, 9_600_000)]),
    _doc(4, [("1 BHK", 4_200_000, None)]),
    _doc(5, [("2 BHK", 5_000_000, None)], completion="2020-01-31"),             # finished long ago: not on the "all" list
    {**_doc(6, [("2 BHK", 4_000_000, None)]), "prices": {"at": NOW - timedelta(days=90), "rows": [
        {"bhk": "2 BHK", "from_inr": 4_000_000, "official": True, "sources": []}]}},  # price too old to show
]


def test_url_key_and_parse_round_trip():
    f = Facet("lohegaon", "all", bhk=2)
    assert f.path == "/projects/area/lohegaon/2-bhk" and f.key == "lohegaon|all|bhk=2" and not f.is_place_page
    assert facets.parse("lohegaon", ["2-bhk"]) == f and facets.from_key(f.key) == f
    g = facets.parse("lohegaon", ["possession-2027", "2-bhk", "ready-to-move"])
    assert g.path == "/projects/area/lohegaon/ready-to-move/2-bhk/possession-2027" and g.kind == "ready-to-move+bhk+possession"
    assert facets.parse("lohegaon", ["7-bhk"]) is None
    assert f.parent() == Facet("lohegaon")


def test_members_cheapest_first_with_sourced_reason():
    listed = facets.members(Facet("lohegaon", "all", bhk=2), DOCS, NOW)
    assert [d["_id"] for d, _ in listed] == ["P2", "P1", "P3"]
    assert listed[0][1] == "2 BHK from ₹69 lakh (the builder's site)"
    assert listed[1][1] == "2 BHK ₹78 lakh to ₹85 lakh (site-a.com and site-b.com)"


def test_view_title_h1_answer_and_prices():
    v = facets.facet_view(Facet("lohegaon", "all", bhk=2), DOCS, NOW)
    assert v["title"].startswith("2 BHK Flats in Lohegaon, Pune") and "3 Projects" in v["title"] and len(v["title"]) <= 62
    assert v["h1"] == "2 BHK flats in new projects in Lohegaon, Pune"
    assert v["indexable"] and v["bhk"] == 2 and v["rows"][0]["price_from"] == 6_900_000
    assert "3 projects" in v["answer"] and "₹69 lakh to ₹91 lakh" in v["answer"]


def test_intent_with_size_keeps_the_intent_order():
    listed = facets.members(Facet("lohegaon", "new-launches", bhk=2), DOCS, NOW)
    assert {d["_id"] for d, _ in listed} <= {"P1", "P2", "P3", "P5"}
    assert all(why.startswith("2 BHK") and "registered with MahaRERA" in why for _, why in listed)


def test_phrases_map_sizes_to_size_pages():
    assert phrases.parse("2 bhk flats in lohegoan")["facet"] == Facet("lohegaon", "all", bhk=2)
    assert phrases.parse("3bhk flat price in wagholi")["facet"] == Facet("wagholi", "all", bhk=3)
    assert phrases.parse("ready to move 2 bhk flats kharadi")["facet"] == Facet("kharadi", "ready-to-move", bhk=2)
    budget = phrases.parse("2 bhk under 50 lakh wagholi")
    assert budget["facet"] is None and budget["existing"]


def test_seeds_include_size_pages():
    keys = {f.key for f in facets.seeds(DOCS)}
    assert {"lohegaon|all|bhk=1", "lohegaon|all|bhk=2", "lohegaon|all|bhk=3", "lohegaon|new-launches"} <= keys


def test_overlap_only_against_pages_of_the_same_size():
    cand = {"facet": Facet("lohegaon", "all", bhk=2), "source": "seed", "impressions": 0, "sources": set()}
    live = [{"_id": "lohegaon|new-launches", "place": "lohegaon", "regnos": ["P1", "P2", "P3"]}]
    assert grow.gate(cand, ["P1", "P2", "P3"], live)["ok"]
    live.append({"_id": "lohegaon|top|bhk=2", "place": "lohegaon", "regnos": ["P1", "P2", "P3"]})
    assert not grow.gate(cand, ["P1", "P2", "P3"], live)["distinct"]


def test_place_prices_per_size():
    out = facets.place_prices("lohegaon", DOCS, NOW)
    two = next(s for s in out["sizes"] if s["bhk"] == 2)
    assert two == {"bhk": 2, "projects": 3, "low": 6_900_000, "high": 9_100_000, "cheapest": {"name": "Project 2", "slug": "project-2"},
                   "path": "/projects/area/lohegaon/2-bhk"}
    assert [s["bhk"] for s in out["sizes"]] == [2]   # one 1 BHK and one 3 BHK price is not a price range
