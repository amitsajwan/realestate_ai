"""The only Mongo file of the calendar. Collections: content_calendar, calendar_status.
Uses only find/find_one/insert_one/update_one/count_documents with $set/$push so the in-memory test fakes work too."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple

from . import tags as _tags
from .config import COLLECTION, STATUS_COLLECTION

STATUSES = ("planned", "approved", "scheduled", "published", "failed", "skipped", "removed")  # removed: deleted on the platform
PUBLISHABLE = ("approved", "scheduled")   # the approval gate: nothing else is ever published
OPEN = ("planned", "approved", "scheduled")  # not yet published, failed or skipped
KINDS = ("post", "showcase", "reel")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


class Store:
    def __init__(self, db, clock: Callable[[], datetime] = _utcnow):
        self.db = db
        self.items = db.get_collection(COLLECTION)
        self.status = db.get_collection(STATUS_COLLECTION)
        self.clock = clock

    async def add(self, slug: str, channel: str, caption: str, image_path: str, due_at: datetime, *, kind: str = "post", status: str = "scheduled",
                  images: Optional[List[str]] = None, video: Optional[str] = None, creative: Optional[dict] = None, week: Optional[int] = None,
                  extra: Optional[dict] = None) -> str:
        """A row. `status` defaults to "scheduled" (publishable); the plan builder passes "planned" so that nothing posts before the owner approves."""
        now = self.clock()
        id = uuid.uuid4().hex
        imgs = list(images) if images else ([image_path] if image_path else [])
        row = {"_id": id, "slug": slug, "kind": kind, "channel": channel, "caption": caption, "image_path": imgs[0] if imgs else image_path,
               "images": imgs, "video": video, "creative": creative or {}, "week": week, "due_at": aware(due_at),
               "status": status, "external_id": None, "permalink": None, "error": None, "attempts": 0,
               "created_at": now, "updated_at": now, "history": [{"at": now, "status": status, "note": "created"}],
               **(extra or {})}
        row["tags"] = _tags.derive(row)   # every row, whoever writes it: what the post was, for comparing results later
        await self.items.insert_one(row)
        return id

    async def backfill_tags(self) -> int:
        """Put tags on rows written before tags existed (or with an older tag schema). Returns how many rows were updated."""
        n = 0
        for d in await self.all(limit=100000):
            if (d.get("tags") or {}).get("schema") == _tags.TAGS_SCHEMA:
                continue
            await self.items.update_one({"_id": d["_id"]}, {"$set": {"tags": _tags.derive(d)}})
            n += 1
        return n

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
        return [d for d in await self.all() if d["status"] in OPEN][:limit]

    async def due(self, now: datetime) -> List[dict]:
        """Approved (or scheduled) rows whose time has come, oldest first. Planned rows are never due."""
        return [d for d in await self.all() if d["status"] in PUBLISHABLE and aware(d["due_at"]) <= now]

    async def reels_to_render(self, now: datetime, lead: timedelta) -> List[dict]:
        """Approved reel rows due within `lead` that have no video yet."""
        return [d for d in await self.all() if d["status"] in PUBLISHABLE and d.get("kind") == "reel" and not d.get("video")
                and aware(d["due_at"]) <= now + lead]

    async def set_video(self, id: str, video: str, info: Optional[dict] = None) -> None:
        """`info` = {duration_s, render} of the rendered file, kept in the row's tags. A post (carousel) that gets a video is going
        out as a Reel of its slides: its tags say so (published_as)."""
        doc = await self.get(id) or {}
        tags = dict(doc.get("tags") or (_tags.derive(doc) if doc else {}))
        tags.update(info or {})
        if doc.get("kind") == "post":
            tags["published_as"] = "reel"
        await self.items.update_one({"_id": id}, {"$set": {"video": video, "tags": tags, "updated_at": self.clock()}})

    async def set_planned(self, id: str, caption: Optional[str] = None, images: Optional[List[str]] = None) -> bool:
        """Change a row's caption or images while it is still planned (an agent edited the post before approval);
        False for any other status: an approved or published row is never changed behind the owner's back."""
        doc = await self.get(id)
        if not doc or doc["status"] != "planned":
            return False
        fields: Dict = {"updated_at": self.clock()}
        if caption is not None:
            fields["caption"] = caption
        if images:
            fields.update(images=list(images), image_path=images[0])
        await self.items.update_one({"_id": id, "status": "planned"}, {"$set": fields})
        return True

    async def approve(self, id: str, due_at: Optional[datetime] = None) -> bool:
        """Approve a planned row; `due_at` moves it (the testing pace), else it keeps its planned time."""
        doc = await self.get(id)
        if not doc or doc["status"] != "planned":
            return False
        await self._move(id, "approved", "approved by owner" + (" (testing pace)" if due_at else ""), **({"due_at": due_at} if due_at else {}))
        return True

    async def next_slot(self, channel: str, after: datetime, gap: timedelta, exclude: Optional[str] = None) -> datetime:
        """The first time at or after `after` that is at least `gap` from every post going out (or just out) on the channel."""
        taken = sorted(aware(d.get("published_at") if d["status"] == "published" and isinstance(d.get("published_at"), datetime) else d["due_at"])
                       for d in await self.all()
                       if d["channel"] == channel and d["_id"] != exclude and d["status"] in ("approved", "scheduled", "published"))
        at = aware(after)
        for t in taken:
            if abs((t - at).total_seconds()) < gap.total_seconds():
                at = t + gap
        return at

    async def recent(self, since: datetime, statuses=("published", "failed", "removed")) -> List[dict]:
        """Rows that finished since `since` (posted with their link, failed with the reason, removed), newest first."""
        rows = [d for d in await self.all() if d["status"] in statuses and aware(d.get("updated_at") or d["due_at"]) >= aware(since)]
        return sorted(rows, key=lambda d: aware(d.get("published_at") or d.get("updated_at") or d["due_at"]), reverse=True)

    async def post_now(self, id: str, gap: Optional[timedelta] = None) -> Optional[dict]:
        """The owner's "Post now": approve it if needed and make it due at once, or, when another post on the channel goes out
        within `gap`, right after it (so many Post now taps queue a few minutes apart). None when it is already published,
        failed, skipped or removed."""
        doc = await self.get(id)
        if not doc or doc["status"] not in OPEN:
            return None
        now = self.clock()
        at = await self.next_slot(doc["channel"], now, gap, exclude=id) if gap else now
        await self._move(id, "approved", "post now by owner", due_at=at)
        return {**doc, "status": "approved", "due_at": at}

    async def retry(self, id: str, due_at: datetime) -> bool:
        """A failed row goes back in the queue (the owner's Retry): approved, due at `due_at`, attempts reset."""
        doc = await self.get(id)
        if not doc or doc["status"] != "failed":
            return False
        await self._move(id, "approved", "retry by owner", due_at=due_at, attempts=0, error=None, last_attempt_at=None)
        return True

    async def unapprove(self, id: str) -> bool:
        """An approved row back to "planned" (the owner changed their mind before it went out)."""
        doc = await self.get(id)
        if not doc or doc["status"] not in ("approved", "scheduled"):
            return False
        await self._move(id, "planned", "moved back to To approve by owner")
        return True

    async def mark_removed(self, id: str, note: str) -> None:
        """A published post that no longer exists on the platform (deleted there): out of Studio and the public feed."""
        await self._move(id, "removed", note, removed_at=self.clock())

    async def checked_live(self, id: str, gone: Optional[datetime] = None, clear: bool = False) -> None:
        """Record a live check: `gone` when the platform said it is not there (the first sighting), `clear` when it is there."""
        fields = {"live_checked_at": self.clock()}
        if gone is not None:
            fields["live_gone_at"] = gone
        elif clear:
            fields["live_gone_at"] = None
        await self.items.update_one({"_id": id}, {"$set": fields})

    async def _move(self, id: str, status: str, note: str, **fields) -> None:
        now = self.clock()
        await self.items.update_one({"_id": id}, {"$set": {**fields, "status": status, "updated_at": now},
                                                  "$push": {"history": {"at": now, "status": status, "note": note}}})

    async def published(self, id: str, external_id: str, permalink: Optional[str], note: str = "") -> None:
        await self._move(id, "published", note or "published", external_id=external_id, permalink=permalink, error=None, published_at=self.clock())

    async def attempt_failed(self, id: str, reason: str, attempts: int, final: bool) -> None:
        """Record a failed try. Not final: the row keeps its approved status and is retried after a pause."""
        doc = await self.get(id)
        keep = doc["status"] if doc and doc["status"] in PUBLISHABLE else "approved"
        await self._move(id, "failed" if final else keep, f"attempt {attempts} failed: {reason}", error=reason, attempts=attempts,
                         last_attempt_at=self.clock())

    async def skip(self, id: str, note: str = "skipped by owner") -> bool:
        doc = await self.get(id)
        if not doc or doc["status"] not in OPEN:
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
