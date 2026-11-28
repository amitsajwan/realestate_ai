"""Schools near a place or a project: the boards' lists read from saved pages, each school placed on Google Maps only when the
pin is surely it, the caps that spread the first fill over runs, and the block hiding itself when there are too few schools."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from app.modules.neighbourhood import places, schools_geo, schools_sources
from app.modules.neighbourhood.config import Config
from app.modules.neighbourhood.researchers import Context, ViewContext
from app.modules.neighbourhood.researchers import schools
from app.modules.neighbourhood.store import CITY, Store
from tests.modules.fakes import FakeDb

NOW = datetime(2026, 11, 28, 9, 0, tzinfo=timezone.utc)
FIX = Path(__file__).parent / "fixtures"
KHARADI = (18.5515, 73.9408)


def page(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


# --- the lists ---------------------------------------------------------------------------------------------------------------

def test_the_cbse_district_list_gives_affiliation_level_address_and_website_and_never_the_heads_name():
    rows = schools_sources.parse_saras_list(page("saras_list.html"))
    assert len(rows) == 6
    podar = next(r for r in rows if r["affiliation"] == "1130577")
    assert podar["name"] == "PODAR INTERNATIONAL SCHOOL- WAGHOLI"
    assert podar["level"] == "Up to Class 10" and podar["address"].endswith("WAGHOLI,PUNE")
    assert podar["website"] == "http://www.podareducation.org/school/wagholi" and podar["school_code"] == "30499"
    assert {r["level"] for r in rows} <= {"Up to Class 12", "Up to Class 10", "Up to Class 8"}
    assert all("not kept" not in json.dumps(r) for r in rows)


def test_a_cbse_schools_details_page_gives_its_pincode():
    assert schools_sources.parse_saras_details(page("saras_details.html")) == {"pincode": "412207", "school_type": "INDEPENDENT"}
    assert schools_sources.saras_token(page("saras_form.html"))


def test_the_cisce_locator_page_gives_district_pincode_isc_and_the_councils_own_position():
    rows, more = schools_sources.parse_cisce_page(page("cisce_page.html"))
    assert more is True
    pune = [r for r in rows if r["district"] == "Pune"]
    assert len(pune) == 3 and len(rows) == 4
    patrick = next(r for r in pune if r["affiliation"] == "MA121")
    assert patrick["pincode"] == "411047" and patrick["icse"] and patrick["isc"]
    assert isinstance(patrick["lat"], float) and isinstance(patrick["lon"], float)
    assert all("not kept" not in json.dumps(r) for r in rows)


def test_websites_from_the_lists_become_links_and_placeholders_none():
    assert schools_sources.website("www.x.in") == "http://www.x.in"
    assert schools_sources.website("https://x.in/") == "https://x.in/"
    assert schools_sources.website("NA") == "" and schools_sources.website("a@b.in") == ""


# --- placing a school ----------------------------------------------------------------------------------------------------------

def cand(name, address, lat=18.58, lon=73.97, types=("school",), pid="g1"):
    return {"id": pid, "displayName": {"text": name}, "formattedAddress": address,
            "location": {"latitude": lat, "longitude": lon}, "types": list(types)}


PODAR = {"name": "PODAR INTERNATIONAL SCHOOL- WAGHOLI", "address": "SR .NO 22/70,UBALE NAGAR,WAGHOLI,PUNE", "pincode": "412207"}


def test_a_pin_is_the_school_when_the_name_and_the_pincode_agree():
    assert schools_geo.check(cand("Podar International School Wagholi (CBSE)", "Ubale Nagar, Wagholi, Pune, Maharashtra 412207"),
                             PODAR) is None


def test_a_pin_in_another_pincode_is_another_school():
    why = schools_geo.check(cand("Podar International School Wagholi", "Pimple Saudagar, Pune, Maharashtra 411027"), PODAR)
    assert "pincode" in why


def test_a_pin_of_another_name_a_play_school_or_a_shop_is_refused():
    assert "preschool" in schools_geo.check(cand("Podar Jumbo Kids", "Wagholi, Pune 412207", types=("preschool", "school")),
                                            {**PODAR, "name": "PODAR INTERNATIONAL SCHOOL"})
    assert "store" in schools_geo.check(cand("Podar International School Wagholi Uniforms", "Wagholi, Pune 412207",
                                             types=("clothing_store",)), PODAR)
    assert "name" in schools_geo.check(cand("Lexicon Kids", "Wagholi, Pune 412207"), PODAR)


def test_a_pin_far_from_the_councils_own_position_or_outside_pune_is_refused():
    school = {"name": "Mount St. Patrick Academy", "address": "Pune", "pincode": "411047", "board_lat": 18.5985, "board_lon": 73.9}
    assert "board" in schools_geo.check(cand("Mount St. Patrick Academy", "Lohegaon, Pune 411047", lat=18.65, lon=73.95), school)
    assert "outside" in schools_geo.check(cand("Podar International School Wagholi", "Nagpur 412207", lat=21.1, lon=79.0), PODAR)


def test_place_words_the_board_adds_to_a_name_do_not_stop_the_match():
    crimson = {"name": "CRIMSON ANISHA GLOBAL SCHOOL MARUNJI MULSHI PUNE", "address": "S NO 11, MARUNJI, MULSHI, PUNE",
               "pincode": "411057"}
    assert schools_geo.check(cand("Crimson Anisha School", "Marunji, Pune, Maharashtra 411057", lat=18.6, lon=73.72), crimson) is None


def test_without_a_board_pincode_a_place_of_its_address_must_be_in_googles():
    school = {"name": "ALARD PUBLIC SCHOOL", "address": "S.NO 50, NEAR RAJIV GANDHI IT PARK, HINJEWADI", "pincode": ""}
    assert schools_geo.check(cand("Alard Public School", "Hinjewadi Phase 1, Pune 411057", lat=18.59, lon=73.73), school) is None
    assert "place" in schools_geo.check(cand("Alard Public School", "Baner, Pune 411045", lat=18.56, lon=73.78), school)


# --- a run -----------------------------------------------------------------------------------------------------------------------

class Web:
    """The boards' sites and Google, from saved pages. `google` maps a word of the query to the candidates it returns."""

    def __init__(self, cisce_status=403, google=None):
        self.cisce_status, self.google = cisce_status, google or {}
        self.calls = {"search": 0, "details": 0, "saras_details": 0, "cisce": 0}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "saras.cbse.gov.in" in url:
            if "AfflicationDetails" in url:
                self.calls["saras_details"] += 1
                return httpx.Response(200, text=page("saras_details.html"))
            return httpx.Response(200, text=page("saras_list.html" if request.method == "POST" else "saras_form.html"))
        if "cisce.org" in url:
            self.calls["cisce"] += 1
            if self.cisce_status != 200:
                return httpx.Response(self.cisce_status, text="<title>Just a moment...</title>")
            return httpx.Response(200, text=page("cisce_page.html").replace("page=2", "page=1"))
        if "places:searchText" in url:
            self.calls["search"] += 1
            q = json.loads(request.content)["textQuery"].lower()
            for word, places_ in self.google.items():
                if word in q:
                    return httpx.Response(200, json={"places": places_})
            return httpx.Response(200, json={"places": []})
        if "places.googleapis.com/v1/places/" in url:
            self.calls["details"] += 1
            return httpx.Response(200, json={"id": url.rsplit("/", 1)[-1], "location": {"latitude": 18.5801, "longitude": 73.9701}})
        return httpx.Response(404)


@pytest.fixture
def wired(monkeypatch):
    def setup(web: Web, seed: bool = False):
        transport = httpx.MockTransport(web)
        monkeypatch.setattr(schools_sources, "cbse_client", lambda timeout=60.0: httpx.AsyncClient(transport=transport))
        if not seed:   # the saved CISCE reading puts 52 more schools in every run; most tests are about CBSE
            monkeypatch.setattr(schools, "CISCE_SEED", FIX / "no-such-file.json")

        async def no_sleep():
            return None
        monkeypatch.setattr(schools, "_sleep", no_sleep)

        async def all_places(db):
            return ["kharadi", "wagholi"]

        async def centre(db, place):
            return {"kharadi": KHARADI, "wagholi": (18.5793, 73.9787)}.get(place)
        monkeypatch.setattr(places, "all_places", all_places)
        monkeypatch.setattr(places, "centre", centre)
        return httpx.AsyncClient(transport=transport)
    return setup


def ctx(db, http, now=NOW, **cfg):
    base = {"google_key": "k", "school_geocodes_per_run": 300, "school_details_per_run": 100}
    return Context(db=db, store=Store(db), now=now, cfg=Config(**{**base, **cfg}), http=http)


async def run(db, http, now=NOW, **cfg):
    """One run stored as the loop stores it (runner.run_once), so the next run sees its lists' state."""
    found = await schools.RESEARCHER.run(ctx(db, http, now=now, **cfg), CITY)
    await Store(db).put("schools", CITY, found.data, found.sources, now)
    return found


WAGHOLI_GOOGLE = {
    "podar": [cand("Podar International School Wagholi (CBSE)", "Wagholi, Pune, Maharashtra 412207", 18.5801, 73.9701, pid="p1")],
    "prodigy": [cand("Prodigy Public School", "Wagholi, Pune, Maharashtra 412207", 18.585, 73.975, pid="p2")],
    "lexicon": [cand("The Lexicon International School, Wagholi", "Wagholi, Pune, Maharashtra 412207", 18.578, 73.981, pid="p3")],
}
LISTED_WITHOUT_PINCODE = sum(1 for r in schools_sources.parse_saras_list(page("saras_list.html")) if not r["pincode"])


@pytest.mark.asyncio
async def test_a_run_lists_every_cbse_school_reads_pincodes_and_places_them(wired):
    web = Web(google=WAGHOLI_GOOGLE)
    http = wired(web)
    db = FakeDb()
    found = await run(db, http)
    held = await Store(db).schools_in({"source": "CBSE"})
    assert len(held) == 6 and all(d["_id"].startswith("CBSE|") for d in held)
    assert web.calls["saras_details"] == LISTED_WITHOUT_PINCODE == 5   # only schools the list gives no pincode for
    assert all(d["pincode"] for d in held)
    assert {d["place_id"] for d in held if d.get("place_id")} == {"p1", "p2", "p3"}
    assert found.data["lists"]["CBSE"] == {"read_on": "2026-11-28", "count": 6}
    assert {s["name"] for s in found.data["schools"]} == {"PODAR INTERNATIONAL SCHOOL- WAGHOLI", "PRODIGY PUBLIC SCHOOL",
                                                          "THE LEXICON INTERNATIONAL SCHOOL"}
    assert found.data["centres"]["kharadi"] == list(KHARADI)
    assert [s["name"] for s in found.sources] == ["CBSE affiliated schools (SARAS)", "Google Maps (school positions)"]
    assert not any("not kept" in json.dumps(d, default=str) for d in held)


@pytest.mark.asyncio
async def test_cisce_refusing_us_puts_the_saved_reading_on_the_map_and_is_not_asked_again_for_a_week(wired):
    web = Web(cisce_status=403)
    http = wired(web, seed=True)
    db = FakeDb()
    found = await run(db, http, google_key="")
    cisce = await Store(db).schools_in({"source": "CISCE"})
    assert len(cisce) == 52 and all(d["board"] == "ICSE" for d in cisce)
    state = found.data["lists"]["CISCE"]
    assert state["read_on"] == "2026-11-28" and state["failed_on"] == "2026-11-28" and state["from"] == "saved reading"
    assert sum(1 for s in found.data["schools"] if s["board"] == "ICSE") == 52   # the council's own positions
    calls = web.calls["cisce"]
    await run(db, http, now=NOW + timedelta(days=3), google_key="")
    assert web.calls["cisce"] == calls
    await run(db, http, now=NOW + timedelta(days=91), google_key="")
    assert web.calls["cisce"] == calls + 1        # due again at 90 days


@pytest.mark.asyncio
async def test_a_list_that_fails_keeps_the_schools_we_hold(wired, monkeypatch):
    web = Web(google=WAGHOLI_GOOGLE)
    http = wired(web)
    db = FakeDb()
    await run(db, http)

    async def down(c):
        raise httpx.ConnectTimeout("saras down")
    monkeypatch.setattr(schools_sources, "read_cbse", down)
    found = await run(db, http, now=NOW + timedelta(days=91))
    assert found.data["lists"]["CBSE"]["failed_on"] == "2027-02-27"
    assert found.data["lists"]["CBSE"]["read_on"] == "2026-11-28"
    assert len(await Store(db).schools_in({"source": "CBSE", "listed": True})) == 6


@pytest.mark.asyncio
async def test_a_school_gone_from_its_boards_list_leaves_the_pages(wired, monkeypatch):
    web = Web(google=WAGHOLI_GOOGLE)
    http = wired(web)
    db = FakeDb()
    await run(db, http)
    rows = schools_sources.parse_saras_list(page("saras_list.html"))

    async def fewer(c):
        return [r for r in rows if r["affiliation"] != "1130577"]
    monkeypatch.setattr(schools_sources, "read_cbse", fewer)
    found = await run(db, http, now=NOW + timedelta(days=91))
    assert "PODAR INTERNATIONAL SCHOOL- WAGHOLI" not in {s["name"] for s in found.data["schools"]}
    assert (await Store(db).schools.find_one({"_id": "CBSE|1130577"}))["listed"] is False


@pytest.mark.asyncio
async def test_no_list_ever_read_is_a_failure_for_the_loop(wired, monkeypatch):
    http = wired(Web())

    async def down(c):
        raise httpx.ConnectTimeout("saras down")
    monkeypatch.setattr(schools_sources, "read_cbse", down)
    with pytest.raises(RuntimeError):
        await schools.RESEARCHER.run(ctx(FakeDb(), http), CITY)


@pytest.mark.asyncio
async def test_the_places_cap_spreads_the_first_fill_over_runs(wired):
    web = Web(google=WAGHOLI_GOOGLE)
    http = wired(web)
    db = FakeDb()
    first = await run(db, http, school_geocodes_per_run=2)
    assert web.calls["search"] == 2 and first.data["last_run"]["calls"] == 2
    assert first.data["pending"] == 6 - len(first.data["schools"])
    await run(db, http, now=NOW + timedelta(hours=6))
    assert web.calls["search"] == 6          # the other four CBSE schools, each asked once
    third = await run(db, http, now=NOW + timedelta(hours=12))
    assert web.calls["search"] == 6 and third.data["last_run"]["calls"] == 0   # those Google did not find wait 30 days
    assert third.data["pending"] == 3


@pytest.mark.asyncio
async def test_the_details_cap_holds(wired):
    web = Web()
    http = wired(web)
    await run(FakeDb(), http, school_details_per_run=2, google_key="")
    assert web.calls["saras_details"] == 2


@pytest.mark.asyncio
async def test_without_a_google_key_nothing_is_asked_of_google(wired):
    web = Web(google=WAGHOLI_GOOGLE)
    found = await run(FakeDb(), wired(web), google_key="")
    assert web.calls["search"] == 0 and found.data["schools"] == []


@pytest.mark.asyncio
async def test_a_google_position_is_read_again_by_its_id_after_30_days(wired):
    web = Web(google=WAGHOLI_GOOGLE)
    http = wired(web)
    db = FakeDb()
    await run(db, http)
    searches = web.calls["search"]
    later = NOW + timedelta(days=31)
    found = await run(db, http, now=later)
    assert web.calls["details"] == 3 and found.data["last_run"]["reread"] == 3
    assert web.calls["search"] - searches == 3        # the three not found are asked again too, 30 days on
    podar = await Store(db).schools.find_one({"place_id": "p1"})
    assert podar["geo_at"] == later and podar["lat"] == 18.5801


def test_a_google_position_past_30_days_is_not_shown():
    old = {"place_id": "p1", "lat": 18.5, "lon": 73.9, "geo_at": NOW - timedelta(days=31)}
    assert schools.position(old, NOW) is None
    assert schools.position({**old, "board_lat": 18.6, "board_lon": 73.8}, NOW) == (18.6, 73.8, "board")
    assert schools.position({**old, "geo_at": NOW - timedelta(days=2)}, NOW) == (18.5, 73.9, "google")


# --- what a page shows ---------------------------------------------------------------------------------------------------------

def school(name, km_north, board="CBSE"):
    return {"name": name, "board": board, "affiliation": "1", "level": "Up to Class 10", "address": "", "website": "",
            "lat": KHARADI[0] + km_north / 111.2, "lon": KHARADI[1]}


def test_fewer_than_three_schools_within_3_km_hide_the_block():
    data = {"schools": [school("A", 1), school("B", 2), school("C", 3.5)], "centres": {"kharadi": list(KHARADI)}}
    assert schools.RESEARCHER.present(data, ViewContext(place="kharadi")) is None


def test_the_block_lists_the_nearest_eight_within_3_km_with_counts_by_board():
    near = [school(f"S{i}", 0.3 * i, board="ICSE" if i % 3 == 0 else "CBSE") for i in range(1, 11)]   # 0.3 .. 3.0 km
    far = [school("Far", 4.5)]
    data = {"schools": far + near[::-1], "centres": {"kharadi": list(KHARADI)}}
    block = schools.RESEARCHER.present(data, ViewContext(place="kharadi"))
    assert [s["name"] for s in block["schools"]] == [f"S{i}" for i in range(1, 9)]
    assert block["schools"][0]["km"] == 0.3
    assert block["total_within_km"] == {"km": 3.0, "count": 10, "by_board": {"CBSE": 7, "ICSE": 3}}
    assert block["page_ready"] is True and len(block["all"]) == 11 and block["all"][-1]["name"] == "Far"


def test_the_page_is_ready_only_with_eight_schools_within_5_km():
    data = {"schools": [school(f"S{i}", 0.5 * i) for i in range(1, 8)], "centres": {"kharadi": list(KHARADI)}}
    assert schools.RESEARCHER.present(data, ViewContext(place="kharadi"))["page_ready"] is False


def test_a_project_page_measures_from_the_projects_own_pin():
    data = {"schools": [school(f"S{i}", 10 + 0.2 * i) for i in range(1, 5)], "centres": {"kharadi": list(KHARADI)}}
    assert schools.RESEARCHER.present(data, ViewContext(place="kharadi")) is None
    pin = ViewContext(place="kharadi", lat=KHARADI[0] + 10 / 111.2, lon=KHARADI[1], project={"slug": "x"})
    block = schools.RESEARCHER.present(data, pin)
    assert block["total_within_km"]["count"] == 4 and block["schools"][0]["km"] == 0.2


def test_names_in_capitals_are_written_as_names():
    assert schools.display_name("PODAR INTERNATIONAL SCHOOL- WAGHOLI") == "Podar International School- Wagholi"
    assert schools.display_name("DPS PUNE") == "DPS Pune"
    assert schools.display_name("St. Mary's School") == "St. Mary's School"
