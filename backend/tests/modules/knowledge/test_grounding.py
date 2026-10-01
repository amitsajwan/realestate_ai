import pytest

from app.modules.calendar.library import ENTRIES
from app.modules.knowledge import Ref, facts_for
from app.modules.knowledge.grounding import INTEREST, listing_grounding
from app.modules.showcase.samples import HOMES

from ..fakes import FakeDb

pytestmark = pytest.mark.asyncio

LISTING = {"_id": "L1", "agent_id": "A1", "title": "2 BHK in Kharadi", "transaction": "sale", "property_type": "apartment", "price_inr": 8_500_000, "city": "Pune",
           "locality": "Kharadi", "bhk": 2, "carpet_sqft": 1100, "super_built_up_sqft": 1400, "floor": 7, "total_floors": 20, "furnishing": "semi", "possession": "ready",
           "rera_no": "P52100012345", "amenities": ["Gym", "Lift"], "status": "live"}
ABOUT = {"project_name": "Green Park", "builder_known_as": "Sunrise Builders", "highlights": ["Corner unit", "Wide balcony"], "amenities": ["Clubhouse", "Gym"],
         "nearby": [{"type": "school", "name": "City School", "minutes": 8}, {"type": "hospital", "name": "Lotus Hospital"}],
         "connectivity": ["Close to the main road"], "water": "Municipal supply", "power_backup": "Lifts and common areas", "maintenance": "3 rupees per sq ft per month",
         "parking": "One covered slot", "possession_note": "As on the RERA page", "rera_note": "Registered", "society": "Registered society",
         "faq": [{"q": "Is the price negotiable?", "a": "The final price is discussed with the agent."}]}


async def test_a_listing_with_about_becomes_plain_sentences_faq_and_area_facts():
    db = FakeDb()
    db.get_collection("listings").docs.append({**LISTING, "about": ABOUT})
    g = await facts_for(Ref.listing("L1"), db)
    assert g.kind == "listing" and not g.sample and g.links["interest"] == INTEREST
    for s in ("The price is ₹85 Lakh.", "The carpet area is 1,100 sq ft.", "It is on floor 7 of 20.", "It is semi-furnished.", "It is ready to move.", "The RERA number is P52100012345.",
              "The project is Green Park.", "The builder is known as Sunrise Builders.", "Nearby school: City School, about 8 minutes away.", "Nearby hospital: Lotus Hospital.",
              "Maintenance: 3 rupees per sq ft per month.", "Parking: One covered slot.", "Water supply: Municipal supply.", "It is currently listed as available on our site.",
              "Amenities: Gym, Lift, Clubhouse."):
        assert s in g.facts, s
    assert g.faq == [{"q": "Is the price negotiable?", "a": "The final price is discussed with the agent."}]
    assert any("EON IT Park" in f for f in g.area_facts) and g.locality == "Kharadi" and any("Line 4" in f for f in g.area_facts)
    assert all(f.startswith("Check:") for f in g.advice)


async def test_a_listing_without_about_is_fine():
    db = FakeDb()
    db.get_collection("listings").docs.append(dict(LISTING))
    g = await facts_for(Ref.listing("L1"), db)
    assert "The carpet area is 1,100 sq ft." in g.facts and g.faq == [] and not any("Maintenance" in f for f in g.facts)
    g2 = listing_grounding({"_id": "L2", "title": "x", "about": None})  # an absent or null about never breaks
    assert g2.facts == [] and g2.area_facts == []


async def test_agent_text_with_a_phone_a_link_or_hype_is_dropped():
    about = {"maintenance": "call 9822012345", "water": "see www.example.com", "parking": "Best parking in Pune", "society": "Quiet society",
             "faq": [{"q": "Contact?", "a": "Call 9822012345"}]}
    g = listing_grounding({**LISTING, "about": about})
    text = " ".join(g.facts + [x["a"] for x in g.faq])
    assert "9822012345" not in text and "example" not in text and "Best" not in text and "Society: Quiet society." in g.facts and g.faq == []


async def test_a_stored_sample_listing_stays_a_sample():
    g = listing_grounding({**LISTING, "title": "Sample 2 BHK in Kharadi"})
    assert g.sample and "not available for sale" in g.facts[0] and not any("listed as available" in f for f in g.facts)
    assert any(f.startswith("The sample price figure is ₹85 Lakh") for f in g.facts)


async def test_every_showcase_sample_home_has_a_labelled_grounding():
    for h in HOMES:
        g = await facts_for(Ref.sample(h.slug))
        assert g.sample and g.kind == "sample" and "not available for sale" in g.facts[0]
        assert f"The carpet area is {h.carpet_text}." in g.facts and any(f"The sample price figure is {h.price_text}" in f for f in g.facts)
        assert not any(f.startswith("The price is") for f in g.facts)
        assert g.locality == h.locality
    assert await facts_for(Ref.sample("nope")) is None


async def test_an_area_grounding_has_the_curated_facts_and_no_prices():
    g = await facts_for(Ref.area("upper-kharadi"))
    assert g.kind == "area" and g.subject == "Upper Kharadi, Pune" and any("eastern corridor" in f for f in g.facts) and g.area_facts == []
    assert await facts_for(Ref.area("Baner")) is None
    assert not any("₹" in f for f in g.facts)


async def test_a_calendar_item_uses_its_verified_library_text_and_review_note():
    e = ENTRIES[0]
    db = FakeDb()
    db.get_collection("content_calendar").docs.append({"_id": "C1", "slug": e.slug, "kind": "post", "caption": "ignored caption #tag", "status": "published"})
    g = await facts_for(Ref.calendar("C1"), db)
    assert g.kind == "post" and g.subject == e.title and g.sources == [e.review] and g.facts
    assert not any(f.endswith("?") for f in g.facts) and not any("#" in f for f in g.facts)
    assert any("MahaRERA" in f for f in g.facts)


async def test_a_calendar_item_without_a_library_entry_uses_its_caption_and_a_showcase_item_its_home():
    db = FakeDb()
    c = db.get_collection("content_calendar")
    c.docs.append({"_id": "C2", "slug": "newsroom-1", "kind": "post", "caption": "Kharadi homes: check the RERA page first. \U0001F3E0\nHave you checked? #Pune https://x.example/y", "status": "published"})
    c.docs.append({"_id": "C3", "slug": HOMES[0].slug, "kind": "showcase", "caption": "", "status": "published"})
    g = await facts_for(Ref.calendar("C2"), db)
    assert g.facts == ["Kharadi homes: check the RERA page first."]
    s = await facts_for(Ref.calendar("C3"), db)
    assert s.sample and s.locality == HOMES[0].locality
    assert await facts_for(Ref.calendar("missing"), db) is None and await facts_for(Ref.listing("missing"), db) is None


async def test_free_text_and_dict_refs():
    g = await facts_for(Ref.text("Two metro lines have been approved. Is it running?"))
    assert g.facts == ["Two metro lines have been approved."]
    assert (await facts_for({"area": "wagholi"})).subject == "Wagholi, Pune"
    assert await facts_for(("sample", HOMES[1].slug)) is not None
    with pytest.raises(ValueError):
        await facts_for({"nothing": 1})
