"""Golden set for the deterministic extractor (no network). Requires >= 90% field accuracy overall."""
import pytest

from app.modules.ai_listing.service import AIListingService

pytestmark = pytest.mark.asyncio

L, CR = 100_000, 10_000_000
S, R = "sale", "rent"

GOLDEN = [
    ("2 BHK in Baner, 1100 sq ft carpet, 85 lakh, ready possession, near Balewadi high street, 3rd floor of 12, semi furnished",
     dict(price_inr=85 * L, bhk=2, carpet_sqft=1100, locality="Baner", transaction=S, floor=3, total_floors=12,
          furnishing="semi", possession="ready", city="Pune")),
    ("3BHK flat for sale in Wakad Pune 1.25 Cr, 1450 sqft SBA, 7th floor",
     dict(price_inr=125 * L, bhk=3, super_built_up_sqft=1450, locality="Wakad", transaction=S, floor=7, property_type="apartment")),
    ("1 BHK for rent in Kothrud, 25k per month, semi furnished",
     dict(price_inr=25000, bhk=1, locality="Kothrud", transaction=R, furnishing="semi")),
    ("2 BHK for rent Hinjewadi 28,000/month furnished 950 sq ft",
     dict(price_inr=28000, bhk=2, carpet_sqft=950, locality="Hinjewadi", transaction=R, furnishing="furnished")),
    ("do bhk flat kiraye pe hai Aundh mein, 30 hazaar mahina, semi furnished",
     dict(price_inr=30000, bhk=2, locality="Aundh", transaction=R)),
    ("Baner mein 3 bhk bechna hai, 1.8 crore, 1500 sq ft carpet",
     dict(price_inr=180 * L, bhk=3, carpet_sqft=1500, locality="Baner", transaction=S)),
    ("बाणेर में २ बीएचके फ्लैट बिक्री के लिए, ८५ लाख, ११०० स्क्वेयर फीट कारपेट",
     dict(price_inr=85 * L, bhk=2, carpet_sqft=1100, locality="Baner", transaction=S)),
    ("वाकड मध्ये ३ बीएचके फ्लॅट विक्रीसाठी, १ कोटी २५ लाख, १३०० चौरस फूट",
     dict(price_inr=125 * L, bhk=3, carpet_sqft=1300, locality="Wakad", transaction=S)),
    ("कोथरूड मध्ये दो बीएचके किराये पर, पच्चीस हजार प्रति माह",
     dict(price_inr=25000, bhk=2, locality="Kothrud", transaction=R)),
    ("पुणे में बालेवाडी ३ बीएचके, पचासी लाख, १२०० स्क्वेअर फूट",
     dict(price_inr=85 * L, bhk=3, carpet_sqft=1200, locality="Balewadi", transaction=S, city="Pune")),
    ("हिंजवडी मध्ये २ बीएचके भाड्याने, वीस हजार",
     dict(price_inr=20000, bhk=2, locality="Hinjewadi", transaction=R)),
    ("Plot for sale in Wagholi 2000 sq ft, 45 lakh",
     dict(price_inr=45 * L, carpet_sqft=2000, locality="Wagholi", transaction=S, property_type="plot")),
    ("200 sq yd plot in Kharghar for sale 1.1 crore",
     dict(price_inr=110 * L, carpet_sqft=1800, locality="Kharghar", transaction=S, property_type="plot")),
    ("Commercial shop for rent in Viman Nagar, 400 sq ft, Rs 60,000 per month",
     dict(price_inr=60000, carpet_sqft=400, locality="Viman Nagar", transaction=R, property_type="shop")),
    ("Office space for sale in Kharadi, 1500 sq ft carpet, 2.1 cr, 5th floor of 9",
     dict(price_inr=210 * L, carpet_sqft=1500, locality="Kharadi", transaction=S, property_type="office", floor=5, total_floors=9)),
    ("1 RK for rent in Andheri 18000 per month",
     dict(price_inr=18000, bhk=1, locality="Andheri", transaction=R, city="Mumbai")),
    ("Studio in Bandra West for rent Rs 65,000/month furnished",
     dict(price_inr=65000, locality="Bandra", transaction=R, furnishing="furnished")),
    ("3 BHK, Whitefield Bangalore, 1.35 Cr, 1650 sqft super built up, 10th floor, ready to move",
     dict(price_inr=135 * L, bhk=3, super_built_up_sqft=1650, locality="Whitefield", transaction=S, floor=10,
          possession="ready", city="Bengaluru")),
    ("2bhk HSR Layout Bengaluru 95 lac carpet 900 sq.ft",
     dict(price_inr=95 * L, bhk=2, carpet_sqft=900, locality="HSR Layout", transaction=S)),
    ("Gachibowli 3 BHK gated community 1.6 cr sale 1800 sft",
     dict(price_inr=160 * L, bhk=3, carpet_sqft=1800, locality="Gachibowli", transaction=S, city="Hyderabad")),
    ("2 BHK apartment Dwarka Delhi 1.1 Cr, 850 sqft carpet, 4/6 floor, RERA P52100012345",
     dict(price_inr=110 * L, bhk=2, carpet_sqft=850, locality="Dwarka", transaction=S, floor=4, total_floors=6,
          rera_no="P52100012345", city="Delhi")),
    ("Rs 85,00,000 2 BHK Kondhwa, 750 sq ft carpet, under construction, possession Dec 2026",
     dict(price_inr=85 * L, bhk=2, carpet_sqft=750, locality="Kondhwa", possession="2026-12")),
    ("3 bhk villa in Bavdhan 3.2 crore 2400 sq ft carpet 3000 sq ft super built up",
     dict(price_inr=320 * L, bhk=3, carpet_sqft=2400, super_built_up_sqft=3000, locality="Bavdhan", property_type="villa")),
    ("Independent house Chennai Adyar, 2200 sqft, 4.5 Cr",
     dict(price_inr=450 * L, carpet_sqft=2200, locality="Adyar", property_type="house", city="Chennai")),
    ("Flat for rent in Velachery, 2BHK, 22k, unfurnished",
     dict(price_inr=22000, bhk=2, locality="Velachery", transaction=R, furnishing="unfurnished")),
    ("Powai 2 BHK 2.4 Cr 1050 sq ft",
     dict(price_inr=240 * L, bhk=2, carpet_sqft=1050, locality="Powai", transaction=S)),
    ("1.5 BHK Thane West 68 L carpet 620",
     dict(price_inr=68 * L, bhk=1.5, carpet_sqft=620, locality="Thane West", transaction=S)),
    ("Sector 150 Noida 3 BHK 1.4 Cr 1750 sq ft",
     dict(price_inr=140 * L, bhk=3, carpet_sqft=1750, locality="Sector 150", city="Noida")),
    ("Sale: 4 BHK penthouse Juhu 12 Cr, 3500 sq ft carpet",
     dict(price_inr=1200 * L, bhk=4, carpet_sqft=3500, locality="Juhu", transaction=S, property_type="apartment")),
    ("Rent 3 BHK Koregaon Park 85,000 per month, 1800 sqft, fully furnished, 2 covered parking",
     dict(price_inr=85000, bhk=3, carpet_sqft=1800, locality="Koregaon Park", transaction=R, furnishing="furnished")),
    ("Land for sale Nashik 5 guntha 30 lakh",
     dict(price_inr=30 * L, carpet_sqft=5445, transaction=S, property_type="plot", city="Nashik")),
    ("3 BHK flat available at Rohan Heights, Pashan Pune. 1350 sq ft SBA, 1.55 Cr, RTM",
     dict(price_inr=155 * L, bhk=3, super_built_up_sqft=1350, locality="Pashan", project_name="Rohan Heights",
          possession="ready")),
    ("किराये पर २ बीएचके, कल्याणी नगर, ३५ हजार महीना",
     dict(price_inr=35000, bhk=2, locality="Kalyani Nagar", transaction=R)),
    ("Balewadi me 2 bhk 1.05 crore mein, 980 sq ft carpet, ready to move",
     dict(price_inr=105 * L, bhk=2, carpet_sqft=980, locality="Balewadi", transaction=S, possession="ready")),
    ("Shop for sale Lajpat Nagar Delhi 300 sq ft 1.8 crore ground floor",
     dict(price_inr=180 * L, carpet_sqft=300, locality="Lajpat Nagar", transaction=S, property_type="shop", floor=0)),
    ("2 BHK for lease in Madhapur, 32,000 per month, 1200 sqft",
     dict(price_inr=32000, bhk=2, carpet_sqft=1200, locality="Madhapur", transaction=R)),
    ("Security deposit 2 lakh. 2 BHK rent Baner 30k, parking, lift, gym",
     dict(price_inr=30000, bhk=2, locality="Baner", transaction=R)),
    ("Pune Hadapsar 3 BHK ready flat 78 lakh 1250 sq ft carpet top floor of 7",
     dict(price_inr=78 * L, bhk=3, carpet_sqft=1250, locality="Hadapsar", floor=7, total_floors=7, city="Pune")),
]


async def _run(text):
    return await AIListingService().from_text(text)


async def test_golden_set_accuracy():
    assert len(GOLDEN) >= 30
    total = ok = 0
    failures = []
    for text, exp in GOLDEN:
        res = await _run(text)
        for k, v in exp.items():
            total += 1
            got = res.draft.get(k)
            if got == v:
                ok += 1
            else:
                failures.append(f"{k}: expected {v!r} got {got!r} | {text[:70]}")
    acc = ok / total
    print(f"\nGOLDEN: {len(GOLDEN)} cases, {ok}/{total} fields = {acc:.1%}")
    for f in failures:
        print("  FAIL", f)
    assert acc >= 0.90, f"accuracy {acc:.1%}\n" + "\n".join(failures)


@pytest.mark.parametrize("text", ["", "   ", "asdf qwerty zzz", "!!!???", "\x00\x01", "😀😀😀", "a" * 20000])
async def test_garbage_input_returns_empty_draft(text):
    res = await _run(text)
    assert res.draft.get("price_inr") is None
    assert "price_inr" in res.missing and "city" in res.missing and "title" in res.missing
