import calendar
import hashlib
import hmac
import json
from datetime import datetime, timedelta

import httpx

from app.modules.whatsapp.config import WhatsAppConfig
from app.modules.whatsapp.graph import WhatsAppGraph
from app.modules.whatsapp.service import WhatsAppService

from ..fakes import FakeDb

TOKEN = "EAAGtesttokenSECRET1234567890abcdef"
SECRET = "app-secret-0123456789"
VERIFY = "verify-token-xyz"
PID = "106540352242922"
BUYER = "919876543210"
NOW = datetime(2026, 10, 1, 10, 0, 0)

LISTING = {"_id": "L1", "agent_id": "AGENT2", "title": "2 BHK in Kharadi", "transaction": "sale", "property_type": "apartment", "price_inr": 8_500_000,
           "city": "Pune", "locality": "Kharadi", "bhk": 2, "carpet_sqft": 1100, "status": "live", "visibility": "public"}


def epoch(dt: datetime) -> str:
    return str(calendar.timegm(dt.utctimetuple()))


def cfg(**kw) -> WhatsAppConfig:
    base = dict(enabled=True, dry_run=True, phone_number_id=PID, owner_agent_id="OWNER", access_token=TOKEN, verify_token=VERIFY, app_secret=SECRET)
    base.update(kw)
    return WhatsAppConfig(**base)


def message(text="Hi", mid="wamid.1", wa=BUYER, ts=None, mtype="text", extra=None):
    m = {"from": wa, "id": mid, "timestamp": epoch(ts or NOW), "type": mtype}
    if mtype == "text":
        m["text"] = {"body": text}
    m.update(extra or {})
    return m


def value(msgs, pid=PID, name="Priya Sharma", wa=BUYER):
    return {"messaging_product": "whatsapp", "metadata": {"display_phone_number": "15550783881", "phone_number_id": pid},
            "contacts": [{"profile": {"name": name}, "wa_id": wa}], "messages": msgs}


def payload(msgs, **kw) -> dict:
    return {"object": "whatsapp_business_account", "entry": [{"id": "WABA", "changes": [{"field": "messages", "value": value(msgs, **kw)}]}]}


def sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def body_of(p: dict) -> bytes:
    return json.dumps(p).encode()


class GraphRecorder:
    """httpx.MockTransport handler: records every request, answers like the Cloud API (or with `fail`)."""

    def __init__(self, fail: dict = None, status: int = 200, raise_exc: Exception = None):
        self.requests, self.fail, self.status, self.raise_exc = [], fail, status, raise_exc

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.raise_exc:
            raise self.raise_exc
        if self.fail:
            return httpx.Response(self.status, json=self.fail)
        body = json.loads(request.content or b"{}") if request.method == "POST" else {}
        if body.get("status") == "read":
            return httpx.Response(200, json={"success": True})
        return httpx.Response(200, json={"messaging_product": "whatsapp", "contacts": [{"wa_id": body.get("to")}],
                                         "messages": [{"id": f"wamid.out{len(self.requests)}"}]})

    def sends(self):
        return [json.loads(r.content) for r in self.requests if r.method == "POST" and json.loads(r.content).get("type") == "text"]


def make(c: WhatsAppConfig = None, db=None, recorder: GraphRecorder = None, llm=None, now=None):
    c = c or cfg()
    db = db if db is not None else FakeDb()
    rec = recorder or GraphRecorder()
    graph = WhatsAppGraph(c, transport=httpx.MockTransport(rec))
    clock = {"now": now or NOW}
    svc = WhatsAppService(db, c, graph, llm, now=lambda: clock["now"])
    return svc, db, rec, clock


async def say(svc, text, mid=None, ts=None, **kw):
    """One inbound text through claim + handle, as the webhook does."""
    say.n = getattr(say, "n", 0) + 1
    m = message(text, mid or f"wamid.t{say.n}", ts=ts or svc.now(), **kw)
    v = value([m])
    assert await svc.claim(m, v)
    return await svc.handle(m, v)


def later(clock, **delta):
    clock["now"] = clock["now"] + timedelta(**delta)
