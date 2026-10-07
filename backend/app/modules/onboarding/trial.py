"""Claim your free trial: an agent sends TRIAL to our WhatsApp number and gets his sign-up code at once, with no person in between.

The WhatsApp message is the proof that he owns the number (WhatsApp verified it), so the code is bound to that number exactly as a
hand-issued invite is (invites.InviteService): the join flow is unchanged (phone, then code). The offer: his first TRIAL_PROPERTIES
properties marketed free, no card; it is recorded on his invite (`plan`, `trial_properties`), not enforced yet.

Limits: at most TRIAL_DAILY_CAP new trials a day (IST); over it, the claim is kept as an invite request for the owner and the
agent is told plainly. A number that claimed in the last REISSUE_AFTER is not sent a new code (the last one still works).
A revoked invite is never re-opened by a claim.
"""
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional

from .invites import InviteService

TRIAL_PROPERTIES = 3
DEFAULT_DAILY_CAP = 20
REISSUE_AFTER = timedelta(hours=1)
IST = timedelta(hours=5, minutes=30)
LABEL = "trial"


def daily_cap() -> int:
    try:
        return max(0, int(os.environ.get("TRIAL_DAILY_CAP") or DEFAULT_DAILY_CAP))
    except ValueError:
        return DEFAULT_DAILY_CAP


def enabled() -> bool:
    return (os.environ.get("TRIAL_CLAIMS") or "on").strip().lower() not in ("0", "false", "no", "off")


@dataclass
class Claim:
    status: str                  # issued | reissued | too_soon | full | blocked
    code: Optional[str] = None   # only for issued / reissued: shown to the agent once, never stored in plain text


class TrialService:
    def __init__(self, db, invites: InviteService, now: Callable[[], datetime] = datetime.utcnow, cap: Optional[int] = None):
        self.db, self.invites, self.now = db, invites, now
        self.col = db.get_collection("invites")
        self.cap = daily_cap() if cap is None else cap

    def _day_start(self, now: datetime) -> datetime:
        """Midnight IST, as a naive UTC time like the stored timestamps."""
        local = now + IST
        return datetime(local.year, local.month, local.day) - IST

    async def claim(self, phone: str, source: str = "whatsapp") -> Claim:
        now = self.now()
        inv = await self.col.find_one({"_id": phone})
        if inv and inv.get("revoked"):
            return Claim("blocked")
        if inv:
            if inv.get("issued_at") and now - inv["issued_at"] < REISSUE_AFTER:
                return Claim("too_soon")
            code = await self.invites.issue(phone, inv.get("label") or LABEL)   # a lost code: a fresh one, the same account
            return Claim("reissued", code)
        today = await self.col.count_documents({"label": LABEL, "created_at": {"$gte": self._day_start(now)}})
        if today >= self.cap:
            await self._queue(phone, source, now)
            return Claim("full")
        code = await self.invites.issue(phone, LABEL)
        await self.col.update_one({"_id": phone}, {"$set": {"plan": "trial", "trial_properties": TRIAL_PROPERTIES, "claimed_via": source,
                                                            "claimed_at": now}})
        return Claim("issued", code)

    async def _queue(self, phone: str, source: str, now: datetime) -> None:
        """Over today's cap: the claim waits in the owner's invite requests (scripts/invite_requests.py), once per number."""
        reqs = self.db.get_collection("invite_requests")
        if await reqs.find_one({"phone": phone, "status": "new"}):
            return
        await reqs.insert_one({"name": "", "phone": phone, "city": "", "message": "Claimed the free trial on WhatsApp (daily cap reached)",
                               "source": f"trial-{source}", "consent": {"given_at": now, "text": "Sent TRIAL to us on WhatsApp"},
                               "ip_hash": None, "status": "new", "created_at": now, "updated_at": now})
