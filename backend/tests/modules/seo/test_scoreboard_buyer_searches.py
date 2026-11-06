"""The MagicBricks board counts only searches a buyer could type, and says which of our pages beat them for which search.
Until 2026-11-06 our own MahaRERA-number and builder-website lookups made up most of the count and showed in "win next"."""
from datetime import datetime, timezone

from app.modules.seo import scoreboard
from app.modules.seo.report import _board

NOW = datetime(2026, 11, 6, 9, 0, tzinfo=timezone.utc)
HOST = "avasetu.in"
MB = "https://www.magicbricks.com/x"


def organic(position: int, link: str) -> dict:
    return {"type": "organic", "position": position, "link": link}


DOCS = [
    {"_id": "flats in kharadi pune", "kind": "area", "area": "kharadi",
     "results": [organic(2, "https://avasetu.in/projects/area/kharadi"), organic(4, MB)]},
    {"_id": "2 bhk flats in wagholi pune", "kind": "area", "area": "wagholi",
     "results": [organic(1, MB), organic(6, "https://avasetu.in/projects/area/wagholi/2-bhk")]},
    {"_id": "casa saptak lohegaon pune", "kind": "project", "area": "lohegaon",
     "results": [organic(3, "https://avasetu.in/projects/casa-saptak-lohegaon")]},
    {"_id": "PR1260002501386", "kind": "regno", "area": "kharadi",
     "results": [organic(5, "https://avasetu.in/projects/a"), organic(4, MB)]},
    {"_id": "builder:P123", "kind": "builder", "area": "kharadi", "results": [organic(1, "https://avasetu.in/builders/b")]},
]


def test_our_own_lookups_are_not_counted_as_searches():
    kept = [d["_id"] for d in scoreboard.buyer_searches(DOCS)]
    assert kept == ["flats in kharadi pune", "2 bhk flats in wagholi pune", "casa saptak lohegaon pune"]


def test_each_row_names_the_page_of_ours_that_showed():
    rows = [scoreboard.row(d, HOST) for d in DOCS[:3]]
    assert [r["page"] for r in rows] == ["/projects/area/kharadi", "/projects/area/wagholi/2-bhk", "/projects/casa-saptak-lohegaon"]
    assert scoreboard.row({"_id": "q", "results": [organic(1, MB)]}, HOST)["page"] is None


def test_head_to_head_is_kept_apart_from_searches_magicbricks_never_showed_for():
    s = scoreboard.score([scoreboard.row(d, HOST) for d in scoreboard.buyer_searches(DOCS)])
    assert (s["searches"], s["both"], s["above_mb"], s["above_mb_when_shown"]) == (3, 2, 2, 1)
    assert [r["query"] for r in s["ahead_rows"]] == ["flats in kharadi pune"]
    assert [r["query"] for r in s["behind_rows"]] == ["2 bhk flats in wagholi pune"]
    assert s["by_kind"]["area"] == {"searches": 2, "ours": 2, "magicbricks": 2, "both": 2, "ahead": 1, "only_us": 0, "only_mb": 0}
    assert s["by_kind"]["project"]["only_us"] == 1 and "regno" not in s["by_kind"]


async def test_the_weekly_board_leaves_lookups_out_and_rankings_shows_the_pages():
    from app.modules.areastats.websearch import RESULTS
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb

    store = Store(FakeDb())
    for d in DOCS:
        await store.db.get_collection(RESULTS).insert_one({**d, "at": NOW})
    line = await scoreboard.run_once(store, NOW)
    assert line["searches"] == 3 and line["buyer_only"] is True
    shown = _board(await store.get_mark(scoreboard.MARK))
    assert shown["ahead_rows"][0]["page"] == "/projects/area/kharadi" and shown["both"] == 2
    assert not any(r["query"] == "PR1260002501386" for r in shown["next"] + shown["won"])
    assert set(shown["by_kind"]) == {"area", "project"}
