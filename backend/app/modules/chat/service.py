"""Chat sessions (`chat_sessions`, _id = session id from the visitor's browser), rate limits, and hand-off of a confirmed lead to the tracking module."""
import logging
import re
from datetime import datetime, timedelta
from typing import Callable, Optional

from app.modules.tracking.schemas import InquiryIn
from app.modules.tracking.service import TrackingError

from . import engine

log = logging.getLogger(__name__)
SESSION_RX = re.compile(r"^[A-Za-z0-9_-]{12,64}$")
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
        self.tracking, self.llm, self.now = tracking, llm, now

    async def conversations(self, agent_id: str, limit: int = 30) -> list:
        """The agent's recent website chats: which need a person, which became leads. Never includes phone numbers (leads hold those)."""
        profile = await self.profiles.find_one({"agent_id": agent_id})
        if not profile:
            return []
        docs = await self.sessions.find({"agent_slug": profile["slug"]}).sort("updated_at", -1).limit(limit).to_list(limit)
        return [{"id": d["_id"][-8:], "updated_at": d.get("updated_at"), "needs_human": bool(d.get("needs_human")) and not d.get("lead_created"),
                 "lead_created": bool(d.get("lead_created")), "summary": engine.summary(d["data"]), "questions": d["data"].get("questions", [])[-3:],
                 "name": d["data"].get("name"), "messages": len(d.get("messages", []))} for d in docs if d.get("messages")]

    async def message(self, session_id: str, agent_slug: str, text: str, source: Optional[str] = None) -> dict:
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

        t = await engine.turn(s["data"], text, self.llm)
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
