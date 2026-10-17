"""Inbox: every conversation the agent has, in one list and one thread per person (owner, 2026-10-17: 'WhatsApp messages and other
messages are difficult to follow, we need clear pages').

Sources (read only, except the WhatsApp reply)
  whatsapp_conversations + whatsapp_messages   WhatsApp on our number; the full thread comes from whatsapp_messages (both directions)
  dm_conversations                             Facebook Messenger / Instagram DMs (last messages kept on the conversation)
  chat_sessions                                website chat on the agent's pages (by agent_slug)

A thread id is "<kind>-<base64url of the stored _id>" (kind: wa, dm, web), so ids never carry a raw phone number.
"Needs you" = the last message is theirs: nobody (bot or person) has answered it.
A person's reply goes out only on WhatsApp, only inside the 24-hour window, through WhatsAppService._send (same caps, dry run and
records); the bot then stays quiet in that chat for HUMAN_HOLD, so it does not talk over the person.
"""
import base64
import binascii
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from app.modules.whatsapp.service import mask

HUMAN_HOLD = timedelta(hours=12)
MAX_THREADS = 100
MAX_MESSAGES = 200
MAX_REPLY = 1000


class InboxError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _enc(kind: str, raw: str) -> str:
    return f"{kind}-" + base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _dec(tid: str):
    kind, _, b = (tid or "").partition("-")
    if kind not in ("wa", "dm", "web") or not b or len(b) > 200:
        raise InboxError("Conversation not found", 404)
    try:
        return kind, base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)).decode()
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise InboxError("Conversation not found", 404)


def _iso(dt) -> Optional[str]:
    return dt.isoformat() + "Z" if isinstance(dt, datetime) else (str(dt) if dt else None)


def _who(role: str, sent_by: Optional[str] = None) -> str:
    """them = the buyer or agent who wrote to us; bot = our assistant; you = a person on our side."""
    if role in ("user", "in"):
        return "them"
    if sent_by in ("owner", "agent", "person") or role in ("agent", "human", "person"):
        return "you"
    return "bot"


class InboxService:
    def __init__(self, db, whatsapp=None, now: Callable[[], datetime] = datetime.utcnow):
        self.db, self.whatsapp, self.now = db, whatsapp, now

    def c(self, name: str):
        return self.db.get_collection(name)

    async def _slug(self, agent_id: str) -> Optional[str]:
        prof = await self.c("agent_public_profiles").find_one({"agent_id": agent_id})
        return (prof or {}).get("slug")

    # ---- the list ---------------------------------------------------------------------------------------------------
    async def threads(self, agent_id: str) -> List[dict]:
        out = []
        for d in await self.c("whatsapp_conversations").find({"agent_id": agent_id}).sort("updated_at", -1).limit(MAX_THREADS).to_list(MAX_THREADS):
            out.append(self._row("wa", d, "whatsapp", d.get("name"), mask(d.get("wa_id", "")), d.get("role") or "buyer",
                                 window=self._window(d), opted_out=bool(d.get("opted_out"))))
        for d in await self.c("dm_conversations").find({"agent_id": agent_id}).sort("updated_at", -1).limit(MAX_THREADS).to_list(MAX_THREADS):
            out.append(self._row("dm", d, d.get("platform") or "messenger", (d.get("data") or {}).get("name"), "", "buyer",
                                 opted_out=bool(d.get("opted_out"))))
        slug = await self._slug(agent_id)
        if slug:
            for d in await self.c("chat_sessions").find({"agent_slug": slug}).sort("updated_at", -1).limit(MAX_THREADS).to_list(MAX_THREADS):
                if d.get("messages"):
                    out.append(self._row("web", d, "website", (d.get("data") or {}).get("name"), "", "buyer"))
        out.sort(key=lambda r: r["last_at"] or "", reverse=True)
        return out[:MAX_THREADS]

    def _window(self, conv: dict) -> bool:
        last = conv.get("last_inbound_at")
        return bool(last) and self.now() - last < timedelta(hours=24)

    def _row(self, kind: str, d: dict, channel: str, name, phone: str, role: str, window: bool = False, opted_out: bool = False) -> dict:
        msgs = d.get("messages") or []
        last = msgs[-1] if msgs else {}
        who = _who(last.get("role", ""), last.get("sent_by"))
        data = d.get("data") or {}
        return {"id": _enc(kind, str(d["_id"])), "channel": channel, "name": (name or "").strip() or None, "phone": phone, "role": role,
                "last_text": (last.get("text") or "")[:160], "last_from": who if msgs else None,
                "last_at": _iso(last.get("ts") or d.get("updated_at")), "needs_you": bool(msgs) and who == "them" and not opted_out,
                "lead_id": d.get("lead_id"), "lead_saved": bool(d.get("lead_id") or d.get("lead_created")),
                "window_open": window, "opted_out": opted_out, "can_reply": kind == "wa" and window and not opted_out,
                "summary": self._summary(data), "messages": len(msgs)}

    @staticmethod
    def _summary(data: dict) -> str:
        bits = []
        if data.get("bhk"):
            bits.append(f"{int(data['bhk']) if float(data['bhk']).is_integer() else data['bhk']} BHK")
        if data.get("locality"):
            bits.append(str(data["locality"]).replace("_", " ").title())
        if data.get("budget_max"):
            bits.append(f"up to Rs {data['budget_max'] / 1e7:.2f} Cr" if data["budget_max"] >= 1e7 else f"up to Rs {data['budget_max'] / 1e5:.0f} L")
        return ", ".join(bits)

    # ---- one thread -------------------------------------------------------------------------------------------------
    async def _own(self, agent_id: str, tid: str):
        kind, raw = _dec(tid)
        if kind == "wa":
            doc = await self.c("whatsapp_conversations").find_one({"_id": raw})
            ok = doc is not None and doc.get("agent_id") == agent_id
        elif kind == "dm":
            doc = await self.c("dm_conversations").find_one({"_id": raw})
            ok = doc is not None and doc.get("agent_id") == agent_id
        else:
            doc = await self.c("chat_sessions").find_one({"_id": raw})
            ok = doc is not None and doc.get("agent_slug") == await self._slug(agent_id)
        if not ok:
            raise InboxError("Conversation not found", 404)
        return kind, doc

    async def thread(self, agent_id: str, tid: str) -> dict:
        kind, doc = await self._own(agent_id, tid)
        if kind == "wa":
            head = self._row("wa", doc, "whatsapp", doc.get("name"), mask(doc.get("wa_id", "")), doc.get("role") or "buyer",
                             window=self._window(doc), opted_out=bool(doc.get("opted_out")))
            rows = await self.c("whatsapp_messages").find({"wa_id": doc["wa_id"], "phone_number_id": doc["phone_number_id"]}).to_list(MAX_MESSAGES * 2)
            rows.sort(key=lambda m: m.get("ts") or m.get("received_at") or datetime.min)
            msgs = [{"from": _who(m.get("direction", ""), m.get("sent_by")), "text": m.get("text") or f"[{m.get('type') or 'message'}]",
                     "at": _iso(m.get("ts")), "status": m.get("status") if m.get("direction") == "out" else None,
                     "error": m.get("error") if m.get("direction") == "out" and m.get("status") in ("failed", "refused") else None}
                    for m in rows][-MAX_MESSAGES:]
        else:
            channel = (doc.get("platform") or "messenger") if kind == "dm" else "website"
            head = self._row(kind, doc, channel, (doc.get("data") or {}).get("name"), "", "buyer", opted_out=bool(doc.get("opted_out")))
            msgs = [{"from": _who(m.get("role", ""), m.get("sent_by")), "text": m.get("text") or "", "at": _iso(m.get("ts")),
                     "status": m.get("status"), "error": None} for m in (doc.get("messages") or [])][-MAX_MESSAGES:]
        return {**head, "thread": msgs, "bot_paused_until": _iso(doc.get("human_until")) if (doc.get("human_until") or datetime.min) > self.now() else None}

    # ---- a person replies (WhatsApp) --------------------------------------------------------------------------------
    async def reply(self, agent_id: str, tid: str, text: str, by: str) -> dict:
        text = (text or "").strip()
        if not text:
            raise InboxError("Write a message first", 422)
        if len(text) > MAX_REPLY:
            raise InboxError(f"Keep it under {MAX_REPLY} characters", 422)
        kind, conv = await self._own(agent_id, tid)
        if kind != "wa":
            raise InboxError("You can reply here only to WhatsApp chats", 409)
        if conv.get("opted_out"):
            raise InboxError("They replied STOP. Do not message them on WhatsApp.", 409)
        if not self._window(conv):
            raise InboxError("More than 24 hours since their last message. WhatsApp allows a reply only after they write again.", 409)
        if self.whatsapp is None:
            raise InboxError("WhatsApp is not connected", 503)
        now = self.now()
        rec = await self.whatsapp._send(conv, text, now)
        await self.c("whatsapp_messages").update_one({"_id": rec["_id"]}, {"$set": {"sent_by": by}})
        if rec["status"] not in ("sent", "dry_run"):
            raise InboxError(f"Not sent: {rec.get('error') or rec['status']}", 502)
        msgs = (conv.get("messages") or []) + [{"role": "agent", "sent_by": by, "text": text, "ts": now, "status": rec["status"]}]
        await self.c("whatsapp_conversations").update_one({"_id": conv["_id"]}, {"$set": {
            "messages": msgs[-20:], "replies": conv.get("replies", []), "human_until": now + HUMAN_HOLD, "updated_at": now}})
        return await self.thread(agent_id, tid)
