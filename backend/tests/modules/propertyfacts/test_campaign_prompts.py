"""PM-3: golden test for the listing prompts on Gulmohar City. A fake LLM tries every way a model goes wrong on a property
post; the guards must keep all of it out of the published copy, while a clean reply that uses the listed price is kept."""
from app.modules.creative import pipeline
from app.modules.propertyfacts import campaign

from ..creative.helpers import FakeLlm
from .test_campaign import gulmohar

BAD_STRATEGY = {"pain": "wants a plot", "idea": "cheap plot", "hook": "Best plot in Ranjangaon for ₹25 lakh",
                "pattern": "number", "proof": [], "format": "stat", "cta": "Call now"}
BAD_COPY = {
    "support": "The dream plot you deserve.",                                        # superlative
    "first_line": "Gulmohar City by Kolte Patil Developers, listed at ₹32.3 lakh.",  # builder not in the facts
    "body": "Prices will rise by 20% by 2027.",                                      # prediction, invented numbers
    "question": "Call 9876543210 to book?",                                          # phone number
    "hashtags": ["#Ranjangaon", "#PlotsInPune", "#MahaRERA"],
}
LEAKS = ("Best plot", "25 lakh", "dream", "Kolte", "20%", "2027", "9876543210")


def price_reveal():
    return dict(campaign.plan(gulmohar()))["price_reveal"]


def test_campaign_briefs_are_listing_mode_set_in_their_area():
    for aid, brief in campaign.plan(gulmohar()):
        assert brief.mode == "listing" and brief.voice.areas == "Ranjangaon, Pune", aid


async def test_the_model_is_sent_the_listing_prompts(tmp_path):
    llm = FakeLlm()
    await pipeline.make(price_reveal(), "buyer", "instagram", llm, out_dir=tmp_path, reviewer=None)
    strategist_sys, copywriter_sys = llm.calls[0][1], llm.calls[1][1]
    for system in (strategist_sys, copywriter_sys):
        assert "Ranjangaon, Pune" in system and "no prices" not in system and "Kharadi" not in system


async def test_guards_keep_every_invention_out(tmp_path):
    llm = FakeLlm(BAD_STRATEGY, BAD_COPY, BAD_STRATEGY, BAD_COPY)
    pack = await pipeline.make(price_reveal(), "buyer", "instagram", llm, out_dir=tmp_path, reviewer=None)
    assert pack.report["ok"]
    published = " ".join([pack.caption, pack.angle["hook"], pack.alt_text])
    for leak in LEAKS:
        assert leak not in published, leak


async def test_a_clean_reply_with_the_listed_price_is_kept(tmp_path):
    good = {"first_line": "A 1,927 sq ft plot at Gulmohar City, Ranjangaon, listed at ₹32.3 lakh.",
            "body": "Gulmohar City is registered on MahaRERA.\nAsk what the price includes before a token.",
            "question": "What would you check first on a site visit?", "hashtags": ["#Ranjangaon", "#PlotsInPune", "#MahaRERA"]}
    llm = FakeLlm(None, good)
    pack = await pipeline.make(price_reveal(), "buyer", "instagram", llm, out_dir=tmp_path, reviewer=None)
    assert pack.report["ok"] and pack.used_llm
    # the caption opens with the card's headline, never the model's own first line; the model's body is kept
    assert pack.caption.startswith(pack.angle["hook"]) and not pack.caption.startswith(good["first_line"])
    assert good["body"].splitlines()[0] in pack.caption
    assert "What would you ask about this price?" in pack.caption        # the angle's own question, not the model's
