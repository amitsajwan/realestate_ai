"""Re-pin every project page that lacks a checked position, in parallel.

Run once after deploying the pin-name fix (propertyfacts/pin.py) to quickly recover
the ~65% of project pages that had no Google-checked position:

  cd backend && PYTHONPATH=. python scripts/repin_catchup.py --dry-run  # count pages to fix
  cd backend && PYTHONPATH=. python scripts/repin_catchup.py            # fix them, 8 at a time
  cd backend && PYTHONPATH=. python scripts/repin_catchup.py --batch 4  # fewer concurrent calls

The normal enrichment loop re-pins one project every 5 minutes.  With 500+ pages missing
a checked position that is many hours; this script does them all in a single run.

Nothing is written unless Google finds a place: a "not found" record stays unchanged
(the enrichment loop will re-ask it on its next round, respecting REFRESH_DAYS).
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.modules.areastats import mappins, pages  # noqa: E402
from app.modules.newsroom.store import Store  # noqa: E402
from app.modules.propertyfacts.pin import Pins  # noqa: E402


async def _candidates(store: Store) -> list[dict]:
    """All indexable projects whose position is not Google-checked."""
    all_docs = await store.all_register()
    return [
        d for d in all_docs
        if pages.indexable(d) and not pages.own_position(d)
    ]


async def _repin(pins: Pins, doc: dict, sem: asyncio.Semaphore, now: datetime,
                 dry: bool) -> tuple[str, str]:
    """(regno, outcome). outcome: 'found', 'not_found', 'skipped', or an error message."""
    regno = doc.get("regno") or doc.get("_id") or ""
    name = str(doc.get("name") or "")
    locality = str(doc.get("locality") or doc.get("place") or "")
    pincode = str(doc.get("pincode") or "")
    geo = doc.get("geo") or {}
    centre = (float(geo["lat"]), float(geo["lon"])) if geo.get("lat") and geo.get("lon") else None
    sold = mappins.names_for(doc)
    if dry:
        return regno, f"would search '{name}'" + (f" also as {sold[:2]}" if sold else "")
    async with sem:
        try:
            pin, note = await pins.find(regno, name, locality, pincode, centre, now=now, names=sold)
        except Exception as exc:
            return regno, f"error: {exc}"
    return regno, "found" if pin else f"not_found ({note[:60]})"


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="count and describe without calling Google")
    ap.add_argument("--batch", type=int, default=8, help="concurrent Google Places calls (default 8)")
    a = ap.parse_args()

    if not settings.google_maps_api_key and not a.dry_run:
        print("GOOGLE_MAPS_API_KEY not set — nothing to do", file=sys.stderr)
        sys.exit(1)

    store = Store(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name])
    docs = await _candidates(store)
    print(f"{len(docs)} projects lack a checked position", flush=True)
    if not docs:
        return

    if a.dry_run:
        for doc in docs[:10]:
            sold = mappins.names_for(doc)
            print(f"  {doc.get('regno') or doc.get('_id')}: {doc.get('name')!r}"
                  + (f" → also try {sold[:2]}" if sold else ""))
        if len(docs) > 10:
            print(f"  … and {len(docs) - 10} more")
        return

    now = datetime.now(timezone.utc)
    pins = Pins(store.db, settings.google_maps_api_key)
    sem = asyncio.Semaphore(a.batch)

    tasks = [_repin(pins, doc, sem, now, dry=False) for doc in docs]
    found = not_found = errors = 0
    for coro in asyncio.as_completed(tasks):
        regno, outcome = await coro
        if outcome == "found":
            found += 1
        elif outcome.startswith("error"):
            errors += 1
        else:
            not_found += 1
        print(f"  {regno}: {outcome}", flush=True)

    print(f"\ndone — {found} found, {not_found} not found, {errors} errors "
          f"(of {len(docs)} without a checked position)", flush=True)


if __name__ == "__main__":
    asyncio.run(_main())
