"""Phone OTP issue/verify. Codes are stored HMAC-hashed with expiry, attempt and rate limits."""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Callable, Protocol

logger = logging.getLogger(__name__)

CODE_TTL = timedelta(minutes=5)
RESEND_COOLDOWN = timedelta(seconds=30)
MAX_PER_HOUR = 5
MAX_ATTEMPTS = 5


class OTPError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class OTPProvider(Protocol):
    async def send(self, phone: str, code: str) -> None: ...


class ConsoleOTPProvider:
    """Development provider: logs the code instead of sending it."""

    async def send(self, phone: str, code: str) -> None:
        logger.warning("DEV OTP for %s is %s", phone, code)


class OTPService:
    def __init__(self, db, provider: OTPProvider, secret: str,
                 now: Callable[[], datetime] = datetime.utcnow):
        self.col = db.get_collection("otp_codes")
        self.provider = provider
        self.secret = secret.encode()
        self.now = now

    def _hash(self, phone: str, code: str) -> str:
        return hmac.new(self.secret, f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()

    async def request(self, phone: str) -> str:
        """Create and send a code. Returns the code (callers only expose it in development)."""
        now = self.now()
        latest = await self.col.find_one({"phone": phone}, sort=[("created_at", -1)])
        if latest and now - latest["created_at"] < RESEND_COOLDOWN:
            raise OTPError("Please wait a few seconds before requesting another code", 429)
        recent = await self.col.count_documents(
            {"phone": phone, "created_at": {"$gte": now - timedelta(hours=1)}})
        if recent >= MAX_PER_HOUR:
            raise OTPError("Too many codes requested. Try again later", 429)
        code = f"{secrets.randbelow(10**6):06d}"
        await self.col.insert_one({
            "phone": phone, "code_hash": self._hash(phone, code), "created_at": now,
            "expires_at": now + CODE_TTL, "attempts": 0, "used": False,
        })
        await self.provider.send(phone, code)
        return code

    async def verify(self, phone: str, code: str) -> None:
        now = self.now()
        doc = await self.col.find_one({"phone": phone, "used": False}, sort=[("created_at", -1)])
        if not doc or doc["expires_at"] < now:
            raise OTPError("Code expired or not requested. Request a new one")
        if doc["attempts"] >= MAX_ATTEMPTS:
            raise OTPError("Too many wrong attempts. Request a new code", 429)
        if not hmac.compare_digest(doc["code_hash"], self._hash(phone, code.strip())):
            await self.col.update_one({"_id": doc["_id"]}, {"$inc": {"attempts": 1}})
            raise OTPError("Incorrect code")
        await self.col.update_one({"_id": doc["_id"]}, {"$set": {"used": True}})
