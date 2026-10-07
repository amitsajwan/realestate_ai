"""LC-1: a Brief built from a listing document carries the listing's facts, and the number guard treats them as given."""
from app.modules.creative import pipeline
from app.modules.creative.guards import problems_in
from app.modules.creative.listing_brief import brief_from_listing, price_label

LISTING = {
    "title": "2 BHK in Sample Heights, Kharadi",
    "transaction": "sale", "property_type": "apartment", "price_inr": 8500000, "bhk": 2.0, "carpet_sqft": 1050,
    "locality": "Kharadi", "city": "Pune", "project_name": "Sample Heights", "rera_no": "P52100012345",
    "amenities": ["Gym", "Clubhouse", "Covered parking"],
    "media": [{"url": "https://cdn.example/u/2026/10/b.jpg", "order": 1}, {"url": "https://cdn.example/u/2026/10/a.jpg", "order": 0}],
}


def test_price_labels():
    assert price_label(8500000) == "₹85 lakh"
    assert price_label(8550000) == "₹85.5 lakh"
    assert price_label(12500000) == "₹1.25 crore"
    assert price_label(25000, "rent") == "₹25,000 a month"


def test_listing_fields_are_carried():
    b = brief_from_listing(LISTING)
    assert b.listing_price_inr == "₹85 lakh" and b.listing_bhk == "2 BHK" and b.listing_carpet_sqft == "1,050 sq ft carpet"
    assert b.listing_rera_no == "P52100012345" and b.listing_project_name == "Sample Heights"
    assert b.listing_media_refs == ["https://cdn.example/u/2026/10/a.jpg", "https://cdn.example/u/2026/10/b.jpg"]
    assert "stat" in b.formats() and "carousel" in b.formats()


def test_guard_accepts_listing_facts_and_rejects_others():
    corpus = brief_from_listing(LISTING).corpus()
    assert problems_in("2 BHK in Kharadi at ₹85 lakh, 1,050 sq ft carpet.", corpus) == []
    assert any("number not in facts" in p for p in problems_in("2 BHK at ₹90 lakh.", corpus))
    assert any("number not in facts" in p for p in problems_in("Only 2026 buyers.", corpus))  # media URL digits are not facts


def test_sparse_listing_invents_nothing():
    b = brief_from_listing({"transaction": "rent", "property_type": "plot", "locality": "Wagholi"})
    assert b.facts == ["Plot for rent in Wagholi."]
    assert b.stat_value == "" and b.formats() == ["single"]
    assert "price" in problems_in("Plot at ₹40 lakh", b.corpus())


async def test_pipeline_pack_from_listing_passes_the_guard(tmp_path):
    b = brief_from_listing(LISTING)
    for seed in range(3):
        pack = await pipeline.make(b, "buyer", "instagram", None, seed=seed, out_dir=tmp_path, reviewer=None)
        assert pack.report["ok"], pack.report
        assert problems_in(pack.caption, b.corpus()) == []
