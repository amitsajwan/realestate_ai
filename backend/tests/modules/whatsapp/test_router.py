"""Webhook verification, signatures, idempotency and the agent-scoped endpoints, through FastAPI's TestClient. No network."""
import logging
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.notifications import router as nr
from app.modules.notifications.service import NotificationService
from app.modules.whatsapp import router as wr
from app.modules.whatsapp.service import WhatsAppService

from ..fakes import FakeDb
from .helpers import NOW, SECRET, TOKEN, VERIFY, GraphRecorder, body_of, message, payload, sign

ENV = {"WHATSAPP_ENABLED": "true", "WHATSAPP_DRY_RUN": "true", "WHATSAPP_PHONE_NUMBER_ID": "106540352242922", "WHATSAPP_ACCESS_TOKEN": TOKEN,
       "WHATSAPP_VERIFY_TOKEN": VERIFY, "WHATSAPP_APP_SECRET": SECRET, "WHATSAPP_OWNER_AGENT_ID": "OWNER", "WHATSAPP_NUMBER_AGENTS": ""}


@pytest.fixture
def env(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    return monkeypatch


def client(db, user_id="OWNER"):
    app = FastAPI()
    app.include_router(wr.router, prefix="/whatsapp")
    app.include_router(nr.router, prefix="/notifications")
    import httpx
    from app.modules.whatsapp.graph import WhatsAppGraph
    rec = GraphRecorder()

    def factory(cfg=None):
        from app.modules.whatsapp.config import load
        c = cfg or load()
        return WhatsAppService(db, c, WhatsAppGraph(c, transport=httpx.MockTransport(rec)), None, now=lambda: NOW)

    app.dependency_overrides[wr.get_service_factory] = lambda: factory
    app.dependency_overrides[nr.get_service] = lambda: NotificationService(db, now=lambda: NOW)
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id=user_id)
    return TestClient(app), rec


def post(c, p, secret=SECRET, header=True):
    b = body_of(p)
    headers = {"Content-Type": "application/json"}
    if header:
        headers["X-Hub-Signature-256"] = sign(b, secret)
    return c.post("/whatsapp/webhook", content=b, headers=headers)


def test_webhook_verification(env):
    c, _ = client(FakeDb())
    ok = c.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY, "hub.challenge": "1158201444"})
    assert ok.status_code == 200 and ok.text == "1158201444"
    assert c.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "1"}).status_code == 403
    assert c.get("/whatsapp/webhook", params={"hub.mode": "unsubscribe", "hub.verify_token": VERIFY, "hub.challenge": "1"}).status_code == 403
    env.setenv("WHATSAPP_VERIFY_TOKEN", "")
    assert c.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "", "hub.challenge": "1"}).status_code == 403


def test_signature_good_bad_and_missing(env, caplog):
    caplog.set_level(logging.DEBUG)
    db = FakeDb()
    c, _ = client(db)
    p = payload([message("Hi", mid="wamid.sig")])
    assert post(c, p, secret="not-the-secret").status_code == 403
    assert post(c, p, header=False).status_code == 403
    assert db.get_collection("whatsapp_messages").docs == []
    r = post(c, p)
    assert r.status_code == 200 and r.json() == {"ok": True, "processed": 1}
    conv = db.get_collection("whatsapp_conversations").docs[0]
    assert conv["agent_id"] == "OWNER" and [m["role"] for m in conv["messages"]] == ["user", "bot"]
    assert TOKEN not in caplog.text and SECRET not in caplog.text


def test_tampered_body_is_rejected(env):
    c, _ = client(FakeDb())
    good = body_of(payload([message("Hi", mid="wamid.t")]))
    sig = sign(good)
    r = c.post("/whatsapp/webhook", content=good.replace(b"Hi", b"Yo"), headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})
    assert r.status_code == 403


def test_meta_retries_are_processed_once(env):
    db = FakeDb()
    c, _ = client(db)
    p = payload([message("Hi", mid="wamid.retry")])
    assert post(c, p).json()["processed"] == 1
    assert post(c, p).json()["processed"] == 0
    out = [m for m in db.get_collection("whatsapp_messages").docs if m["direction"] == "out"]
    assert len(out) == 1
    assert len(db.get_collection("whatsapp_conversations").docs[0]["messages"]) == 2


def test_disabled_answers_200_and_does_nothing(env):
    env.setenv("WHATSAPP_ENABLED", "false")
    db = FakeDb()
    c, rec = client(db)
    r = post(c, payload([message("Hi", mid="wamid.off")]))
    assert r.status_code == 200 and r.json()["processed"] == 0 and db.cols.get("whatsapp_messages") is None and rec.requests == []


def test_non_message_payloads_and_statuses_are_accepted(env):
    c, _ = client(FakeDb())
    assert post(c, {"object": "page", "entry": []}).json()["processed"] == 0
    st = {"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {"statuses": [{"id": "wamid.x", "status": "read"}]}}]}]}
    assert post(c, st).status_code == 200


def test_conversations_and_notifications_are_agent_scoped(env):
    db = FakeDb()
    c, _ = client(db)
    post(c, payload([message("Hi", mid="wamid.c1")]))
    convs = c.get("/whatsapp/conversations").json()
    assert len(convs) == 1 and convs[0]["channel"] == "whatsapp" and "9876543210" not in convs[0]["phone"]
    n = c.get("/notifications").json()
    assert n["unread"] == 1 and n["items"][0]["kind"] == "new_whatsapp_lead"
    other, _ = client(db, user_id="SOMEONE")
    assert other.get("/whatsapp/conversations").json() == []
    assert other.get("/notifications").json() == {"items": [], "unread": 0}
    assert other.post(f"/notifications/{n['items'][0]['id']}/read").status_code == 404
    assert c.post(f"/notifications/{n['items'][0]['id']}/read").json()["read"] is True
    assert c.get("/notifications?unread=true").json()["unread"] == 0


def test_agent_routes_require_auth():
    paths = {r.path: r for r in wr.router.routes}
    assert current_active_user in [d.call for d in paths["/conversations"].dependant.dependencies]
    for r in nr.router.routes:
        assert current_active_user in [d.call for d in r.dependant.dependencies]
