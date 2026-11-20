"""The name and place a project is sold under, read from the pages that print its MahaRERA number (seo/marketname.py)."""
from datetime import datetime, timezone

from app.modules.seo import marketname

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)

ALTAMIRA = {"_id": "P52100079807", "regno": "P52100079807", "name": "ALTAMIRA BY VTP LUXE PHASE 1",
            "promoter": "MERCULUS CONSTRUWELL PRIVATE LIMITED", "pincode": "412207", "locality": "wagholi",
            "pune_place": "wagholi", "pune_place_name": "Wagholi", "group_name": "Altamira By VTP Luxe"}


def organic(pos, title, link):
    return {"type": "organic", "position": pos, "title": title, "link": link, "snippet": ""}


# Google's answer for "P52100079807" on 2026-11-04, as webfacts stored it
ALTAMIRA_RESULTS = [
    organic(1, "Altamira by VTP Luxe® | 3 BHK Luxury Residences in ...", "https://www.vtprealty.in/projects/vtp-altamira-kharadi-pune"),
    organic(2, "VTP Altair 3 Kharadi - Brochure, Pros&Cons, PriceSheet", "https://housiey.com/projects/vtp-altair-3"),
    organic(3, "VTP Altamira Kharadi Pune | Book 3 BHK Luxury Apartments", "https://www.starestate.com/vtp-altamira"),
    organic(4, "Altamira by Vtp Luxe - Kharadi", "https://www.beyondwalls.com/property/pune/kharadi/altamira-by-vtp-luxe"),
    organic(5, "Merculus Vtp Altair 3 in Upper Kharadi, Pune",
            "https://housing.com/in/buy/projects/page/344550-merculus-vtp-altair-3-by-merculus-construwell-private-limited-in-upper-kharadi"),
    organic(6, "VTP Altamira in Kharadi, Pune - PropertyPistol", "https://www.propertypistol.com/projects/vtp-altamira-kharadi-pid-19991"),
    organic(7, "VTP Altamira RERA Details - P52100079807, Pune",
            "https://www.squareyards.com/pune-residential-property/vtp-altamira/339735/project/rera/p52100079807"),
    organic(8, "Buy and Sell Property", "https://www.justlead.in/type/residential-apartment/vtp-altamira/16698"),
    organic(9, "VTP Altamira Kharadi | 3 BHK In Pune Price & Reviews", "https://punepropertyinvestor.com/vtp-altamira-kharadi/"),
]


def test_a_page_title_gives_the_name_without_its_place_or_what_the_searcher_wants():
    assert marketname.title_name("VTP Altamira Kharadi Pune | Book 3 BHK Luxury Apartments") == ["VTP", "Altamira"]
    assert marketname.title_name("VTP Altamira in Kharadi, Pune - PropertyPistol") == ["VTP", "Altamira"]
    assert marketname.title_name("Altamira by VTP Luxe® | 3 BHK Luxury Residences in ...") == ["Altamira", "by", "VTP", "Luxe"]


def test_the_name_most_sites_printing_the_number_use_becomes_the_market_name():
    got = marketname.read(ALTAMIRA, ALTAMIRA_RESULTS)
    assert got["name"] == "VTP Altamira"
    assert got["name_sites"] == 4


def test_the_place_most_of_those_sites_name_is_kept_when_it_is_not_ours():
    got = marketname.read(ALTAMIRA, ALTAMIRA_RESULTS)
    assert got["place"] == "Kharadi"


def test_another_project_of_the_same_builder_is_not_the_name():
    # "VTP Altair 3" carries no word of Altamira's own: two sites calling it that never make it the page's name
    results = ALTAMIRA_RESULTS[1:2] + ALTAMIRA_RESULTS[4:5]
    assert marketname.read(ALTAMIRA, results)["name"] is None


def test_one_site_alone_does_not_name_a_project():
    assert marketname.read(ALTAMIRA, ALTAMIRA_RESULTS[2:3])["name"] is None


def test_a_name_measured_on_our_own_searches_is_kept():
    doc = {**ALTAMIRA, "search_name": "Altamira VTP Wagholi"}
    assert marketname.read(doc, ALTAMIRA_RESULTS)["name"] is None


def test_a_portal_putting_the_promoter_before_the_name_does_not_rename_the_page():
    doc = {"_id": "P1", "regno": "P1", "name": "Maitri Meadows", "promoter": "HIGHSPOT DEVELOPERS", "pincode": "411047",
           "locality": "lohegaon", "pune_place": "lohegaon", "pune_place_name": "Lohegaon"}
    results = [organic(i, "Highspot Maitri Meadows Lohegaon | Price", f"https://site{i}.com/p") for i in range(1, 5)]
    assert marketname.read(doc, results)["name"] is None


def test_a_name_that_only_drops_the_place_or_the_phase_changes_nothing():
    doc = {"_id": "P2", "regno": "P2", "name": "Regency Astra Baner", "promoter": "REGENCY", "pincode": "411045",
           "locality": "baner", "pune_place": "baner", "pune_place_name": "Baner"}
    results = [organic(i, "Regency Astra - Baner, Pune", f"https://site{i}.com/p") for i in range(1, 5)]
    assert marketname.read(doc, results)["name"] is None


def test_a_far_place_a_marketer_names_is_not_where_the_project_is_sold():
    doc = {"_id": "P3", "regno": "P3", "name": "Green Acres", "promoter": "X", "pincode": "410506",
           "locality": None, "pune_place": "talegaon", "pune_place_name": "Talegaon"}
    results = [organic(i, f"Green Acres near Hinjawadi {i}", f"https://site{i}.com/hinjawadi") for i in range(1, 5)]
    assert marketname.read(doc, results)["place"] is None


def test_pages_that_would_share_one_name_get_none():
    towers = [{"_id": f"P{i}", "regno": f"P{i}", "name": f"Sunrise Vistas - T{i}", "promoter": "SUNRISE BUILDERS", "pincode": "411045",
               "locality": "baner", "pune_place": "baner", "pune_place_name": "Baner", "page_slug": f"sunrise-vistas-t{i}",
               "completion_now": "2030-01-01", "page_text": "x", "prices": {"rows": [{"bhk": "2 BHK", "from_inr": 1}]}}
              for i in (1, 4)]
    kept = {d["_id"]: [organic(j, "Sunrise Vistas Baner | Price", f"https://site{j}.com/p") for j in range(1, 5)] for d in towers}
    alone = marketname.read(towers[0], kept["P1"])
    assert alone["name"] == "Sunrise Vistas"          # each page alone would take it
    reads = [(d, g) for d, g in marketname.dedupe([(d, marketname.read(d, kept[d["_id"]])) for d in towers])]
    assert len(reads) == 2 and all(g["name"] is None for _, g in reads)


async def test_the_daily_step_writes_the_name_and_place_and_logs_a_measured_fix(monkeypatch):
    from app.modules.areastats import pages
    from app.modules.newsroom.store import Store
    from app.modules.seo import actions

    from ..fakes import FakeDb
    monkeypatch.setattr(marketname, "searchable", lambda d, now=None: True)
    monkeypatch.setattr(marketname, "_served", lambda d: True)
    db = FakeDb()
    await db.get_collection("projects").insert_one({**ALTAMIRA, "page_slug": "altamira-by-vtp-luxe-phase-1-wagholi"})
    await db.get_collection("web_search_results").insert_one({"_id": "P52100079807", "kind": "regno", "results": ALTAMIRA_RESULTS})
    store = Store(db)
    assert await marketname.run_once(store, NOW) == {"read": 1, "names": 1, "places": 1}
    doc = await store.project("P52100079807")
    assert doc["market_name"] == "VTP Altamira" and doc["market_place"] == "Kharadi"
    assert pages.shown_name(doc) == "VTP Altamira"
    fix = await db.get_collection(actions.ACTIONS).find_one({"fix": "name"})
    assert fix["new"] == "VTP Altamira" and fix["old"] is None
    assert await marketname.run_once(store, NOW) is None          # once a day
    assert await marketname.run_once(store, NOW, force=True) == {"read": 1, "names": 0, "places": 0}   # nothing new


async def test_switched_off_it_reads_nothing(monkeypatch):
    from app.modules.newsroom.store import Store

    from ..fakes import FakeDb
    monkeypatch.setenv("SEO_MARKET_NAMES", "off")
    assert await marketname.run_once(Store(FakeDb()), NOW) is None
