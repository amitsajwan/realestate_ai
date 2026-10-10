"""Date-watch reels (app/modules/calendar/delay_reels.py): see what the system would post, preview it, or plan it now.

The calendar loop plans these by itself once a day (CALENDAR_DELAY_REELS, on by default); this script is for looking and testing.
  PYTHONPATH=. python scripts/delay_reels.py list [--area wagholi]
        the board candidates (most moved first, net of the COVID extension) and the projects held back for the owner to check
  PYTHONPATH=. python scripts/delay_reels.py preview [--area wagholi] [--out uploads/datewatch-preview]
        draw and check one board's slides and render its MP4 (no area = all of Pune)
  PYTHONPATH=. python scripts/delay_reels.py plan
        what the loop does: plan next Monday's board and Thursday's moves as PLANNED rows (owner approves in Studio)
On the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/delay_reels.py list
"""
import argparse
import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.calendar import area_reels, delay_reels as dr  # noqa: E402


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    return AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]


async def _cands():
    from app.modules.newsroom.store import Store
    docs = await Store(_db()).all_projects()
    as_of = max((str(d.get("details_checked_at") or "")[:10] for d in docs), default="") or date.today().isoformat()
    return dr.candidates(docs, date.today()), as_of


def _row(c: dict) -> str:
    covid = f" (-{c['covid']} covid)" if c["covid"] else ""
    return (f"{c['net']:>3}m net{covid:13} {c['area']:14} {c['regno']}  {c['name'][:34]:34} "
            f"{dr._month(c['first'])} -> {dr._month(c['now'])}  booked {c['booked']}/{c['total']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--area", default="")
    p = sub.add_parser("preview")
    p.add_argument("--area", default="")
    p.add_argument("--out", default="uploads/datewatch-preview")
    sub.add_parser("plan")
    a = ap.parse_args()
    if a.cmd == "plan":
        from app.modules.calendar.config import uploads_dir
        from app.modules.calendar.store import Store
        db = _db()
        n = asyncio.run(dr.autoplan(db, Store(db), date.today(), uploads_dir(), say=print))
        print(f"{n} rows planned. Approve them in Studio > Calendar; nothing posts before that.")
        return 0
    cands, as_of = asyncio.run(_cands())
    if a.cmd == "list":
        rows = dr.board_rows(cands, a.area)
        print(f"{len(cands)} qualifying projects (booked homes, date ahead); board for {a.area or 'all of Pune'}:")
        for c in rows:
            print("  " + _row(c))
        more = [c for c in cands if c["net"] >= dr.MIN_NET_MONTHS and not c["review"] and (not a.area or c["area"] == a.area)]
        print(f"{len(more)} projects moved {dr.MIN_NET_MONTHS}+ months net. Next in line:")
        for c in more[len(rows):len(rows) + 12]:
            print("  " + _row(c))
        held = [c for c in dr.held_for_review(cands) if not a.area or c["area"] == a.area]
        print(f"{len(held)} held for the owner to check on MahaRERA (moved more than {dr.REVIEW_OVER_MONTHS} months):")
        for c in held:
            print("  " + _row(c))
        return 0
    reel = dr.board(cands, a.area, as_of)
    if reel is None:
        print("no board: fewer than", dr.MIN_BOARD, "projects")
        return 1
    out = Path(a.out)
    paths = area_reels.save_slides(reel, out / reel.key)
    mp4 = area_reels.render_video(paths, out / f"{reel.key}.mp4")
    print(reel.caption_ig, "\n", mp4)
    return 0


if __name__ == "__main__":
    sys.exit(main())
