"""An agent's campaign: their name, logo and phone on the cards, a code-made contact block in every caption, and Marathi
posts whose numbers can never change in translation."""
import json
from pathlib import Path

from app.core import brand
from app.modules.creative import translate
from app.modules.creative.layouts import render_layout
from app.modules.creative.layouts.base import DEVANAGARI_FONTS, card, load_font
from app.modules.creative.models import Brief, CardBrand, Copy, Design
from app.modules.propertyfacts import identity, jobs

from .test_jobs import LISTING, setup

HD = {"agent_id": "a1", "slug": "house-deal", "phone": "+919921993099",
      "branding_data": {"business_name": "House Deal", "logo": "/uploads/images/hd.jpg", "website": "https://house-deal.com/",
                        "tagline": "Your Dream Home, Our Best Deal"}}


def test_identity_of_an_agent_and_of_our_own_page():
    who = identity.identity(HD, "https://avasetu.in", Path("/srv/uploads"), "mr")
    assert who.voice.name == "House Deal" and who.voice.team == "House Deal team"
    assert who.card_brand == CardBrand("House Deal", "Call +91 99219 93099", str(Path("/srv/uploads/images/hd.jpg")))
    assert who.contact == ["\U0001F4DE कॉल / WhatsApp: +91 99219 93099", "\U0001F310 वेबसाइट: house-deal.com",
                           "\U0001F3E0 Avasetu वर: avasetu.in/agent/house-deal"]
    ours = identity.identity({**HD, "slug": "avasetu"}, "https://avasetu.in", Path("/srv"), "en")
    assert ours.voice is None and ours.card_brand is None and ours.contact == []
    assert identity.identity(None, "https://avasetu.in", Path("/srv")).card_brand is None


def _copy(**kw):
    base = dict(hook="₹32.3 lakh for a plot in Gulmohar City", support="A 1,927 sq ft plot", slides=[],
                caption_first_line="₹32.3 lakh for a plot in Gulmohar City.", body="Listed at ₹32.3 lakh.",
                cta_question="What would you check first?", hashtags=["#Ranjangaon"], card_cta="Save this",
                payload={"kicker": "GULMOHAR CITY", "value": "₹32.3 lakh", "label": "for this plot", "fmt": "stat"})
    base.update(kw)
    return Copy(**base)


class Translator:
    def __init__(self, fn):
        self.fn = fn

    async def json(self, system, user):
        return self.fn(json.loads(user)) if "translate one social post" in system else None


async def test_a_translation_keeps_every_number_or_is_not_used():
    brief = Brief(topic="Price", facts=["A 1,927 sq ft plot at Gulmohar City is listed at ₹32.3 lakh."], language="mr")
    good = await translate.translate(_copy(), brief, Translator(lambda s: {
        **s, "hook": "गुलमोहर सिटीत प्लॉट ₹32.3 lakh", "first_line": "गुलमोहर सिटीत प्लॉट ₹32.3 lakh.",
        "payload": {**s["payload"], "label": "या प्लॉटसाठी"}}))
    assert good.language == "mr" and good.hook == "गुलमोहर सिटीत प्लॉट ₹32.3 lakh" and good.payload["label"] == "या प्लॉटसाठी"
    assert good.payload["value"] == "₹32.3 lakh" and good.hashtags == ["#Ranjangaon"]
    bad = await translate.translate(_copy(), brief, Translator(lambda s: {
        **s, "hook": "गुलमोहर सिटीत प्लॉट ₹30 lakh", "first_line": "प्लॉट ₹३२.३ lakh.", "body": "सर्वोत्तम प्लॉट, best deal"}))
    assert bad.hook == _copy().hook and bad.caption_first_line == _copy().caption_first_line and bad.body == _copy().body
    assert bad.language == "en"                                      # nothing usable came back: the post stays English
    same = await translate.translate(_copy(), Brief(topic="x", language="en"), Translator(lambda s: 1 / 0))
    assert same == _copy()


def test_marathi_cards_use_the_devanagari_font_and_the_agents_footer(tmp_path):
    assert Path(load_font(30).path).name.startswith("Poppins")
    with card(devanagari=True):
        assert Path(load_font(30, "bold").path).name == DEVANAGARI_FONTS["bold"]
    copy = _copy(hook="गुलमोहर सिटीत प्लॉट", language="mr")
    agent = CardBrand("House Deal", "Call +91 99219 93099", str(brand.MARK_PNG))
    [r] = render_layout(copy, Design(layout="big_number", palette="navy", brand=agent))
    footer = [i.text for i in r.items if i.role == "brand"]
    assert "House Deal" in footer and "Call +91 99219 93099" in footer and brand.NAME not in footer


async def test_an_agents_marathi_campaign(tmp_path):
    db, runs, _, _ = await setup(tmp_path)
    await db.get_collection("agent_public_profiles").update_one({"agent_id": "a1"}, {"$set": HD})
    runs.llm_factory = lambda: Translator(lambda s: {**s, "first_line": "मराठी: " + s["first_line"]})
    doc, created = await runs.create("a1", "L1", language="mr")
    assert created and doc["language"] == "mr"
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    assert d["status"] == "done" and len(d["posts"]) >= 10 and jobs.run_out(d)["language"] == "mr"
    for p in d["posts"]:
        assert "+91 99219 93099" in p["caption"] and "house-deal.com" in p["caption"] and "avasetu.in/agent/house-deal" in p["caption"]
        assert "House Deal team" in p["caption"] or p["caption"].startswith("मराठी: ")
    assert sum(p["caption"].startswith("मराठी: ") for p in d["posts"]) >= 8
    assert any("card_translator@2/listing" in p["prompts"] for p in d["posts"])
    _, created = await runs.create("a1", "L1", language="en")      # another language makes a new run
    assert created
    assert LISTING["_id"] == "L1"


def test_claims_seen_live_are_refused_unless_the_facts_say_so():
    from app.modules.creative.guards import problems_in
    facts = "A 1,927 sq ft plot at Gulmohar City is listed at ₹32.3 lakh. EMI of ₹22,425 a month."
    for line in ("₹22,425 monthly EMI makes this plot affordable.", "Is this the right investment for you?",
                 "Secure your land without overpaying.", "तुमच्या जीवनशैलीला बसणारा आकार", "सर्व खर्च आधीच दाखवले आहेत.",
                 "निश्चित 2029 तारीख", "साइट व्हिजिटची सर्वात मोठी चूक"):
        assert any(p.startswith("claim not in facts") for p in problems_in(line, facts)), line
    assert problems_in("A 1,927 sq ft plot listed at ₹32.3 lakh.", facts) == []


def test_property_posts_ask_a_question_that_fits_and_the_link_line_is_in_the_posts_language():
    from app.modules.creative import copywriter, strategist
    from app.modules.propertyfacts import campaign
    from .test_campaign import gulmohar
    for aid, brief in campaign.plan(gulmohar()):
        copy = copywriter.rule_copy(strategist.rule_angle(brief, "buyer", "instagram", 0, []), brief)
        assert "How many did you do" not in copy.cta_question, aid
    mr = dict(campaign.plan(gulmohar(), language="mr"))["price_reveal"]
    assert mr.link_line == "Gulmohar City, Ranjangaon ची संपूर्ण माहिती आणि MahaRERA नोंद: बायोमधील लिंक."


async def test_a_rate_limited_translation_is_asked_again(monkeypatch):
    monkeypatch.setattr(translate, "RETRY_WAITS", (0, 0))
    calls = []

    def flaky(s):
        calls.append(1)
        return None if len(calls) < 3 else {**s, "hook": "गुलमोहर सिटीत प्लॉट ₹32.3 lakh"}
    brief = Brief(topic="Price", facts=["A plot at Gulmohar City is listed at ₹32.3 lakh."], language="mr")
    out = await translate.translate(_copy(), brief, Translator(flaky))
    assert len(calls) == 3 and out.hook == "गुलमोहर सिटीत प्लॉट ₹32.3 lakh" and out.language == "mr"
