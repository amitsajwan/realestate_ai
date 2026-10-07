"""Shared text helpers: copy guards, Indian number formatting, Indian mobile numbers, LLM output clean-up.

Moved unchanged from marketing/facts.py, marketing/polish.py and onboarding/phone.py (MODERNIZATION step 2); their output is
pinned by tests/platform_layer/test_text.py.
"""
import re

# ---- copy guards: no hype words, no phone numbers in generated copy -------------------------------------------------
HYPE = re.compile(r"\b(best|guarantee\w*|lowest|cheapest|perfect|dream|unbeatable|no\.? ?1|luxurious)\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")

# ---- caption hooks: the first line is what Instagram shows before '... more' -----------------------------------------
HOOK_MAX = 125  # Instagram cuts the caption at about this many characters
# A first line that is only a section label or a greeting wastes the visible part of the caption (the card already carries the label).
_LABEL_ONLY = re.compile(r"^(myth vs\.? fact|fact check|did you know|quick tip|tip of the day|explainer|checklist|poll|"
                         r"sample listing|new listing|just listed|hi|hello|hey|namaste|नमस्ते|नमस्कार)\W*$", re.I)
_GREETING = re.compile(r"^(hi|hello|hey|namaste|नमस्ते|नमस्कार)\b", re.I)


def first_line(caption: str) -> str:
    """The caption's opening line (text before the first line break), stripped."""
    return (caption or "").strip().split("\n", 1)[0].strip()


def hook_problems(caption: str, limit: int = HOOK_MAX) -> list:
    """Why the caption's first line is not a usable hook (empty list = fine): it must fit before Instagram's '... more'
    (<= `limit` characters), have at least 3 words, and not be only a label, an emoji or a greeting."""
    line = first_line(caption)
    out = []
    if len(line) > limit:
        out.append(f"first line is {len(line)} characters (limit {limit})")
    words = [w for w in line.split() if any(c.isalpha() for c in w)]
    if len(words) < 3:
        out.append(f"first line has {len(words)} words (want at least 3)")
    bare = re.sub(r"^[^\wऀ-ॿ]+|[^\wऀ-ॿ]+$", "", line)
    if _LABEL_ONLY.match(bare) or (bare.isupper() and len(words) < 6) or line.rstrip(" \U0001F447⬇️").endswith(":"):
        out.append(f"first line is only a label: '{line}'")
    if _GREETING.match(bare):
        out.append(f"first line opens with a greeting: '{line}'")
    return out


# ---- LLM output clean-up ----------------------------------------------------------------------------------------------
CHATTER = re.compile(r"^(of course|sure|certainly|absolutely|okay|ok|here(?:'s| is| are)|rewritten|below is)\b[^\n]*$", re.I)


def clean_llm_text(out: str) -> str:
    """Drop what chatty models wrap around the answer: code fences, surrounding quotes and 'Here is the rewritten post:' lines."""
    text = (out or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?|```$", "", text).strip()
    lines = text.split("\n")
    while len(lines) > 1 and (CHATTER.match(lines[0].strip()) or not lines[0].strip()):
        lines.pop(0)
    text = "\n".join(lines).strip()
    if len(text) > 1 and text[0] in "\"'“" and text[-1] in "\"'”":
        text = text[1:-1].strip()
    return text


# ---- Indian number formatting ------------------------------------------------------------------------------------------
LAKH = 100_000
CRORE = 10_000_000


def _trim(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def money(n: int, rent: bool = False) -> str:
    """8500000 -> '₹85 Lakh', 12500000 -> '₹1.25 Cr', 45000 -> '₹45,000' (+ '/month' for rent)."""
    if n >= CRORE:
        s = f"₹{_trim(n / CRORE)} Cr"
    elif n >= LAKH:
        s = f"₹{_trim(n / LAKH)} Lakh"
    else:
        s = f"₹{n:,}"
    return s + "/month" if rent else s


def sqft(n: int) -> str:
    return f"{n:,} sq ft"


def bhk_label(b: float) -> str:
    return f"{int(b)} BHK" if float(b).is_integer() else f"{b:g} BHK"


# ---- Indian mobile numbers ---------------------------------------------------------------------------------------------
_INDIAN_MOBILE = re.compile(r"^[6-9]\d{9}$")


def normalize_indian_mobile(raw: str) -> str:
    """Return the number as +91XXXXXXXXXX or raise ValueError.

    Accepts '+91 98765 43210', '098765-43210', '919876543210', '9876543210'.
    """
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if not _INDIAN_MOBILE.match(digits):
        raise ValueError("Enter a valid 10-digit Indian mobile number")
    return f"+91{digits}"
