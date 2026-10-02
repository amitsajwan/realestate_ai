"""Guide-run (G1) and Admin-run (AD1) test data helper: find, promote and remove ONLY the guides' test records.

  python scripts/g1_testdata.py scan              # list every document that mentions the test numbers/names (ids only, no values)
  python scripts/g1_testdata.py promote 9000000014  # temporary owner for the concierge / admin test (test numbers only)
  python scripts/g1_testdata.py controls          # show the Admin pause switches (admin_settings 'controls')
  python scripts/g1_testdata.py delete --confirm  # delete those documents and the uploaded files only they reference;
                                                  # Admin pause switches changed by a test user go back to unpaused

Test numbers are hard-coded below and nothing else can be touched: the script refuses any other phone.
Run from backend/ with PYTHONPATH=. (same MONGODB_URL/DATABASE_NAME as the app).
"""
import argparse
import asyncio
import os
import re
import shutil

from bson import ObjectId, json_util
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

TEST_PHONES = [f"90000000{n}" for n in range(11, 20)]  # 9000000011 to 9000000019 only
TEST_NAMES = ["Test Agent G1", "G1 Test Realty", "G1 Concierge Agent", "G1 Temp Owner", "G1 Buyer",
              "Admin Test Agent", "Admin Temp Owner", "Admin Web Person", "AD1 Test Homes"]
SETTINGS = "admin_settings"  # shared owner settings: never deleted wholesale, only the test users' changes are undone
# collections whose matched documents identify more test records (their ids are followed)
EXPAND = {"users", "agent_profiles", "listings", "concierge_agents", "leads", "contacts", "chat_sessions",
          "interest_links", "marketing_packs"}
UPLOAD_RE = re.compile(r"/uploads/[A-Za-z0-9_./-]+")


async def scan(db):
    markers = set(TEST_PHONES) | set(TEST_NAMES)
    names = sorted(await db.list_collection_names())
    hits: dict = {}
    for _ in range(4):  # follow ids a few hops (user -> profile -> listing -> lead ...)
        before = len(markers)
        for coll in names:
            if coll.startswith("system.") or coll == SETTINGS:
                continue
            async for doc in db[coll].find({}):
                blob = json_util.dumps(doc)
                found = [m for m in markers if m in blob]
                if not found:
                    continue
                hits[(coll, str(doc["_id"]))] = (doc, sorted(found))
                if coll in EXPAND:
                    markers.add(str(doc["_id"]))
                    for k in ("slug", "user_id", "agent_id", "listing_id", "lead_id", "contact_id", "session_id", "code"):
                        v = doc.get(k)
                        if isinstance(v, (str, ObjectId)) and len(str(v)) >= 6:
                            markers.add(str(v))
        if len(markers) == before:
            break
    return hits


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["scan", "promote", "controls", "delete"])
    ap.add_argument("phone", nargs="?")
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]

    if args.action == "promote":
        if args.phone not in TEST_PHONES:
            raise SystemExit("refused: not a guide test number")
        r = await db.users.update_one({"phone": "+91" + args.phone}, {"$set": {"is_superuser": True}})
        u = await db.users.find_one({"phone": "+91" + args.phone}, {"_id": 1})
        print(f"promoted matched={r.matched_count} modified={r.modified_count} user_id={u and u['_id']}")
        return

    if args.action == "controls":
        doc = await db[SETTINGS].find_one({"_id": "controls"}) or {}
        print({k: doc.get(k) for k in ("posting_paused", "comments_paused", "news_paused", "updated_at")}, "history", len(doc.get("history", [])))
        return

    hits = await scan(db)
    by_coll: dict = {}
    for (coll, _id), (_doc, found) in sorted(hits.items()):
        by_coll[coll] = by_coll.get(coll, 0) + 1
        print(f"{coll:28s} {_id:26s} via {','.join(m if len(m) < 20 else m[:8] + '..' for m in found)[:90]}")
    print("COUNTS", by_coll or "nothing left")
    if args.action == "scan":
        return
    if not args.confirm:
        raise SystemExit("add --confirm to delete")
    # files referenced only by the matched documents
    ours = set()
    for (_c, _i), (doc, _f) in hits.items():
        ours |= set(UPLOAD_RE.findall(json_util.dumps(doc)))
    others = set()
    hit_keys = set(hits)
    for coll in await db.list_collection_names():
        if coll.startswith("system."):
            continue
        async for doc in db[coll].find({}):
            if (coll, str(doc["_id"])) in hit_keys:
                continue
            blob = json_util.dumps(doc)
            if "/uploads/" in blob:
                others |= set(UPLOAD_RE.findall(blob)) & ours
    removed_files = 0
    for u in sorted(ours - others):
        rel = u.lstrip("/")
        for p in {rel, os.path.join(os.path.dirname(rel), "thumb_" + os.path.basename(rel))}:
            if p.startswith("uploads/") and ".." not in p and os.path.isfile(p):
                os.remove(p)
                removed_files += 1
    for (coll, _id), (doc, _f) in hits.items():
        if coll == "listings" and re.fullmatch(r"[A-Za-z0-9]{8,40}", _id):
            d = os.path.join("uploads", "marketing", _id)  # the marketing pack folder of a test listing
            if os.path.isdir(d):
                shutil.rmtree(d)
                removed_files += 1
        await db[coll].delete_one({"_id": doc["_id"]})
    print(f"deleted documents={len(hits)} files={removed_files} kept_shared_files={len(ours & others)}")
    await reset_controls(db, {_id for (coll, _id) in hits if coll == "users"})


async def reset_controls(db, test_user_ids: set) -> None:
    """Undo the Admin pause switches the test users changed: drop their history rows; if a test user made the last change, unpause."""
    doc = await db[SETTINGS].find_one({"_id": "controls"})
    if not doc or not test_user_ids:
        print("admin controls: nothing to reset")
        return
    history = [h for h in doc.get("history", []) if str(h.get("by")) not in test_user_ids]
    if not history and str(doc.get("updated_by")) in test_user_ids:
        await db[SETTINGS].delete_one({"_id": "controls"})  # only test users ever touched it: as if never set
        print("admin controls: removed (only test users had changed them)")
        return
    changes = {"history": history}
    if str(doc.get("updated_by")) in test_user_ids:
        changes.update(posting_paused=False, comments_paused=False, news_paused=False, updated_by="cleanup")
    await db[SETTINGS].update_one({"_id": "controls"}, {"$set": changes})
    print(f"admin controls: kept, {len(doc.get('history', [])) - len(history)} test rows removed")


if __name__ == "__main__":
    asyncio.run(main())
