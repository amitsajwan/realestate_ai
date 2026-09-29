"""Listing lifecycle + reads. Owner scoping: every agent-side read/write filters by agent_id and
returns 404 (never 403) for other agents' listings."""
import re
import uuid
from datetime import datetime
from typing import Callable, List, Optional

from .schemas import (PUBLIC_STATUSES, PUBLIC_VISIBILITIES, Listing, ListingCreate, ListingUpdate,
                      PublicAgent, PublicListing)

# from -> allowed targets via POST /{id}/status. draft -> live goes through publish (validation).
TRANSITIONS = {
    "draft": set(),
    "live": {"under_offer", "sold", "rented", "paused", "expired"},
    "under_offer": {"live", "sold", "rented", "paused", "expired"},
    "paused": {"live", "expired"},
    "expired": {"live"},
    "sold": set(),
    "rented": set(),
}
FINGERPRINT_FIELDS = ("city", "locality", "project_name", "bhk", "carpet_sqft", "transaction")
CARPET_BUCKET = 50


class ListingError(Exception):
    def __init__(self, message: str, status_code: int = 400, detail=None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail if detail is not None else message


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def compute_fingerprint(doc: dict) -> str:
    """city|locality|project|bhk|carpet bucket|transaction, normalised, for duplicate detection."""
    bhk = doc.get("bhk")
    carpet = doc.get("carpet_sqft")
    return "|".join([
        _norm(doc.get("city")), _norm(doc.get("locality")), _norm(doc.get("project_name")),
        f"{float(bhk):g}" if bhk is not None else "",
        str(int(round(carpet / CARPET_BUCKET)) * CARPET_BUCKET) if carpet else "",
        _norm(doc.get("transaction")),
    ])


def missing_for_publish(doc: dict) -> List[str]:
    missing = [f for f in ("title", "transaction", "property_type", "price_inr", "city", "locality") if not doc.get(f)]
    if not any(m.get("kind") == "image" for m in doc.get("media") or []):
        missing.append("media")
    if not ((doc.get("description") or {}).get("en") or "").strip():
        missing.append("description.en")
    return missing


class ListingService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow):
        self.listings = db.get_collection("listings")
        self.profiles = db.get_collection("agent_public_profiles")
        self.now = now

    async def _mine(self, agent_id: str, listing_id: str) -> dict:
        doc = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise ListingError("Listing not found", 404)
        return doc

    @staticmethod
    def _out(doc: dict) -> Listing:
        return Listing.model_validate({**doc, "id": doc["_id"]})

    # ---- agent side -------------------------------------------------------------------------
    async def create(self, agent_id: str, body: ListingCreate) -> Listing:
        now = self.now()
        lid = uuid.uuid4().hex
        doc = {**body.model_dump(), "_id": lid, "id": lid, "agent_id": agent_id, "status": "draft",
               "created_at": now, "updated_at": now, "published_at": None, "freshness_confirmed_at": None}
        await self.listings.insert_one(doc)
        return self._out(doc)

    async def list_mine(self, agent_id: str, status: Optional[str] = None, limit: int = 50) -> List[Listing]:
        flt = {"agent_id": agent_id}
        if status:
            flt["status"] = status
        docs = await self.listings.find(flt).sort("created_at", -1).limit(limit).to_list(limit)
        return [self._out(d) for d in docs]

    async def get_mine(self, agent_id: str, listing_id: str) -> Listing:
        return self._out(await self._mine(agent_id, listing_id))

    async def patch(self, agent_id: str, listing_id: str, body: ListingUpdate) -> Listing:
        doc = await self._mine(agent_id, listing_id)
        changes = body.model_dump(exclude_unset=True)
        merged = {**doc, **changes}
        if doc["status"] != "draft" and (changes.keys() & set(FINGERPRINT_FIELDS)):
            changes["fingerprint"] = compute_fingerprint(merged)
        changes["updated_at"] = self.now()
        await self.listings.update_one({"_id": listing_id, "agent_id": agent_id}, {"$set": changes})
        return self._out({**doc, **changes})

    async def publish(self, agent_id: str, listing_id: str) -> Listing:
        doc = await self._mine(agent_id, listing_id)
        if doc["status"] != "draft":
            raise ListingError(f"Only draft listings can be published (status is {doc['status']})", 409)
        missing = missing_for_publish(doc)
        if missing:
            raise ListingError("Missing required fields to publish", 422,
                               {"message": "Missing required fields to publish", "missing": missing})
        now = self.now()
        changes = {"status": "live", "published_at": now, "freshness_confirmed_at": now,
                   "updated_at": now, "fingerprint": compute_fingerprint(doc)}
        await self.listings.update_one({"_id": listing_id, "agent_id": agent_id}, {"$set": changes})
        return self._out({**doc, **changes})

    async def change_status(self, agent_id: str, listing_id: str, target: str) -> Listing:
        doc = await self._mine(agent_id, listing_id)
        current = doc["status"]
        if current == "draft" and target == "live":
            raise ListingError("Use publish to make a draft live", 409)
        if target not in TRANSITIONS[current]:
            raise ListingError(f"Cannot change status from {current} to {target}", 409)
        now = self.now()
        changes = {"status": target, "updated_at": now}
        if target == "live" and current in ("paused", "expired"):
            changes["freshness_confirmed_at"] = now  # re-activating confirms the listing is still available
        await self.listings.update_one({"_id": listing_id, "agent_id": agent_id}, {"$set": changes})
        return self._out({**doc, **changes})

    # ---- public side ------------------------------------------------------------------------
    @staticmethod
    def _agent(profile: dict) -> PublicAgent:
        return PublicAgent(slug=profile["slug"], agent_name=profile.get("agent_name"),
                           phone=profile.get("phone"), photo=profile.get("photo"))

    @staticmethod
    def _public_flt(**extra) -> dict:
        return {"status": {"$in": list(PUBLIC_STATUSES)}, "visibility": {"$in": list(PUBLIC_VISIBILITIES)}, **extra}

    async def public_list(self, slug: str, limit: int = 20, offset: int = 0):
        profile = await self.profiles.find_one({"slug": slug, "is_public": True})
        if not profile:
            raise ListingError("Agent site not found", 404)
        flt = self._public_flt(agent_id=profile["agent_id"])
        total = await self.listings.count_documents(flt)
        docs = await self.listings.find(flt).sort("published_at", -1).skip(offset).limit(limit).to_list(limit)
        agent = self._agent(profile)
        items = [PublicListing.model_validate({**d, "id": d["_id"], "agent": agent}) for d in docs]
        return items, total

    async def public_get(self, listing_id: str) -> PublicListing:
        doc = await self.listings.find_one(self._public_flt(_id=listing_id))
        profile = await self.profiles.find_one({"agent_id": doc["agent_id"], "is_public": True}) if doc else None
        if not doc or not profile:
            raise ListingError("Listing not found", 404)
        return PublicListing.model_validate({**doc, "id": doc["_id"], "agent": self._agent(profile)})
