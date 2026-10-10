"""Puzzle reels (app/modules/calendar/puzzle_reels.py): list them, preview them, put them in the content calendar.

  PYTHONPATH=. python scripts/puzzle_reels.py list
        every puzzle today's MahaRERA area stats support: question, options, answer
  PYTHONPATH=. python scripts/puzzle_reels.py preview [--out uploads/puzzlereels]
        draw and check the slides and render the MP4 of each, for review
  PYTHONPATH=. python scripts/puzzle_reels.py plan --start 2026-10-12 [--time 12:30] [--channels instagram facebook_page]
        add the puzzles to the calendar as PLANNED rows, one a day. Nothing posts until the owner approves each row in Studio.
On the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/puzzle_reels.py list
"""
import argparse
import asyncio
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.calendar import area_reels, puzzle_reels as pr  # noqa: E402


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    return AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]


async def _puzzles():
    return pr.puzzles(await pr.load_stats(_db()))


def cmd_list(reels) -> None:
    for r in reels:
        print(f"{r.key}  (as of {r.as_of})\n  {r.question}")
        for i, o in enumerate(r.options):
            print(f"  {pr.LETTERS[i]}) {o}{'   <- answer' if i == r.answer else ''}")
    print(f"{len(reels)} puzzles")


def cmd_preview(reels, out: Path) -> None:
    for r in reels:
        paths = area_reels.save_slides(r, out / r.key)
        mp4 = area_reels.render_video(paths, out / f"{r.key}.mp4")
        print(f"{r.key}: {mp4}")


async def plan(reels, start: date, at: time, channels, uploads: Path, say=print) -> int:
    from app.modules.calendar.schedule import IST
    from app.modules.calendar.store import Store
    store = Store(_db())
    have = {(ch, slug) for ch, slug, _ in await store.existing()}
    done = {slug.rsplit("-", 1)[0] for _, slug, _ in await store.existing() if slug.startswith("puzzle-")}
    n, day = 0, 0
    for r in reels:
        due_day = start + timedelta(days=day)
        slug = r.slug(due_day)
        if slug.rsplit("-", 1)[0] in done:
            say(f"{r.key}: already in the calendar")
            continue
        folder = uploads / area_reels.SUBDIR.replace("areareels", "puzzlereels") / slug
        images = [p.resolve().relative_to(uploads.resolve()).as_posix() for p in area_reels.save_slides(r, folder)]
        due = datetime.combine(due_day, at, IST)
        for ch in channels:
            if (ch, slug) in have:
                continue
            creative = {"role": "puzzle", "source": "puzzle_reels", "template": "puzzle", "reel_key": slug, "ref": r.key,
                        "path": "puzzle_reels", "layout": "reel", "ok": True, "hook": r.hook, "hook_type": "puzzle",
                        "slides": images, "script": r.script, "as_of": r.as_of, "answer": r.options[r.answer],
                        **({"area": r.area} if r.area else {})}
            await store.add(slug, ch, r.caption_ig if ch == "instagram" else r.caption_fb, images[0], due, kind="reel",
                            status="planned", images=images, creative=creative, extra={"area": r.area} if r.area else None)
            n += 1
            say(f"{r.key} {ch}: planned for {due.isoformat()[:16]} IST")
        day += 1
    say(f"{n} rows planned. Approve them in Studio > Calendar; nothing posts before that.")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("preview")
    p.add_argument("--out", default="uploads/puzzlereels")
    p = sub.add_parser("plan")
    p.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    p.add_argument("--time", default="12:30", help="IST, HH:MM")
    p.add_argument("--channels", nargs="+", default=["instagram", "facebook_page"], choices=["facebook_page", "instagram"])
    a = ap.parse_args()
    reels = asyncio.run(_puzzles())
    if a.cmd == "list":
        cmd_list(reels)
    elif a.cmd == "preview":
        cmd_preview(reels, Path(a.out))
    else:
        from app.modules.calendar.config import uploads_dir
        hh, mm = (int(x) for x in a.time.split(":"))
        asyncio.run(plan(reels, date.fromisoformat(a.start), time(hh, mm), a.channels, uploads_dir()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
