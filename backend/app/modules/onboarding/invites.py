"""Pilot access: each invited agent gets a personal 6-digit code bound to their phone number.

Drop-in for OTPService (same request/verify interface) so the join flow is identical for the agent:
enter phone, enter the code you were sent on WhatsApp. Codes are stored HMAC-hashed, reusable until
revoked, and brute force is bounded (lockout after 5 wrong attempts, hard stop after 15 until re-issued).

An invited number signed out on a new phone should not have to ask us for its code, so with `send_code` it also gets a
one-time code on WhatsApp each time it asks. The invite still decides who may sign in, and the personal code stays good
in case WhatsApp does not deliver.
"""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Optional

from .otp import OTPError, OTPService

log = logging.getLogger(__name__)

LOCK_AFTER = 5
LOCK_FOR = timedelta(minutes=30)
HARD_STOP_AFTER = 15
NOT_INVITED = "This number has no free trial yet. Claim yours at avasetu.in/trial and we will send your sign-up code on WhatsApp."


class _CodeSender:
    def __init__(self, send: Callable[[str, str], Awaitable[None]]):
        self.send = send


class InviteService:
    def __init__(self, db, secret: str, now: Callable[[], datetime] = datetime.utcnow,
                 send_code: Optional[Callable[[str, str], Awaitable[None]]] = None):
        self.col = db.get_collection("invites")
        self.secret = secret.encode()
        self.now = now
        self.one_time = OTPService(db, _CodeSender(send_code), secret, now) if send_code else None

    def _hash(self, phone: str, code: str) -> str:
        return hmac.new(self.secret, f"invite:{phone}:{code}".encode(), hashlib.sha256).hexdigest()

    # ---- admin side (scripts/invite.py) ----
    async def issue(self, phone: str, label: str = "") -> str:
        """Create or re-issue the phone's code (resets lockouts). Returns the plaintext code once."""
        code = f"{secrets.randbelow(10**6):06d}"
        now = self.now()
        doc = {"_id": phone, "phone": phone, "code_hash": self._hash(phone, code), "label": label,
               "revoked": False, "fail_count": 0, "total_fails": 0, "locked_until": None, "issued_at": now}
        if await self.col.find_one({"_id": phone}):
            await self.col.update_one({"_id": phone}, {"$set": {k: v for k, v in doc.items() if k != "_id"}})
        else:
            await self.col.insert_one({**doc, "created_at": now})
        return code

    async def revoke(self, phone: str) -> bool:
        if not await self.col.find_one({"_id": phone}):
            return False
        await self.col.update_one({"_id": phone}, {"$set": {"revoked": True}})
        return True

    # ---- agent side (same interface as OTPService) ----
    async def request(self, phone: str) -> Optional[str]:
        inv = await self.col.find_one({"_id": phone})
        if not inv or inv.get("revoked"):
            raise OTPError(NOT_INVITED, 403)
        if not self.one_time:
            return None  # nothing to send: the code was handed to the agent personally
        try:
            return await self.one_time.request(phone)
        except OTPError:
            raise
        except Exception:  # WhatsApp is down or refused: the personal code still signs in
            log.exception("invites: could not send a login code on WhatsApp")
            return None

    async def verify(self, phone: str, code: str) -> None:
        now = self.now()
        inv = await self.col.find_one({"_id": phone})
        if not inv or inv.get("revoked"):
            raise OTPError(NOT_INVITED, 403)
        if inv["total_fails"] >= HARD_STOP_AFTER:
            raise OTPError("This invite is locked. Ask us to send you a new code", 429)
        if inv.get("locked_until") and inv["locked_until"] > now:
            raise OTPError("Too many wrong attempts. Try again in a while", 429)
        if not await self._code_matches(inv, phone, code):
            fails = inv["fail_count"] + 1
            upd = {"fail_count": fails, "total_fails": inv["total_fails"] + 1}
            if fails >= LOCK_AFTER:
                upd.update(fail_count=0, locked_until=now + LOCK_FOR)
            await self.col.update_one({"_id": phone}, {"$set": upd})
            raise OTPError("Incorrect code")
        await self.col.update_one({"_id": phone}, {"$set": {"fail_count": 0, "total_fails": 0, "locked_until": None,
                                                            "last_login_at": now}})

    async def _code_matches(self, inv: dict, phone: str, code: str) -> bool:
        if hmac.compare_digest(inv["code_hash"], self._hash(phone, code.strip())):
            return True
        if not self.one_time:
            return False
        try:
            await self.one_time.verify(phone, code)
            return True
        except OTPError:
            return False
