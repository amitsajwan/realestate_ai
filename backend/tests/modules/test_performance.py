"""Property performance (contract section 3)."""
import pytest

from .reverse_helpers import add_lead, add_view, make

pytestmark = pytest.mark.asyncio


async def _items(svc, agent="A1"):
    return {i["listing_id"]: i for i in (await svc.performance(agent))["items"]}


async def test_empty_state():
    svc, _, _ = await make(with_listings=False)
    assert await svc.performance("A1") == {"items": []}


async def test_listings_without_activity_show_zeros():
    svc, _, _ = await make()
    items = await _items(svc)
    assert set(items) == {"L1", "L2", "L3", "L4", "L5", "L6"}  # A2's L7 never appears
    assert items["L1"] == {"listing_id": "L1", "title": "2BHK in Baner", "price_inr": 8_500_000, "status": "live",
                           "views": 0, "unique_visitors": 0, "enquiries": 0, "qualified": 0, "site_visits": 0,
                           "by_source": {}}
    assert items["L5"]["status"] == "draft"


async def test_views_and_unique_visitors():
    svc, db, clock = await make()
    for anon in ("anon-1", "anon-1", "anon-1", "anon-2"):
        await add_view(db, clock, "L1", anon)
    await add_view(db, clock, "L2", "anon-1")
    await add_view(db, clock, "L1", "anon-9", agent="A2")  # another agent's traffic
    await db.get_collection("events").insert_one({"agent_id": "A1", "anon_id": "anon-1", "type": "page_view",
                                                  "listing_id": "L1", "ts": clock()})  # not a listing view
    items = await _items(svc)
    assert (items["L1"]["views"], items["L1"]["unique_visitors"]) == (4, 2)
    assert (items["L2"]["views"], items["L2"]["unique_visitors"]) == (1, 1)


async def test_enquiries_qualified_site_visits_and_sources():
    svc, db, clock = await make()
    await add_lead(db, clock, "c1", first_listing="L1", source="whatsapp", base=40)                    # hot -> qualified
    await add_lead(db, clock, "c2", first_listing="L1", source="instagram", lo=5_000_000, hi=8_000_000)  # budget -> qualified
    await add_lead(db, clock, "c3", first_listing="L1", source="whatsapp", timeline="now")               # timeline -> qualified
    await add_lead(db, clock, "c4", first_listing="L1", source=None)                                     # nothing -> not
    await add_lead(db, clock, "c5", first_listing="L1", source="whatsapp", stage="site_visit")
    await add_lead(db, clock, "c6", first_listing="L1", stage="negotiating", base=20)                    # warm
    await add_lead(db, clock, "c7", first_listing="L1", stage="won")
    await add_lead(db, clock, "c8", first_listing="L1", stage="contacted")   # not a site visit
    await add_lead(db, clock, "c9", first_listing="L1", stage="lost")        # enquiry, no visit
    await add_lead(db, clock, "x1", first_listing="L2", source="facebook")
    await add_lead(db, clock, "x2", first_listing="L1", agent="A2", source="whatsapp")  # other agent
    await add_lead(db, clock, "x3", first_listing=None)                                # no listing
    await add_lead(db, clock, "x4", first_listing="GONE")                              # unknown listing
    items = await _items(svc)
    l1 = items["L1"]
    assert l1["enquiries"] == 9
    assert l1["qualified"] == 4  # c1 c2 c3 c6
    assert l1["site_visits"] == 3  # c5 c6 c7
    assert l1["by_source"] == {"whatsapp": 3, "instagram": 1, "direct": 5}
    assert items["L2"]["enquiries"] == 1 and items["L2"]["by_source"] == {"facebook": 1}


async def test_qualified_uses_decayed_score():
    svc, db, clock = await make()
    # base 40 but 20 days idle: 40 * 0.4 = 16 -> still warm (>= 15)
    await add_lead(db, clock, "old", first_listing="L1", base=40, last_activity_days_ago=20)
    # base 30 idle 20 days: 12 -> cold and no stated info -> not qualified
    await add_lead(db, clock, "older", first_listing="L1", base=30, last_activity_days_ago=20)
    assert (await _items(svc))["L1"]["qualified"] == 1


async def test_sorted_by_enquiries_then_views():
    svc, db, clock = await make()
    await add_lead(db, clock, "c1", first_listing="L3")
    await add_lead(db, clock, "c2", first_listing="L3")
    await add_lead(db, clock, "c3", first_listing="L2")
    for _ in range(3):
        await add_view(db, clock, "L1", "anon-1")
    await add_view(db, clock, "L4", "anon-1")
    order = [i["listing_id"] for i in (await svc.performance("A1"))["items"]]
    assert order[:4] == ["L3", "L2", "L1", "L4"]
    assert set(order[4:]) == {"L5", "L6"}


async def test_owner_isolation():
    svc, db, clock = await make()
    await add_lead(db, clock, "c1", first_listing="L1")
    await add_view(db, clock, "L1", "anon-1")
    items = await _items(svc, "A2")
    assert set(items) == {"L7"} and items["L7"]["views"] == 0 and items["L7"]["enquiries"] == 0
