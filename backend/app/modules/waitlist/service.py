"""Invite requests: a public form feeds a queue the owner works through by hand.

Abuse controls: honeypot (dropped silently, nothing stored), per-phone and per-client-ip hourly limits.
The client ip is only ever stored as a salted hash.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from .schemas import CONSENT_TEXT, InviteRequestIn

COLLECTION = "invite_requests"
ATTEMPTS = "invite_request_attempts"  # rolling-window log for rate limits (a repeat request updates a row, so rows alone can't count)
MAX_PER_PHONE_PER_HOUR = 3
MAX_PER_IP_PER_HOUR = 20
DEDUPE_WINDOW = timedelta(hours=24)
HOUR = timedelta(hours=1)


class RateLimited(Exception):
    """Too many requests from this phone or client ip."""


def hash_ip(ip: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()


def client_ip(forwarded_for: Optional[str], peer: Optional[str]) -> Optional[str]:
    """First hop of X-Forwarded-For (the server sits behind a proxy), else the socket peer."""
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return peer or None


class WaitlistService:
    def __init__(self, db, salt: str, now: Callable[[], datetime] = datetime.utcnow):
        self.col = db.get_collection(COLLECTION)
        self.attempts = db.get_collection(ATTEMPTS)
        self.salt = salt
        self.now = now

    async def submit(self, data: InviteRequestIn, ip: Optional[str]) -> bool:
        """Store or update the request. The caller answers the same for accepted, duplicate and honeypot alike (no information
        leak); the return value only says whether a new request now waits for the owner (False for a repeat or the honeypot)."""
        if data.website:  # honeypot hit: pretend success, keep nothing
            return False
        now = self.now()
        ip_hash = hash_ip(ip, self.salt) if ip else None
        since = now - HOUR
        if await self.attempts.count_documents({"phone": data.phone, "at": {"$gte": since}}) >= MAX_PER_PHONE_PER_HOUR:
            raise RateLimited("Too many requests")
        if ip_hash and await self.attempts.count_documents({"ip_hash": ip_hash, "at": {"$gte": since}}) >= MAX_PER_IP_PER_HOUR:
            raise RateLimited("Too many requests")
        await self.attempts.insert_one({"phone": data.phone, "ip_hash": ip_hash, "at": now})

        # only a request still waiting is merged: one the owner already invited or dismissed must not swallow a new one
        existing = await self.col.find_one({"phone": data.phone, "status": "new", "created_at": {"$gte": now - DEDUPE_WINDOW}},
                                           sort=[("created_at", -1)])
        if existing:
            await self.col.update_one({"_id": existing["_id"]}, {"$set": {
                "name": data.name, "city": data.city, "message": data.message, "updated_at": now}})
            return False
        await self.col.insert_one({
            "name": data.name, "phone": data.phone, "city": data.city, "message": data.message, "source": data.source,
            "consent": {"given_at": now, "text": CONSENT_TEXT},
            "ip_hash": ip_hash, "status": "new", "created_at": now, "updated_at": now,
        })
        return True

    # -- admin (scripts/invite_requests.py) --------------------------------------------------------------
    async def list_new(self) -> List[dict]:
        """New requests, oldest first."""
        return await self.col.find({"status": "new"}).sort("created_at", 1).to_list(length=None)

    async def mark_invited(self, phone: str) -> bool:
        if not await self.col.find_one({"phone": phone, "status": "new"}):
            return False
        await self.col.update_many({"phone": phone, "status": "new"},
                                   {"$set": {"status": "invited", "updated_at": self.now()}})
        return True
