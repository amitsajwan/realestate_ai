"""Projects found by number in Google results reach the register: candidate names, exact-number matches only, the watch list."""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.modules.areastats import discover, owner, pages, refresh, watch, websearch
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
        page = int(re.search(r"[?&]page=(\d+)", url).group(1))
        asked.append(name)
        return pages_by_name.get(name, NONE_PAGE) if page == 1 else NONE_PAGE
    return get


def google(results: list, asked: list):
    async def ask(q):
        asked.append(q)
        return results
    return ask


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

    # the watch source hands it to the register: its area at once (PR1260002501386 is placed by hand in Upper Kharadi,
    # pune_places.VERIFIED), and its own page
    watch.add_source(discover.SOURCE, lambda: discover.watch_items(store.db))
    await watch.sync(store, NOW)
    await pages.assign_all(store)
    p = await store.project("PR1260002501386")
    assert p["locality"] == "upper_kharadi" and p["watched_by"] == ["web_discovered"] and p["page_slug"] == "lodha-camelot-upper-kharadi"
    assert await discover.resolve(store, site({}, asked), NOW + timedelta(days=2)) == {"tried": None}   # nothing left to find


async def test_a_same_named_project_with_another_number_is_never_taken():
    store, asked = Store(FakeDb()), []
    await seen(store, regno="PR1260002501413")                 # Camelot's second tower: not on this results page
    out = await discover.resolve(store, site({"Lodha Camelot": CAMELOT_PAGE}, asked), NOW)
    assert out["found"] is None and list(dict.fromkeys(asked)) == ["Lodha Camelot", "Camelot"]    # a full page: its next page too
    doc = await store.db.get_collection(DISCOVERED).find_one({"_id": "PR1260002501413"})
    assert doc["status"] == "open" and doc["tried_names"] == ["Lodha Camelot", "Camelot"]
    assert await discover.watch_items(store.db) == []
    # every name tried: the report lists it; a new title with a new name puts it back in line the next day
    assert [p["regno"] for p in await discover.pending(store)] == ["PR1260002501413"]
    await store.db.get_collection(DISCOVERED).update_one({"_id": "PR1260002501413"}, {"$set": {"seen": [
        {"title": TITLE}, {"title": "Camelot Kharadi Tower B by Lodha | Official"}]}})
    assert await discover.resolve(store, site({}, asked), NOW + timedelta(hours=2)) == {"tried": None}   # tried today already
    out = await discover.resolve(store, site({}, asked), NOW + timedelta(days=1))
    assert out["tried"] == "PR1260002501413" and asked[-3:] == ["Camelot Tower B", "Tower B", "Camelot Tower"]


def test_names_from_a_page_address():
    assert discover.names_from_link("https://x.in/pulse/rera/maharashtra/pune/ganga-arcadia-c-building-P52100000412")[0] == "Ganga Arcadia C Building"
    assert discover.names_from_link("https://x.in/pristine-allure-part2-kharadi-pune-rera-project.html")[0] == "Pristine Allure Part2"
    assert discover.names_from_link("https://x.in/ganga-arcadia-kharadi-pid-10967")[0] == "Ganga Arcadia"
    assert discover.names_from_link("https://x.in/projects/10967") == discover.names_from_link("https://x.in") == []


async def test_when_names_run_out_the_number_is_searched_on_google_once_and_its_pages_give_the_name():
    store, asked, searched = Store(FakeDb()), [], []
    regno = "PR1260002501386"
    await seen(store, regno=regno, title="Kharadi Pune")              # no name in the title
    ask = google([{"title": f"RERA {regno}", "link": f"https://x.in/rera/lodha-camelot-{regno}", "snippet": ""},
                  {"title": "Some other page", "link": "https://y.in/a-project", "snippet": "no number here"}], searched)
    out = await discover.resolve(store, site({"Lodha Camelot": CAMELOT_PAGE}, asked), NOW, ask)
    assert out["found"] == "LODHA CAMELOT" and searched == [f'"{regno}"'] and asked[0] == "Lodha Camelot"
    doc = await store.db.get_collection(DISCOVERED).find_one({"_id": regno})
    assert doc["seen"][-1]["link"].endswith(regno) and len(doc["seen"]) == 2      # only the page printing the number


async def test_a_number_google_cannot_name_is_not_searched_again():
    store, searched = Store(FakeDb()), []
    await seen(store, title="Kharadi Pune")
    out = await discover.resolve(store, site({}, []), NOW, google([], searched))
    assert out["found"] is None
    assert await discover.resolve(store, site({}, []), NOW + timedelta(days=2), google([], searched)) == {"tried": None}
    assert len(searched) == 1


async def test_a_failed_google_search_is_asked_again_the_next_day():
    store, searched = Store(FakeDb()), []
    await seen(store, title="Kharadi Pune")

    async def down(q):
        raise RuntimeError("no credit")
    assert (await discover.resolve(store, site({}, []), NOW, down))["found"] is None
    assert await discover.resolve(store, site({}, []), NOW + timedelta(hours=2), down) == {"tried": None}
    await discover.resolve(store, site({}, []), NOW + timedelta(days=1), google([], searched))
    assert len(searched) == 1


async def test_a_project_on_a_later_results_page_is_found():
    store, asked = Store(FakeDb()), []
    await seen(store, title="Camelot Kharadi")
    head, card = LAST.split('<div class="row shadow', 2)[:2]
    first = head + ('<div class="row shadow' + card) * 10

    async def get(url):
        asked.append(url)
        return CAMELOT_PAGE if "page=2&" in url else first
    out = await discover.resolve(store, get, NOW)
    assert out["found"] == "LODHA CAMELOT" and len(asked) == 2


async def test_old_misprinted_and_other_district_numbers_are_dropped_unsearched():
    store, asked, searched = Store(FakeDb()), [], []
    coll = store.db.get_collection(DISCOVERED)
    for regno in ("P52100000412", "PS2100080481", "P521000295451", "PR1330002600931"):
        await seen(store, regno=regno, title="Ganga Arcadia Kharadi")
    assert await discover.resolve(store, site({}, asked), NOW, google([], searched)) == {"tried": None}
    assert asked == searched == [] and await coll.find({}).to_list(10) == []


def test_which_numbers_are_worth_finding():
    assert websearch.worth_finding("P52100025978") and websearch.worth_finding("PR1260002501386")
    assert websearch.worth_finding("PR1261012400049")
    assert not websearch.worth_finding("P52100019999") and not websearch.worth_finding("P5210002510")


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
    assert (await store.project("PR1260002501386"))["page_slug"] == "lodha-camelot-upper-kharadi"


async def test_the_screen_hides_dropped_numbers_and_shows_what_nothing_could_find():
    store = Store(FakeDb())
    await seen(store, regno="P52100000412", title="Ganga Arcadia Kharadi")
    await seen(store, regno="P52100028813", title="Kharadi Pune")
    await discover.resolve(store, site({}, []), NOW, google([], []))
    assert [(i["regno"], i["state"]) for i in (await owner.found(store))["items"]] == [("P52100028813", "missing")]
