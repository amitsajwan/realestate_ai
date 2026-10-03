import pytest

from app.modules.agentprojects import cards
from app.modules.agentprojects.service import public_view

AGENT = {"name": "House Deal", "phone_display": "74472 12121", "primary": "#004274"}


def doc(slug="goyal-my-home", **kw):
    d = {"_id": slug, "slug": slug, "name": "Goyal My Home, Upper Kharadi", "builder": "Goyal Properties",
         "locality": "Upper Kharadi", "rera_no": "P52100078796", "possession_target": "2028-03",
         "positioning": "One tower of 143 homes on Nagar Road, next to Decathlon Kharadi.",
         "who_it_suits": ["Buyers who want Upper Kharadi", "Large 2 BHK buyers near ₹1 crore"],
         "configurations": [{"label": "2 BHK", "bhk": 2, "carpet_sqft": 941, "price_inr": 9700000, "source": "agent"},
                            {"label": "3 BHK", "bhk": 3, "carpet_sqft": 1205, "price_inr": 12500000, "source": "agent"}],
         "media": [{"url": "/area/wtc-kharadi.jpg", "caption": "WTC", "credit": "Photo: DesiBoy101, CC BY 4.0, Wikimedia Commons",
                    "artist_impression": False, "kind": "image"}],
         "rera": {"regno": "P52100078796", "name": "MY HOME UPPER KHARADI", "promoter": "GODIVA PROMOTERS LLP",
                  "completion_at_registration": "2028-12-31", "completion_now": "2029-04-30", "units_total": 143,
                  "units_booked": 102, "url": "u", "checked_at": "2026-10-03"}}
    d.update(kw)
    return public_view(d)


def test_project_carousel_passes_layout_checks_and_carries_the_facts():
    slides = cards.project_carousel(doc(), AGENT)
    assert len(slides) == 5 and all(s.img.size == (1080, 1350) for s in slides)
    text = " ".join(i.text for s in slides for i in s.items)
    for want in ("₹97 L – ₹1.25 Cr", "71%", "P52100078796", "30 Apr 2029", "Mar 2028", "As quoted by House Deal",
                 "Area photo, not the project", "74472 12121", "Powered by Avasetu"):
        assert want in text, want


def test_no_carousel_without_a_maharera_reading():
    with pytest.raises(cards.CardProblem):
        cards.project_carousel(doc(rera=None), AGENT)


def test_comparison_never_calls_projects_new():
    ps = [doc(), doc("kosmic", name="Triaa Kosmic Kourtyard", locality="Wagholi")]
    slides = cards.compare_carousel(ps, AGENT, cards.area_label(ps))
    assert len(slides) == 4
    cover = " ".join(i.text for i in slides[0].items).lower()
    assert "2 projects" in cover and " new " not in f" {cover} "
    assert cards.area_label(ps) == "Upper Kharadi & Wagholi · Pune"
    with pytest.raises(cards.CardProblem):
        cards.compare_carousel(ps[:1], AGENT, "x")


def test_caption_states_sources_and_dates():
    c = cards.caption(doc(), AGENT)
    assert "MahaRERA P52100078796: completion date filed 30 Apr 2029, 71% of 143 homes booked (read on 3 Oct 2026)" in c
    assert "Prices as quoted by House Deal" in c and "#UpperKharadi" in c


def test_money_and_dates():
    assert cards.lakh(5999000) == "₹59.99 L" and cards.lakh(12500000) == "₹1.25 Cr" and cards.lakh(10000000) == "₹1 Cr"
    assert cards.day("2029-04-30") == "30 Apr 2029" and cards.day("2028-03") == "Mar 2028" and cards.day(None) == ""


def test_reel_scenes_carry_the_facts_and_no_phone_number():
    from app.modules.agentprojects import reel
    from app.modules.reels.compose import Renderer
    sc = reel.scenes(doc(), AGENT)
    text = " ".join((l if isinstance(l, str) else l.text) for s in sc for l in s.lines)
    assert "*71%* of 143 homes booked" in text and "*30 Apr 2029*" in text and "Comment *PRICE*" in text
    assert sc[0].badge == "AREA PHOTO, NOT THE PROJECT" and sc[0].image.name == "wtc-kharadi.jpg"
    Renderer(sc, end_card=False)  # raises on any phone number
