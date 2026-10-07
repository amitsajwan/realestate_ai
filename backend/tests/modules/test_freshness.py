"""Listing freshness: 'still available?' (contract docs/contracts/activity.md section 2)."""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_backend import current_active_user
from app.modules.listings import router as lr
from app.modules.listings.freshness import freshness_of
from app.modules.listings.schemas import ListingCreate, ListingUpdate
from app.modules.listings.service import ListingError, ListingService

from .listings_fakes import ListingsDb
from .qual_helpers import Clock

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 3, 1, 12, 0, 0)
FULL = dict(title="2BHK in Baner", transaction="sale", property_type="apartment", price_inr=8500000,
            city="Pune", locality="Baner", bhk=2, description={"en": "Bright"})


def doc(days=None, status="live", confirmed=True, published=None, created=None):
    """A stored listing whose confirmation (or fallback timestamp) is `days` old."""
    stamp = NOW - timedelta(days=days) if isinstance(days, (int, float)) else days
    return {"status": status, "freshness_confirmed_at": stamp if confirmed else None,
            "published_at": published, "created_at": created or NOW - timedelta(days=400)}


# ---- pure rules --------------------------------------------------------------------------------
@pytest.mark.parametrize("delta,expected", [
    (timedelta(0), ("fresh", 0)),
    (timedelta(days=20, hours=23, minutes=59, seconds=59), ("fresh", 20)),
    (timedelta(days=21), ("confirm", 21)),
    (timedelta(days=44, hours=23, minutes=59, seconds=59), ("confirm", 44)),
    (timedelta(days=45), ("hidden", 45)),
    (timedelta(days=200), ("hidden", 200)),
])
def test_boundaries(delta, expected):
    assert freshness_of(doc(NOW - delta), NOW) == expected


def test_under_offer_follows_the_same_rules():
    assert freshness_of(doc(30, status="under_offer"), NOW) == ("confirm", 30)
    assert freshness_of(doc(60, status="under_offer"), NOW) == ("hidden", 60)


@pytest.mark.parametrize("status", ["draft", "paused", "expired", "sold", "rented"])
def test_other_statuses_are_always_fresh(status):
    assert freshness_of(doc(100, status=status), NOW) == ("fresh", None)


def test_fallback_chain_confirmed_then_published_then_created():
    assert freshness_of(doc(1, published=NOW - timedelta(days=99)), NOW) == ("fresh", 1)   # confirmed wins
    assert freshness_of(doc(confirmed=False, days=None, published=NOW - timedelta(days=30)), NOW) == ("confirm", 30)
    assert freshness_of(doc(confirmed=False, days=None, created=NOW - timedelta(days=50)), NOW) == ("hidden", 50)
    assert freshness_of({"status": "live"}, NOW) == ("fresh", None)  # nothing to measure from


def test_clock_skew_never_gives_negative_days():
    assert freshness_of(doc(NOW + timedelta(hours=1)), NOW) == ("fresh", 0)


# ---- service -------------------------------------------------------------------------------------
async def make():
    db, clock = ListingsDb(), Clock()
    await db.get_collection("agent_public_profiles").insert_one(
        {"slug": "rahul", "agent_id": "A1", "agent_name": "Rahul", "phone": "1", "photo": None, "is_public": True})
    return ListingService(db, now=clock), db, clock


async def live(svc, agent="A1", **over):
    lst = await svc.create(agent, ListingCreate(**{**FULL, **over}))
    return await svc.publish(agent, lst.id)


async def test_new_listing_is_fresh_and_draft_has_null_days():
    svc, _, _ = await make()
    draft = await svc.create("A1", ListingCreate())
    assert (draft.freshness, draft.days_since_confirmed) == ("fresh", None)
    lst = await live(svc)
    assert (lst.freshness, lst.days_since_confirmed) == ("fresh", 0)


async def test_all_agent_reads_and_writes_carry_freshness():
    svc, db, clock = await make()
    lst = await live(svc)
    clock.advance(days=21)
    got = await svc.get_mine("A1", lst.id)
    assert (got.freshness, got.days_since_confirmed) == ("confirm", 21)
    assert [(l.freshness, l.days_since_confirmed) for l in await svc.list_mine("A1")] == [("confirm", 21)]
    patched = await svc.patch("A1", lst.id, ListingUpdate(title="New title"))
    assert (patched.freshness, patched.days_since_confirmed) == ("confirm", 21)  # editing is not confirming
    clock.advance(days=24)
    changed = await svc.change_status("A1", lst.id, "under_offer")
    assert (changed.freshness, changed.days_since_confirmed) == ("hidden", 45)
    assert "freshness" not in db.get_collection("listings").docs[0]  # computed, never stored


async def test_reactivation_from_paused_restamps():
    svc, _, clock = await make()
    lst = await live(svc)
    await svc.change_status("A1", lst.id, "paused")
    clock.advance(days=60)
    back = await svc.change_status("A1", lst.id, "live")
    assert (back.freshness, back.days_since_confirmed) == ("fresh", 0)


async def test_confirm_available_resets_the_clock_from_confirm_and_hidden():
    svc, db, clock = await make()
    a, b = await live(svc), await live(svc)
    clock.advance(days=30)
    assert (await svc.get_mine("A1", a.id)).freshness == "confirm"
    out = await svc.confirm_available("A1", a.id)
    assert (out.freshness, out.days_since_confirmed, out.freshness_confirmed_at) == ("fresh", 0, clock())
    clock.advance(days=20)
    assert (await svc.get_mine("A1", b.id)).freshness == "hidden"  # 50 days
    out = await svc.confirm_available("A1", b.id)
    assert out.freshness == "fresh" and out.status == "live"
    assert (await svc.get_mine("A1", a.id)).days_since_confirmed == 20


async def test_confirm_available_under_offer_ok_other_statuses_409():
    svc, _, _ = await make()
    lst = await live(svc)
    await svc.change_status("A1", lst.id, "under_offer")
    assert (await svc.confirm_available("A1", lst.id)).status == "under_offer"
    draft = await svc.create("A1", ListingCreate(**FULL))
    for target in ("paused", "expired", "sold", "rented"):
        other = await live(svc)
        await svc.change_status("A1", other.id, target)
        with pytest.raises(ListingError) as exc:
            await svc.confirm_available("A1", other.id)
        assert exc.value.status_code == 409, target
    with pytest.raises(ListingError) as exc:
        await svc.confirm_available("A1", draft.id)
    assert exc.value.status_code == 409


async def test_confirm_available_is_owner_only():
    svc, _, _ = await make()
    lst = await live(svc)
    for agent, lid in (("A2", lst.id), ("A1", "NOPE")):
        with pytest.raises(ListingError) as exc:
            await svc.confirm_available(agent, lid)
        assert exc.value.status_code == 404


# ---- public reads ----------------------------------------------------------------------------------
async def test_public_list_excludes_hidden_and_keeps_confirm_stage_visible():
    svc, _, clock = await make()
    old = await live(svc, title="old")
    clock.advance(days=25)
    mid = await live(svc, title="mid")
    clock.advance(days=20)  # old is 45 days (hidden), mid is 20 (fresh)
    items, total = await svc.public_list("rahul")
    assert [i.id for i in items] == [mid.id] and total == 1
    clock.advance(days=1)   # mid = 21 days -> confirm stage, still visible to buyers
    assert (await svc.public_list("rahul"))[1] == 1
    await svc.confirm_available("A1", old.id)
    items, total = await svc.public_list("rahul")
    assert {i.id for i in items} == {old.id, mid.id} and total == 2


async def test_public_list_pagination_counts_only_visible():
    svc, _, clock = await make()
    hidden = await live(svc, title="stale")
    clock.advance(days=46)
    fresh = [await live(svc, title=f"f{i}") for i in range(3)]
    page1, total = await svc.public_list("rahul", limit=2, offset=0)
    page2, _ = await svc.public_list("rahul", limit=2, offset=2)
    assert total == 3 and len(page1) == 2 and len(page2) == 1
    assert {i.id for i in page1 + page2} == {f.id for f in fresh} and hidden.id not in {i.id for i in page1 + page2}


async def test_public_get_hidden_is_404_until_confirmed():
    svc, _, clock = await make()
    lst = await live(svc)
    clock.advance(days=44)
    assert (await svc.public_get(lst.id)).id == lst.id
    clock.advance(days=1)
    with pytest.raises(ListingError) as exc:
        await svc.public_get(lst.id)
    assert exc.value.status_code == 404
    await svc.confirm_available("A1", lst.id)
    assert (await svc.public_get(lst.id)).id == lst.id


async def test_public_listing_has_no_freshness_fields():
    svc, _, _ = await make()
    lst = await live(svc)
    pub = (await svc.public_get(lst.id)).model_dump()
    assert "freshness" not in pub and "days_since_confirmed" not in pub


async def test_hidden_listing_keeps_status_live_for_marketing_and_social():
    svc, db, clock = await make()
    lst = await live(svc)
    clock.advance(days=90)
    assert (await svc.get_mine("A1", lst.id)).freshness == "hidden"
    assert db.get_collection("listings").docs[0]["status"] == "live"  # nothing rewrites the stored status


# ---- router ------------------------------------------------------------------------------------
@pytest.fixture
def env():
    db, clock = ListingsDb(), Clock()
    svc = ListingService(db, now=clock)
    who = SimpleNamespace(id="A1")
    app = FastAPI()
    app.include_router(lr.router, prefix="/listings")
    app.include_router(lr.public_router, prefix="/public")
    app.dependency_overrides[lr.get_service] = lambda: svc
    app.dependency_overrides[current_active_user] = lambda: who
    db.get_collection("agent_public_profiles").docs.append(
        {"slug": "rahul", "agent_id": "A1", "agent_name": "Rahul", "phone": "1", "photo": None, "is_public": True})
    return TestClient(app), who, clock


def _live(c):
    lid = c.post("/listings", json={**FULL, "media": []}).json()["id"]
    assert c.post(f"/listings/{lid}/publish").status_code == 200
    return lid


def test_router_freshness_fields_and_confirm(env):
    c, _, clock = env
    lid = _live(c)
    got = c.get(f"/listings/{lid}").json()
    assert got["freshness"] == "fresh" and got["days_since_confirmed"] == 0
    clock.advance(days=30)
    assert c.get(f"/listings/{lid}").json()["freshness"] == "confirm"
    assert c.get("/listings").json()["items"][0]["days_since_confirmed"] == 30
    r = c.post(f"/listings/{lid}/confirm-available")
    assert r.status_code == 200 and r.json()["freshness"] == "fresh" and r.json()["id"] == lid
    assert c.get(f"/listings/{lid}").json()["days_since_confirmed"] == 0


def test_router_confirm_rules(env):
    c, who, clock = env
    lid = _live(c)
    draft = c.post("/listings", json=FULL).json()["id"]
    assert c.post(f"/listings/{draft}/confirm-available").status_code == 409
    c.post(f"/listings/{lid}/status", json={"status": "paused"})
    assert c.post(f"/listings/{lid}/confirm-available").status_code == 409
    c.post(f"/listings/{lid}/status", json={"status": "live"})
    assert c.post(f"/listings/{lid}/confirm-available").status_code == 200
    who.id = "A2"
    assert c.post(f"/listings/{lid}/confirm-available").status_code == 404


def test_router_public_hides_stale_listing(env):
    c, _, clock = env
    lid = _live(c)
    clock.advance(days=45)
    assert c.get(f"/public/listings/{lid}").status_code == 404
    assert c.get("/public/agents/rahul/listings").json() == {"items": [], "total": 0}
    assert c.get(f"/listings/{lid}").json()["freshness"] == "hidden"  # the agent still sees it
    c.post(f"/listings/{lid}/confirm-available")
    body = c.get(f"/public/listings/{lid}").json()
    assert body["id"] == lid and "freshness" not in body

