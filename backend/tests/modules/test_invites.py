from datetime import datetime, timedelta

import json
import time

import httpx
import jwt
import pytest

from app.modules.onboarding.invites import HARD_STOP_AFTER, InviteService
from app.modules.onboarding.otp import OTPError
from app.modules.onboarding.service import OnboardingService, default_branding
from app.modules.whatsapp.config import WhatsAppConfig
from app.modules.whatsapp.graph import WhatsAppGraph

from .fakes import FakeDb
from .test_onboarding import Clock, FakeUsers

pytestmark = pytest.mark.asyncio
PHONE = "+919876543210"


def make():
    clock, db = Clock(), FakeDb()
    return InviteService(db, "secret", now=clock), db, clock


async def test_issue_then_login_with_code():
    inv, _, _ = make()
    code = await inv.issue(PHONE, "Rahul, Baner")
    assert len(code) == 6 and code.isdigit()
    assert await inv.request(PHONE) is None  # nothing is sent; the code was handed over personally
    await inv.verify(PHONE, code)
    await inv.verify(PHONE, code)  # reusable: it is the agent's personal access code


async def test_not_invited_and_revoked_are_rejected_with_403():
    inv, _, _ = make()
    for call in (inv.request(PHONE), inv.verify(PHONE, "123456")):
        with pytest.raises(OTPError) as e:
            await call
        assert e.value.status_code == 403
    code = await inv.issue(PHONE)
    assert await inv.revoke(PHONE) is True
    with pytest.raises(OTPError) as e:
        await inv.verify(PHONE, code)
    assert e.value.status_code == 403
    assert await inv.revoke("+919999999999") is False


async def test_wrong_codes_lock_then_expire_lock():
    inv, _, clock = make()
    code = await inv.issue(PHONE)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        with pytest.raises(OTPError) as e:
            await inv.verify(PHONE, wrong)
        assert e.value.status_code == 400
    with pytest.raises(OTPError) as e:  # locked: even the right code is refused
        await inv.verify(PHONE, code)
    assert e.value.status_code == 429
    clock.advance(minutes=31)
    await inv.verify(PHONE, code)


async def test_hard_stop_until_reissued():
    inv, _, clock = make()
    code = await inv.issue(PHONE)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(HARD_STOP_AFTER):
        try:
            await inv.verify(PHONE, wrong)
        except OTPError:
            pass
        clock.advance(minutes=31)  # skip the temporary locks
    with pytest.raises(OTPError) as e:
        await inv.verify(PHONE, code)
    assert e.value.status_code == 429 and "new code" in str(e.value)
    new_code = await inv.issue(PHONE)  # re-issue resets everything and invalidates the old code
    await inv.verify(PHONE, new_code)
    if new_code != code:
        with pytest.raises(OTPError):
            await inv.verify(PHONE, code)


async def test_codes_are_stored_hashed():
    inv, db, _ = make()
    code = await inv.issue(PHONE)
    doc = await db.get_collection("invites").find_one({"_id": PHONE})
    assert code not in str(doc)


async def test_join_flow_through_invite_creates_user_and_site():
    inv, db, _ = make()
    users = FakeUsers()

    async def token(u):
        return f"tok-{u.id}"

    async def brand(n, c):
        return default_branding(n, c)

    svc = OnboardingService(db, inv, users, token, "https://x.test", branding=brand)
    with pytest.raises(OTPError):
        await svc.request_code(PHONE)  # not invited yet
    code = await inv.issue(PHONE)
    await svc.request_code(PHONE)
    res = await svc.verify_and_login(PHONE, code)
    assert res["is_new_user"] and res["access_token"] == "tok-u1"
    again = await svc.verify_and_login(PHONE, code)  # returning agent, same user
    assert not again["is_new_user"] and len(users.users) == 1


def test_agent_token_lives_30_days_and_still_validates_under_app_strategy():
    from app.core.auth_backend import SECRET_KEY, ALGORITHM
    from app.modules.onboarding.router import _agent_jwt
    from app.core.config import settings
    import asyncio

    user = type("U", (), {"id": "abc123"})()
    token = asyncio.run(_agent_jwt().write_token(user))
    claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="fastapi-users:auth")
    lifetime = claims["exp"] - time.time()
    assert settings.join_token_days * 86400 - 120 < lifetime <= settings.join_token_days * 86400
    assert claims["sub"] == "abc123"


def make_with_whatsapp(send=None):
    clock, db, sent = Clock(), FakeDb(), []

    async def record(phone, code):
        sent.append((phone, code))

    return InviteService(db, "secret", now=clock, send_code=send or record), sent, clock


async def test_invited_number_gets_a_one_time_login_code_on_whatsapp():
    inv, sent, _ = make_with_whatsapp()
    await inv.issue(PHONE)
    code = await inv.request(PHONE)
    assert sent == [(PHONE, code)]
    await inv.verify(PHONE, code)
    with pytest.raises(OTPError):  # used once
        await inv.verify(PHONE, code)


async def test_number_without_an_invite_gets_nothing_on_whatsapp():
    inv, sent, _ = make_with_whatsapp()
    with pytest.raises(OTPError) as e:
        await inv.request(PHONE)
    assert e.value.status_code == 403 and sent == []


async def test_revoked_invite_cannot_use_a_code_already_sent():
    inv, _, _ = make_with_whatsapp()
    await inv.issue(PHONE)
    code = await inv.request(PHONE)
    await inv.revoke(PHONE)
    with pytest.raises(OTPError) as e:
        await inv.verify(PHONE, code)
    assert e.value.status_code == 403


async def test_whatsapp_code_expires_after_five_minutes():
    inv, _, clock = make_with_whatsapp()
    await inv.issue(PHONE)
    code = await inv.request(PHONE)
    clock.advance(minutes=6)
    with pytest.raises(OTPError):
        await inv.verify(PHONE, code)


async def test_personal_code_still_signs_in_when_whatsapp_fails():
    async def broken(phone, code):
        raise RuntimeError("WhatsApp is not sending")

    inv, _, _ = make_with_whatsapp(broken)
    personal = await inv.issue(PHONE)
    assert await inv.request(PHONE) is None
    await inv.verify(PHONE, personal)


async def test_login_code_message_fills_the_body_and_the_copy_button():
    seen = {}

    def reply(request):
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"messages": [{"id": "wamid.1"}]})

    graph = WhatsAppGraph(WhatsAppConfig(access_token="t"), transport=httpx.MockTransport(reply))
    assert await graph.send_login_code("123", "919876543210", "482913") == "wamid.1"
    assert seen["to"] == "919876543210" and seen["template"]["name"] == "login_code_v1"
    assert [c["parameters"][0]["text"] for c in seen["template"]["components"]] == ["482913", "482913"]
    assert seen["template"]["components"][1]["sub_type"] == "url"
