"""Keeping the calendar honest about what is really on Facebook and Instagram, without anyone telling it.

- duplicate_of(doc, rows): a published row on the same channel, in the last DUPLICATE_DAYS, that opens with the same line. The runner
  holds such a row back instead of posting the same thing twice, and Studio shows the warning before it is approved.
- check_published(store, exists, ...): a few published rows per runner pass (the least recently checked first) are looked up on the
  platform; one that is gone twice, CONFIRM_AFTER apart (deleted by the owner on Facebook or Instagram, or by a clean-up), becomes
  "removed", which takes it out of Studio and the public feed. A lookup that cannot tell (network, permissions) changes nothing.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, List, Optional

import httpx

from .store import Store, aware

log = logging.getLogger(__name__)

DUPLICATE_DAYS = 60
CHECK_EVERY = timedelta(hours=6)   # a published row is looked up at most this often
CHECK_PER_PASS = 8                 # rows looked up per runner pass (each pass is a couple of minutes apart)
CONFIRM_AFTER = timedelta(minutes=30)  # "gone" must be seen twice this far apart: a brief permission hiccup removes nothing

Exists = Callable[[dict], Awaitable[Optional[bool]]]   # True: still there; False: gone; None: cannot tell


def opening(caption: str) -> str:
    """The first non-empty line, lower-case letters and digits only: what a reader sees first."""
    line = next((l for l in (caption or "").splitlines() if l.strip()), "")
    return re.sub(r"[^a-z0-9]+", " ", line.lower()).strip()


def duplicate_of(doc: dict, rows: List[dict], now: Optional[datetime] = None) -> Optional[dict]:
    key = opening(doc.get("caption", ""))
    if len(key) < 12:  # too short to say two posts are the same
        return None
    now = now or datetime.now(timezone.utc)
    for r in rows:
        if r["_id"] == doc["_id"] or r.get("status") != "published" or r.get("channel") != doc.get("channel"):
            continue
        at = r.get("published_at")
        if isinstance(at, datetime) and now - aware(at) > timedelta(days=DUPLICATE_DAYS):
            continue
        if opening(r.get("caption", "")) == key:
            return r
    return None


async def check_published(store: Store, exists: Exists, now: datetime, per_pass: int = CHECK_PER_PASS) -> dict:
    out = {"checked": 0, "removed": 0, "unknown": 0}
    rows = [d for d in await store.all() if d.get("status") == "published" and d.get("external_id")]
    def wait(d):
        return CONFIRM_AFTER if isinstance(d.get("live_gone_at"), datetime) else CHECK_EVERY
    due = [d for d in rows if not isinstance(d.get("live_checked_at"), datetime) or now - aware(d["live_checked_at"]) >= wait(d)]
    due.sort(key=lambda d: aware(d["live_checked_at"]) if isinstance(d.get("live_checked_at"), datetime) else datetime.min.replace(tzinfo=timezone.utc))
    for d in due[:per_pass]:
        try:
            alive = await exists(d)
        except Exception:
            log.exception("calendar: live check failed for %s", d["_id"])
            alive = None
        out["checked"] += 1
        if alive is False and isinstance(d.get("live_gone_at"), datetime):
            await store.mark_removed(d["_id"], "no longer on the platform (deleted there)")
            out["removed"] += 1
            continue
        out["unknown"] += alive is None
        await store.checked_live(d["_id"], gone=now if alive is False else None, clear=alive is True)
    return out


def graph_exists(social, transport: Optional[httpx.AsyncBaseTransport] = None) -> Exists:
    """Ask the Graph API whether a published post is still there. Meta answers code 100 for an object that does not exist; a post
    on another Page (an old Page we no longer manage) also counts as gone from ours."""
    async def exists(doc: dict) -> Optional[bool]:
        ext = str(doc.get("external_id") or "")
        if doc.get("channel") == "facebook_page" and "_" in ext and social.page_id and not ext.startswith(social.page_id + "_"):
            return False
        if not social.page_token:
            return None
        url = f"https://graph.facebook.com/{social.graph_version}/{ext}"
        async with httpx.AsyncClient(timeout=20, transport=transport) as c:
            r = await c.get(url, params={"fields": "id", "access_token": social.page_token})
        try:
            body = r.json()
        except ValueError:
            return None
        if "error" not in body:
            return True
        return False if int((body["error"] or {}).get("code") or 0) == 100 else None
    return exists
