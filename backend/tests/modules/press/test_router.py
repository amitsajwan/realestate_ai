"""Press's Studio API: every route is owner-only, and the patch endpoint edits a draft, marks it sent/skipped, records
a reply or a link won."""
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.press.router import configure, get_db, public_router, router
from app.modules.press.store import Store

from ..fakes import FakeDb

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)
OWNER = SimpleNamespace(id="owner", is_superuser=True)
AGENT = SimpleNamespace(id="agent1", is_superuser=False)


def client(user, db=None):
    db = db or FakeDb()
    configure(is_operator=lambda u: False)
    app = FastAPI()
    app.include_router(router, prefix="/press")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_active_user] = lambda: user
    return TestClient(app), db


async def seed_story_and_pitch(db):
    store = Store(db)
    facts = [{"text": "Kharadi registered 4 new MahaRERA projects.", "area": "kharadi", "topic": "registrations",
              "source": "s", "as_of": "2026-11-17"}]
    await store.save_story("2026-11", facts, facts, NOW)
    j = {"outlet": "Hindustan Times", "title": "t", "url": "https://hindustantimes.com/a", "date": "", "name": None,
         "email": None, "contact_page": None}
    draft = {"subject": "subj", "body": "body", "origin": "template"}
    return await store.save_pitch("2026-11", j, draft, NOW)


def test_an_agent_cannot_open_press():
    c, _ = client(AGENT)
    assert c.get("/press/story").status_code == 403
    assert c.get("/press/pitches").status_code == 403
    assert c.get("/press/summary").status_code == 403
    assert c.post("/press/run").status_code == 403
    assert c.patch("/press/pitches/x", json={"status": "sent"}).status_code == 403


def test_the_owner_sees_the_story_and_pitches():
    import asyncio
    db = FakeDb()
    pitch = asyncio.get_event_loop().run_until_complete(seed_story_and_pitch(db))
    c, _ = client(OWNER, db)
    story = c.get("/press/story").json()
    assert story["month"] == "2026-11" and story["facts"][0]["area"] == "kharadi"
    pitches = c.get("/press/pitches").json()
    assert len(pitches) == 1 and pitches[0]["id"] == pitch["_id"] and pitches[0]["status"] == "draft"


def test_patch_edits_the_draft_and_marks_it_sent():
    import asyncio
    db = FakeDb()
    pitch = asyncio.get_event_loop().run_until_complete(seed_story_and_pitch(db))
    c, _ = client(OWNER, db)
    r = c.patch(f"/press/pitches/{pitch['_id']}", json={"subject": "edited subject", "status": "sent"})
    assert r.status_code == 200
    out = r.json()
    assert out["subject"] == "edited subject" and out["status"] == "sent"


def test_patch_records_a_reply_and_a_link_won():
    import asyncio
    db = FakeDb()
    pitch = asyncio.get_event_loop().run_until_complete(seed_story_and_pitch(db))
    c, _ = client(OWNER, db)
    r = c.patch(f"/press/pitches/{pitch['_id']}", json={"replied": True, "link_won_url": "https://hindustantimes.com/story"})
    assert r.status_code == 200
    out = r.json()
    assert out["replied"] is True and out["link_won_url"] == "https://hindustantimes.com/story"
    summary = c.get("/press/summary").json()
    assert summary["replied"] == 1 and summary["links_won"] == 1


def test_patch_on_an_unknown_pitch_is_404():
    c, _ = client(OWNER)
    assert c.patch("/press/pitches/missing", json={"status": "sent"}).status_code == 404


def test_public_story_has_headline_facts_only_no_journalist_details():
    import asyncio
    db = FakeDb()
    asyncio.get_event_loop().run_until_complete(seed_story_and_pitch(db))
    app = FastAPI()
    app.include_router(public_router, prefix="/public")
    app.dependency_overrides[get_db] = lambda: db
    c = TestClient(app)
    r = c.get("/public/press/story")
    assert r.status_code == 200
    body = r.json()
    assert body["month"] == "2026-11" and body["headline_facts"][0]["area"] == "kharadi"
    assert "journalist" not in body and "pitches" not in body


def test_an_unknown_status_is_refused():
    import asyncio
    db = FakeDb()
    pitch = asyncio.get_event_loop().run_until_complete(seed_story_and_pitch(db))
    c, _ = client(OWNER, db)
    assert c.patch(f"/press/pitches/{pitch['_id']}", json={"status": "weird"}).status_code == 400
