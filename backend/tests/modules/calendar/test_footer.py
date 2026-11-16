from app.modules.calendar.footer import FACEBOOK_FOOTER, INSTAGRAM_FOOTER, with_footer


def test_footers_are_the_agreed_text():
    assert FACEBOOK_FOOTER == "Avasetu · https://avasetu.in"
    assert INSTAGRAM_FOOTER == "Avasetu · link in our bio"


def test_appended_once_per_channel():
    fb = with_footer("Hello Kharadi", "facebook_page")
    assert fb.endswith(FACEBOOK_FOOTER) and "link in our bio" not in fb
    ig = with_footer("Hello Kharadi", "instagram")
    assert ig.endswith(INSTAGRAM_FOOTER) and "http" not in ig


def test_idempotent():
    for ch in ("facebook_page", "instagram"):
        once = with_footer("Body text #pune", ch)
        assert with_footer(once, ch) == once and once.count("Avasetu ·") == 1


def test_length_limits_keep_the_footer():
    long = "word " * 1000
    fb = with_footer(long, "facebook_page")
    ig = with_footer(long, "instagram")
    assert len(fb) < 900 and fb.endswith(FACEBOOK_FOOTER)
    assert len(ig) < 2000 and ig.endswith(INSTAGRAM_FOOTER)


def test_at_most_ten_hashtags_five_on_instagram_and_tail_block_survives():
    tags = " ".join(f"#t{i}" for i in range(15))
    out = with_footer("Nice home\n\n" + tags, "instagram")
    assert out.count("#") == 5 and out.endswith(INSTAGRAM_FOOTER)
    assert with_footer("Nice home\n\n" + tags, "facebook_page").count("#") == 10
    body = "word " * 300 + "\n" + " ".join(f"#t{i}" for i in range(5))
    out = with_footer(body, "facebook_page")
    assert len(out) < 900 and "#t4" in out


def test_empty_caption():
    assert with_footer("", "facebook_page") == FACEBOOK_FOOTER


def test_pre_rebrand_footer_is_replaced_not_doubled():
    old = "Body text\n\nPUNE Property · https://avasetu.in"
    out = with_footer(old, "facebook_page")
    assert "PUNE Property" not in out and out.count("Avasetu ·") == 1 and out.endswith(FACEBOOK_FOOTER)


# ---- the brand-search line (docs/plan/visibility-base.md step 4) ----------------------------------------------------------------

def test_a_buyer_post_asks_for_a_search_by_name_just_above_the_footer():
    out = with_footer("2 BHK in Kharadi from ₹78 lakh", "instagram", key="p1", place="Kharadi")
    assert out.endswith('🔎 Search "Avasetu Kharadi" on Google\n' + INSTAGRAM_FOOTER)
    assert out.count("🔎") == 1


def test_the_search_line_is_in_the_posts_language_with_the_brand_in_latin_letters():
    mr = with_footer("खराडीत नवीन घरे", "facebook_page", key="p1", place="खराडी", language="mr")
    assert '🔎 Google वर "Avasetu खराडी" शोधा' in mr
    hi = with_footer("नए घर", "facebook_page", key="p1", language="hi")
    assert '🔎 Google पर "Avasetu Pune" सर्च करें' in hi


def test_the_search_line_is_never_kept_twice_and_recruitment_posts_have_none():
    once = with_footer("Wagholi homes", "facebook_page", key="p1", place="Wagholi")
    assert with_footer(once, "facebook_page", key="p1", place="Wagholi") == once
    assert "🔎" not in with_footer("Join the free trial", "facebook_page")


def test_a_long_buyer_post_keeps_the_search_line_and_the_footer_inside_the_limit():
    out = with_footer("word " * 1000, "facebook_page", key="p1", place="Lohegaon")
    assert len(out) < 900 and out.endswith('🔎 Search "Avasetu Lohegaon" on Google\n' + FACEBOOK_FOOTER)
