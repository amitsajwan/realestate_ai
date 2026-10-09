"""radar_watches and radar_signals: the radar is their only writer (docs/RADAR.md §8)."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

WATCHES, SIGNALS, USAGE = "radar_watches", "radar_signals", "radar_usage"


def now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes(db) -> None:
    s = db.get_collection(SIGNALS)
    await s.create_index([("source", 1), ("external_id", 1)], unique=True)
    await s.create_index([("status", 1), ("score", -1)])
    await s.create_index([("area", 1), ("created_at", -1)])
    await s.create_index("expire_at", expireAfterSeconds=0)
    await db.get_collection(WATCHES).create_index([("source", 1), ("kind", 1), ("value", 1)], unique=True)


async def add_signal(db, doc: dict) -> bool:
    """False when it was already stored."""
    from pymongo.errors import DuplicateKeyError
    try:
        await db.get_collection(SIGNALS).insert_one({**doc, "status": "new", "created_at": now()})
        return True
    except DuplicateKeyError:
        return False


async def pending(db, status: str, limit: int) -> List[dict]:
    return await db.get_collection(SIGNALS).find({"status": status}).sort("created_at", 1).to_list(limit)


async def set_signal(db, sid, fields: dict, expire_days: Optional[int] = None) -> None:
    if expire_days:
        fields = {**fields, "expire_at": now() + timedelta(days=expire_days)}
    await db.get_collection(SIGNALS).update_one({"_id": sid}, {"$set": {**fields, "updated_at": now()}})


async def upsert_watch(db, source: str, kind: str, value: str, **fields) -> None:
    await db.get_collection(WATCHES).update_one(
        {"source": source, "kind": kind, "value": value},
        {"$setOnInsert": {"created_at": now(), "active": True, "hits": 0, "found": 0, "cursor": None, **fields}}, upsert=True)


async def active_watches(db, source: str, kind: str, limit: int = 500) -> List[dict]:
    return await db.get_collection(WATCHES).find({"source": source, "kind": kind, "active": True}).sort("checked_at", 1).to_list(limit)


async def touch_watch(db, wid, **fields) -> None:
    inc = {k: fields.pop(k) for k in ("hits", "found") if k in fields}
    update = {"$set": {**fields, "checked_at": now()}}
    if inc:
        update["$inc"] = inc
    await db.get_collection(WATCHES).update_one({"_id": wid}, update)


async def spend(db, what: str, n: int = 1) -> int:
    """Today's usage counter for a capped resource; returns the new total."""
    day = now().strftime("%Y-%m-%d")
    doc = await db.get_collection(USAGE).find_one_and_update({"_id": f"{day}:{what}"}, {"$inc": {"n": n}}, upsert=True,
                                                            return_document=True)
    return int((doc or {}).get("n", n))


async def used(db, what: str) -> int:
    doc = await db.get_collection(USAGE).find_one({"_id": f"{now().strftime('%Y-%m-%d')}:{what}"})
    return int((doc or {}).get("n", 0))
