"""GET /newsroom/items?status=...: the owner's Scheduled, Published and Rejected lists."""
from datetime import timedelta

from .helpers import NOW
from .test_router import owner_env, seed, setup  # noqa: F401 (owner_env is an autouse fixture)


async def test_lists_by_status_with_links_reason_and_newest_first():
    c, store = setup()
    await seed(store, 4)
    await store.move("i1", "approved", "approved by owner", publish={"platform_id": None, "scheduled_for": NOW + timedelta(days=2)})
    await store.move("i2", "published", "", published_at=NOW, publish={"platform_id": "p1", "scheduled_for": None, "channels": {
        "facebook": {"ok": True, "id": "p1", "permalink": "https://facebook.test/p1"},
        "instagram": {"ok": False, "error": "limit"}}})
    assert c.post("/newsroom/items/i3/reject", json={"reason": "old news"}).status_code == 200
    assert c.post("/newsroom/items/i4/reject", json={}).status_code == 200

    sched = c.get("/newsroom/items?status=scheduled").json()
    assert [r["id"] for r in sched] == ["i1"] and sched[0]["status"] == "approved"
    assert sched[0]["scheduled_for"].startswith(str((NOW + timedelta(days=2)).date()))
    assert sched[0]["news_url"].startswith("https://site.test/news/") and sched[0]["areas"] == ["kharadi"]

    pub = c.get("/newsroom/items?status=published").json()
    assert len(pub) == 1 and pub[0]["permalinks"] == {"facebook": "https://facebook.test/p1"}
    assert pub[0]["published_at"] and pub[0]["news_url"].startswith("https://site.test/news/") and pub[0]["reason"] is None
    assert pub[0]["title"] and pub[0]["check"]["ok"] is True

    rej = c.get("/newsroom/items?status=rejected").json()
    assert [r["id"] for r in rej] == ["i4", "i3"]  # most recently changed first
    by = {r["id"]: r for r in rej}
    assert by["i3"]["reason"] == "old news" and by["i4"]["reason"] is None and by["i3"]["news_url"] is None
    assert len(c.get("/newsroom/items?status=rejected&limit=1").json()) == 1


async def test_unknown_status_is_422_and_pending_is_not_a_list():
    c, store = setup()
    await seed(store)
    assert c.get("/newsroom/items?status=pending_review").status_code == 422
    assert c.get("/newsroom/items?status=dropped").status_code == 422
    assert c.get("/newsroom/items").status_code == 422


async def test_lists_are_owner_only():
    from types import SimpleNamespace
    from app.core.auth_backend import current_active_user
    c, store = setup()
    c.app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="SOMEONE", is_superuser=False)
    assert c.get("/newsroom/items?status=published").status_code == 403
