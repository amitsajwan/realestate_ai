"""Who hears what about an agent's marketing (owner, 2026-11-07: "how will the agent know the post is ready").

    ready   a run finished: its posts go to the approval calendar by themselves (nothing publishes: calendar.store's PUBLISHABLE
            is still the gate), the owner is told there is something to approve, the agent that it waits for approval
    posted  a post went out: the agent gets one Studio alert and one WhatsApp with the links, once every channel of that post
            has finished, not one message per channel

The owner's id and the WhatsApp sender come from app.wiring: this module knows neither. Nothing here can fail a run or a post.
The ledger `agent_post_news` (written only here) keeps one message per post.
"""
import logging
import re
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.modules.notifications.service import notify

log = logging.getLogger(__name__)

TEMPLATE = "agent_post_live_v1"   # UTILITY on our WABA: the body below must match Meta's copy
BODY = ("Namaste {} ji, your post for {} is live on Avasetu's pages.\n\n"
        "Instagram: {}\nFacebook: {}\n\n"
        "Avasetu team")
LEDGER = "agent_post_news"
FINISHED = ("published", "failed", "skipped", "removed")
NOT_POSTED = "not posted there"

_owner: Callable[[], str] = lambda: ""
_tell: Optional[Callable[[str, List[str]], Awaitable[Any]]] = None


def configure(owner: Callable[[], str], tell: Optional[Callable[[str, List[str]], Awaitable[Any]]] = None) -> None:
    global _owner, _tell
    _owner, _tell = owner, tell


def mobile(phone: Any) -> str:
    """An Indian mobile as WhatsApp wants it, or ""."""
    d = re.sub(r"\D", "", str(phone or ""))
    d = "91" + d if len(d) == 10 else d
    return d if len(d) == 12 and d.startswith("91") and d[2] in "6789" else ""


async def ready(db: Any, agent_id: str, listing: dict, posts: int, reels: int, now: Optional[datetime] = None) -> None:
    """The alerts for a finished run, whose posts are already in the calendar."""
    what = " and ".join(x for x in (f"{posts} post{'s' if posts != 1 else ''}" if posts else "",
                                    f"{reels} reel{'s' if reels != 1 else ''}" if reels else "") if x)
    name = listing.get("project_name") or listing.get("title") or "your listing"
    owner = _owner()
    if owner and owner != agent_id:
        await notify(db, owner, "agent_posts_ready", f"{what} ready to approve: {name}.", {"screen": "/studio/content"}, now)
    await notify(db, agent_id, "posts_waiting_approval", f"Your {what} for {name} are ready. They go out once the Avasetu team approves them.",
                 {"screen": f"/studio/listings/{listing['_id']}"}, now)


async def posted(store: Any, doc: dict) -> bool:
    """Called for each calendar row that went out. -> True when the agent was told. Only an agent's campaign rows count, and
    only when every channel of that post has finished, so a post gives one message with both links."""
    agent_id, slug = doc.get("agent_id"), doc.get("slug")
    if not doc.get("campaign_run") or not agent_id or agent_id == _owner():
        return False
    rows = [r for r in await store.all() if r.get("slug") == slug and r.get("agent_id") == agent_id]
    if not rows or any(r.get("status") not in FINISHED for r in rows):
        return False
    links: Dict[str, str] = {r["channel"]: r.get("permalink") or "" for r in rows if r.get("status") == "published"}
    if not links:
        return False
    db = store.db
    ledger = db.get_collection(LEDGER)
    key = f"{agent_id}:{slug}"
    if await ledger.find_one({"_id": key}):
        return False
    await ledger.insert_one({"_id": key, "agent_id": agent_id, "slug": slug, "channels": sorted(links)})
    listing = await db.get_collection("listings").find_one({"_id": doc.get("listing_id")}) or {}
    name = listing.get("project_name") or listing.get("title") or "your listing"
    await notify(db, agent_id, "post_live", f"Your post for {name} is live.", {"screen": f"/studio/listings/{doc.get('listing_id')}"})
    prof = await db.get_collection("agent_public_profiles").find_one({"agent_id": agent_id}) or {}
    phone = mobile(prof.get("phone"))
    if phone and _tell:
        first = str(prof.get("agent_name") or "").split(" ")[0] or "there"
        await _tell(phone, [first, name, links.get("instagram") or NOT_POSTED, links.get("facebook_page") or NOT_POSTED])
    return True
