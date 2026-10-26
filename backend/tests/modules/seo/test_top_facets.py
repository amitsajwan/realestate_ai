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


def test_sold_out_projects_are_not_ranked_and_the_rest_go_by_share_booked():
    listed = facets.members(Facet("kharadi", "top"), DOCS, NOW)
    assert [d["_id"] for d, _ in listed] == ["P3", "P4", "P5", "P6"]
    assert listed[0][1] == "58 of 661 homes still open, 603 booked (91%)"


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
                                  "Project 3 leads on homes booked: 58 of 661 homes still open")
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
