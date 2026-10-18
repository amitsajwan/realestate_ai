"""Messenger and Instagram DM assistant: the WhatsApp assistant's brain on the Page's own inboxes. One incoming message in, at most one reply
out (free, inside the 24-hour window the buyer opened).

Collections
  dm_messages       _id = Meta message id (inbound, the idempotency key) or out-<uuid> (outbound, saved before sending; message_id
                    is Meta's id once sent)
  dm_conversations  _id = "<platform>:<sender id>" (platform = messenger | instagram): agent, engine state, last 20 messages, opt-out, lead id,
                    human_until (a person replied from the Page inbox: the assistant stays quiet until then)

Rules
  - Routing: the lead this sender already has (the comment assistant's private reply, or an earlier DM) > an interest code in the text > the
    owner agent.
  - Answers come from the website chat engine and grounded knowledge, in the buyer's language; the engine asks for the number with its consent line.
  - A lead from the first message (no number yet); the number and requirement are added as the buyer gives them.
  - A person replying from the Page inbox (an echo without our BOT_TAG) pauses the assistant in that chat for MESSENGER_HUMAN_PAUSE_HOURS.
  - STOP / START as on WhatsApp. Replies only inside 24 hours of the buyer's last message. Dry run records the reply and sends nothing.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Callable, Optional

from . import adapters, lang as L
from .brain import SHARED_ASK, UNDERSTAND, ChatBrain  # noqa: F401  (UNDERSTAND: the tests read it here)
from .dm_config import DmConfig
from .dm_graph import BOT_TAG, DmGraphError
from .service import MAX_KEPT, MAX_REPLIES_PER_HOUR, MAX_TEXT, START_RX, STOP_RX, WINDOW

log = logging.getLogger(__name__)

PLATFORMS = ("messenger", "instagram")
OURS_WINDOW = timedelta(minutes=10)   # an echo of a reply we sent this recently, with the same text, is ours even without the tag

NOTICE = {
    "en": "Note: {agent} may also reply to you here. Reply STOP at any time and we will not message you again.",
    "hi": "सूचना: {agent} भी आपको यहाँ जवाब दे सकते हैं। संदेश बंद करवाने के लिए कभी भी STOP लिखें।",
    "hinglish": "Note: {agent} bhi aapko yahan reply kar sakte hain. Messages band karne ke liye kabhi bhi STOP likhein.",
    "mr": "सूचना: {agent} सुद्धा तुम्हाला इथे उत्तर देऊ शकतात. मेसेज बंद करण्यासाठी कधीही STOP लिहा.",
    "mr_latn": "Note: {agent} suddha tumhala ithe uttar deu shaktat. Message band karnyasathi kadhihi STOP liha.",
}


def _ts(ms) -> Optional[datetime]:
    try:
        return datetime.utcfromtimestamp(int(ms) / 1000)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def platform_of(obj: str) -> Optional[str]:
    return {"page": "messenger", "instagram": "instagram"}.get(obj or "")


def refs_of(ev: dict) -> dict:
    """Where the person came from, as Meta tells it: the ref of the link or ad they opened (m.me / ig.me ?ref=, click-to-message ads), the
    post, reel or story they shared or replied to (ids and links). Empty when the chat simply started."""
    msg, pb = ev.get("message") or {}, ev.get("postback") or {}
    referral = ev.get("referral") or msg.get("referral") or pb.get("referral") or {}
    out = {"ref": str(referral.get("ref") or "")[:64], "ad_id": str(referral.get("ad_id") or "")[:64], "media_ids": [], "urls": [],
           "reply_to_story": False}
    reply_to = msg.get("reply_to") or {}
    story = reply_to.get("story") or {}
    if story:
        out["reply_to_story"] = True
        out["media_ids"].append(str(story.get("id") or ""))
        out["urls"].append(str(story.get("url") or ""))
    for att in msg.get("attachments") or []:
        pay = att.get("payload") or {}
        for k in ("reel_video_id", "id", "media_id", "ig_post_media_id"):
            if pay.get(k):
                out["media_ids"].append(str(pay[k]))
        if pay.get("url"):
            out["urls"].append(str(pay["url"])[:500])
        if pay.get("title"):
            out["shared_title"] = str(pay["title"])[:200]
    out["media_ids"] = [x for x in out["media_ids"] if x][:5]
    out["urls"] = [x for x in out["urls"] if x][:5]
    return {k: v for k, v in out.items() if v}


def parse(ev: dict) -> dict:
    """One `messaging` event -> {kind: message | echo | other, mid, sender, recipient, text, media, ts, tag, refs}."""
    msg = ev.get("message") or {}
    pb = ev.get("postback") or {}
    sender = str((ev.get("sender") or {}).get("id") or "")
    recipient = str((ev.get("recipient") or {}).get("id") or "")
    refs = refs_of(ev)
    if msg:
        kind = "echo" if msg.get("is_echo") else "message"
        text = str(msg.get("text") or "")
        media = bool(msg.get("attachments")) and not text
        return {"kind": kind, "mid": str(msg.get("mid") or ""), "sender": sender, "recipient": recipient, "text": text[:1000],
                "media": media, "ts": _ts(ev.get("timestamp")), "tag": msg.get("metadata"), "refs": refs}
    if pb:  # a tapped button (ice breaker, persistent menu): its title is what the buyer "said"
        return {"kind": "message", "mid": str(pb.get("mid") or ""), "sender": sender, "recipient": recipient,
                "text": str(pb.get("title") or pb.get("payload") or "")[:1000], "media": False, "ts": _ts(ev.get("timestamp")), "tag": None,
                "refs": refs}
    if ev.get("referral"):  # opened the chat from a link or an ad without writing yet: remembered for their first message
        return {"kind": "referral", "mid": "", "sender": sender, "recipient": recipient, "text": "", "media": False, "ts": _ts(ev.get("timestamp")),
                "tag": None, "refs": refs}
    return {"kind": "other", "mid": "", "sender": sender, "recipient": recipient, "text": "", "media": False, "ts": None, "tag": None}


class DmService(ChatBrain):
    def __init__(self, db, cfg: DmConfig, graph=None, llm=None, now: Callable[[], datetime] = datetime.utcnow):
        self.db, self.cfg, self.graph, self.llm, self.now = db, cfg, graph, llm, now
        self.messages = db.get_collection("dm_messages")
        self.convs = db.get_collection("dm_conversations")

    def _clean(self, text) -> str:
        from app.platform.meta_graph.publisher import sanitize
        return sanitize(text, self.cfg.secrets)

    def _ours(self, account_id: str) -> bool:
        return bool(account_id) and account_id in (self.cfg.page_id, self.cfg.ig_id)

    # ---- webhook intake (in the request: fast, no network) ------------------------------------------------------------
    async def claim(self, platform: str, m: dict) -> bool:
        """Store an inbound buyer message once. False for a retry Meta sent again, our own account, or a message with no id."""
        if m["kind"] != "message" or not m["mid"] or not m["sender"] or self._ours(m["sender"]):
            return False
        if await self.messages.find_one({"_id": m["mid"]}):
            return False
        try:
            await self.messages.insert_one({"_id": m["mid"], "direction": "in", "platform": platform, "sender": m["sender"],
                                            "text": m["text"], "ts": m["ts"] or self.now(), "received_at": self.now(), "status": "received"})
        except Exception:  # a duplicate key from a concurrent retry
            return False
        return True

    async def echo(self, platform: str, m: dict) -> bool:
        """A message the Page sent. Ours (tagged, or the reply we just sent) is ignored; anything else is a person answering from the Page
        inbox, so the assistant steps back in that chat. Returns True when it paused the chat."""
        buyer = m["recipient"]
        if not buyer or m["tag"] == BOT_TAG:
            return False
        now = self.now()
        if m["mid"] and await self.messages.find_one({"message_id": m["mid"], "direction": "out"}):
            return False
        # Instagram may not echo the tag, and the echo can arrive before the send call returns: our reply is saved before it is sent
        sent = await self.messages.find_one({"direction": "out", "recipient": buyer, "text": m["text"]})
        if sent and now - sent["ts"] < OURS_WINDOW:
            return False
        cid = f"{platform}:{buyer}"
        conv = await self.convs.find_one({"_id": cid})
        until = now + timedelta(hours=self.cfg.human_pause_hours)
        if conv:
            msgs = (conv.get("messages") or []) + [{"role": "agent", "text": m["text"] or "[attachment]", "ts": now}]
            await self.convs.update_one({"_id": cid}, {"$set": {"human_until": until, "messages": msgs[-MAX_KEPT:], "updated_at": now}})
        else:
            await self.convs.insert_one(self._new_conv(cid, platform, buyer, now) | {"human_until": until})
        return True

    async def remember_referral(self, platform: str, m: dict) -> None:
        """They opened the chat from a link or an ad and have not written yet: what they opened is kept for their first message."""
        if not m.get("sender") or self._ours(m["sender"]) or not m.get("refs"):
            return
        cid, now = f"{platform}:{m['sender']}", self.now()
        if await self.convs.find_one({"_id": cid}):
            await self.convs.update_one({"_id": cid}, {"$set": {"pending_refs": m["refs"], "origin_checked": False}})
        else:
            await self.convs.insert_one(self._new_conv(cid, platform, m["sender"], now) | {"pending_refs": m["refs"]})

    @staticmethod
    def _new_conv(cid: str, platform: str, sender: str, now: datetime) -> dict:
        from app.modules.chat import engine
        return {"_id": cid, "platform": platform, "sender": sender, "agent_id": None, "routed_by": None, "data": engine.new_data(),
                "messages": [], "created_at": now, "opted_out": False, "notice_sent_at": None, "lead_id": None, "context": None,
                "language": None, "needs_human_notified": False, "replies": [], "human_until": None}

    # ---- routing --------------------------------------------------------------------------------------------------------
    async def _route(self, conv: dict, text: str, now: datetime, refs: Optional[dict] = None) -> None:
        if refs or not conv.get("origin_checked"):
            # once per chat, and again whenever Meta says what they opened or shared: the post, reel, link or comment behind the chat
            conv["origin_checked"] = True
            origin = await adapters.dm_origin(self.db, conv["platform"], conv["sender"], refs)
            if origin:
                conv["context"] = origin
                if origin.get("listing_id") and conv.get("routed_by") in (None, "owner"):
                    listing_agent = await adapters.listing_agent(self.db, origin["listing_id"])
                    if listing_agent:
                        conv["agent_id"], conv["routed_by"] = listing_agent, "origin"
        if not conv.get("agent_id"):
            known = await adapters.find_dm_lead(self.db, conv["platform"], conv["sender"])
            if known:
                conv["agent_id"], conv["routed_by"], conv["lead_id"] = known.get("agent_id"), "lead", known["_id"]
        link = await adapters.find_interest_link(self.db, text) if text else None
        if link:
            conv["context"] = adapters.link_context(link, "wrote the code of")
            if conv.get("routed_by") in (None, "owner"):
                conv["agent_id"], conv["routed_by"] = adapters.interest_target_agent(link, self.cfg.owner_agent_id), "interest_code"
            await adapters.record_interest_event(self.db, link["code"], f"{conv['platform']}:{conv['sender']}", now)
        if not conv.get("agent_id"):
            conv["agent_id"], conv["routed_by"] = self.cfg.owner_agent_id or None, "owner"

    # ---- one message (background task) -------------------------------------------------------------------------------
    async def handle(self, platform: str, m: dict) -> dict:
        try:
            return await self._handle(platform, m)
        except Exception as e:
            log.error("dm: could not handle message: %s", self._clean(f"{type(e).__name__}: {e}"))
            if m.get("mid"):
                await self.messages.update_one({"_id": m["mid"]}, {"$set": {"status": "error", "error": self._clean(str(e))}})
            return {"status": "error"}

    async def _handle(self, platform: str, m: dict) -> dict:
        now = self.now()
        text = (m["text"] or "").strip()[:MAX_TEXT]
        cid = f"{platform}:{m['sender']}"
        conv = await self.convs.find_one({"_id": cid}) or self._new_conv(cid, platform, m["sender"], now)
        sent_at = m["ts"] or now
        last_in = conv.get("last_inbound_at")
        conv["last_inbound_at"] = max(sent_at, last_in) if last_in else sent_at
        refs, conv["pending_refs"] = m.get("refs") or conv.get("pending_refs"), None
        await self._route(conv, text, now, refs)
        lang = L.sticky(conv.get("language"), adapters.detect_language(text) if text else "en", text)
        conv["language"] = lang

        if text and STOP_RX.match(text):
            conv["opted_out"], conv["opted_out_at"] = True, now
            await adapters.mark_dm_opt_out(self.db, conv.get("lead_id"), True, now)
            return await self._finish(conv, m["mid"], L.pick(L.STOPPED, lang), "stopped", now, text)
        if conv.get("opted_out"):
            if text and START_RX.match(text):
                conv["opted_out"], conv["opted_out_at"] = False, None
                await adapters.mark_dm_opt_out(self.db, conv.get("lead_id"), False, now)
                return await self._finish(conv, m["mid"], L.pick(L.RESTARTED, lang), "restarted", now, text)
            return await self._finish(conv, m["mid"], None, "opted_out", now, text)

        human = conv.get("human_until") and conv["human_until"] > now
        reply = None
        if not human:
            shared = (m.get("refs") or {}).get("shared_title") or ""
            if (m["media"] or not text) and conv.get("context") and conv["context"].get("kind"):
                # they shared our post without a word: what it is about, then what they would like to know
                reply = await self._answer(conv, shared or SHARED_ASK, lang)
            else:
                reply = L.pick(L.MEDIA, lang) if (m["media"] or not text) else await self._answer(conv, text, lang)
        elif text:
            await self._answer(conv, text, lang)  # still learn the requirement and number for the lead; the person answers
        agent_id = conv.get("agent_id")
        if agent_id and conv.get("role") == "agent":
            if not conv.get("agent_notified"):
                conv["agent_notified"] = True
                label = adapters.DM_LABEL[conv["platform"]]
                await adapters.notify(self.db, agent_id, "dm_agent", f"An agent wrote on {label}: \"{(text or '')[:140]}\"",
                                      {"conversation_id": conv["_id"]}, now)
        elif agent_id:
            await self._lead(conv, agent_id, text or "[attachment]", now)
        else:
            log.warning("dm: no agent for this chat (set MESSENGER_OWNER_AGENT_ID); replying without saving a lead")
        if reply and agent_id and not conv.get("notice_sent_at") and conv.get("role") != "agent":
            reply = f"{reply}\n\n{L.pick(NOTICE, lang, agent=await adapters.agent_name(self.db, agent_id) or L.pick(L.TEAM, lang))}"
            conv["notice_sent_at"] = now
        return await self._finish(conv, m["mid"], reply, "answered" if reply else "human", now, text)

    async def _lead(self, conv: dict, agent_id: str, text: str, now: datetime) -> None:
        label = adapters.DM_LABEL[conv["platform"]]
        try:
            contact_id, created = await adapters.upsert_dm_lead(self.db, agent_id=agent_id, platform=conv["platform"], sender=conv["sender"],
                                                                data=conv["data"], message=f"{label}: {text}", now=now, interest=conv.get("context"))
        except Exception as e:  # a lead problem must never stop the reply
            log.warning("dm: lead not stored: %s", self._clean(type(e).__name__))
            return
        conv["lead_id"] = contact_id
        ref = {"lead_id": contact_id, "conversation_id": conv["_id"]}
        who = conv["data"].get("name") or "A buyer"
        if created:
            await adapters.notify(self.db, agent_id, "new_dm_lead", f"{who} messaged on {label}. {adapters.summary(conv['data'])}", ref, now)
        if conv["data"].get("needs_human") and not conv.get("needs_human_notified"):
            conv["needs_human_notified"] = True
            asked = (conv["data"].get("questions") or [""])[-1]
            await adapters.notify(self.db, agent_id, "dm_needs_you", f"{who} asked something on {label} we could not answer: \"{asked[:120]}\"",
                                  ref, now)

    # ---- sending ----------------------------------------------------------------------------------------------------------
    def in_window(self, conv: dict, now: datetime) -> bool:
        last = conv.get("last_inbound_at")
        return bool(last) and now - last < WINDOW

    async def _send(self, conv: dict, reply: str, now: datetime) -> dict:
        rec = {"direction": "out", "platform": conv["platform"], "recipient": conv["sender"], "agent_id": conv.get("agent_id"), "text": reply,
               "ts": now, "error": None, "dry_run": self.cfg.dry_run}
        recent = [r for r in conv.get("replies", []) if r > now - timedelta(hours=1)]
        if not self.in_window(conv, now):
            rec.update(status="refused", error="outside the 24-hour messaging window")
        elif len(recent) >= MAX_REPLIES_PER_HOUR:
            rec.update(status="refused", error="hourly reply cap for this buyer")
        elif self.cfg.dry_run:
            rec["status"] = "dry_run"
        elif self.graph is None or not self.cfg.can_send:
            rec.update(status="failed", error="Messenger is not connected (no Page token)")
        else:
            rec.update(_id=f"out-{uuid.uuid4().hex}", status="sending", message_id=None)
            await self.messages.insert_one(dict(rec))  # saved first, so its echo is known as ours however fast it comes back
            try:
                rec["message_id"] = await self.graph.send_text(conv["sender"], reply) or None
                rec["status"] = "sent"
            except DmGraphError as e:
                rec.update(status="failed", error=self._clean(e))
                log.warning("dm: send failed: %s", rec["error"])
            await self.messages.update_one({"_id": rec["_id"]}, {"$set": {k: rec[k] for k in ("status", "message_id", "error")}})
        if rec["status"] in ("sent", "dry_run"):
            conv["replies"] = recent + [now]
        if "_id" not in rec:
            rec["_id"] = f"out-{uuid.uuid4().hex}"
            await self.messages.insert_one(rec)
        return rec

    async def _finish(self, conv: dict, mid: str, reply: Optional[str], outcome: str, now: datetime, text: str) -> dict:
        conv["messages"] = conv.get("messages", []) + [{"role": "user", "text": text or "[attachment]", "ts": now}]
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

    # ---- Studio -------------------------------------------------------------------------------------------------------------
    async def conversations(self, agent_id: str, limit: int = 30) -> list:
        docs = await self.convs.find({"agent_id": agent_id}).sort("updated_at", -1).limit(min(max(limit, 1), 100)).to_list(100)
        now = self.now()
        return [{
            "id": uuid.uuid5(uuid.NAMESPACE_URL, d["_id"]).hex[:12], "channel": d["platform"], "name": d["data"].get("name") or None,
            "lead_id": d.get("lead_id"), "summary": adapters.summary(d["data"]), "needs_human": bool(d.get("needs_human")),
            "opted_out": bool(d.get("opted_out")), "updated_at": d.get("updated_at"), "language": d.get("language") or "en",
            "interest_title": (d.get("context") or {}).get("title") or None, "window_open": self.in_window(d, now),
            "person_replying": bool(d.get("human_until") and d["human_until"] > now),
            "messages": [{"role": x["role"], "text": x["text"][:600], "ts": x["ts"], "status": x.get("status")} for x in (d.get("messages") or [])[-6:]],
        } for d in docs]
