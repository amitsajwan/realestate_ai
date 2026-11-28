"""Neighbourhood articles: found from OpenStreetMap, written from facts only, published only when checked and not thin."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.communities import discover, router, runner, write
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
CENTRES = {"Wagholi": (18.5800, 73.9800), "Kharadi": (18.5500, 73.9400)}
PLACES = [
    {"type": "node", "id": 1, "lat": 18.6000, "lon": 73.9900, "tags": {"place": "village", "name": "Kesnand"}},
    {"type": "node", "id": 2, "lat": 18.5850, "lon": 73.9750, "tags": {"place": "neighbourhood", "name": "Ubale Nagar"}},
    {"type": "node", "id": 3, "lat": 18.5810, "lon": 73.9810, "tags": {"place": "suburb", "name": "Wagholi"}},          # one of ours
    {"type": "node", "id": 4, "lat": 18.5520, "lon": 73.9420, "tags": {"place": "neighbourhood", "name": "Eon Free Zone"}},  # nearer Kharadi
    {"type": "node", "id": 5, "lat": 18.5900, "lon": 73.9850, "tags": {"place": "hamlet", "name": "वाघेश्वर"}},           # no English name
]
NEARBY = [
    {"type": "node", "id": 11, "lat": 18.6010, "lon": 73.9910, "tags": {"amenity": "school", "name": "Kesnand Zilla Parishad School"}},
    {"type": "node", "id": 12, "lat": 18.5950, "lon": 73.9850, "tags": {"amenity": "hospital", "name": "Lifeline Hospital"}},
    {"type": "node", "id": 13, "lat": 18.6050, "lon": 73.9950, "tags": {"amenity": "bank", "name": "Bank of Maharashtra"}},
    {"type": "node", "id": 14, "lat": 18.5980, "lon": 73.9880, "tags": {"shop": "supermarket", "name": "D Mart"}},
    {"type": "node", "id": 15, "lat": 18.6020, "lon": 73.9920, "tags": {"amenity": "place_of_worship", "religion": "hindu", "name": "Shiv Mandir"}},
]


@pytest.fixture(autouse=True)
def no_local_copies(monkeypatch, tmp_path):
    """The shipped OSM copies cover these test coordinates: the tests use their own OpenStreetMap answers instead."""
    monkeypatch.setattr(discover, "LOCAL", tmp_path / "none.json.gz")
    monkeypatch.setattr(write, "from_local", lambda lat, lon: None)


def osm(nearby=NEARBY, down=False):
    async def get_json(url, params):
        if "nominatim" in url:
            name = params["q"].split(",")[0]
            c = CENTRES.get(name)
            return [{"lat": str(c[0]), "lon": str(c[1]), "name": name, "address": {"county": "Haveli Subdistrict"}}] if c else []
        if down:
            return None
        if '"place"' in params["data"]:
            return {"elements": PLACES if "18.58," in params["data"] else []}
        return {"elements": nearby}
    return get_json


async def seeded():
    db = FakeDb()
    store = Store(db)
    for regno, name, loc in (("P1", "Kesnand Heights Phase 2", "wagholi"), ("P2", "Green Kesnand", "wagholi"),
                             ("P3", "Kesnandkar Plaza", "wagholi"), ("P4", "Kesnand View", "kharadi")):
        await store.projects.insert_one({"_id": regno, "regno": regno, "name": name, "locality": loc, "promoter": "Rohan Builders",
                                         "completion_now": "2028-06-30", "units_total": 120, "units_booked": 45, "news": []})
    return db, store


class FakeLLM:
    def __init__(self, out):
        self.out, self.calls = out, []

    async def json(self, system, user):
        self.calls.append(user)
        return self.out


GOOD = {"title": "Kesnand, Wagholi: a neighbourhood guide",
        "paragraphs": [
            "Kesnand is a neighbourhood on the northern side of the Wagholi area of Pune, measured from the area's centre in a "
            "straight line on OpenStreetMap. Two MahaRERA-registered projects are named after Kesnand, both by Rohan Builders.",
        ]}


async def test_finds_neighbourhoods_that_belong_to_the_area_with_their_evidence():
    db, store = await seeded()
    assert await discover.run(store, osm(), NOW) == {"areas": 2, "found": 2}
    docs = {d["_id"]: d for d in await db.get_collection(discover.COLLECTION).find({}).to_list(None)}
    assert set(docs) == {"wagholi/kesnand", "wagholi/ubale-nagar"}   # not Wagholi itself, not nearer Kharadi, not Devanagari-only
    assert docs["wagholi/kesnand"]["projects_named"] == 2            # "Kesnandkar" is not Kesnand; P4 is in Kharadi
    assert docs["wagholi/kesnand"]["osm_url"] == "https://www.openstreetmap.org/node/1"
    assert docs["wagholi/ubale-nagar"]["projects_named"] == 0
    await discover.run(store, osm(), NOW + timedelta(days=7))        # a second run refreshes, never duplicates
    assert await db.get_collection(discover.COLLECTION).count_documents({}) == 2


def test_the_query_asks_for_each_place_s_position():
    assert "out body;" in discover.query(18.58, 73.98)   # `out tags` answers names without lat/lon: nothing could be kept


async def test_the_local_copy_answers_when_overpass_does_not(tmp_path, monkeypatch):
    import gzip
    import json
    local = tmp_path / "n.json.gz"
    local.write_bytes(gzip.compress(json.dumps([[p["tags"]["name"], p["tags"]["place"], p["lat"], p["lon"], p["id"]]
                                                for p in PLACES]).encode("utf-8")))
    monkeypatch.setattr(discover, "LOCAL", local)
    db, store = await seeded()
    assert await discover.run(store, osm(down=True), NOW) == {"areas": 2, "found": 3}
    ids = {d["_id"] for d in await db.get_collection(discover.COLLECTION).find({}).to_list(None)}
    assert ids == {"wagholi/kesnand", "wagholi/ubale-nagar", "kharadi/eon-free-zone"}   # each kept by its nearest area


async def test_writes_from_facts_and_publishes_only_a_checked_article():
    db, store = await seeded()
    await discover.run(store, osm(), NOW)
    doc = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    llm = FakeLLM(GOOD)
    out = await write.write_one(store, doc, llm, osm(), NOW)
    assert out == {"id": "wagholi/kesnand", "published": True, "notes": []}
    facts = llm.calls[0]
    # the model gets only the distance and a bare project count: the nearby places and each project's own facts are the
    # page's own lists, not the model's to restate (and so not its to get wrong)
    assert "Neighbourhood: Kesnand, in the Wagholi area of Pune" in facts
    assert "2 MahaRERA-registered projects named after Kesnand, by Rohan Builders" in facts
    assert "Kesnand Zilla Parishad School" not in facts and "Kesnand Heights Phase 2" not in facts and "45 of 120" not in facts
    saved = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    assert saved["published"] and saved["title"] == GOOD["title"] and len(saved["facts"]["projects"]) == 2
    # but the page's own data keeps every fact in full, each nearby place linked to its OpenStreetMap page
    nearby = saved["facts"]["nearby"]
    assert all(n["url"] and n["url"].startswith("https://www.openstreetmap.org/") for n in nearby)
    # the Shiv Mandir in NEARBY is left out: places of worship are never listed (owner, 2026-11-28)
    assert sorted(n["km"] for n in nearby) == [0.2, 0.3, 0.8, 0.8]
    assert not any("mandir" in n["name"].lower() for n in nearby)


async def test_a_nearby_metro_station_says_whether_it_is_running():
    # a neighbourhood page used to just say "station ... nearby"; it now says what app/core/pune_metro has checked,
    # never claiming a station is open before it is (the one fact here a reader could actually be misled by)
    db, store = await seeded()
    await discover.run(store, osm(), NOW)
    doc = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    stations = NEARBY + [
        {"type": "node", "id": 20, "lat": 18.5903, "lon": 73.7576, "tags": {"railway": "station", "name": "Wakad Chowk"}},
        {"type": "node", "id": 21, "lat": 18.5592, "lon": 73.7906, "tags": {"railway": "station", "name": "Baner Gaon Metro Station"}},
    ]
    out = await write.write_one(store, doc, FakeLLM(GOOD), osm(nearby=stations), NOW)
    assert out["published"]
    saved = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    by_name = {n["name"]: n for n in saved["facts"]["nearby"]}
    assert by_name["Wakad Chowk"]["transit"] == {"status": "running", "line_short": "Pink Line (Line 3)", "tracker": None}
    assert by_name["Baner Gaon Metro Station"]["transit"] == {"status": "being built", "line_short": "Pink Line (Line 3)",
                                                               "tracker": "/news/track/pune-metro-line-3"}
    # the model was never told any of this, so it could not have said either station was open or being built
    llm = FakeLLM(GOOD)
    await write.write_one(store, doc, llm, osm(nearby=stations), NOW)
    assert "Wakad" not in llm.calls[0] and "Baner" not in llm.calls[0]


def test_matching_a_station_needs_every_distinctive_word():
    # "Wakad" alone must never claim to be "Wakad Chowk" station, and an unrelated name must match nothing
    assert write.match_station("Wakad Chowk").name == "Wakad Chowk"
    assert write.match_station("Wakad Chowk Metro Station").name == "Wakad Chowk"
    assert write.match_station("Wakad") is None
    assert write.match_station("Shivaji Nagar Bus Stand") is None


async def test_a_title_that_misses_the_name_is_replaced_not_refused():
    db, store = await seeded()
    await discover.run(store, osm(), NOW)
    doc = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    out = await write.write_one(store, doc, FakeLLM({**GOOD, "title": "A guide to the area"}), osm(), NOW)
    assert out["published"]
    saved = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    assert saved["title"] == "Kesnand, Wagholi: a neighbourhood guide"


async def test_invented_numbers_sales_words_or_thin_facts_are_not_published():
    db, store = await seeded()
    await discover.run(store, osm(), NOW)
    coll = db.get_collection(discover.COLLECTION)
    doc = await coll.find_one({"_id": "wagholi/kesnand"})
    bad = {**GOOD, "paragraphs": ["Prices start at 55 lakh in this premium pocket. " + GOOD["paragraphs"][0]]}
    out = await write.write_one(store, doc, FakeLLM(bad), osm(), NOW)
    assert not out["published"] and "numbers not in the facts: 55" in out["notes"][0] and "sales words" in out["notes"][0]
    assert (await coll.find_one({"_id": "wagholi/kesnand"}))["published"] is False
    llm = FakeLLM(GOOD)
    thin = await write.write_one(store, doc, llm, osm(nearby=NEARBY[:2]), NOW)
    assert not thin["published"] and thin["notes"][0].startswith("too few facts") and llm.calls == []   # no model call when thin


async def test_a_failed_refresh_keeps_the_last_good_article():
    db, store = await seeded()
    await discover.run(store, osm(), NOW)
    coll = db.get_collection(discover.COLLECTION)
    await write.write_one(store, await coll.find_one({"_id": "wagholi/kesnand"}), FakeLLM(GOOD), osm(), NOW)
    out = await write.write_one(store, await coll.find_one({"_id": "wagholi/kesnand"}), FakeLLM({}), osm(down=True), NOW + timedelta(days=60))
    assert not out["published"]
    saved = await coll.find_one({"_id": "wagholi/kesnand"})
    assert saved["published"] and saved["title"] == GOOD["title"]


async def test_off_by_default_and_paced_most_evidence_first(monkeypatch):
    monkeypatch.delenv("COMMUNITY_ARTICLES_ENABLED", raising=False)
    assert runner.enabled() is False
    monkeypatch.setenv("COMMUNITY_ARTICLES_PER_DAY", "2")
    db, store = await seeded()
    llm = FakeLLM(GOOD)
    first = await runner.step(store, llm, osm(), NOW)
    assert first["found"]["found"] == 2 and first["wrote"]["id"] == "wagholi/kesnand"   # 2 projects named: first
    assert await runner.step(store, llm, osm(), NOW + timedelta(hours=1)) == {}         # pace: one every 12 hours
    later = await runner.step(store, llm, osm(), NOW + timedelta(hours=12))
    assert later["wrote"]["id"] == "wagholi/ubale-nagar" and "found" not in later
    assert not later["wrote"]["published"]                                              # the draft names Kesnand: refused
    assert await runner.next_doc(store, NOW + timedelta(days=1)) is None                # both tried, none due yet
    assert (await runner.next_doc(store, NOW + timedelta(days=15)))["_id"] == "wagholi/ubale-nagar"   # refused: retried
    await db.get_collection(discover.COLLECTION).update_one({"_id": "wagholi/ubale-nagar"}, {"$set": {"written_at": NOW + timedelta(days=50)}})
    assert (await runner.next_doc(store, NOW + timedelta(days=61)))["_id"] == "wagholi/kesnand"   # published: refreshed


def test_only_published_articles_are_served():
    import asyncio

    async def prep():
        db, store = await seeded()
        await discover.run(store, osm(), NOW)
        coll = db.get_collection(discover.COLLECTION)
        await write.write_one(store, await coll.find_one({"_id": "wagholi/kesnand"}), FakeLLM(GOOD), osm(), NOW)
        return db
    loop = asyncio.new_event_loop()
    try:
        db = loop.run_until_complete(prep())
    finally:
        loop.close()
    app = FastAPI()
    app.include_router(router.public_router, prefix="/public")
    app.dependency_overrides[router.get_db] = lambda: db
    c = TestClient(app)
    items = c.get("/public/communities?area=wagholi").json()
    assert [(i["slug"], i["area_slug"], i["area_name"], i["updated"]) for i in items] == [("kesnand", "wagholi", "Wagholi", "2026-10-12")]
    assert c.get("/public/communities?area=kharadi").json() == [] and c.get("/public/communities?area=nowhere").json() == []
    one = c.get("/public/communities/wagholi/kesnand").json()
    assert one["title"] == GOOD["title"] and len(one["paragraphs"]) == 1 and one["facts"]["nearby"]
    assert c.get("/public/communities/wagholi/ubale-nagar").status_code == 404   # found, not written
