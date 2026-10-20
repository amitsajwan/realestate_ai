"""Rebuild the /go hub (the Instagram bio page) from the posts and reels published in the last days, with today's card rule
(calendar.adapters.register_hub: one card per listing, reels included, recruitment posts left out, the Instagram code).

  python scripts/rebuild_go_hub.py [--days 30] [--dry]

Cards for single posts of a listing (the older rule: one card per post) are removed, and cards of agent-recruitment posts too.
News cards are kept (the newsroom makes them). Each rebuilt card keeps its post's publish time, so the newest post stays on top.
Run on the server:  docker compose exec -T -e PYTHONPATH=. media python scripts/rebuild_go_hub.py
"""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import get_database, init_database  # noqa: E402
from app.modules.calendar import adapters  # noqa: E402
from app.modules.calendar.config import uploads_dir  # noqa: E402
from app.modules.calendar.reach import audience  # noqa: E402


async def main(days: int, dry: bool) -> None:
    await init_database()
    db = get_database()
    cal, hub = db.get_collection("content_calendar"), db.get_collection("hub_items")
    since = datetime.utcnow() - timedelta(days=days)
    rows = await cal.find({"status": "published", "published_at": {"$gte": since}}).sort("published_at", 1).to_list(5000)
    old = 0
    for card in await hub.find({"kind": "post"}).to_list(5000):
        if str(card.get("ref", "")).startswith("news-"):
            continue
        row = await cal.find_one({"slug": card["ref"]})
        if row and (row.get("listing_id") or audience(row) == "agents"):
            old += 1
            if not dry:
                await hub.delete_one({"_id": card["_id"]})
    made = 0
    for row in rows:
        if dry:
            made += 1
            continue
        await adapters.register_hub(db, row, row.get("permalink") or "", uploads_dir())
        listing = row.get("listing_id")
        key = f"listing:{listing}" if listing and await db.get_collection("listings").find_one({"_id": listing}) else f"post:{row['slug']}"
        card = await hub.find_one({"_id": key})
        if card and card.get("slug") == row["slug"]:   # keep the post's publish time, not now
            await hub.update_one({"_id": key}, {"$set": {"updated_at": row["published_at"]}})
            made += 1
    print(f"{'would remove' if dry else 'removed'} {old} per-post or recruitment cards; {'would register' if dry else 'registered'} "
          f"{made} published rows from the last {days} days; hub now has {await hub.count_documents({})} cards (dead ones drop on the next read)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--dry", action="store_true")
    a = p.parse_args()
    asyncio.run(main(a.days, a.dry))
