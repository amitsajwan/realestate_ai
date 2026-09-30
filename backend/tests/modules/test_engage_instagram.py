"""Instagram comment assistant: real IgGraph/EngageGraph over httpx MockTransport fakes (no network) driving the shared EngageService."""
from datetime import datetime, timedelta
from urllib.parse import parse_qs

import httpx
import pytest

from app.modules.engage.brain import decide
from app.modules.engage.config import EngageConfig, load
from app.modules.engage.graph import EngageGraph
from app.modules.engage.ig_graph import IgGraph
from app.modules.engage.service import EngageService

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 9, 30, 12, 0, 0)
WHEN = (NOW - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+0000")
ME = "kharadi_prop"


def ig_comment(cid, text, user="priya", replies=None, when=WHEN):
    c = {"id": cid, "text": text, "username": user, "timestamp": when}
    if replies:
        c["replies"] = {"data": replies}
    return c


def media(comments, mid="M1", caption="2 BHK in Kharadi"):
    return {"id": mid, "caption": caption, "timestamp": WHEN, "permalink": f"https://instagram.com/p/{mid}/", "comments": {"data": comments}}


class NoAnswerLLM:
    async def json(self, system, user):
        return {"intent": "question", "language": "en", "answerable": False, "reply": ""}


class Meta:
    """Fake Graph API for both the Page and the Instagram account."""

    def __init__(self, ig_media=None, fb_posts=None):
        self.ig_media, self.fb_posts, self.calls, self.replies, self.fb_replies = ig_media or [], fb_posts or [], [], [], []

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path.split("/", 2)[2]  # drop /v23.0
        self.calls.append((request.method, path))
        if request.method == "GET" and path == "IG":
            return httpx.Response(200, json={"username": ME, "id": "IG"})
        if request.method == "GET" and path == "IG/media":
            return httpx.Response(200, json={"data": self.ig_media})
        if request.method == "GET" and path == "PAGE/posts":
            return httpx.Response(200, json={"data": self.fb_posts})
        if request.method == "POST" and path.endswith("/replies"):
            self.replies.append((path.split("/")[0], parse_qs(request.content.decode())["message"][0]))
            return httpx.Response(200, json={"id": f"rep{len(self.replies)}"})
        if request.method == "POST" and path.endswith("/comments"):
            self.fb_replies.append((path.split("/")[0], parse_qs(request.content.decode())["message"][0]))
            return httpx.Response(200, json={"id": f"fbrep{len(self.fb_replies)}"})
        return httpx.Response(404, json={"error": {"message": "nope", "code": 100}})


def make(meta, dry_run=False, llm=None, **cfg):
    db = FakeDb()
    conf = EngageConfig(enabled=True, dry_run=dry_run, page_id="PAGE", ig_business_id="IG", instagram_enabled=cfg.pop("instagram_enabled", True),
                        page_token="tok", site_url="https://site.test", landing_url="https://site.test/agent/rahul#enquire", **cfg)
    t = httpx.MockTransport(meta.handler)
    return EngageService(db, EngageGraph(conf, t), llm, conf, now=lambda: NOW, ig_graph=IgGraph(conf, t)), db


def rows(db):
    return db.get_collection("engage_comments").docs


async def test_interested_comment_is_answered_with_link_in_bio_and_no_url():
    meta = Meta([media([ig_comment("c1", "INTERESTED")])])
    svc, db = make(meta)
    assert await svc.run_once() == {"replied": 1}
    assert meta.replies == [("c1", meta.replies[0][1])]
    text = meta.replies[0][1]
    assert "link in our bio" in text and "http" not in text and "site.test" not in text
    doc = rows(db)[0]
    assert doc["_id"] == "instagram:c1" and doc["comment_id"] == "c1" and doc["channel"] == "instagram" and doc["status"] == "replied"
    assert doc["permalink"] == "https://instagram.com/p/M1/" and doc["reply_id"] == "rep1"
    assert await svc.run_once() == {}  # deduped


async def test_own_account_comments_and_already_replied_comments_are_ignored():
    meta = Meta([media([ig_comment("c1", "INTERESTED", user=ME.upper()),
                        ig_comment("c2", "INTERESTED", user="amit", replies=[{"id": "r", "username": ME}]),
                        ig_comment("c3", "INTERESTED", user="amit", replies=[{"id": "r", "username": "someone_else"}])])])
    svc, db = make(meta)
    assert await svc.run_once() == {"ignored": 2, "replied": 1}
    assert [r[0] for r in meta.replies] == ["c3"]
    assert [d["status"] for d in rows(db)] == ["ignored", "ignored", "replied"]


async def test_spam_is_ignored_and_a_question_is_queued_for_a_person():
    llm = NoAnswerLLM()
    meta = Meta([media([ig_comment("c1", "Earn money click here", user="bot"), ig_comment("c2", "Which school is nearby?", user="amit")])])
    svc, db = make(meta, llm=llm)
    assert await svc.run_once() == {"ignored": 1, "replied": 1}
    by = {d["comment_id"]: d for d in rows(db)}
    assert by["c1"]["status"] == "ignored" and by["c1"]["intent"] == "spam"
    assert by["c2"]["needs_human"] and "link in our bio" in by["c2"]["reply"] and "http" not in by["c2"]["reply"]
    assert [r[0] for r in meta.replies] == ["c2"]




@pytest.mark.parametrize("text", ["DM me the price", "@kharadi_prop is this available", "pls dm"])
async def test_mentions_and_dm_requests_are_queued_without_a_public_reply(text):
    d = await decide(text, "amit", "facts", "https://x", None, channel="instagram", handle=ME)
    if text == "pls dm":  # "dm" alone is an interest keyword, answered with the bio link
        assert d.intent != "spam"
        return
    assert d.needs_human and d.reply is None and d.reason == "mention or DM request"


async def test_dm_me_comment_goes_to_the_queue_through_the_service():
    meta = Meta([media([ig_comment("c1", "DM me details", user="amit")])])
    svc, db = make(meta)
    assert await svc.run_once() == {"needs_human": 1} and meta.replies == []


async def test_dry_run_records_but_posts_nothing():
    meta = Meta([media([ig_comment("c1", "INTERESTED")])])
    svc, db = make(meta, dry_run=True)
    assert await svc.run_once() == {"dry_run": 1} and meta.replies == [] and "link in our bio" in rows(db)[0]["reply"]


async def test_person_and_hourly_caps_apply_on_instagram():
    meta = Meta([media([ig_comment(f"c{i}", "INTERESTED", user="same") for i in range(3)])])
    svc, db = make(meta)
    assert await svc.run_once() == {"replied": 2, "capped": 1}
    meta2 = Meta([media([ig_comment(f"c{i}", "INTERESTED", user=f"u{i}") for i in range(5)])])
    svc2, db2 = make(meta2, max_replies_per_hour=2)
    assert await svc2.run_once() == {"replied": 2} and len(meta2.replies) == 2


async def test_facebook_behaviour_is_unchanged_and_both_channels_share_the_hourly_cap():
    fb_post = {"id": "PAGE_P1", "message": "hello", "comments": {"data": [{"id": "C1", "message": "INTERESTED", "from": {"id": "u1", "name": "Priya Sharma"}, "created_time": WHEN}]}}
    meta = Meta([media([ig_comment("c1", "INTERESTED")])], [fb_post])
    svc, db = make(meta)
    assert await svc.run_once() == {"replied": 2}
    fb = [d for d in rows(db) if d["channel"] == "facebook"][0]
    assert fb["_id"] == "C1" and "site.test/agent/rahul" in meta.fb_replies[0][1] and "link in our bio" not in meta.fb_replies[0][1]
    meta_b = Meta([media([ig_comment("c1", "INTERESTED")])], [fb_post])
    svc_b, db_b = make(meta_b, max_replies_per_hour=1)
    assert await svc_b.run_once() == {"replied": 1} and len(meta_b.fb_replies) == 1 and meta_b.replies == []


async def test_same_id_on_both_platforms_does_not_collide():
    fb_post = {"id": "PAGE_P1", "message": "hello", "comments": {"data": [{"id": "77", "message": "INTERESTED", "from": {"id": "u1", "name": "A"}, "created_time": WHEN}]}}
    meta = Meta([media([ig_comment("77", "INTERESTED")])], [fb_post])
    svc, db = make(meta)
    assert await svc.run_once() == {"replied": 2} and sorted(d["_id"] for d in rows(db)) == ["77", "instagram:77"]


async def test_only_ids_work_per_channel():
    fb_post = {"id": "PAGE_P1", "message": "hello", "comments": {"data": [{"id": "C1", "message": "INTERESTED", "from": {"id": "u1", "name": "A"}, "created_time": WHEN}]}}
    meta = Meta([media([ig_comment("c1", "INTERESTED", user="a"), ig_comment("c2", "INTERESTED", user="b")])], [fb_post])
    svc, db = make(meta)
    assert await svc.run_once(only_ids={"c2"}) == {"replied": 1} and [r[0] for r in meta.replies] == ["c2"] and meta.fb_replies == []
    assert await svc.run_once(only_ids={"C1"}) == {"replied": 1} and len(meta.fb_replies) == 1 and len(meta.replies) == 1
    assert await svc.run_once(only_ids={"instagram:c1"}) == {"replied": 1}


async def test_instagram_disabled_never_touches_instagram():
    meta = Meta([media([ig_comment("c1", "INTERESTED")])])
    svc, db = make(meta, instagram_enabled=False)
    await svc.run_once()
    assert not any(p.startswith("IG") for _, p in meta.calls) and rows(db) == []


async def test_status_is_recorded_per_channel_and_instagram_failure_does_not_stop_facebook():
    def handler(request):
        if "IG" in request.url.path:
            return httpx.Response(400, json={"error": {"message": "token invalid", "code": 190}})
        return httpx.Response(200, json={"data": []})
    db = FakeDb()
    conf = EngageConfig(enabled=True, dry_run=False, page_id="PAGE", ig_business_id="IG", instagram_enabled=True, page_token="tok")
    t = httpx.MockTransport(handler)
    svc = EngageService(db, EngageGraph(conf, t), None, conf, now=lambda: NOW, ig_graph=IgGraph(conf, t))
    assert await svc.run_once() == {"error": 1}
    st = {d["_id"]: d for d in db.get_collection("engage_status").docs}
    assert st["facebook"]["ok"] is True and st["instagram"]["ok"] is False and st["instagram"]["reconnect"] is True


async def test_config_defaults_instagram_on_only_when_the_account_id_is_set(monkeypatch):
    for k in ("META_IG_BUSINESS_ID", "ENGAGE_INSTAGRAM_ENABLED"):
        monkeypatch.delenv(k, raising=False)
    assert load().instagram_enabled is False
    monkeypatch.setenv("META_IG_BUSINESS_ID", "123")
    assert load().instagram_enabled is True
    monkeypatch.setenv("ENGAGE_INSTAGRAM_ENABLED", "false")
    assert load().instagram_enabled is False
