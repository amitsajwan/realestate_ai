"""T1.2 project register: every in-area MahaRERA project once (by registration number), facts with source and date, kept up to
date across runs; news items linked only on a clear match. Pages come from the real fixtures, with cards moved into our area."""
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.modules.newsroom import register
from app.modules.newsroom.config import NewsroomConfig
from app.modules.newsroom.pipeline import run_once
from app.modules.newsroom.sources.maharera import MahaReraSource, parse_projects
from app.modules.newsroom.stages.filter import assess, same_story
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import MahaReraProject, RawItem

from ..fakes import FakeDb
from .helpers import FakeSource

NOW = datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc)
CFG = NewsroomConfig(enabled=True, daily_cap=2)
FIX = Path(__file__).parent / "fixtures" / "sources"
# 12910 results (the fixture says 12920): pages count from 1, so the newest page is 1291
FIRST = (FIX / "maharera_pune_first.html").read_text(encoding="utf-8").replace(">12920<", ">12910<", 1)
LAST = (FIX / "maharera_pune_last.html").read_text(encoding="utf-8")
EMPTY = "<html><body>Registered Projects Search Record No Records Found</body></html>"  # the site's flaky answer

# page 1291: three cards moved into our area (two by pincode, one by name). Page 1290: the same page again (the same projects,
# so nothing may be stored twice) with one more project, in Upper Kharadi by name. Dates are old on purpose: the register
# keeps projects whatever their age, unlike the news filter.
PAGE_1291 = (LAST.replace("412202", "412207", 1)  # AARAMBH PHASE 1 -> Wagholi
             .replace("411016", "411014", 1)  # VIKRAM MARQUEE -> Kharadi
             .replace("Satvam Hills C5", "Satvam Kharadi Heights", 1))  # Mulshi pincode, Kharadi by name
PAGE_1290 = (PAGE_1291.replace("SHREERAM ICON", "SHREERAM ICON UPPER KHARADI", 1)
             .replace("413102", "412202", 1)  # near Pune: a name alone does not count from Baramati's 413102
             .replace("PR1260002602002", "PR1260002699999", 1))  # a different project, so a new number
IN_AREA = {"PP1260002601725": "wagholi", "PM1260002602035": "kharadi", "PP1260002601969": "kharadi"}


def site(pages, calls=None):
    async def get(url):
        if calls is not None:
            calls.append(url)
        if "page=0&" in url:
            return FIRST
        for n, body in pages.items():
            if f"page={n}&" in url:
                return body
        return EMPTY
    return get


def stages(get):
    return {"filter": assess, "same_story": same_story, "get": get}


async def run(store, get, now=NOW, extra=()):
    return await run_once(store, [MahaReraSource(pages=3), *extra], stages(get), None, None, now, CFG)


def proj(**kw) -> MahaReraProject:
    base = dict(regno="PR1260000000001", name="Example Towers", promoter="", location="Haveli", district="Pune",
                pincode="412202", last_modified="2026-09-20", url="https://maharerait.maharashtra.gov.in/public/project/view/1")
    base.update(kw)
    return MahaReraProject(**base)


# --- which projects are ours -------------------------------------------------------------------------------------------

def test_locality_by_pincode_and_by_name():
    assert register.locality(proj(pincode="411014")) == ("kharadi", "pincode")
    assert register.locality(proj(pincode="412207")) == ("wagholi", "pincode")
    assert register.locality(proj(pincode="411047")) == ("lohegaon", "pincode")  # Lohegaon's pincode, once mapped to Wagholi
    assert register.locality(proj(pincode="411014", name="Skyline Upper Kharadi")) == ("upper_kharadi", "pincode and project name")
    assert register.locality(proj(name="Mantra Kharadi Phase 3")) == ("kharadi", "project name")
    assert register.locality(proj(name="Wagholi Greens", pincode="412207")) == ("wagholi", "pincode")
    assert register.locality(proj()) is None
    assert register.locality(proj(name="Near EON IT Park Residency")) is None  # a landmark is not a locality


def test_own_pincode_beats_a_name_but_upper_kharadi_is_finer():
    # real 412207 projects (2026-10-04): named for Kharadi, filed in Wagholi's pincode
    assert register.locality(proj(name="Kharadi Pune P1", pincode="412207")) == ("wagholi", "pincode")
    assert register.locality(proj(name="MY HOME UPPER KHARADI", pincode="412207")) == ("upper_kharadi", "pincode and project name")
    assert register.locality(proj(name="Belmont Skyone", pincode="411047")) == ("lohegaon", "pincode")
    assert register.locality(proj(name="Lohgaon Heights", pincode="411047")) == ("lohegaon", "pincode")
    # a name that says only another locality keeps a project out, even on our own pincode
    assert register.locality(proj(name="Solitaire Business Hub Viman Nagar Phase 1", pincode="411047")) is None
    assert register.locality(proj(name="Kharadi Viman Nagar Link", pincode="411014")) == ("kharadi", "pincode")


def test_shared_pincode_needs_the_name():
    assert register.locality(proj(name="Menlo Homes Hinjewadi Phase I", pincode="411057")) == ("hinjawadi", "pincode and project name")
    assert register.locality(proj(name="YASHWIN HINJAWADI", pincode="411057")) == ("hinjawadi", "pincode and project name")
    assert register.locality(proj(name="One Place - Wakad", pincode="411057")) == ("wakad", "pincode and project name")
    assert register.locality(proj(name="The Crown Greens", pincode="411057")) is None  # Hinjawadi or Wakad or Maan: unknown
    assert register.locality(proj(name="NESTORIA BANER", pincode="411045")) == ("baner", "pincode and project name")
    assert register.locality(proj(name="Palladio Balewadi Central Phase 1", pincode="411045")) is None  # Balewadi is not ours
    assert register.locality(proj(name="Keshav Nagar Greens", pincode="411036")) == ("keshav_nagar", "pincode and project name")
    assert register.locality(proj(name="Keshavnagar Heights", pincode="411036")) == ("keshav_nagar", "pincode and project name")
    assert register.locality(proj(name="NEWTON HOME MUNDHWA", pincode="411036")) is None  # Mundhwa shares the pincode


def test_name_only_matches():
    assert register.locality(proj(name="Pune Baner Project-Tower 4 and 5", pincode="411038")) == ("baner", "project name")
    assert register.locality(proj(name="MY HOME WAKAD", pincode="")) == ("wakad", "project name")
    # named for an area but filed far from it: "Hinjewadi Road" in Talegaon's 410506 is not Hinjawadi
    assert register.locality(proj(name="XRBIA HINJEWADI ROAD/RIVERFRONT-PH-1", pincode="410506")) is None
    assert register.locality(proj(name="Wagholikar Heritage", pincode="413102")) is None  # whole words only
    assert register.locality(proj(name="Wagholikar Heritage", pincode="412202")) is None


def test_area_names_come_from_the_one_area_list():
    from app.modules.newsroom.stages.filter import named_areas
    assert named_areas("Hinjewadi Phase 3 - Tower 1") == ["hinjawadi"]
    assert named_areas("Skyline Upper Kharadi") == ["kharadi", "upper_kharadi"]
    assert named_areas("Keshavnagar Heights, Baner Road") == ["keshav_nagar", "baner"]
    assert named_areas("Wagholikar Heritage") == [] and named_areas("") == []
    assert named_areas("Lohgaon Heights") == ["lohegaon"]


def test_a_maharera_item_on_lohegaons_pincode_is_lohegaon_news():
    from app.modules.newsroom.sources.maharera import to_item
    from app.modules.newsroom.stages.filter import assess
    rel = assess(to_item(proj(name="Belmont Skyone", pincode="411047", last_modified="2026-09-28")), NOW)
    assert rel.keep and rel.areas == ["lohegaon"]


def test_records_hold_facts_with_source_and_date():
    recs = register.records(parse_projects(PAGE_1291), NOW)
    assert {r["regno"]: r["locality"] for r in recs} == IN_AREA
    r = next(x for x in recs if x["regno"] == "PM1260002602035")
    assert r == {"regno": "PM1260002602035", "name": "VIKRAM MARQUEE", "promoter": "Vikram Developers", "taluka": "Pune City",
                 "district": "Pune", "pincode": "411014", "locality": "kharadi", "locality_from": "pincode",
                 "last_modified": "2026-09-24", "source": "MahaRERA", "source_url": r["source_url"], "checked_at": NOW}
    assert r["source_url"].startswith("https://maharerait.maharashtra.gov.in/public/project/view/")
    banned = {"rating", "score", "review", "opinion", "verdict"}
    assert not banned & set(r)


def test_individual_promoters_are_never_stored():
    recs = register.records([proj(pincode="411014", promoter="")], NOW)  # the parser blanks people (test_sources_maharera)
    assert recs[0]["promoter"] == ""
    assert all(p.promoter != "Shekhar Valmik Kurundale" for p in parse_projects(LAST))


# --- the register after a newsroom run ----------------------------------------------------------------------------------

async def test_run_fills_register_once_per_project():
    store = Store(FakeDb())
    counts = await run(store, site({1291: PAGE_1291, 1290: PAGE_1290, 1289: LAST}))
    docs = await store.projects.find({}).to_list(None)
    regnos = [d["_id"] for d in docs]
    assert sorted(regnos) == sorted([*IN_AREA, "PR1260002699999"]) and len(regnos) == len(set(regnos))
    assert counts["projects"] == 4
    upper = await store.project("PR1260002699999")
    assert upper["locality"] == "upper_kharadi" and upper["locality_from"] == "project name"
    assert all(d["first_seen"] == NOW and d["news"] == [] for d in docs)


async def test_second_run_adds_nothing_and_refreshes_facts():
    store = Store(FakeDb())
    await run(store, site({1291: PAGE_1291}))
    later = NOW + timedelta(days=3)
    newer = PAGE_1291.replace("2026-09-24", "2026-10-02", 1)  # VIKRAM MARQUEE's record was modified again
    counts = await run(store, site({1291: newer}), now=later)
    assert counts["projects"] == 0
    assert await store.projects.count_documents({}) == 3
    v = await store.project("PM1260002602035")
    assert v["last_modified"] == "2026-10-02" and v["checked_at"] == later and v["first_seen"] == NOW


async def test_old_projects_are_registered_though_the_news_filter_drops_them():
    store = Store(FakeDb())
    await run(store, site({1291: PAGE_1291}), now=NOW + timedelta(days=60))  # every card is now far past the news age limit
    assert await store.projects.count_documents({}) == 3
    assert await store.items.count_documents({"status": "relevant"}) == 0


async def test_flaky_pages_are_asked_again(caplog):
    calls, answers = [], {}

    async def get(url):
        calls.append(url)
        if "page=0&" in url:
            answers["p0"] = answers.get("p0", 0) + 1
            return EMPTY if answers["p0"] == 1 else FIRST  # the count comes on the second try
        if "page=1291&" in url:
            answers["p1291"] = answers.get("p1291", 0) + 1
            return EMPTY if answers["p1291"] < 3 else PAGE_1291  # the cards on the third
        return EMPTY  # 1290 and 1289 never answer
    store = Store(FakeDb())
    with caplog.at_level(logging.WARNING):
        await run(store, get)
    assert await store.projects.count_documents({}) == 3
    assert sum("page=1290&" in u for u in calls) == 3 * 3  # 3 tries in the pass, 3 in each of 2 late rounds
    assert "[1290, 1289]" in caplog.text


async def test_a_page_lost_to_a_burst_of_failures_is_recovered_later():
    """What happened live on 2026-10-03: the page with the newest in-area projects failed all 3 quick tries."""
    answers = {}

    async def get(url):
        if "page=0&" in url:
            return FIRST
        if "page=1291&" in url:
            answers["n"] = answers.get("n", 0) + 1
            return EMPTY if answers["n"] <= 4 else PAGE_1291  # down for the whole first pass and the first late try
        return EMPTY
    store = Store(FakeDb())
    await run(store, get)
    assert await store.projects.count_documents({}) == 3


async def test_register_failure_never_stops_the_news():
    store = Store(FakeDb())

    async def boom(records):
        raise RuntimeError("db down")
    store.record_projects = boom
    counts = await run(store, site({1291: PAGE_1291}))
    assert counts["collected"] == 10 and counts["errors"] == 1


# --- news links ---------------------------------------------------------------------------------------------------------

def news(n, title, text):
    return RawItem(id=f"n{n}", source="Times of India", url=f"https://news.test/{n}", title=title, text=text,
                   published_at=NOW - timedelta(days=1), fetched_at=NOW)


async def registered_store():
    store = Store(FakeDb())
    await run(store, site({1291: PAGE_1291}))
    return store


async def test_news_links_by_name_and_by_registration_number():
    store = await registered_store()
    items = [
        news(1, "Possession begins at Vikram Marquee in Kharadi", "Buyers at the Kharadi project will get keys from November."),
        news(2, "Wagholi project gets possession nod", "MahaRERA records show project PP1260002601725 has an updated possession date."),
        news(3, "Wagholi: Vikram Marquee possession talk", "A Wagholi residents' group discussed possession timelines."),
    ]
    await run_once(store, [FakeSource(items)], stages(site({})), None, None, NOW, CFG)
    vikram, aarambh = await store.project("PM1260002602035"), await store.project("PP1260002601725")
    assert [(n["item_id"], n["matched_by"]) for n in vikram["news"]] == [("n1", "project name")]  # n3 is about Wagholi
    assert [(n["item_id"], n["matched_by"]) for n in aarambh["news"]] == [("n2", "registration number")]
    assert vikram["news"][0]["url"] == "https://news.test/1" and vikram["news"][0]["source"] == "Times of India"


async def test_maharera_records_are_not_news_about_themselves():
    store = await registered_store()
    assert all(d["news"] == [] for d in await store.projects.find({}).to_list(None))


async def test_a_news_item_is_linked_once():
    store = await registered_store()
    link = {"item_id": "n1", "title": "t", "url": "u", "source": "s", "published_at": None, "matched_by": "project name"}
    assert await store.link_news("PM1260002602035", link) is True
    assert await store.link_news("PM1260002602035", link) is False
    assert await store.link_news("PX0000000000", link) is False


def test_vague_names_are_not_linked_by_name():
    assert not register.specific_name("The Element")
    assert not register.specific_name("NEOWORLD")
    assert not register.specific_name("AARAMBH PHASE 1")
    assert register.specific_name("Belmont Skyone")
    assert register.specific_name("Mantra Kharadi Phase 3")
    p = {"name": "Mantra Kharadi Phase 3"}
    assert register.names_project(p, "possession at mantra kharadi phase-3 is due")
    assert not register.names_project(p, "mantra kharadi phase 32 is due")
    assert not register.names_project({"name": "The Element"}, "the element of surprise")


def test_registration_numbers_found_in_text():
    assert register.regnos_in("see PR1260002601907 and P52100012345, again PR1260002601907") == ["PR1260002601907", "P52100012345"]
    assert register.regnos_in("PIN 411014, call 9876543210") == []


async def test_the_count_page_gets_late_rounds_too():
    """Live on 2026-10-03 the count page failed 3 quick tries and the whole MahaRERA read was skipped."""
    answers = {}

    async def get(url):
        if "page=0&" in url:
            answers["n"] = answers.get("n", 0) + 1
            return EMPTY if answers["n"] <= 3 else FIRST
        return PAGE_1291 if "page=1291&" in url else EMPTY
    store = Store(FakeDb())
    await run(store, get)
    assert await store.projects.count_documents({}) == 3


async def test_two_maharera_projects_are_not_the_same_story():
    """Live on 2026-10-03: 'The Element' and 'Belmont Skyone' were dropped as the same story as another MahaRERA item."""
    store = Store(FakeDb())
    page = PAGE_1291.replace("2026-09-01", "2026-09-28").replace("2026-09-24", "2026-09-29")  # recent enough to be news
    await run(store, site({1291: page}))
    kept = await store.items.find({"status": "relevant"}).to_list(None)
    assert sorted(d["raw"]["title"].split(": ")[1].split(",")[0] for d in kept) == ["AARAMBH PHASE 1", "Satvam Kharadi Heights", "VIKRAM MARQUEE"]
