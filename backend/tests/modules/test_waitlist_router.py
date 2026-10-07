import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.waitlist import router as wr
from app.modules.waitlist.service import WaitlistService

from .fakes import FakeDb

URL = "/join/request-invite"
GOOD = {"name": "Rahul Sharma", "phone": "9876543210", "city": "Pune", "message": "Baner", "consent": True}


@pytest.fixture
def env():
    db = FakeDb()
    svc = WaitlistService(db, "salt")
    app = FastAPI()
    app.include_router(wr.router, prefix="/join")
    app.dependency_overrides[wr.get_service] = lambda: svc
    return TestClient(app), db


def rows(db):
    return db.get_collection("invite_requests").docs


def test_success_duplicate_and_honeypot_have_the_same_response(env):
    c, db = env
    ok = c.post(URL, json=GOOD)
    dup = c.post(URL, json={**GOOD, "message": "changed"})
    bot = c.post(URL, json={**GOOD, "phone": "9123456780", "website": "http://spam"})
    for r in (ok, dup, bot):
        assert r.status_code == 200 and r.json() == {"received": True}
    assert ok.content == dup.content == bot.content
    assert len(rows(db)) == 1 and rows(db)[0]["message"] == "changed"


def test_invalid_fields_and_missing_consent_are_422(env):
    c, db = env
    assert c.post(URL, json={**GOOD, "consent": False}).status_code == 422
    assert c.post(URL, json={k: v for k, v in GOOD.items() if k != "consent"}).status_code == 422
    assert c.post(URL, json={**GOOD, "phone": "123"}).status_code == 422
    assert c.post(URL, json={**GOOD, "name": "x"}).status_code == 422
    assert c.post(URL, json={**GOOD, "message": "x" * 501}).status_code == 422
    assert rows(db) == []


def test_city_defaults_to_pune(env):
    c, db = env
    body = {k: v for k, v in GOOD.items() if k != "city"}
    assert c.post(URL, json=body).status_code == 200
    assert rows(db)[0]["city"] == "Pune"


def test_phone_rate_limit_returns_429(env):
    c, _ = env
    for _ in range(3):
        assert c.post(URL, json=GOOD).status_code == 200
    r = c.post(URL, json=GOOD)
    assert r.status_code == 429 and r.json()["detail"] == "Too many requests"


def test_ip_rate_limit_uses_first_forwarded_hop(env):
    c, db = env
    hdr = {"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}
    for i in range(20):
        assert c.post(URL, json={**GOOD, "phone": f"98765{i:05d}"}, headers=hdr).status_code == 200
    assert c.post(URL, json={**GOOD, "phone": "9000000009"}, headers=hdr).status_code == 429
    other = {"X-Forwarded-For": "203.0.113.6"}
    assert c.post(URL, json={**GOOD, "phone": "9000000009"}, headers=other).status_code == 200
    assert "203.0.113.5" not in repr(rows(db))


def test_falls_back_to_socket_peer_when_no_proxy_header(env):
    c, db = env
    c.post(URL, json=GOOD)
    assert rows(db)[0]["ip_hash"] and "testclient" not in repr(rows(db))


def test_the_owner_is_told_once_per_new_request_and_a_failing_alert_never_fails_the_form(env):
    c, db = env
    told = []

    async def tell(name, city):
        told.append((name, city))

    wired = wr._on_new_request  # app/wiring.py's alert, restored afterwards
    wr.configure(on_new_request=tell)
    try:
        c.post(URL, json=GOOD)
        c.post(URL, json={**GOOD, "message": "again"})  # merged into the waiting request: no second alert
        c.post(URL, json={**GOOD, "phone": "9123456780", "website": "http://spam"})  # honeypot: none
        assert told == [("Rahul Sharma", "Pune")]

        async def broken(name, city):
            raise RuntimeError("notifications down")

        wr.configure(on_new_request=broken)
        r = c.post(URL, json={**GOOD, "phone": "9000000001", "name": "Asha"})
        assert r.status_code == 200 and len(rows(db)) == 2
    finally:
        wr.configure(on_new_request=wired)
