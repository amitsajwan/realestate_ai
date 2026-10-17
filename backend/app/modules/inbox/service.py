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
import re
from datetime import datetime, timedelta
from typing import Callable, List, Optional
from urllib.parse import quote

from app.core import brand
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
        mine = {"$or": [{"agent_id": agent_id}, {"passed_by": agent_id}]}
        for d in await self.c("whatsapp_conversations").find(mine).sort("updated_at", -1).limit(MAX_THREADS).to_list(MAX_THREADS):
            out.append(self._row("wa", d, "whatsapp", d.get("name"), mask(d.get("wa_id", "")), d.get("role") or "buyer",
                                 window=self._window(d), opted_out=bool(d.get("opted_out")), viewer=agent_id))
        for d in await self.c("dm_conversations").find(mine).sort("updated_at", -1).limit(MAX_THREADS).to_list(MAX_THREADS):
            out.append(self._row("dm", d, d.get("platform") or "messenger", (d.get("data") or {}).get("name"), "", "buyer",
                                 opted_out=bool(d.get("opted_out")), viewer=agent_id))
        slug = await self._slug(agent_id)
        web = {"$or": [{"agent_slug": slug}, {"passed_to": agent_id}]} if slug else {"passed_to": agent_id}
        for d in await self.c("chat_sessions").find(web).sort("updated_at", -1).limit(MAX_THREADS).to_list(MAX_THREADS):
            if d.get("messages"):
                out.append(self._row("web", d, "website", (d.get("data") or {}).get("name"), "", "buyer", viewer=agent_id))
        out.sort(key=lambda r: r["last_at"] or "", reverse=True)
        return out[:MAX_THREADS]

    def _window(self, conv: dict) -> bool:
        last = conv.get("last_inbound_at")
        return bool(last) and self.now() - last < timedelta(hours=24)

    def _row(self, kind: str, d: dict, channel: str, name, phone: str, role: str, window: bool = False, opted_out: bool = False,
             viewer: Optional[str] = None) -> dict:
        """passed: "out" = this viewer passed it to an agent (no longer his to answer), "in" = passed to this viewer."""
        msgs = d.get("messages") or []
        passed = "out" if d.get("passed_by") and d.get("passed_by") == viewer else "in" if d.get("passed_to") and d.get("passed_to") == viewer else None
        last = msgs[-1] if msgs else {}
        who = _who(last.get("role", ""), last.get("sent_by"))
        data = d.get("data") or {}
        return {"id": _enc(kind, str(d["_id"])), "channel": channel, "name": (name or "").strip() or None, "phone": phone, "role": role,
                "last_text": (last.get("text") or "")[:160], "last_from": who if msgs else None,
                "last_at": _iso(last.get("ts") or d.get("updated_at")), "needs_you": bool(msgs) and who == "them" and not opted_out and passed != "out",
                "passed": passed, "passed_at": _iso(d.get("passed_at")) if passed else None,
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
            ok = doc is not None and agent_id in (doc.get("agent_id"), doc.get("passed_by"))
        elif kind == "dm":
            doc = await self.c("dm_conversations").find_one({"_id": raw})
            ok = doc is not None and agent_id in (doc.get("agent_id"), doc.get("passed_by"))
        else:
            doc = await self.c("chat_sessions").find_one({"_id": raw})
            ok = doc is not None and (agent_id in (doc.get("passed_to"), doc.get("passed_by")) or doc.get("agent_slug") == await self._slug(agent_id))
        if not ok:
            raise InboxError("Conversation not found", 404)
        return kind, doc

    async def thread(self, agent_id: str, tid: str) -> dict:
        kind, doc = await self._own(agent_id, tid)
        if kind == "wa":
            head = self._row("wa", doc, "whatsapp", doc.get("name"), mask(doc.get("wa_id", "")), doc.get("role") or "buyer",
                             window=self._window(doc), opted_out=bool(doc.get("opted_out")), viewer=agent_id)
            rows = await self.c("whatsapp_messages").find({"wa_id": doc["wa_id"], "phone_number_id": doc["phone_number_id"]}).to_list(MAX_MESSAGES * 2)
            rows.sort(key=lambda m: m.get("ts") or m.get("received_at") or datetime.min)
            msgs = [{"from": _who(m.get("direction", ""), m.get("sent_by")), "text": m.get("text") or f"[{m.get('type') or 'message'}]",
                     "at": _iso(m.get("ts")), "status": m.get("status") if m.get("direction") == "out" else None,
                     "error": m.get("error") if m.get("direction") == "out" and m.get("status") in ("failed", "refused") else None}
                    for m in rows][-MAX_MESSAGES:]
        else:
            channel = (doc.get("platform") or "messenger") if kind == "dm" else "website"
            head = self._row(kind, doc, channel, (doc.get("data") or {}).get("name"), "", "buyer", opted_out=bool(doc.get("opted_out")), viewer=agent_id)
            msgs = [{"from": _who(m.get("role", ""), m.get("sent_by")), "text": m.get("text") or "", "at": _iso(m.get("ts")),
                     "status": m.get("status"), "error": None} for m in (doc.get("messages") or [])][-MAX_MESSAGES:]
        other = doc.get("passed_to") if head["passed"] == "out" else None
        prof = await self.c("agent_public_profiles").find_one({"agent_id": other}) if other else None
        head["passed_to_name"] = self._agent_name(prof) if prof else None
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

    # ---- the owner passes a buyer to an agent -----------------------------------------------------------------------
    # The conversation and its lead move to the agent (his Inbox and Leads; WhatsApp routing keeps them with him, since
    # routed_by is no longer "owner"); the owner still sees it, marked "Passed to". The agent gets a Studio alert, and the owner
    # gets a wa.me link with the buyer's details to send from his own WhatsApp (no template or billing needed).
    async def agents(self, owner_id: str) -> List[dict]:
        rows = await self.c("agent_public_profiles").find({"agent_id": {"$nin": [owner_id, None, ""]}}).to_list(500)
        out = [{"agent_id": str(p["agent_id"]), "name": self._agent_name(p), "has_whatsapp": bool(_wa_digits(p.get("phone")))} for p in rows]
        return sorted(out, key=lambda a: a["name"].lower())

    @staticmethod
    def _agent_name(profile: dict) -> str:
        return ((profile.get("branding_data") or {}).get("business_name") or profile.get("agent_name") or profile.get("slug") or "Agent").strip()

    async def pass_to(self, owner_id: str, tid: str, to_agent: str) -> dict:
        kind, doc = await self._own(owner_id, tid)
        if (doc.get("role") or "buyer") == "agent":
            raise InboxError("This chat is from an agent, not a buyer", 409)
        if not to_agent or to_agent == owner_id:
            raise InboxError("Pick an agent", 422)
        prof = await self.c("agent_public_profiles").find_one({"agent_id": to_agent})
        if not prof:
            raise InboxError("Agent not found", 404)
        now = self.now()
        data = doc.get("data") or {}
        phone = ("+" + doc["wa_id"]) if kind == "wa" else (data.get("phone") or "")
        lead_id = await self._move_lead(doc.get("lead_id"), owner_id, to_agent, phone, now)
        mark = {"passed_by": owner_id, "passed_to": to_agent, "passed_at": now}
        if kind == "web":
            await self.c("chat_sessions").update_one({"_id": doc["_id"]}, {"$set": {**mark, **({"lead_id": lead_id} if lead_id else {})}})
        else:
            col = "whatsapp_conversations" if kind == "wa" else "dm_conversations"
            await self.c(col).update_one({"_id": doc["_id"]}, {"$set": {**mark, "agent_id": to_agent, "routed_by": "owner_pass",
                                                                     **({"lead_id": lead_id} if lead_id else {})}})
        who = (doc.get("name") if kind == "wa" else data.get("name")) or "A buyer"
        wants = self._summary(data)
        from app.modules.notifications.service import notify
        await notify(self.db, to_agent, "buyer_passed", f"{who} was passed to you{': ' + wants if wants else ''}. Call or message them soon.",
                     {"screen": f"/studio/inbox/{tid}", **({"lead_id": lead_id} if lead_id else {})}, now)
        digits = _wa_digits(prof.get("phone"))
        text = self._handover_text(doc, kind, who, phone, wants)
        return {"passed_to": self._agent_name(prof), "lead_id": lead_id,
                "whatsapp_url": f"https://wa.me/{digits}?text={quote(text)}" if digits else None}

    async def _move_lead(self, lead_id: Optional[str], owner_id: str, to_agent: str, phone: str, now: datetime) -> Optional[str]:
        """The owner's lead becomes the agent's; if the agent already has this phone as a lead, that one is kept."""
        contacts = self.c("contacts")
        lead = await contacts.find_one({"_id": lead_id, "agent_id": owner_id}) if lead_id else None
        if not lead and phone:
            lead = await contacts.find_one({"agent_id": owner_id, "phone": phone})
        if not lead:
            return None
        if lead.get("phone"):
            theirs = await contacts.find_one({"agent_id": to_agent, "phone": lead["phone"]})
            if theirs:
                return theirs["_id"]
        await contacts.update_one({"_id": lead["_id"]}, {"$set": {"agent_id": to_agent, "passed_by": owner_id, "passed_at": now}})
        return lead["_id"]

    def _handover_text(self, doc: dict, kind: str, who: str, phone: str, wants: str) -> str:
        channel = {"wa": "WhatsApp", "web": "our website chat"}.get(kind, (doc.get("platform") or "Messenger").title())
        said = next((m.get("text") for m in reversed(doc.get("messages") or []) if m.get("role") in ("user", "in") and m.get("text")), "")
        lines = [f"New buyer for you from {brand.NAME}", f"Name: {who}"]
        lines.append(f"Phone: {phone}" if phone else f"No number yet: they wrote on {channel}. See the chat in Studio > Inbox.")
        if wants:
            lines.append(f"Wants: {wants}")
        if said:
            lines.append(f'They said: "{said[:200]}"')
        lines.append("Please call or WhatsApp them today.")
        return "\n".join(lines)


def _wa_digits(phone) -> Optional[str]:
    """'+91 98765 43210' -> '919876543210'; None unless it is an Indian mobile."""
    d = re.sub(r"\D", "", str(phone or ""))
    if len(d) == 10 and d[0] in "6789":
        d = "91" + d
    return d if len(d) == 12 and d.startswith("91") and d[2] in "6789" else None
