"""Admin home: owner gating, overview aggregation, pause switches gating the runners, invite-request invite / dismiss."""
import asyncio
import logging
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.admin import controls, health
from app.modules.admin import router as ar
from app.modules.admin.service import AdminService, day_start
from app.modules.concierge import router as cr

from ..concierge.helpers import make

NOW = datetime(2026, 10, 2, 6, 0, 0)  # 11:30 in India
OWNER = SimpleNamespace(id="OWNER", is_superuser=True)
AGENT = SimpleNamespace(id="agent1", is_superuser=False)


async def ok_ping():
    return {"ok": True, "configured": True}


def client(user, db=None, ping=ok_ping):
    svc, db, _ = make(db)
    cr.limiter.hits.clear()
    health._ai_cache.clear()
    app = FastAPI()
    app.include_router(ar.router, prefix="/admin")
    app.dependency_overrides[ar.get_service] = lambda: AdminService(db, now=lambda: NOW)
    app.dependency_overrides[cr.get_service] = lambda: svc
    app.dependency_overrides[ar.get_ai_ping] = lambda: ping
    app.dependency_overrides[current_active_user] = lambda: user
    return TestClient(app), db, svc


@pytest.fixture(autouse=True)
def quiet_env(monkeypatch):
    for k in ("CONCIERGE_OWNER_IDS", "CALENDAR_ENABLED", "NEWSROOM_ENABLED", "ENGAGE_ENABLED", "WHATSAPP_ENABLED", "META_PAGE_ID",
              "META_PAGE_ACCESS_TOKEN", "META_IG_BUSINESS_ID", "SOCIAL_DRY_RUN"):
        monkeypatch.delenv(k, raising=False)


# ---- owner gating ------------------------------------------------------------------------------------------------------
def test_every_route_is_owner_only():
    c, _, _ = client(AGENT)
    assert c.get("/admin/overview").status_code == 403
    assert c.post("/admin/controls", json={"posting_paused": True}).status_code == 403
    assert c.get("/admin/invite-requests").status_code == 403
    assert c.post("/admin/invite-requests/x/invite").status_code == 403
    assert c.post("/admin/invite-requests/x/dismiss").status_code == 403
    for route in ar.router.routes:
        assert any(getattr(d.call, "__name__", "") == "owner_only" for d in route.dependant.dependencies), route.path


def test_concierge_owner_ids_grant_access(monkeypatch):
    monkeypatch.setenv("CONCIERGE_OWNER_IDS", "u9, u10")
    assert client(SimpleNamespace(id="u10", is_superuser=False))[0].get("/admin/controls").status_code == 200
    assert client(SimpleNamespace(id="u11", is_superuser=False))[0].get("/admin/controls").status_code == 403


# ---- overview ----------------------------------------------------------------------------------------------------------
def test_day_start_is_midnight_in_india():
    assert day_start(NOW) == datetime(2026, 10, 1, 18, 30)
    assert day_start(datetime(2026, 10, 1, 19, 0)) == datetime(2026, 10, 1, 18, 30)


async def seed(db):
    today, days3, days10 = NOW - timedelta(hours=1), NOW - timedelta(days=3), NOW - timedelta(days=10)
    contacts = db.get_collection("contacts")
    await contacts.insert_one({"source": "chat", "anon_ids": ["chat-abc"], "created_at": today, "phone": "+919000000099"})
    await contacts.insert_one({"source": "whatsapp", "anon_ids": ["whatsapp:1"], "created_at": today})
    await contacts.insert_one({"source": "facebook_comment", "anon_ids": [], "created_at": days3})
    await contacts.insert_one({"source": "whatsapp", "anon_ids": [], "created_at": days10})
    for ts in (today, days3, days10):
        await db.get_collection("interest_events").insert_one({"type": "interest", "ts": ts})
    await db.get_collection("interest_events").insert_one({"type": "click", "ts": today})
    await db.get_collection("engage_comments").insert_one({"status": "replied", "replied_at": today})
    await db.get_collection("engage_comments").insert_one({"status": "dry_run", "processed_at": today})
    cal = db.get_collection("content_calendar")
    await cal.insert_one({"status": "published", "channel": "facebook_page", "published_at": today})
    await cal.insert_one({"status": "published", "channel": "instagram", "published_at": days3})
    await cal.insert_one({"status": "planned", "channel": "instagram"})
    await cal.insert_one({"status": "planned", "channel": "facebook_page"})
    await db.get_collection("publications").insert_one({"status": "published", "channel": "instagram", "updated_at": today})
    await db.get_collection("newsroom_items").insert_one({"status": "pending_review"})
    await db.get_collection("invite_requests").insert_one({"_id": ObjectId(), "name": "Web Person", "phone": "+919000000017", "city": "Pune",
                                                           "status": "new", "created_at": today})
    await db.get_collection("invite_requests").insert_one({"name": "Old", "phone": "+919000000018", "status": "invited", "created_at": days3})
    await db.get_collection("engage_status").insert_one({"_id": "facebook", "ok": False, "reconnect": True, "code": 190, "checked_at": today})
    await db.get_collection("calendar_status").insert_one({"_id": "runner", "last_run_at": today, "last_error": None})


def test_overview_counts_waiting_agents_health_and_controls(monkeypatch):
    monkeypatch.setenv("CALENDAR_ENABLED", "true")
    monkeypatch.setenv("META_PAGE_ID", "P1")
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "EAAB" + "x" * 30)
    c, db, svc = client(OWNER)
    asyncio.run(seed(db))
    asyncio.run(svc.create_agent("OWNER", "Rahul Sharma", "+919876543210", "Rahul, Baner"))
    r = c.get("/admin/overview")
    assert r.status_code == 200
    o = r.json()
    t, w = o["counts"]["today"], o["counts"]["week"]
    assert t["leads"] == 2 and t["chat_leads"] == 1 and t["whatsapp_leads"] == 1
    assert w["leads"] == 3 and w["leads_by_source"] == {"chat": 1, "whatsapp": 1, "facebook_comment": 1}
    assert t["interest_taps"] == 1 and w["interest_taps"] == 2
    assert t["comments_answered"] == 1
    assert t["posts_published"] == {"facebook_page": 1, "instagram": 1}
    assert w["posts_published"] == {"facebook_page": 1, "instagram": 2}
    assert o["waiting"] == {"posts": 2, "news": 1, "invite_requests": 1}
    assert [x["name"] for x in o["invite_requests"]] == ["Web Person"]
    assert o["invite_requests"][0]["mobile"] == "90******17"
    assert o["agents"][0]["name"] == "Rahul Sharma" and o["agents"][0]["progress"]["total"] == 8 and o["agents"][0]["mobile"] == "98******10"
    rows = {h["key"]: h for h in o["health"]}
    assert set(rows) == {"facebook", "instagram", "whatsapp", "ai", "posting", "comments", "news"}
    assert rows["facebook"]["status"] == "bad" and "meta_connect.ps1" in rows["facebook"]["fix"]
    assert rows["ai"]["status"] == "ok" and rows["posting"]["status"] == "ok" and rows["posting"]["last_run_at"]
    assert rows["news"]["status"] == "warn" and rows["whatsapp"]["status"] == "warn"
    assert o["controls"]["posting_paused"] is False
    for phone in ("9876543210", "9000000017", "9000000099"):  # no phone numbers in the answer, only masked ones
        assert phone not in r.text


def test_ai_ping_is_cached_for_ten_minutes():
    health._ai_cache.clear()
    calls, t = [], [1000.0]

    async def ping():
        calls.append(1)
        return {"ok": len(calls) > 1, "configured": True}

    clock = lambda: t[0]
    assert asyncio.run(health.ai_status(ping, clock))["ok"] is False
    t[0] += 599
    assert asyncio.run(health.ai_status(ping, clock))["ok"] is False and len(calls) == 1
    t[0] += 2
    assert asyncio.run(health.ai_status(ping, clock))["ok"] is True and len(calls) == 2


def test_ai_ping_failure_shows_red():
    async def broken():
        raise RuntimeError("down")
    c, _, _ = client(OWNER, ping=broken)
    rows = {h["key"]: h for h in c.get("/admin/overview").json()["health"]}
    assert rows["ai"]["status"] == "bad" and rows["ai"]["fix"]


# ---- controls ----------------------------------------------------------------------------------------------------------
def test_controls_store_who_and_when_and_show_in_health():
    c, db, _ = client(OWNER)
    assert c.post("/admin/controls", json={"bogus": True}).status_code == 422
    r = c.post("/admin/controls", json={"posting_paused": True})
    assert r.json()["posting_paused"] is True and r.json()["comments_paused"] is False and r.json()["updated_by"] == "OWNER"
    c.post("/admin/controls", json={"news_paused": True})
    doc = asyncio.run(db.get_collection("admin_settings").find_one({"_id": "controls"}))
    assert doc["posting_paused"] and doc["news_paused"] and len(doc["history"]) == 2 and doc["history"][0]["by"] == "OWNER"
    rows = {h["key"]: h for h in c.get("/admin/overview").json()["health"]}
    assert rows["posting"]["text"] == "Paused by you"
    assert c.post("/admin/controls", json={"posting_paused": False}).json()["posting_paused"] is False
    assert c.get("/admin/controls").json()["news_paused"] is True


async def _spin(module, monkeypatch, db):
    real_sleep = asyncio.sleep

    async def quick(_):
        await real_sleep(0)

    monkeypatch.setattr(module, "get_database", lambda: db)
    monkeypatch.setattr(module.asyncio, "sleep", quick)
    task = asyncio.create_task(module.loop())
    for _ in range(10):
        await real_sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def _paused_db(**flags):
    from tests.modules.fakes import FakeDb
    db = FakeDb()
    await controls.set_controls(db, flags, "OWNER", NOW)
    return db


async def test_calendar_runner_skips_while_posting_is_paused(monkeypatch, caplog):
    from app.modules.calendar import runner
    monkeypatch.setenv("CALENDAR_ENABLED", "true")
    calls = []

    async def run_once(*a, **k):
        calls.append(1)
        return {}

    monkeypatch.setattr(runner, "run_once", run_once)
    monkeypatch.setattr(runner, "prerender_reels", lambda *a, **k: asyncio.sleep(0))
    caplog.set_level(logging.INFO, logger=runner.__name__)
    await _spin(runner, monkeypatch, await _paused_db(posting_paused=True))
    assert calls == [] and "paused by owner" in caplog.text
    await _spin(runner, monkeypatch, await _paused_db(posting_paused=False, news_paused=True))
    assert calls  # resumed: the cycle runs again


async def test_newsroom_runner_skips_while_news_is_paused(monkeypatch, caplog):
    from app.modules.newsroom import runner
    monkeypatch.setenv("NEWSROOM_ENABLED", "true")
    calls = []

    async def cycle(*a, **k):
        calls.append(1)
        return {}

    monkeypatch.setattr(runner, "cycle", cycle)
    caplog.set_level(logging.INFO, logger=runner.__name__)
    await _spin(runner, monkeypatch, await _paused_db(news_paused=True))
    assert calls == [] and "paused by owner" in caplog.text
    await _spin(runner, monkeypatch, await _paused_db(posting_paused=True))
    assert calls


async def test_engage_runner_skips_while_comments_are_paused(monkeypatch, caplog):
    from app.modules.engage import runner
    monkeypatch.setenv("ENGAGE_ENABLED", "true")
    monkeypatch.setenv("META_PAGE_ID", "P1")
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "EAAB" + "x" * 30)
    calls = []

    class Svc:
        def __init__(self, *a, **k):
            pass

        async def run_once(self):
            calls.append(1)
            return {}

    monkeypatch.setattr(runner, "EngageService", Svc)
    monkeypatch.setattr(runner, "default_llm", lambda: None)
    caplog.set_level(logging.INFO, logger=runner.__name__)
    await _spin(runner, monkeypatch, await _paused_db(comments_paused=True))
    assert calls == [] and "paused by owner" in caplog.text
    await _spin(runner, monkeypatch, await _paused_db(comments_paused=False))
    assert calls


async def test_a_broken_settings_read_never_pauses():
    class Broken:
        def get_collection(self, name):
            raise RuntimeError("db down")
    assert await controls.is_paused(Broken(), "posting_paused") is False


# ---- invite requests ---------------------------------------------------------------------------------------------------
def test_invite_request_creates_the_agent_and_marks_it_invited():
    c, db, _ = client(OWNER)
    asyncio.run(seed(db))
    items = c.get("/admin/invite-requests").json()["items"]
    assert len(items) == 1 and items[0]["mobile"] == "90******17"
    rid = items[0]["id"]
    r = c.post(f"/admin/invite-requests/{rid}/invite")
    assert r.status_code == 200
    out = r.json()
    assert len(out["code"]) == 6 and "9000000017" in out["whatsapp_message"] and out["agent"]["name"] == "Web Person"
    assert out["request"]["status"] == "invited"
    doc = asyncio.run(db.get_collection("invite_requests").find_one({"_id": ObjectId(rid)}))
    assert doc["status"] == "invited" and doc["invited_by"] == "OWNER" and doc["agent_id"] == out["agent"]["id"]
    assert c.get("/admin/invite-requests").json()["items"] == []
    assert c.post(f"/admin/invite-requests/{rid}/invite").status_code == 409
    agents = c.get("/admin/overview").json()["agents"]
    assert [a["name"] for a in agents] == ["Web Person"]


def test_dismiss_and_missing_request():
    c, db, _ = client(OWNER)
    asyncio.run(seed(db))
    rid = c.get("/admin/invite-requests").json()["items"][0]["id"]
    assert c.post(f"/admin/invite-requests/{rid}/dismiss").json()["status"] == "dismissed"
    assert c.post(f"/admin/invite-requests/{rid}/dismiss").status_code == 409
    assert c.post(f"/admin/invite-requests/{ObjectId()}/invite").status_code == 404
    assert c.get("/admin/overview").json()["agents"] == []
