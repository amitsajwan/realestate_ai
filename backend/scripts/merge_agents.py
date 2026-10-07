"""Merge a duplicate agent account into the agent's real one, and give the real one the duplicate's address.

  cd backend && PYTHONPATH=. python scripts/merge_agents.py --from house-deal --into sharad --slug house-deal [--dry-run]

Used once for House Deal (2026-10-03): the owner made /agent/house-deal (5 projects, posts) while House Deal already had an
account (/agent/sharad, login on Sharad's own mobile, 3 listings). The real account keeps its login, listings, brand and consent;
it takes over the duplicate's projects, interest links, events and calendar rows, and its slug becomes --slug. The duplicate's
profile is hidden and renamed, its concierge record removed and its login user deactivated. Old /agent/<into> links are
redirected in frontend/next.config.js.
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

MOVE = ("agent_projects", "interest_links", "events", "content_calendar", "listings", "leads", "contacts")


async def merge(db, src_slug: str, dst_slug: str, new_slug: str, dry: bool, log=print) -> dict:
    profiles = db.get_collection("agent_public_profiles")
    src = await profiles.find_one({"slug": src_slug})
    dst = await profiles.find_one({"slug": dst_slug})
    if not src or not dst:
        raise SystemExit(f"need both /agent/{src_slug} and /agent/{dst_slug}")
    a, b = src["agent_id"], dst["agent_id"]
    moved = {}
    for name in MOVE:
        n = await db.get_collection(name).count_documents({"agent_id": a})
        if n:
            moved[name] = n
            if not dry:
                await db.get_collection(name).update_many({"agent_id": a}, {"$set": {"agent_id": b}})
    log(f"move {a} -> {b}: {moved}")
    now = datetime.now(timezone.utc)
    if not dry:
        retired = f"{src_slug}-retired-{now:%Y%m%d}"
        await profiles.update_one({"_id": src["_id"]}, {"$set": {"slug": retired, "is_public": False, "is_active": False, "updated_at": now}})
        if new_slug != dst_slug:
            await profiles.update_one({"_id": dst["_id"]}, {"$set": {"slug": new_slug, "updated_at": now}})
        await db.get_collection("concierge_agents").delete_one({"_id": a})
        await db.get_collection("concierge_audit").insert_one({"at": now, "by": "owner", "action": "agent.merge", "agent_id": b,
                                                               "keys": sorted(moved), "note": f"merged {a} ({src_slug}) into {b}"})
        try:
            from bson import ObjectId
            await db.get_collection("users").update_one({"_id": ObjectId(a)}, {"$set": {"is_active": False}})
        except Exception as e:  # the profile is already hidden; a missing user is not fatal
            log(f"could not deactivate user {a}: {e}")
        log(f"/agent/{new_slug} is now {b}; the duplicate is /agent/{retired} (hidden)")
    return {"from": a, "into": b, "moved": moved}


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--into", dest="dst", required=True)
    ap.add_argument("--slug", required=True, help="the address the merged account ends up with")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    await merge(db, a.src, a.dst, a.slug, a.dry_run)


if __name__ == "__main__":
    asyncio.run(_main())
