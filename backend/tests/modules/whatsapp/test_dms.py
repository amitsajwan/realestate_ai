"""Messenger and Instagram DM assistant: parsing, leads (and the comment assistant's leads), the number, a person taking over, STOP, the
24-hour window, sending, and the webhook. No network."""
import json
from datetime import timedelta

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.whatsapp import dm_config, dm_router
from app.modules.whatsapp.dm_config import DmConfig
from app.modules.whatsapp.dm_graph import BOT_TAG, DmGraph
from app.modules.whatsapp.dms import DmService, parse

from ..fakes import FakeDb
from .helpers import NOW, SECRET, VERIFY, body_of, epoch, later, sign

pytestmark = pytest.mark.asyncio

PAGE, IG, PSID, IGSID = "P100", "IG200", "psid-555", "igsid-777"
TOKEN = "EAAPagetokenSECRET1234567890abcdef"


def cfg(**kw) -> DmConfig:
    base = dict(enabled=True, dry_run=True, page_id=PAGE, ig_id=IG, owner_agent_id="OWNER", page_token=TOKEN, verify_token=VERIFY,
                app_secret=SECRET)
    base.update(kw)
    return DmConfig(**base)


class Recorder:
    def __init__(self, fail=None):
        self.requests, self.fail = [], fail

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.fail:
            return httpx.Response(400, json=self.fail)
        return httpx.Response(200, json={"recipient_id": "x", "message_id": f"m_out{len(self.requests)}"})


def make(c=None, db=None, rec=None):
    c = c or cfg()
    db = db if db is not None else FakeDb()
    rec = rec or Recorder()
    clock = {"now": NOW}
    svc = DmService(db, c, DmGraph(c, transport=httpx.MockTransport(rec)), None, now=lambda: clock["now"])
    return svc, db, rec, clock


def event(text="Hi", mid=None, sender=PSID, recipient=PAGE, ts=None, echo=False, tag=None, attachments=None):
    event.n = getattr(event, "n", 0) + 1
    msg = {"mid": mid or f"m_{event.n}"}
    if text is not None:
        msg["text"] = text
    if echo:
        msg["is_echo"] = True
    if tag:
        msg["metadata"] = tag
    if attachments:
        msg["attachments"] = attachments
    return {"sender": {"id": sender}, "recipient": {"id": recipient}, "timestamp": int(epoch(ts or NOW)) * 1000, "message": msg}


async def say(svc, text, platform="messenger", sender=PSID, **kw):
    m = parse(event(text, sender=sender, ts=svc.now(), **kw))
    assert await svc.claim(platform, m)
    return await svc.handle(platform, m)


def leads(db):
    return db.get_collection("contacts").docs


async def conv(db, platform="messenger", sender=PSID):
    return await db.get_collection("dm_conversations").find_one({"_id": f"{platform}:{sender}"})


# ---- config and parsing ---------------------------------------------------------------------------------------------
def test_config_is_off_and_dry_by_default_and_shares_the_apps_secret(monkeypatch):
    for k in ("MESSENGER_ENABLED", "MESSENGER_DRY_RUN", "MESSENGER_APP_SECRET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SECRET)
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", TOKEN)
    c = dm_config.load()
    assert c.enabled is False and c.dry_run is True and c.app_secret == SECRET and c.human_pause_hours == 12
    assert TOKEN not in repr(c) and SECRET not in repr(c)
    monkeypatch.setenv("MESSENGER_HUMAN_PAUSE_HOURS", "lots")
    assert dm_config.load().human_pause_hours == 12


def test_parse_reads_messages_echoes_buttons_and_attachments():
    m = parse(event("Hello"))
    assert m["kind"] == "message" and m["sender"] == PSID and m["text"] == "Hello" and m["ts"] == NOW
    assert parse(event("x", echo=True, tag=BOT_TAG))["kind"] == "echo"
    assert parse(event(None, attachments=[{"type": "image"}]))["media"] is True
    pb = parse({"sender": {"id": PSID}, "recipient": {"id": PAGE}, "timestamp": 0, "postback": {"mid": "m_pb", "title": "Prices?"}})
    assert pb["kind"] == "message" and pb["text"] == "Prices?"
    assert parse({"sender": {"id": PSID}, "read": {"watermark": 1}})["kind"] == "other"


async def test_claim_is_once_and_never_for_our_own_account():
    svc, _, _, _ = make()
    m = parse(event("Hi", mid="m_once"))
    assert await svc.claim("messenger", m) and not await svc.claim("messenger", m)
    assert not await svc.claim("messenger", parse(event("Hi", sender=PAGE)))
    assert not await svc.claim("instagram", parse(event("Hi", sender=IG)))


# ---- answering and leads -----------------------------------------------------------------------------------------------
async def test_a_first_message_gets_an_answer_a_lead_and_a_notification():
    svc, db, rec, _ = make()
    r = await say(svc, "Hi, looking for a 2 BHK in Kharadi")
    assert r["status"] == "answered" and r["send_status"] == "dry_run" and r["agent_id"] == "OWNER"
    assert "STOP" in r["reply"] and rec.requests == []  # dry run: nothing sent
    (lead,) = leads(db)
    assert lead["phone"] == "" and lead["source"] == "facebook" and lead["dm"]["id"] == PSID and lead["consent"] is None
    assert lead["requirement"]["bhk"] == 2 and "Kharadi" in lead["requirement"]["localities"]
    (n,) = db.get_collection("notifications").docs
    assert n["kind"] == "new_dm_lead" and "Messenger" in n["summary"]
    r2 = await say(svc, "What about Wagholi?")
    assert "STOP" not in r2["reply"] and len(leads(db)) == 1  # the notice once; one lead


async def test_a_commenter_the_comment_assistant_messaged_keeps_their_lead_and_agent():
    svc, db, _, _ = make()
    await db.get_collection("contacts").insert_one({"_id": "C1", "agent_id": "AGENT2", "name": "Asha", "phone": "", "anon_ids": ["facebook:u1"],
                                                    "dm": {"channel": "facebook", "id": PSID}, "stage": "new", "requirement": None})
    r = await say(svc, "Yes please, 3 BHK")
    assert r["agent_id"] == "AGENT2" and r["lead_id"] == "C1"
    (lead,) = leads(db)
    assert lead["requirement"]["bhk"] == 3 and f"messenger_dm:{PSID}" in lead["anon_ids"]


async def test_instagram_dms_are_their_own_channel():
    svc, db, _, _ = make()
    await say(svc, "Hi", platform="instagram", sender=IGSID)
    (lead,) = leads(db)
    assert lead["source"] == "instagram" and lead["name"] == "Instagram buyer" and (await conv(db, "instagram", IGSID))


async def test_a_shared_number_goes_on_the_lead_with_consent():
    svc, db, _, _ = make()
    await say(svc, "Hi")
    await say(svc, "My number is 98765 43210")
    if not leads(db)[0]["phone"]:  # the engine confirms the number before taking it
        await say(svc, "Yes")
    (lead,) = leads(db)
    assert lead["phone"] == "+919876543210" and "Messenger" in lead["consent"]["basis"] and lead["score_base"] >= 25


async def test_a_shared_number_joins_the_agents_existing_lead_with_that_number():
    svc, db, _, _ = make()
    await db.get_collection("contacts").insert_one({"_id": "W1", "agent_id": "OWNER", "name": "Ravi", "phone": "+919876543210",
                                                    "anon_ids": ["whatsapp:919876543210"], "stage": "new", "requirement": None})
    await say(svc, "Hi")
    await say(svc, "My number is 98765 43210")
    if len(leads(db)) == 2:
        await say(svc, "Yes")
    (lead,) = leads(db)
    assert lead["_id"] == "W1" and lead["dm"]["id"] == PSID


# ---- a person takes over ----------------------------------------------------------------------------------------------------
async def test_a_person_replying_from_the_page_inbox_pauses_the_assistant_in_that_chat():
    svc, db, _, clock = make()
    await say(svc, "Hi")
    paused = await svc.echo("messenger", parse(event("Hi Priya, Rahul here. When can you visit?", sender=PAGE, recipient=PSID, echo=True)))
    assert paused
    r = await say(svc, "Saturday works, budget 90L")
    assert r["status"] == "human" and r["reply"] is None
    assert leads(db)[0]["requirement"]["budget_max_inr"]  # the lead still learns from the chat
    later(clock, hours=13)
    assert (await say(svc, "Any update?"))["status"] == "answered"


async def test_our_own_echoes_never_pause_the_assistant():
    svc, db, _, _ = make()
    r = await say(svc, "Hi")
    assert not await svc.echo("messenger", parse(event(r["reply"], sender=PAGE, recipient=PSID, echo=True, tag=BOT_TAG)))
    assert not await svc.echo("messenger", parse(event(r["reply"], sender=PAGE, recipient=PSID, echo=True)))  # same text, just sent
    assert (await conv(db))["human_until"] is None


# ---- STOP, window, sending --------------------------------------------------------------------------------------------------
async def test_stop_and_start():
    svc, db, _, _ = make()
    await say(svc, "Hi")
    assert (await say(svc, "STOP"))["status"] == "stopped"
    assert leads(db)[0]["dm"]["opted_out"] is True and leads(db)[0].get("consent") is None
    assert (await say(svc, "hello?"))["status"] == "opted_out"
    assert (await say(svc, "START"))["status"] == "restarted"


async def test_no_reply_outside_the_24_hour_window():
    svc, db, _, clock = make()
    m = parse(event("Hi", ts=NOW - timedelta(hours=30)))
    assert await svc.claim("messenger", m)
    r = await svc.handle("messenger", m)
    assert r["send_status"] == "refused"


async def test_live_send_uses_the_send_api_with_the_bot_tag_and_never_puts_the_token_in_the_url():
    svc, db, rec, _ = make(cfg(dry_run=False))
    r = await say(svc, "Hi")
    assert r["send_status"] == "sent"
    (req,) = rec.requests
    assert str(req.url) == f"https://graph.facebook.com/v23.0/{''.join(c for c in PAGE if c.isdigit())}/messages"
    assert TOKEN not in str(req.url) and req.headers["authorization"] == f"Bearer {TOKEN}"
    body = json.loads(req.content)
    assert body["recipient"] == {"id": PSID} and body["messaging_type"] == "RESPONSE" and body["message"]["metadata"] == BOT_TAG
    out = [d for d in db.get_collection("dm_messages").docs if d["direction"] == "out"]
    assert out[0]["message_id"] == "m_out1" and out[0]["status"] == "sent"  # so its echo is recognised as ours
    assert not await svc.echo("instagram", parse(event("anything", mid="m_out1", sender=IG, recipient=PSID, echo=True)))


async def test_an_echo_that_beats_the_send_call_is_still_ours():
    """Instagram may echo before the Send API call returns: the reply is saved before sending, so its text is recognised."""
    svc, db, _, _ = make(cfg(dry_run=False))
    seen = {}

    class Racing(DmGraph):
        async def send_text(self, recipient_id, text):
            seen["paused"] = await svc.echo("instagram", parse(event(text, sender=IG, recipient=recipient_id, echo=True)))
            return "m_fast"

    svc.graph = Racing(svc.cfg)
    r = await say(svc, "Hi", platform="instagram", sender=PSID)
    assert r["send_status"] == "sent" and seen["paused"] is False


async def test_a_send_failure_is_stored_without_the_token():
    svc, db, _, _ = make(cfg(dry_run=False), rec=Recorder(fail={"error": {"code": 10, "message": f"bad token {TOKEN}"}}))
    r = await say(svc, "Hi")
    assert r["send_status"] == "failed"
    out = [d for d in db.get_collection("dm_messages").docs if d["direction"] == "out"][0]
    assert TOKEN not in out["error"]


# ---- webhook --------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("MESSENGER_ENABLED", "true")
    monkeypatch.setenv("MESSENGER_APP_SECRET", SECRET)
    monkeypatch.setenv("MESSENGER_VERIFY_TOKEN", VERIFY)
    monkeypatch.setenv("META_PAGE_ID", PAGE)
    monkeypatch.setenv("META_IG_BUSINESS_ID", IG)
    monkeypatch.setenv("MESSENGER_OWNER_AGENT_ID", "OWNER")
    db = FakeDb()
    app = FastAPI()
    app.include_router(dm_router.router, prefix="/messenger")
    app.dependency_overrides[dm_router.get_service_factory] = lambda: (lambda c=None: dm_router.build_service(c or cfg(), db=db, llm=None))
    return TestClient(app), db


def post(c, payload, secret=SECRET):
    b = body_of(payload)
    return c.post("/messenger/webhook", content=b, headers={"x-hub-signature-256": sign(b, secret), "content-type": "application/json"})


def test_webhook_verification(client):
    c, _ = client
    ok = c.get("/messenger/webhook", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY, "hub.challenge": "123"})
    assert ok.status_code == 200 and ok.text == "123"
    assert c.get("/messenger/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "no", "hub.challenge": "1"}).status_code == 403


def test_webhook_checks_the_signature_and_handles_page_and_instagram_messages(client):
    c, db = client
    page = {"object": "page", "entry": [{"id": PAGE, "messaging": [event("Hi from Messenger")]}]}
    assert post(c, page, secret="wrong").status_code == 403
    r = post(c, page)
    assert r.status_code == 200 and r.json()["processed"] == 1
    assert post(c, page).json()["processed"] == 0  # Meta's retry: handled once
    ig = {"object": "instagram", "entry": [{"id": IG, "messaging": [event("Hi from Instagram", sender=IGSID, recipient=IG)]}]}
    assert post(c, ig).json()["processed"] == 1
    assert {d["source"] for d in db.get_collection("contacts").docs} == {"facebook", "instagram"}
    assert post(c, {"object": "whatsapp_business_account", "entry": []}).json()["processed"] == 0


def test_webhook_does_nothing_while_disabled(client, monkeypatch):
    c, db = client
    monkeypatch.setenv("MESSENGER_ENABLED", "false")
    r = post(c, {"object": "page", "entry": [{"id": PAGE, "messaging": [event("Hi")]}]})
    assert r.json()["note"] == "disabled" and db.get_collection("contacts").docs == []
