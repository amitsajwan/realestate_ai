"""The only file that touches Mongo for the newsroom. Collections: newsroom_items, newsroom_status.
Uses only find/find_one/insert_one/update_one/count_documents with $set/$push/$in/$gte so the in-memory test fakes work too."""
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from .codec import to_doc
from .types import STATUSES, RawItem

ITEMS = "newsroom_items"
STATUS = "newsroom_status"
DONE = ("scheduled", "published")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Store:
    def __init__(self, db, clock: Callable[[], datetime] = _utcnow):
        self.items = db.get_collection(ITEMS)
        self.status = db.get_collection(STATUS)
        self.clock = clock

    async def add_new(self, items: List[RawItem]) -> int:
        """Insert items whose id is not stored yet; returns how many were new."""
        added = 0
        for it in items:
            if await self.items.find_one({"_id": it.id}):
                continue
            now = self.clock()
            try:
                await self.items.insert_one({"_id": it.id, "status": "new", "raw": to_doc(it), "created_at": now, "updated_at": now,
                                             "history": [{"at": now, "status": "new", "note": ""}]})
            except Exception as e:  # a concurrent insert of the same id (DuplicateKeyError): treat as already present
                if "duplicate" not in f"{type(e).__name__} {e}".lower():
                    raise
                continue
            added += 1
        return added

    async def get(self, id: str) -> Optional[dict]:
        return await self.items.find_one({"_id": id})

    async def next_batch(self, status: str, limit: int) -> List[dict]:
        return await self.items.find({"status": status}).sort("created_at", 1).limit(limit).to_list(limit)

    async def move(self, id: str, status: str, note: str = "", **fields) -> None:
        now = self.clock()
        await self.items.update_one({"_id": id}, {"$set": {**fields, "status": status, "updated_at": now},
                                                  "$push": {"history": {"at": now, "status": status, "note": note}}})

    async def queue(self, limit: int = 50) -> List[dict]:
        return await self.items.find({"status": "pending_review"}).sort("updated_at", -1).limit(limit).to_list(limit)

    async def counts(self) -> Dict[str, int]:
        return {s: await self.items.count_documents({"status": s}) for s in STATUSES}

    async def published_since(self, since: datetime) -> int:
        """Items scheduled or published at or after `since` (for the daily cap)."""
        return await self.items.count_documents({"status": {"$in": list(DONE)}, "published_at": {"$gte": since}})

    async def live_titles(self, exclude_id: str, limit: int = 300) -> list:
        """Titles of items still in play (not dropped, rejected or failed), for spotting the same story from another publisher."""
        docs = await self.items.find({"status": {"$nin": ["dropped", "rejected", "failed"]}}).to_list(limit)
        return [(d.get("raw") or {}).get("title", "") for d in docs if d["_id"] != exclude_id]

    async def set_run(self, **fields) -> None:
        """Runner bookkeeping (last_run_at, last_error, ...); a single document."""
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
