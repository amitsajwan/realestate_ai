"""Launch House Deal on the new Avasetu Page and @avasetu_ (2026-10-03): the same carousels and reels, at most 3 posts a day.

  cd backend && PYTHONPATH=. python scripts/house_deal_launch.py [--dry-run]

The first post (the comparison carousel) and the first reel go out at once (approved, due now) so the owner can see them appear;
the rest are added as "planned" for the owner to approve in Studio > Calendar. New slugs (hd-...), so rows made for the old Page
are never reused; still-open rows for the old Page are skipped. Uses the files house_deal_golive.py rendered under
uploads/agentprojects/house-deal/. Idempotent per (slug, channel).
"""
import argparse
import asyncio
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.agentprojects import cards  # noqa: E402
from app.modules.agentprojects.service import ProjectService  # noqa: E402
from scripts.house_deal_content import AGENT  # noqa: E402
from scripts.house_deal_golive import FOLDER, IST, captions, compare_caption  # noqa: E402

SLUG = "house-deal"
CHANNELS = ("instagram", "facebook_page")


def plan(projects: dict, today) -> list:
    """(slug, kind, project slug or 'compare', IST datetime or None for 'now', approved?)"""
    d = lambda n, h, m=0: datetime.combine(today + timedelta(days=n), time(h, m), tzinfo=IST)  # noqa: E731
    return [
        ("hd-compare", "post", "compare", None, True),
        ("hd-amco-equa-reel", "reel", "amco-equa", None, True),
        ("hd-amco-equa", "post", "amco-equa", d(0, 19, 30), False),
        ("hd-anshul-medora", "post", "anshul-medora", d(1, 11), False),
        ("hd-rohan-abhilasha", "post", "rohan-abhilasha", d(1, 15), False),
        ("hd-anshul-medora-reel", "reel", "anshul-medora", d(1, 19), False),
        ("hd-triaa-kosmic-kourtyard", "post", "triaa-kosmic-kourtyard", d(2, 11), False),
        ("hd-goyal-my-home", "post", "goyal-my-home", d(2, 15), False),
        ("hd-rohan-abhilasha-reel", "reel", "rohan-abhilasha", d(2, 19), False),
        ("hd-triaa-kosmic-kourtyard-reel", "reel", "triaa-kosmic-kourtyard", d(3, 19), False),
        ("hd-goyal-my-home-reel", "reel", "goyal-my-home", d(4, 19), False),
    ]


async def launch(db, site: str, now: datetime, dry: bool, log=print) -> int:
    from app.modules.calendar.store import Store
    profile = await db.get_collection("agent_public_profiles").find_one({"slug": SLUG})
    agent_id = profile["agent_id"]
    projects = {p.slug: p.model_dump(mode="json") for p in await ProjectService(db).list_for_owner(agent_id)}
    store = Store(db)
    rows = await store.all()
    old = [r for r in rows if r["slug"].startswith("house-deal-") and r["status"] in ("planned", "approved", "scheduled")]
    have = {(r["slug"], r["channel"]) for r in rows}
    if not dry:
        for r in old:
            await store.skip(r["_id"], "replaced by the launch on the new Avasetu Page (hd-* rows)")
    log(f"old-Page rows skipped: {len(old)}")
    added = 0
    for slug, kind, ref, when, approved in plan(projects, now.astimezone(IST).date()):
        if ref == "compare":
            ig, fb = captions(compare_caption(list(projects.values())), site)
            images = [f"{FOLDER}/compare-{k}.jpg" for k in range(1, 8)]
        else:
            ig, fb = captions(cards.caption(projects[ref], AGENT), site, ref)
            images = [f"{FOLDER}/{ref}-{k}.jpg" for k in range(1, 6)]
        due = now - timedelta(minutes=1) if when is None else when.astimezone(timezone.utc)
        for ch in CHANNELS:
            if (slug, ch) in have:
                continue
            caption = ig if ch == "instagram" else fb
            imgs = [] if kind == "reel" else (images if ch == "instagram" else images[:1])
            log(f"  {'APPROVED' if approved else 'planned':<8} {ch:<13} {kind:<4} "
                f"{'now' if when is None else when.strftime('%a %d %b %H:%M IST'):<20} {slug}")
            if dry:
                continue
            await store.add(slug, ch, caption, imgs[0] if imgs else "", due, kind=kind, status="approved" if approved else "planned",
                            images=imgs, video=f"{FOLDER}/{ref}.mp4" if kind == "reel" else None,
                            creative={"source": "agentprojects", "reel_key": slug}, extra={"agent_id": agent_id})
            added += 1
    return added


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    n = await launch(db, settings.public_site_url, datetime.now(timezone.utc), a.dry_run)
    print(f"done: {n} rows added")


if __name__ == "__main__":
    asyncio.run(_main())
