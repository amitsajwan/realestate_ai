"""Phone alerts (app/modules/notifications/push.py): which notifications ring, what the lock screen shows, who gets them, and the
phones that stop getting them."""
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.notifications import push, router as notif_router, service, webpush
from app.modules.notifications.config import PushConfig

from ..fakes import FakeDb

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 11, 3, 9, 0)
PUBLIC, PRIVATE = webpush.generate_keys()
CFG = PushConfig(public_key=PUBLIC, private_key=PRIVATE)
UA_PUBLIC = "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4"
AUTH = "BTBZMqHH6r4Tts7J_aSIgg"


def phone(n: int, host: str = "fcm.googleapis.com") -> dict:
    return {"endpoint": f"https://{host}/fcm/send/phone-{n}", "keys": {"p256dh": UA_PUBLIC, "auth": AUTH}}


class Outbox:
    """Stands in for the push services: records each POST and answers with the status set for its endpoint."""
    def __init__(self, answers=None):
        self.sent, self.answers = [], answers or {}

    async def __call__(self, url, headers, body):
        self.sent.append((url, headers, body))
        return self.answers.get(url, 201)


async def test_a_new_lead_rings_every_phone_the_agent_turned_alerts_on_and_no_one_elses():
    db = FakeDb()
    await push.save(db, "A1", phone(1), "Chrome Android", NOW)
    await push.save(db, "A1", phone(2, "web.push.apple.com"), "Safari iPhone", NOW)
    await push.save(db, "B2", phone(3), "Chrome Android", NOW)
    out = Outbox()
    assert await push.alert(db, "A1", "new_lead", "Rohit enquired on your website", {"lead_id": "L9"}, NOW, CFG, out) == (2, 0)
    assert sorted(u for u, _, _ in out.sent) == [phone(1)["endpoint"], phone(2, "web.push.apple.com")["endpoint"]]


async def test_quiet_notifications_wait_on_the_studio_badge_and_nothing_rings_without_keys():
    db = FakeDb()
    await push.save(db, "A1", phone(1), "", NOW)
    out = Outbox()
    assert await push.alert(db, "A1", "seo_week", "Your SEO week", {}, NOW, CFG, out) == (0, 0)
    assert await push.alert(db, "A1", "new_lead", "Rohit enquired", {}, NOW, PushConfig(), out) == (0, 0)
    assert out.sent == []


async def test_the_lock_screen_shows_the_alert_never_a_phone_number_and_a_tap_opens_the_lead():
    msg = push.message("new_lead", 'Rohit enquired on your website: "call me on 98220 12345 or +919890123456"', {"lead_id": "L9",
                       "screen": "/studio/leads/L9"})
    assert msg["title"] == "New lead"
    assert "98220" not in msg["body"] and "9890123456" not in msg["body"] and msg["body"].count("[number]") == 2
    assert msg["url"] == "/studio/leads/L9" and msg["tag"] == "new_lead:L9"
    assert push.message("whatsapp_reply", "x", {"conversation_id": "C1"})["url"] == "/studio/inbox"
    assert push.message("lead_waiting", "x", {"lead_id": "L2"})["url"] == "/studio/leads/L2"
    assert push.message("invite_request", "x", {"screen": "https://evil.example/"})["url"] == "/studio"   # only Studio screens
    assert len(push.message("new_lead", "word " * 100, {})["body"]) <= push.MAX_BODY


async def test_a_phone_the_push_service_forgot_is_removed_and_a_failing_one_is_kept():
    db = FakeDb()
    for n in (1, 2, 3):
        await push.save(db, "A1", phone(n), "", NOW)
    out = Outbox({phone(1)["endpoint"]: 410, phone(2)["endpoint"]: 500})
    assert await push.alert(db, "A1", "new_lead", "Rohit", {}, NOW, CFG, out) == (1, 1)
    left = {d["_id"]: d for d in db.get_collection("push_subscriptions").docs}
    assert phone(1)["endpoint"] not in left
    assert left[phone(2)["endpoint"]]["last_status"] == 500 and left[phone(3)["endpoint"]]["last_status"] == 201


async def test_a_push_service_that_hangs_or_breaks_never_stops_the_alert():
    db = FakeDb()
    await push.save(db, "A1", phone(1), "", NOW)

    async def broken(url, headers, body):
        raise RuntimeError("connection reset")
    assert await push.alert(db, "A1", "new_lead", "Rohit", {}, NOW, CFG, broken) == (0, 0)


async def test_only_browser_push_services_are_accepted_so_our_server_never_posts_to_an_address_of_our_own():
    for ok in ("https://fcm.googleapis.com/fcm/send/x", "https://jmt17.google.com/fcm/send/x", "https://updates.push.services.mozilla.com/wpush/v2/x",
               "https://web.push.apple.com/Q", "https://wns2-par02p.notify.windows.com/w/?token=x"):
        assert push.push_endpoint_ok(ok), ok
    for bad in ("http://fcm.googleapis.com/x", "https://backend:8000/api", "https://169.254.169.254/latest", "https://evilfcm.googleapis.com.example/x",
                "https://fcm.googleapis.com.evil.example/x", "https://metadata.google.internal/x", "https://10.0.0.5/x",
                "https://google.com.evil.example/x", "https://user:pw@fcm.googleapis.com/x", "https://fcm.googleapis.com:8443/x", "not a url"):
        assert not push.push_endpoint_ok(bad), bad
    with pytest.raises(ValueError):
        await push.save(FakeDb(), "A1", {"endpoint": "https://backend:8000/x", "keys": {"p256dh": UA_PUBLIC, "auth": AUTH}}, "", NOW)


async def test_the_same_phone_subscribing_again_is_one_row_and_follows_the_agent_signed_in():
    db = FakeDb()
    await push.save(db, "A1", phone(1), "", NOW)
    await push.save(db, "B2", phone(1), "", NOW)
    rows = db.get_collection("push_subscriptions").docs
    assert len(rows) == 1 and rows[0]["agent_id"] == "B2"
    assert await push.remove(db, "A1", phone(1)["endpoint"]) is False    # not A1's any more
    assert await push.remove(db, "B2", phone(1)["endpoint"]) is True


async def test_an_agent_keeps_alerts_on_their_latest_phones_only():
    db = FakeDb()
    for n in range(push.MAX_PER_AGENT + 2):
        await push.save(db, "A1", phone(n), "", datetime(2026, 11, 3, 9, n))
    kept = {d["_id"] for d in db.get_collection("push_subscriptions").docs}
    assert len(kept) == push.MAX_PER_AGENT and phone(0)["endpoint"] not in kept and phone(11)["endpoint"] in kept


async def test_notify_saves_the_alert_first_and_then_rings_the_phone(monkeypatch):
    db = FakeDb()
    await push.save(db, "A1", phone(1), "", NOW)
    out = Outbox()
    monkeypatch.setattr(push, "load", lambda: CFG)
    monkeypatch.setattr(push, "_post", out)
    await service.notify(db, "A1", "new_lead", "Rohit enquired on your website", {"lead_id": "L9"}, NOW)
    assert len(db.get_collection("notifications").docs) == 1 and len(out.sent) == 1


async def test_notify_keeps_the_alert_when_the_push_breaks(monkeypatch):
    db = FakeDb()

    async def boom(*a, **k):
        raise RuntimeError("push down")
    monkeypatch.setattr(push, "alert", boom)
    assert await service.notify(db, "A1", "new_lead", "Rohit", {}, NOW)
    assert len(db.get_collection("notifications").docs) == 1


def _client(db, monkeypatch, cfg=CFG, agent="A1"):
    monkeypatch.setattr(notif_router, "get_database", lambda: db)
    monkeypatch.setattr(notif_router, "load_push", lambda: cfg)
    app = FastAPI()
    app.include_router(notif_router.router, prefix="/notifications")
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id=agent)
    return TestClient(app)


def test_studio_learns_whether_alerts_can_be_turned_on_and_the_key_to_use(monkeypatch):
    db = FakeDb()
    assert _client(db, monkeypatch).get("/notifications/push").json() == {"enabled": True, "public_key": PUBLIC, "phones": 0}
    assert _client(db, monkeypatch, PushConfig()).get("/notifications/push").json() == {"enabled": False, "public_key": None, "phones": 0}


def test_a_phone_turns_alerts_on_and_off_through_the_api(monkeypatch):
    db = FakeDb()
    c = _client(db, monkeypatch)
    assert c.put("/notifications/push/subscription", json=phone(1), headers={"User-Agent": "Chrome Android"}).json() == {"on": True}
    assert c.get("/notifications/push").json()["phones"] == 1
    assert c.put("/notifications/push/subscription", json={**phone(1), "endpoint": "https://backend:8000/x"}).status_code == 400
    assert c.request("DELETE", "/notifications/push/subscription", json={"endpoint": phone(1)["endpoint"]}).json() == {"on": False, "removed": True}
    assert _client(db, monkeypatch, PushConfig()).put("/notifications/push/subscription", json=phone(1)).status_code == 409
