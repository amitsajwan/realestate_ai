"""A page that stands for several MahaRERA registrations says the whole project's counts and dates everywhere it is read:
the page API, its plain paragraph, the area lists' and top lists' cards, the chat's brief and the knowledge index. The page's own
record is one of the registrations, so its counts read alone are one part's (2026-11-12: 85 of 88 such pages said one wing's
homes as the project's; Venkatesh Vanaya 168 of 745)."""
from datetime import datetime, timedelta, timezone

from app.modules.areastats import pages
from app.modules.areastats.pagefacts import sales_of
from app.modules.knowledge import index as knowledge
from app.modules.newsroom.store import Store
from app.modules.seo import facets
from app.modules.seo.facets import Facet

from ..fakes import FakeDb

READ = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)
NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
BASE = {"locality": "kharadi", "pune_place": "kharadi", "pincode": "411014", "promoter": "SVBPL HOMES PVT LTD", "cluster_id": "C1",
        "details_checked_at": READ, "details_ok": True, "news": []}
# (regno, homes, booked, filed completion): Venkatesh Vanaya's seven registrations; the last has not reported its homes yet
PARTS = [("PR1261012601206", 168, 0, "2031-04-30"), ("PR1261012601751", 78, 0, "2030-08-31"), ("PR1261012601264", 144, 0, "2030-12-31"),
         ("PR1261012601304", 249, 0, "2031-01-31"), ("PR1261012601229", 90, 0, "2031-10-31"), ("PC1261012601213", 16, 0, "2032-04-30"),
         ("PR1261012601239", 0, 0, "2033-01-31")]


def vanaya(booked=None):
    docs = []
    for i, (regno, homes, sold, filed) in enumerate(PARTS):
        docs.append({**BASE, "_id": regno, "regno": regno, "name": f"VENKATESH VANAYA PART {i + 1}",
                     "page_slug": f"venkatesh-vanaya-{regno.lower()}", "units_total": homes,
                     "units_booked": (booked or {}).get(regno, sold), "completion_now": filed, "completion_at_registration": filed,
                     **({} if i == 0 else {"cluster_primary": PARTS[0][0]})})
    return docs


ALONE = {**BASE, "_id": "P52100000001", "regno": "P52100000001", "name": "Rohan Abhilasha", "page_slug": "rohan-abhilasha-kharadi",
         "units_total": 416, "units_booked": 244, "completion_now": "2029-10-30", "completion_at_registration": "2028-12-31",
         "cluster_id": None}


def test_the_whole_project_is_summed_over_the_registrations_that_report_it():
    docs = vanaya({"PR1261012601751": 30, "PR1261012601264": None})
    s = pages.project_scope(docs[0], docs)
    assert s["registrations"] == 7 and s["regnos"][0] == "PR1261012601206"
    assert (s["units_total"], s["units_counted"]) == (745, 6)            # the 0 is a registration that has not reported yet
    assert (s["units_booked"], s["booked_of"], s["booked_counted"]) == (30, 601, 5)   # bookings against the same registrations' homes
    assert (s["completion_first"], s["completion_last"], s["completion_passed"]) == ("2030-08-31", "2033-01-31", False)


def test_only_a_page_that_hosts_its_registrations_has_a_project_scope():
    docs = vanaya()
    assert pages.project_scope(docs[1], docs) is None                    # a tower: its address answers 301 to the project's page
    assert pages.project_scope(ALONE, [ALONE]) is None                   # registered once
    unhosted = [{**docs[0], "completion_now": None}] + docs[1:]           # a primary search may not list hosts nothing:
    assert pages.project_scope(unhosted[0], unhosted) is None            # each registration keeps its own page


def test_the_paragraph_says_the_whole_project_and_never_one_part_s_count():
    docs = vanaya()
    text = pages.paragraph(docs[0], pages.project_scope(docs[0], docs))
    assert "registered with MahaRERA in 7 parts (towers or phases): PR1261012601206, PR1261012601751" in text
    assert "Its parts have filed completion dates from 31 Aug 2030 to 31 Jan 2033." in text
    assert "0 of 745 homes were booked when we read the record on 3 Oct 2026, across 6 of its 7 parts." in text
    assert "168" not in text
    assert "244 of 416 homes were booked" in pages.paragraph(ALONE)      # one registration reads as before


def test_a_list_card_counts_the_whole_project():
    docs = vanaya()
    assert pages.card_counts(docs[0], pages.project_scope(docs[0], docs)) == {
        "units_total": 745, "units_booked": 0, "registrations": 7, "sold_out": False, "stage": None,
        "completion_now": "2030-08-31", "possession_to": "2033-01-31"}   # possession from the first part to the last
    assert pages.card_counts(ALONE, None) == {"units_total": 416, "units_booked": 244}


async def _db(docs):
    db = FakeDb()
    for d in docs:
        await Store(db).projects.insert_one(dict(d))
    return db


async def test_the_page_api_carries_the_scope_and_leaves_out_one_part_s_comparison():
    db = await _db(vanaya() + [ALONE])
    page = await pages.project_page(db, "venkatesh-vanaya-pr1261012601264", NOW)   # a tower's address gets the project's page
    assert page["regno"] == "PR1261012601206"
    assert page["project"]["units_total"] == 745 and page["project"]["registrations"] == 7
    assert page["area_compare"] is None and "168" not in page["paragraph"]
    alone = await pages.project_page(db, "rohan-abhilasha-kharadi", NOW)
    assert alone["project"] is None


async def test_the_area_list_card_and_the_chat_say_the_whole_project():
    db = await _db(vanaya() + [ALONE])
    rows = {r["slug"]: r for r in await pages.listing(db, area="kharadi")}
    card = rows["venkatesh-vanaya-pr1261012601206"]
    assert (card["units_total"], card["units_booked"], card["registrations"]) == (745, 0, 7)
    assert (card["completion_now"], card["possession_to"], card["stage"]) == ("2030-08-31", "2033-01-31", None)
    assert "venkatesh-vanaya-pr1261012601264" not in rows                  # towers are not cards of their own
    assert (rows["rohan-abhilasha-kharadi"]["units_total"], rows["rohan-abhilasha-kharadi"]["units_booked"]) == (416, 244)
    brief = await pages.chat_brief(db, "venkatesh-vanaya-pr1261012601206")
    assert "0 of 745 homes" in brief["paragraph"] and "168" not in brief["paragraph"]


async def test_the_knowledge_index_the_chat_answers_from_says_the_whole_project():
    db = await _db(vanaya() + [ALONE])
    chunks = await knowledge.project_all(db)
    first = next(c for c in chunks if c["id"] == "project:PR1261012601206")
    assert "0 of 745 homes" in first["text"] and "7 MahaRERA registrations" in first["text"] and "168" not in first["text"]


def test_a_top_list_card_counts_the_whole_project():
    docs = vanaya()
    row = facets._row(docs[0], "why", 1, NOW, docs)
    assert (row["units_total"], row["units_booked"], row["registrations"], row["units_open"]) == (745, 0, 7, 745)
    assert (row["completion_now"], row["possession_to"], row["completion_at_registration"]) == ("2030-08-31", "2033-01-31", None)
    alone = facets._row(ALONE, "why", 1, NOW, [ALONE])
    assert (alone["units_total"], alone["units_booked"]) == (416, 244) and "registrations" not in alone


def test_homes_booked_lately_adds_up_the_registrations_over_their_joint_span():
    def hist(*readings):
        return {"booked_history": [{"at": NOW - timedelta(days=d), "booked": b} for d, b in readings]}
    a, b = hist((60, 10), (10, 25)), hist((40, 5), (0, 9))
    out = sales_of([a, b, {}])
    assert out == {"booked": 19, "days": 60, "since": (NOW - timedelta(days=60)).date().isoformat()}
    assert sales_of([{}, hist((30, 4), (0, 4))]) is None
