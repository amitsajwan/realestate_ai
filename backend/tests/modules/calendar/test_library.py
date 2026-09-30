import re

import pytest
from PIL import Image

from app.modules.calendar import guards, library, render
from app.modules.calendar.library import ENTRIES, PILLARS, SITE

BANNED_WORDS = re.compile(r"\b(builders?|developers?)\b.*\b(pvt|ltd|group|realty|properties)\b", re.I)
PERSON_OR_PHONE = re.compile(r"\b(mr|mrs|ms|shri|smt)\.?\s+[A-Z]", re.I)


def test_forty_posts_with_unique_slugs():
    slugs = [e.slug for e in ENTRIES]
    assert len(slugs) == 40 and len(set(slugs)) == 40
    assert all(re.fullmatch(r"[a-z0-9-]+", s) for s in slugs)
    assert {e.pillar for e in ENTRIES} == set(PILLARS)


def test_every_pillar_is_well_represented():
    counts = {p: sum(1 for e in ENTRIES if e.pillar == p) for p in PILLARS}
    assert min(counts.values()) >= 3, counts


def test_every_guard_passes_on_every_caption():
    assert guards.check_all(ENTRIES) == {}


def test_instagram_captions_have_no_urls_and_few_hashtags():
    for e in ENTRIES:
        assert "http" not in e.ig_caption and "www." not in e.ig_caption, e.slug
        tags = re.findall(r"#\w+", e.ig_caption)
        assert 3 <= len(tags) <= 8, e.slug
        if e.link:
            assert "link in our bio" in e.ig_caption.lower(), e.slug


def test_length_limits():
    for e in ENTRIES:
        assert len(e.fb_caption) < 900, (e.slug, len(e.fb_caption))
        assert len(e.ig_caption) < 2000, e.slug


def test_every_facebook_link_points_to_an_existing_site_path():
    paths = guards.site_paths()
    assert "/insights/kharadi-upper-kharadi-wagholi" in paths and "/localities/wagholi" in paths  # parsed from the frontend sources
    linked = [e for e in ENTRIES if e.link]
    assert linked
    for e in linked:
        assert e.link in paths, e.slug
        assert f"{SITE}{e.link}" in e.fb_caption


def test_each_post_ends_with_a_question_or_save_share_prompt():
    for e in ENTRIES:
        last = [ln for ln in e.body.splitlines() if ln.strip()][-1]
        assert guards.PROMPT.search(last), e.slug


def test_every_post_records_what_needs_a_source():
    for e in ENTRIES:
        assert len(e.review) > 30, e.slug


def test_no_prices_predictions_phones_or_names():
    for e in ENTRIES:
        text = f"{e.title} {' '.join(e.points)} {e.fb_caption} {e.ig_caption}"
        assert not guards.PRICE.search(text), e.slug
        assert not guards.PREDICT.search(text), e.slug
        assert not guards.PHONE.search(text), e.slug
        assert not PERSON_OR_PHONE.search(text), e.slug
        assert not BANNED_WORDS.search(text), e.slug


def test_metro_posts_follow_approved_is_not_running():
    for e in ENTRIES:
        text = f"{e.body} {' '.join(e.points)}".lower()
        if "metro" in text and e.pillar != "agent":
            assert "approved" in text and ("not running" in text or "not yet running" in text or "not the same" in text), e.slug


def test_guards_catch_bad_captions():
    bad = library.Entry("x", "myth", "K", "T", ("p",), "The best flat, call 9876543210 or see https://x.test\nNo prompt here.", ("#a",), "r")
    problems = " | ".join(guards.check_entry(bad, guards.site_paths()))
    for needle in ("hype", "phone", "URL", "hashtags", "question"):
        assert needle in problems, needle
    wrong_link = library.Entry("y", "myth", "K", "T", ("p",), "Fine text?", ("#a", "#b", "#c"), "r", link="/nope")
    assert "not a site page" in " | ".join(guards.check_entry(wrong_link, guards.site_paths()))


def test_ig_cards_are_portrait_and_fb_cards_square(tmp_path):
    for e in ENTRIES:
        fb = render.render_entry(e, tmp_path, "facebook_page")
        ig = render.render_entry(e, tmp_path, "instagram")
        assert fb == tmp_path / f"{e.slug}.jpg" and ig == tmp_path / "ig" / f"{e.slug}.jpg"
        with Image.open(fb) as a, Image.open(ig) as b:
            assert a.size == (1080, 1080), e.slug
            assert b.size == (1080, 1350), e.slug


def test_card_text_stays_in_the_margins_and_is_never_cut():
    for e in ENTRIES:
        if e.card_from:
            continue
        for size in ((1080, 1080), render.PORTRAIT):
            c = render._card(e.kicker, e.title, list(e.points), size)
            for x0, y0, x1, y1 in c.boxes:
                assert x0 >= 84 - 6 and x1 <= size[0] - 84 + 6, (e.slug, size, (x0, x1))
                assert y0 >= 0 and y1 <= size[1] - 40, (e.slug, size)
            assert not any("…" in t or "..." in t for t in c.texts), e.slug
            for p in e.points:  # every point is drawn whole
                assert any(t in p for t in c.texts), (e.slug, p)


def test_image_path_per_channel():
    assert render.image_path("abc") == "calendar/abc.jpg"
    assert render.image_path("abc", "instagram") == "calendar/ig/abc.jpg"


@pytest.mark.parametrize("slug", ["agent-hindi", "agent-marathi"])
def test_devanagari_pitches_reuse_the_prerendered_cards(slug):
    assert library.BY_SLUG[slug].card_from == slug.replace("agent-", "agents-")
    assert (render.STATIC_DIR / f"{slug.replace('agent-', 'agents-')}.jpg").is_file()
