"""Trend reels (explainers that need no property of ours): render them, and optionally queue them for the owner's approval.

  cd backend && PYTHONPATH=. python scripts/trend_reels.py --out /tmp/trend            # render the mp4s, captions and a manifest; touches nothing else
  cd backend && PYTHONPATH=. python scripts/trend_reels.py --queue [--dry-run]         # also add them to the calendar as "planned"

Every figure comes from app/modules/reels/trend.py FACTS (dated, sourced) or its calculator. The reels that use `secondary` facts
(portal prices, stamp duty, GST) are listed with their sources: confirm them against the official pages BEFORE approving in Studio >
Calendar. Rows are "planned": nothing posts until the owner approves each one. The voice-over is used when GOOGLE_TTS_API_KEY is set.
"""
import argparse
import asyncio
import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.reels import trend  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
FOLDER = "calendar/trend"        # under uploads/
CHANNELS = ("instagram", "facebook_page")
SLOT = time(19, 0)               # evening, IST; one trend reel a day, from tomorrow


def render_all(out: Path, today: date) -> list:
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for r in trend.TRENDS:
        problems = trend.check(r, today)
        if problems:
            print(f"SKIPPED {r.slug}: {'; '.join(problems)}")
            continue
        mp4 = trend.render(r, out / f"{r.slug}.mp4", today=today)
        caps = trend.captions(r)
        manifest.append({
            "slug": r.slug, "video": mp4.name, "experiment": r.experiment, "variant": r.variant, "hook_type": r.hook_type,
            "engine": r.engine, "locality": r.locality, "price_band": r.price_band, "captions": caps,
            "facts": [{"id": f.id, "text": f.text, "source": f.source, "url": f.url, "as_of": f.as_of, "valid_until": f.valid_until,
                       "kind": f.kind} for f in (trend.FACTS[i] for i in r.facts)],
            "confirm_before_approving": [f.id for f in trend.secondary_facts(r)],
        })
        print(f"rendered {mp4}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


async def queue(db, manifest: list, out: Path, today: date, dry: bool, log=print) -> int:
    """Copy each video to uploads/calendar/trend and add "planned" rows (Instagram and Facebook) at one reel a day, from tomorrow."""
    from app.modules.calendar.config import uploads_dir
    from app.modules.calendar.store import Store
    store = Store(db)
    have = {(r["slug"], r["channel"]) for r in await store.all()}
    dest = uploads_dir() / FOLDER
    added = 0
    for n, m in enumerate(manifest):
        due = datetime.combine(today + timedelta(days=n + 1), SLOT, tzinfo=IST).astimezone(timezone.utc)
        for ch in CHANNELS:
            if (m["slug"], ch) in have:
                continue
            log(f"  planned {ch:<13} {due.astimezone(IST).strftime('%a %d %b %H:%M IST')}  {m['slug']}"
                + (f"   CONFIRM FIRST: {', '.join(m['confirm_before_approving'])}" if m["confirm_before_approving"] else ""))
            if dry:
                continue
            dest.mkdir(parents=True, exist_ok=True)
            (dest / m["video"]).write_bytes((out / m["video"]).read_bytes())
            cover = (out / m["video"]).with_name(Path(m["video"]).stem + "-cover.jpg")
            if cover.is_file():
                (dest / cover.name).write_bytes(cover.read_bytes())
            await store.add(m["slug"], ch, m["captions"]["instagram" if ch == "instagram" else "facebook"], "", due, kind="reel",
                            status="planned", video=f"{FOLDER}/{m['video']}",
                            creative={"source": "trend_reels", "reel_key": m["slug"], "hook": m["captions"]["facebook"].splitlines()[0],
                                      "experiment": m["experiment"], "variant": m["variant"], "hook_type": m["hook_type"],
                                      "engine": m["engine"], "locality": m["locality"], "price_band": m["price_band"]})
            added += 1
    return added


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="trend-reels")
    ap.add_argument("--queue", action="store_true", help="add the reels to the calendar as planned rows")
    ap.add_argument("--dry-run", action="store_true", help="with --queue: print the rows, write nothing")
    a = ap.parse_args()
    today = datetime.now(IST).date()
    out = Path(a.out)
    manifest = render_all(out, today)
    for m in manifest:
        if m["confirm_before_approving"]:
            print(f"CONFIRM before approving {m['slug']}: " + ", ".join(m["confirm_before_approving"]))
            for f in m["facts"]:
                if f["kind"] == "secondary":
                    print(f"    {f['id']}: {f['source']} ({f['url']}), {f['as_of']}")
    if a.queue:
        from motor.motor_asyncio import AsyncIOMotorClient

        from app.core.config import settings
        db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
        n = await queue(db, manifest, out, today, a.dry_run)
        print(f"done: {n} rows {'would be ' if a.dry_run else ''}added")


if __name__ == "__main__":
    asyncio.run(_main())
