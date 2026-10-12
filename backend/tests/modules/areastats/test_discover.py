"""Projects found by number in Google results reach the register: candidate names, exact-number matches only, the watch list."""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.modules.areastats import discover, pages, refresh, watch
from app.modules.areastats.websearch import DISCOVERED
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 12, 6, 0, tzinfo=timezone.utc)
FIX = Path(__file__).parents[1] / "newsroom" / "fixtures" / "sources"
LAST = (FIX / "maharera_pune_last.html").read_text(encoding="utf-8")
# the fixture's first card, made into Lodha Camelot in Kharadi (411014)
CAMELOT_PAGE = (LAST.replace("PP1260002601949", "PR1260002501386").replace("Shantivan Homes Phase 8", "LODHA CAMELOT")
                .replace(">412210<", ">411014<", 1))
NONE_PAGE = '<div>Showing Final <span class="x">0</span> results</div>'
FLAKY = "<html>No Records Found</html>"
TITLE = "Lodha Camelot Kharadi Pune | Price & Floor Plans"


def site(pages_by_name: dict, asked: list):
    async def get(url):
        name = re.search(r"project_name=([^&]*)&", url).group(1).replace("%20", " ")
        asked.append(name)
        return pages_by_name.get(name, NONE_PAGE)
    return get


async def seen(store, regno="PR1260002501386", title=TITLE, at=NOW):
    await store.db.get_collection(DISCOVERED).insert_one(
        {"_id": regno, "first_seen": at, "last_seen": at, "seen": [{"query": "q", "title": title, "link": "https://x.in", "at": at}]})


def test_names_from_a_result_title():
    assert discover.names_from_title(TITLE) == ["Lodha Camelot", "Camelot"]
    assert discover.names_from_title("Kolte Patil Life Republic - 2 BHK flats in Hinjawadi") == [
        "Kolte Patil Life Republic", "Patil Life Republic", "Kolte Patil Life", "Republic"]
    assert discover.names_from_title("New launch projects in Wagholi") == []        # no name in it
    assert discover.names_from_title("Om | Pune") == []                             # too short to search


async def test_a_number_is_found_by_name_and_reaches_the_register_with_its_area_and_page():
    store, asked = Store(FakeDb()), []
    await seen(store)
    out = await discover.resolve(store, site({"Lodha Camelot": CAMELOT_PAGE}, asked), NOW)
    assert out == {"tried": "PR1260002501386", "found": "LODHA CAMELOT"} and asked == ["Lodha Camelot"]
    doc = await store.db.get_collection(DISCOVERED).find_one({"_id": "PR1260002501386"})
    assert doc["status"] == "found" and doc["maharera_id"] == 66815 and doc["pincode"] == "411014"

    # the watch source hands it to the register: Kharadi at once (pincode), and its own page
    watch.add_source(discover.SOURCE, lambda: discover.watch_items(store.db))
    await watch.sync(store, NOW)
    await pages.assign_all(store)
    p = await store.project("PR1260002501386")
    assert p["locality"] == "kharadi" and p["watched_by"] == ["web_discovered"] and p["page_slug"] == "lodha-camelot-kharadi"
    assert await discover.resolve(store, site({}, asked), NOW + timedelta(days=2)) == {"tried": None}   # nothing left to find


async def test_a_same_named_project_with_another_number_is_never_taken():
    store, asked = Store(FakeDb()), []
    await seen(store, regno="PR1260002501413")                 # Camelot's second tower: not on this results page
    out = await discover.resolve(store, site({"Lodha Camelot": CAMELOT_PAGE}, asked), NOW)
    assert out["found"] is None and asked == ["Lodha Camelot", "Camelot"]
    doc = await store.db.get_collection(DISCOVERED).find_one({"_id": "PR1260002501413"})
    assert doc["status"] == "open" and doc["tried_names"] == ["Lodha Camelot", "Camelot"]
    assert await discover.watch_items(store.db) == []
    # every name tried: a person sees it; a new title with a new name puts it back in line the next day
    assert [p["regno"] for p in await discover.pending(store)] == ["PR1260002501413"]
    await store.db.get_collection(DISCOVERED).update_one({"_id": "PR1260002501413"}, {"$set": {"seen": [
        {"title": TITLE}, {"title": "Camelot Kharadi Tower B by Lodha | Official"}]}})
    assert await discover.resolve(store, site({}, asked), NOW + timedelta(hours=2)) == {"tried": None}   # tried today already
    out = await discover.resolve(store, site({}, asked), NOW + timedelta(days=1))
    assert out["tried"] == "PR1260002501413" and asked[-3:] == ["Camelot Tower B", "Tower B", "Camelot Tower"]


async def test_a_site_that_does_not_answer_leaves_the_name_untried():
    store, asked = Store(FakeDb()), []
    await seen(store)

    async def down(url):
        asked.append(url)
        return FLAKY
    out = await discover.resolve(store, down, NOW)
    assert out["found"] is None
    doc = await store.db.get_collection(DISCOVERED).find_one({"_id": "PR1260002501386"})
    assert doc["tried_names"] == []                            # asked again on the next try


async def test_the_refresh_step_runs_discovery_before_the_watch_list():
    store, asked = Store(FakeDb()), []
    await seen(store)
    watch.add_source(discover.SOURCE, lambda: discover.watch_items(store.db))
    pages_by_name = {"Lodha Camelot": CAMELOT_PAGE}

    async def get(url):
        if "project_name=&" in url:                            # the pincode sweep: nothing new
            return NONE_PAGE
        return await site(pages_by_name, asked)(url)

    async def fetch(mid):
        return None
    out = await refresh.step(store, get, fetch, NOW, pages=1, limit=1)
    assert out["discover"]["found"] == "LODHA CAMELOT" and out["watch"]["watched"] == 1
    assert (await store.project("PR1260002501386"))["page_slug"] == "lodha-camelot-kharadi"
