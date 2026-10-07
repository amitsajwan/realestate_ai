"""Bring the queued agent-recruitment reels up to date: the new caption (no "Screens show sample data", agent_reels.caption) and
a fresh render (the listing-reel screen is now a real House Deal project, not a sample home).

  docker compose exec -T -e PYTHONPATH=. backend python scripts/fix_agent_reel_captions.py            # dry run: prints before/after
  docker compose exec -T -e PYTHONPATH=. backend python scripts/fix_agent_reel_captions.py --apply    # writes

Only content_calendar rows with creative.source == "agent_reels" and status planned, approved or scheduled are touched (published,
failed and skipped rows are history). For each: caption = agent_reels.caption(code, channel); `video` is unset and an already
rendered <uploads>/calendar/reels/<reel_key>.mp4 (and its -cover.jpg) is removed, so the worker renders the reel again before it is
due. The status (approved stays approved) and the due time are not changed. Running it twice changes nothing the second time.
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.reels import agent_reels as ar  # noqa: E402

OPEN = ("planned", "approved", "scheduled")
QUERY = {"creative.source": "agent_reels", "status": {"$in": list(OPEN)}}
REEL_DIR = "calendar/reels"


def changes(rows: List[dict]) -> List[dict]:
    """Per row that needs it: {_id, slug, channel, code, reel_key, before, after, video}. Pure."""
    out = []
    for r in rows:
        c = r.get("creative") or {}
        code = c.get("reel_code")
        if r.get("status") not in OPEN or c.get("source") != "agent_reels" or code not in ar.BY_CODE:
            continue
        after = ar.caption(code, r["channel"])
        if r.get("caption") == after and not r.get("video"):
            continue
        out.append({"_id": r["_id"], "slug": r.get("slug"), "channel": r["channel"], "code": code,
                    "reel_key": c.get("reel_key") or r.get("slug"), "before": r.get("caption") or "", "after": after,
                    "video": r.get("video")})
    return out


def stale_files(uploads: Path, reel_key: str) -> List[Path]:
    mp4 = Path(uploads) / REEL_DIR / f"{reel_key}.mp4"
    return [p for p in (mp4, mp4.with_name(f"{mp4.stem}-cover.jpg")) if p.is_file()]


async def run(db, uploads: Path, apply: bool, say=print) -> int:
    items = db.get_collection("content_calendar")
    rows = await items.find(QUERY).to_list(None)
    todo = changes(rows)
    say(f"{len(rows)} open agent-reel rows, {len(todo)} to update ({'APPLY' if apply else 'dry run: nothing is written'})")
    for t in todo:
        say(f"\n--- {t['code']} {t['channel']} ({t['slug']}, {t['_id']})")
        if t["before"] != t["after"]:
            say("BEFORE:\n" + t["before"] + "\nAFTER:\n" + t["after"])
        else:
            say("caption already up to date")
        files = stale_files(uploads, t["reel_key"])
        say(f"video: {t['video'] or 'none'} -> re-render" + (f"; remove {', '.join(str(f) for f in files)}" if files else ""))
        if apply:
            await items.update_one({"_id": t["_id"]}, {"$set": {"caption": t["after"], "updated_at": datetime.utcnow()},
                                                       "$unset": {"video": ""}})
            for f in files:
                f.unlink(missing_ok=True)
    return len(todo)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    a = ap.parse_args()
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    asyncio.run(run(db, Path(settings.upload_directory), a.apply))
    return 0


if __name__ == "__main__":
    sys.exit(main())
