"""Take the distances out of project page texts written before projects had their own pin (2026-10-14).

Until then nearby places were measured from the middle of the project's locality, so every Kharadi page said "Shree Hospital
(0.1 km) ..." whatever the project. This drops each sentence of `page_text` that quotes a distance in km, on records whose fact
sheet has no project pin (propertyfacts.pin); the next enrichment writes the text again from checked facts.

  cd backend && PYTHONPATH=. python scripts/drop_area_distances.py           # say what would change, write nothing
  cd backend && PYTHONPATH=. python scripts/drop_area_distances.py --apply
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.areastats.enrich import sheet_value  # noqa: E402
from app.modules.propertyfacts.store import COLLECTION as FACTS  # noqa: E402

KM = re.compile(r"\d+(?:\.\d+)?\s*km\b", re.I)
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def without_distances(text: str) -> str:
    paras = []
    for para in (text or "").split("\n"):
        kept = [s for s in SENTENCE.split(para.strip()) if s and not KM.search(s)]
        if kept:
            paras.append(" ".join(kept))
    return "\n".join(paras)


async def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.core.config import settings
    from app.modules.newsroom.store import Store
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    store, facts = Store(db), db.get_collection(FACTS)
    changed = 0
    for d in await store.all_projects():
        text = d.get("page_text") or ""
        if not KM.search(text):
            continue
        sheet = await facts.find_one({"_id": (d.get("regno") or d["_id"]).upper()})
        if sheet_value(sheet, "located_at") == "project":
            continue
        new = without_distances(text)
        changed += 1
        print(f"{d['_id']}: {len(text)} -> {len(new)} chars")
        if args.apply:
            await store.set_project(d["_id"], page_text=new)
    print(f"{changed} page text(s) {'changed' if args.apply else 'would change'}")


if __name__ == "__main__":
    asyncio.run(_main())
