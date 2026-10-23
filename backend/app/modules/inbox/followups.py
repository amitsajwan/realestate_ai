"""Lead follow-ups that do not wait for a person (owner, 2026-10-23: two website leads sat unanswered for 10 hours and 3 days).

Every INTERVAL_S:
  1. Auto follow-up (LEAD_AUTO_FOLLOWUP=true; off by default: each one is a paid WhatsApp template). A website form lead of the
     owner's own agent (WHATSAPP_OWNER_AGENT_ID) that is still New, has consent and an Indian mobile, came in AUTO_DELAY to
     AUTO_WINDOW ago and nobody has contacted, gets the approved follow-up template, the same path as the Studio button
     (InboxService.start: once per 24 h, STOP respected, lead moves to Contacted, the bot answers their reply). Tried once per lead:
     `auto_followup_at` (+ `auto_followup_error`) is set before anything else, so a crash or a refusal never sends twice.
  2. Waiting alert (always on). A lead whose contact status (tracking/contact.py) is not_contacted or waiting_you for more than
     ALERT_AFTER gets one in-app notification (kind 'lead_waiting') to its agent; `waiting_alert_for` keeps the moment it was
     about, so the same wait is told once and a new wait (they wrote again) is told again. Leads older than ALERT_DAYS are left.
Each lead is handled on its own: an error is logged and the rest go on.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Callable, Optional

from app.core.database import get_database
from app.modules.tracking import contact as contactmod
from app.platform.heartbeats import heartbeat

log = logging.getLogger(__name__)

INTERVAL_S = 300
AUTO_DELAY = timedelta(minutes=2)       # a person who is at the desk may call first
AUTO_WINDOW = timedelta(hours=24)       # older leads are not messaged out of the blue by the machine
ALERT_AFTER = timedelta(hours=2)
ALERT_DAYS = 14
ALERT_KIND = "lead_waiting"
MAX_LEADS = 500


def auto_on() -> bool:
    return os.getenv("LEAD_AUTO_FOLLOWUP", "").strip().lower() in ("1", "true", "yes", "on")


def _owner() -> str:
    from app.modules.whatsapp.config import load
    return load().owner_agent_id or ""


async def auto_followups(db, inbox, owner: str, now: datetime) -> int:
    """Send the follow-up template to fresh, uncontacted form leads of `owner`. Returns how many went out."""
    leads = await db.get_collection("contacts").find({
        "agent_id": owner, "channel": "form", "stage": "new", "created_at": {"$gte": now - AUTO_WINDOW},
        "auto_followup_at": {"$exists": False}}).to_list(MAX_LEADS)
    leads = [c for c in leads if c["created_at"] <= now - AUTO_DELAY and c.get("consent") and contactmod.wa_digits(c.get("phone"))]
    if not leads:
        return 0
    convs = await contactmod.conversations_by_lead(db, leads)
    sent = 0
    for c in leads:
        if contactmod.state_of(c, convs[c["_id"]])["state"] != "not_contacted":
            continue
        await db.get_collection("contacts").update_one({"_id": c["_id"]}, {"$set": {"auto_followup_at": now}})
        try:
            r = await inbox.start(owner, c["_id"], "auto")
            sent += bool(r.get("sent"))
        except Exception as e:   # InboxError (no WhatsApp, STOP, sent already) or a send failure: kept on the lead, not retried
            log.warning("lead follow-up not sent for %s: %s", c["_id"], e)
            await db.get_collection("contacts").update_one({"_id": c["_id"]}, {"$set": {"auto_followup_error": str(e)[:200]}})
    return sent


def _alert_text(c: dict, state: str, waited: timedelta) -> str:
    hours = int(waited.total_seconds() // 3600)
    took = f"{hours // 24} days" if hours >= 48 else f"{hours} hours"
    what = (c.get("last_message") or c.get("message") or "").strip()
    about = f" ({what[:80]})" if what else ""
    if state == "waiting_you":
        return f"{c.get('name') or 'A buyer'} replied {took} ago and is waiting for an answer{about}."
    return f"{c.get('name') or 'A new lead'} came in {took} ago and nobody has contacted them yet{about}."


async def waiting_alerts(db, now: datetime, notify: Optional[Callable] = None) -> int:
    """One alert per wait for leads nobody has reached or answered in ALERT_AFTER. Returns how many alerts."""
    if notify is None:
        from app.modules.notifications.service import notify
    leads = await db.get_collection("contacts").find({
        "stage": {"$nin": ["won", "lost"]}, "created_at": {"$gte": now - timedelta(days=ALERT_DAYS)}}).to_list(MAX_LEADS)
    if not leads:
        return 0
    convs = await contactmod.conversations_by_lead(db, leads)
    told = 0
    for c in leads:
        try:
            s = contactmod.state_of(c, convs[c["_id"]])
            if s["state"] not in ("not_contacted", "waiting_you") or not s["at"] or now - s["at"] < ALERT_AFTER:
                continue
            if c.get("waiting_alert_for") == s["at"]:
                continue
            await notify(db, c["agent_id"], ALERT_KIND, _alert_text(c, s["state"], now - s["at"]),
                         {"lead_id": c["_id"], "screen": f"/studio/leads/{c['_id']}"}, now)
            await db.get_collection("contacts").update_one({"_id": c["_id"]}, {"$set": {"waiting_alert_for": s["at"]}})
            told += 1
        except Exception:
            log.exception("waiting alert failed for lead %s", c.get("_id"))
    return told


async def cycle(db, now: datetime) -> None:
    owner = _owner()
    if auto_on() and owner:
        from app.modules.inbox.service import InboxService
        from app.modules.whatsapp.router import build_service
        n = await auto_followups(db, InboxService(db, build_service(db=db), now=lambda: now), owner, now)
        if n:
            log.info("lead follow-ups: %d sent", n)
    n = await waiting_alerts(db, now)
    if n:
        log.info("lead follow-ups: %d waiting alerts", n)


async def loop() -> None:
    while True:
        try:
            async with heartbeat("lead_followups", get_database):
                await cycle(get_database(), datetime.utcnow())
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("lead follow-ups: cycle failed")
        await asyncio.sleep(INTERVAL_S)
