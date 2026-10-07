"""In-app notifications for agents (collection `notifications`). A row: {_id, agent_id, kind, summary, ref, created_at, read, read_at}.

Any module may call `notify(db, agent_id, kind, summary, ref)`; Studio reads them (agent scoped) to show a badge. No phone numbers in
summaries: the lead itself holds those.
"""
import uuid
from datetime import datetime
from typing import Callable, Optional

KINDS = ("new_whatsapp_lead", "whatsapp_needs_you", "new_chat_lead", "chat_needs_you", "invite_request",
         "content_needs_you", "answer_gap")  # content_needs_you: the system cannot fix it alone (e.g. a missing Meta permission);
#                                              answer_gap: buyers keep asking something about a home that its details do not answer
MAX_SUMMARY = 300


async def notify(db, agent_id: str, kind: str, summary: str, ref: Optional[dict] = None, now: Optional[datetime] = None) -> Optional[str]:
    if not agent_id or not kind:
        return None
    doc = {"_id": uuid.uuid4().hex, "agent_id": agent_id, "kind": kind[:40], "summary": (summary or "")[:MAX_SUMMARY],
           "ref": ref or {}, "created_at": now or datetime.utcnow(), "read": False, "read_at": None}
    await db.get_collection("notifications").insert_one(doc)
    # TODO(paid alerts): when the owner adds a payment method, also send the agent a WhatsApp *utility template* here (e.g. "new_lead_alert"),
    # because the agent has not messaged us in the last 24 hours, so a free-form message is not allowed. Keep it behind a NOTIFY_WHATSAPP_TEMPLATE flag.
    return doc["_id"]


class NotificationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class NotificationService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow):
        self.col = db.get_collection("notifications")
        self.now = now

    @staticmethod
    def view(d: dict) -> dict:
        return {"id": d["_id"], "kind": d["kind"], "summary": d.get("summary") or "", "ref": d.get("ref") or {},
                "created_at": d["created_at"], "read": bool(d.get("read"))}

    async def list(self, agent_id: str, unread_only: bool = False, limit: int = 30) -> dict:
        flt = {"agent_id": agent_id}
        if unread_only:
            flt["read"] = False
        docs = await self.col.find(flt).sort("created_at", -1).limit(min(max(limit, 1), 100)).to_list(100)
        unread = await self.col.count_documents({"agent_id": agent_id, "read": False})
        return {"items": [self.view(d) for d in docs], "unread": unread}

    async def mark_read(self, agent_id: str, notification_id: str) -> dict:
        doc = await self.col.find_one({"_id": notification_id, "agent_id": agent_id})
        if not doc:
            raise NotificationError("Notification not found", 404)
        await self.col.update_one({"_id": notification_id, "agent_id": agent_id}, {"$set": {"read": True, "read_at": self.now()}})
        doc.update(read=True)
        return self.view(doc)
