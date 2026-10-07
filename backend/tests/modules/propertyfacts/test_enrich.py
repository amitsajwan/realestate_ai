"""gather_project: a registered project's facts with no listing, kept like a listing's, without losing an agent's offer."""
from app.modules.propertyfacts import gather as gather_mod
from app.modules.propertyfacts.enrich import gather_project

from .test_register_and_store import RECORD, NOW, Register, WithRegister
from .test_registration import LISTING


async def test_a_project_without_a_listing_gets_a_kept_sheet():
    f = WithRegister(Register(RECORD))
    out = await gather_project(None, "p52100076768", "Gulmohar City", "Ranjangaon", now=NOW, clients=f)
    assert out["key"] == "P52100076768" and "our register" in out["match"]
    v = out["view"]
    assert v["maharera"]["completion_now"] == "2029-04-30" and v["nearby"] and "offer" not in v
    assert not any(isinstance(c, int) for c in f.calls)              # fresh register details: MahaRERA not asked


async def test_regathering_keeps_the_agents_offer():
    f = WithRegister(Register(RECORD))
    await gather_mod.gather({**LISTING, "id": "L1", "price_inr": 3230000, "carpet_sqft": 1927}, f, NOW)
    out = await gather_project(None, "P52100076768", "Gulmohar City", "Ranjangaon", now=NOW, clients=f)
    offer = out["view"]["offer"]
    assert offer["price_inr"] == 3230000 and offer["plot_sqft"] == 1927 and offer["source"] == "the agent's listing"
    assert (await f.facts_store.get("P52100076768"))["listing_id"] == "L1"
    assert out["view"]["numbers"]["price_per_sqft"] == 1676


async def test_nothing_found_returns_no_view_and_notes():
    f = WithRegister(Register(), page="", nominatim=None)
    out = await gather_project(None, "P52100099999", "Unknown Heights", "Nowhere", now=NOW, clients=f)
    assert out["notes"] and (out["view"] is None or "maharera" not in out["view"])
