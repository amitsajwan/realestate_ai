from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.waitlist.schemas import CONSENT_TEXT, InviteRequestIn
from app.modules.waitlist.service import (
    MAX_PER_IP_PER_HOUR, MAX_PER_PHONE_PER_HOUR, RateLimited, WaitlistService, client_ip, hash_ip,
)
from scripts.invite_requests import format_request

from .fakes import FakeDb

pytestmark = pytest.mark.asyncio


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 12, 0, 0)

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


def body(**over):
    d = {"name": "Rahul Sharma", "phone": "98765 43210", "city": "Pune", "message": "Baner, 2BHK sales", "consent": True}
    d.update(over)
    return InviteRequestIn(**d)


def make():
    clock, db = Clock(), FakeDb()
    return WaitlistService(db, "salt", now=clock), db, clock


def rows(db):
    return db.get_collection("invite_requests").docs


# -- validation ---------------------------------------------------------------------------------------

def test_valid_request_is_normalised():
    b = body(name="  Rahul  ", message="   ")
    assert b.phone == "+919876543210" and b.name == "Rahul" and b.message is None and b.city == "Pune"


def test_city_defaults_to_pune():
    assert InviteRequestIn(name="Rahul", phone="9876543210", consent=True).city == "Pune"


@pytest.mark.parametrize("over", [
    {"name": "R"}, {"name": "x" * 101}, {"phone": "12345"}, {"phone": "5876543210"}, {"city": "P"}, {"city": "x" * 61},
    {"message": "x" * 501}, {"consent": False},
])
def test_invalid_fields_are_rejected(over):
    with pytest.raises(ValidationError):
        body(**over)


def test_consent_is_required():
    with pytest.raises(ValidationError):
        InviteRequestIn(name="Rahul", phone="9876543210")
    with pytest.raises(ValidationError):
        body(consent=False)


# -- storing ------------------------------------------------------------------------------------------

async def test_request_is_stored_as_new_with_consent_record():
    svc, db, clock = make()
    assert await svc.submit(body(), "203.0.113.9") is None
    (r,) = rows(db)
    assert r["phone"] == "+919876543210" and r["status"] == "new" and r["city"] == "Pune"
    assert r["consent"] == {"given_at": clock.t, "text": CONSENT_TEXT}
    assert r["created_at"] == r["updated_at"] == clock.t


async def test_honeypot_is_dropped_silently_and_not_stored():
    svc, db, _ = make()
    assert await svc.submit(body(website="http://spam.example"), "203.0.113.9") is None
    assert rows(db) == []
    assert db.get_collection("invite_request_attempts").docs == []  # does not even count towards limits


async def test_empty_honeypot_is_a_normal_request():
    svc, db, _ = make()
    await svc.submit(body(website=""), "203.0.113.9")
    assert len(rows(db)) == 1


async def test_repeat_within_24h_updates_the_existing_row():
    svc, db, clock = make()
    await svc.submit(body(message="first"), "203.0.113.9")
    first_id = rows(db)[0]["_id"]
    clock.advance(hours=2)
    await svc.submit(body(name="Rahul S", message="second"), "203.0.113.9")
    (r,) = rows(db)
    assert r["_id"] == first_id and r["name"] == "Rahul S" and r["message"] == "second"
    assert r["created_at"] < r["updated_at"] == clock.t and r["status"] == "new"


async def test_repeat_after_24h_is_a_new_row():
    svc, db, clock = make()
    await svc.submit(body(), "203.0.113.9")
    clock.advance(hours=25)
    await svc.submit(body(), "203.0.113.9")
    assert len(rows(db)) == 2


# -- rate limits --------------------------------------------------------------------------------------

async def test_phone_limit_is_three_per_rolling_hour():
    svc, db, clock = make()
    for i in range(MAX_PER_PHONE_PER_HOUR):
        await svc.submit(body(message=f"m{i}"), f"203.0.113.{i}")
    with pytest.raises(RateLimited):
        await svc.submit(body(), "203.0.113.99")
    assert len(rows(db)) == 1  # the three repeats updated one row; the blocked one changed nothing
    assert rows(db)[0]["message"] == f"m{MAX_PER_PHONE_PER_HOUR - 1}"
    clock.advance(minutes=61)
    await svc.submit(body(), "203.0.113.99")  # window rolled over


async def test_other_phones_are_not_affected_by_a_blocked_phone():
    svc, _, _ = make()
    for _ in range(MAX_PER_PHONE_PER_HOUR):
        await svc.submit(body(), "203.0.113.1")
    await svc.submit(body(phone="9123456780"), "203.0.113.2")


async def test_ip_limit_is_twenty_per_hour_across_phones():
    svc, db, clock = make()
    for i in range(MAX_PER_IP_PER_HOUR):
        await svc.submit(body(phone=f"98765{i:05d}"), "198.51.100.7")
    with pytest.raises(RateLimited):
        await svc.submit(body(phone="9000000001"), "198.51.100.7")
    await svc.submit(body(phone="9000000001"), "198.51.100.8")  # a different client is fine
    clock.advance(minutes=61)
    await svc.submit(body(phone="9000000002"), "198.51.100.7")


async def test_unknown_ip_skips_only_the_ip_limit():
    svc, db, _ = make()
    for i in range(MAX_PER_IP_PER_HOUR + 2):
        await svc.submit(body(phone=f"98765{i:05d}"), None)
    assert len(rows(db)) == MAX_PER_IP_PER_HOUR + 2
    assert all(r["ip_hash"] is None for r in rows(db))


# -- ip handling --------------------------------------------------------------------------------------

async def test_raw_ip_is_never_stored():
    svc, db, _ = make()
    ip = "203.0.113.55"
    await svc.submit(body(), ip)
    stored = repr(rows(db)) + repr(db.get_collection("invite_request_attempts").docs)
    assert ip not in stored
    assert rows(db)[0]["ip_hash"] == hash_ip(ip, "salt")
    assert len(rows(db)[0]["ip_hash"]) == 64


def test_hash_is_salted_and_stable():
    assert hash_ip("1.2.3.4", "a") == hash_ip("1.2.3.4", "a")
    assert hash_ip("1.2.3.4", "a") != hash_ip("1.2.3.4", "b")
    assert hash_ip("1.2.3.4", "a") != hash_ip("1.2.3.5", "a")


def test_client_ip_prefers_first_forwarded_hop():
    assert client_ip("203.0.113.1, 10.0.0.2", "10.0.0.3") == "203.0.113.1"
    assert client_ip(" 203.0.113.1 ", "10.0.0.3") == "203.0.113.1"
    assert client_ip(None, "10.0.0.3") == "10.0.0.3"
    assert client_ip("", "10.0.0.3") == "10.0.0.3"
    assert client_ip(None, None) is None


# -- admin --------------------------------------------------------------------------------------------

async def test_list_new_is_oldest_first_and_mark_invited_hides_it():
    svc, db, clock = make()
    await svc.submit(body(phone="9000000001", name="First"), "1.1.1.1")
    clock.advance(minutes=5)
    await svc.submit(body(phone="9000000002", name="Second"), "1.1.1.2")
    assert [r["name"] for r in await svc.list_new()] == ["First", "Second"]
    assert await svc.mark_invited("+919000000001") is True
    assert [r["name"] for r in await svc.list_new()] == ["Second"]
    assert await svc.mark_invited("+919000000001") is False
    assert await svc.mark_invited("+919111111111") is False


async def test_format_request_shows_phone_name_city_message_date():
    svc, _, _ = make()
    await svc.submit(body(), "1.1.1.1")
    out = format_request((await svc.list_new())[0])
    for part in ("+919876543210", "Rahul Sharma", "Pune", "Baner, 2BHK sales", "2026-01-01"):
        assert part in out
