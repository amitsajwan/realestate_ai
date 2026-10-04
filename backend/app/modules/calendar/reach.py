"""Reach: a few targeted hashtags per audience (agents or buyers) and an Instagram location tag (Pune or the project's area).

Applied to every calendar row just before it is published. Hashtags already in the caption are replaced, not added to:
3 to 5 specific tags beat 30 generic ones. Location tags need Facebook place ids; they come from the environment
(IG_LOCATION_PUNE, IG_LOCATION_KHARADI, IG_LOCATION_UPPER_KHARADI, IG_LOCATION_WAGHOLI) and are simply left out when unset.
"""
import os
import re
from typing import List, Optional

_TAG = re.compile(r"(?<![\w&])#\w+")
_TAG_LINE = re.compile(r"^\s*(?:#\w+\s*)+$")

AGENT_TAGS = ["#PuneRealEstate", "#RealEstateAgentPune", "#PuneBrokers", "#ChannelPartner", "#PuneProperty"]
AREA_TAGS = {
    "upper_kharadi": ["#UpperKharadi", "#KharadiPune"],
    "kharadi": ["#KharadiPune", "#KharadiFlats"],
    "wagholi": ["#WagholiPune", "#WagholiHomes"],
}
BUYER_TAGS = ["#PuneProperty", "#MahaRERA", "#PuneHomes"]
AGENT_SOURCES = ("promo_agents", "promo_agents_v2")
PER_CHANNEL = {"instagram": 5, "facebook_page": 3}


def audience(doc: dict) -> str:
    """'agents' for our recruitment posts, 'buyers' for everything else (projects, homes, news, guides)."""
    src = str((doc.get("creative") or {}).get("source") or "")
    return "agents" if src in AGENT_SOURCES or str(doc.get("slug", "")).startswith("promo") else "buyers"


def area(doc: dict) -> Optional[str]:
    text = (doc.get("caption") or "").lower()
    if "upper kharadi" in text:
        return "upper_kharadi"
    if "kharadi" in text:
        return "kharadi"
    if "wagholi" in text:
        return "wagholi"
    return None


def hashtags(doc: dict) -> List[str]:
    n = PER_CHANNEL.get(doc.get("channel", ""), 3)
    if audience(doc) == "agents":
        return AGENT_TAGS[:n]
    tags = AREA_TAGS.get(area(doc) or "", []) + BUYER_TAGS
    return list(dict.fromkeys(tags))[:n]


def with_hashtags(caption: str, tags: List[str]) -> str:
    """The caption without its own hashtags (lines of only tags dropped, inline tags removed), plus one line of `tags`."""
    lines = [ln for ln in (caption or "").splitlines() if not _TAG_LINE.match(ln)]
    body = "\n".join(_TAG.sub(lambda m: m.group(0)[1:], ln).rstrip() for ln in lines).rstrip()  # "#Wagholi" -> "Wagholi"
    body = re.sub(r"\n{3,}", "\n\n", body)
    return f"{body}\n\n{' '.join(tags)}" if tags else body


def location_id(doc: dict) -> Optional[str]:
    """The Facebook place id for the row's area, else Pune; None when not configured (the post goes out without one)."""
    if doc.get("channel") != "instagram":
        return None
    keys = ([area(doc).upper()] if area(doc) else []) + ["PUNE"]
    for k in keys:
        v = (os.environ.get(f"IG_LOCATION_{k}") or "").strip()
        if v.isdigit():
            return v
    return None


def apply(doc: dict) -> dict:
    return {**doc, "caption": with_hashtags(doc.get("caption", ""), hashtags(doc))}
