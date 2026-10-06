"""Slow background enrichment of project pages: priority, the checker, one per interval, urgent requests, the page text."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.areastats import enrich, pages
from app.modules.newsroom.store import Store

from ..fakes import FakeDb
from .test_pages import FULL, seeded

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
GATHERED = {"nearby": [{"label": "school", "name": "Lexicon School", "km": 1.2}], "numbers": {}, "maharera": {"project_type": "Residential"}}


class FakeLLM:
    def __init__(self, text):
        self.text, self.calls = text, 0

    async def json(self, system, user):
        self.calls += 1
        return {"text": self.text}


GOOD = ("Rohan Abhilasha 4 is a housing project by Rohan Builders in Wagholi, Pune. Its completion date filed with MahaRERA is "
        "30 Oct 2029, later than the 31 Dec 2028 filed at registration. 244 of 416 homes were booked when the record was read.\n\n"
        "Lexicon School is about 1.2 km away.")


@pytest.fixture(autouse=True)
def gatherer(monkeypatch):
    calls = []

    async def gather(db, regno, name, locality, city="Pune", now=None):
        calls.append(regno)
        return GATHERED
    monkeypatch.setitem(enrich._deps, "gather", gather)
    return calls


async def ready(*docs):
    db, store = await seeded(*docs)
    await pages.assign_all(store)
    return db, store


async def test_urgent_first_then_google_then_indexable_then_bigger():
    db, store = await ready(("A", "Alpha", "wagholi", {**FULL, "units_total": 100, "units_booked": 50}),
                            ("B", "Bravo", "wagholi", {**FULL, "gsc_impressions": 40}),
                            ("C", "Charlie", "wagholi", {}),
                            ("D", "Delta", "wagholi", {**FULL, "units_total": 900, "units_booked": 10}),
                            ("E", "Echo", "wagholi", {**FULL, "enriched_at": NOW - timedelta(days=5)}))
    order = []
    for _ in range(4):
        d = await enrich.next_project(store, NOW)
        order.append(d["_id"])
        await store.set_project(d["_id"], enriched_at=NOW)
    assert order == ["B", "D", "A", "C"]          # Google impressions, then indexable (bigger first), then thin; E is fresh
    assert await enrich.next_project(store, NOW) is None
    await enrich.enrich_now(db, "e")
    assert (await enrich.next_project(store, NOW))["_id"] == "E"   # urgent beats freshness


def test_the_checker_refuses_invented_numbers_sales_words_and_links():
    facts = enrich.facts_text({**FULL, "_id": "P1", "name": "Rohan Abhilasha 4", "locality": "wagholi", "regno": "P1"}, GATHERED)
    assert enrich.check_text(GOOD, facts) == []
    assert any("numbers not in the facts" in p for p in enrich.check_text(GOOD + " Prices start at 55 lakh.", facts))
    assert "sales words" in enrich.check_text(GOOD.replace("housing project", "luxury project"), facts)
    assert "links or phone numbers" in enrich.check_text(GOOD + " Call 9876543210.", facts)
    assert "too short" in enrich.check_text("Nice.", facts)


async def test_one_project_per_interval_and_urgent_ones_at_once(gatherer):
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}),
                            ("P2", "Other", "wagholi", {**FULL}))
    llm = FakeLLM(GOOD)
    out = await enrich.step(store, llm, NOW, None, timedelta(minutes=30))
    assert out["regno"] in ("P1", "P2") and out["text"] and out["gathered"] and not out["urgent"]
    assert await enrich.step(store, llm, NOW + timedelta(minutes=10), NOW, timedelta(minutes=30)) is None   # not yet
    await enrich.enrich_now(db, "P2" if out["regno"] == "P1" else "P1")
    urgent = await enrich.step(store, llm, NOW + timedelta(minutes=11), NOW, timedelta(minutes=30))
    assert urgent["urgent"] and await db.get_collection(enrich.REQUESTS).count_documents({}) == 0
    assert len(gatherer) == 2 and llm.calls == 2


async def test_a_refused_draft_keeps_the_code_paragraph_and_the_page_shows_accepted_text():
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    await enrich.step(store, FakeLLM("A luxury project with the best views in Pune, homes from Rs 55 lakh, book now."), NOW, None,
                      timedelta(minutes=30))
    doc = await store.project("P1")
    assert "page_text" not in doc and doc["enriched_at"] == NOW and "kept the code-written paragraph" in doc["enrich_notes"]
    page = await pages.project_page(db, doc["page_slug"])
    assert page["paragraph"].startswith("Rohan Abhilasha 4 is a project by Rohan Builders")

    await store.set_project("P1", enriched_at=None)
    await enrich.step(store, FakeLLM(GOOD), NOW, None, timedelta(minutes=30))
    page = await pages.project_page(db, doc["page_slug"])
    assert page["paragraph"] == GOOD and page["enriched_at"] == "2026-10-06"


async def test_without_a_gatherer_it_still_writes_from_the_register_facts(monkeypatch):
    monkeypatch.setitem(enrich._deps, "gather", None)
    db, store = await ready(("P1", "Rohan Abhilasha 4", "wagholi", {**FULL, "promoter": "Rohan Builders"}))
    out = await enrich.step(store, FakeLLM(GOOD.split("\n\n")[0]), NOW, None, timedelta(minutes=30))
    assert out["text"] and "no gatherer configured" in out["notes"]


async def test_enrich_now_for_an_unknown_project_says_so():
    db = FakeDb()
    assert await enrich.enrich_now(db, "NOPE") is False


def test_off_unless_switched_on(monkeypatch):
    monkeypatch.delenv("PROJECT_ENRICH_ENABLED", raising=False)
    assert enrich.load().enabled is False
    monkeypatch.setenv("PROJECT_ENRICH_ENABLED", "on")
    monkeypatch.setenv("PROJECT_ENRICH_EVERY_MINUTES", "30")
    assert enrich.load().enabled and enrich.load().every == timedelta(minutes=30)
