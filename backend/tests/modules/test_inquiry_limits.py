"""Inquiry abuse protection (contract docs/contracts/activity.md section 3)."""
import asyncio
import copy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.tracking import router as tr
from app.modules.tracking.service import TrackingError

from .qual_helpers import inquiry, make

pytestmark = pytest.mark.asyncio

PHONES = ["9876543210", "9123456780", "9012345678", "9898989898", "9797979797", "9696969696", "9595959595"]


async def _blocked(svc, **kw):
    with pytest.raises(TrackingError) as exc:
        await svc.capture_inquiry(inquiry(**kw))
    assert exc.value.status_code == 429
    assert str(exc.value) == "Too many messages. Please try again later"


def _count(db, name):
    return len(db.get_collection(name).docs)


# ---- honeypot ------------------------------------------------------------------------------------
async def test_honeypot_returns_success_and_stores_nothing():
    svc, db, _ = await make()
    res = await svc.capture_inquiry(inquiry(website="http://spam.example"))
    assert res == {"received": True, "new_lead": False}
    for name in ("contacts", "events", "inquiry_log"):
        assert _count(db, name) == 0, name


async def test_honeypot_is_silent_even_without_consent_or_for_unknown_agents_and_never_rate_limited():
    svc, db, _ = await make()
    assert await svc.capture_inquiry(inquiry(website="x", consent=False)) == {"received": True, "new_lead": False}
    assert await svc.capture_inquiry(inquiry(website="x", agent_slug="nobody")) == {"received": True, "new_lead": False}
    for _ in range(10):
        assert (await svc.capture_inquiry(inquiry(website="x")))["new_lead"] is False
    assert _count(db, "contacts") == _count(db, "inquiry_log") == 0


async def test_blank_website_is_a_normal_inquiry():
    svc, db, _ = await make()
    for blank in (None, "", "   "):
        res = await svc.capture_inquiry(inquiry(website=blank, phone=PHONES[len(str(blank))]))
        assert res["received"] is True
    assert _count(db, "contacts") == 3


async def test_honeypot_does_not_consume_a_real_visitors_allowance():
    svc, _, _ = await make()
    for _ in range(4):
        await svc.capture_inquiry(inquiry(website="bot"))
    for i in range(3):
        await svc.capture_inquiry(inquiry(anon_id=f"anon-visitor-{i}"))
    await _blocked(svc, anon_id="anon-visitor-9")


# ---- per (agent, phone): 3 per rolling hour ----------------------------------------------------------
async def test_third_inquiry_ok_fourth_is_429_and_counts_updates_of_an_existing_lead():
    svc, db, clock = await make()
    assert (await svc.capture_inquiry(inquiry(anon_id="anon-visitor-1")))["new_lead"] is True
    assert (await svc.capture_inquiry(inquiry(anon_id="anon-visitor-2")))["new_lead"] is False
    assert (await svc.capture_inquiry(inquiry(anon_id="anon-visitor-3")))["new_lead"] is False  # 3rd still ok
    await _blocked(svc, anon_id="anon-visitor-4")
    assert _count(db, "contacts") == 1


async def test_rejected_attempt_stores_nothing_and_is_not_counted():
    svc, db, clock = await make()
    for i in range(3):
        await svc.capture_inquiry(inquiry(anon_id=f"anon-visitor-{i}"))
    events, log = _count(db, "events"), _count(db, "inquiry_log")
    before = copy.deepcopy(db.get_collection("contacts").docs[0])
    await _blocked(svc, anon_id="anon-visitor-7", message="new message")
    assert (_count(db, "events"), _count(db, "inquiry_log")) == (events, log)
    assert db.get_collection("contacts").docs[0] == before


async def test_phone_limit_is_per_agent_and_per_phone():
    svc, _, _ = await make()
    for i in range(3):
        await svc.capture_inquiry(inquiry(anon_id=f"anon-visitor-{i}"))
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-5", phone=PHONES[1]))            # other phone
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-6", agent_slug="priya", listing_id="L7"))  # other agent
    await _blocked(svc, anon_id="anon-visitor-8")


async def test_phone_limit_rolling_window_expires():
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-1"))       # t0
    clock.advance(minutes=10)
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-2"))       # t0+10
    clock.advance(minutes=20)
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-3"))       # t0+30
    await _blocked(svc, anon_id="anon-visitor-4")
    clock.advance(minutes=29, seconds=59)                              # t0+59:59, first still inside the hour
    await _blocked(svc, anon_id="anon-visitor-4")
    clock.advance(seconds=1)                                           # t0+60:00, first has expired
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-4"))
    await _blocked(svc, anon_id="anon-visitor-5")                      # window now holds t0+10, t0+30, t0+60
    clock.advance(minutes=10)                                          # t0+70: t0+10 expires
    await svc.capture_inquiry(inquiry(anon_id="anon-visitor-5"))


# ---- per anon_id: 5 per rolling hour -----------------------------------------------------------------
async def test_fifth_inquiry_from_one_visitor_ok_sixth_is_429():
    svc, db, _ = await make()
    for phone in PHONES[:5]:
        assert (await svc.capture_inquiry(inquiry(phone=phone)))["new_lead"] is True
    await _blocked(svc, phone=PHONES[5])
    assert _count(db, "contacts") == 5
    assert (await svc.capture_inquiry(inquiry(phone=PHONES[5], anon_id="anon-visitor-2")))["new_lead"] is True


async def test_anon_limit_rolling_window_expires():
    svc, _, clock = await make()
    for phone in PHONES[:5]:
        await svc.capture_inquiry(inquiry(phone=phone))
        clock.advance(minutes=1)
    await _blocked(svc, phone=PHONES[5])                # t0+5
    clock.advance(minutes=54, seconds=59)               # t0+59:59
    await _blocked(svc, phone=PHONES[5])
    clock.advance(seconds=1)                            # t0+60: the first attempt expired
    await svc.capture_inquiry(inquiry(phone=PHONES[5]))


async def test_missing_consent_is_not_counted():
    svc, db, _ = await make()
    for _ in range(5):
        with pytest.raises(TrackingError):
            await svc.capture_inquiry(inquiry(consent=False))
    assert _count(db, "inquiry_log") == 0
    await svc.capture_inquiry(inquiry())


# ---- router --------------------------------------------------------------------------------------------
BODY = {"agent_slug": "rahul", "anon_id": "anon-visitor-1", "name": "Amit Kumar", "phone": "9876543210",
        "consent": True, "listing_id": "L1", "source": "whatsapp"}


@pytest.fixture
def env():
    loop = asyncio.new_event_loop()
    svc, db, clock = loop.run_until_complete(make())
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(tr.public_router, prefix="/t")
    app.include_router(tr.inbox_router, prefix="/inbox")
    app.dependency_overrides[tr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    yield TestClient(app), db, clock
    loop.close()


def test_router_honeypot(env):
    c, db, _ = env
    r = c.post("/t/inquiry", json={**BODY, "website": "http://spam.example"})
    assert r.status_code == 200 and r.json() == {"received": True, "new_lead": False}
    assert _count(db, "contacts") == 0 and _count(db, "events") == 0


def test_router_limits_return_429_with_friendly_message(env):
    c, db, clock = env
    for i in range(3):
        assert c.post("/t/inquiry", json={**BODY, "anon_id": f"anon-visitor-{i}"}).status_code == 200
    r = c.post("/t/inquiry", json={**BODY, "anon_id": "anon-visitor-9"})
    assert r.status_code == 429 and r.json()["detail"] == "Too many messages. Please try again later"
    clock.advance(hours=1)
    assert c.post("/t/inquiry", json={**BODY, "anon_id": "anon-visitor-9"}).status_code == 200


def test_router_anon_limit(env):
    c, _, _ = env
    for phone in PHONES[:5]:
        assert c.post("/t/inquiry", json={**BODY, "phone": phone}).status_code == 200
    assert c.post("/t/inquiry", json={**BODY, "phone": PHONES[5]}).status_code == 429
