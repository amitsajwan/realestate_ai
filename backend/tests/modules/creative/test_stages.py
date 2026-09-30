import pytest

from app.modules.creative import art_director, copywriter, critic, hooks, strategist
from app.modules.creative.guards import problems_in, word_count
from app.modules.creative.layouts import render_layout
from app.modules.creative.models import Angle, Brief, Copy, Design
from app.modules.creative.samples import agent_briefs, buyer_briefs

from .helpers import FakeLlm, build, simple_brief


# ---- strategist -------------------------------------------------------------------------------
async def test_rule_angle_is_complete_and_hook_is_short():
    for b in buyer_briefs() + agent_briefs():
        for aud in ("buyer", "agent"):
            a = await strategist.plan(b, aud, "instagram", None, seed=3)
            assert 2 <= word_count(a.hook) <= 9, a.hook
            assert a.fmt in b.formats() and a.cta and a.idea and a.pain
            assert problems_in(a.hook, b.corpus()) == []


async def test_hook_patterns_rotate():
    b = buyer_briefs()[0]
    b.prefer = "single"
    seen = {(await strategist.plan(b, "buyer", "instagram", None, seed=s)).pattern for s in range(6)}
    assert len(seen) >= 3


async def test_llm_angle_is_used_when_valid():
    b = simple_brief()
    llm = FakeLlm({"pain": "Buyers trust verbal dates", "idea": "Get the date in writing", "hook": "Is your possession date in writing?",
                   "pattern": "question", "proof": ["The agreement should state the possession date."], "format": "single", "cta": "Save this."})
    a = await strategist.plan(b, "buyer", "instagram", llm, 1)
    assert a.source == "llm" and a.hook == "Is your possession date in writing?"
    assert a.proof == ["The agreement should state the possession date."]


@pytest.mark.parametrize("bad_hook", [
    "This hook has far too many words to ever fit on a card",   # > 9 words
    "The best flat in Kharadi",                                 # hype
    "Call 9876543210 now",                                      # phone
    "Rates will rise 40 percent",                               # prediction + number not in facts
    "Tips for buyers",                                          # generic
])
async def test_bad_llm_hook_falls_back_to_rules(bad_hook):
    a = await strategist.plan(simple_brief(), "buyer", "instagram", FakeLlm({"hook": bad_hook, "format": "single"}), 0)
    assert a.hook != bad_hook and a.source == "rules" and word_count(a.hook) <= 9


async def test_llm_proof_must_come_from_facts_and_format_must_be_possible():
    llm = FakeLlm({"hook": "Is your date in writing?", "proof": ["Prices doubled in Kharadi"], "format": "poll"})
    a = await strategist.plan(simple_brief(), "buyer", "instagram", llm, 0)
    assert a.proof == simple_brief().facts[:3] and a.fmt == "single"


async def test_llm_failure_or_garbage_uses_rules():
    for llm in (FakeLlm(RuntimeError("down")), FakeLlm(None), FakeLlm({"hook": 7})):
        a = await strategist.plan(simple_brief(), "buyer", "instagram", llm, 0)
        assert a.source == "rules" and a.hook


async def test_strategist_avoids_the_last_layout_when_it_can():
    b = buyer_briefs()[1]  # myth -> only myth_fact, plus single
    a = await strategist.plan(b, "buyer", "instagram", None, 0, recent_layouts=["myth_fact"])
    assert a.fmt != "myth-vs-fact"


# ---- copywriter -------------------------------------------------------------------------------
async def test_rule_copy_passes_all_guards_for_every_sample():
    for b in buyer_briefs() + agent_briefs():
        for ch in ("instagram", "facebook"):
            aud = "agent" if b in agent_briefs() else "buyer"
            a = await strategist.plan(b, aud, ch, None, 1)
            c = await copywriter.write(a, b)
            assert copywriter.review_copy(c, b.corpus(), ch) == [], (b.topic, copywriter.review_copy(c, b.corpus(), ch))
            assert all(word_count(s) <= 14 for s in c.slides)


async def test_instagram_caption_has_no_url_and_3_to_8_tags_facebook_may_link():
    b = simple_brief(link="https://example.test/insights/x")
    a = await strategist.plan(b, "buyer", "instagram", None, 0)
    c = await copywriter.write(a, b)
    ig = c.caption("instagram", b.link)
    assert "http" not in ig and "link in our bio" in ig and 3 <= len(c.hashtags) <= 8
    fb = c.caption("facebook", b.link)
    assert "https://example.test/insights/x" in fb


async def test_first_line_is_short_enough_to_show_before_more():
    a = await strategist.plan(simple_brief(), "buyer", "instagram", None, 0)
    c = await copywriter.write(a, simple_brief())
    assert len(c.caption_first_line) <= 125 and c.caption_first_line.split("\n")[0] == c.caption_first_line


async def test_llm_copy_used_and_bad_fields_replaced():
    b = buyer_briefs()[4]
    a = await strategist.plan(b, "buyer", "instagram", None, 0)
    good = {"support": "Visit at a second hour to see the real street.", "first_line": "Would you buy after one 10-minute visit?",
            "body": "A second visit shows what the first one hides.", "question": "When did you last visit twice?",
            "hashtags": ["#PuneProperty", "#Kharadi", "#SiteVisit"]}
    c = await copywriter.write(a, b, FakeLlm(good))
    # "10-minute" is a number that is not in the facts -> that field is rejected, the others stay
    assert c.caption_first_line == copywriter.rule_copy(a, b).caption_first_line
    assert c.support == good["support"] and c.hashtags == good["hashtags"] and c.source == "llm"


@pytest.mark.parametrize("field,value", [("body", "The best, perfect home, guaranteed. Call 9876543210."),
                                         ("first_line", "Prices will rise next year"), ("body", "Visit www.example.com now")])
async def test_llm_copy_with_hype_phone_prediction_or_url_is_rejected(field, value):
    b = simple_brief()
    a = await strategist.plan(b, "buyer", "instagram", None, 0)
    base = copywriter.rule_copy(a, b)
    c = await copywriter.write(a, b, FakeLlm({field: value}))
    assert getattr(c, "body" if field == "body" else "caption_first_line") == (base.body if field == "body" else base.caption_first_line)


async def test_generic_filler_is_caught():
    assert problems_in("Unlock the ultimate guide to buying", "x")
    c = Copy("Hook words here", "", [], "First line.", "In today's world, buying is hard.", "Q?", ["#a1b", "#a2b", "#a3b"])
    assert any("filler" in p for p in copywriter.review_copy(c, "x", "facebook"))


async def test_slides_from_llm_limited_to_14_words_and_3_to_5():
    b = buyer_briefs()[0]
    a = await strategist.plan(b, "buyer", "instagram", None, 0)
    long = " ".join(["word"] * 15)
    c = await copywriter.write(a, b, FakeLlm({"slides": [long, "Two", "Three"]}))
    assert c.slides == b.steps[:5]
    c = await copywriter.write(a, b, FakeLlm({"slides": ["Ask for the RERA number", "Compare carpet area", "Walk the street"]}))
    assert c.slides[0] == "Ask for the RERA number"


async def test_variants_only_when_asked_and_guarded():
    b = simple_brief()
    a = await strategist.plan(b, "buyer", "instagram", None, 0)
    c = await copywriter.write(a, b, FakeLlm({}), languages=())
    assert c.variants == {}
    c = await copywriter.write(a, b, FakeLlm({}), languages=("hinglish",))
    assert "hinglish" in c.variants and c.variants["hinglish"].endswith(c.hashtags[-1])
    c = await copywriter.write(a, b, FakeLlm({}, text_reply="Call 9876543210 abhi"), languages=("marathi",))
    assert c.variants == {}


# ---- art director -----------------------------------------------------------------------------
def _angle(fmt, aud="buyer"):
    return Angle(aud, "instagram", "p", "i", "Hook words here", "question", [], fmt, "c")


def test_art_director_never_repeats_the_last_layout_when_there_is_a_choice():
    copy, _, _ = build("photo_led")
    for seed in range(12):
        d = art_director.choose(copy, _angle("single"), ["photo_led"], seed)
        assert d.layout != "photo_led"
        d = art_director.choose(copy, _angle("single"), ["photo_led", "quote_tip"], seed)
        assert d.layout != "quote_tip"


def test_art_director_palette_photo_and_size():
    copy, _, _ = build("photo_led")
    d = art_director.choose(copy, _angle("single"), [], 2)
    assert d.size == (1080, 1350) and d.palette in ("navy_gold", "navy_teal", "navy_coral", "cream")
    a = _angle("single"); a.channel = "facebook"
    assert art_director.choose(copy, a, [], 2).size == (1080, 1080)
    assert art_director.choose(copy, _angle("single", "agent"), [], 0).layout in ("product_showcase", "quote_tip")


def test_single_format_layouts_are_audience_specific():
    copy, _, _ = build("quote_tip")
    for seed in range(8):
        assert art_director.choose(copy, _angle("single", "buyer"), [], seed).layout != "product_showcase"
        assert art_director.choose(copy, _angle("single", "agent"), [], seed).layout != "photo_led"


def test_emphasis_words():
    assert art_director.emphasis_words("3 site visits before you pay a token")[0] == "3"
    assert "nobody" in art_director.emphasis_words("What nobody tells you about carpet area")
    assert len(art_director.emphasis_words("A very long hook with many good words")) <= 2


# ---- critic -----------------------------------------------------------------------------------
def _review(layout="poll", mutate=None, recent=()):
    copy, design, brief = build(layout)
    if mutate:
        mutate(copy, design)
    return critic.review(copy, design, render_layout(copy, design), brief.corpus(), "instagram", recent), copy


def test_clean_pack_passes():
    for layout in ("big_number", "myth_fact", "poll", "before_after", "quote_tip", "photo_led", "product_showcase", "checklist"):
        rep, _ = _review(layout)
        assert rep.ok, (layout, rep.errors())


def test_critic_flags_long_hook_long_slide_and_hype():
    rep, _ = _review("poll", lambda c, d: setattr(c, "hook", "one two three four five six seven eight nine ten"))
    assert any(p.rule == "hook_length" for p in rep.errors())
    rep, _ = _review("checklist", lambda c, d: c.slides.__setitem__(0, " ".join(["w"] * 16)))
    assert any(p.rule == "slide_length" for p in rep.errors())
    rep, _ = _review("poll", lambda c, d: setattr(c, "body", "The best perfect flat"))
    assert any(p.rule == "copy_guard" for p in rep.errors())


def test_critic_flags_repeated_layout_and_invented_numbers():
    rep, _ = _review("poll", recent=["poll"])
    assert any(p.rule == "repeat_layout" for p in rep.errors())
    rep, _ = _review("poll", lambda c, d: setattr(c, "caption_first_line", "Saves 45 percent"))
    assert any("number not in facts" in p.message for p in rep.errors())


def test_critic_flags_bad_contrast_and_overflow():
    def dim(c, d):
        d.palette = "cream"
    rep, _ = _review("poll", dim)
    assert rep.ok  # cream is designed to pass
    from app.modules.creative.layouts import palette
    assert palette.contrast((255, 255, 255), (250, 245, 235)) < 1.2  # the metric itself: white on cream fails


def test_critic_flags_margins_truncation_and_hashtags():
    copy, design, brief = build("quote_tip")
    r = render_layout(copy, design)
    r[0].items[0].box = (10, 10, 400, 60)
    r[0].items[1].truncated = True
    copy.hashtags = ["#one"]
    rep = critic.review(copy, design, r, brief.corpus(), "instagram")
    rules = {p.rule for p in rep.errors()}
    assert {"margins", "truncated", "copy_guard"} <= rules


async def test_llm_critique_is_advice_only():
    copy, design, _ = build("poll")
    probs = await critic.llm_critique(FakeLlm({"stops_scroll": False, "problems": ["Weak hook"], "better_hook": "Which would you pick?"}), copy, design)
    assert {p.severity for p in probs} == {"warn"} and len(probs) == 2
    assert await critic.llm_critique(None, copy, design) == []
    assert await critic.llm_critique(FakeLlm(RuntimeError("x")), copy, design) == []


def test_hooks_library_has_the_six_patterns():
    assert set(hooks.PATTERNS) == {"mistake", "number", "myth", "nobody", "comparison", "question"}
    assert hooks.pick_pattern(0, ["a", "b", "c"]) != hooks.pick_pattern(1, ["a", "b", "c"])
