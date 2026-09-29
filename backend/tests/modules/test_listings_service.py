from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.listings.schemas import ListingCreate, ListingUpdate
from app.modules.listings.service import ListingError, ListingService, compute_fingerprint

from .listings_fakes import ListingsDb

pytestmark = pytest.mark.asyncio


class Clock:
    """Advances one second per call so ordering is deterministic."""
    def __init__(self):
        self.t = datetime(2026, 1, 1, 12, 0, 0)

    def __call__(self):
        self.t += timedelta(seconds=1)
        return self.t


FULL = dict(
    title="2BHK in Baner", transaction="sale", property_type="apartment", price_inr=8500000,
    city="Pune", locality="Baner", project_name="Sky Heights", bhk=2, carpet_sqft=845,
    description={"en": "Bright corner flat"}, media=[{"url": "https://x/a.jpg", "kind": "image", "order": 0}],
)


async def make():
    db = ListingsDb()
    await db.get_collection("agent_public_profiles").insert_one(
        {"slug": "rahul", "agent_id": "A1", "agent_name": "Rahul", "phone": "+919876543210",
         "photo": "p.jpg", "is_public": True})
    await db.get_collection("agent_public_profiles").insert_one(
        {"slug": "hidden", "agent_id": "A3", "agent_name": "H", "is_public": False})
    return ListingService(db, now=Clock()), db


async def live(svc, agent="A1", **over):
    lst = await svc.create(agent, ListingCreate(**{**FULL, **over}))
    return await svc.publish(agent, lst.id)


# ---- create / read / patch -------------------------------------------------------------------
async def test_create_sparse_draft():
    svc, db = await make()
    lst = await svc.create("A1", ListingCreate())
    assert lst.status == "draft" and lst.visibility == "network" and lst.agent_id == "A1"
    assert len(lst.id) == 32 and lst.published_at is None
    stored = db.get_collection("listings").docs[0]
    assert stored["_id"] == stored["id"] == lst.id


async def test_list_mine_filters_and_isolation():
    svc, _ = await make()
    d = await svc.create("A1", ListingCreate(title="draft"))
    lv = await live(svc)
    await live(svc, agent="A2")
    assert {x.id for x in await svc.list_mine("A1")} == {d.id, lv.id}
    assert [x.id for x in await svc.list_mine("A1", status="live")] == [lv.id]
    assert len(await svc.list_mine("A1", limit=1)) == 1
    assert (await svc.list_mine("A1"))[0].id == lv.id  # newest first


async def test_get_mine_and_owner_scoping_404():
    svc, _ = await make()
    lst = await svc.create("A1", ListingCreate())
    assert (await svc.get_mine("A1", lst.id)).id == lst.id
    for call in (svc.get_mine("A2", lst.id), svc.patch("A2", lst.id, ListingUpdate(title="x")),
                 svc.publish("A2", lst.id), svc.change_status("A2", lst.id, "paused"),
                 svc.get_mine("A1", "nope")):
        with pytest.raises(ListingError) as e:
            await call
        assert e.value.status_code == 404


async def test_patch_only_sets_given_fields():
    svc, _ = await make()
    lst = await svc.create("A1", ListingCreate(**FULL))
    out = await svc.patch("A1", lst.id, ListingUpdate(price_inr=9000000, floor=4))
    assert out.price_inr == 9000000 and out.floor == 4 and out.title == FULL["title"]
    assert out.updated_at > lst.updated_at and out.created_at == lst.created_at
    out = await svc.patch("A1", lst.id, ListingUpdate(bhk=None))
    assert out.bhk is None and out.city == "Pune"


async def test_patch_cannot_touch_protected_fields():
    with pytest.raises(ValidationError):
        ListingUpdate(status="live")
    with pytest.raises(ValidationError):
        ListingUpdate(agent_id="A2")
    with pytest.raises(ValidationError):
        ListingUpdate(title=None)


# ---- validation ------------------------------------------------------------------------------
@pytest.mark.parametrize("bad", [
    {"price_inr": 0}, {"price_inr": -5}, {"price_inr": 85.5}, {"price_inr": "85"},
    {"bhk": 0.4}, {"bhk": 21}, {"carpet_sqft": 0}, {"super_built_up_sqft": -1},
    {"title": "x" * 121}, {"media": [{"url": "  "}]}, {"media": [{"url": ""}]},
    {"amenities": [""]}, {"amenities": ["x" * 41]}, {"amenities": "gym"},
    {"transaction": "lease"}, {"property_type": "castle"}, {"visibility": "world"},
])
async def test_field_validation(bad):
    with pytest.raises(ValidationError):
        ListingCreate(**bad)


async def test_valid_edges_and_amenity_strip():
    lst = ListingCreate(bhk=0.5, price_inr=1, amenities=[" Gym ", "Pool"], media=[{"url": " https://a "}])
    assert lst.amenities == ["Gym", "Pool"] and lst.media[0].url == "https://a"
    assert ListingCreate(bhk=20).bhk == 20


# ---- publish ---------------------------------------------------------------------------------
async def test_publish_success():
    svc, db = await make()
    out = await live(svc)
    assert out.status == "live" and out.published_at and out.freshness_confirmed_at == out.published_at
    assert db.get_collection("listings").docs[0]["fingerprint"] == "pune|baner|sky heights|2|850|sale"


async def test_publish_lists_missing_fields():
    svc, _ = await make()
    lst = await svc.create("A1", ListingCreate())
    with pytest.raises(ListingError) as e:
        await svc.publish("A1", lst.id)
    assert e.value.status_code == 422
    assert set(e.value.detail["missing"]) == {"title", "transaction", "property_type", "price_inr",
                                              "city", "locality", "media", "description.en"}


async def test_publish_requires_an_image_not_just_video():
    svc, _ = await make()
    lst = await svc.create("A1", ListingCreate(**{**FULL, "media": [{"url": "v.mp4", "kind": "video"}]}))
    with pytest.raises(ListingError) as e:
        await svc.publish("A1", lst.id)
    assert e.value.detail["missing"] == ["media"]


async def test_publish_twice_is_409_and_failed_publish_stays_draft():
    svc, _ = await make()
    out = await live(svc)
    with pytest.raises(ListingError) as e:
        await svc.publish("A1", out.id)
    assert e.value.status_code == 409
    d = await svc.create("A1", ListingCreate())
    with pytest.raises(ListingError):
        await svc.publish("A1", d.id)
    assert (await svc.get_mine("A1", d.id)).status == "draft"


# ---- transitions -----------------------------------------------------------------------------
@pytest.mark.parametrize("path", [
    ["under_offer", "sold"], ["under_offer", "rented"], ["under_offer", "live"], ["paused", "live"],
    ["paused", "expired", "live"], ["expired"], ["under_offer", "paused", "live", "under_offer", "expired"],
])
async def test_legal_transitions(path):
    svc, _ = await make()
    lst = await live(svc)
    for target in path:
        lst = await svc.change_status("A1", lst.id, target)
        assert lst.status == target


@pytest.mark.parametrize("start,target", [
    ("draft", "live"), ("draft", "paused"), ("draft", "sold"), ("sold", "live"), ("rented", "live"),
    ("sold", "paused"), ("paused", "sold"), ("paused", "under_offer"), ("expired", "paused"),
    ("live", "live"), ("live", "draft"),
])
async def test_illegal_transitions_409(start, target):
    svc, db = await make()
    lst = await live(svc)
    db.get_collection("listings").docs[0]["status"] = start
    with pytest.raises(ListingError) as e:
        await svc.change_status("A1", lst.id, target)
    assert e.value.status_code == 409


async def test_reactivation_reconfirms_freshness():
    svc, _ = await make()
    lst = await live(svc)
    await svc.change_status("A1", lst.id, "expired")
    back = await svc.change_status("A1", lst.id, "live")
    assert back.freshness_confirmed_at > lst.freshness_confirmed_at and back.published_at == lst.published_at


# ---- fingerprint -----------------------------------------------------------------------------
def test_fingerprint_stable_under_formatting_and_small_area_changes():
    base = dict(city="Pune", locality="Baner", project_name="Sky Heights", bhk=2, carpet_sqft=845, transaction="sale")
    fp = compute_fingerprint(base)
    assert fp == compute_fingerprint({**base, "city": " PUNE ", "locality": "baner!", "project_name": "sky-heights"})
    assert fp == compute_fingerprint({**base, "carpet_sqft": 860, "bhk": 2.0})
    assert fp != compute_fingerprint({**base, "carpet_sqft": 1200})
    assert fp != compute_fingerprint({**base, "transaction": "rent"})
    assert fp != compute_fingerprint({**base, "bhk": 3})


async def test_fingerprint_refreshed_when_live_listing_edited():
    svc, db = await make()
    lst = await live(svc)
    await svc.patch("A1", lst.id, ListingUpdate(locality="Aundh"))
    assert db.get_collection("listings").docs[0]["fingerprint"].startswith("pune|aundh|")


# ---- public reads ----------------------------------------------------------------------------
async def test_public_list_visibility_rules():
    svc, _ = await make()
    pub = await live(svc, visibility="public", title="pub")
    net = await live(svc, visibility="network", title="net")
    await live(svc, visibility="private", title="private")
    off = await live(svc, title="offer")
    await svc.change_status("A1", off.id, "under_offer")
    paused = await live(svc, title="paused")
    await svc.change_status("A1", paused.id, "paused")
    await svc.create("A1", ListingCreate(**FULL, ))  # draft
    await live(svc, agent="A2", title="other agent")
    items, total = await svc.public_list("rahul")
    assert {i.id for i in items} == {pub.id, net.id, off.id} and total == 3
    dumped = items[0].model_dump()
    assert dumped["agent"] == {"slug": "rahul", "agent_name": "Rahul", "phone": "+919876543210", "photo": "p.jpg"}
    for leak in ("visibility", "freshness_confirmed_at", "agent_id", "fingerprint"):
        assert leak not in dumped
    assert {i.status for i in items} == {"live", "under_offer"}


async def test_public_list_unknown_or_hidden_agent_404():
    svc, _ = await make()
    for slug in ("nobody", "hidden"):
        with pytest.raises(ListingError) as e:
            await svc.public_list(slug)
        assert e.value.status_code == 404


async def test_public_list_paging():
    svc, _ = await make()
    ids = [(await live(svc, title=f"L{i}")).id for i in range(5)]
    page1, total = await svc.public_list("rahul", limit=2, offset=0)
    page2, _ = await svc.public_list("rahul", limit=2, offset=2)
    page3, _ = await svc.public_list("rahul", limit=2, offset=4)
    assert total == 5 and [len(p) for p in (page1, page2, page3)] == [2, 2, 1]
    assert [i.id for p in (page1, page2, page3) for i in p] == ids[::-1]  # newest published first
    assert (await svc.public_list("rahul", limit=2, offset=10))[0] == []


async def test_public_get():
    svc, _ = await make()
    pub = await live(svc)
    got = await svc.public_get(pub.id)
    assert got.id == pub.id and got.agent.slug == "rahul" and "visibility" not in got.model_dump()
    priv = await live(svc, visibility="private")
    draft = await svc.create("A1", ListingCreate(**FULL))
    paused = await live(svc)
    await svc.change_status("A1", paused.id, "paused")
    sold = await live(svc)
    await svc.change_status("A1", sold.id, "sold")
    for lid in (priv.id, draft.id, paused.id, sold.id, "missing"):
        with pytest.raises(ListingError) as e:
            await svc.public_get(lid)
        assert e.value.status_code == 404


async def test_public_get_hidden_agent_404():
    svc, db = await make()
    lst = await live(svc, agent="A3")
    with pytest.raises(ListingError):
        await svc.public_get(lst.id)
