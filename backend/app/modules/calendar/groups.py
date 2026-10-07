"""What a calendar row is about, for Studio > Content's type filter: listings | news | guides | agents | other.

Pure: decided from the row's kind, slug and creative (source, role, template). Sources in the calendar (2026-10):
  campaign (Studio "Start marketing", slug campaign-<listing id>-<angle>), agentprojects (agent project posts and reels, hd-*)
      -> listings
  area_insight (area reels from MahaRERA records), newsroom / news -> news. The newsroom itself posts to the Page directly
      (newsroom.adapters), not through this calendar, so today only the area reels land here.
  library (evergreen guide posts), trend_reels (explainers), reel with template tip, role guide -> guides
  promo_agents, promo_agents_v2, agent_reels (reach.audience "agents"), agent (product posts for agents), role agent,
      reel with template pitch -> agents
  home / kind showcase (sample homes, being retired), anything unknown -> other
"""
import re
from typing import Optional

from .reach import audience

GROUPS = ("listings", "news", "guides", "agents", "other")
LISTING_SOURCES = ("campaign", "agentprojects")
NEWS_SOURCES = ("area_insight", "newsroom", "news")
GUIDE_SOURCES = ("library", "trend_reels")
_CAMPAIGN_SLUG = re.compile(r"^campaign-([0-9a-f]{32}|[^-]+)-")


def group_of(doc: dict) -> str:
    c = doc.get("creative") or {}
    src, role, tpl = str(c.get("source") or ""), str(c.get("role") or ""), str(c.get("template") or "")
    slug = str(doc.get("slug") or "")
    if audience(doc) == "agents" or src == "agent" or role == "agent" or tpl == "pitch":
        return "agents"
    if src in LISTING_SOURCES or role in ("listing", "project") or slug.startswith(("campaign-", "hd-")):
        return "listings"
    if src in NEWS_SOURCES or role in ("area", "news"):
        return "news"
    if src in GUIDE_SOURCES or role == "guide" or (src == "reel" and tpl == "tip"):
        return "guides"
    return "other"


def campaign_id(doc: dict) -> Optional[str]:
    """The listing a property-campaign row belongs to (one campaign per listing), else None."""
    c = doc.get("creative") or {}
    slug = str(doc.get("slug") or "")
    if c.get("source") != "campaign" and not slug.startswith("campaign-"):
        return None
    if doc.get("listing_id"):
        return str(doc["listing_id"])
    m = _CAMPAIGN_SLUG.match(slug)
    return m.group(1) if m else None
