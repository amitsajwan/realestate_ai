"""Collections of the interest module: interest_links, interest_events, interest_log, hub_items."""
import secrets
from datetime import datetime
from typing import Optional

ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # no look-alikes (i l o 0 1)
CODE_LEN = 7


def new_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LEN))


class Store:
    def __init__(self, db):
        self.links = db.get_collection("interest_links")
        self.events = db.get_collection("interest_events")
        self.log = db.get_collection("interest_log")
        self.hub = db.get_collection("hub_items")

    async def find_link(self, kind: str, ref: str, channel: str) -> Optional[dict]:
        return await self.links.find_one({"kind": kind, "ref": ref, "channel": channel})

    async def by_code(self, code: str) -> Optional[dict]:
        return await self.links.find_one({"code": code})

    async def insert_link(self, doc: dict) -> dict:
        for _ in range(8):  # a clash on a 7-char code is rare; just draw again
            code = new_code()
            if not await self.links.find_one({"code": code}):
                doc = {**doc, "code": code}
                await self.links.insert_one({**doc, "_id": code})
                return doc
        raise RuntimeError("could not allocate an interest code")

    async def links_for_ref(self, ref: str) -> list:
        return await self.links.find({"ref": ref}).to_list(50)

    async def add_event(self, code: str, type_: str, anon_id: str, now: datetime) -> None:
        await self.events.insert_one({"code": code, "type": type_, "anon_id": anon_id, "ts": now})

    async def count(self, code: str, type_: str) -> int:
        return await self.events.count_documents({"code": code, "type": type_})

    # --- abuse log: one row per accepted public attempt, counted inside a rolling window ---
    async def attempts(self, kind: str, key: str, since: datetime) -> int:
        return await self.log.count_documents({"kind": kind, "key": key, "ts": {"$gt": since}})

    async def log_attempt(self, kind: str, key: str, now: datetime) -> None:
        await self.log.insert_one({"kind": kind, "key": key, "ts": now})

    async def hub_items(self, limit: int) -> list:
        return await self.hub.find({}).sort("updated_at", -1).limit(limit).to_list(limit)
