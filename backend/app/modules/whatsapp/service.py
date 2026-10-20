"""WhatsApp buyer assistant: one incoming message in, at most one reply out (free, inside the 24-hour window the buyer opened).

Collections
  whatsapp_messages       _id = Meta message id (inbound, the idempotency key) or the sent message id / out-<uuid> (outbound)
  whatsapp_conversations  _id = "<phone_number_id>:<wa_id>": agent, engine state, last 20 messages, last inbound time, opt-out, lead id

Rules
  - Routing: the receiving number's agent (WHATSAPP_NUMBER_AGENTS) > the agent behind an interest code in the text > the owner agent.
  - Answers come from the website chat engine and grounded knowledge (no invented facts or prices, sample homes labelled), in the buyer's language.
  - The buyer started the chat, so we may reply and keep a lead: consent is recorded as that, and they are told once how to stop (STOP).
  - An agent (an account, or a sign-up code sent to this number) is never a buyer: no lead, no buyer greeting; the owner is told and
    the agent gets one 'our team will reply here' every 12 hours. TRIAL claims tell the owner too.
  - After a person replies from the Studio inbox (human_until), the bot stays quiet in that chat and the person is told of each message.
  - Another business's auto-reply bot (the same text again and again, or a burst of messages) gets no more replies for a day, so two bots
    never talk to each other (2026-10-18: 84 messages in 6 minutes); the owner is told once.
  - STOP / UNSUBSCRIBE: opted out, one confirmation, then silence until START.
  - Replies only inside 24 hours of the buyer's last message; otherwise refused and logged (no paid templates yet).
  - Dry run records the reply and sends nothing. Tokens never reach logs or stored errors.
"""
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Callable, Optional

from . import adapters, lang as L
from .brain import ChatBrain
from .config import WhatsAppConfig
from .graph import WhatsAppGraphError

log = logging.getLogger(__name__)

WINDOW = timedelta(hours=24)
MAX_KEPT = 20
MAX_TEXT = 500
MAX_REPLIES_PER_HOUR = 30
AGENT_ACK_EVERY = timedelta(hours=12)
AUTO_QUIET = timedelta(hours=24)      # kept on old chats as auto_until; since 2026-10-20 a flagged chat stays quiet for good (auto_sender)
AUTO_SAME = 3                         # the same text (AUTO_MIN_CHARS or longer) this many times within AUTO_SPAN ...
AUTO_MIN_CHARS = 12                   # "ok" three times is a person
AUTO_BURST = 8                        # ... or this many messages within BURST_SPAN: a bot, not a person
AUTO_SPAN = timedelta(minutes=15)
BURST_SPAN = timedelta(minutes=1)
STOP_RX = re.compile(r"^\W*(stop|stop all|unsubscribe|opt ?out|cancel|end|quit|band karo|बंद करो|बंद|थांबवा)\W*$", re.I)
START_RX = re.compile(r"^\W*(start|unstop|resume|subscribe)\W*$", re.I)
# An agent claiming the free trial ("TRIAL", "free trial", "claim my free trial", ट्रायल): answered with his sign-up code, never as a buyer
TRIAL_RX = re.compile(r"^\W*(?:i\s+want\s+(?:a|the|my)?\s*|claim\s+(?:my\s+|your\s+|the\s+|a\s+)?)?(?:free\s+)?trial\b[\w\s.!]{0,40}$|^\W*(?:फ्री\s+)?ट्रायल", re.I)
MEDIA_TYPES = ("image", "audio", "video", "document", "sticker", "voice")


def _ts(value) -> Optional[datetime]:
    try:
        return datetime.utcfromtimestamp(int(value))
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def mask(phone: str) -> str:
    digits = "".join(ch for ch in phone or "" if ch.isdigit())
    return f"+{digits[:2]} {digits[2:4]}******{digits[-2:]}" if len(digits) >= 8 else "******"


# an agent who is not signed up yet starts the free trial right here, by sending TRIAL
TRIAL_HERE = {
    "en": "Free trial for agents, 1 month free: reply TRIAL here and we send your sign-up code. Details: {url}",
    "hi": "एजेंट्स के लिए फ्री ट्रायल, 1 महीना फ्री: यहीं TRIAL लिखकर भेजें, हम आपका साइन-अप कोड भेज देंगे। जानकारी: {url}",
    "hinglish": "Agents ke liye free trial, 1 mahina free: yahin TRIAL likh kar bhejein, hum aapka sign-up code bhej denge. Details: {url}",
    "mr": "एजंटसाठी फ्री ट्रायल, 1 महिना फ्री: इथेच TRIAL लिहून पाठवा, आम्ही तुमचा साइन-अप कोड पाठवू. माहिती: {url}",
    "mr_latn": "Agents sathi free trial, 1 mahina free: ithech TRIAL lihun pathva, aamhi tumcha sign-up code pathvu. Mahiti: {url}",
}


class WhatsAppService(ChatBrain):
    trial_line = TRIAL_HERE
    def __init__(self, db, cfg: WhatsAppConfig, graph=None, llm=None, now: Callable[[], datetime] = datetime.utcnow):
        self.db, self.cfg, self.graph, self.llm, self.now = db, cfg, graph, llm, now
        self.messages = db.get_collection("whatsapp_messages")
        self.convs = db.get_collection("whatsapp_conversations")

    def _clean(self, text) -> str:
        from app.platform.meta_graph.publisher import sanitize
        return sanitize(text, self.cfg.secrets)

    # ---- webhook intake (called in the request: fast, no network) -------------------------------------------------
    async def claim(self, msg: dict, value: dict) -> bool:
        """Store the inbound message once. False when it was already seen (Meta retries) or has no id."""
        mid = str(msg.get("id") or "")
        if not mid or await self.messages.find_one({"_id": mid}):
            return False
        pid = str(((value.get("metadata") or {}).get("phone_number_id")) or "")
        try:
            await self.messages.insert_one({"_id": mid, "direction": "in", "wa_id": str(msg.get("from") or ""), "phone_number_id": pid,
                                            "type": msg.get("type"), "text": self._text_of(msg)[:1000], "ts": _ts(msg.get("timestamp")) or self.now(),
                                            "received_at": self.now(), "status": "received"})
        except Exception:  # a duplicate key from a concurrent retry
            return False
        return True

    async def status_update(self, st: dict) -> None:
        """Delivery receipts for what we sent (sent / delivered / read / failed)."""
        mid = str(st.get("id") or "")
        if mid and await self.messages.find_one({"_id": mid, "direction": "out"}):
            err = (st.get("errors") or [{}])[0] if st.get("errors") else None
            changes = {"delivery": str(st.get("status") or "")[:20], "delivery_at": self.now()}
            if err:
                changes["error"] = self._clean(f"{err.get('code', '')} {err.get('title') or err.get('message') or ''}")
            await self.messages.update_one({"_id": mid}, {"$set": changes})

    @staticmethod
    def _text_of(msg: dict) -> str:
        t = msg.get("type")
        if t == "text":
            return str((msg.get("text") or {}).get("body") or "")
        if t == "button":
            return str((msg.get("button") or {}).get("text") or "")
        if t == "interactive":
            i = msg.get("interactive") or {}
            r = i.get("button_reply") or i.get("list_reply") or {}
            return str(r.get("title") or "")
        return ""

    # ---- routing ----------------------------------------------------------------------------------------------------
    async def _route(self, conv: dict, pid: str, text: str, now: datetime, referral: Optional[dict] = None) -> None:
        mapped = self.cfg.number_agents.get(pid)
        if mapped:
            conv["agent_id"], conv["routed_by"] = mapped, "number"
        if referral:  # they tapped "Send message" on one of our ads or posts: that post is what they ask about
            origin = await adapters.dm_origin(self.db, "whatsapp", conv["wa_id"], {"media_ids": [referral.get("source_id")],
                                                                                   "urls": [referral.get("source_url")]})
            if origin:
                conv["context"] = origin
        link = await adapters.find_interest_link(self.db, text) if text else None
        if link:
            conv["context"] = adapters.link_context(link, "wrote the code of")
            if not mapped and conv.get("routed_by") in (None, "owner"):
                conv["agent_id"], conv["routed_by"] = adapters.interest_target_agent(link, self.cfg.owner_agent_id), "interest_code"
            await adapters.record_interest_event(self.db, link["code"], f"whatsapp:{conv['wa_id']}", now)
        if not conv.get("agent_id"):
            conv["agent_id"], conv["routed_by"] = self.cfg.owner_agent_id or None, "owner"

    # ---- one message (background task) ------------------------------------------------------------------------------
    async def handle(self, msg: dict, value: dict) -> dict:
        try:
            return await self._handle(msg, value)
        except Exception as e:
            log.error("whatsapp: could not handle message: %s", self._clean(f"{type(e).__name__}: {e}"))
            mid = str(msg.get("id") or "")
            if mid:
                await self.messages.update_one({"_id": mid}, {"$set": {"status": "error", "error": self._clean(str(e))}})
            return {"status": "error"}

    async def _handle(self, msg: dict, value: dict) -> dict:
        now = self.now()
        pid = str((value.get("metadata") or {}).get("phone_number_id") or self.cfg.phone_number_id)
        wa_id = "".join(ch for ch in str(msg.get("from") or "") if ch.isdigit())
        mid = str(msg.get("id") or "")
        if not wa_id:
            return {"status": "ignored"}
        profile = next((c.get("profile") or {} for c in value.get("contacts") or [] if str(c.get("wa_id")) == str(msg.get("from"))), {})
        mtype = msg.get("type") or "unknown"
        text = self._text_of(msg).strip()[:MAX_TEXT]
        sent_at = _ts(msg.get("timestamp")) or now

        cid = f"{pid}:{wa_id}"
        conv = await self.convs.find_one({"_id": cid})
        is_new = conv is None
        if is_new:
            conv = {"_id": cid, "wa_id": wa_id, "phone_number_id": pid, "agent_id": None, "routed_by": None, "name": (profile.get("name") or "")[:60],
                    "data": adapters.new_chat_state("+" + wa_id, profile.get("name")), "messages": [], "created_at": now, "opted_out": False,
                    "notice_sent_at": None, "lead_id": None, "context": None, "language": None, "needs_human_notified": False, "replies": []}
        last_in = conv.get("last_inbound_at")
        conv["last_inbound_at"] = max(sent_at, last_in) if last_in else sent_at
        await self._route(conv, pid, text, now, msg.get("referral"))
        if mtype == "reaction":  # a thumbs-up on our message: nothing to say
            return await self._finish(conv, mid, None, "ignored", now, text, mtype)

        detected = adapters.detect_language(text) if text else "en"
        lang = L.sticky(conv.get("language"), detected, text)
        conv["language"] = lang

        # STOP / START first: respected even before anything else
        if text and STOP_RX.match(text):
            conv["opted_out"], conv["opted_out_at"] = True, now
            await adapters.mark_lead_opt_out(self.db, conv.get("lead_id"), True, now)
            await self._mark_read(pid, mid)
            return await self._finish(conv, mid, L.pick(L.STOPPED, lang), "stopped", now, text, mtype)
        if conv.get("opted_out"):
            if text and START_RX.match(text):
                conv["opted_out"], conv["opted_out_at"] = False, None
                await adapters.mark_lead_opt_out(self.db, conv.get("lead_id"), False, now)
                await self._mark_read(pid, mid)
                return await self._finish(conv, mid, L.pick(L.RESTARTED, lang), "restarted", now, text, mtype)
            log.info("whatsapp: buyer %s has opted out; message stored, no reply", mask(wa_id))
            return await self._finish(conv, mid, None, "opted_out", now, text, mtype)

        await self._mark_read(pid, mid)
        if text and TRIAL_RX.match(text) and adapters.trial_claims_on():
            conv["trial_claimed_at"] = now   # an agent, not a buyer: no lead, no buyer notice
            reply, status = await adapters.claim_trial(self.db, "+" + wa_id, lang, now)
            if status in ("issued", "full") and self.cfg.owner_agent_id:
                who = conv.get("name") or "An agent"
                await adapters.notify(self.db, self.cfg.owner_agent_id, "trial_claimed",
                                      f"{who} claimed the free trial on WhatsApp" + ("" if status == "issued" else " (today's trials are full, request saved)"),
                                      {"conversation_id": cid, "screen": "/studio/agents?tab=signedup"}, now)
            return await self._finish(conv, mid, reply, "trial", now, text, mtype)
        if conv.get("human_until") and conv["human_until"] > now:   # a person on our side answered here (Studio inbox): the bot stays quiet
            to = conv.get("agent_id") or self.cfg.owner_agent_id
            if to:
                await adapters.notify(self.db, to, "whatsapp_reply", f"{conv.get('name') or 'Someone'} replied on WhatsApp: \"{(text or f'[{mtype}]')[:120]}\"",
                                      {"conversation_id": cid, "screen": "/studio/inbox"}, now)
            return await self._finish(conv, mid, None, "held", now, text, mtype)
        # another business's bot never turns into a person: once flagged the chat stays quiet (2026-10-20: after each 24-hour pause
        # +91 80100 00535's bot started the loop again); a person can still answer it from the Studio inbox
        if conv.get("auto_sender") or conv.get("auto_until"):
            return await self._finish(conv, mid, None, "auto_sender", now, text, mtype)
        if self._auto_sender(conv, text, now):
            conv["auto_sender"], conv["auto_until"] = True, now + AUTO_QUIET
            if self.cfg.owner_agent_id:
                await adapters.notify(self.db, self.cfg.owner_agent_id, "whatsapp_auto_sender",
                                      f"{conv.get('name') or mask(wa_id)} looks like an auto-reply bot (\"{(text or '')[:80]}\"): the bot stopped replying in this chat",
                                      {"conversation_id": cid, "screen": "/studio/inbox"}, now)
            log.warning("whatsapp: %s looks like an auto-reply bot; quiet from now on", mask(wa_id))
            return await self._finish(conv, mid, None, "auto_sender", now, text, mtype)
        agent = await adapters.agent_for_phone(self.db, "+" + wa_id, exclude=self.cfg.owner_agent_id)
        if agent:
            return await self._agent_chat(conv, mid, agent, text, lang, now, mtype)
        agent_id = conv.get("agent_id")
        if mtype == "location":
            reply = L.pick(L.LOCATION, lang)
        elif mtype in MEDIA_TYPES or not text:
            reply = L.pick(L.MEDIA, lang)
        else:
            reply = await self._answer(conv, text, lang)
        agent_id = conv.get("agent_id")   # the answer may route the chat (a project's word names its listing's agent)

        if not agent_id:
            log.warning("whatsapp: no agent for this chat (set WHATSAPP_OWNER_AGENT_ID); replying without saving a lead")
        elif conv.get("role") == "agent":
            if not conv.get("agent_notified") and self.cfg.owner_agent_id:
                conv["agent_notified"] = True
                await adapters.notify(self.db, self.cfg.owner_agent_id, "agent_whatsapp",
                                      f"{conv.get('name') or 'An agent'} (agent, not signed up) wrote on WhatsApp: \"{(text or '')[:120]}\"",
                                      {"conversation_id": cid, "screen": "/studio/inbox"}, now)
        else:
            await self._lead(conv, agent_id, wa_id, pid, text or f"[{mtype}]", now)
        if reply and not conv.get("notice_sent_at") and agent_id and conv.get("role") != "agent":   # the buyer notice is not for agents
            reply = f"{reply}\n\n{L.pick(L.NOTICE, lang, agent=await adapters.agent_name(self.db, agent_id) or L.pick(L.TEAM, lang))}"
            conv["notice_sent_at"] = now
        return await self._finish(conv, mid, reply, "answered", now, text, mtype)

    @staticmethod
    def _auto_sender(conv: dict, text: str, now: datetime) -> bool:
        """True when this message (with the kept history) reads like another business's auto-reply bot: the same text AUTO_SAME times
        within AUTO_SPAN, or AUTO_BURST messages within BURST_SPAN. A person saying 'ok' again and again is not one."""
        said = [m for m in conv.get("messages") or [] if m.get("role") == "user" and m.get("ts") and m["ts"] > now - AUTO_SPAN]
        norm = lambda t: re.sub(r"\W+", " ", (t or "").lower()).strip()
        if len(norm(text)) >= AUTO_MIN_CHARS and sum(1 for m in said if norm(m.get("text")) == norm(text)) + 1 >= AUTO_SAME:
            return True
        return sum(1 for m in said if m["ts"] > now - BURST_SPAN) + 1 >= AUTO_BURST

    async def _agent_chat(self, conv: dict, mid: str, agent: dict, text: str, lang: str, now: datetime, mtype: str) -> dict:
        """An agent wrote (an account or a sign-up code on this number): never a buyer lead or the buyer greeting. The owner is told
        every message; the agent gets one short 'our team will reply here' at most every AGENT_ACK_EVERY, so a person answers him."""
        conv["role"], conv["agent_user_id"] = "agent", agent.get("user_id")
        if agent.get("name"):
            conv["name"] = agent["name"]
        if self.cfg.owner_agent_id:
            said = (text or f"[{mtype}]")[:120]
            await adapters.notify(self.db, self.cfg.owner_agent_id, "agent_whatsapp", f"{agent.get('name') or 'An agent'} (agent) wrote on WhatsApp: \"{said}\"",
                                  {"conversation_id": conv["_id"], "screen": "/studio/inbox"}, now)
        reply = None
        last = conv.get("agent_ack_at")
        if not last or now - last >= AGENT_ACK_EVERY:
            reply, conv["agent_ack_at"] = adapters.agent_ack(agent, "+" + conv["wa_id"], lang), now
        return await self._finish(conv, mid, reply, "agent", now, text, mtype)

    async def _lead(self, conv: dict, agent_id: str, wa_id: str, pid: str, text: str, now: datetime) -> None:
        try:
            contact_id, created = await adapters.upsert_lead(
                self.db, agent_id=agent_id, phone="+" + wa_id, wa_id=wa_id, name=conv.get("name") or None, data=conv["data"],
                message=f"WhatsApp: {text}", now=now, phone_number_id=pid, interest=conv.get("context"))
        except Exception as e:  # a lead problem must never stop the reply
            log.warning("whatsapp: lead not stored: %s", self._clean(type(e).__name__))
            return
        conv["lead_id"] = contact_id
        ref = {"lead_id": contact_id, "conversation_id": conv["_id"]}
        who = conv.get("name") or "A buyer"
        if created:
            await adapters.notify(self.db, agent_id, "new_whatsapp_lead", f"{who} messaged on WhatsApp. {adapters.summary(conv['data'])}", ref, now)
        if conv["data"].get("needs_human") and not conv.get("needs_human_notified"):
            conv["needs_human_notified"] = True
            asked = (conv["data"].get("questions") or [""])[-1]
            await adapters.notify(self.db, agent_id, "whatsapp_needs_you", f"{who} asked something on WhatsApp we could not answer: \"{asked[:120]}\"", ref, now)

    # ---- sending ----------------------------------------------------------------------------------------------------
    async def _mark_read(self, pid: str, mid: str) -> None:
        if self.cfg.dry_run or not mid or self.graph is None or not self.cfg.can_send:
            return
        try:
            await self.graph.mark_read(pid, mid)
        except WhatsAppGraphError as e:
            log.info("whatsapp: mark read failed: %s", self._clean(e))

    def in_window(self, conv: dict, now: datetime) -> bool:
        last = conv.get("last_inbound_at")
        return bool(last) and now - last < WINDOW

    async def _send(self, conv: dict, reply: str, now: datetime) -> dict:
        """Returns the outbound record. Never sends outside the 24-hour window, when opted out (except the STOP confirmation, which the caller
        decides), over the hourly cap, or in dry run."""
        rec = {"direction": "out", "wa_id": conv["wa_id"], "phone_number_id": conv["phone_number_id"], "agent_id": conv.get("agent_id"),
               "type": "text", "text": reply, "ts": now, "error": None, "dry_run": self.cfg.dry_run}
        recent = [r for r in conv.get("replies", []) if r > now - timedelta(hours=1)]
        if not self.in_window(conv, now):
            rec.update(status="refused", error="outside the 24-hour customer service window (would need a paid template)")
            log.warning("whatsapp: reply to %s refused: outside the 24-hour window", mask(conv["wa_id"]))
        elif len(recent) >= MAX_REPLIES_PER_HOUR:
            rec.update(status="refused", error="hourly reply cap for this buyer")
            log.warning("whatsapp: reply to %s refused: hourly cap", mask(conv["wa_id"]))
        elif self.cfg.dry_run:
            rec["status"] = "dry_run"
        elif self.graph is None or not self.cfg.can_send:
            rec.update(status="failed", error="WhatsApp is not connected (no access token)")
        else:
            try:
                rec["_id"] = await self.graph.send_text(conv["phone_number_id"], conv["wa_id"], reply) or None
                rec["status"] = "sent"
            except WhatsAppGraphError as e:
                rec.update(status="failed", error=self._clean(e))
                log.warning("whatsapp: send failed: %s", rec["error"])
        if rec["status"] in ("sent", "dry_run"):
            conv["replies"] = recent + [now]
        rec["_id"] = rec.get("_id") or f"out-{uuid.uuid4().hex}"
        await self.messages.insert_one(rec)
        return rec

    async def _finish(self, conv: dict, mid: str, reply: Optional[str], outcome: str, now: datetime, text: str, mtype: str) -> dict:
        conv["messages"] = conv.get("messages", []) + [{"role": "user", "text": text or f"[{mtype}]", "ts": now}]
        status = None
        if reply:
            rec = await self._send(conv, reply, now)
            status = rec["status"]
            conv["messages"].append({"role": "bot", "text": reply, "ts": now, "status": status})
        conv["messages"] = conv["messages"][-MAX_KEPT:]
        conv["updated_at"] = now
        conv["needs_human"] = bool(conv["data"].get("needs_human"))
        if await self.convs.find_one({"_id": conv["_id"]}):
            await self.convs.update_one({"_id": conv["_id"]}, {"$set": {k: v for k, v in conv.items() if k != "_id"}})
        else:
            await self.convs.insert_one(conv)
        if mid:
            await self.messages.update_one({"_id": mid}, {"$set": {"status": outcome, "agent_id": conv.get("agent_id"), "processed_at": now}})
        return {"status": outcome, "reply": reply, "send_status": status, "agent_id": conv.get("agent_id"), "lead_id": conv.get("lead_id")}

    # ---- Studio -------------------------------------------------------------------------------------------------------
    async def conversations(self, agent_id: str, limit: int = 30) -> list:
        docs = await self.convs.find({"agent_id": agent_id}).sort("updated_at", -1).limit(min(max(limit, 1), 100)).to_list(100)
        out = []
        for d in docs:
            msgs = d.get("messages") or []
            out.append({
                "id": d["_id"].split(":")[-1][-4:] + "-" + uuid.uuid5(uuid.NAMESPACE_URL, d["_id"]).hex[:8], "channel": "whatsapp",
                "name": d.get("name") or None, "phone": mask(d.get("wa_id", "")), "lead_id": d.get("lead_id"),
                "summary": adapters.summary(d["data"]), "needs_human": bool(d.get("needs_human")), "opted_out": bool(d.get("opted_out")),
                "updated_at": d.get("updated_at"), "language": d.get("language") or "en",
                "interest_title": (d.get("context") or {}).get("title") or None,
                "window_open": self.in_window(d, self.now()), "role": d.get("role") or "buyer",
                "messages": [{"role": m["role"], "text": m["text"][:600], "ts": m["ts"], "status": m.get("status")} for m in msgs[-6:]],
            })
        return out
