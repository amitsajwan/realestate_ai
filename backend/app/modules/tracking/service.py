"""Tracking + lead capture. Owner scoping: every read/write is filtered by agent_id."""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Callable, Optional

from . import scoring
from .schemas import EventIn, InquiryIn, StageUpdate

logger = logging.getLogger(__name__)

BOT_MARKERS = ("bot", "crawler", "spider", "preview", "facebookexternalhit", "whatsapp/", "curl", "python-requests")
MAX_EVENTS_PER_ANON_PER_MINUTE = 60


class TrackingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def is_bot(user_agent: Optional[str]) -> bool:
    ua = (user_agent or "").lower()
    return not ua or any(m in ua for m in BOT_MARKERS)


class TrackingService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow):
        self.profiles = db.get_collection("agent_public_profiles")
        self.events = db.get_collection("events")
        self.contacts = db.get_collection("contacts")
        self.now = now

    async def _agent_id(self, slug: str) -> str:
        profile = await self.profiles.find_one({"slug": slug, "is_public": True})
        if not profile:
            raise TrackingError("Agent site not found", 404)
        return profile["agent_id"]

    async def _record(self, agent_id: str, e, type_: str, contact_id: Optional[str]) -> int:
        """Store one event and return the points it earned."""
        prior = 0
        if type_ == "listing_view" and e.listing_id:
            prior = await self.events.count_documents(
                {"agent_id": agent_id, "anon_id": e.anon_id, "type": "listing_view", "listing_id": e.listing_id})
        await self.events.insert_one({
            "agent_id": agent_id, "anon_id": e.anon_id, "contact_id": contact_id, "type": type_,
            "listing_id": e.listing_id, "source": e.source, "utm": e.utm, "ts": self.now(),
        })
        return scoring.event_points(type_, prior)

    async def track_event(self, e: EventIn, user_agent: Optional[str]) -> bool:
        """Returns False when ignored (bot / rate limited); never raises for the visitor's benefit
        except for unknown agents."""
        agent_id = await self._agent_id(e.agent_slug)
        if is_bot(user_agent):
            return False
        minute_ago = self.now() - timedelta(minutes=1)
        if await self.events.count_documents({"anon_id": e.anon_id, "ts": {"$gte": minute_ago}}) >= MAX_EVENTS_PER_ANON_PER_MINUTE:
            return False
        contact = await self.contacts.find_one({"agent_id": agent_id, "anon_ids": e.anon_id})
        points = await self._record(agent_id, e, e.type, contact["_id"] if contact else None)
        if contact:
            await self.contacts.update_one(
                {"_id": contact["_id"]},
                {"$inc": {"score_base": points}, "$set": {"last_activity_at": self.now()}})
        return True

    async def capture_inquiry(self, i: InquiryIn) -> dict:
        if not i.consent:
            raise TrackingError("Consent is required to contact you about this enquiry")
        agent_id = await self._agent_id(i.agent_slug)
        now = self.now()
        contact = await self.contacts.find_one({"agent_id": agent_id, "phone": i.phone})
        created = contact is None
        if created:
            # anonymous history from this browser becomes the new contact's history
            history = await self.events.find({"agent_id": agent_id, "anon_id": i.anon_id, "contact_id": None}).to_list(1000)
            base, seen = 0, {}
            for ev in sorted(history, key=lambda d: d["ts"]):
                lid = ev.get("listing_id")
                prior = seen.get(lid, 0) if ev["type"] == "listing_view" else 0
                base += scoring.event_points(ev["type"], prior)
                if ev["type"] == "listing_view":
                    seen[lid] = prior + 1
            res = await self.contacts.insert_one({
                "_id": uuid.uuid4().hex,
                "agent_id": agent_id, "name": i.name, "phone": i.phone, "message": i.message,
                "anon_ids": [i.anon_id], "stage": "new", "source": i.source, "utm": i.utm,
                "first_listing_id": i.listing_id,
                "consent": {"given_at": now, "purpose": "enquiry follow-up", "agent_slug": i.agent_slug},
                "score_base": base, "created_at": now, "last_activity_at": now, "notes": [],
            })
            contact_id = res.inserted_id
            await self.events.update_many(
                {"agent_id": agent_id, "anon_id": i.anon_id, "contact_id": None}, {"$set": {"contact_id": contact_id}})
        else:
            contact_id = contact["_id"]
            await self.contacts.update_one({"_id": contact_id}, {"$addToSet": {"anon_ids": i.anon_id}})
        points = await self._record(agent_id, i, "inquiry", contact_id)
        await self.contacts.update_one(
            {"_id": contact_id}, {"$inc": {"score_base": points}, "$set": {"last_activity_at": now, "last_message": i.message}})
        return {"received": True, "new_lead": created}

    # ---- agent-facing (owner scoped) ----

    def _view(self, c: dict) -> dict:
        now = self.now()
        value = scoring.score(c.get("score_base", 0), c["last_activity_at"], now)
        return {
            "id": c["_id"], "name": c["name"], "phone": c["phone"], "stage": c["stage"],
            "source": c.get("source"), "message": c.get("last_message") or c.get("message"),
            "score": value, "temperature": scoring.temperature(value),
            "first_listing_id": c.get("first_listing_id"),
            "created_at": c["created_at"], "last_activity_at": c["last_activity_at"],
        }

    async def list_leads(self, agent_id: str, stage: Optional[str] = None, limit: int = 50) -> list:
        flt = {"agent_id": agent_id}
        if stage:
            flt["stage"] = stage
        docs = await self.contacts.find(flt).sort("last_activity_at", -1).limit(min(limit, 200)).to_list(200)
        views = [self._view(d) for d in docs]  # already most-recent first
        return sorted(views, key=lambda v: -v["score"])  # stable: hottest first, ties stay most-recent first

    async def lead_detail(self, agent_id: str, contact_id: str) -> dict:
        contact = await self.contacts.find_one({"_id": contact_id, "agent_id": agent_id})
        if not contact:
            raise TrackingError("Lead not found", 404)
        events = await self.events.find({"agent_id": agent_id, "contact_id": contact_id}).sort("ts", 1).to_list(500)
        return {
            **self._view(contact), "notes": contact.get("notes", []),
            "consent": contact.get("consent"),
            "timeline": [{"type": e["type"], "listing_id": e.get("listing_id"), "source": e.get("source"), "ts": e["ts"]}
                         for e in events],
        }

    async def update_stage(self, agent_id: str, contact_id: str, u: StageUpdate) -> dict:
        contact = await self.contacts.find_one({"_id": contact_id, "agent_id": agent_id})
        if not contact:
            raise TrackingError("Lead not found", 404)
        upd = {"$set": {"stage": u.stage, "last_activity_at": self.now()}}
        if u.note:
            upd["$push"] = {"notes": {"text": u.note, "ts": self.now(), "stage": u.stage}}
        await self.contacts.update_one({"_id": contact_id, "agent_id": agent_id}, upd)
        return await self.lead_detail(agent_id, contact_id)
