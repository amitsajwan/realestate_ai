"""Who sits above us on Google, read from the searches we already ran: the rival to study is Google's pick in each area, not one
we chose (docs/plan/rival-housiey-ravet.md: Housiey led Ravet while the board only watched MagicBricks)."""
from datetime import datetime, timezone

from app.modules.seo import note, scoreboard
from app.modules.seo.report import _board

NOW = datetime(2026, 11, 6, 9, 0, tzinfo=timezone.utc)
HOST = "avasetu.in"


def organic(position: int, link: str) -> dict:
    return {"type": "organic", "position": position, "link": link}


DOCS = [
    {"_id": "new projects in ravet pune", "area": "ravet", "results": [
        organic(1, "https://www.nobroker.in/new-projects-in-ravet_pune"), organic(2, "https://housiey.com/in/pune/ravet"),
        organic(3, "https://housiey.com/projects/rama-celestial-city-phase-2"), organic(5, "https://avasetu.in/projects/area/ravet"),
        organic(7, "https://www.magicbricks.com/ravet"), {"type": "organic", "ad": True, "position": 1, "link": "https://ads.example.com"}]},
    {"_id": "flats in wagholi", "area": "wagholi", "results": [
        organic(1, "https://avasetu.in/projects/area/wagholi"), organic(2, "https://housiey.com/in/pune/wagholi")]},
    {"_id": "rohan abhilasha", "area": None, "results": [organic(1, "https://housiey.com/projects/rohan-abhilasha")]},
]


def test_a_site_is_counted_once_per_search_and_only_when_above_us_or_we_are_absent():
    rows = {t["site"]: t for t in scoreboard.leaders(DOCS, HOST)}
    assert rows["housiey.com"] == {"site": "housiey.com", "searches": 3, "above_us": 2, "top3": 3}
    assert rows["nobroker.in"] == {"site": "nobroker.in", "searches": 1, "above_us": 1, "top3": 1}
    assert rows["magicbricks.com"]["above_us"] == 0
    assert HOST not in rows and "ads.example.com" not in rows
    assert scoreboard.leaders(DOCS, HOST)[0]["site"] == "housiey.com"


def test_leaders_are_kept_per_area_for_the_searches_tied_to_one():
    areas = scoreboard.area_leaders(DOCS, HOST)
    assert set(areas) == {"ravet", "wagholi"}
    assert [t["site"] for t in areas["ravet"]][:2] == ["housiey.com", "nobroker.in"]
    assert areas["wagholi"][0] == {"site": "housiey.com", "searches": 1, "above_us": 0, "top3": 1}


def test_the_weekly_note_names_the_sites_above_us_most_often():
    board = {"searches": 3, "leaders": scoreboard.leaders(DOCS, HOST)}
    assert scoreboard.leader_line(board) == "Above us most often, of 3 Google searches: housiey.com 2, nobroker.in 1."
    assert scoreboard.leader_line({"searches": 0}) == "" and scoreboard.leader_line({"searches": 3, "leaders": []}) == ""
    week = note.summary(None, None, {}, board, 0)
    assert len(note.notes(week, "AI", "", scoreboard.leader_line(board))) == 3


async def test_the_weekly_board_stores_the_leaders_and_rankings_shows_them():
    from app.modules.areastats.websearch import RESULTS
    from app.modules.newsroom.store import Store
    from ..fakes import FakeDb

    store = Store(FakeDb())
    for d in DOCS:
        await store.db.get_collection(RESULTS).insert_one({**d, "at": NOW})
    assert await scoreboard.run_once(store, NOW) is not None
    shown = _board(await store.get_mark(scoreboard.MARK))
    assert shown["leaders"][0]["site"] == "housiey.com" and shown["area_leaders"]["ravet"][0]["site"] == "housiey.com"
