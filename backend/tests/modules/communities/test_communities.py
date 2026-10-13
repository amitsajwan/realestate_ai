"""Neighbourhood articles: found from OpenStreetMap, written from facts only, published only when checked and not thin."""
from datetime import datetime, timedelta, timezone

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
            "Kesnand is a neighbourhood in the Wagholi area of Pune, on the northern side of the area. Distances here are measured "
            "in a straight line on OpenStreetMap, so road distances will be longer.",
            "Within a short distance there is a school, Kesnand Zilla Parishad School, and Lifeline Hospital. Bank of Maharashtra, a "
            "D Mart supermarket and the Shiv Mandir temple are also close by, according to OpenStreetMap.",
            "Two projects registered with MahaRERA carry the name of the neighbourhood, both by Rohan Builders. Their completion dates "
            "are the ones filed with MahaRERA and can change, so check each project page and the MahaRERA record before deciding.",
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


async def test_writes_from_facts_and_publishes_only_a_checked_article():
    db, store = await seeded()
    await discover.run(store, osm(), NOW)
    doc = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    llm = FakeLLM(GOOD)
    out = await write.write_one(store, doc, llm, osm(), NOW)
    assert out == {"id": "wagholi/kesnand", "published": True, "notes": []}
    facts = llm.calls[0]
    assert "Nearby school: Kesnand Zilla Parishad School" in facts and "Kesnand Heights Phase 2" in facts and "45 of 120 homes booked" in facts
    saved = await db.get_collection(discover.COLLECTION).find_one({"_id": "wagholi/kesnand"})
    assert saved["published"] and saved["title"] == GOOD["title"] and len(saved["facts"]["projects"]) == 2


async def test_invented_numbers_sales_words_or_thin_facts_are_not_published():
    db, store = await seeded()
    await discover.run(store, osm(), NOW)
    coll = db.get_collection(discover.COLLECTION)
    doc = await coll.find_one({"_id": "wagholi/kesnand"})
    bad = {**GOOD, "paragraphs": GOOD["paragraphs"][:2] + ["Prices start at 55 lakh in this premium pocket. " + GOOD["paragraphs"][2]]}
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
    assert one["title"] == GOOD["title"] and len(one["paragraphs"]) == 3 and one["facts"]["nearby"]
    assert c.get("/public/communities/wagholi/ubale-nagar").status_code == 404   # found, not written
