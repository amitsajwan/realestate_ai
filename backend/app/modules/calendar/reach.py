"""Reach: a few targeted hashtags per audience (agents or buyers) and an Instagram location tag (Pune or the project's area).

Applied to every calendar row just before it is published. Hashtags already in the caption are replaced, not added to:
3 to 5 specific tags beat 30 generic ones. Areas, their spellings and their hashtags come from app.core.areas (one list for
every module). Location tags need Facebook place ids; they come from the environment, one per area (`Area.location_env`,
e.g. IG_LOCATION_WAGHOLI) with IG_LOCATION_PUNE as the fallback, and are simply left out when unset.
"""
import os
import re
from typing import List, Optional

from app.core import areas as pune_areas

_TAG = re.compile(r"(?<![\w&])#\w+")
_TAG_LINE = re.compile(r"^\s*(?:#\w+\s*)+$")

AGENT_TAGS = ["#PuneRealEstate", "#RealEstateAgentPune", "#PuneBrokers", "#ChannelPartner", "#PuneProperty"]
BUYER_TAGS = ["#PuneProperty", "#MahaRERA", "#PuneHomes"]
AGENT_SOURCES = ("promo_agents", "promo_agents_v2")
PER_CHANNEL = {"instagram": 5, "facebook_page": 3}


def audience(doc: dict) -> str:
    """'agents' for our recruitment posts, 'buyers' for everything else (projects, homes, news, guides)."""
    src = str((doc.get("creative") or {}).get("source") or "")
    return "agents" if src in AGENT_SOURCES or str(doc.get("slug", "")).startswith("promo") else "buyers"


def area(doc: dict) -> Optional[pune_areas.Area]:
    """The row's area: its explicit `area` key (set by the daily-reel rows) when known, else the most specific area the
    caption names; None when it names none of ours."""
    explicit = pune_areas.get(str(doc.get("area") or ""))
    if explicit:
        return explicit
    named = pune_areas.named_in(doc.get("caption") or "")
    return named[0] if named else None


def hashtags(doc: dict) -> List[str]:
    n = PER_CHANNEL.get(doc.get("channel", ""), 3)
    if audience(doc) == "agents":
        return AGENT_TAGS[:n]
    a = area(doc)
    tags = list(a.hashtags if a else ()) + BUYER_TAGS
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
    a = area(doc)
    for env in ([a.location_env] if a else []) + ["IG_LOCATION_PUNE"]:
        v = (os.environ.get(env) or "").strip()
        if v.isdigit():
            return v
    return None


def apply(doc: dict) -> dict:
    return {**doc, "caption": with_hashtags(doc.get("caption", ""), hashtags(doc))}
