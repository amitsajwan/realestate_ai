"""WhatsApp buyer assistant: one incoming message in, at most one reply out (free, inside the 24-hour window the buyer opened).

Collections
  whatsapp_messages       _id = Meta message id (inbound, the idempotency key) or the sent message id / out-<uuid> (outbound)
  whatsapp_conversations  _id = "<phone_number_id>:<wa_id>": agent, engine state, last 20 messages, last inbound time, opt-out, lead id

Rules
  - Routing: the receiving number's agent (WHATSAPP_NUMBER_AGENTS) > the agent behind an interest code in the text > the owner agent.
  - Answers come from the website chat engine and grounded knowledge (no invented facts or prices, sample homes labelled), in the buyer's language.
  - The buyer started the chat, so we may reply and keep a lead: consent is recorded as that, and they are told once how to stop (STOP).
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
from .config import WhatsAppConfig
from .graph import WhatsAppGraphError

log = logging.getLogger(__name__)

WINDOW = timedelta(hours=24)
MAX_KEPT = 20
MAX_TEXT = 500
MAX_REPLIES_PER_HOUR = 30
STOP_RX = re.compile(r"^\W*(stop|stop all|unsubscribe|opt ?out|cancel|end|quit|band karo|बंद करो|बंद|थांबवा)\W*$", re.I)
START_RX = re.compile(r"^\W*(start|unstop|resume|subscribe)\W*$", re.I)
MEDIA_TYPES = ("image", "audio", "video", "document", "sticker", "voice")


def _ts(value) -> Optional[datetime]:
    try:
        return datetime.utcfromtimestamp(int(value))
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def mask(phone: str) -> str:
    digits = "".join(ch for ch in phone or "" if ch.isdigit())
    return f"+{digits[:2]} {digits[2:4]}******{digits[-2:]}" if len(digits) >= 8 else "******"


class WhatsAppService:
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
    async def _route(self, conv: dict, pid: str, text: str, now: datetime) -> None:
        mapped = self.cfg.number_agents.get(pid)
        if mapped:
            conv["agent_id"], conv["routed_by"] = mapped, "number"
        link = await adapters.find_interest_link(self.db, text) if text else None
        if link:
            conv["context"] = {"kind": link.get("kind"), "ref": link.get("ref"), "sample": bool(link.get("sample")), "code": link.get("code"),
                               "title": (link.get("title") or "")[:140],
                               "listing_id": link.get("ref") if link.get("kind") == "listing" and not link.get("sample") else None}
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
        await self._route(conv, pid, text, now)
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
        agent_id = conv.get("agent_id")
        if mtype == "location":
            reply = L.pick(L.LOCATION, lang)
        elif mtype in MEDIA_TYPES or not text:
            reply = L.pick(L.MEDIA, lang)
        else:
            reply = await self._answer(conv, text, lang)

        if not agent_id:
            log.warning("whatsapp: no agent for this chat (set WHATSAPP_OWNER_AGENT_ID); replying without saving a lead")
        else:
            await self._lead(conv, agent_id, wa_id, pid, text or f"[{mtype}]", now)
        if not conv.get("notice_sent_at") and agent_id:
            reply = f"{reply}\n\n{L.pick(L.NOTICE, lang, agent=await adapters.agent_name(self.db, agent_id) or L.pick(L.TEAM, lang))}"
            conv["notice_sent_at"] = now
        return await self._finish(conv, mid, reply, "answered", now, text, mtype)

    async def _answer(self, conv: dict, text: str, lang: str) -> str:
        data = conv["data"]
        grounding = await adapters.grounding_for(self.db, conv.get("context"), data.get("locality"))
        t = await adapters.chat_turn(data, text, self.llm, grounding)
        reply, english_left = L.localise_fixed(t.reply, lang)
        if english_left and self.llm is not None:
            translated = await adapters.translate(t.reply, lang, self.llm)
            if translated != t.reply:
                reply = translated
        opts = L.options_line(t.quick, lang)
        return f"{reply}\n{opts}" if opts else reply

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
                "window_open": self.in_window(d, self.now()),
                "messages": [{"role": m["role"], "text": m["text"][:600], "ts": m["ts"], "status": m.get("status")} for m in msgs[-6:]],
            })
        return out
