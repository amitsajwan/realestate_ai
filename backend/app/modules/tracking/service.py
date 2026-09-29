"""Tracking + lead capture. Owner scoping: every read/write is filtered by agent_id."""
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Callable, Optional

from . import matching, requirement as reqmod, scoring, summary
from .followup import Polish, build_draft, polish_safely, whatsapp_url
from .schemas import DraftIn, EventIn, InquiryIn, StageUpdate

logger = logging.getLogger(__name__)

BOT_MARKERS = ("bot", "crawler", "spider", "preview", "facebookexternalhit", "whatsapp/", "curl", "python-requests")
MAX_EVENTS_PER_ANON_PER_MINUTE = 60
FOLLOW_UP_DAYS = 2


class TrackingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def is_bot(user_agent: Optional[str]) -> bool:
    ua = (user_agent or "").lower()
    return not ua or any(m in ua for m in BOT_MARKERS)


class TrackingService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow, polish: Optional[Polish] = None):
        self.listings = db.get_collection("listings")  # READ-ONLY here (matching); owned by the listings module
        self.polish = polish
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
        fields, sources = await self._observe_requirement(agent_id, i)
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
                "requirement": reqmod.merge(None, fields, sources) if fields else None,
            })
            contact_id = res.inserted_id
            await self.events.update_many(
                {"agent_id": agent_id, "anon_id": i.anon_id, "contact_id": None}, {"$set": {"contact_id": contact_id}})
        else:
            contact_id = contact["_id"]
            await self.contacts.update_one({"_id": contact_id}, {"$addToSet": {"anon_ids": i.anon_id}})
            if fields:
                merged = reqmod.merge(contact.get("requirement"), fields, sources)
                await self.contacts.update_one({"_id": contact_id}, {"$set": {"requirement": merged}})
        points = await self._record(agent_id, i, "inquiry", contact_id)
        await self.contacts.update_one(
            {"_id": contact_id}, {"$inc": {"score_base": points}, "$set": {"last_activity_at": now, "last_message": i.message}})
        return {"received": True, "new_lead": created}

    async def _own_listing(self, agent_id: str, listing_id: Optional[str]) -> Optional[dict]:
        if not listing_id:
            return None
        return await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})

    async def _observe_requirement(self, agent_id: str, i: InquiryIn):
        """What this enquiry tells us: stated fields > parsed from message > defaults from the enquired listing."""
        fields: dict = {}
        sources: dict = {}
        stated = {"bhk": i.bhk, "timeline": i.timeline, "financing": i.financing}
        for k, v in stated.items():
            if v is not None:
                fields[k], sources[k] = v, "stated"
        if i.budget_min_inr is not None or i.budget_max_inr is not None:
            fields["budget_min_inr"], fields["budget_max_inr"], sources["budget"] = i.budget_min_inr, i.budget_max_inr, "stated"
        for k, v in reqmod.infer_from_message(i.message).items():
            name = "budget" if k.startswith("budget") else k
            if sources.get(name) != "stated":  # stated always wins within one enquiry
                fields[k] = v
                sources[name] = "inferred"
        listing = await self._own_listing(agent_id, i.listing_id)
        if listing:
            if listing.get("locality"):
                fields["localities"], sources["localities"] = [listing["locality"]], "default"
            if "bhk" not in sources and listing.get("bhk"):
                fields["bhk"], sources["bhk"] = listing["bhk"], "default"
        # a buyer who only enquired about a listing has no requirement worth storing beyond its defaults
        return fields, sources

    # ---- agent-facing (owner scoped) ----

    def _view(self, c: dict) -> dict:
        now = self.now()
        value = scoring.score(c.get("score_base", 0), c["last_activity_at"], now)
        return {
            "id": c["_id"], "name": c["name"], "phone": c["phone"], "stage": c["stage"],
            "source": c.get("source"), "message": c.get("last_message") or c.get("message"),
            "score": value, "temperature": scoring.temperature(value),
            "first_listing_id": c.get("first_listing_id"),
            "requirement_line": reqmod.requirement_line(reqmod.public(c.get("requirement"))),
            "created_at": c["created_at"], "last_activity_at": c["last_activity_at"],
        }

    async def list_leads(self, agent_id: str, stage: Optional[str] = None, limit: int = 50) -> list:
        flt = {"agent_id": agent_id}
        if stage:
            flt["stage"] = stage
        docs = await self.contacts.find(flt).sort("last_activity_at", -1).limit(min(limit, 200)).to_list(200)
        views = [self._view(d) for d in docs]  # already most-recent first
        return sorted(views, key=lambda v: -v["score"])  # stable: hottest first, ties stay most-recent first

    async def _agent_listings(self, agent_id: str) -> list:
        return await self.listings.find({"agent_id": agent_id}).to_list(500)

    def _matches(self, contact: dict, req: Optional[dict], listings: list) -> list:
        by_id = {l["_id"]: l for l in listings}
        ref = by_id.get(contact.get("first_listing_id"))
        if ref:
            transaction = ref.get("transaction") or "sale"
        else:
            text = (contact.get("last_message") or contact.get("message") or "").lower()
            transaction = "rent" if re.search(r"\b(rent|rental|kiraya|kiraye)\b", text) else "sale"
        return matching.top_matches(req, listings, transaction, ref.get("property_type") if ref else None)

    def _follow_up(self, c: dict) -> dict:
        due = c.get("follow_up_due_at")
        return {"due_at": due, "overdue": bool(due and due < self.now() and c["stage"] not in summary.CLOSED)}

    async def lead_detail(self, agent_id: str, contact_id: str) -> dict:
        contact = await self.contacts.find_one({"_id": contact_id, "agent_id": agent_id})
        if not contact:
            raise TrackingError("Lead not found", 404)
        events = await self.events.find({"agent_id": agent_id, "contact_id": contact_id}).sort("ts", 1).to_list(500)
        listings = await self._agent_listings(agent_id)
        view = self._view(contact)
        req = reqmod.public(contact.get("requirement"))
        titles = {l["_id"]: l.get("title") for l in listings if l.get("title")}
        counts = summary.event_counts(events, titles)
        return {
            **view, "notes": contact.get("notes", []),
            "consent": contact.get("consent"),
            "timeline": [{"type": e["type"], "listing_id": e.get("listing_id"), "source": e.get("source"), "ts": e["ts"]}
                         for e in events],
            "requirement": req,
            "ai_summary": summary.ai_summary(req, counts, contact.get("source"), contact["stage"], view["temperature"]),
            "next_action": summary.next_action(contact, view["temperature"], req, self.now()),
            "matches": self._matches(contact, req, listings),
            "follow_up": self._follow_up(contact),
        }

    async def update_stage(self, agent_id: str, contact_id: str, u: StageUpdate) -> dict:
        contact = await self.contacts.find_one({"_id": contact_id, "agent_id": agent_id})
        if not contact:
            raise TrackingError("Lead not found", 404)
        now = self.now()
        changes = {"last_activity_at": now}
        if u.stage:
            changes["stage"] = u.stage
            if u.stage == "contacted" and (contact["stage"] != "contacted" or not contact.get("follow_up_due_at")):
                changes["contacted_at"] = now
                changes["follow_up_due_at"] = now + timedelta(days=FOLLOW_UP_DAYS)
        if u.follow_up_at is not None:
            changes["follow_up_due_at"] = u.follow_up_at
        upd = {"$set": changes}
        if u.note:
            upd["$push"] = {"notes": {"text": u.note, "ts": now, "stage": u.stage or contact["stage"]}}
        await self.contacts.update_one({"_id": contact_id, "agent_id": agent_id}, upd)
        return await self.lead_detail(agent_id, contact_id)

    async def followup_draft(self, agent_id: str, contact_id: str, body: Optional[DraftIn] = None) -> dict:
        contact = await self.contacts.find_one({"_id": contact_id, "agent_id": agent_id})
        if not contact:
            raise TrackingError("Lead not found", 404)
        listings = await self._agent_listings(agent_id)
        req = reqmod.public(contact.get("requirement"))
        first = next((l for l in listings if l["_id"] == contact.get("first_listing_id")), None)
        others = [m for m in self._matches(contact, req, listings) if m["listing_id"] != contact.get("first_listing_id")]
        draft = build_draft(contact, req, first.get("title") if first else None, others[0] if others else None,
                            (body.language if body else "en"), self.now())
        message = await polish_safely(draft, self.polish)
        return {"message": message, "whatsapp_url": whatsapp_url(contact["phone"], message),
                "language": draft["language"], "based_on": draft["based_on"]}

    async def today(self, agent_id: str) -> dict:
        from .today import build_today
        return await build_today(self, agent_id)
