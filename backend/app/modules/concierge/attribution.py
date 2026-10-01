"""'Listed by' attribution for agents' listings posted on the Avasetu Page and Instagram.

Never includes a phone number: buyers reach the agent through his interest link (Facebook: URL; Instagram: link in bio
via the /go hub).
"""
from app.core import brand
import re
from typing import Optional

from app.modules.interest.service import InterestService, interest_url, upsert_hub_item

from . import config

_DIGITS = re.compile(r"(?:\+?\d[\s-]?){8,}")
IG_LINK_LINE = "Interested? Link in our bio."


def _clean(value) -> str:
    """Text for a caption: collapsed whitespace, and anything phone-number-like removed."""
    return re.sub(r"\s+", " ", _DIGITS.sub("", str(value or ""))).strip(" ,-|")


def attribution_line(profile: dict) -> str:
    """'Listed by <business name or agent name> on Avasetu' plus ' | RERA agent reg: <no>' when known. Empty if no name is known."""
    branding = (profile or {}).get("branding_data") or {}
    name = _clean(branding.get("business_name")) or _clean((profile or {}).get("agent_name"))
    if not name:
        return ""
    line = f"Listed by {name} on {brand.NAME}"
    rera = re.sub(r"[^A-Za-z0-9/ -]", "", str(branding.get("rera_agent_no") or "")).strip()
    if re.fullmatch(r"(?:\+?91)?[6-9]\d{9}", rera.replace(" ", "").replace("-", "")):
        rera = ""  # a mobile number is not a registration number
    return f"{line} | RERA agent reg: {rera}" if rera else line


def _is_sample(listing: dict) -> bool:
    return (listing.get("title") or "").strip().lower().startswith("sample")


async def _eligible_profile(db, agent_id: str, listing: dict) -> Optional[dict]:
    if not agent_id or agent_id in config.owner_agent_ids() or _is_sample(listing):
        return None
    return await db.get_collection("agent_public_profiles").find_one({"agent_id": agent_id})


async def attribution_text(db, agent_id: str, listing: dict, channel: str) -> str:
    """Lines added to a caption ('' for the owner's own listings and samples). channel: facebook_page | instagram."""
    profile = await _eligible_profile(db, agent_id, listing)
    line = attribution_line(profile) if profile else ""
    if not line:
        return ""
    if channel == "instagram":
        return f"{line}\n{IG_LINK_LINE}"
    url = await interest_url(db, kind="listing", ref=listing["_id"], agent_id=agent_id, channel="facebook",
                             title=listing.get("title") or "", locality=listing.get("locality") or "")
    return f"{line}\nInterested? {url}"


async def register_hub_item(db, agent_id: str, listing: dict, pack: dict, media_base: str, permalink: str = "") -> None:
    """Put the listing on the /go hub (the Instagram 'link in bio' page) with the agent's interest code."""
    if not await _eligible_profile(db, agent_id, listing):
        return
    from app.modules.social.service import rebase
    link = await InterestService(db).create_link("listing", listing["_id"], agent_id, "instagram",
                                                 title=listing.get("title") or "", locality=listing.get("locality") or "")
    cover = ((pack.get("images") or {}).get("cover") or {}).get("path") or ""
    await upsert_hub_item(db, "listing", listing["_id"], listing.get("title") or "",
                          image_url=rebase(cover, media_base) if cover else "", subtitle=listing.get("locality") or "",
                          interest_code=link["code"], permalink=permalink)
