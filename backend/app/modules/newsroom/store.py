"""The only file that touches Mongo for the newsroom. Collections: newsroom_items, newsroom_status, projects (the project register).
Uses only find/find_one/insert_one/update_one/count_documents with $set/$push/$in/$gte so the in-memory test fakes work too."""
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from .codec import to_doc
from .types import STATUSES, RawItem

ITEMS = "newsroom_items"
STATUS = "newsroom_status"
PROJECTS = "projects"  # one document per MahaRERA registration number in our areas (_id = the number)
DONE = ("scheduled", "published")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Store:
    def __init__(self, db, clock: Callable[[], datetime] = _utcnow):
        self.db = db
        self.items = db.get_collection(ITEMS)
        self.status = db.get_collection(STATUS)
        self.projects = db.get_collection(PROJECTS)
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

    async def update(self, id: str, **fields) -> None:
        """Set fields on an item without changing its status or history (card paths, publish bookkeeping)."""
        await self.items.update_one({"_id": id}, {"$set": {**fields, "updated_at": self.clock()}})

    async def update_raw(self, id: str, text: str) -> None:
        """Replace the stored raw text (the article reader enriches it); status and history are untouched."""
        doc = await self.items.find_one({"_id": id})
        if doc is None:
            return
        await self.items.update_one({"_id": id}, {"$set": {"raw": {**doc["raw"], "text": text}, "updated_at": self.clock()}})

    async def queue(self, limit: int = 50) -> List[dict]:
        return await self.items.find({"status": "pending_review"}).sort("updated_at", -1).limit(limit).to_list(limit)

    async def insert_item(self, doc: dict) -> bool:
        """Insert a ready-made item (the weekly digest); False when that id already exists."""
        if await self.items.find_one({"_id": doc["_id"]}):
            return False
        try:
            await self.items.insert_one(doc)
        except Exception as e:
            if "duplicate" not in f"{type(e).__name__} {e}".lower():
                raise
            return False
        return True

    async def recent_done(self, since: datetime, limit: int = 200) -> List[dict]:
        """Items approved, scheduled or published, newest first (the digest keeps those from the last week; the window is applied by the caller)."""
        return await self.items.find({"status": {"$in": ["approved", *DONE]}, "updated_at": {"$gte": since}}).sort("updated_at", -1).limit(limit).to_list(limit)

    async def public(self, limit: int = 20) -> List[dict]:
        """Items shown on the public news page: approved, scheduled or published, newest first."""
        return await self.items.find({"status": {"$in": ["approved", *DONE]}}).sort("updated_at", -1).limit(limit).to_list(limit)

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
        await self.set_mark("runner", **fields)

    async def get_run(self) -> dict:
        return await self.get_mark("runner")

    async def set_mark(self, name: str, **fields) -> None:
        """Set fields on one bookkeeping document in newsroom_status (the runner's, the area sweep's place)."""
        key = {"_id": name}
        if await self.status.find_one(key):
            await self.status.update_one(key, {"$set": fields})
            return
        try:
            await self.status.insert_one({**key, **fields})
        except Exception:  # lost a race with another writer
            await self.status.update_one(key, {"$set": fields})

    async def get_mark(self, name: str) -> dict:
        return await self.status.find_one({"_id": name}) or {}

    # --- project register -----------------------------------------------------------------------------------------------

    async def record_projects(self, records: List[dict]) -> Dict[str, int]:
        """Insert or refresh register records (from register.records) by registration number: never two documents for one
        project. `first_seen` is set once; everything else is what MahaRERA said when we last read it."""
        out = {"new": 0, "updated": 0}
        for r in records:
            key = {"_id": r["regno"]}
            if await self.projects.find_one(key) is None:
                try:
                    await self.projects.insert_one({**key, **r, "first_seen": r["checked_at"], "news": []})
                    out["new"] += 1
                    continue
                except Exception as e:  # inserted meanwhile by another run: refresh it instead
                    if "duplicate" not in f"{type(e).__name__} {e}".lower():
                        raise
            await self.projects.update_one(key, {"$set": r})
            out["updated"] += 1
        return out

    async def project(self, regno: str) -> Optional[dict]:
        return await self.projects.find_one({"_id": regno})

    async def projects_in(self, areas: List[str], limit: int = 500) -> List[dict]:
        return await self.projects.find({"locality": {"$in": list(areas)}}).to_list(limit)

    async def all_projects(self, limit: int = 20000) -> List[dict]:
        """Every register record (a few thousand at most: our areas only), for the area stats and the relabel pass."""
        return await self.projects.find({}).to_list(limit)

    async def set_project(self, regno: str, **fields) -> None:
        """Set fields on one register record (details from MahaRERA's project API, a corrected locality)."""
        await self.projects.update_one({"_id": regno}, {"$set": fields})

    async def link_news(self, regno: str, link: dict) -> bool:
        """Add a news item to a project's `news` once; False when it was already linked or the project is unknown."""
        doc = await self.projects.find_one({"_id": regno})
        if doc is None or any(n.get("item_id") == link["item_id"] for n in doc.get("news") or []):
            return False
        await self.projects.update_one({"_id": regno}, {"$push": {"news": link}})
        return True
