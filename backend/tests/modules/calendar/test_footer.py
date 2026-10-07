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


def test_at_most_ten_hashtags_and_tail_block_survives():
    tags = " ".join(f"#t{i}" for i in range(15))
    out = with_footer("Nice home\n\n" + tags, "instagram")
    assert out.count("#") == 10 and out.endswith(INSTAGRAM_FOOTER)
    body = "word " * 300 + "\n" + " ".join(f"#t{i}" for i in range(5))
    out = with_footer(body, "facebook_page")
    assert len(out) < 900 and "#t4" in out


def test_empty_caption():
    assert with_footer("", "facebook_page") == FACEBOOK_FOOTER


def test_pre_rebrand_footer_is_replaced_not_doubled():
    old = "Body text\n\nPUNE Property · https://avasetu.in"
    out = with_footer(old, "facebook_page")
    assert "PUNE Property" not in out and out.count("Avasetu ·") == 1 and out.endswith(FACEBOOK_FOOTER)
