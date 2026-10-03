"""Content calendar admin. NOTHING is published until you approve it.

  python scripts/calendar_admin.py plan --start 2026-10-12 --weeks 4 [--llm] [--include-local-languages] [--render-reels]
        make the creative for every slot and store it as `planned` (images go to uploads/calendar/); needs MongoDB
  python scripts/calendar_admin.py preview-plan [--week N] [--out DIR]     one contact sheet per week + all captions, to review before approving
  python scripts/calendar_admin.py approve --all | --week N | <id>          planned -> approved (the runner may then publish it at its time)
  python scripts/calendar_admin.py skip <id>                                 drop one item
  python scripts/calendar_admin.py list [--status planned|approved|published|failed|skipped]
  python scripts/calendar_admin.py status
  python scripts/calendar_admin.py --dry-check                               run the caption guards over the library (exit 1 on any problem)
  python scripts/calendar_admin.py preview-offline --start 2026-10-12 --weeks 4 --out DIR   (no database) plan, render and sheet in a folder
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py plan --start 2026-10-12 --weeks 4 --llm
"""
import argparse
import asyncio
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.calendar import builder, guards, library, preview, schedule  # noqa: E402
from app.modules.calendar.config import load as load_config  # noqa: E402
from app.modules.calendar.config import uploads_dir  # noqa: E402

IST = schedule.IST


def _ist(dt: datetime) -> str:
    return preview.ist(dt)


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


async def _store():
    from app.core.database import get_database, init_database
    from app.modules.calendar.store import Store
    try:
        return Store(get_database())
    except RuntimeError:  # scripts run outside the app lifespan: connect first
        await init_database()
        return Store(get_database())


def _llm(use: bool):
    if not use:
        return None
    from app.platform.llm import default_llm
    llm = default_llm()
    if llm is None:
        print("no LLM key configured (GROQ_API_KEY): using the deterministic path for every item")
    return llm


async def plan(store, start: date, weeks: int, use_llm: bool, include_local: bool, render_reels: bool, uploads: Path) -> list:
    made = await builder.build_and_store(store, start, weeks, uploads, _llm(use_llm), include_local, render_reels, say=print)
    print(f"{len(made)} item(s) planned (status `planned`: nothing posts until you approve). Next: preview-plan, then approve.")
    return made


async def preview_plan(store, out: Path, week, uploads: Path) -> dict:
    docs = [d for d in await store.all() if d["status"] in ("planned", "approved", "scheduled") and (week is None or d.get("week") == week)]
    paths = preview.write_preview(docs, uploads, out)
    for w, p in paths.items():
        print(f"week {w}: {p}")
    print(f"captions: {out}/week-N-captions.txt")
    return paths


async def approve(store, id, week, all_: bool) -> int:
    n = 0
    for d in await store.all():
        if d["status"] != "planned":
            continue
        if all_ or (week is not None and d.get("week") == week) or d["_id"] == id:
            n += int(await store.approve(d["_id"]))
    print(f"{n} item(s) approved")
    return n


async def list_rows(store, status) -> None:
    for d in await store.listing(status):
        print(f"{d['_id']}  {_ist(d['due_at'])}  w{d.get('week') or '-'}  {d['channel']:13} {d.get('kind', 'post'):8} {d['status']:9} {d['slug']}"
              + (f"  ERROR: {d['error']}" if d.get("error") else ""))


async def skip(store, id: str) -> None:
    print("skipped" if await store.skip(id) else "not found, or already published/skipped")


async def status(store) -> None:
    cfg = load_config()
    from app.modules.social.config import load as load_social
    run = await store.get_run()
    print(f"enabled={cfg.enabled} dry_run={load_social().dry_run} counts={await store.counts()}")
    print(f"last_run_at={run.get('last_run_at')} last_counts={run.get('last_counts')} last_error={run.get('last_error')}")
    for d in await store.upcoming(3):
        print(f"next: {_ist(d['due_at'])} {d['channel']} {d.get('kind', 'post')} {d['slug']} [{d['status']}]")


async def offline(start: date, weeks: int, out: Path, use_llm: bool, include_local: bool, render_reels: bool) -> None:
    """Plan into an in-memory store and write the contact sheets: for design review without a database."""
    import importlib
    FakeDb = importlib.import_module("tests.modules.fakes").FakeDb
    from app.modules.calendar.store import Store
    store = Store(FakeDb())
    uploads = out / "uploads"
    await plan(store, start, weeks, use_llm, include_local, render_reels, uploads)
    await preview_plan(store, out / "sheets", None, uploads)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", choices=["plan", "preview-plan", "approve", "skip", "list", "status", "preview-offline"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--start", default=None, help="first day (default: next Monday)")
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--llm", action="store_true", help="use the real LLM in the creative studio; each item falls back to the deterministic path on failure")
    ap.add_argument("--include-local-languages", action="store_true", help="also plan the Hindi and Marathi agent posts (have a native reader approve first)")
    ap.add_argument("--render-reels", action="store_true", help="render the reel videos now instead of in the runner's pre-render step (about a minute each)")
    ap.add_argument("--out", default=str(uploads_dir() / "calendar-preview"))
    ap.add_argument("--status", default=None)
    ap.add_argument("--dry-check", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # captions hold emoji and Devanagari; a Windows console is not UTF-8 by default
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.WARNING)
    if a.dry_check:
        return dry_check()
    if a.mode is None:
        ap.error("choose a mode or --dry-check")
    if a.start:
        start = date.fromisoformat(a.start)
    else:
        today = date.today()
        start = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    uploads = uploads_dir()

    async def go():
        if a.mode == "preview-offline":
            return await offline(start, a.weeks, Path(a.out), a.llm, a.include_local_languages, a.render_reels)
        store = await _store()
        if a.mode == "plan":
            if dry_check():
                print("refusing to plan: fix the guard failures first")
                return 1
            await plan(store, start, a.weeks, a.llm, a.include_local_languages, a.render_reels, uploads)
        elif a.mode == "preview-plan":
            await preview_plan(store, Path(a.out), a.week, uploads)
        elif a.mode == "approve":
            if not (a.all or a.week is not None or a.id):
                ap.error("approve needs --all, --week N or an id")
            await approve(store, a.id, a.week, a.all)
        elif a.mode == "skip":
            if not a.id:
                ap.error("skip needs an id")
            await skip(store, a.id)
        elif a.mode == "list":
            await list_rows(store, a.status)
        else:
            await status(store)
        return 0

    return asyncio.run(go()) or 0


if __name__ == "__main__":
    sys.exit(main())
