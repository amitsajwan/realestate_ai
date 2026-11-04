"""The "top projects in <place>" list: ranked among projects a buyer can still buy, sold out ones apart (app/modules/seo/facets.py)."""
from datetime import datetime, timedelta, timezone

from app.modules.seo import facets
from app.modules.seo.facets import Facet

NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)


def _doc(i, total, booked, completion="2029-04-30", registered="2023-04-05", **more):
    return {"_id": f"P{i}", "regno": f"P{i}", "name": f"Project {i}", "page_slug": f"project-{i}", "pune_place": "kharadi",
            "promoter": f"Builder {i}", "completion_now": completion, "registered_on": registered, "units_total": total,
            "units_booked": booked, **more}


DOCS = [
    _doc(1, 27, 27),                                   # 100% booked: sold out, never ranked
    _doc(2, 470, 466),                                 # 99%, 4 open: nearly sold out
    _doc(3, 661, 603),                                 # 91%, 58 open
    _doc(4, 377, 332, profile={"photos": [{"path": "p4/a.jpg", "alt": "Tower", "source": "builder"}]},
         prices={"at": NOW - timedelta(days=3), "rows": [
             {"bhk": "3 BHK", "from_inr": 13_000_000, "official": True, "sources": []},
             {"bhk": "2 BHK", "from_inr": 9_500_000, "to_inr": 9_630_000, "official": True, "sources": []}]}),  # 88%
    _doc(5, 201, 107, completion="2027-03-31"),        # 53%, possession within a year
    _doc(6, 168, 12, registered="2026-06-01"),         # new launch, 156 open
]


def test_sold_out_projects_are_not_ranked_and_the_rest_go_by_homes_booked_a_month():
    listed = facets.members(Facet("kharadi", "top"), DOCS, NOW)
    # 603, 332 and 107 booked over 43 months; the launch's 12 over its first 5 months count as 6 months' worth
    assert [d["_id"] for d, _ in listed] == ["P3", "P4", "P5", "P6"]
    assert listed[0][1] == "about 14 homes booked a month since registration (Apr 2023); 58 of 661 homes still open"


def test_homes_booked_in_the_last_90_days_rank_first_once_there_are_two_readings():
    selling = {**DOCS[4], "booked_history": [{"at": NOW - timedelta(days=120), "booked": 60}, {"at": NOW - timedelta(days=5), "booked": 107}]}
    listed = facets.members(Facet("kharadi", "top"), [*DOCS[:4], selling, DOCS[5]], NOW)
    assert listed[0][0]["_id"] == "P5" and "47 homes booked" in listed[0][1] and "94 of 201 homes still open" in listed[0][1]


def test_the_sold_out_list_is_most_booked_first_and_says_what_is_left():
    gone = facets.sold_out(Facet("kharadi", "top"), DOCS, NOW)
    assert [(d["_id"], why) for d, why in gone] == [("P1", "27 of 27 homes booked"), ("P2", "466 of 470 homes booked, 4 still open")]


def test_view_counts_answer_and_card_fields():
    v = facets.facet_view(Facet("kharadi", "top"), DOCS, NOW)
    assert v["count"] == 4 and v["sold_out_count"] == 2 and [r["slug"] for r in v["sold_out"]] == ["project-1", "project-2"]
    assert v["answer"].startswith("As of 26 Oct 2026, 4 projects in Kharadi still have 10 or more homes open on MahaRERA. "
                                  "Project 3 sells fastest: about 14 homes booked a month since registration (Apr 2023); "
                                  "58 of 661 homes still open")
    assert "2 more are sold out or nearly" in v["answer"]
    by = {r["slug"]: r for r in v["rows"]}
    assert by["project-4"]["price"] == {"bhk": 2, "from_inr": 9_500_000, "to_inr": 9_630_000}
    assert by["project-4"]["photo"] == {"url": "/uploads/p4/a.jpg", "alt": "Tower", "source": "builder"}
    assert by["project-3"]["price"] is None and by["project-3"]["photo"] is None and by["project-3"]["units_open"] == 58
    assert [by[f"project-{i}"]["stage"] for i in (3, 5, 6)] == ["under-construction", "possession-soon", "new-launch"]


def test_a_finished_project_reads_ready():
    assert facets.stage(_doc(9, 50, 20, completion="2026-03-31"), NOW) == "ready"


def test_offices_and_shops_are_neither_ranked_nor_listed_as_sold_out():
    offices = _doc(7, 142, 77, project_type="Commercial")
    shops = _doc(8, 28, 27, project_type="Commercial")
    assert "P7" not in [d["_id"] for d, _ in facets.members(Facet("kharadi", "top"), [*DOCS, offices], NOW)]
    assert "P8" not in [d["_id"] for d, _ in facets.sold_out(Facet("kharadi", "top"), [*DOCS, shops], NOW)]


def test_move_in_now_lists_only_finished_homes_with_ten_or_more_left():
    docs = [_doc(10, 224, 142, completion="2026-03-31"),                            # 82 open: listed
            _doc(11, 142, 142, completion="2026-02-28"),                            # every home booked
            _doc(12, 52, 50, completion="2026-01-31"),                              # 2 open
            _doc(13, 0, 0, completion="2025-12-31"),                                # count unknown
            _doc(14, 90, 40, completion="2025-11-30", project_type="Commercial")]   # offices
    listed = facets.members(Facet("kharadi", "ready-to-move"), docs, NOW)
    assert [(d["_id"], why) for d, why in listed] == [("P10", "completion filed for 31 Mar 2026, now passed, 82 of 224 homes not booked")]


# ---- the top list ranks how fast a project sells, one row per project (2026-11-03) ------------------------------------------

def test_a_younger_project_selling_faster_ranks_above_an_older_one_nearly_sold():
    old = _doc(20, 620, 600, registered="2020-10-01")        # 97% booked over six years: about 8 a month
    young = _doc(21, 400, 180, registered="2025-04-26")      # 45% booked in 18 months: 10 a month
    listed = facets.members(Facet("kharadi", "top"), [old, young], NOW)
    assert [d["_id"] for d, _ in listed] == ["P21", "P20"]


def test_registrations_of_one_project_are_one_row_named_once():
    one = dict(promoter="Pristine Properties")
    docs = [_doc(30, 300, 150, name="Pristine O2 World Part 1", **one), _doc(31, 300, 200, name="Pristine O2 World Part 2", **one),
            _doc(32, 300, 100, name="Other Homes", **one)]
    listed = facets.members(Facet("kharadi", "top"), docs, NOW)
    assert [d["_id"] for d, _ in listed] == ["P31", "P32"]


def test_small_buildings_are_left_out_unless_their_project_is_big_enough():
    tiny = _doc(40, 24, 10)
    towers = [_doc(41, 24, 10, name="Shanti Anand A Wing", promoter="Shanti"), _doc(42, 24, 12, name="Shanti Anand B Wing", promoter="Shanti")]
    listed = facets.members(Facet("kharadi", "top"), [tiny, *towers], NOW)
    assert [d["_id"] for d, _ in listed] == ["P42"]


def test_a_row_says_whether_the_date_moved_and_the_builders_date_record():
    b = dict(promoter="Kolte Patil Developers")
    mine = _doc(50, 300, 150, completion="2029-10-31", completion_at_registration="2028-06-30", **b)
    # five more of the builder's projects: four kept their date, one moved a year
    others = [_doc(51 + i, 100, 50, completion="2028-06-30", completion_at_registration="2028-06-30", pune_place="baner", **b) for i in range(4)]
    others.append(_doc(55, 100, 50, completion="2029-06-30", completion_at_registration="2028-06-30", pune_place="baner", **b))
    listed = facets.members(Facet("kharadi", "top"), [mine, *others], NOW)
    why = listed[0][1]
    # 16 months, less the 4 of MahaRERA's 2026 order
    assert "; completion date moved 12 months later; " in why
    assert why.endswith("the builder kept the date on 4 of 6 Pune projects")


def test_a_kept_date_is_said_as_not_moved_by_the_builder():
    kept = _doc(60, 300, 150, completion="2029-04-30", completion_at_registration="2029-04-30")
    assert facets.members(Facet("kharadi", "top"), [kept], NOW)[0][1].endswith("completion date not moved by the builder")


def test_a_row_names_the_brand_buyers_search_and_keeps_the_company_it_is_filed_under():
    godrej = _doc(70, 1582, 323, name="Godrej Aqua Vista", promoter="Oxford Realty LLP")
    v = facets.facet_view(Facet("kharadi", "top"), [*DOCS, godrej], NOW)
    by = {r["slug"]: r for r in v["rows"]}
    assert by["project-70"]["builder_name"] == "Godrej Properties" and by["project-70"]["promoter"] == "Oxford Realty LLP"
    assert by["project-3"]["builder_name"] == "Builder 3"
    assert facets.builder_name({"name": "Godrej Aqua Vista"}) is None   # no promoter on record: never joined by name alone


def test_picks_name_one_project_per_need_with_the_fact_that_puts_it_there():
    v = facets.facet_view(Facet("kharadi", "top"), DOCS, NOW)
    assert [(p["need"], p["slug"], p["fact"]) for p in v["picks"]] == [
        ("Selling fastest", "project-3", "about 14 homes booked a month since registration (Apr 2023)"),
        ("Lowest checked price", "project-4", "2 BHK from ₹95 lakh"),
        ("Earliest possession", "project-5", "possession filed for 31 Mar 2027"),
        ("Most homes to choose from", "project-6", "156 of 168 homes open"),
        ("Just launched", "project-6", "registered Jun 2026, 12 of 168 homes booked"),
    ]


def test_a_builder_that_keeps_its_dates_is_picked_only_where_this_project_kept_its_own():
    b = dict(promoter="Kolte Patil Developers")
    others = [_doc(81 + i, 100, 50, completion="2028-06-30", completion_at_registration="2028-06-30", pune_place="baner", **b) for i in range(5)]
    moved = _doc(80, 300, 150, completion="2029-10-31", completion_at_registration="2028-06-30", **b)
    kept = _doc(86, 200, 60, completion="2029-04-30", completion_at_registration="2029-04-30", **b)
    need = lambda docs: [p for p in facets.facet_view(Facet("kharadi", "top"), [*DOCS, *docs], NOW)["picks"]
                         if p["need"] == "Builder that keeps its dates"]
    assert need([moved, *others]) == []
    got = need([moved, kept, *others])
    assert [p["slug"] for p in got] == ["project-86"]
    assert got[0]["fact"] == "date not moved; the builder kept the date on 6 of 7 Pune projects"


def test_a_list_too_short_for_picks_shows_none_and_picks_follow_the_records():
    assert facets.facet_view(Facet("kharadi", "top"), [DOCS[2]], NOW)["picks"] == []
    # once another project gets a lower checked price, that pick moves to it on the next build
    cheaper = {**DOCS[4], "prices": {"at": NOW - timedelta(days=1), "rows": [{"bhk": "2 BHK", "from_inr": 7_900_000, "official": True, "sources": []}]}}
    picks = facets.facet_view(Facet("kharadi", "top"), [*DOCS[:4], cheaper, DOCS[5]], NOW)["picks"]
    assert next(p for p in picks if p["need"] == "Lowest checked price")["slug"] == "project-5"
    assert facets.facet_view(Facet("kharadi", "all", bhk=2), DOCS, NOW)["picks"] == []


def test_every_place_gets_picks_from_its_own_projects_and_a_thin_one_gets_none():
    loh = [{**d, "_id": "L" + d["_id"], "regno": "L" + d["regno"], "page_slug": "loh-" + d["page_slug"], "pune_place": "lohegaon",
            "pune_place_name": "Lohegaon"} for d in DOCS]
    picks = facets.facet_view(Facet("lohegaon", "top"), [*DOCS, *loh], NOW)["picks"]
    assert len(picks) == 5 and all(p["slug"].startswith("loh-") for p in picks)
    # two projects still selling there: the picks would only repeat the cards
    thin = [loh[2], loh[4]]
    assert facets.facet_view(Facet("lohegaon", "top"), [*DOCS, *thin], NOW)["picks"] == []


def test_a_top_list_title_counts_its_top_ten_says_most_booked_and_keeps_the_month_first():
    t = facets.title(Facet("kharadi", "top"), "Kharadi", 27, "Nov 2026")
    assert t == "Top 10 Projects in Kharadi, Pune (Nov 2026): Most Booked"
    assert facets.title(Facet("kharadi", "top"), "Kharadi", 5, "Nov 2026") == "Top 5 Projects in Kharadi, Pune (Nov 2026): Most Booked"
    # a long place name loses the tail before the month
    assert facets.title(Facet("x", "top"), "Pimpri Chinchwad", 27, "Nov 2026") == "Top 10 Projects in Pimpri Chinchwad, Pune (Nov 2026)"
    for name in ("Upper Kharadi", "Keshav Nagar", "Pimpri Chinchwad"):
        assert len(facets.title(Facet("x", "top"), name, 27, "Nov 2026")) <= 62
    assert "best" not in t.lower()   # a claim the facts do not make


def test_a_short_top_list_or_a_size_list_keeps_the_plain_title():
    assert facets.title(Facet("kharadi", "top"), "Kharadi", 2, "Nov 2026") == "Top Projects in Kharadi, Pune (Nov 2026): 2 on MahaRERA"
    assert facets.title(Facet("kharadi", "top", bhk=2), "Kharadi", 5, "Nov 2026").startswith("Top Projects with 2 BHK Flats")


def test_a_list_without_a_dated_change_takes_the_month_its_projects_were_last_read():
    read = NOW - timedelta(days=2)   # 24 Oct 2026
    docs = [{**d, "details_checked_at": read} for d in DOCS]
    v = facets.facet_view(Facet("kharadi", "top"), docs, NOW)
    assert v["month"] == "Oct 2026" and "(Oct 2026)" in v["title"]
    assert facets.facet_view(Facet("kharadi", "top"), DOCS, NOW)["month"] is None   # never today's month without a read
