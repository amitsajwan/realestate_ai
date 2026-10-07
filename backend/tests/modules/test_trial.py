"""Claim your free trial: TRIAL on WhatsApp -> a sign-up code at once (onboarding/trial.py, whatsapp service), within a daily cap."""
from datetime import datetime, timedelta

from app.modules.onboarding.invites import InviteService
from app.modules.onboarding.trial import TrialService
from app.modules.whatsapp.service import TRIAL_RX

from .fakes import FakeDb
from .whatsapp.helpers import BUYER, cfg, later, make, say

NOW = datetime(2026, 10, 7, 6, 0)   # 11:30 IST
PHONE = "+919876543210"


def _svc(db, clock, cap=2):
    inv = InviteService(db, "secret", now=lambda: clock["now"])
    return TrialService(db, inv, now=lambda: clock["now"], cap=cap), inv


async def test_a_claim_issues_a_working_code_and_records_the_trial():
    db, clock = FakeDb(), {"now": NOW}
    trial, inv = _svc(db, clock)
    c = await trial.claim(PHONE)
    assert c.status == "issued" and len(c.code) == 6
    await inv.verify(PHONE, c.code)                       # the normal join flow accepts it
    doc = await db.get_collection("invites").find_one({"_id": PHONE})
    assert (doc["label"], doc["plan"], doc["trial_properties"], doc["claimed_via"]) == ("trial", "trial", 3, "whatsapp")
    assert "code" not in doc and c.code not in str(doc)   # only the hash is kept


async def test_a_second_claim_soon_after_sends_nothing_new_later_a_fresh_code_for_the_same_number():
    db, clock = FakeDb(), {"now": NOW}
    trial, inv = _svc(db, clock)
    first = await trial.claim(PHONE)
    assert (await trial.claim(PHONE)).status == "too_soon"
    clock["now"] = NOW + timedelta(hours=2)
    again = await trial.claim(PHONE)
    assert again.status == "reissued" and again.code
    await inv.verify(PHONE, again.code)


async def test_over_the_daily_cap_the_claim_waits_for_the_owner_and_the_next_day_it_opens_again():
    db, clock = FakeDb(), {"now": NOW}
    trial, _ = _svc(db, clock, cap=1)
    assert (await trial.claim("+919800000001")).status == "issued"
    full = await trial.claim("+919800000002")
    assert full.status == "full" and full.code is None
    req = await db.get_collection("invite_requests").find_one({"phone": "+919800000002"})
    assert req["status"] == "new" and req["source"] == "trial-whatsapp"
    clock["now"] = NOW + timedelta(days=1)
    assert (await trial.claim("+919800000003")).status == "issued"


async def test_a_revoked_number_cannot_reopen_itself():
    db, clock = FakeDb(), {"now": NOW}
    trial, inv = _svc(db, clock)
    await inv.issue(PHONE, "pilot")
    await inv.revoke(PHONE)
    assert (await trial.claim(PHONE)).status == "blocked"


def test_what_counts_as_a_trial_claim():
    for t in ("TRIAL", "trial", "Free trial", "Claim your free trial!", "I want a free trial", "ट्रायल", "फ्री ट्रायल"):
        assert TRIAL_RX.match(t), t
    for t in ("Hi", "2 BHK trial", "is a trial visit possible tomorrow at 5pm in kharadi?", "price?"):
        assert not TRIAL_RX.match(t), t


async def test_trial_on_whatsapp_replies_with_the_code_and_makes_no_buyer_lead(monkeypatch):
    monkeypatch.delenv("TRIAL_CLAIMS", raising=False)
    svc, db, rec, clock = make()
    r = await say(svc, "TRIAL")
    assert r["status"] == "trial" and r["lead_id"] is None
    reply = r["reply"]
    assert "free trial is ready" in reply and "first 3 properties" in reply and "/join?phone=9876543210" in reply
    assert await db.get_collection("contacts").count_documents({}) == 0          # an agent, not a buyer lead
    assert (await db.get_collection("invites").find_one({"_id": "+" + BUYER}))["plan"] == "trial"


async def test_trial_claims_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("TRIAL_CLAIMS", "off")
    svc, db, rec, clock = make()
    r = await say(svc, "TRIAL")
    assert "sign-up code" not in (r.get("reply") or "")
    assert await db.get_collection("invites").count_documents({}) == 0
