from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.calendar import library
from app.modules.calendar import router as cr
from app.modules.calendar.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def owner_env(monkeypatch):
    monkeypatch.setenv("CALENDAR_OWNER_IDS", "OWNER")


def setup(user_id="OWNER", superuser=False):
    store = Store(FakeDb(), clock=lambda: NOW)
    app = FastAPI()
    app.include_router(cr.router, prefix="/calendar")
    app.dependency_overrides[cr.get_store] = lambda: store
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id=user_id, is_superuser=superuser)
    return TestClient(app), store


async def seed(store):
    e = library.BY_SLUG["carpet-under-rera"]
    a = await store.add(e.slug, "facebook_page", e.fb_caption, "calendar/carpet-under-rera.jpg", NOW + timedelta(days=2))
    b = await store.add(e.slug, "instagram", e.ig_caption, "calendar/ig/carpet-under-rera.jpg", NOW + timedelta(days=1))
    return a, b


def test_every_route_is_owner_only():
    assert len(cr.router.routes) == 8
    for route in cr.router.routes:
        assert any(d.call is cr.owner_only for d in route.dependant.dependencies), route.path


def test_strangers_are_refused_everywhere():
    c, _ = setup(user_id="someone-else")
    assert c.get("/calendar/upcoming").status_code == 403
    assert c.get("/calendar/status").status_code == 403
    assert c.post("/calendar/items/x/skip").status_code == 403
    assert c.post("/calendar/items/x/approve").status_code == 403


def test_superuser_is_allowed_even_without_the_owner_list(monkeypatch):
    monkeypatch.delenv("CALENDAR_OWNER_IDS")
    c, _ = setup(user_id="root", superuser=True)
    assert c.get("/calendar/upcoming").status_code == 200


async def test_upcoming_lists_scheduled_items_soonest_first():
    c, store = setup()
    a, b = await seed(store)
    rows = c.get("/calendar/upcoming").json()
    assert [r["id"] for r in rows] == [b, a] and rows[0]["channel"] == "instagram" and rows[0]["slug"] == "carpet-under-rera"
    assert c.get("/calendar/upcoming?limit=1").json()[0]["id"] == b


async def test_status_reports_counts_and_runner_state():
    c, store = setup()
    await seed(store)
    await store.set_run(last_run_at=NOW, last_counts={"published": 0}, last_error=None)
    st = c.get("/calendar/status").json()
    assert st["enabled"] is False and st["counts"]["scheduled"] == 2 and st["last_error"] is None and st["next_due"]


async def test_skip_then_not_skippable_again():
    c, store = setup()
    a, _ = await seed(store)
    assert c.post(f"/calendar/items/{a}/skip").json() == {"id": a, "status": "skipped"}
    assert (await store.get(a))["status"] == "skipped"
    assert c.post(f"/calendar/items/{a}/skip").status_code == 409
    assert c.post("/calendar/items/nope/skip").status_code == 404
    assert [r["id"] for r in c.get("/calendar/upcoming").json()] != [a]


async def test_upcoming_shows_kind_images_and_planned_items_and_approve_moves_them():
    c, store = setup()
    pid = await store.add("w1-a", "instagram", "cap", "calendar/w1/a-1.jpg", NOW + timedelta(days=1), kind="post", status="planned",
                          images=["calendar/w1/a-1.jpg", "calendar/w1/a-2.jpg"], creative={"layout": "checklist", "path": "rules", "secret": "x"}, week=1)
    rid = await store.add("reel-w1-tip", "facebook_page", "cap", "", NOW + timedelta(days=2), kind="reel", status="planned", week=1)
    rows = c.get("/calendar/upcoming").json()
    first = rows[0]
    assert first["id"] == pid and first["kind"] == "post" and first["status"] == "planned" and first["week"] == 1
    assert first["image_urls"] == ["/uploads/calendar/w1/a-1.jpg", "/uploads/calendar/w1/a-2.jpg"] and first["caption"] == "cap"
    assert first["creative"] == {"path": "rules", "layout": "checklist"}  # whitelisted fields only
    assert rows[1]["kind"] == "reel" and rows[1]["image_urls"] == [] and rows[1]["video_url"] is None
    got = c.post(f"/calendar/items/{pid}/approve").json()
    assert {k: got[k] for k in ("id", "status")} == {"id": pid, "status": "approved"} and got["due_at"]
    assert (await store.get(pid))["status"] == "approved"
    assert c.post(f"/calendar/items/{pid}/approve").status_code == 409
    assert c.post("/calendar/items/nope/approve").status_code == 404
    assert c.post(f"/calendar/items/{rid}/skip").json()["status"] == "skipped"
