"""Problems seen in the first live campaign (2026-10-06): sales claims, 'only', 'tap', 'sample', Marathi misspellings,
a caption that opened with a different line than the card, English cards under a Marathi caption, no agent on the card."""
import pytest

from app.core import areas, brand
from app.modules.creative import copywriter, i18n, strategist
from app.modules.creative.guards import problems_in, repair
from app.modules.creative.layouts import render_layout
from app.modules.creative.layouts.base import violations
from app.modules.creative.models import CardBrand, Copy, Design

from .helpers import FakeLlm, build, simple_brief

FACTS = "EMI of ₹22,425 a month. Gulmohar City is 3 km from IndoSpace."


@pytest.mark.parametrize("text,why", [
    ("₹22,425 monthly EMI makes this plot affordable", "value claim"),
    ("Secure your land without overpaying", "value claim"),
    ("A budget-friendly plot", "value claim"),
    ("Tap to explore this plot", "tap or click"),
    ("Click the link", "tap or click"),
    ("Only 3 km to IndoSpace", "only/just"),
    ("फक्त 3 km", "only/just"),
    ("सिर्फ 3 km दूर", "only/just"),
    ("केवळ 3 km", "only/just"),
    ("हा प्लॉट परवडणारा आहे", "value claim"),
    ("सस्ता प्लॉट", "value claim"),
    ("तुमचे नवीन घर इथे", "promise"),
    ("आपका नया घर", "promise"),
    ("Build your new home here", "promise"),
    ("A sample listing", "sample"),
])
def test_sales_claims_are_refused_in_every_language(text, why):
    assert why in problems_in(text, FACTS)


def test_plain_facts_pass():
    for ok in ("EMI of ₹22,425 a month for this plot.", "Gulmohar City is 3 km from IndoSpace.", "Not only the price: check the NA order.",
               "गुलमोहर सिटी IndoSpace पासून 3 km.", "Ask what the price includes.", "Check every switch, tap and wall."):
        assert problems_in(ok, FACTS) == [], ok


def test_minimisers_are_repaired_not_just_refused():
    assert repair("Only 3 km to IndoSpace.") == "3 km to IndoSpace."
    assert repair("IndoSpace is just 3 km away.") == "IndoSpace is 3 km away."
    assert repair("IndoSpace फक्त 3 km.") == "IndoSpace 3 km."
    assert problems_in(repair("Just 3 km to work"), FACTS) == []


def test_marathi_spelling_is_fixed():
    assert i18n.fix_spelling("1.77 गुनथा प्लॉट रंजनगांवमध्ये", "mr") == "1.77 गुंठा प्लॉट रांजणगावमध्ये"
    assert i18n.fix_spelling("रांजनगाव, शिरुर", "mr") == "रांजणगाव, शिरूर"
    assert i18n.fix_spelling("रंजनगांव", "hi") == "रांजणगांव"
    assert i18n.fix_spelling("Ranjangaon गुंठा", "en") == "Ranjangaon गुंठा"


def test_every_area_and_nearby_town_has_a_marathi_and_hindi_spelling():
    names = [a.name for a in areas.AREAS] + ["Pune", "Ranjangaon", "Shikrapur", "Shirur"]
    for n in names:
        assert set(i18n.PLACES[n]) >= {"mr", "hi"}, n
    assert "Ranjangaon = रांजणगाव" in i18n.glossary("mr") and "guntha = गुंठा" in i18n.glossary("mr")


async def test_the_caption_opens_with_the_card_headline_whatever_the_model_writes():
    b = simple_brief()
    a = await strategist.plan(b, "buyer", "instagram", None, 0)
    c = await copywriter.write(a, b, FakeLlm({"first_line": "The biggest site-visit mistake buyers make.",
                                              "body": "Ask for the date in writing."}))
    assert copywriter.same_headline(c.caption_first_line, c.hook) and c.caption("instagram").startswith(c.hook)
    bad = Copy(c.hook, "", [], "Another line entirely.", "body", "Q?", ["#abc", "#abd", "#abe"])
    assert "the caption's first line is not the card's headline" in copywriter.review_copy(bad, b.corpus(), "instagram")


def test_a_number_card_does_not_ask_how_many_site_visits():
    assert "How many" not in copywriter.QUESTION["stat"]


AGENT = CardBrand("House Deal", "Call / WhatsApp +91 99219 93099", str(brand.MARK_PNG), phone="+91 99219 93099",
                  price="₹32.3 lakh", rera="P52100076768")


def _texts(r):
    return " | ".join(i.text for i in r.items)


@pytest.mark.parametrize("layout", ["big_number", "myth_fact", "poll", "quote_tip", "photo_led"])
def test_an_agents_single_card_carries_the_contact_strip(layout):
    copy, design, _ = build(layout)
    design.brand = AGENT
    for pal in ("navy_gold", "cream"):
        design.palette = pal
        [r] = render_layout(copy, design)
        t = _texts(r)
        for want in ("House Deal", "+91 99219 93099", "₹32.3 lakh", "P52100076768"):
            assert want in t, (layout, want)
        assert violations(r) == [] and not any(i.truncated for i in r.items), (layout, pal)
        assert brand.TAGLINE not in t


def test_an_agents_carousel_ends_with_a_contact_card_and_every_slide_names_the_agent():
    copy, design, _ = build("checklist")
    design.brand = AGENT
    slides = render_layout(copy, design)
    for r in slides:
        assert "+91 99219 93099" in _texts(r) and violations(r) == [] and not any(i.truncated for i in r.items)
    last = _texts(slides[-1])
    assert "₹32.3 lakh" in last and "P52100076768" in last and copy.cta_question not in last


def test_a_marathi_card_is_drawn_in_marathi():
    copy, design, _ = build("checklist")
    copy.language, copy.hook = "mr", "प्लॉटचे कागद तपासा"
    copy.slides = ["NA ऑर्डर", "7/12 उतारा", "मंजूर ले-आउट"]
    design.brand = AGENT
    slides = render_layout(copy, design)
    texts = " ".join(_texts(r) for r in slides)
    assert "पुढे पाहा" in texts and "कॉल / WhatsApp" in texts and "Swipe" not in texts
    for r in slides:
        assert violations(r) == [] and not any(i.truncated for i in r.items)
    copy2, d2, _ = build("myth_fact")
    copy2.language, copy2.payload["kicker"] = "mr", "गैरसमज विरुद्ध सत्य"
    [r] = render_layout(copy2, d2)
    assert "गैरसमज" in _texts(r) and "सत्य" in _texts(r) and "MYTH" not in _texts(r)
