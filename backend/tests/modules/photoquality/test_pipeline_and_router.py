"""The creative pipeline's redo-once on an AI 'redo', and POST /quality/review scoping."""
from types import SimpleNamespace

import cv2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.creative import pipeline
from app.modules.photoquality import router as qr
from app.modules.photoquality.analysis import load_bgr

from ..creative.helpers import simple_brief
from ..listings_fakes import ListingsDb
from .test_analysis_enhance import ROOM


class Reviewer:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    async def __call__(self, paths, context, **kw):
        self.calls.append((list(paths), context))
        return self.replies.pop(0)


AI_REDO = {"score": 35, "verdict": "redo", "notes": ["text cut at the bottom"], "source": "ai"}
AI_GOOD = {"score": 86, "verdict": "good", "notes": [], "source": "ai"}


async def test_redo_once_on_ai_redo(tmp_path):
    rev = Reviewer(AI_REDO, AI_GOOD)
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", None, seed=0, out_dir=tmp_path, reviewer=rev)
    assert len(rev.calls) == 2                       # the first pack, then the single redo
    assert pack.report["vision"]["redone"] is True and pack.report["vision"]["verdict"] == "good"
    assert pack.report["ok"] is True                 # the redo passed every critic guard
    assert pack.images == rev.calls[1][0]
    assert rev.calls[0][1]["critic"]["ok"] is True and rev.calls[0][1]["headline"]


async def test_redo_is_not_kept_when_its_review_is_worse(tmp_path):
    rev = Reviewer(AI_REDO, {**AI_REDO, "score": 20})
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", None, seed=0, out_dir=tmp_path, reviewer=rev)
    assert len(rev.calls) == 2 and pack.report["vision"]["score"] == 35 and "redone" not in pack.report["vision"]
    assert pack.images == rev.calls[0][0]


async def test_no_redo_for_good_or_rule_only_reviews(tmp_path):
    for reply in (AI_GOOD, {**AI_REDO, "source": "rules"}):
        rev = Reviewer(reply)
        pack = await pipeline.make(simple_brief(), "buyer", "instagram", None, seed=0, out_dir=tmp_path, reviewer=rev)
        assert len(rev.calls) == 1 and pack.report["vision"]["verdict"] == reply["verdict"]


async def test_reviewer_off_and_reviewer_crash(tmp_path):
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", None, seed=0, out_dir=tmp_path, reviewer=None)
    assert "vision" not in pack.report

    async def boom(paths, context):
        raise RuntimeError("x")
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", None, seed=0, out_dir=tmp_path, reviewer=boom)
    assert "vision" not in pack.report and pack.images


# ---- POST /quality/review -----------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIRECTORY", str(tmp_path))
    monkeypatch.delenv("CONCIERGE_OWNER_IDS", raising=False)
    monkeypatch.setenv("CALENDAR_OWNER_IDS", "OWNER")
    monkeypatch.setenv("NEWSROOM_OWNER_IDS", "OWNER")
    for rel in ("marketing/L1/cover.jpg", "calendar/w1/x-1.jpg", "news/n1-ig.jpg"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(p), load_bgr(ROOM))
    db = ListingsDb()
    db.get_collection("listings").docs.append({"_id": "L1", "agent_id": "A1", "title": "2BHK"})
    db.get_collection("marketing_packs").docs.append({"_id": "L1", "headline": "2BHK in Baner", "instagram": {"caption": "cap"},
                                                      "images": {"cover": {"path": "/uploads/marketing/L1/cover.jpg"},
                                                                 "facts": {"path": "/uploads/../../etc/passwd"}}})
    db.get_collection("content_calendar").docs.append({"_id": "C1", "kind": "post", "caption": "c", "images": ["calendar/w1/x-1.jpg"]})
    db.get_collection("newsroom_items").docs.append({"_id": "N1", "draft": {"title": "Metro", "text": "t"}, "card": {"ig": "news/n1-ig.jpg"}})
    seen = []

    async def reviewer(paths, context, use_cache=True):
        seen.append(([p.name for p in paths], context, use_cache))
        return {"score": 82, "verdict": "good", "notes": [], "source": "ai", "ai_available": True, "model": "m"}

    who = SimpleNamespace(id="A1", is_superuser=False)
    app = FastAPI()
    app.include_router(qr.router, prefix="/quality")
    app.dependency_overrides[current_active_user] = lambda: who
    app.dependency_overrides[qr.get_db] = lambda: db
    app.dependency_overrides[qr.get_reviewer] = lambda: reviewer
    return TestClient(app), who, seen


def test_listing_review_is_scoped_to_its_agent(api):
    c, who, seen = api
    r = c.post("/quality/review", json={"kind": "listing", "id": "L1"})
    assert r.status_code == 200 and r.json()["summary"] == "Quality 82/100 · Good"
    assert seen[-1][0] == ["cover.jpg"] and seen[-1][1]["caption"] == "cap"   # the path escaping uploads is ignored
    who.id = "A2"
    assert c.post("/quality/review", json={"kind": "listing", "id": "L1"}).status_code == 404
    assert c.post("/quality/review", json={"kind": "listing", "id": "nope"}).status_code == 404
    who.is_superuser = True   # the concierge owner may review any agent's cards
    assert c.post("/quality/review", json={"kind": "listing", "id": "L1", "refresh": True}).status_code == 200
    assert seen[-1][2] is False


def test_calendar_and_news_are_owner_only(api):
    c, who, seen = api
    assert c.post("/quality/review", json={"kind": "calendar", "id": "C1"}).status_code == 403
    assert c.post("/quality/review", json={"kind": "news", "id": "N1"}).status_code == 403
    who.id = "OWNER"
    r = c.post("/quality/review", json={"kind": "calendar", "id": "C1"})
    assert r.status_code == 200 and seen[-1][0] == ["x-1.jpg"] and seen[-1][1]["caption"] == "c"
    r = c.post("/quality/review", json={"kind": "news", "id": "N1"})
    assert r.status_code == 200 and seen[-1][0] == ["n1-ig.jpg"] and seen[-1][1]["headline"] == "Metro"
    assert c.post("/quality/review", json={"kind": "news", "id": "N2"}).status_code == 404
    assert c.post("/quality/review", json={"kind": "other", "id": "N1"}).status_code == 422


def test_no_images_is_not_an_error(api):
    c, who, _ = api
    who.is_superuser = True
    db =c.app.dependency_overrides[qr.get_db]()
    db.get_collection("listings").docs.append({"_id": "L2", "agent_id": "A1"})
    r = c.post("/quality/review", json={"kind": "listing", "id": "L2"})
    assert r.status_code == 200 and r.json()["score"] is None
