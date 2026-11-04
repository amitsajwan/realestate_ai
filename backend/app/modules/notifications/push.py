"""Alerts on the agent's phone (Web Push to Studio), for the notifications where a person is waiting (owner, 2026-11-03).

Collection `push_subscriptions` (owned here): one row per phone browser that turned on alerts in Studio,
{_id: endpoint, agent_id, endpoint, keys: {p256dh, auth}, user_agent, created_at, last_sent_at, last_status}. The endpoint is the
id: a phone that subscribes again (new login, another agent on the same phone) takes the row over.

`alert()` runs inside notify(), after the in-app notification is saved, so a failed push never loses the alert: it is still on
the Studio badge. A push service that answers 404 or 410 has forgotten the phone (alerts turned off, app removed): its row goes.
Nothing goes out while the VAPID keys are not set (config.py).
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Awaitable, Callable, Optional, Tuple
from urllib.parse import urlsplit

import httpx

from . import webpush
from .config import PushConfig, load

log = logging.getLogger(__name__)

COLLECTION = "push_subscriptions"
SEND_TIMEOUT_S = 5.0
TTL_S = 6 * 3600          # a phone that is off for longer gets the alert on the Studio badge instead
MAX_BODY = 180            # lock screens show two or three lines
MAX_PER_AGENT = 10        # phones and browsers one agent can have alerts on

# The notifications that ring the phone, each with its title: a buyer, an agent or a request is waiting for a person. The rest
# (the SEO week, answer gaps, content the system could not post) wait on the Studio badge.
TITLES = {
    "new_lead": "New lead",
    "upcoming_registered": "A coming-soon project looks registered",
    "new_chat_lead": "New lead from the website chat",
    "new_whatsapp_lead": "New lead on WhatsApp",
    "new_dm_lead": "New lead in messages",
    "chat_needs_you": "A buyer is waiting in the chat",
    "whatsapp_needs_you": "A buyer is waiting on WhatsApp",
    "dm_needs_you": "A buyer is waiting in messages",
    "whatsapp_reply": "New WhatsApp reply",
    "comment_needs_you": "A comment needs your answer",
    "buyer_passed": "A buyer was passed to you",
    "lead_waiting": "A lead is waiting",
    "agent_site_enquiry": "Enquiry on an agent's site",
    "lead_auto_passed": "A lead was passed on",
    "lead_asked": "An agent asked for a lead",
    "trial_claimed": "New trial claimed",
    "invite_request": "New invite request",
}

# a buyer's number never shows on a lock screen (notify() keeps them out of summaries; this also catches one in a quoted message)
PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")

Post = Callable[[str, dict, bytes], Awaitable[int]]

# Our server POSTs to the endpoint a phone gives it, so only the browsers' own push services are accepted, over https: never an
# address of ours or anyone else's (an internal service, a metadata server). Google's has more than one name: Chrome on Android
# uses fcm.googleapis.com, Chromium builds jmt17.google.com (seen 2026-11-03), so both Google domains are accepted.
PUSH_HOSTS = ("googleapis.com", "google.com", "push.services.mozilla.com", "push.apple.com", "notify.windows.com")


def push_endpoint_ok(endpoint: str) -> bool:
    try:
        parts = urlsplit(endpoint)
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    return (parts.scheme == "https" and not parts.username and not parts.password and parts.port in (None, 443)
            and any(host == h or host.endswith("." + h) for h in PUSH_HOSTS))


def open_url(ref: Optional[dict]) -> str:
    """The Studio screen a tap on the alert opens."""
    ref = ref or {}
    for key in ("screen", "href"):
        v = ref.get(key)
        if isinstance(v, str) and v.startswith("/studio"):
            return v
    if ref.get("lead_id"):
        return f"/studio/leads/{ref['lead_id']}"
    if ref.get("conversation_id"):
        return "/studio/inbox"
    return "/studio"


def message(kind: str, summary: str, ref: Optional[dict]) -> dict:
    """The JSON the phone's service worker shows (studio/public/studio/sw.js). `tag` groups alerts about the same person, so a
    second alert replaces the first instead of stacking."""
    body = PHONE.sub("[number]", summary or "").strip()
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY - 1].rstrip() + "…"
    ref = ref or {}
    tag = ref.get("lead_id") or ref.get("conversation_id") or kind
    return {"title": TITLES.get(kind, "Studio"), "body": body, "url": open_url(ref), "tag": f"{kind}:{tag}"}


async def save(db, agent_id: str, subscription: dict, user_agent: str, now: datetime) -> None:
    """Turn alerts on for one phone browser. The oldest phones beyond MAX_PER_AGENT stop getting them."""
    endpoint = subscription["endpoint"]
    if not push_endpoint_ok(endpoint):
        raise ValueError("Not a browser push service address")
    col = db.get_collection(COLLECTION)
    await col.update_one({"_id": endpoint}, {"$set": {
        "agent_id": agent_id, "endpoint": endpoint, "keys": {"p256dh": subscription["keys"]["p256dh"], "auth": subscription["keys"]["auth"]},
        "user_agent": (user_agent or "")[:300], "created_at": now}}, upsert=True)
    rows = await col.find({"agent_id": agent_id}).sort("created_at", -1).to_list(100)
    for old in rows[MAX_PER_AGENT:]:
        await col.delete_one({"_id": old["_id"]})


async def remove(db, agent_id: str, endpoint: str) -> bool:
    """Turn alerts off for one phone browser (only the agent's own)."""
    res = await db.get_collection(COLLECTION).delete_one({"_id": endpoint, "agent_id": agent_id})
    return bool(getattr(res, "deleted_count", 0))


async def count(db, agent_id: str) -> int:
    return await db.get_collection(COLLECTION).count_documents({"agent_id": agent_id})


async def _post(url: str, headers: dict, body: bytes) -> int:
    async with httpx.AsyncClient(timeout=SEND_TIMEOUT_S) as client:
        res = await client.post(url, headers=headers, content=body)
    if res.status_code >= 400 and res.status_code not in (404, 410):
        log.warning("push to %s answered %s: %s", url.split("/")[2], res.status_code, res.text[:200])
    return res.status_code


async def alert(db, agent_id: str, kind: str, summary: str, ref: Optional[dict] = None, now: Optional[datetime] = None,
                cfg: Optional[PushConfig] = None, post: Optional[Post] = None) -> Tuple[int, int]:
    """Ring every phone of `agent_id` that has alerts on, if `kind` is one that rings. Returns (sent, forgotten). Never raises."""
    cfg = cfg or load()
    if kind not in TITLES or not agent_id or not cfg.enabled:
        return 0, 0
    post = post or _post
    now = now or datetime.utcnow()
    col = db.get_collection(COLLECTION)
    payload = message(kind, summary, ref)
    sent = forgotten = 0
    try:
        subs = await col.find({"agent_id": agent_id}).to_list(MAX_PER_AGENT)
    except Exception:
        log.exception("push: could not read the phones of %s", agent_id)
        return 0, 0
    for sub in subs:
        if not push_endpoint_ok(sub.get("endpoint") or ""):   # saved before a rule change: never posted to
            continue
        try:
            url, headers, body = webpush.request(sub, payload, cfg.public_key, cfg.private_key, cfg.subject, ttl=TTL_S)
            status = await asyncio.wait_for(post(url, headers, body), SEND_TIMEOUT_S + 1)
        except Exception as e:
            log.warning("push to a phone of %s failed: %s", agent_id, e)
            status = 0
        if status in (404, 410):
            await col.delete_one({"_id": sub["_id"]})
            forgotten += 1
            continue
        await col.update_one({"_id": sub["_id"]}, {"$set": {"last_sent_at": now, "last_status": status}})
        sent += 200 <= status < 300
    return sent, forgotten
