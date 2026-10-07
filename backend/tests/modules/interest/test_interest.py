"""Interest links and hub: service and router, in-memory fakes, no network."""
import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.interest import router as ir
from app.modules.interest.service import InterestError, InterestService, interest_url, upsert_hub_item
from app.modules.tracking.service import TrackingService

from ..listings_fakes import ListingsCollection, ListingsDb

pytestmark = pytest.mark.asyncio


class DelCollection(ListingsCollection):
    async def delete_one(self, flt):
        from ..listings_fakes import match
        for d in self.docs:
            if match(d, flt):
                self.docs.remove(d)
                return


class Db(ListingsDb):
    def get_collection(self, name):
        return self.cols.setdefault(name, DelCollection())


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 12, 0, 0)

    def __call__(self):
        return self.t


SAMPLE = {"title": "Sample listing: 2BHK in Kharadi", "locality": "Kharadi", "subtitle": "Illustrative", "image_url": "/img/x"}


def samples(ref):
    return SAMPLE if ref == "kharadi-2bhk-ready" else None


async def owner():
    return "OWNER"


async def make():
    db, clock = Db(), Clock()
    p = db.get_collection("agent_public_profiles")
    await p.insert_one({"slug": "rahul", "agent_id": "A1", "is_public": True, "agent_name": "Rahul Sharma"})
    await p.insert_one({"slug": "owner", "agent_id": "OWNER", "is_public": True, "agent_name": "Avasetu"})
    await db.get_collection("listings").insert_one({"_id": "L1", "agent_id": "A1", "title": "2BHK in Baner", "locality": "Baner"})
    svc = InterestService(db, now=clock, samples=samples, owner_agent_id=owner)
    return svc, db, clock


def leads(db):
    return db.get_collection("contacts").docs


# ---- links ----
async def test_create_link_is_idempotent_per_kind_ref_channel():
    svc, db, _ = await make()
    a = await svc.create_link("listing", "L1", "A1", "facebook")
    b = await svc.create_link("listing", "L1", "A1", "facebook")
    c = await svc.create_link("listing", "L1", "A1", "instagram")
    assert a["code"] == b["code"] != c["code"]
    assert 6 <= len(a["code"]) <= 8 and a["code"].isalnum()
    assert a["title"] == "2BHK in Baner" and a["locality"] == "Baner"
    assert len(db.get_collection("interest_links").docs) == 2


async def test_unknown_kind_or_channel_rejected():
    svc, _, _ = await make()
    with pytest.raises(InterestError):
        await svc.create_link("nope", "L1", "A1", "facebook")
    with pytest.raises(InterestError):
        await svc.create_link("post", "p1", "A1", "tiktok")


async def test_interest_url_helper(monkeypatch):
    _, db, _ = await make()
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://site.test/")
    u1 = await interest_url(db, kind="post", ref="cal1", agent_id="A1", channel="facebook", title="Kharadi guide")
    u2 = await interest_url(db, kind="post", ref="cal1", agent_id="A1", channel="facebook")
    assert u1 == u2 and u1.startswith("https://site.test/i/")


async def test_view_shows_subject_agent_and_sample_flag():
    svc, _, _ = await make()
    real = await svc.create_link("listing", "L1", "A1", "facebook")
    v = await svc.view(real["code"])
    assert v["title"] == "2BHK in Baner" and v["agent_name"] == "Rahul Sharma" and v["sample"] is False
    s = await svc.create_link("listing", "kharadi-2bhk-ready", "A1", "instagram")
    v = await svc.view(s["code"])
    assert v["sample"] is True and v["title"].startswith("Sample listing") and v["agent_name"] == "Avasetu"
    with pytest.raises(InterestError) as e:
        await svc.view("zzzzzzz")
    assert e.value.status_code == 404


# ---- click and interest ----
async def test_click_is_recorded():
    svc, db, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    assert await svc.record_click(link["code"], ip="1.1.1.1") == {"recorded": True}
    assert await svc.store.count(link["code"], "click") == 1


async def test_one_tap_creates_an_anonymous_lead_with_channel_source_and_context():
    svc, db, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    res = await svc.record_interest(link["code"], ip="1.1.1.1", anon_id="browser-abc-123")
    assert res == {"received": True, "new_lead": True, "details_saved": False}
    (lead,) = leads(db)
    assert lead["agent_id"] == "A1" and lead["source"] == "facebook" and lead["phone"] == ""
    assert "2BHK in Baner" in lead["message"] and lead["first_listing_id"] == "L1"
    # it shows in the agent's inbox through the normal tracking view, with a score and temperature
    inbox = await TrackingService(db, now=svc.now).list_leads("A1")
    assert len(inbox) == 1 and inbox[0]["temperature"] == "cold" and inbox[0]["source"] == "facebook"


async def test_second_tap_by_same_visitor_does_not_duplicate_the_lead():
    svc, db, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    await svc.record_interest(link["code"], ip="1.1.1.1", anon_id="browser-abc-123")
    res = await svc.record_interest(link["code"], ip="1.1.1.1", anon_id="browser-abc-123")
    assert res["new_lead"] is False and len(leads(db)) == 1


async def test_contact_details_need_consent():
    svc, db, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    for kw in ({"phone": "9876543210"}, {"name": "Asha"}, {"note": "Is it ready?"}):
        with pytest.raises(InterestError) as e:
            await svc.record_interest(link["code"], consent=False, ip="2.2.2.2", **kw)
        assert e.value.status_code == 400 and "box" in str(e.value)
    assert leads(db) == []


async def test_details_with_consent_go_through_the_tracking_inquiry_flow():
    svc, db, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "instagram")
    await svc.record_interest(link["code"], ip="1.1.1.1", anon_id="browser-abc-123")  # the tap first
    res = await svc.record_interest(link["code"], name="Asha Rao", phone="98765 43210", note="Is it ready to move?",
                                    consent=True, ip="1.1.1.1", anon_id="browser-abc-123")
    assert res["details_saved"] is True and res["new_lead"] is True
    (lead,) = leads(db)  # the anonymous placeholder was replaced by the real lead
    assert lead["phone"] == "+919876543210" and lead["name"] == "Asha Rao" and lead["source"] == "instagram"
    assert lead["consent"]["purpose"] == "enquiry follow-up" and lead["first_listing_id"] == "L1"
    assert "Is it ready to move?" in lead["message"] and lead["score_base"] >= 25


async def test_bad_phone_is_a_422_not_a_crash():
    svc, _, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    with pytest.raises(InterestError) as e:
        await svc.record_interest(link["code"], phone="12345", consent=True, ip="3.3.3.3")
    assert e.value.status_code == 422


async def test_sample_interest_is_a_labelled_platform_lead_for_the_owner():
    svc, db, _ = await make()
    link = await svc.create_link("listing", "kharadi-2bhk-ready", "A1", "instagram")
    await svc.record_interest(link["code"], ip="1.1.1.1", anon_id="browser-abc-123")
    (lead,) = leads(db)
    assert lead["agent_id"] == "OWNER" and lead["name"] == "Platform interest"
    assert lead["message"].startswith("PLATFORM INTEREST (sample home") and lead["first_listing_id"] is None


async def test_page_level_post_interest_is_a_platform_lead():
    svc, db, _ = await make()
    link = await svc.create_link("page", "kharadi-guide", "A1", "facebook", title="Kharadi guide")
    await svc.record_interest(link["code"], ip="1.1.1.1")
    (lead,) = leads(db)
    assert lead["agent_id"] == "OWNER" and "educational page" in lead["message"]


async def test_honeypot_looks_successful_and_stores_nothing():
    svc, db, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    res = await svc.record_interest(link["code"], website="http://spam.example", ip="1.1.1.1")
    assert res["new_lead"] is False and leads(db) == []
    assert await svc.store.count(link["code"], "interest") == 0


async def test_interest_rate_limit_per_ip_and_code_then_free_after_an_hour():
    svc, db, clock = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    for i in range(3):
        await svc.record_interest(link["code"], ip="9.9.9.9", anon_id=f"browser-{i}-aaaa")
    with pytest.raises(InterestError) as e:
        await svc.record_interest(link["code"], ip="9.9.9.9", anon_id="browser-9-aaaa")
    assert e.value.status_code == 429
    await svc.record_interest(link["code"], ip="8.8.8.8", anon_id="browser-8-aaaa")  # another IP is fine
    clock.t += timedelta(hours=1, seconds=1)
    await svc.record_interest(link["code"], ip="9.9.9.9", anon_id="browser-9-aaaa")


async def test_click_rate_limit():
    svc, _, _ = await make()
    link = await svc.create_link("listing", "L1", "A1", "facebook")
    for _ in range(60):
        await svc.record_click(link["code"], ip="7.7.7.7")
    with pytest.raises(InterestError) as e:
        await svc.record_click(link["code"], ip="7.7.7.7")
    assert e.value.status_code == 429


# ---- router ----
@pytest.fixture
def env():
    loop = asyncio.new_event_loop()
    svc, db, clock = loop.run_until_complete(make())
    app = FastAPI()
    app.include_router(ir.public_router, prefix="/public")
    app.include_router(ir.router, prefix="/interest")
    app.dependency_overrides[ir.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: SimpleNamespace(id="A1")
    ir.clear_hub_cache()
    yield TestClient(app), svc, db, loop
    loop.close()


def test_router_flow_and_no_pii_in_urls(env):
    c, svc, db, loop = env
    r = c.post("/interest/links", json={"kind": "listing", "ref": "L1", "channel": "facebook"})
    assert r.status_code == 200
    link = r.json()
    code = link["code"]
    assert c.post("/interest/links", json={"kind": "listing", "ref": "L1", "channel": "facebook"}).json()["code"] == code
    assert c.get(f"/public/interest/{code}").json()["title"] == "2BHK in Baner"
    assert c.post(f"/public/interest/{code}/click", json={"anon_id": "browser-abc-123"}).status_code == 202
    assert c.post(f"/public/interest/{code}", json={"anon_id": "browser-abc-123"}).json()["new_lead"] is True
    bad = c.post(f"/public/interest/{code}", json={"name": "Asha", "consent": False})
    assert bad.status_code == 400
    ok = c.post(f"/public/interest/{code}", json={"name": "Asha", "phone": "9876543210", "consent": True,
                                                    "anon_id": "browser-abc-123"})
    assert ok.status_code == 200 and ok.json()["details_saved"] is True
    stats = c.get("/interest/links/L1").json()["links"][0]
    assert stats["clicks"] == 1 and stats["interests"] == 2
    assert c.get("/public/interest/nope123").status_code == 404
    assert "+91" not in link["url"] and "9876543210" not in link["url"]


def test_router_rate_limit_is_429(env):
    c, svc, db, loop = env
    code = c.post("/interest/links", json={"kind": "listing", "ref": "L1", "channel": "facebook"}).json()["code"]
    codes = [c.post(f"/public/interest/{code}", json={"anon_id": f"browser-{i}-xxxx"}).status_code for i in range(4)]
    assert codes == [200, 200, 200, 429]


def test_hub_uses_hub_items_newest_first_capped_at_12_and_cached(env):
    c, svc, db, loop = env
    for i in range(14):
        loop.run_until_complete(upsert_hub_item(db, "post", f"p{i}", f"Post {i}", subtitle="s", interest_code=f"c{i}",
                                                permalink=f"https://fb.test/{i}"))
        db.get_collection("hub_items").docs[-1]["updated_at"] = datetime(2026, 1, 1) + timedelta(minutes=i)
    r = c.get("/public/hub")
    body = r.json()
    assert r.headers["cache-control"] == "public, max-age=60"
    assert len(body["items"]) == 12 and body["items"][0]["title"] == "Post 13"
    assert body["items"][0]["interest_code"] == "c13" and body["items"][0]["sample"] is False
    loop.run_until_complete(upsert_hub_item(db, "post", "late", "Late post"))
    assert len(c.get("/public/hub").json()["items"]) == 12 and c.get("/public/hub").json()["items"][0]["title"] == "Post 13"  # cached


def test_upsert_hub_item_updates_in_place(env):
    c, svc, db, loop = env
    loop.run_until_complete(upsert_hub_item(db, "post", "p1", "First"))
    loop.run_until_complete(upsert_hub_item(db, "post", "p1", "Renamed", interest_code="abc"))
    docs = db.get_collection("hub_items").docs
    assert len(docs) == 1 and docs[0]["title"] == "Renamed" and docs[0]["interest_code"] == "abc"


def test_an_empty_hub_shows_no_sample_homes(env, monkeypatch):
    c, svc, db, loop = env
    monkeypatch.setenv("INTEREST_OWNER_AGENT_ID", "OWNER")
    body = c.get("/public/hub").json()
    assert body["items"] == [] and body["links"]["invite"].endswith("/request-invite")
    assert db.get_collection("interest_links").docs == []
    assert c.get("/public/interest/sample-image/kharadi-2bhk-ready").status_code != 200   # the sample photo route is gone
