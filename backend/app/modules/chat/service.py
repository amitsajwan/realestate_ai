"""Chat sessions (`chat_sessions`, _id = session id from the visitor's browser), rate limits, and hand-off of a confirmed lead to the tracking module."""
import logging
import re
from datetime import datetime, timedelta
from typing import Callable, Optional

from app.modules.knowledge.grounding import Ref, facts_for
from app.modules.tracking.schemas import InquiryIn
from app.modules.tracking.service import TrackingError

from . import engine

log = logging.getLogger(__name__)
SESSION_RX = re.compile(r"^[A-Za-z0-9_-]{12,64}$")
ID_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
AREA_RX = re.compile(r"^[A-Za-z][A-Za-z _-]{1,39}$")
MAX_TEXT = 500
MAX_PER_HOUR = 60
MAX_MESSAGES_KEPT = 40


class ChatError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class ChatService:
    def __init__(self, db, tracking, llm=None, now: Callable[[], datetime] = datetime.utcnow):
        self.sessions = db.get_collection("chat_sessions")
        self.profiles = db.get_collection("agent_public_profiles")
        self.db, self.listings, self.calendar = db, db.get_collection("listings"), db.get_collection("content_calendar")
        self.tracking, self.llm, self.now = tracking, llm, now

    async def conversations(self, agent_id: str, limit: int = 30) -> list:
        """The agent's recent website chats: which need a person, which became leads. Never includes phone numbers (leads hold those)."""
        profile = await self.profiles.find_one({"agent_id": agent_id})
        if not profile:
            return []
        docs = await self.sessions.find({"agent_slug": profile["slug"]}).sort("updated_at", -1).limit(limit).to_list(limit)
        return [{"id": d["_id"][-8:], "updated_at": d.get("updated_at"), "needs_human": bool(d.get("needs_human")) and not d.get("lead_created"),
                 "lead_created": bool(d.get("lead_created")), "summary": engine.summary(d["data"]), "questions": d["data"].get("questions", [])[-3:], "missing": d["data"].get("missing", [])[-3:],
                 "name": d["data"].get("name"), "messages": len(d.get("messages", []))} for d in docs if d.get("messages")]

    async def grounding_for(self, context: Optional[dict]):
        """What we know about the page the visitor is on: a public listing, a published post, or an area (in that order). None when unknown.
        The context comes from the browser, so every id is looked up and checked here; nothing in it is trusted."""
        ctx = context or {}
        lid, pid, loc = ctx.get("listing_id"), ctx.get("post_id"), ctx.get("locality")
        try:
            if lid and ID_RX.match(str(lid)):
                doc = await self.listings.find_one({"_id": str(lid), "status": {"$in": ["live", "under_offer"]}, "visibility": {"$in": ["public", "network"]}})
                if doc:
                    return await facts_for(Ref.listing(str(lid)), self.db)
            if pid and ID_RX.match(str(pid)):
                doc = await self.calendar.find_one({"_id": str(pid), "status": "published"})
                if doc:
                    return await facts_for(Ref.calendar(str(pid)), self.db)
            if loc and AREA_RX.match(str(loc)):
                return await facts_for(Ref.area(str(loc)), self.db)
        except Exception as e:  # knowledge is a help, never a reason to fail a chat message
            log.info("chat grounding failed: %s", e)
        return None

    async def message(self, session_id: str, agent_slug: str, text: str, source: Optional[str] = None, context: Optional[dict] = None) -> dict:
        if not SESSION_RX.match(session_id or ""):
            raise ChatError("Invalid session")
        text = (text or "").strip()
        if not text or len(text) > MAX_TEXT:
            raise ChatError("Please send a short message (up to 500 characters)")
        if not await self.profiles.find_one({"slug": agent_slug, "is_public": True}):
            raise ChatError("Unknown site", 404)
        now = self.now()
        s = await self.sessions.find_one({"_id": session_id}) or {
            "_id": session_id, "agent_slug": agent_slug, "created_at": now, "data": engine.new_data(), "messages": [], "hits": []}
        s["hits"] = [h for h in s.get("hits", []) if h > now - timedelta(hours=1)]
        if len(s["hits"]) >= MAX_PER_HOUR:
            return {"reply": "You have sent a lot of messages in a short time. Please try again a little later.", "quick_replies": [], "lead_created": False}
        s["hits"].append(now)

        t = await engine.turn(s["data"], text, self.llm, await self.grounding_for(context))
        lead_created = False
        if t.lead:
            try:
                await self.tracking.capture_inquiry(InquiryIn(
                    agent_slug=agent_slug, anon_id=("chat-" + session_id)[:64], source=(source or "chat")[:40], consent=True, **t.lead))
                lead_created = True
            except TrackingError as e:  # e.g. too many enquiries from this number: keep chatting, tell the visitor kindly
                log.info("chat lead not stored: %s", e)
                t.reply = "Thanks! We already have your details, and our team will be in touch soon."
        s["messages"] = (s.get("messages", []) + [
            {"role": "user", "text": text, "ts": now}, {"role": "bot", "text": t.reply, "ts": now}])[-MAX_MESSAGES_KEPT:]
        s.update(updated_at=now, needs_human=bool(s["data"].get("needs_human")), lead_created=bool(s.get("lead_created") or lead_created))
        if await self.sessions.find_one({"_id": session_id}):
            await self.sessions.update_one({"_id": session_id}, {"$set": {k: v for k, v in s.items() if k != "_id"}})
        else:
            await self.sessions.insert_one(s)
        return {"reply": t.reply, "quick_replies": t.quick, "lead_created": lead_created}
