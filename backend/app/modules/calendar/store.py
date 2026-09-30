"""The only Mongo file of the calendar. Collections: content_calendar, calendar_status.
Uses only find/find_one/insert_one/update_one/count_documents with $set/$push so the in-memory test fakes work too."""
import uuid
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from .config import COLLECTION, STATUS_COLLECTION

STATUSES = ("scheduled", "published", "failed", "skipped")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


class Store:
    def __init__(self, db, clock: Callable[[], datetime] = _utcnow):
        self.items = db.get_collection(COLLECTION)
        self.status = db.get_collection(STATUS_COLLECTION)
        self.clock = clock

    async def add(self, slug: str, channel: str, caption: str, image_path: str, due_at: datetime) -> str:
        now = self.clock()
        id = uuid.uuid4().hex
        await self.items.insert_one({"_id": id, "slug": slug, "channel": channel, "caption": caption, "image_path": image_path, "due_at": aware(due_at),
                                     "status": "scheduled", "external_id": None, "permalink": None, "error": None, "attempts": 0,
                                     "created_at": now, "updated_at": now, "history": [{"at": now, "status": "scheduled", "note": "seeded"}]})
        return id

    async def get(self, id: str) -> Optional[dict]:
        return await self.items.find_one({"_id": id})

    async def all(self, limit: int = 2000) -> List[dict]:
        return await self.items.find({}).sort("due_at", 1).limit(limit).to_list(limit)

    async def existing(self) -> List[Tuple[str, str, datetime]]:
        """(channel, slug, due_at) of every row: scheduled, published, failed and skipped all count as used."""
        return [(d["channel"], d["slug"], aware(d["due_at"])) for d in await self.all()]

    async def listing(self, status: Optional[str] = None, limit: int = 200) -> List[dict]:
        return [d for d in await self.all() if status is None or d["status"] == status][:limit]

    async def upcoming(self, limit: int = 50) -> List[dict]:
        return [d for d in await self.all() if d["status"] == "scheduled"][:limit]

    async def due(self, now: datetime) -> List[dict]:
        """Scheduled rows whose time has come, oldest first."""
        return [d for d in await self.all() if d["status"] == "scheduled" and aware(d["due_at"]) <= now]

    async def _move(self, id: str, status: str, note: str, **fields) -> None:
        now = self.clock()
        await self.items.update_one({"_id": id}, {"$set": {**fields, "status": status, "updated_at": now},
                                                  "$push": {"history": {"at": now, "status": status, "note": note}}})

    async def published(self, id: str, external_id: str, permalink: Optional[str], note: str = "") -> None:
        await self._move(id, "published", note or "published", external_id=external_id, permalink=permalink, error=None, published_at=self.clock())

    async def attempt_failed(self, id: str, reason: str, attempts: int, final: bool) -> None:
        """Record a failed try. Not final: the row stays scheduled and is retried after a pause."""
        await self._move(id, "failed" if final else "scheduled", f"attempt {attempts} failed: {reason}", error=reason, attempts=attempts,
                         last_attempt_at=self.clock())

    async def skip(self, id: str, note: str = "skipped by owner") -> bool:
        doc = await self.get(id)
        if not doc or doc["status"] != "scheduled":
            return False
        await self._move(id, "skipped", note)
        return True

    async def counts(self) -> Dict[str, int]:
        return {s: await self.items.count_documents({"status": s}) for s in STATUSES}

    async def set_run(self, **fields) -> None:
        key = {"_id": "runner"}
        if await self.status.find_one(key):
            await self.status.update_one(key, {"$set": fields})
            return
        try:
            await self.status.insert_one({**key, **fields})
        except Exception:  # lost a race with another writer
            await self.status.update_one(key, {"$set": fields})

    async def get_run(self) -> dict:
        return await self.status.find_one({"_id": "runner"}) or {}
