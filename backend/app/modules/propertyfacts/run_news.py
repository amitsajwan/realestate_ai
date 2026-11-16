"""Who hears what about an agent's marketing (owner, 2026-11-07: "how will the agent know the post is ready").

    ready   a run finished: its posts go to the approval calendar by themselves (nothing publishes: calendar.store's PUBLISHABLE
            is still the gate), the owner is told there is something to approve, the agent that it waits for approval
    posted  a post went out: the agent gets one Studio alert and one WhatsApp with the links, once every channel of that post
            has finished, not one message per channel
    results two days later, once per listing, the numbers and the question: boost, keep or remove (owner, 2026-11-07: "you guide"). Asked
            then and not at posting, since nobody can judge a post with no numbers. A tap only tells the owner: nothing here
            spends money or takes a post down, and the tap opens WhatsApp's 24 hours so a person can answer in the Inbox

The owner's id and the WhatsApp sender come from app.wiring: this module knows neither. Nothing here can fail a run or a post.
The ledger `agent_post_news` (written only here) keeps one message per post. Every message lands in the agent's Inbox thread.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.modules.interest.store import Store as InterestStore
from app.modules.notifications.service import notify

log = logging.getLogger(__name__)

TEMPLATE = "agent_post_live_v1"   # UTILITY on our WABA: the body below must match Meta's copy
BODY = ("Namaste {} ji, your post for {} is live on Avasetu's pages.\n\n"
        "Instagram: {}\nFacebook: {}\n\n"
        "Avasetu team")
RESULTS_TEMPLATE = "agent_post_results_v1"   # with quick-reply buttons Boost, Keep, Remove
RESULTS_BODY = ("Namaste {} ji, your posts for {} after 2 days: {}.\n\n"
                "Would you like to boost them, keep them as they are, or remove them? Tap below, or reply here.\n\n"
                "Avasetu team")
RESULTS_AFTER = timedelta(hours=48)
ASK_AGAIN = timedelta(days=7)      # one question a listing a week: a remade campaign does not ask twice
TOO_OLD = timedelta(days=14)       # a post older than this was never going to be asked about
VIEW_KEYS = ("views", "plays", "reach", "fb_reels_total_plays", "blue_reels_play_count", "post_impressions_unique")
LEDGER = "agent_post_news"
FINISHED = ("published", "failed", "skipped", "removed")
NOT_POSTED = "not posted there"

_owner: Callable[[], str] = lambda: ""
_tell: Optional[Callable[..., Awaitable[Any]]] = None


def configure(owner: Callable[[], str], tell: Optional[Callable[..., Awaitable[Any]]] = None) -> None:
    """`tell(db, wa_id, name, template, params, text, about)` sends a template and keeps it in the agent's Inbox thread."""
    global _owner, _tell
    _owner, _tell = owner, tell


def _naive(d: Any) -> Any:
    return d.astimezone(timezone.utc).replace(tzinfo=None) if isinstance(d, datetime) and d.tzinfo else d


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
    await ledger.insert_one({"_id": key, "agent_id": agent_id, "slug": slug, "channels": sorted(links), "listing_id": doc.get("listing_id"),
                             "at": _naive(doc.get("published_at")) or datetime.utcnow(), "asked_at": None})
    listing = await db.get_collection("listings").find_one({"_id": doc.get("listing_id")}) or {}
    name = listing.get("project_name") or listing.get("title") or "your listing"
    await notify(db, agent_id, "post_live", f"Your post for {name} is live.", {"screen": f"/studio/listings/{doc.get('listing_id')}"})
    prof = await db.get_collection("agent_public_profiles").find_one({"agent_id": agent_id}) or {}
    phone = mobile(prof.get("phone"))
    if phone and _tell:
        params = [_first(prof), name, links.get("instagram") or NOT_POSTED, links.get("facebook_page") or NOT_POSTED]
        await _tell(db, phone, prof.get("agent_name") or "", TEMPLATE, params, BODY.format(*params), name)
    return True


def _first(prof: dict) -> str:
    return str(prof.get("agent_name") or "").split(" ")[0] or "there"


async def numbers(store: Any, agent_id: str, listing_id: str) -> str:
    """What the listing's posts have done so far, in words: '1,240 views, 3 enquiries'. Views are the latest snapshot of each row
    (insights.collector); enquiries the "I am interested" presses on its links."""
    db, links = store.db, InterestStore(store.db)
    views = enquiries = 0
    for r in [r for r in await store.all() if r.get("listing_id") == listing_id and r.get("agent_id") == agent_id and r.get("status") == "published"]:
        snaps = await db.get_collection("content_metrics").find({"post_id": r["_id"]}).sort("at", -1).limit(1).to_list(1)
        mets = (snaps[0].get("metrics") if snaps else None) or {}
        views += int(max([v for k, v in mets.items() if k in VIEW_KEYS and isinstance(v, (int, float))] or [0]))
        link = await links.find_link("post", r.get("slug"), "instagram" if r.get("channel") == "instagram" else "facebook")
        enquiries += await links.count(link["code"], "interest") if link else 0
    said = f"{enquiries} enquir{'y' if enquiries == 1 else 'ies'}"
    return f"{views:,} views, {said}" if views else f"views are not in yet, {said}"


async def ask(store: Any, agent_id: str, listing_id: str) -> bool:
    """Send the results and the question for one listing. -> False when there is no one to ask."""
    db = store.db
    prof = await db.get_collection("agent_public_profiles").find_one({"agent_id": agent_id}) or {}
    phone = mobile(prof.get("phone"))
    if not phone or not _tell:
        return False
    listing = await db.get_collection("listings").find_one({"_id": listing_id}) or {}
    name = listing.get("project_name") or listing.get("title") or "your listing"
    params = [_first(prof), name, await numbers(store, agent_id, listing_id)]
    await _tell(db, phone, prof.get("agent_name") or "", RESULTS_TEMPLATE, params, RESULTS_BODY.format(*params), name)
    return True


async def results_due(store: Any, now: Optional[datetime] = None) -> int:
    """The calendar's cycle: ask about each listing whose posts have had two days. -> how many were asked."""
    now = _naive(now or datetime.utcnow())
    ledger = store.db.get_collection(LEDGER)
    asked = 0
    for news in await ledger.find({"asked_at": None}).to_list(200):
        at = news.get("at")
        if not isinstance(at, datetime) or now - at < RESULTS_AFTER:
            continue
        same = await ledger.find({"listing_id": news.get("listing_id"), "agent_id": news.get("agent_id")}).to_list(50)
        recent = any(isinstance(d.get("asked_at"), datetime) and now - d["asked_at"] < ASK_AGAIN for d in same)
        if not recent and now - at < TOO_OLD and await ask(store, news["agent_id"], news.get("listing_id")):
            asked += 1
        await ledger.update_one({"_id": news["_id"]}, {"$set": {"asked_at": now}})
    return asked


async def ask_by_hand(store: Any, wa_id: str) -> bool:
    """The owner's button on an agent's Inbox thread: the same question about the agent's latest post, whenever they choose."""
    db = store.db
    ledger = db.get_collection(LEDGER)
    for prof in await db.get_collection("agent_public_profiles").find({}).to_list(500):
        if mobile(prof.get("phone")) == wa_id:
            rows = await ledger.find({"agent_id": prof.get("agent_id")}).to_list(200)
            rows = sorted((r for r in rows if isinstance(r.get("at"), datetime)), key=lambda r: r["at"])
            return await ask(store, prof["agent_id"], rows[-1].get("listing_id")) if rows else False
    return False
