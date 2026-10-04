"""Fill the project register for all 8 areas now, instead of waiting ~10 days for the newsroom's gentle step.

  cd backend && PYTHONPATH=. python scripts/area_backfill.py --dry-run   # say what it would read, write nothing
  cd backend && PYTHONPATH=. python scripts/area_backfill.py             # one full sweep, then every record's details

Runs areastats.refresh.step until the pincode sweep has gone round once and no record waits for details: about 250 search
pages and one project API call per in-area project (about 1,000 on 2026-10-04), PAUSE seconds apart, so about an hour.
Safe to stop and run again: the sweep keeps its place and records are keyed by registration number.
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.agentprojects.maharera import make_fetch  # noqa: E402
from app.modules.areastats import refresh  # noqa: E402
from app.modules.newsroom.adapters import make_fetcher  # noqa: E402
from app.modules.newsroom.store import Store  # noqa: E402

PAGES, DETAILS = 10, 50  # per step


async def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        print(f"would read every page of pincodes {', '.join(refresh.pincodes())} on MahaRERA and the details of each in-area "
              f"project, {refresh.PAUSE}s apart")
        return
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings
    store = Store(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name])
    get, fetch, swept = make_fetcher(), make_fetch(), False
    while True:
        out = await refresh.step(store, get, fetch, datetime.now(timezone.utc), PAGES, 0 if not swept else DETAILS)
        swept = swept or bool((out.get("sweep") or {}).get("round_done"))
        print(out, flush=True)
        if swept and not ((out.get("details") or {}).get("read") or (out.get("details") or {}).get("failed")):
            break
        await asyncio.sleep(refresh.PAUSE)
    print("done")


if __name__ == "__main__":
    asyncio.run(_main())
