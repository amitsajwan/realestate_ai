from datetime import datetime, timedelta

import pytest

from app.modules.tracking import scoring
from app.modules.tracking.schemas import EventIn, InquiryIn, StageUpdate
from app.modules.tracking.service import TrackingError, TrackingService, is_bot

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio
BROWSER = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile Safari/604.1"


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 12, 0, 0)

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


async def make():
    db, clock = FakeDb(), Clock()
    profiles = db.get_collection("agent_public_profiles")
    await profiles.insert_one({"slug": "rahul", "agent_id": "A1", "is_public": True})
    await profiles.insert_one({"slug": "priya", "agent_id": "A2", "is_public": True})
    return TrackingService(db, now=clock), db, clock


def ev(type_, listing="L1", anon="anon-visitor-1", slug="rahul", **kw):
    return EventIn(agent_slug=slug, anon_id=anon, type=type_, listing_id=listing, **kw)


def inquiry(**kw):
    base = dict(agent_slug="rahul", anon_id="anon-visitor-1", name="Amit", phone="98765 43210",
                message="Is 2BHK available?", consent=True, listing_id="L1", source="whatsapp")
    base.update(kw)
    return InquiryIn(**base)


def test_bot_detection():
    assert is_bot(None) and is_bot("Googlebot/2.1") and is_bot("WhatsApp/2.23 A")
    assert not is_bot(BROWSER)


def test_scoring_rules():
    assert scoring.event_points("listing_view", 0) == 1
    assert scoring.event_points("listing_view", 1) == 3  # repeat view bonus
    assert scoring.event_points("listing_view", 5) == 0  # capped
    assert scoring.event_points("inquiry") == 25
    now = datetime(2026, 1, 20)
    assert scoring.score(40, now - timedelta(days=1), now) == 40
    assert scoring.score(40, now - timedelta(days=10), now) == 28
    assert scoring.score(40, now - timedelta(days=30), now) == 16
    assert [scoring.temperature(v) for v in (0, 15, 35)] == ["cold", "warm", "hot"]


async def test_events_ignored_for_bots_and_unknown_agents():
    svc, db, _ = await make()
    assert await svc.track_event(ev("listing_view"), "Googlebot") is False
    assert await svc.track_event(ev("listing_view"), BROWSER) is True
    with pytest.raises(TrackingError) as e:
        await svc.track_event(ev("listing_view", slug="ghost"), BROWSER)
    assert e.value.status_code == 404
    assert await db.get_collection("events").count_documents({}) == 1


async def test_event_rate_limit_per_visitor():
    svc, db, _ = await make()
    for _ in range(60):
        assert await svc.track_event(ev("page_view", listing=None), BROWSER)
    assert await svc.track_event(ev("page_view", listing=None), BROWSER) is False


async def test_anonymous_history_becomes_lead_timeline_and_score():
    svc, db, clock = await make()
    await svc.track_event(ev("listing_view"), BROWSER)            # 1
    clock.advance(minutes=5)
    await svc.track_event(ev("listing_view"), BROWSER)            # 3 (repeat)
    clock.advance(minutes=1)
    await svc.track_event(ev("whatsapp_click"), BROWSER)          # 10
    clock.advance(minutes=1)
    res = await svc.capture_inquiry(inquiry())                    # +25
    assert res == {"received": True, "new_lead": True}

    leads = await svc.list_leads("A1")
    assert len(leads) == 1
    lead = leads[0]
    assert lead["phone"] == "+919876543210" and lead["stage"] == "new"
    assert lead["score"] == 1 + 3 + 10 + 25 and lead["temperature"] == "hot"

    detail = await svc.lead_detail("A1", lead["id"])
    assert [t["type"] for t in detail["timeline"]] == ["listing_view", "listing_view", "whatsapp_click", "inquiry"]
    assert detail["consent"]["purpose"]

    # after identification, new events from that browser attach to the lead
    clock.advance(hours=1)
    await svc.track_event(ev("call_click"), BROWSER)
    detail = await svc.lead_detail("A1", lead["id"])
    assert detail["timeline"][-1]["type"] == "call_click" and detail["score"] == 49


async def test_second_inquiry_same_phone_updates_same_lead():
    svc, db, _ = await make()
    await svc.capture_inquiry(inquiry())
    res = await svc.capture_inquiry(inquiry(anon_id="anon-visitor-2", message="Call me"))
    assert res["new_lead"] is False
    assert len(await svc.list_leads("A1")) == 1
    assert (await svc.list_leads("A1"))[0]["message"] == "Call me"


async def test_consent_is_required():
    svc, db, _ = await make()
    with pytest.raises(TrackingError):
        await svc.capture_inquiry(inquiry(consent=False))
    assert await db.get_collection("contacts").count_documents({}) == 0


async def test_agents_only_see_their_own_leads():
    svc, _, _ = await make()
    await svc.capture_inquiry(inquiry())
    await svc.capture_inquiry(inquiry(agent_slug="priya", anon_id="anon-visitor-9", phone="9123456780"))
    a1, a2 = await svc.list_leads("A1"), await svc.list_leads("A2")
    assert len(a1) == 1 and len(a2) == 1 and a1[0]["id"] != a2[0]["id"]
    with pytest.raises(TrackingError) as e:
        await svc.lead_detail("A2", a1[0]["id"])
    assert e.value.status_code == 404
    with pytest.raises(TrackingError):
        await svc.update_stage("A2", a1[0]["id"], StageUpdate(stage="won"))


async def test_stage_update_with_note_and_hottest_first():
    svc, _, clock = await make()
    await svc.capture_inquiry(inquiry(phone="9876543210", anon_id="anon-visitor-1"))
    clock.advance(minutes=1)
    await svc.track_event(ev("whatsapp_click", anon="anon-visitor-1"), BROWSER)
    await svc.capture_inquiry(inquiry(phone="9123456780", anon_id="anon-visitor-2", name="Sita"))
    leads = await svc.list_leads("A1")
    assert leads[0]["name"] == "Amit"  # higher score first
    out = await svc.update_stage("A1", leads[0]["id"], StageUpdate(stage="site_visit", note="Visit Sat 11am"))
    assert out["stage"] == "site_visit" and out["notes"][0]["text"] == "Visit Sat 11am"
    assert [l["id"] for l in await svc.list_leads("A1", stage="site_visit")] == [leads[0]["id"]]
