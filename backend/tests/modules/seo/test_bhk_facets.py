"""Size pages from published prices: /projects/area/<place>/2-bhk (app/modules/seo/facets.py, phrases.py, grow.py)."""
from datetime import datetime, timedelta, timezone

from app.modules.newsroom.store import Store
from app.modules.seo import facets, grow, phrases
from app.modules.seo.facets import Facet

from ..fakes import FakeDb

NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)


def _doc(i, rows, completion="2028-06-30", registered="2025-03-01", place="lohegaon"):
    return {"_id": f"P{i}", "regno": f"P{i}", "name": f"Project {i}", "page_slug": f"project-{i}", "pune_place": place,
            "promoter": f"Builder {i}", "completion_now": completion, "registered_on": registered, "units_total": 100,
            "page_text": "Written.", "prices": {"at": NOW - timedelta(days=3), "rows": [
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


def test_members_cheapest_first_with_the_price_as_reason_and_no_site_named():
    listed = facets.members(Facet("lohegaon", "all", bhk=2), DOCS, NOW)
    assert [d["_id"] for d, _ in listed] == ["P2", "P1", "P3"]
    assert listed[0][1] == "2 BHK from ₹69 lakh"
    assert listed[1][1] == "2 BHK ₹78 lakh to ₹85 lakh"


def test_view_title_h1_answer_and_prices():
    v = facets.facet_view(Facet("lohegaon", "all", bhk=2), DOCS, NOW)
    assert v["title"].startswith("2 BHK Flats in Lohegaon, Pune") and "3 Projects" in v["title"] and len(v["title"]) <= 62
    assert v["h1"] == "2 BHK flats in new projects in Lohegaon, Pune"
    assert v["indexable"] and v["bhk"] == 2 and v["rows"][0]["price_from"] == 6_900_000
    assert "3 projects" in v["answer"] and "₹69 lakh to ₹91 lakh" in v["answer"]
    assert all("site" not in str(r) for r in v["rows"]) and "price_source" not in v["rows"][0]


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
                   "path": "/projects/area/lohegaon/2-bhk", "key": "lohegaon|all|bhk=2"}
    assert [s["bhk"] for s in out["sizes"]] == [2]   # one 1 BHK and one 3 BHK price is not a price range


def test_a_size_list_leaves_out_a_project_with_every_home_booked():
    gone = {**_doc(7, [("2 BHK", 4_500_000, None)]), "units_booked": 100}   # 100 of 100 booked
    listed = [d["_id"] for d, _ in facets.members(Facet("lohegaon", "all", bhk=2), [*DOCS, gone], NOW)]
    assert "P7" not in listed and "P1" in listed



def test_a_list_is_in_search_only_when_three_of_its_projects_are():
    f = Facet("lohegaon", "all")
    register_only = [{k: v for k, v in d.items() if k != "prices"} for d in DOCS]
    v = facets.facet_view(f, register_only, NOW)
    assert v["count"] == 5 and not v["indexable"]           # five projects listed, written but none with a fact of its own
    facts = {"web_facts": {"facts": [{"key": "towers"}]}}
    two = [{**d, **facts} if d["_id"] in ("P1", "P2") else d for d in register_only]
    assert not facets.facet_view(f, two, NOW)["indexable"]
    three = [{**d, **facts} if d["_id"] in ("P1", "P2", "P3") else d for d in register_only]
    assert facets.facet_view(f, three, NOW)["indexable"]


async def test_the_live_page_list_counts_each_pages_projects_and_says_whether_search_may_index_it():
    # 2026-10-27..29 the list raised on every call (records handed where (record, reason) pairs were expected): /facets was a 500
    db = FakeDb()
    for d in DOCS:
        await Store(db).projects.insert_one(dict(d))
    await db.get_collection(grow.PAGES).insert_one({"_id": "lohegaon|all|bhk=2", "status": "live"})
    out = await grow.live_pages(db, NOW)
    assert [(p["path"], p["count"], p["indexable"]) for p in out] == [("/projects/area/lohegaon/2-bhk", 3, True)]


async def test_a_size_without_a_live_page_is_shown_without_a_link():
    # the crawl of 2026-10-30 found area pages linking /kharadi/4-bhk and others that answer 404
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.modules.seo import router as sr
    db = FakeDb()
    for d in DOCS:
        await Store(db).projects.insert_one(dict(d))
    app = FastAPI()
    app.include_router(sr.public_router, prefix="/p")
    app.dependency_overrides[sr.get_db] = lambda: db
    get = lambda: TestClient(app).get("/p/place-prices/lohegaon").json()["sizes"]
    assert [(s["bhk"], s["path"]) for s in get()] == [(2, None)] and "key" not in get()[0]
    await db.get_collection(grow.PAGES).insert_one({"_id": "lohegaon|all|bhk=2", "status": "live"})
    assert get()[0]["path"] == "/projects/area/lohegaon/2-bhk"


def test_phases_of_one_project_are_one_row_with_the_cheapest_price():
    phase = lambda i, n, lo: {**_doc(i, [("2 BHK", lo, None)]), "name": f"Pristine O2 World Part {n}", "promoter": "Logipark"}
    listed = facets.members(Facet("lohegaon", "all", bhk=2), [phase(11, 1, 8_200_000), phase(12, 2, 8_000_000), _doc(3, [("2 BHK", 9_100_000, None)])], NOW)
    assert [d["_id"] for d, _ in listed] == ["P12", "P3"]


def test_a_card_carries_every_size_published_price_smallest_first():
    # buyers compare by size: a card shows one price per size, not only the cheapest (docs/plan/rival-housiey-ravet.md L5)
    assert facets.size_prices(DOCS[0], NOW) == [{"bhk": 2, "from_inr": 7_800_000}, {"bhk": 3, "from_inr": 11_000_000}]
    assert facets.size_prices(DOCS[1], NOW) == [{"bhk": 2, "from_inr": 6_900_000}]   # 2.5 BHK counts with the 2 BHK homes
    assert facets.size_prices(DOCS[5], NOW) == []                                     # a price too old to show
