from types import SimpleNamespace

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.newsroom import router as nr
from app.modules.newsroom.store import Store
from app.modules.newsroom.types import CheckResult

from ..fakes import FakeDb
from .helpers import NOW, FakePublisher, FakeSource, good_stages, item
from app.modules.newsroom.config import NewsroomConfig
from app.modules.newsroom.pipeline import run_once


@pytest.fixture(autouse=True)
def owner_env(monkeypatch):
    monkeypatch.setenv("NEWSROOM_OWNER_IDS", "OWNER")


def setup(checker=None):
    store = Store(FakeDb())
    app = FastAPI()
    app.include_router(nr.router, prefix="/newsroom")
    app.dependency_overrides[nr.get_store] = lambda: store
    app.dependency_overrides[nr.get_checker] = lambda: checker
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="OWNER", is_superuser=False)
    return TestClient(app), store


async def seed(store, n=1):
    await run_once(store, [FakeSource([item(i) for i in range(1, n + 1)])], good_stages(), FakePublisher(), object(), NOW, NewsroomConfig(daily_cap=2))


def test_every_route_is_owner_only():
    assert len(nr.router.routes) == 6
    for route in nr.router.routes:
        assert any(d.call is nr.owner_only for d in route.dependant.dependencies), route.path


async def test_queue_and_status():
    c, store = setup()
    await seed(store)
    await store.set_run(last_run_at=NOW, last_error=None)
    q = c.get("/newsroom/queue").json()
    assert len(q) == 1 and q[0]["id"] == "i1" and q[0]["pillar"] == "infrastructure" and q[0]["areas"] == ["kharadi"]
    assert q[0]["sources"][0]["url"] == "https://news.test/1" and q[0]["age_days"] is not None and q[0]["draft"]["text"]
    st = c.get("/newsroom/status").json()
    assert st["enabled"] is False and st["counts"]["pending_review"] == 1 and st["last_error"] is None


async def test_approve_unedited_then_not_pending_again():
    c, store = setup()
    await seed(store)
    r = c.post("/newsroom/items/i1/approve", json={})
    assert r.status_code == 200 and r.json()["edited"] is False
    d = await store.get("i1")
    assert d["status"] == "approved" and d["review"]["by"] == "OWNER"
    assert c.post("/newsroom/items/i1/approve", json={}).status_code == 409
    assert c.post("/newsroom/items/nope/approve", json={}).status_code == 404


async def test_approve_with_edit_reruns_check_and_stores_text():
    calls = []

    def checker(d, facts, raw):
        calls.append(d.text)
        return CheckResult(ok="bad" not in d.text, problems=["bad word"])
    c, store = setup(checker)
    await seed(store)
    r = c.post("/newsroom/items/i1/approve", json={"text": "bad edit"})
    assert r.status_code == 422 and (await store.get("i1"))["status"] == "pending_review"
    r = c.post("/newsroom/items/i1/approve", json={"text": "Better text. Thoughts?", "when": "2099-01-01T10:00:00Z"})
    assert r.status_code == 200 and r.json()["edited"] is True and len(calls) == 2
    d = await store.get("i1")
    assert d["draft"]["text"] == "Better text. Thoughts?" and d["review"]["edits"] is True and d["publish"]["scheduled_for"].year == 2099


async def test_approve_rejects_past_time():
    c, store = setup()
    await seed(store)
    assert c.post("/newsroom/items/i1/approve", json={"when": "2000-01-01T00:00:00Z"}).status_code == 422


async def test_reject():
    c, store = setup()
    await seed(store)
    assert c.post("/newsroom/items/i1/reject", json={"reason": "off topic"}).status_code == 200
    d = await store.get("i1")
    assert d["status"] == "rejected" and d["history"][-1]["note"] == "off topic"
    assert c.post("/newsroom/items/i1/reject").status_code == 409


def test_a_signed_in_user_who_is_not_the_owner_is_refused(monkeypatch):
    c, _ = setup()
    monkeypatch.delenv("NEWSROOM_OWNER_IDS", raising=False)
    assert c.get("/newsroom/queue").status_code == 403
    assert c.post("/newsroom/items/x/approve", json={}).status_code == 403
    monkeypatch.setenv("NEWSROOM_OWNER_IDS", "OWNER")
    assert c.get("/newsroom/queue").status_code == 200
