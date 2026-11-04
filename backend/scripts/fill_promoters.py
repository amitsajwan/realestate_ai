"""Fill the blank promoters of the projects in our areas from their MahaRERA cards (areastats/refresh.fill_promoters).

  cd backend && PYTHONPATH=. python scripts/fill_promoters.py --dry-run    # in the backend container on the VM: names it would write
  cd backend && PYTHONPATH=. python scripts/fill_promoters.py

The pincode sweep fills them too, but it takes two weeks and more to come back to our areas after the firm list widens. Idempotent:
only a blank promoter is written, and an individual promoter stays blank (personal data, sources/maharera._ORG).
"""
import argparse
import asyncio
import sys
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.modules.areastats import refresh  # noqa: E402
from app.modules.newsroom import adapters  # noqa: E402
from app.modules.newsroom.store import Store  # noqa: E402


async def main(dry_run: bool) -> None:
    store = Store(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name])
    out = await refresh.fill_promoters(store, adapters.make_fetcher(), dry_run=dry_run)
    for regno, name in out.pop("names"):
        print(regno, name)
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    asyncio.run(main(parser.parse_args().dry_run))
