"""Owner pause switches, stored in `admin_settings` (document 'controls').

The background runners call `is_paused(db, flag)` at the start of each cycle and skip it while the flag is true:
  posting_paused  -> calendar runner (scheduled Facebook / Instagram posts)
  comments_paused -> engage runner (comment replies)
  news_paused     -> newsroom runner (fetching, drafting and publishing news)
A missing document means nothing is paused. A read error never pauses anything (the runner carries on as before).
"""
import logging
from datetime import datetime
from typing import Dict, Optional

log = logging.getLogger(__name__)

COLLECTION = "admin_settings"
DOC_ID = "controls"
FLAGS = ("posting_paused", "comments_paused", "news_paused")


def _iso(dt) -> Optional[str]:
    if isinstance(dt, datetime):
        return dt.isoformat() + ("Z" if dt.tzinfo is None else "")
    return dt


async def get_controls(db) -> Dict:
    doc = await db.get_collection(COLLECTION).find_one({"_id": DOC_ID}) or {}
    out = {f: bool(doc.get(f)) for f in FLAGS}
    out["updated_at"] = _iso(doc.get("updated_at"))
    out["updated_by"] = doc.get("updated_by")
    return out


async def set_controls(db, changes: Dict[str, bool], by: str, now: datetime) -> Dict:
    """Set the given flags (unknown keys are ignored) and remember who changed what, when."""
    changes = {k: bool(v) for k, v in changes.items() if k in FLAGS and v is not None}
    col = db.get_collection(COLLECTION)
    if changes:
        fields = {**changes, "updated_at": now, "updated_by": by}
        update = {"$set": fields, "$push": {"history": {"at": now, "by": by, **changes}}}
        if await col.find_one({"_id": DOC_ID}):
            await col.update_one({"_id": DOC_ID}, update)
        else:
            await col.insert_one({"_id": DOC_ID, **{f: False for f in FLAGS}, **fields, "history": [{"at": now, "by": by, **changes}]})
        log.info("admin: controls changed by %s: %s", by, changes)
    return await get_controls(db)


async def is_paused(db, flag: str) -> bool:
    try:
        doc = await db.get_collection(COLLECTION).find_one({"_id": DOC_ID})
        return bool(doc and doc.get(flag))
    except Exception:  # a broken settings read must never stop or pause the runners
        log.warning("admin: could not read the pause switches", exc_info=True)
        return False
