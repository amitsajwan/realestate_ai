"""Who else sells this project: classify web-search results for a MahaRERA registration number.

Given a `regno`, reads the most-recent `web_search_results` document (kind="project") and the project
record's promoter/name, then puts every result URL into one of four buckets:

  portals  – a curated fixed list of real-estate listing portals active in India
  builder  – the promoter's or project's own microsite (domain contains promoter key-words)
  agents   – every other marketer: channel partners, aggregator microsites, etc.
  platform – agents on avasetu.in whose live listings carry the same MahaRERA number

Rows are excluded when the site is in websearch.NOT_MARKETERS (us, the regulator, social media,
encyclopaedias) or when the search result is a "related" / "question" type, not an actual page.

Portal inclusion criteria (each decided once, documented here):
  99acres.com      – pure listing portal, nationwide
  housing.com      – pure listing portal
  magicbricks.com  – pure listing portal
  nobroker.in      – listing portal (no broker model)
  squareyards.com  – listing portal + brokerage
  makaan.com       – listing portal (Quikr group)
  proptiger.com    – listing portal + advisory
  ghar.tv          – listing portal, mostly Pune/Maharashtra
  commonfloor.com  – listing portal (Quikr group)
  nestaway.com     – listing portal (rentals, included for completeness)
  quikr.com        – classifieds portal, significant real-estate section
  beyondwalls.com  – listing portal, builder-developer focus
  bookmywing.com   – listing portal, Pune-area focus
  housiey.com      – listing portal, no agent or channel-partner function
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.modules.areastats.text import promoter_key
from app.modules.areastats.websearch import NOT_MARKETERS, site as _site

# ---------------------------------------------------------------------------
# Portal domains – exact match (websearch.site() already strips "www.").
# ---------------------------------------------------------------------------
PORTALS: frozenset[str] = frozenset([
    "99acres.com",
    "housing.com",
    "magicbricks.com",
    "nobroker.in",
    "squareyards.com",
    "makaan.com",
    "proptiger.com",
    "ghar.tv",
    "commonfloor.com",
    "nestaway.com",
    "quikr.com",
    "beyondwalls.com",
    "bookmywing.com",
    "housiey.com",
])

_ALPHA = re.compile(r"[a-z0-9]+")

OWN_SITE = "avasetu.in"


# ---------------------------------------------------------------------------
# Pure classification (no I/O – easy to unit-test)
# ---------------------------------------------------------------------------

def classify(link: str, project_name: str, promoter: str) -> Optional[str]:
    """Return "portals" | "builder" | "agents", or None to exclude.

    None is returned for:
    - empty or unresolvable links
    - sites in NOT_MARKETERS (our own site, the regulator, social media …)
    - our own domain (avasetu.in) – platform entries come from a DB query, not the search
    """
    s = _site(link)
    if not s:
        return None
    # Exclude our own domain and all NOT_MARKETERS
    if s == OWN_SITE or s.endswith("." + OWN_SITE):
        return None
    if any(s == n or s.endswith("." + n) for n in NOT_MARKETERS):
        return None

    if s in PORTALS:
        return "portals"

    # Builder detection: promoter key words or project name words present in the hostname.
    host_slug = "".join(_ALPHA.findall(s.lower()))

    def _words_in_host(text: str) -> bool:
        parts = _ALPHA.findall(text.lower())
        return bool(parts) and all(p in host_slug for p in parts)

    pkey = promoter_key(promoter)
    if (pkey and _words_in_host(pkey)) or (project_name and _words_in_host(project_name)):
        return "builder"

    return "agents"


def _to_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "site": _site(raw.get("link", "")),
        "title": (raw.get("title") or "").strip(),
        "link": (raw.get("link") or "").strip(),
        "position": raw.get("position"),
        "ad": bool(raw.get("ad")),
    }


# ---------------------------------------------------------------------------
# Main async entry point
# ---------------------------------------------------------------------------

async def sellers(db: Any, regno: str) -> Dict[str, Any]:
    """Return seller groups for a MahaRERA project registration number.

    Returns::

        {
          "searched_at": datetime | None,
          "query":       str | None,
          "groups": {
            "agents":   [row, ...],   # channel partners and microsites, shown first
            "builder":  [row, ...],
            "portals":  [row, ...],
            "platform": [row, ...],   # agents on avasetu.in with a live listing for this project
          }
        }

    An empty result (all groups empty, searched_at None) means the web search has not yet run
    for this project; the API returns it rather than a 404 so the card can say "not searched yet".
    """
    groups: Dict[str, List[Dict[str, Any]]] = {
        "agents": [],
        "builder": [],
        "portals": [],
        "platform": [],
    }
    searched_at: Optional[datetime] = None
    query: Optional[str] = None

    # ----------------------------------------------------------------
    # 1. Project record: promoter name and project name for builder detection
    # ----------------------------------------------------------------
    project_doc: Dict[str, Any] = await db.get_collection("projects").find_one({"_id": regno}) or {}
    project_name: str = (project_doc.get("name") or "").strip()
    promoter: str = (project_doc.get("promoter") or "").strip()

    # ----------------------------------------------------------------
    # 2. web_search_results (kind == "project") – most recent for this regno
    # ----------------------------------------------------------------
    seen_links: set[str] = set()
    cursor = db.get_collection("web_search_results").find(
        {"regno": regno, "kind": "project"}
    ).sort("at", -1).limit(1)
    async for doc in cursor:
        searched_at = doc.get("at")
        query = doc.get("_id")  # _id is the query string
        for item in doc.get("results") or []:
            # Skip non-page entries (related searches, "people also ask")
            if item.get("type") in ("related", "question"):
                continue
            link = (item.get("link") or "").strip()
            if not link or link in seen_links:
                continue
            group = classify(link, project_name, promoter)
            if group:
                seen_links.add(link)
                groups[group].append(_to_row(item))

    # ----------------------------------------------------------------
    # 3. Platform agents: live listings for this regno on avasetu.in
    #    Show name + profile link only; never phone numbers.
    # ----------------------------------------------------------------
    profiles_coll = db.get_collection("agent_public_profiles")
    listings_coll = db.get_collection("listings")

    # Collect distinct agent IDs that have a live/under-offer listing for this rera_no
    agent_ids: set[str] = set()
    async for lst in listings_coll.find(
        {"rera_no": regno, "status": {"$in": ["live", "under_offer"]}}
    ):
        aid = lst.get("agent_id")
        if aid:
            agent_ids.add(str(aid))

    for aid in agent_ids:
        profile = await profiles_coll.find_one({"agent_id": aid})
        if not profile:
            continue
        slug = profile.get("slug") or ""
        name = (profile.get("display_name") or profile.get("agent_name") or "").strip()
        if not name:
            first = (profile.get("first_name") or "").strip()
            last = (profile.get("last_name") or "").strip()
            name = f"{first} {last}".strip() or slug or aid
        if slug:
            link = f"https://{OWN_SITE}/{slug}"
        else:
            link = f"https://{OWN_SITE}"
        groups["platform"].append({
            "site": OWN_SITE,
            "title": name,
            "link": link,
            "position": None,
            "ad": False,
        })

    return {"searched_at": searched_at, "query": query, "groups": groups}
