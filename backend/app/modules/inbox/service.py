"""Inbox: every conversation the agent has, in one list and one thread per person (owner, 2026-10-17: 'WhatsApp messages and other
messages are difficult to follow, we need clear pages').

Sources (read only, except the WhatsApp reply)
  whatsapp_conversations + whatsapp_messages   WhatsApp on our number; the full thread comes from whatsapp_messages (both directions)
  dm_conversations                             Facebook Messenger / Instagram DMs (last messages kept on the conversation)
  chat_sessions                                website chat on the agent's pages (by agent_slug)
  engage_comments                              comments on our Facebook/Instagram posts, one thread per commenter (2026-10-17: they moved here
                                               from the Interest screen); 'ignored' ones (emoji, tags) and our own are left out

A thread id is "<kind>-<base64url of the stored _id>" (kind: wa, dm, web; cm: "<channel>|<commenter id>"), so ids never carry a raw phone number.
"Needs you" = the last message is theirs: nobody (bot or person) has answered it.
A person's reply goes out only on WhatsApp, only inside the 24-hour window, through WhatsAppService._send (same caps, dry run and
records); the bot then stays quiet in that chat for HUMAN_HOLD, so it does not talk over the person. Outside the window a person can
start (or restart) a chat from a lead with the approved follow-up template, once per 24 hours (start). The template alone does not
hold the bot back: their answer to it gets the bot's reply at once (2026-10-23: Rahul's "Hi" sat unanswered for hours because the
template started the 12-hour hold and nobody was watching). Messaging a New lead moves it to Contacted.
"""
import base64
import binascii
import re
from datetime import datetime, timedelta
from typing import Callable, List, Optional
from urllib.parse import quote

from app.core import brand
from app.modules.areastats import pages as project_pages
from app.modules.whatsapp.service import mask

from . import handover

_ask_post = None   # app.wiring: the boost, keep or remove question (propertyfacts.run_news), a domain above this one


def configure(ask_post) -> None:
    global _ask_post
    _ask_post = ask_post


HUMAN_HOLD = timedelta(hours=12)
MAX_THREADS = 100
MAX_MESSAGES = 200
MAX_REPLY = 1000
MAX_COMMENTS = 300
COMMENT_CHANNEL = {"facebook": "facebook_comment", "instagram": "instagram_comment"}
COMMENT_TROUBLE = ("capped", "failed")   # the bot could not answer: a person should
TEMPLATE_GAP = timedelta(hours=24)
FOLLOWUP_OLD = "enquiry_followup_v1"       # approved UTILITY template on our WABA; each body below must match Meta's copy
FOLLOWUP_OLD_BODY = ("Namaste {} ji, this is Avasetu. You asked about a {} in Pune ({}). Thank you!\n\n"
                     "To shortlist the right homes, could you tell us:\n"
                     "1. Which part of Pune you'd like to live in, or where you or your family work?\n"
                     "2. Ready to move, or under construction is fine?\n"
                     "3. Is it for your family to live in, or an investment?\n\n"
                     "Hindi mein baat karna ho to bataiye.")
# owner, 2026-11-06: "why we say can we talk in Hindi, why not Marathi also". A template's words are fixed by Meta, so the new wording is a new
# template: v2 goes first, and until Meta approves it the send fails and v1 goes instead, so no lead waits.
FOLLOWUP_TEMPLATE = "enquiry_followup_v2"
FOLLOWUP_BODY = FOLLOWUP_OLD_BODY.replace("Hindi mein baat", "Hindi ya Marathi mein baat")
# An enquiry on a project page already says where and what (2026-10-30: Subhash Girase asked for a site visit at 96 Arrcade,
# Kharadi, and the template above asked him which part of Pune he wanted). It gets this one; until Meta approves it the send fails
# and FOLLOWUP_TEMPLATE goes instead, so no lead waits.
PROJECT_OLD = "project_enquiry_v1"   # UTILITY, submitted 2026-10-30; each body below must match Meta's copy
PROJECT_OLD_BODY = ("Namaste {} ji, this is Avasetu. Thank you for asking about {} on our website.\n\n"
                    "You asked for {}. Our team will call you shortly about it.\n\n"
                    "If you have a question before that, reply here. Hindi mein baat karna ho to bataiye.\n\n"
                    "Avasetu team")
PROJECT_TEMPLATE = "project_enquiry_v2"
PROJECT_BODY = PROJECT_OLD_BODY.replace("Hindi mein baat", "Hindi ya Marathi mein baat")
PROJECT_WANT = {"A site visit": "a site visit", "Floor plans": "the floor plans"}


class InboxError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _enc(kind: str, raw: str) -> str:
    return f"{kind}-" + base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _dec(tid: str):
    kind, _, b = (tid or "").partition("-")
    if kind not in ("wa", "dm", "web", "cm") or not b or len(b) > 200:
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
        out += self._comment_rows(await self._comments(agent_id))
        out.sort(key=lambda r: r["last_at"] or "", reverse=True)
        return out[:MAX_THREADS]

    # ---- comments on our posts ------------------------------------------------------------------------------------
    async def _comments(self, agent_id: str, key: Optional[str] = None) -> List[dict]:
        flt = {"agent_id": agent_id, "status": {"$ne": "ignored"}}
        if key:
            channel, _, sender = key.partition("|")
            flt.update({"channel": channel, "from_id": sender} if channel != "facebook" else
                       {"$or": [{"channel": "facebook"}, {"channel": None}], "from_id": sender})
        docs = await self.c("engage_comments").find(flt).sort("processed_at", -1).limit(MAX_COMMENTS).to_list(MAX_COMMENTS)
        return [d for d in docs if not str(d.get("reason") or "").startswith("own comment") and d.get("from_id")]

    @staticmethod
    def _comment_key(d: dict) -> str:
        return f"{d.get('channel') or 'facebook'}|{d['from_id']}"

    @staticmethod
    def _comment_needs(d: dict) -> bool:
        return not d.get("done_at") and (bool(d.get("needs_human")) or d.get("status") in COMMENT_TROUBLE)

    def _comment_rows(self, docs: List[dict]) -> List[dict]:
        groups: dict = {}
        for d in docs:  # newest first, so the first of each group is the latest comment
            groups.setdefault(self._comment_key(d), []).append(d)
        return [self._comment_head(key, ds) for key, ds in groups.items()]

    def _comment_head(self, key: str, docs: List[dict]) -> dict:
        last = docs[0]
        channel = key.partition("|")[0]
        replied = last.get("status") == "replied" and last.get("reply")
        return {"id": _enc("cm", key), "channel": COMMENT_CHANNEL.get(channel, "facebook_comment"), "name": (last.get("from_name") or "").strip() or None,
                "phone": "", "role": "buyer", "last_text": ((last.get("reply") if replied else last.get("text")) or "")[:160],
                "last_from": "bot" if replied else "them", "last_at": _iso(last.get("replied_at") if replied else last.get("processed_at")),
                "needs_you": any(self._comment_needs(d) for d in docs), "passed": None, "passed_at": None,
                "lead_id": None, "lead_saved": any(d.get("phone") for d in docs), "window_open": False, "opted_out": False, "can_reply": False,
                "summary": "", "messages": len(docs), "post_url": last.get("permalink"),
                "reason": next((self._comment_why(d) for d in docs if self._comment_needs(d)), None)}

    @staticmethod
    def _comment_why(d: dict) -> str:
        if d.get("status") == "capped":
            return "The bot already answered this person enough times today"
        if d.get("status") == "failed":
            return "The bot's reply did not go out"
        return d.get("reason") or "Please answer this one"

    def _comment_thread(self, docs: List[dict]) -> List[dict]:
        msgs = []
        for d in reversed(docs):  # oldest first
            msgs.append({"from": "them", "text": d.get("text") or "", "at": _iso(d.get("processed_at")), "status": None, "error": None})
            if d.get("reply") and d.get("status") in ("replied", "dry_run"):
                msgs.append({"from": "bot", "text": d["reply"], "at": _iso(d.get("replied_at") or d.get("processed_at")),
                             "status": "dry_run" if d["status"] == "dry_run" else None, "error": None})
        return msgs[-MAX_MESSAGES:]

    async def done(self, agent_id: str, tid: str) -> dict:
        """'Done' on a comment thread: the person answered it on Facebook/Instagram (or it needs no answer); it stops needing you."""
        kind, raw = _dec(tid)
        if kind != "cm":
            raise InboxError("Only comments can be marked done; answer chats by replying", 409)
        docs = await self._comments(agent_id, raw)
        if not docs:
            raise InboxError("Conversation not found", 404)
        now = self.now()
        for d in docs:
            if self._comment_needs(d):
                await self.c("engage_comments").update_one({"_id": d["_id"]}, {"$set": {"done_at": now, "done_by": agent_id}})
        return await self.thread(agent_id, tid)

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
                "summary": self._summary(data), "messages": len(msgs), "follow_up_sent_at": _iso(d.get("template_sent_at"))}

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
        if kind == "cm":
            raise InboxError("Comments are answered on Facebook or Instagram", 409)
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
        if tid.startswith("cm-"):
            docs = await self._comments(agent_id, _dec(tid)[1])
            if not docs:
                raise InboxError("Conversation not found", 404)
            return {**self._comment_head(self._comment_key(docs[0]), docs), "thread": self._comment_thread(docs), "bot_paused_until": None,
                    "passed_to_name": None}
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

    async def ask_about_post(self, agent_id: str, tid: str) -> dict:
        """The owner asks an agent, any time: boost, keep or remove their latest post, with its numbers. A template, so it goes
        outside the 24-hour window too."""
        kind, conv = await self._own(agent_id, tid)
        if kind != "wa" or conv.get("role") != "agent":
            raise InboxError("This is for a WhatsApp chat with an agent", 409)
        if conv.get("opted_out"):
            raise InboxError("They replied STOP. Do not message them on WhatsApp.", 409)
        if not _ask_post or not await _ask_post(self.db, conv["wa_id"]):
            raise InboxError("This agent has no post to ask about yet", 409)
        return await self.thread(agent_id, tid)

    # ---- a person starts a WhatsApp chat with a lead --------------------------------------------------------------
    # Our number is on the Cloud API, so nobody can open it in the WhatsApp app (owner, 2026-10-21: "we need a way to send a
    # WhatsApp message"). Inside the 24-hour window the person just writes in the thread; outside it the only thing WhatsApp allows is
    # an approved template, sent at most once per TEMPLATE_GAP so a quiet buyer is not chased.
    async def start(self, agent_id: str, lead_id: str, by: str) -> dict:
        lead = await self.c("contacts").find_one({"_id": lead_id, "agent_id": agent_id})
        if not lead:
            raise InboxError("Lead not found", 404)
        digits = _wa_digits(lead.get("phone"))
        if not digits:
            raise InboxError("This lead has no Indian mobile number to message", 422)
        if self.whatsapp is None or not self.whatsapp.cfg.phone_number_id:
            raise InboxError("WhatsApp is not connected", 503)
        now = self.now()
        pid = str(self.whatsapp.cfg.phone_number_id)
        cid = f"{pid}:{digits}"
        tid = _enc("wa", cid)
        conv = await self.c("whatsapp_conversations").find_one({"_id": cid})
        if conv and conv.get("opted_out"):
            raise InboxError("They replied STOP. Do not message them on WhatsApp.", 409)
        if conv and self._window(conv):
            return {"id": tid, "sent": False}
        if conv and conv.get("template_sent_at") and now - conv["template_sent_at"] < TEMPLATE_GAP:
            raise InboxError("The follow-up message already went out in the last 24 hours. Wait for their reply, or call them.", 409)
        if not conv:
            name = (lead.get("name") or "").strip()[:60]
            from app.modules.whatsapp import adapters
            conv = {"_id": cid, "wa_id": digits, "phone_number_id": pid, "agent_id": agent_id, "routed_by": "lead_start", "name": name,
                    "data": adapters.new_chat_state("+" + digits, name or None), "messages": [], "created_at": now, "opted_out": False,
                    "notice_sent_at": None, "lead_id": lead_id, "context": None, "language": None, "needs_human_notified": False, "replies": []}
            await self.c("whatsapp_conversations").insert_one(conv)
        project = await self.project_of(lead)
        rec = None
        tries = [(PROJECT_TEMPLATE, PROJECT_BODY, project_params(lead, project)), (PROJECT_OLD, PROJECT_OLD_BODY, project_params(lead, project))] if project else []
        tries += [(FOLLOWUP_TEMPLATE, FOLLOWUP_BODY, followup_params(lead, project)), (FOLLOWUP_OLD, FOLLOWUP_OLD_BODY, followup_params(lead, project))]
        for name, body, params in tries:
            text = body.format(*params)
            rec = await self.whatsapp.send_template(conv, name, "en", params, text, now)
            if rec["status"] != "failed":
                break
        await self.c("whatsapp_messages").update_one({"_id": rec["_id"]}, {"$set": {"sent_by": by}})
        if rec["status"] not in ("sent", "dry_run"):
            raise InboxError(f"Not sent: {rec.get('error') or rec['status']}", 502)
        msgs = (conv.get("messages") or []) + [{"role": "agent", "sent_by": by, "text": text, "ts": now, "status": rec["status"]}]
        await self.c("whatsapp_conversations").update_one({"_id": cid}, {"$set": {
            "messages": msgs[-20:], "lead_id": conv.get("lead_id") or lead_id, "template_sent_at": now, "updated_at": now}})
        if lead.get("stage", "new") == "new":
            await self.c("contacts").update_one({"_id": lead_id, "agent_id": agent_id, "stage": "new"}, {"$set": {
                "stage": "contacted", "contacted_at": now, "follow_up_due_at": now + timedelta(days=2), "last_activity_at": now}})
        return {"id": tid, "sent": True}

    # ---- a lead's conversations (the lead page shows them) -----------------------------------------------------------
    async def for_lead(self, agent_id: str, lead_id: str) -> List[dict]:
        """Every chat with this lead, newest first: WhatsApp (by lead or by their mobile on our number), Messenger/Instagram (by
        lead), website chat (by the number they gave). Same thread shape as the inbox."""
        lead = (await self.c("contacts").find_one({"_id": lead_id, "agent_id": agent_id})
                or await self.c("contacts").find_one({"_id": lead_id, "passed_by": agent_id}))   # the owner's look at a buyer he passed
        if not lead:
            raise InboxError("Lead not found", 404)
        out = []
        for tid in await self._lead_tids(agent_id, lead):
            try:
                out.append(await self.thread(agent_id, tid))
            except InboxError:
                continue   # passed to another agent, or no longer this viewer's
        out.sort(key=lambda r: r["last_at"] or "", reverse=True)
        return out

    async def _lead_tids(self, agent_id: str, lead: dict) -> List[str]:
        lead_id = lead["_id"]
        tids = []
        for d in await self.c("whatsapp_conversations").find({"lead_id": lead_id}).to_list(20):
            tids.append(_enc("wa", str(d["_id"])))
        digits = _wa_digits(lead.get("phone"))
        if digits:
            for d in await self.c("whatsapp_conversations").find({"wa_id": digits}).to_list(20):
                tids.append(_enc("wa", str(d["_id"])))
        for d in await self.c("dm_conversations").find({"lead_id": lead_id}).to_list(20):
            tids.append(_enc("dm", str(d["_id"])))
        slug = await self._slug(agent_id)
        if slug and lead.get("phone"):
            for d in await self.c("chat_sessions").find({"agent_slug": slug, "data.phone": lead["phone"]}).to_list(20):
                tids.append(_enc("web", str(d["_id"])))
        return list(dict.fromkeys(tids))

    # ---- the owner passes a buyer to an agent -----------------------------------------------------------------------
    # The lead and every chat with them move to the agent (his Inbox and Leads; WhatsApp routing keeps them with him, since
    # routed_by is no longer "owner"); the owner still sees the chats, marked "Passed to". The agent gets the handover card
    # (handover.py: every fact on the lead) as a Studio alert and, from our number, as the approved agent template; the owner also
    # gets a wa.me link with the same card to send from his own WhatsApp when the template could not go.
    # A pass can also be automatic: the owner's rules (lead_routes) send leads about a project or an area to one agent
    # (followups.auto_passes).
    async def agents(self, owner_id: str) -> List[dict]:
        rows = await self.c("agent_public_profiles").find({"agent_id": {"$nin": [owner_id, None, ""]}}).to_list(500)
        phones = [p["phone"] for p in rows if p.get("phone")]
        off = {u.get("phone") for u in await self.c("users").find({"phone": {"$in": phones}, "is_active": False}).to_list(1000)}
        out = [{"agent_id": str(p["agent_id"]), "name": self._agent_name(p), "has_whatsapp": bool(_lead_digits(p)),
                "slug": p.get("slug")} for p in rows if _live(p) and p.get("phone") not in off]
        return sorted(out, key=lambda a: a["name"].lower())

    async def _live_agent(self, agent_id: str) -> dict:
        """The agent's profile; a retired or switched-off account cannot take a buyer (2026-10-26: Saket went to the retired copy of
        House Deal, whose Studio nobody opens, because both accounts read "House Deal" in the picker)."""
        prof = await self.c("agent_public_profiles").find_one({"agent_id": agent_id}) if agent_id else None
        if not prof:
            raise InboxError("Agent not found", 404)
        user = await self.c("users").find_one({"phone": prof["phone"]}) if prof.get("phone") else None
        if not _live(prof) or (user is not None and user.get("is_active") is False):
            raise InboxError(f"{self._agent_name(prof)} ({prof.get('slug')}) is a retired account. Pick their live one.", 409)
        return prof

    @staticmethod
    def _agent_name(profile: dict) -> str:
        return ((profile.get("branding_data") or {}).get("business_name") or profile.get("agent_name") or profile.get("slug") or "Agent").strip()

    async def project_of(self, lead: dict) -> Optional[dict]:
        """The project page they enquired on (name, area, MahaRERA number), from the page the form was on; one record is read."""
        ft = lead.get("first_touch") or {}
        path = (ft.get("enquiry_page") or ft.get("landing") or "").split("?")[0]
        m = re.match(r"^/projects/([a-z0-9-]{1,120})$", path)
        return await project_pages.chat_brief(self.db, m.group(1)) if m else None

    async def handover_for(self, owner_id: str, lead_id: str) -> dict:
        """The card as the agent will get it, and the agent a rule would pick, for the owner to check before passing."""
        lead = await self.c("contacts").find_one({"_id": lead_id, "agent_id": owner_id})
        if not lead:
            raise InboxError("Lead not found", 404)
        project = await self.project_of(lead)
        tids = await self._lead_tids(owner_id, lead)
        return {"card": await self._card(owner_id, lead, project, tids), "project": project,
                "rule": await self.route_for(owner_id, lead, project), "areas": self._areas(lead, project)}

    async def _card(self, agent_id: str, lead: dict, project: Optional[dict], tids: List[str]) -> dict:
        chats = []
        for tid in tids:
            try:
                _, doc = await self._own(agent_id, tid)
                chats.append({**await self.thread(agent_id, tid), "data": doc.get("data")})
            except InboxError:
                continue
        events = await self.c("events").find({"$or": [{"contact_id": lead["_id"]}, {"anon_id": {"$in": lead.get("anon_ids") or []}}]}
                                             ).sort("ts", 1).to_list(200)
        return handover.card(lead, project, chats, [e.get("path") for e in events if e.get("path")])

    async def pass_lead(self, owner_id: str, lead_id: str, to_agent: str, by: str = "owner", rule: Optional[dict] = None,
                        always: Optional[str] = None) -> dict:
        """Pass a lead and every chat with them. `always` ('area' or 'project') also adds the rule that sends the next lead about
        this one's area or project page to the same agent by itself."""
        lead = await self.c("contacts").find_one({"_id": lead_id, "agent_id": owner_id})
        if not lead:
            raise InboxError("Lead not found", 404)
        if not to_agent or to_agent == owner_id:
            raise InboxError("Pick an agent", 422)
        prof = await self._live_agent(to_agent)
        now = self.now()
        project = await self.project_of(lead)
        tids = await self._lead_tids(owner_id, lead)
        card = await self._card(owner_id, lead, project, tids)   # read before anything moves: the chats are still the owner's
        mark = {"passed_by": owner_id, "passed_to": to_agent, "passed_at": now}
        for tid in tids:
            try:
                kind, doc = await self._own(owner_id, tid)
            except InboxError:
                continue
            await self._move_chat(kind, doc, mark, lead_id)
        kept = await self._move_lead(lead_id, owner_id, to_agent, lead.get("phone") or "", now)
        sent = await self._tell_agent(prof, card, now)
        await self.c("contacts").update_one({"_id": kept}, {"$set": {"handover": {
            "to": to_agent, "by": by, "rule": rule, "at": now, "text": card["text"], **sent}}})
        who = (lead.get("name") or "A buyer").strip()
        about = next((x["value"] for x in card["lines"] if x["label"] == "Project"), "")
        from app.modules.notifications.service import notify
        await notify(self.db, to_agent, "buyer_passed", f"{who} was passed to you{': ' + about if about else ''}. Call them today.",
                     {"screen": f"/studio/leads/{kept}", "lead_id": kept}, now)
        added = None
        if always == "project" and project:
            added = {"kind": "project", "key": project["slug"], "label": project["name"]}
        elif always == "area" and self._areas(lead, project):
            area = self._areas(lead, project)[0]
            added = {"kind": "area", "key": area, "label": area}
        if added:
            await self.add_route(owner_id, to_agent, added["kind"], added["label"], key=added["key"])
        digits = _lead_digits(prof)
        return {"passed_to": self._agent_name(prof), "lead_id": kept, "card": card, **sent, "rule_added": added,
                "whatsapp_url": f"https://wa.me/{digits}?text={quote(card['text'])}" if digits else None}

    async def tell_agent_of_lead(self, lead: dict) -> dict:
        """A buyer who enquired on an agent's own site: the agent gets the card as the site-enquiry template from our number, which
        names their business; while Meta has not approved that one, the pass template goes instead so no enquiry waits.
        -> {whatsapp_status, whatsapp_error, text, agent_name}. Raises InboxError for a retired account."""
        agent_id = lead["agent_id"]
        prof = await self._live_agent(agent_id)
        project = await self.project_of(lead)
        card = await self._card(agent_id, lead, project, await self._lead_tids(agent_id, lead))
        name = self._agent_name(prof)
        sent = await self._tell_agent(prof, card, self.now(), handover.SITE_TEMPLATE, handover.site_params(card, name), handover.SITE_BODY)
        if sent["whatsapp_status"] == "failed":
            sent = await self._tell_agent(prof, card, self.now())
        return {**sent, "text": card["text"], "agent_name": name}

    async def _tell_agent(self, prof: dict, card: dict, now: datetime, template: str = handover.AGENT_TEMPLATE,
                          params: Optional[List[str]] = None, body: str = handover.AGENT_BODY) -> dict:
        """An approved agent template from our number (the pass card unless another is given). -> {whatsapp_status,
        whatsapp_error}; a failure never stops the pass."""
        digits = _lead_digits(prof)
        if not digits:
            return {"whatsapp_status": "no_mobile", "whatsapp_error": "The agent's site has no Indian mobile"}
        if self.whatsapp is None or not self.whatsapp.cfg.phone_number_id:
            return {"whatsapp_status": "failed", "whatsapp_error": "WhatsApp is not connected"}
        params = params or handover.template_params(card)
        conv = {"wa_id": digits, "phone_number_id": str(self.whatsapp.cfg.phone_number_id), "agent_id": str(prof["agent_id"])}
        try:
            rec = await self.whatsapp.send_template(conv, template, "en", params, body.format(*params), now)
        except Exception as e:   # the pass is done either way; the owner still has the wa.me link
            return {"whatsapp_status": "failed", "whatsapp_error": str(e)[:200]}
        return {"whatsapp_status": rec["status"], "whatsapp_error": rec.get("error")}

    async def _move_chat(self, kind: str, doc: dict, mark: dict, lead_id: Optional[str]) -> None:
        if kind == "web":
            await self.c("chat_sessions").update_one({"_id": doc["_id"]}, {"$set": {**mark, **({"lead_id": lead_id} if lead_id else {})}})
        else:
            col = "whatsapp_conversations" if kind == "wa" else "dm_conversations"
            await self.c(col).update_one({"_id": doc["_id"]}, {"$set": {**mark, "agent_id": mark["passed_to"], "routed_by": "owner_pass",
                                                                     **({"lead_id": lead_id} if lead_id else {})}})

    async def pass_to(self, owner_id: str, tid: str, to_agent: str, always: Optional[str] = None) -> dict:
        """Pass from a chat. A chat with a lead passes the whole lead (pass_lead); a chat with no lead yet moves on its own, with
        what the chat knows."""
        kind, doc = await self._own(owner_id, tid)
        if (doc.get("role") or "buyer") == "agent":
            raise InboxError("This chat is from an agent, not a buyer", 409)
        if not to_agent or to_agent == owner_id:
            raise InboxError("Pick an agent", 422)
        data = doc.get("data") or {}
        phone = ("+" + doc["wa_id"]) if kind == "wa" else (data.get("phone") or "")
        contacts = self.c("contacts")
        lead = await contacts.find_one({"_id": doc.get("lead_id"), "agent_id": owner_id}) if doc.get("lead_id") else None
        lead = lead or (await contacts.find_one({"agent_id": owner_id, "phone": phone}) if phone else None)
        if lead:
            return await self.pass_lead(owner_id, lead["_id"], to_agent, always=always)
        prof = await self._live_agent(to_agent)
        now = self.now()
        await self._move_chat(kind, doc, {"passed_by": owner_id, "passed_to": to_agent, "passed_at": now}, None)
        who = (doc.get("name") if kind == "wa" else data.get("name")) or "A buyer"
        wants = self._summary(data)
        from app.modules.notifications.service import notify
        await notify(self.db, to_agent, "buyer_passed", f"{who} was passed to you{': ' + wants if wants else ''}. Call or message them soon.",
                     {"screen": f"/studio/inbox/{tid}"}, now)
        digits = _lead_digits(prof)
        text = self._handover_text(doc, kind, who, phone, wants)
        return {"passed_to": self._agent_name(prof), "lead_id": None, "card": {"text": text, "lines": [], "missing": []},
                "whatsapp_status": None, "whatsapp_error": None, "rule_added": None,
                "whatsapp_url": f"https://wa.me/{digits}?text={quote(text)}" if digits else None}

    async def passed(self, owner_id: str, days: int = 14) -> List[dict]:
        """The owner's recent passes, newest first: who, to whom, how (by hand or by a rule), the card and whether the WhatsApp to
        the agent went out, with a wa.me link to send it again from the owner's phone. A passed lead leaves the owner's Leads, so
        this is where the owner still sees it."""
        since = self.now() - timedelta(days=days)
        # passes, and the enquiries made on an agent's own site that the owner watches (followups.agent_site_enquiries)
        rows = await self.c("contacts").find({"$or": [{"passed_by": owner_id, "passed_at": {"$gte": since}},
                                                      {"watched_by": owner_id, "agent_wa_at": {"$gte": since}}]}).to_list(200)
        profs: dict = {}
        out = []
        for c in sorted(rows, key=lambda r: r.get("passed_at") or r["agent_wa_at"], reverse=True):
            to = c.get("passed_to") or c.get("agent_id")
            if to not in profs:
                profs[to] = await self.c("agent_public_profiles").find_one({"agent_id": to}) or {}
            site = not c.get("passed_at")
            h = ({"by": "site", "whatsapp_status": c.get("agent_wa_status"), "whatsapp_error": c.get("agent_wa_error"),
                  "text": c.get("agent_wa_text")} if site else c.get("handover") or {})
            digits = _lead_digits(profs[to])
            out.append({"lead_id": c["_id"], "name": c.get("name"), "passed_at": _iso(c["agent_wa_at"] if site else c["passed_at"]),
                        "agent_id": to, "agent_name": self._agent_name(profs[to]) if profs[to] else "Agent", "by": h.get("by") or "owner",
                        "rule": (h.get("rule") or {}).get("label"), "whatsapp_status": h.get("whatsapp_status"),
                        "whatsapp_error": h.get("whatsapp_error"), "text": h.get("text"),
                        "whatsapp_url": f"https://wa.me/{digits}?text={quote(h['text'])}" if digits and h.get("text") else None})
        return out

    # ---- the owner's rules: leads about a project or an area go to one agent by themselves ---------------------------
    @staticmethod
    def _areas(lead: dict, project: Optional[dict]) -> List[str]:
        out = [project["area"]] if project and project.get("area") else []
        return list(dict.fromkeys(out + list((lead.get("requirement") or {}).get("localities") or [])))

    async def routes(self, owner_id: str) -> List[dict]:
        rows = await self.c("lead_routes").find({"owner_id": owner_id}).to_list(200)
        names: dict = {}
        for r in rows:
            if r["agent_id"] not in names:
                prof = await self.c("agent_public_profiles").find_one({"agent_id": r["agent_id"]})
                names[r["agent_id"]] = self._agent_name(prof) if prof else "Agent"
        return sorted([{"id": r["_id"], "agent_id": r["agent_id"], "agent_name": names[r["agent_id"]], "kind": r["kind"],
                        "label": r.get("label") or r["key"], "passed": r.get("passed", 0)} for r in rows],
                      key=lambda r: (r["agent_name"].lower(), r["label"].lower()))

    async def add_route(self, owner_id: str, agent_id: str, kind: str, label: str, key: Optional[str] = None) -> dict:
        """kind 'area' (label = an area's name, e.g. Wagholi) or 'project' (key = a project page's slug, label its name).
        One agent per area or project."""
        label = (label or "").strip()
        key = (key or label).strip()
        key = key.lower() if kind == "area" else key
        if kind not in ("area", "project") or not key or len(key) > 120:
            raise InboxError("Say which area or project page", 422)
        await self._live_agent(agent_id)
        rid = f"{owner_id}:{kind}:{key}"
        now = self.now()
        if await self.c("lead_routes").find_one({"_id": rid}):
            await self.c("lead_routes").update_one({"_id": rid}, {"$set": {"agent_id": agent_id, "label": label, "updated_at": now}})
        else:
            await self.c("lead_routes").insert_one({"_id": rid, "owner_id": owner_id, "agent_id": agent_id, "kind": kind, "key": key,
                                                    "label": label, "created_at": now, "passed": 0})
        return {"id": rid}

    async def remove_route(self, owner_id: str, rid: str) -> dict:
        await self.c("lead_routes").delete_one({"_id": rid, "owner_id": owner_id})
        return {"removed": rid}

    async def route_for(self, owner_id: str, lead: dict, project: Optional[dict]) -> Optional[dict]:
        """The rule that picks this lead: its project page first, then the project's area, then an area they named."""
        keys = ([("project", project["slug"])] if project else []) + [("area", a.lower()) for a in self._areas(lead, project)]
        for kind, key in keys:
            r = await self.c("lead_routes").find_one({"_id": f"{owner_id}:{kind}:{key}"})
            if r:
                return {"id": r["_id"], "agent_id": r["agent_id"], "kind": kind, "label": r.get("label") or key}
        return None

    async def _move_lead(self, lead_id: Optional[str], owner_id: str, to_agent: str, phone: str, now: datetime) -> Optional[str]:
        """The owner's lead becomes the agent's; if the agent already has this phone as a lead, that one is kept (and the owner's
        copy is marked passed, so the automatic pass does not try it again)."""
        contacts = self.c("contacts")
        lead = await contacts.find_one({"_id": lead_id, "agent_id": owner_id}) if lead_id else None
        if not lead and phone:
            lead = await contacts.find_one({"agent_id": owner_id, "phone": phone})
        if not lead:
            return None
        mark = {"passed_by": owner_id, "passed_to": to_agent, "passed_at": now}
        if lead.get("phone"):
            theirs = await contacts.find_one({"agent_id": to_agent, "phone": lead["phone"]})
            if theirs:
                await contacts.update_one({"_id": lead["_id"]}, {"$set": mark})
                return theirs["_id"]
        await contacts.update_one({"_id": lead["_id"]}, {"$set": {"agent_id": to_agent, **mark}})
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


def _money(inr) -> str:
    return f"Rs {inr / 1e7:.2f}".rstrip("0").rstrip(".") + " Cr" if inr >= 1e7 else f"Rs {inr / 1e5:.0f} L"


def _first_name(lead: dict) -> str:
    name = (lead.get("name") or "").split()
    return name[0][:40] if name else "Sir"


def project_params(lead: dict, project: dict) -> List[str]:
    """{{1}} name, {{2}} the project and its area, {{3}} what they asked for on its page (the form's line, handover.ask_of)."""
    where = f", {project['area']}" if project.get("area") else ""
    want = PROJECT_WANT.get(handover.ask_of(lead.get("message"))["want"] or "", "the price sheet and floor plans")
    return [_first_name(lead), re.sub(r"\s+", " ", f"{project['name']}{where}").strip()[:100], want]


def followup_params(lead: dict, project: Optional[dict] = None) -> List[str]:
    """{{1}} name, {{2}} what they want, {{3}} the budget, else the area they asked about, else 'your enquiry on our website';
    WhatsApp rejects empty or multi-line parameters."""
    req = lead.get("requirement") or {}
    bhk = req.get("bhk")
    what = f"{int(bhk) if float(bhk).is_integer() else bhk} BHK home" if bhk else "home"
    lo, hi = req.get("budget_min_inr"), req.get("budget_max_inr")
    budget = f"{_money(lo)} to {_money(hi)}" if lo and hi and lo != hi else f"up to {_money(hi)}" if hi else ""
    area = (project or {}).get("area") or ", ".join(req.get("localities") or [])[:60]
    return [_first_name(lead), what, budget or area or "your enquiry on our website"]


def _live(profile: dict) -> bool:
    """A profile that can take buyers: not switched off and not a merged-away copy (slug '<name>-retired-<date>')."""
    return profile.get("is_active") is not False and "-retired-" not in (profile.get("slug") or "")


def _lead_digits(profile: dict) -> Optional[str]:
    """Where the agent gets buyers on WhatsApp: the office number on their site (branding_data.office_phone) when they set one, else
    the profile phone. House Deal (2026-10-30): the office line +91 74472 12121 is also the phone of their retired login, so it
    cannot be the profile phone (that is how a retired account is recognised) and lives in office_phone instead."""
    return _wa_digits((profile.get("branding_data") or {}).get("office_phone")) or _wa_digits(profile.get("phone"))


def _wa_digits(phone) -> Optional[str]:
    """'+91 98765 43210' -> '919876543210'; None unless it is an Indian mobile."""
    d = re.sub(r"\D", "", str(phone or ""))
    if len(d) == 10 and d[0] in "6789":
        d = "91" + d
    return d if len(d) == 12 and d.startswith("91") and d[2] in "6789" else None
