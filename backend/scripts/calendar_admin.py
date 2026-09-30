"""Content calendar admin.

  python scripts/calendar_admin.py preview [--out DIR] [--start 2026-10-06 --weeks 8]   render every card (no network, no database) and print the schedule with captions
  python scripts/calendar_admin.py --dry-check                                             run the safety guards over every caption (exit 1 on any problem)
  python scripts/calendar_admin.py seed --start 2026-10-06 --weeks 8                       write scheduled rows (idempotent; needs MongoDB)
  python scripts/calendar_admin.py list [--status scheduled|published|failed|skipped]
  python scripts/calendar_admin.py skip <id>
  python scripts/calendar_admin.py status
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py seed --start 2026-10-06 --weeks 8
"""
import argparse
import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.calendar import guards, library, render, schedule  # noqa: E402
from app.modules.calendar.config import load as load_config  # noqa: E402
from app.modules.calendar.config import uploads_dir  # noqa: E402

IST = schedule.IST


def caption_for(entry, channel: str) -> str:
    return entry.ig_caption if channel == "instagram" else entry.fb_caption


def layout(start: date, weeks: int, existing=()):
    return schedule.build_schedule(library.ENTRIES, start, weeks, existing=existing)


def _ist(dt: datetime) -> str:
    return (dt if dt.tzinfo else dt.replace(tzinfo=schedule.timezone.utc)).astimezone(IST).strftime("%a %d %b %H:%M IST")


def dry_check() -> int:
    bad = guards.check_all(library.ENTRIES)
    slugs = [e.slug for e in library.ENTRIES]
    if len(set(slugs)) != len(slugs):
        bad["_slugs"] = ["duplicate slugs"]
    for slug, problems in bad.items():
        for p in problems:
            print(f"FAIL {slug}: {p}")
    print(f"{len(library.ENTRIES)} posts checked, {sum(len(v) for v in bad.values())} problem(s)")
    return 1 if bad else 0


def preview(out: Path, start: date, weeks: int) -> None:
    paths = render.render_all(out)
    print(f"rendered {len(paths)} cards into {out} (square for Facebook, ig/ portrait 1080x1350 for Instagram)")
    for s in layout(start, weeks):
        e = library.BY_SLUG[s.slug]
        print(f"\n===== {_ist(s.due_at)}  {s.channel}  [{e.pillar}] {s.slug} =====\n{caption_for(e, s.channel)}")


async def _store():
    from app.core.database import get_database
    from app.modules.calendar.store import Store
    return Store(get_database())


async def seed(start: date, weeks: int) -> None:
    store = await _store()
    slots = layout(start, weeks, await store.existing())
    for s in slots:
        e = library.BY_SLUG[s.slug]
        await store.add(s.slug, s.channel, caption_for(e, s.channel), render.image_path(s.slug, s.channel), s.due_at)
        print(f"scheduled {_ist(s.due_at)}  {s.channel:13} {s.slug}")
    print(f"{len(slots)} new row(s) written")


async def list_rows(status) -> None:
    for d in await (await _store()).listing(status):
        print(f"{d['_id']}  {_ist(d['due_at'])}  {d['channel']:13} {d['status']:9} {d['slug']}" + (f"  ERROR: {d['error']}" if d.get("error") else ""))


async def skip(id: str) -> None:
    print("skipped" if await (await _store()).skip(id) else "not found or not scheduled")


async def status() -> None:
    store = await _store()
    cfg = load_config()
    from app.modules.social.config import load as load_social
    run = await store.get_run()
    print(f"enabled={cfg.enabled} dry_run={load_social().dry_run} counts={await store.counts()}")
    print(f"last_run_at={run.get('last_run_at')} last_counts={run.get('last_counts')} last_error={run.get('last_error')}")
    nxt = await store.upcoming(3)
    for d in nxt:
        print(f"next: {_ist(d['due_at'])} {d['channel']} {d['slug']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", choices=["preview", "seed", "list", "skip", "status"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--start", default="2026-10-06")
    ap.add_argument("--weeks", type=int, default=8)
    ap.add_argument("--out", default=str(uploads_dir() / "calendar-preview"))
    ap.add_argument("--status", default=None)
    ap.add_argument("--dry-check", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # captions hold emoji and Devanagari; a Windows console is not UTF-8 by default
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.dry_check:
        return dry_check()
    if a.mode is None:
        ap.error("choose a mode or --dry-check")
    start = date.fromisoformat(a.start)
    if a.mode == "preview":
        preview(Path(a.out), start, a.weeks)
    elif a.mode == "seed":
        if dry_check():
            print("refusing to seed: fix the guard failures first")
            return 1
        asyncio.run(seed(start, a.weeks))
    elif a.mode == "list":
        asyncio.run(list_rows(a.status))
    elif a.mode == "skip":
        if not a.id:
            ap.error("skip needs an id")
        asyncio.run(skip(a.id))
    else:
        asyncio.run(status())
    return 0


if __name__ == "__main__":
    sys.exit(main())
