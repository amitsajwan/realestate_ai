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
  3. Automatic pass (always on; the owner's rules are the switch). A lead of the owner's that came in PASS_DELAY to AUTO_WINDOW ago,
     is not won or lost and was never passed goes to the agent a rule in `lead_routes` names (its project page, the project's area,
     or an area they named: InboxService.route_for), through the same InboxService.pass_lead as the Studio button, so the agent gets
     the full handover card. PASS_DELAY leaves the auto follow-up its turn first (the template goes from Avasetu, then the agent
     calls). Tried once per lead (`auto_pass_at`); the owner gets one 'lead_auto_passed' alert saying who it went to and whether
     the WhatsApp to the agent went out.
  4. Agent site enquiry (always on). A form lead that came straight to an agent (their own site, not the owner's) in the last
     AGENT_WA_WINDOW and was never passed is sent to that agent on WhatsApp from our number, as the same card and approved template
     a pass uses (InboxService.tell_agent_of_lead), to their office number when the site has one (owner, 2026-10-30: House Deal's
     enquiries reach them on WhatsApp through Avasetu). Tried once per lead (`agent_wa_at`, `agent_wa_status`). The owner follows
     these like passes: `watched_by` puts the lead in their Leads > Passed (read only) and they get one 'agent_site_enquiry' alert.
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
PASS_DELAY = timedelta(minutes=4)
PASSED_KIND = "lead_auto_passed"
MAX_LEADS = 500
AGENT_WA_WINDOW = timedelta(hours=1)    # a lead from before this step went live is not sent late


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


async def auto_passes(db, inbox, owner: str, now: datetime, notify: Optional[Callable] = None) -> int:
    """Pass the owner's fresh leads that a rule names to that rule's agent. Returns how many were passed."""
    if notify is None:
        from app.modules.notifications.service import notify
    if not await db.get_collection("lead_routes").find_one({"owner_id": owner}):
        return 0
    leads = await db.get_collection("contacts").find({
        "agent_id": owner, "created_at": {"$gte": now - AUTO_WINDOW}, "stage": {"$nin": ["won", "lost"]},
        "passed_at": {"$exists": False}, "auto_pass_at": {"$exists": False}}).to_list(MAX_LEADS)
    passed = 0
    for c in leads:
        if c["created_at"] > now - PASS_DELAY:
            continue
        try:
            rule = await inbox.route_for(owner, c, await inbox.project_of(c))
            if not rule:
                continue
            await db.get_collection("contacts").update_one({"_id": c["_id"]}, {"$set": {"auto_pass_at": now}})
            r = await inbox.pass_lead(owner, c["_id"], rule["agent_id"], by="auto", rule=rule)
            await db.get_collection("lead_routes").update_one({"_id": rule["id"]}, {"$inc": {"passed": 1}})
            wa = ("WhatsApp to them sent" if r["whatsapp_status"] in ("sent", "dry_run") else
                  f"WhatsApp to them not sent ({r.get('whatsapp_error') or r['whatsapp_status']}): send it from Studio > Leads > Passed")
            await notify(db, owner, PASSED_KIND, f"{c.get('name') or 'A lead'} went to {r['passed_to']} by your {rule['label']} rule. {wa}.",
                         {"lead_id": r["lead_id"], "whatsapp_url": r.get("whatsapp_url")}, now)
            passed += 1
        except Exception as e:   # InboxError (agent retired, lead gone) or a send failure: kept on the lead, not retried
            log.warning("automatic pass failed for lead %s: %s", c["_id"], e)
            await db.get_collection("contacts").update_one({"_id": c["_id"]}, {"$set": {"auto_pass_error": str(e)[:200]}})
    return passed


SITE_KIND = "agent_site_enquiry"


async def agent_site_enquiries(db, inbox, owner: str, now: datetime, notify: Optional[Callable] = None) -> int:
    """Send each fresh form lead on an agent's own site to that agent's WhatsApp and tell the owner. Returns how many went out."""
    if notify is None:
        from app.modules.notifications.service import notify
    leads = await db.get_collection("contacts").find({
        "agent_id": {"$nin": [owner, None, ""]}, "channel": "form", "created_at": {"$gte": now - AGENT_WA_WINDOW},
        "passed_at": {"$exists": False}, "agent_wa_at": {"$exists": False}}).to_list(MAX_LEADS)
    sent = 0
    for c in leads:
        await db.get_collection("contacts").update_one({"_id": c["_id"]}, {"$set": {"agent_wa_at": now, "watched_by": owner}})
        r: dict = {}
        try:
            r = await inbox.tell_agent_of_lead(c)
            status, error = r["whatsapp_status"], r.get("whatsapp_error")
        except Exception as e:   # InboxError (retired account) or a send failure: kept on the lead, not retried
            status, error = "failed", str(e)[:200]
        if status != "sent":
            log.warning("agent site enquiry %s not sent to the agent: %s %s", c["_id"], status, error)
        await db.get_collection("contacts").update_one({"_id": c["_id"]}, {"$set": {
            "agent_wa_status": status, "agent_wa_error": error, "agent_wa_text": r.get("text")}})
        sent += status == "sent"
        wa = "WhatsApp to them sent" if status in ("sent", "dry_run") else f"WhatsApp to them not sent ({error or status})"
        try:
            await notify(db, owner, SITE_KIND, f"{c.get('name') or 'A buyer'} enquired on {r.get('agent_name') or 'an agent'}'s site. {wa}.",
                         {"lead_id": c["_id"], "screen": f"/studio/leads/{c['_id']}"}, now)
        except Exception:
            log.exception("owner alert for agent site enquiry %s failed", c["_id"])
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
    if owner:
        from app.modules.inbox.service import InboxService
        from app.modules.whatsapp.router import build_service
        inbox = InboxService(db, build_service(db=db), now=lambda: now)
        if auto_on():
            n = await auto_followups(db, inbox, owner, now)
            if n:
                log.info("lead follow-ups: %d sent", n)
        n = await auto_passes(db, inbox, owner, now)
        if n:
            log.info("lead follow-ups: %d passed to agents by rule", n)
        n = await agent_site_enquiries(db, inbox, owner, now)
        if n:
            log.info("lead follow-ups: %d agent site enquiries sent to the agent on WhatsApp", n)
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
