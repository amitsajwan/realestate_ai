import re

import pytest

from app.modules.marketing.content import (CAPTION_MAX, FB_MAX, HASHTAGS_MAX, HEADLINE_MAX, STATUS_MAX, WA_MAX,
                                           build_content, hashtags, sanitize_hashtag)
from app.modules.marketing.facts import budget_phrase, money
from app.modules.marketing.polish import accept, polish_content, polish_text

from .marketing_helpers import VARIANTS, facts

BANNED = re.compile(r"\b(best|guarantee\w*|lowest|cheapest|perfect|dream|unbeatable|no\.? ?1)\b", re.I)


def _texts(c):
    return [c["angle"], c["headline"], c["instagram"]["caption"], c["facebook"]["post"], c["whatsapp"]["message"],
            c["whatsapp"]["status_text"], c["reel"]["hook"], c["reel"]["cta"], *[b["text"] for b in c["reel"]["beats"]]]


def test_money_formats():
    assert money(8500000) == "₹85 Lakh"
    assert money(12500000) == "₹1.25 Cr"
    assert money(10000000) == "₹1 Cr"
    assert money(1250000) == "₹12.5 Lakh"
    assert money(45000, rent=True) == "₹45,000/month"
    assert money(250000000) == "₹25 Cr"


def test_budget_buckets():
    assert budget_phrase(8500000) == "under ₹1 Cr"
    assert budget_phrase(10000000) == "under ₹1.5 Cr"  # strictly above the price
    assert budget_phrase(4500000) == "under ₹50 Lakh"
    assert budget_phrase(45000, rent=True) == "under ₹50,000/month"
    assert budget_phrase(250000000) == "under ₹30 Cr"


@pytest.mark.parametrize("name,angle", [
    ("sale_ready_full", "Ready-to-move 2 BHK apartment in Baner under ₹1 Cr"),
    ("sale_uc_no_amen", "Under-construction 2 BHK apartment in Baner under ₹1.5 Cr"),
    ("rent_cheap", "1 BHK apartment for rent in Baner under ₹50,000/month"),
    ("luxury_villa", "Ready-to-move 5 BHK villa in Koregaon Park under ₹30 Cr"),
    ("plot_min", "Plot in Baner under ₹50 Lakh"),
])
def test_angle_golden(name, angle):
    assert build_content(facts(**VARIANTS[name]), "en")["angle"] == angle


def test_golden_full_listing():
    c = build_content(facts(), "en")
    assert c["headline"] == "2 BHK apartment for sale in Baner, Pune | ₹85 Lakh"
    assert c["whatsapp"]["message"] == (
        "2 BHK apartment for sale in Baner, Pune - ₹85 Lakh (1,100 sq ft, Ready to move)\nRERA: P52100012345\n"
        "Details and photos: https://site.test/agent/rahul/listings/L1?src=whatsapp\nReply here to plan a visit.")
    assert c["whatsapp"]["status_text"] == "2 BHK | Baner | ₹85 Lakh\nReply INTERESTED for details"
    cap = c["instagram"]["caption"]
    assert cap.startswith("\U0001F3E1 2 BHK apartment for sale in Baner, Pune · 1,100 sq ft · Ready to move\n₹85 Lakh\nRERA: P52100012345")
    assert "Amenities: Gym, Swimming pool, Clubhouse" in cap
    assert cap.splitlines()[-1] == "\U0001F4AC Interested? Comment INTERESTED and Avasetu team will share the details and plan a site visit."
    assert c["instagram"]["hashtags"][:4] == ["#Baner", "#Pune", "#2BHK", "#Apartment"]


def test_optional_facts_absent_not_invented():
    c = build_content(facts(**VARIANTS["plot_min"]), "en")
    txt = "\n".join(_texts(c))
    for word in ("RERA", "Amenities", "BHK", "Floor", "furnished", "Ready", "Possession"):
        assert word not in txt, word
    assert "2,400 sq ft" in c["facebook"]["post"]
    assert "₹45 Lakh" in c["headline"]


def test_rent_price_has_month():
    c = build_content(facts(**VARIANTS["rent_cheap"]), "en")
    assert "₹45,000/month" in c["headline"] and "for rent" in c["headline"]


def test_never_invent_numbers_and_claims():
    for name, over in VARIANTS.items():
        f = facts(**over)
        c = build_content(f, "en")
        allowed = set(re.findall(r"\d[\d,]*(?:\.\d+)?", " ".join(str(x) for x in (
            f.price_text, f.bhk_text, f.area_text, f.rera, f.floor, f.total_floors, f.agent_phone, f.listing_id))))
        allowed |= set(re.findall(r"\d[\d,]*(?:\.\d+)?", f.rera or "")) | {"15"}
        allowed |= {"0", "3", "6", "9", "12"}  # reel second markers
        for t in _texts(c)[1:]:  # everything except the angle (its budget ceiling is derived, tested separately)
            t = re.sub(r"https?://\S+", "", t)
            for tok in re.findall(r"\d[\d,]*(?:\.\d+)?", t):
                assert tok.rstrip(",") in allowed, (name, tok, t)
            assert not BANNED.search(t), (name, t)
        # amenities named are only real ones
        if not f.amenities:
            assert "Amenities" not in c["instagram"]["caption"] + c["facebook"]["post"]
        for tag in c["instagram"]["hashtags"]:
            assert tag.lower().lstrip("#") not in {"luxury", "premium", "bestdeal"}


def test_limits_and_hashtag_rules():
    long = facts(title="t", locality="L" * 100, city="C" * 70, project_name="P" * 110,
                 amenities=["Amenity number %d" % i for i in range(60)], _id="LX")
    c = build_content(long, "en")
    assert len(c["headline"]) <= HEADLINE_MAX
    assert len(c["instagram"]["caption"]) <= CAPTION_MAX
    assert "Comment INTERESTED" in c["instagram"]["caption"].splitlines()[-1]
    assert len(c["facebook"]["post"]) <= FB_MAX and len(c["whatsapp"]["message"]) <= WA_MAX
    assert len(c["whatsapp"]["status_text"]) <= STATUS_MAX
    tags = c["instagram"]["hashtags"]
    assert len(tags) <= HASHTAGS_MAX and len({t.lower() for t in tags}) == len(tags)
    assert all(re.fullmatch(r"#[^\W_]+", t) for t in tags)


def test_hashtag_sanitising():
    assert sanitize_hashtag("Pimple Saurabh") == "PimpleSaurabh"
    assert sanitize_hashtag("Koregaon-Park!!") == "KoregaonPark"
    tags = hashtags(facts(locality="Pune", city="pune"))  # duplicates collapse case-insensitively
    assert [t.lower() for t in tags].count("#pune") == 1


def test_reel_shape():
    r = build_content(facts(), "en")["reel"]
    assert r["duration_s"] == 15 and [b["seconds"] for b in r["beats"]] == ["0-3s", "3-6s", "6-9s", "9-12s", "12-15s"]
    assert "₹85 Lakh" in r["beats"][3]["text"] and "Baner" in r["beats"][2]["text"]
    assert r["beats"][0]["text"] == r["hook"] and r["beats"][-1]["text"] == r["cta"]


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_devanagari_templates_keep_facts(lang):
    c = build_content(facts(), lang)
    assert c["language"] == lang
    assert re.search(r"[ऀ-ॿ]", c["instagram"]["caption"])
    for t in (c["headline"], c["instagram"]["caption"], c["whatsapp"]["message"], c["facebook"]["post"]):
        assert "₹85 Lakh" in t and "2 BHK" in t and "Baner" in t
    assert "P52100012345" in c["whatsapp"]["message"] and "src=whatsapp" in c["whatsapp"]["message"]
    assert re.search(r"[ऀ-ॿ]", c["reel"]["cta"])


def test_unsupported_language_falls_back_to_english():
    c = build_content(facts(), "ta")
    assert c["language"] == "en" and c["headline"].startswith("2 BHK apartment")


# ---- polish ---------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_polish_accepts_when_facts_kept():
    f = facts()
    c = build_content(f, "en")

    async def ok(draft, lang):
        return draft.replace("Interested?", "Like what you see?")

    out = await polish_content(build_content(f, "en"), f, ok)
    assert "Like what you see?" in out["instagram"]["caption"] and "Like what you see?" in out["facebook"]["post"]
    assert out["instagram"]["caption"] != c["instagram"]["caption"]
    assert out["whatsapp"] == c["whatsapp"] and out["headline"] == c["headline"]  # only the two social texts cost an LLM call


@pytest.mark.asyncio
@pytest.mark.parametrize("dropped", ["₹85 Lakh", "2 BHK", "Baner", "1,100 sq ft", "P52100012345"])
async def test_polish_rejected_when_protected_fact_missing(dropped):
    f = facts()
    base = build_content(f, "en")

    async def bad(draft, lang):
        return draft.replace(dropped, "something")

    out = await polish_content(build_content(f, "en"), f, bad)
    assert out["instagram"]["caption"] == base["instagram"]["caption"]
    assert out["whatsapp"]["message"] == base["whatsapp"]["message"]


@pytest.mark.asyncio
async def test_polish_rejects_lost_link_overlong_empty_and_errors():
    f = facts()
    draft = build_content(f, "en")["whatsapp"]["message"]

    async def nolink(d, lang):
        return d.replace("https://site.test/agent/rahul/listings/L1?src=whatsapp", "the link")

    async def huge(d, lang):
        return d + " x" * 500

    async def empty(d, lang):
        return "  "

    async def boom(d, lang):
        raise RuntimeError("llm down")

    for p in (nolink, huge, empty, boom):
        assert await polish_text(p, draft, "en", f, WA_MAX) == draft
    assert accept("₹85 Lakh", "Only ₹85 Lakh", f)
    assert not accept("₹85 Lakh", "cheap", f)


# ---- no phone numbers in any post ------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
@pytest.mark.parametrize("name", list(VARIANTS))
def test_no_phone_number_or_call_prompt_in_any_post(name, lang):
    """Buyers reach the agent through 'Comment INTERESTED', a message or the listing link: the agent's number is never posted."""
    f = facts(**VARIANTS[name])
    assert f.agent_phone  # the profile has a phone, so this proves it is deliberately left out
    c = build_content(f, lang)
    everything = "\n".join(_texts(c) + [c["instagram"]["caption"], c["facebook"]["post"], " ".join(c["instagram"]["hashtags"])])
    digits = re.sub(r"\D", "", f.agent_phone)
    assert digits not in re.sub(r"\D", "", everything)
    assert digits[-6:] not in everything
    assert not re.search(r"\b(call|कॉल)\b", everything, re.I)
    assert "INTERESTED" in c["instagram"]["caption"] and "INTERESTED" in c["facebook"]["post"]


def test_facebook_post_reads_well_and_stays_within_limits():
    post = build_content(facts(), "en")["facebook"]["post"]
    assert post.startswith("\U0001F3E1 2 BHK apartment for sale in Baner, Pune · 1,100 sq ft · Ready to move\n₹85 Lakh")
    assert "\U0001F4D0 Area: 1,100 sq ft (carpet)" in post and "✅ Possession: Ready to move" in post
    assert post.rstrip().endswith("plan a site visit.") and len(post) <= FB_MAX


# ---- LLM polish guard rails --------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [
    lambda d: d.replace("Comment INTERESTED", "Contact us"),                 # lost the call to action
    lambda d: d.replace("Avasetu team", "Rahul"),                        # lost the team signature
    lambda d: d + "\nCall 9876543210 now",                                     # invented a phone number
    lambda d: d.replace("Interested?", "Your dream home!"),                    # hype
])
async def test_polish_rejects_lost_cta_signature_phone_or_hype(bad):
    f = facts()
    base = build_content(f, "en")

    async def evil(draft, lang):
        return bad(draft)

    out = await polish_content(build_content(f, "en"), f, evil)
    assert out["instagram"]["caption"] == base["instagram"]["caption"] and out["facebook"]["post"] == base["facebook"]["post"]


@pytest.mark.asyncio
async def test_llm_backed_polish_uses_text_and_falls_back_when_the_llm_is_down():
    from app.modules.marketing.polish import make_llm_polish

    class LLM:
        def __init__(self, reply):
            self.reply, self.seen = reply, []

        async def text(self, system, user):
            self.seen.append((system, user))
            return self.reply

    f = facts()
    base = build_content(f, "en")
    good = LLM(base["facebook"]["post"].replace("Interested?", "Like what you see?"))
    out = await polish_content(build_content(f, "en"), f, make_llm_polish(good))
    assert "Like what you see?" in out["facebook"]["post"] and "NEVER add facts" in good.seen[0][0]
    down = await polish_content(build_content(f, "en"), f, make_llm_polish(LLM(None)))
    assert down["facebook"]["post"] == base["facebook"]["post"]


def test_polish_is_off_unless_switched_on(monkeypatch):
    from app.modules.marketing.polish import default_polish

    monkeypatch.delenv("MARKETING_POLISH", raising=False)
    assert default_polish() is None
    monkeypatch.setenv("MARKETING_POLISH", "true")
    monkeypatch.setenv("AI_LLM_API_KEY", "k")
    assert default_polish() is not None


@pytest.mark.parametrize("raw,clean", [
    ("Of course! Here is the rewritten post:\n\nLovely 2 BHK. Comment INTERESTED.", "Lovely 2 BHK. Comment INTERESTED."),
    ("Sure, here's a warmer version:\nLovely 2 BHK.", "Lovely 2 BHK."),
    ("```\nLovely 2 BHK.\n```", "Lovely 2 BHK."),
    ('"Lovely 2 BHK."', "Lovely 2 BHK."),
    ("Lovely 2 BHK.\nHere is the floor plan link.", "Lovely 2 BHK.\nHere is the floor plan link."),  # only the FIRST lines are chatter
])
def test_chatty_model_wrappers_are_stripped(raw, clean):
    from app.platform.text import clean_llm_text

    assert clean_llm_text(raw) == clean


# ---- sample (illustrative) listings are labelled everywhere ---------------------------------------------
def test_sample_listing_is_labelled_in_every_text_and_card():
    from app.modules.marketing.images import render

    f = facts(title="Sample: 2 BHK in Baner")
    assert f.sample and not facts().sample
    c = build_content(f, "en")
    for text in (c["instagram"]["caption"], c["facebook"]["post"], c["whatsapp"]["message"]):
        assert "SAMPLE LISTING" in text
    assert "SAMPLE LISTING" in c["instagram"]["caption"].splitlines()[0]
    assert "SAMPLE LISTING" in render("cover", f, None).texts and "FOR SALE" not in render("cover", f, None).texts
    assert "SAMPLE LISTING" not in build_content(facts(), "en")["facebook"]["post"]


# ---- group post -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
def test_group_post_is_short_dated_tracked_and_has_no_contact_details(lang):
    f = facts()
    f.as_of = "30 Sep 2026"
    post = build_content(f, lang)["group"]["post"]
    assert "30 Sep 2026" in post and "src=fbgroup" in post and "src=whatsapp" not in post
    assert "₹85 Lakh" in post and "Baner" in post and "P52100012345" in post
    assert len(post.splitlines()) <= 8 and len(post) <= 600
    assert re.sub(r"\D", "", f.agent_phone) not in re.sub(r"\D", "", post)


def test_group_post_without_a_date_omits_the_line_and_samples_are_labelled():
    assert "Available as of" not in build_content(facts(), "en")["group"]["post"]
    first = build_content(facts(title="Sample: 2 BHK"), "en")["group"]["post"].splitlines()
    assert "SAMPLE LISTING" in first[0] and first[1].startswith("SAMPLE LISTING (")


# ---- links back to the agent's site -----------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
def test_facebook_post_links_to_the_listing_tagged_as_facebook(lang):
    f = facts()
    f.share_url = "https://x.test/agent/rahul/listings/L1?src=whatsapp"
    c = build_content(f, lang)
    assert "https://x.test/agent/rahul/listings/L1?src=facebook" in c["facebook"]["post"]
    assert "src=whatsapp" not in c["facebook"]["post"] and len(c["facebook"]["post"]) <= FB_MAX
    assert "http" not in c["instagram"]["caption"]  # Instagram captions are not clickable
    assert "link in bio" in build_content(f, "en")["instagram"]["caption"] and len(c["instagram"]["caption"]) <= CAPTION_MAX


def test_no_link_lines_without_a_share_url():
    f = facts()
    f.share_url = ""
    c = build_content(f, "en")
    assert "http" not in c["facebook"]["post"] and "link in bio" not in c["instagram"]["caption"]


def test_about_highlights_appear_in_captions_at_most_two_and_verbatim():
    f = facts(about={"highlights": ["East facing", "Corner flat", "Park facing"]})
    assert f.highlights == ["East facing", "Corner flat"]
    c = build_content(f, "en")
    ig, fb = c["instagram"]["caption"], c["facebook"]["post"]
    for txt in (ig, fb):
        assert "East facing" in txt and "Corner flat" in txt and "Park facing" not in txt
    assert len(ig) <= CAPTION_MAX and len(fb) <= FB_MAX


def test_no_about_means_captions_unchanged():
    assert facts().highlights == []
    assert facts(about={"water": "Borewell water"}).highlights == []
    assert build_content(facts(about={"highlights": []}), "en") == build_content(facts(), "en")

# ---- reel hooks -----------------------------------------------------------------------------------------------
def test_reel_hook_is_guess_the_price_with_a_reveal_and_never_the_old_take_a_look():
    r = build_content(facts(), "en")["reel"]
    assert r["hook"] == "Guess the price of this 2 BHK apartment in Baner"
    assert r["beats"][3]["text"] == "₹85 Lakh. Did you guess right?"
    assert "₹" not in r["hook"]  # the price is the reveal, not the opening
    assert build_content(facts(**VARIANTS["rent_cheap"]), "en")["reel"]["hook"] == "Guess the rent of this 1 BHK apartment in Baner"


def test_reel_hook_without_a_price_asks_a_question_and_skips_the_reveal():
    r = build_content(facts(price_inr=None), "en")["reel"]
    assert r["hook"] == "Would you live in this 2 BHK apartment in Baner?"
    assert "guess" not in " ".join(b["text"] for b in r["beats"]).lower()
    assert build_content(facts(price_inr=None, locality=None, city=None), "en")["reel"]["hook"] == "Would you live in this 2 BHK apartment?"


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_reel_hook_in_devanagari_keeps_the_facts(lang):
    r = build_content(facts(), lang)["reel"]
    assert re.search(r"[ऀ-ॿ]", r["hook"]) and "2 BHK" in r["hook"] and "Baner" in r["hook"] and "{" not in r["hook"]
    assert r["beats"][3]["text"].startswith("₹85 Lakh. ")
    assert "{" not in build_content(facts(price_inr=None, locality=None, city=None), lang)["reel"]["hook"]


# ---- the first caption line is the hook ------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
@pytest.mark.parametrize("sample", [False, True])
@pytest.mark.parametrize("name", list(VARIANTS))
def test_every_text_opens_with_a_hook_not_a_label_or_greeting(name, lang, sample):
    """Instagram shows about 125 characters before '... more': the first line is what and where plus a standout fact."""
    from app.modules.calendar.guards import hook_problems

    over = dict(VARIANTS[name], **({"title": "Sample: x"} if sample else {}))
    f = facts(**over)
    c = build_content(f, lang)
    for text in (c["instagram"]["caption"], c["facebook"]["post"], c["whatsapp"]["message"], c["group"]["post"]):
        line = text.splitlines()[0]
        assert hook_problems(text) == [], (line, hook_problems(text))
        assert (f.locality or f.city) in line and (f.bhk_text or "") in line
        assert ("SAMPLE LISTING" in line) == sample  # a sample is labelled inside the visible part, never hidden below '... more'
    ig_line = c["instagram"]["caption"].splitlines()[0]
    assert f.area_text is None or f.area_text in ig_line  # the standout fact
