"""Guide reels (app/modules/calendar/guide_reels.py): the team's words, the pictures, the voiced video, and the rows that post it.

  PYTHONPATH=. python scripts/guide_reel.py write mhada-deadline-mr              the team's words only (nothing drawn or posted)
  PYTHONPATH=. python scripts/guide_reel.py plan mhada-deadline-mr               words + pictures + the Instagram and Facebook rows
                                                                                 (approved; the renderer draws the video before they are due)
  PYTHONPATH=. python scripts/guide_reel.py render mhada-deadline-mr             draw the video now and put it on the rows
A hand-made picture for shot n goes in uploads/calendar/guides/<slug>/own/<n>.jpg; delete <n>.png there to have a shot drawn again.
On the server: docker compose exec -T -e PYTHONPATH=. media python scripts/guide_reel.py plan mhada-deadline-mr
On Cloud Run: gcloud run jobs execute renderer --region asia-south1 --args=scripts/guide_reel.py,render,mhada-deadline-mr
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.calendar import guide_reels as gr  # noqa: E402


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    return AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]


async def _run(a) -> int:
    from app.modules.calendar.config import uploads_dir
    guide = gr.load(a.guide)
    if a.cmd == "write":
        beats, note = await gr.write(guide)
        print(json.dumps({"beats": beats, "note": note}, ensure_ascii=False, indent=1))
        return 0
    from app.modules.calendar.store import Store
    store = Store(_db())
    if a.cmd == "plan":
        if a.replace:   # rows not posted yet are planned again (new words, same pictures)
            gone = await store.items.delete_many({"slug": guide.slug, "external_id": None, "status": {"$in": ["approved", "planned"]}})
            print(f"{gone.deleted_count} unposted rows removed")
        prep = await gr.prepare(guide, uploads_dir(), say=print)
        for b in prep.beats:
            print(f"  [{b['screen']}]  {b['voice']}")
        ids = await gr.schedule(store, guide, prep)
        print(f"{len(ids)} rows added, due {guide['due']}" if ids else "rows were already there; nothing added")
        return 0
    rows = [d for d in await store.all() if d["slug"] == guide.slug and d.get("kind") == "reel"]
    if not rows:
        print("no rows: run plan first")
        return 1
    video = gr.render_row(rows[0], uploads_dir())
    from app.modules.calendar import adapters
    info = adapters.video_info(video, uploads_dir())
    for d in rows:
        await store.set_video(d["_id"], video, info)
    print(f"video {video} {info}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["write", "plan", "render"])
    ap.add_argument("guide")
    ap.add_argument("--replace", action="store_true", help="plan: remove this guide's unposted rows first")
    return asyncio.run(_run(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
