"""A new website form lead is told to its agent at once (tracking.capture_inquiry -> app/wiring.py -> notify), instead of only by the
2-hour waiting alert."""
from datetime import datetime

import pytest

from app import wiring
from app.modules.tracking import service as tracking_service

from .fakes import FakeDb
from .qual_helpers import inquiry, make

pytestmark = pytest.mark.asyncio


@pytest.fixture
def told(monkeypatch):
    calls = []

    async def on_new_lead(db, lead):
        calls.append(lead)
    monkeypatch.setattr(tracking_service, "_on_new_lead", on_new_lead)
    return calls


async def test_a_new_form_lead_is_told_to_its_agent_once(told):
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry(message="Is the 2 BHK still available?"))
    assert len(told) == 1 and told[0]["agent_id"] == "A1" and told[0]["name"] == "Amit Kumar" and told[0]["stage"] == "new"
    clock.advance(minutes=5)
    await svc.capture_inquiry(inquiry(message="Any update?"))   # the same buyer again: the same lead, not a new one
    assert len(told) == 1


async def test_a_website_chat_lead_is_left_to_the_chats_own_alert(told):
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry(channel="chat"))
    assert told == []


async def test_a_failing_alert_never_loses_the_enquiry(monkeypatch):
    async def broken(db, lead):
        raise RuntimeError("notifications down")
    monkeypatch.setattr(tracking_service, "_on_new_lead", broken)
    svc, db, _ = await make()
    assert (await svc.capture_inquiry(inquiry()))["new_lead"] is True
    assert len(db.get_collection("contacts").docs) == 1


async def test_the_alert_says_who_and_what_they_wrote_and_opens_the_lead():
    db = FakeDb()
    now = datetime(2026, 11, 3, 9, 0)
    await wiring._new_lead_alert(db, {"_id": "L9", "agent_id": "A1", "name": "Rohit", "created_at": now,
                                      "message": "Is the 2 BHK  in Baner\nstill available?"})
    n = db.get_collection("notifications").docs[0]
    assert n["agent_id"] == "A1" and n["kind"] == "new_lead"
    assert n["summary"] == 'Rohit enquired on your website: "Is the 2 BHK in Baner still available?"'
    assert n["ref"] == {"lead_id": "L9", "screen": "/studio/leads/L9"}
    await wiring._new_lead_alert(db, {"_id": "L10", "agent_id": "A1", "name": None, "message": None})
    assert db.get_collection("notifications").docs[1]["summary"] == "A buyer enquired on your website."
