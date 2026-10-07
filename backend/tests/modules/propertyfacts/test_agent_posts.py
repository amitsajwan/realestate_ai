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
    assert who.card_brand == CardBrand("House Deal", "कॉल / WhatsApp +91 99219 93099", str(Path("/srv/uploads/images/hd.jpg")),
                                       phone="+91 99219 93099")
    assert identity.identity(HD, "https://avasetu.in", Path("/srv"), "en").card_brand.line == "Call / WhatsApp +91 99219 93099"
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


def marathi(src):
    """A stand-in translation: every text marked as Marathi, numbers untouched."""
    if isinstance(src, str):
        return "मराठी: " + src
    if isinstance(src, list):
        return [marathi(s) for s in src]
    if isinstance(src, dict):  # a big number ("1.77 guntha") keeps its length: the stand-in prefix would not fit
        return {k: v if k == "value" else marathi(v) for k, v in src.items()}
    return src


class Translator:
    def __init__(self, fn):
        self.fn = fn

    async def json(self, system, user):
        return self.fn(json.loads(user)) if "translate one social post" in system else None


MR = {"hook": "गुलमोहर सिटीत प्लॉट ₹32.3 lakh", "support": "1,927 sq ft चा प्लॉट", "body": "किंमत ₹32.3 lakh.",
      "question": "तुम्ही आधी काय तपासाल?", "payload": {"label": "या प्लॉटसाठी", "value": "₹32.3 lakh"}}


async def test_a_translation_keeps_every_number_or_is_not_used():
    brief = Brief(topic="Price", facts=["A 1,927 sq ft plot at Gulmohar City is listed at ₹32.3 lakh."], language="mr",
                  kicker="GULMOHAR CITY")
    good = await translate.translate(_copy(), brief, Translator(lambda s: {**s, **MR, "first_line": "a model's own first line"}))
    assert good.language == "mr" and good.hook == MR["hook"] and good.payload["label"] == "या प्लॉटसाठी"
    assert good.caption_first_line == MR["hook"] + "."                 # the first line IS the card's headline
    assert good.payload["value"] == "₹32.3 lakh" and good.hashtags == ["#Ranjangaon"]
    assert good.payload["kicker"] == "GULMOHAR CITY" and good.card_cta == "सेव्ह करा"   # code's own words, not the model's
    bad = await translate.translate(_copy(), brief, Translator(lambda s: {
        **s, **MR, "hook": "गुलमोहर सिटीत प्लॉट ₹30 lakh", "body": "सर्वोत्तम प्लॉट, best deal"}))
    assert bad == _copy()                                            # a wrong number: the post stays wholly English
    half = await translate.translate(_copy(), brief, Translator(lambda s: {**s, **MR, "body": s["body"] + " Ask what it includes."}))
    assert half == _copy()                                           # an English body under Marathi cards is never made
    claim = await translate.translate(_copy(), brief, Translator(lambda s: {**s, **MR, "body": "हा प्लॉट परवडणारा आहे: ₹32.3 lakh."}))
    assert claim == _copy()                                          # a sales claim added in translation is refused
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
    runs.llm_factory = lambda: Translator(marathi)
    doc, created = await runs.create("a1", "L1", language="mr")
    assert created and doc["language"] == "mr"
    await runs.run_once()
    d = await runs.latest("a1", "L1")
    assert d["status"] == "done" and len(d["posts"]) >= 10 and jobs.run_out(d)["language"] == "mr"
    for p in d["posts"]:
        assert "+91 99219 93099" in p["caption"] and "house-deal.com" in p["caption"] and "avasetu.in/agent/house-deal" in p["caption"]
        assert p["caption"].startswith("मराठी: ") and ("खाली सांगा" in p["caption"] or "कमेंटमध्ये" in p["caption"])
        assert "card_translator@3/listing" in p["prompts"]
    _, created = await runs.create("a1", "L1", language="en")      # another language makes a new run
    assert created
    assert LISTING["_id"] == "L1"
