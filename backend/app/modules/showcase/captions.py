"""Hook-first captions for the showcase posts. Deterministic template first; optional LLM polish with hard guards.

Facts come ONLY from the sample dataset. Every caption says 'Sample listing' and 'Illustrative home, not available for sale;
real agent listings coming'. Instagram: no URLs, 'link in our bio', 3 to 8 hashtags. Facebook: may link to the /localities page.
"""
from app.core import brand
import hashlib
import os
import re
from typing import List, Optional

from app.platform.text import HYPE, PHONE, clean_llm_text

from .samples import AGENTS_CTA, RERA_LINE, SAMPLE_LABEL, SAMPLE_NOTE, ICON_LABELS, Home, area_lines

URL = re.compile(r"(https?://|www\.|\b[a-z0-9-]+\.(com|in|io|app|org|net)\b)", re.I)
HASHTAG = re.compile(r"#\w+")
LABEL_LINE = f"{SAMPLE_LABEL}. {SAMPLE_NOTE}."
IG_CTA = "Comment INTERESTED for details on this sample."
IG_AGENTS = "Agents: list your homes free, link in our bio."


def site_url() -> str:
    return brand.site()


def hook(h: Home) -> str:
    """One of a few hook lines, chosen deterministically per home so a run of posts does not repeat the same opening."""
    opts = [
        f"{h.bhk} BHK in {h.locality}, {h.carpet_text} carpet: here is how a home looks on {brand.NAME}.",
        f"What does a {h.bhk} BHK in {h.locality} look like? Swipe to see this sample home.",
        f"A {h.bhk} BHK in {h.locality}, {h.possession.split(',')[0].lower()}: take a look inside this sample.",
    ]
    return opts[int(hashlib.md5(h.slug.encode()).hexdigest(), 16) % len(opts)]


def facts_block(h: Home) -> str:
    amen = ", ".join(ICON_LABELS[a].lower() for a in h.amenities[:5])
    poss = h.possession
    lines = [
        f"{h.bhk} BHK | {h.carpet_text} carpet area | {h.floor_text}",
        f"{poss} | {h.furnishing}",
        f"Amenities: {amen}",
        f"Sample price: {h.price_text} (an illustrative figure)",
        RERA_LINE,
    ]
    return "\n".join(lines)


def hashtags(h: Home) -> List[str]:
    loc = "".join(w.capitalize() for w in h.locality.split())
    tags = [f"#{loc}", "#PuneRealEstate", f"#{h.bhk}BHK", "#PuneProperty", "#SampleListing", "#HomeBuyers"]
    if h.locality == "Wagholi" or "Kharadi" in h.locality:
        tags.append("#PuneHomes")
    return tags[:7]


def instagram_body(h: Home) -> str:
    return "\n\n".join([hook(h), LABEL_LINE, facts_block(h), area_lines(h)[0], f"{IG_CTA}\n{IG_AGENTS}"])


def instagram_caption(h: Home, body: Optional[str] = None) -> str:
    return (body or instagram_body(h)) + "\n\n" + " ".join(hashtags(h))


def facebook_caption(h: Home, body: Optional[str] = None) -> str:
    base = body or "\n\n".join([hook(h), LABEL_LINE, facts_block(h), area_lines(h)[0],
                                "Comment INTERESTED for details on this sample. Agents: list your homes free on " + brand.NAME + "."])
    return base + f"\n\nArea guides: {site_url()}/localities"


# ---- optional LLM polish -------------------------------------------------------------------------------------
POLISH_SYSTEM = (
    "You are a careful copywriter for an Indian real-estate page. Rewrite the post so it reads warmer and more natural, keeping "
    "the SAME facts, same order and about the same length. Keep every number, price, area, locality, the words 'Sample listing', "
    "'Comment INTERESTED' and 'link in our bio' EXACTLY. NEVER add facts, amenities, distances, nearby places, prices, promises, "
    "superlatives (best, perfect, dream, luxurious), phone numbers, links or hashtags. Output ONLY the rewritten post."
)


def _numbers(s: str) -> set:
    return set(re.findall(r"\d[\d,\.]*", s))


def protected(h: Home, channel: str) -> List[str]:
    need = [SAMPLE_LABEL, "not available for sale", h.price_text, f"{h.carpet_sqft:,}", h.locality, f"{h.bhk} BHK", "real agent listings coming"]
    if channel == "instagram":
        need += ["Comment INTERESTED", "link in our bio"]
    return need


def accept(draft: str, polished: Optional[str], h: Home, channel: str) -> bool:
    """A polished text is rejected (the draft is kept) if it drops a protected fact, invents a number, a phone, a URL (Instagram),
    a hashtag or hype, or grows more than 25%."""
    if not polished or not polished.strip():
        return False
    if len(polished) > len(draft) * 1.25 or len(polished) < len(draft) * 0.5:
        return False
    if not all(x in polished for x in protected(h, channel)):
        return False
    if PHONE.search(polished) or HYPE.search(polished) or HASHTAG.search(polished):
        return False
    if URL.search(polished) and not URL.search(draft):
        return False
    return _numbers(polished) <= _numbers(draft)


async def polish(llm, draft: str, h: Home, channel: str) -> str:
    """LLM re-wording through any client with `text(system, user)`; any failure or guard rejection keeps the draft."""
    if llm is None:
        return draft
    try:
        out = await llm.text(POLISH_SYSTEM, f"POST:\n{draft}")
    except Exception:
        return draft
    out = clean_llm_text(out or "")
    return out.strip() if accept(draft, out, h, channel) else draft


async def build_caption(h: Home, channel: str, llm=None) -> str:
    """The caption to publish: deterministic, or LLM-polished if `llm` is given and passes the guards."""
    if channel == "instagram":
        return instagram_caption(h, await polish(llm, instagram_body(h), h, "instagram"))
    base = facebook_caption(h)
    body = base.rsplit("\n\nArea guides:", 1)[0]
    return facebook_caption(h, await polish(llm, body, h, "facebook"))


def validate(caption: str, channel: str) -> List[str]:
    """Problems in a finished caption (empty list = fine). Used by publish and tests."""
    bad = []
    low = caption.lower()
    if SAMPLE_LABEL.lower() not in low:
        bad.append("missing the 'Sample listing' label")
    if "not available for sale" not in low or "real agent listings coming" not in low:
        bad.append("missing the sample disclaimer")
    if PHONE.search(caption):
        bad.append("phone number")
    if HYPE.search(caption):
        bad.append("hype word")
    if channel == "instagram":
        if URL.search(caption):
            bad.append("URL in an Instagram caption")
        if "link in our bio" not in low:
            bad.append("missing 'link in our bio'")
        n = len(HASHTAG.findall(caption))
        if not 3 <= n <= 8:
            bad.append(f"{n} hashtags (need 3 to 8)")
    return bad
