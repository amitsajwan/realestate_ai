"""Draw the 3D floor plans of one project (areastats.plans3d) and keep them on its record, so its page shows them.

  cd backend && PYTHONPATH=. python scripts/plans_3d.py PR1260002501386            # Lodha Camelot (its group's primary record)
  cd backend && PYTHONPATH=. python scripts/plans_3d.py PR1260002501386 --dry-run  # read, check and draw; write nothing
  cd backend && PYTHONPATH=. python scripts/plans_3d.py PR1260002501386 --redo     # draw again the plans already drawn

Costs about Rs 4 a drawing on the paid Gemini key (a plan that fails the checks is not drawn). Run where uploads/ is: the
backend container on the VM.
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.modules.areastats import plans3d  # noqa: E402
from app.modules.newsroom.store import Store  # noqa: E402


async def main(regno: str, dry_run: bool, redo: bool) -> None:
    store = Store(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name])
    doc = await store.project(regno.strip().upper())
    if doc is None:
        sys.exit(f"{regno}: not in the register")
    if doc.get("cluster_primary"):
        doc = await store.project(doc["cluster_primary"])
    fields = await plans3d.make(doc, datetime.now(timezone.utc), redo=redo)
    print(json.dumps(fields["plans_3d"], default=str, indent=1, ensure_ascii=False))
    if not dry_run:
        await store.set_project(doc["_id"], **fields)
        print(f"kept on {doc['_id']}: {len(fields['plans_3d']['items'])} drawings")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("regno")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    asyncio.run(main(a.regno, a.dry_run, a.redo))
