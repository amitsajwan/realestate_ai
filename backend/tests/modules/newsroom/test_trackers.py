"""Trackers: reports attach by fixed rules whatever the filter decided, the same story folds into one timeline line, and the status
line changes only when the owner writes one."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.newsroom import public as pub
from app.modules.newsroom import presentation as pr
from app.modules.newsroom import router as owner
from app.modules.newsroom import trackers
from app.modules.newsroom.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 25, 9, 0, tzinfo=timezone.utc)


async def report(store, id, title, source="Punekar News", days_ago=1, status="dropped"):
    at = NOW - timedelta(days=days_ago)
    await store.items.insert_one({"_id": id, "status": status, "created_at": at, "raw": {
        "id": id, "source": source, "url": f"https://example.com/{id}", "title": title, "text": title, "published_at": at, "fetched_at": at}})


def apps(store):
    app = FastAPI()
    app.include_router(pub.router, prefix="/public")
    app.include_router(owner.router, prefix="/newsroom")
    app.dependency_overrides[pub.get_store] = lambda: store
    app.dependency_overrides[owner.get_store] = lambda: store
    app.dependency_overrides[owner.owner_only] = lambda: type("U", (), {"id": "owner"})()
    return TestClient(app)


def test_every_tracker_file_loads_with_a_status():
    defs = trackers.definitions()
    assert {"purandar-airport", "pune-ring-road", "hcmtr", "pune-metro-line-3", "lohegaon-hospital", "home-loan-rates"} <= set(defs)
    assert all(d["history"][-1]["status"] for d in defs.values())


def test_rules_match_the_thing_and_not_its_namesakes():
    ring, metro = trackers.get("pune-ring-road"), trackers.get("pune-metro-line-3")
    assert trackers.matches(ring, "Pune Ring Road Cost Rises By Rs 10,502 Crore As Maharashtra Takes Over Stretch From NHAI")
    assert not trackers.matches(ring, "Bengaluru sub-registrar suspended over Peripheral Ring Road project land sale")
    assert not trackers.matches(ring, "October 30 deadline set for HCMTR, inner ring road land surveys")
    assert trackers.matches(trackers.get("hcmtr"), "October 30 deadline set for HCMTR, inner ring road land surveys")
    assert trackers.matches(metro, "Ready to run, but yet to roll: Undue delay in Hinjewadi Metro launch frustrates IT professionals")
    assert not trackers.matches(metro, "Alstom to Deliver First Mumbai Metro Line 4 Train by Dec")


async def test_dropped_reports_attach_once_and_maharera_records_never():
    store = Store(FakeDb())
    await report(store, "a1", "Purandar Airport: Pune Administration to Compulsorily Acquire Remaining 40 Hectares")
    await report(store, "a2", "Listed or updated on MahaRERA: Purandar Airport View, Purandhar", source="MahaRERA")
    await report(store, "a3", "Pune Reports First Suspected Dengue Death of 2026")
    assert await trackers.attach_new(store, NOW) == 1
    await report(store, "a4", "Purandar Airport Project Moves Ahead as MADC Begins Consultant Appointment", days_ago=0)
    assert await trackers.attach_new(store, NOW + timedelta(hours=1)) == 1   # only what came in since the last pass
    assert [r["item_id"] for r in await store.tracker_reports("purandar-airport")] == ["a4", "a1"]


def test_the_same_story_from_several_publishers_is_one_timeline_line():
    rows = [{"title": "Purandar Airport: Pune Administration to Compulsorily Acquire Remaining 40 Hectares", "source": "Punekar News",
             "url": "https://a", "date": NOW - timedelta(days=1)},
            {"title": "Purandar Airport: Administration to Compulsorily Acquire Remaining 40 Hectares - Pune Mirror", "source": "Pune Mirror",
             "url": "https://b", "date": NOW - timedelta(days=1, hours=3)},
            {"title": "HC rejects farmers' plea against Purandar airport land acquisition", "source": "Hindustan Times",
             "url": "https://c", "date": NOW - timedelta(days=30)},
            {"title": "A wrong match", "source": "X", "url": "https://d", "date": NOW, "hidden": True}]
    lines = trackers.groups(rows)
    assert [g["source"] for g in lines] == ["Punekar News", "Hindustan Times"]
    assert [a["name"] for a in lines[0]["also"]] == ["Pune Mirror"]


async def test_owner_status_update_becomes_the_public_status_and_bad_ones_are_refused():
    store = Store(FakeDb())
    await report(store, "h1", "Lohegaon Hospital Opens OPD to Patients", days_ago=0)
    await trackers.attach_new(store, NOW)
    c = apps(store)
    before = c.get("/public/trackers/lohegaon-hospital").json()
    assert before["newer_reports"] == 1 and before["timeline"][0]["headline"] == "Lohegaon Hospital Opens OPD to Patients"
    assert c.post("/newsroom/trackers/lohegaon-hospital/status", json={"status": "Open", "date": "2026-10-25"}).status_code == 422
    assert c.post("/newsroom/trackers/lohegaon-hospital/status", json={"status": "The OPD is open.", "date": "2026-10-25", "stage": 9}).status_code == 422
    ok = c.post("/newsroom/trackers/lohegaon-hospital/status", json={"status": "The OPD is open to patients.", "date": "2026-10-25", "stage": 2,
                                                                     "sources": ["Punekar News"]})
    assert ok.status_code == 200 and ok.json()["new_count"] == 0
    after = c.get("/public/trackers/lohegaon-hospital").json()
    assert (after["status"], after["stage"], after["status_sources"]) == ("The OPD is open to patients.", 2, ["Punekar News"])
    assert after["history"][1]["status"].startswith("Built and staffed")   # the older line stays in the history


async def test_a_hidden_report_leaves_the_public_page_and_area_lists_keep_city_wide_rates():
    store = Store(FakeDb())
    await report(store, "w1", "Wagholi Water Supply Disrupted as Bhima River Level Drops")
    await trackers.attach_new(store, NOW)
    c = apps(store)
    assert c.post("/newsroom/trackers/merged-villages-water/reports/w1/hide", json={"hidden": True}).status_code == 200
    assert c.get("/public/trackers/merged-villages-water").json()["timeline"] == []
    wagholi = {t["slug"] for t in c.get("/public/trackers?area=wagholi").json()}
    assert "merged-villages-water" in wagholi and "home-loan-rates" in wagholi and "lohegaon-hospital" not in wagholi
    assert c.get("/public/trackers?area=nowhere").json() == []
    assert c.get("/public/trackers/no-such").status_code == 404


def test_text_read_as_windows_1252_is_put_back():
    assert pr.one_line("gets â‚¹10,502 crore, Maharashtraâ€™s bills") == "gets ₹10,502 crore, Maharashtra’s bills"
    assert pr.one_line("café ₹5") == "café ₹5"
