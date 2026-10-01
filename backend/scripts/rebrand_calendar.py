"""Redraw every not-yet-published calendar item in the current brand, keeping the owner's approvals.
  docker compose exec -T -e PYTHONPATH=. backend python scripts/rebrand_calendar.py
Published rows are untouched. Rows that were approved come back approved (by due date); planned rows come back planned."""
import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from app.core.database import get_database, init_database
from app.modules.ai_listing.llm import default_llm
from app.modules.calendar.builder import build_and_store
from app.modules.calendar.store import Store


async def main():
    await init_database()
    db = get_database()
    col = db.get_collection("content_calendar")
    approved = [d async for d in col.find({"status": {"$in": ["approved", "scheduled"]}})]
    last_approved = max((d["due_at"] for d in approved), default=None)
    gone = await col.delete_many({"status": {"$in": ["approved", "scheduled", "planned"]}})
    print(f"removed {gone.deleted_count} unpublished rows ({len(approved)} were approved, up to {last_approved})")
    store = Store(db)
    uploads = Path(os.environ.get("UPLOAD_DIRECTORY", "uploads"))
    first = min((d["due_at"] for d in approved), default=datetime.now(timezone.utc))
    weeks = max(1, ((last_approved - first).days // 7) + 1) if last_approved else 1
    made = await build_and_store(store, first.date(), weeks, uploads, llm=default_llm(), say=print)
    n = 0
    if last_approved is not None:
        for m in made:
            due = m["item"].due_at
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            la = last_approved if last_approved.tzinfo else last_approved.replace(tzinfo=timezone.utc)
            if due <= la:
                await col.update_one({"_id": m["id"]}, {"$set": {"status": "approved"}})
                n += 1
    print(f"rebuilt {len(made)} rows in the new brand; {n} approved again (due on or before the last approved date)")


asyncio.run(main())
