#!/usr/bin/env python3
"""Delete every listing and the marketing it produced: the listings, their marketing runs, and their calendar rows.

Brand calendar rows (no listing_id), agents, users, property_facts and project_pins are kept: re-marketing a listing
reuses the extracted facts instead of paying Gemini/Maps again. Dry-run by default; --yes deletes.

On the VM:  cd ~/app/backend && .venv/bin/python scripts/clear_listings.py [--yes]
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_database, get_database

CALENDAR = "content_calendar"


async def main(dry_run: bool) -> None:
    await init_database()
    db = get_database()
    targets = [
        ("listings", {}),
        ("marketing_runs", {}),
        (CALENDAR, {"listing_id": {"$exists": True, "$ne": None}}),
    ]
    for name, flt in targets:
        n = await db.get_collection(name).count_documents(flt)
        print(f"{name}: {n} rows")
        if not dry_run:
            r = await db.get_collection(name).delete_many(flt)
            print(f"  deleted {r.deleted_count}")
    if dry_run:
        print("dry run: nothing deleted; pass --yes to delete")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="delete instead of only counting")
    asyncio.run(main(not ap.parse_args().yes))
