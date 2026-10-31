"""Draw the 3D floor plans of projects (areastats.plans3d) and keep them on their records, so their pages show them after the
floor-plan form.

  cd backend && PYTHONPATH=. python scripts/plans_3d.py PR1260002501386            # one project (its group's primary record)
  cd backend && PYTHONPATH=. python scripts/plans_3d.py PR1260002501386 --dry-run  # read, check and draw; write nothing
  cd backend && PYTHONPATH=. python scripts/plans_3d.py PR1260002501386 --redo     # draw again the plans already drawn
  cd backend && PYTHONPATH=. python scripts/plans_3d.py --targets [--max 20]       # every target project (plans3d.target)

With --targets a project with no plan stored gets its plans collected first (areastats.planfind); one with none found is left
alone (nothing is ever drawn without a plan). Costs about Rs 0.1 a reading and Rs 4 a drawing on the paid Gemini key. Run
where uploads/ is: the backend container on the VM.
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
from app.modules.areastats import planfind, plans3d  # noqa: E402
from app.modules.newsroom.store import Store  # noqa: E402


async def one(store: Store, doc: dict, dry_run: bool, redo: bool, find: bool) -> dict:
    now = datetime.now(timezone.utc)
    if find and not plans3d.unit_plans(doc):
        found = await planfind.collect(store, doc, now)
        if not dry_run:
            await store.set_project(doc["_id"], **found)
        doc = {**doc, **found}
        if not plans3d.unit_plans(doc):
            return {"plans_3d": None, "why": "no plan found"}
    fields = await plans3d.make(doc, now, redo=redo)
    if not dry_run:
        await store.set_project(doc["_id"], **fields)
    return fields


async def main(regno: str, dry_run: bool, redo: bool, targets: bool, most: int) -> None:
    store = Store(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name])
    if not targets:
        doc = await store.project(regno.strip().upper())
        if doc is None:
            sys.exit(f"{regno}: not in the register")
        if doc.get("cluster_primary"):
            doc = await store.project(doc["cluster_primary"])
        fields = await one(store, doc, dry_run, redo, find=False)
        print(json.dumps(fields["plans_3d"], default=str, indent=1, ensure_ascii=False))
        return
    today = datetime.now(timezone.utc).date()
    docs = [d for d in await store.all_projects() if plans3d.target(d, today)]
    # the ones with plans stored first (cheapest to draw), then the most looked-at
    docs.sort(key=lambda d: (0 if plans3d.unit_plans(d) else 1, -int(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0)))
    print(f"{len(docs)} target projects")
    drawn = 0
    for d in docs[:most]:
        try:
            fields = await one(store, d, dry_run, redo, find=True)
        except Exception as e:   # one project failing never stops the rest
            print(f"{d['_id']} {d.get('name')}: failed ({type(e).__name__}: {e})")
            continue
        p = fields.get("plans_3d")
        n = len(p["items"]) if p else 0
        drawn += n
        why = "; ".join(f"{t['why']}" for t in (p or {}).get("tried") or []) or fields.get("why", "")
        print(f"{d['_id']} {d.get('pune_place')} {d.get('name')}: {n} drawings | {why[:220]}", flush=True)
    print(f"done: {drawn} drawings")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("regno", nargs="?", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--targets", action="store_true")
    ap.add_argument("--max", type=int, default=100)
    a = ap.parse_args()
    if not a.targets and not a.regno:
        ap.error("give a regno or --targets")
    asyncio.run(main(a.regno, a.dry_run, a.redo, a.targets, a.max))
