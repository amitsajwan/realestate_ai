"""Abuse protection for POST /t/inquiry (contract: docs/contracts/activity.md section 3).

Every accepted attempt is written to the small `inquiry_log` collection ({agent_id, phone, anon_id, ts}); the limits
count log rows inside a rolling hour. A row older than WINDOW no longer counts (a row exactly WINDOW old is expired).
Rejected attempts are not logged, so a blocked visitor is free again one hour after their last accepted attempt."""
from datetime import timedelta

WINDOW = timedelta(hours=1)
MAX_PER_PHONE = 3   # per (agent, phone) per rolling hour
MAX_PER_ANON = 5    # per anonymous visitor per rolling hour
TOO_MANY = "Too many messages. Please try again later"


def is_honeypot(website) -> bool:
    """The hidden `website` input real visitors never fill: any non-blank value means a bot."""
    return bool((website or "").strip())


async def over_limit(log, agent_id: str, phone: str, anon_id: str, now) -> bool:
    since = now - WINDOW
    if await log.count_documents({"agent_id": agent_id, "phone": phone, "ts": {"$gt": since}}) >= MAX_PER_PHONE:
        return True
    return await log.count_documents({"anon_id": anon_id, "ts": {"$gt": since}}) >= MAX_PER_ANON


async def record_attempt(log, agent_id: str, phone: str, anon_id: str, now) -> None:
    await log.insert_one({"agent_id": agent_id, "phone": phone, "anon_id": anon_id, "ts": now})
