"""Durable intake queue for WhatsApp, Messenger and Instagram webhook payloads."""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from pymongo.errors import DuplicateKeyError

from app.core.database import get_database
from app.platform.heartbeats import heartbeat

COLLECTION = "conversation_webhook_jobs"
POLL_SECONDS = 1.0
HEARTBEAT_INTERVAL_S = 30.0
STALE_AFTER = timedelta(minutes=10)
MAX_ATTEMPTS = 3

log = logging.getLogger(__name__)


def payload_id(channel: str, payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(f"{channel}\n{body}".encode()).hexdigest()


async def enqueue(db, channel: str, payload: dict, now: Callable[[], datetime] = datetime.utcnow) -> bool:
    doc = {
        "_id": payload_id(channel, payload),
        "channel": channel,
        "payload": payload,
        "status": "queued",
        "attempts": 0,
        "created_at": now(),
    }
    try:
        await db.get_collection(COLLECTION).insert_one(doc)
        return True
    except DuplicateKeyError:
        return False


def message_count(channel: str, payload: dict) -> int:
    if channel == "whatsapp":
        return sum(
            len(((change or {}).get("value") or {}).get("messages") or [])
            for entry in payload.get("entry") or []
            for change in (entry or {}).get("changes") or []
            if (change or {}).get("field") == "messages"
        )
    return sum(
        1
        for entry in payload.get("entry") or []
        for event in (entry or {}).get("messaging") or []
        if (event or {}).get("message") or (event or {}).get("postback")
    )


async def _process_whatsapp(payload: dict, factory=None) -> None:
    from . import config, router

    service = (factory or router.build_service)(config.load())
    for entry in payload.get("entry") or []:
        for change in (entry or {}).get("changes") or []:
            if (change or {}).get("field") != "messages":
                continue
            value = change.get("value") or {}
            for status in value.get("statuses") or []:
                await service.status_update(status)
            for message in value.get("messages") or []:
                if await service.claim(message, value):
                    await service.handle(message, value)


async def _process_dm(payload: dict, factory=None) -> None:
    from . import dm_config, dm_router
    from .dms import parse, platform_of

    platform = platform_of(payload.get("object"))
    if not platform:
        return
    service = (factory or dm_router.build_service)(dm_config.load())
    for entry in payload.get("entry") or []:
        for event in (entry or {}).get("messaging") or []:
            message = parse(event or {})
            if message["kind"] == "echo":
                await service.echo(platform, message)
            elif await service.claim(platform, message):
                await service.handle(platform, message)


async def process_payload(channel: str, payload: dict, whatsapp_factory=None, dm_factory=None) -> None:
    if channel == "whatsapp":
        await _process_whatsapp(payload, whatsapp_factory)
    elif channel == "dm":
        await _process_dm(payload, dm_factory)
    else:
        raise ValueError(f"unknown webhook channel: {channel}")


async def requeue_stale(db, now: datetime) -> None:
    await db.get_collection(COLLECTION).update_many(
        {"status": "processing", "started_at": {"$lt": now - STALE_AFTER}},
        {"$set": {"status": "queued"}},
    )


async def run_once(db, whatsapp_factory=None, dm_factory=None,
                   now: Callable[[], datetime] = datetime.utcnow) -> bool:
    jobs = db.get_collection(COLLECTION)
    current = now()
    await requeue_stale(db, current)
    doc = await jobs.find_one({"status": "queued"}, sort=[("created_at", 1)])
    if not doc:
        return False
    claimed = await jobs.update_one(
        {"_id": doc["_id"], "status": "queued"},
        {"$set": {"status": "processing", "started_at": current}, "$inc": {"attempts": 1}},
    )
    if not claimed.modified_count:
        return True
    try:
        await process_payload(doc["channel"], doc["payload"], whatsapp_factory, dm_factory)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        attempts = int(doc.get("attempts") or 0) + 1
        status = "failed" if attempts >= MAX_ATTEMPTS else "queued"
        await jobs.update_one(
            {"_id": doc["_id"], "status": "processing"},
            {"$set": {"status": status, "finished_at": now(), "error": f"{type(exc).__name__}: {exc}"[:300]}},
        )
        log.exception("conversation webhook job failed")
        return True
    await jobs.update_one(
        {"_id": doc["_id"], "status": "processing"},
        {"$set": {"status": "done", "finished_at": now()}},
    )
    return True


async def loop() -> None:
    log.info("conversation webhook queue: loop started")
    while True:
        try:
            async with heartbeat("inbound_messages", get_database, every_s=HEARTBEAT_INTERVAL_S):
                worked = await run_once(get_database())
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("conversation webhook queue cycle failed")
            worked = False
        if not worked:
            await asyncio.sleep(POLL_SECONDS)
