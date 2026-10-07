"""Pinned output of the shared text helpers: copy guards, INR / sq ft / BHK formatting, Indian mobile numbers.

Recorded from the code before it moved into the platform (MODERNIZATION step 2); a move must not change a single output.
"""
import pytest

from app.platform.text import HYPE, PHONE, bhk_label, clean_llm_text, money, normalize_indian_mobile, sqft


@pytest.mark.parametrize("n, sale, rent", [
    (0, "₹0", "₹0/month"),
    (999, "₹999", "₹999/month"),
    (45000, "₹45,000", "₹45,000/month"),
    (99999, "₹99,999", "₹99,999/month"),
    (100000, "₹1 Lakh", "₹1 Lakh/month"),
    (150000, "₹1.5 Lakh", "₹1.5 Lakh/month"),
    (8500000, "₹85 Lakh", "₹85 Lakh/month"),
    (9999999, "₹100 Lakh", "₹100 Lakh/month"),  # today's rounding; pinned as is
    (10000000, "₹1 Cr", "₹1 Cr/month"),
    (12500000, "₹1.25 Cr", "₹1.25 Cr/month"),
    (125000000, "₹12.5 Cr", "₹12.5 Cr/month"),
])
def test_money(n, sale, rent):
    assert money(n) == sale
    assert money(n, rent=True) == rent


@pytest.mark.parametrize("n, out", [(760, "760 sq ft"), (1200, "1,200 sq ft"), (12345, "12,345 sq ft")])
def test_sqft(n, out):
    assert sqft(n) == out


@pytest.mark.parametrize("b, out", [(1, "1 BHK"), (2.0, "2 BHK"), (2.5, "2.5 BHK"), (3, "3 BHK")])
def test_bhk_label(b, out):
    assert bhk_label(b) == out


@pytest.mark.parametrize("text, hype", [
    ("Best deal", True), ("guaranteed returns", True), ("No. 1 project", True), ("no1 builder", True),
    ("Dream home", True), ("LUXURIOUS flat", True), ("Lowest price", True),
    ("good flat", False), ("bestseller", False),
])
def test_hype_guard(text, hype):
    assert bool(HYPE.search(text)) is hype


@pytest.mark.parametrize("text, found", [
    ("call 9876543210", ["9876543210"]),
    ("+91 9876543210", ["+91 9876543210"]),
    ("+91-9876543210", ["+91-9876543210"]),
    ("919876543210", ["919876543210"]),
    ("5876543210", []),
    ("98765432101", []),
    ("date 2026-10-01", []),
    ("12345 67890", []),
])
def test_phone_guard(text, found):
    assert PHONE.findall(text) == found


@pytest.mark.parametrize("raw, out", [
    ("```\nHello\n```", "Hello"),
    ('"Quoted"', "Quoted"),
    ("Here is the rewritten post:\nActual text", "Actual text"),
    ("Sure!\n\nText", "Text"),
    ("plain", "plain"),
])
def test_clean_llm_text(raw, out):
    assert clean_llm_text(raw) == out


@pytest.mark.parametrize("raw", ["+91 98765 43210", "098765-43210", "919876543210", "9876543210"])
def test_indian_mobile_is_normalised(raw):
    assert normalize_indian_mobile(raw) == "+919876543210"


@pytest.mark.parametrize("raw", ["12345", "5876543210", "", None])
def test_invalid_indian_mobile_is_refused(raw):
    with pytest.raises(ValueError, match="Enter a valid 10-digit Indian mobile number"):
        normalize_indian_mobile(raw)


# ---- caption hooks (first line before Instagram's '... more') ----------------------------------------------------------
@pytest.mark.parametrize("caption", [
    "\U0001F914 A RERA number does not mean you can stop checking. Here is what it really tells you \U0001F447\n\nMore text.",
    "2 BHK in Kharadi, 780 sq ft, ready to move\n\nDetails",
    "\U0001F91D पुणे के प्रॉपर्टी एजेंट, एक सवाल: कितने खरीदार कमेंट में खो जाते हैं?",
])
def test_hook_problems_accepts_a_real_hook(caption):
    from app.platform.text import hook_problems

    assert hook_problems(caption) == []


@pytest.mark.parametrize("caption, needle", [
    ("\U0001F914 Myth vs fact\n\nMyth: \"It has a RERA number, so I can relax.\"", "label"),
    ("MYTH VS FACT\n\nMore", "label"),
    ("\U0001F4B3 Pay against progress\n\nBefore every instalment:", ""),  # 3 words: allowed by the helper, the library still rewrote it
    ("\U0001F3E1\n\n2 BHK in Baner", "words"),
    ("Before you sign:\n\n1. Read it", "label"),
    ("Hi! 2 BHK apartment for sale in Baner", "greeting"),
    ("word " * 30 + "\n\nrest", "characters"),
])
def test_hook_problems_flags_labels_emoji_greetings_and_long_lines(caption, needle):
    from app.platform.text import first_line, hook_problems

    problems = " | ".join(hook_problems(caption))
    assert first_line(caption) == caption.strip().split("\n")[0].strip()
    if needle:
        assert needle in problems, problems
    else:
        assert problems == ""
