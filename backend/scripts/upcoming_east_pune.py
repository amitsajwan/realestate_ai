"""The coming-soon projects of the East Pune band, kept short on purpose (owner 2026-11-02: "dont disclose much").

  cd backend && PYTHONPATH=. python scripts/upcoming_east_pune.py              # in the backend container on the VM
  cd backend && PYTHONPATH=. python scripts/upcoming_east_pune.py --dry-run    # print what it would set, write nothing

Idempotent. Each record says only the builder, the area and the home types. The old Esbee record (esbee-upper-kharadi) is hidden,
because the owner places the project in Wagholi; next.config sends its old address to the new one. The banner's picks are kept,
with the Esbee pick moved. No prices or offers: the schema has no field for them.

The owner confirmed on 2026-11-02 that the Vilas Javdekar project is new, not Yashwin Enchante Phase 2 (P52100077455, registered).
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
from app.modules.areastats import spotlight, upcoming  # noqa: E402

OLD_ESBEE = "esbee-upper-kharadi"
READ_ON = "2026-11-02"


def _record(slug, name, builder, area, logo, summary, source):
    homes = [{"bhk": b, "source": source, "to_confirm": True} for b in (2, 3)]
    return {"slug": slug, "name": name, "builder": builder, "area": area, "logo": logo, "summary": summary, "note": "2 & 3 BHK · coming soon",
            "homes": homes, "facts": [{"label": "Status", "value": "Not yet registered with MahaRERA", "source": "Avasetu's check of the register"}],
            "sources": [{"name": source, "url": "", "read_on": READ_ON}]}


RECORDS = [
    _record("esbee-wagholi", "Esbee new project", "Esbee Realty", "wagholi", "/upcoming/logos/esbee.png",
            "A new Esbee Realty project planned in Wagholi. It is not yet registered with MahaRERA; details come out when it is.",
            "An agent's website"),
    _record("ceratec-central-park", "Ceratec Central Park", "Ceratec Group", "wagholi", "/upcoming/logos/ceratec.webp",
            "A Ceratec Group project planned in Wagholi. It is not yet registered with MahaRERA; details come out when it is.",
            "Ceratec's website"),
    _record("vilas-javdekar-upper-kharadi", "Vilas Javdekar new project", "Vilas Javdekar", "upper_kharadi", "/upcoming/logos/vj.png",
            "A new Vilas Javdekar project listed in Upper Kharadi. It is not yet registered with MahaRERA; details come out when it is.",
            "A Housing.com listing"),
]


def new_picks(items):
    """The banner's picks with the old Esbee one moved, and any of the three not yet on it added."""
    old = upcoming.PREFIX + OLD_ESBEE
    out = [{**it, "slug": upcoming.PREFIX + "esbee-wagholi", "note": ""} if it["slug"] == old else {**it} for it in items]
    for r in RECORDS:
        slug = upcoming.PREFIX + r["slug"]
        if not any(it["slug"] == slug for it in out):
            out.append({"slug": slug, "note": ""})
    return out


async def main(dry_run: bool) -> None:
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    now = datetime.now(timezone.utc)
    cfg = await spotlight.get_config(db)
    picks = new_picks(cfg["items"])
    if dry_run:
        print([r["slug"] for r in RECORDS], "hide", OLD_ESBEE, [it["slug"] for it in picks])
        return
    for r in RECORDS:
        await upcoming.put(db, r, now)
    await db.get_collection(upcoming.COLLECTION).update_one({"_id": OLD_ESBEE}, {"$set": {"status": "hidden", "updated_at": now}})
    await spotlight.set_config(db, {"auto": cfg["auto"], "items": picks}, "scripts/upcoming_east_pune.py", now)
    print("Done:", [it["slug"] for it in picks])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    asyncio.run(main(ap.parse_args().dry_run))
