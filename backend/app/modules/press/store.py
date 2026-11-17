"""The only file that touches Mongo for press. Collections: `press_stories` (one a month, `_id` the month "YYYY-MM") and
`press_pitches` (one a journalist pitched that month)."""
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

STORIES = "press_stories"
PITCHES = "press_pitches"


class Store:
    def __init__(self, db):
        self.db = db
        self.stories = db.get_collection(STORIES)
        self.pitches = db.get_collection(PITCHES)

    async def save_story(self, month: str, facts: List[dict], headline_facts: List[dict], now: datetime) -> dict:
        doc = {"_id": month, "month": month, "facts": facts, "headline_facts": headline_facts, "created_at": now}
        if await self.stories.find_one({"_id": month}):
            await self.stories.update_one({"_id": month}, {"$set": doc})
        else:
            await self.stories.insert_one(doc)
        return doc

    async def story(self, month: str) -> Optional[dict]:
        return await self.stories.find_one({"_id": month})

    async def latest_story(self) -> Optional[dict]:
        docs = await self.stories.find({}).to_list(2000)
        return max(docs, key=lambda d: d.get("month", ""), default=None)

    async def save_pitch(self, month: str, journalist: dict, draft: dict, now: datetime) -> dict:
        """One pitch, keyed so the same journalist (by article URL) is not pitched twice in a month. The id is a hash,
        not the URL itself, so it is a plain path segment in the Studio API."""
        raw = f"{month}|{journalist.get('url') or journalist.get('outlet')}"
        key = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        existing = await self.pitches.find_one({"_id": key})
        if existing:
            return existing
        doc = {"_id": key, "month": month, "journalist": {k: journalist.get(k) for k in
               ("name", "outlet", "email", "contact_page")}, "article": {k: journalist.get(k) for k in ("title", "url", "date")},
               "email": journalist.get("email"), "subject": draft["subject"], "body": draft["body"],
               "origin": draft.get("origin", "template"), "status": "draft", "replied": False, "link_won_url": None,
               "created_at": now}
        await self.pitches.insert_one(doc)
        return doc

    async def pitches_for(self, month: Optional[str] = None) -> List[dict]:
        flt = {"month": month} if month else {}
        docs = await self.pitches.find(flt).to_list(5000)
        docs.sort(key=lambda d: d.get("created_at") or datetime.min, reverse=True)
        return docs

    async def pitch(self, pitch_id: str) -> Optional[dict]:
        return await self.pitches.find_one({"_id": pitch_id})

    async def update_pitch(self, pitch_id: str, **fields) -> Optional[dict]:
        await self.pitches.update_one({"_id": pitch_id}, {"$set": fields})
        return await self.pitch(pitch_id)

    async def summary(self) -> Dict[str, int]:
        """All-time counts for the Studio screen: sent, replies, links won."""
        docs = await self.pitches.find({}).to_list(100000)
        return {"sent": sum(1 for d in docs if d.get("status") == "sent"),
                "replied": sum(1 for d in docs if d.get("replied")), "links_won": sum(1 for d in docs if d.get("link_won_url"))}

    async def prune_old(self, now: datetime, ttl_days: int) -> int:
        from datetime import timedelta
        cutoff = now - timedelta(days=ttl_days)
        res = await self.pitches.delete_many({"created_at": {"$lt": cutoff}})
        return int(getattr(res, "deleted_count", 0) or 0)
