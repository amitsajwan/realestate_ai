"""Builder logos from official sites the owner's team named, for big builders the daily pass could not place (areastats/logos.py).

  cd backend && PYTHONPATH=. python scripts/builder_logos_by_hand.py              # in the backend container on the VM
  cd backend && PYTHONPATH=. python scripts/builder_logos_by_hand.py --dry-run    # print the builders it would read, write nothing

The daily pass finds a builder's site through enrichment or one web search, and recorded "no site of the builder found" for these
(2026-10-31). Idempotent: run it again any time. A builder whose logo is not found keeps what it has.
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.modules.areastats import logos, profile, webfacts  # noqa: E402
from app.modules.areastats.pages import builder_key  # noqa: E402
from app.modules.newsroom.store import Store  # noqa: E402

SITES = {
    "kolte-patil": ("koltepatil.com", ["Kolte Patil", "Kolte-Patil"]),
    "kohinoor-group": ("iamkohinoor.com", ["Kohinoor"]),
    "goel-ganga": ("goelgangadevelopments.com", ["Goel Ganga", "Ganga"]),
    "vilas-javdekar": ("javdekars.com", ["Vilas Javdekar", "VJ"]),
    "jindal-mittal-graha-nirman": ("mittalbuilders.com", ["Mittal", "Jindal Mittal"]),
}


async def main(dry_run: bool) -> None:
    store = Store(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name])
    every = await store.all_projects()
    now = datetime.now(timezone.utc)
    for key, (site, names) in SITES.items():
        ids = [d["_id"] for d in every if builder_key(d) == key]
        if dry_run:
            print(key, site, len(ids), "records")
            continue
        got = await logos.find_logo(site, key, names, webfacts.fetch_page, profile.fetch_bytes)
        if got["status"] == "found":
            await store.set_projects(ids, builder_logo={**got, "at": now})
        print(key, got["status"], got.get("path") or got.get("why"), len(ids), "records")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    asyncio.run(main(ap.parse_args().dry_run))
