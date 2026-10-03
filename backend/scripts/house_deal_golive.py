"""House Deal said yes (relayed by the owner, 2026-10-03): take the preview live and queue their posts for the owner's approval.

  cd backend && PYTHONPATH=. python scripts/house_deal_golive.py --dry-run     # print the plan, write nothing
  cd backend && PYTHONPATH=. python scripts/house_deal_golive.py              # do it (idempotent)

What it does:
1. Removes branding_data.preview: /agent/house-deal is a normal public agent site (indexable, no PREVIEW note).
2. Records House Deal's consent on their concierge record (the standard consent text; recorded by the owner).
3. Re-reads every project from MahaRERA, then renders the carousels and reels under uploads/agentprojects/house-deal/.
4. Adds calendar rows with status "planned": NOTHING publishes until the owner approves each row in Studio > Calendar.
   Comparison carousel first, then one project a day (Instagram carousel + Facebook post), then one reel a day on Instagram.
   Each row carries agent_id, so "I am interested" taps go to House Deal's inbox.
No invite code is issued here: the owner issues one from Studio > Agents with Mohini's mobile.
"""
import argparse
import asyncio
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable, List, Tuple

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.agentprojects import cards  # noqa: E402
from app.modules.agentprojects.service import ProjectError, ProjectService  # noqa: E402
from app.modules.concierge.service import CONSENT_TEXT  # noqa: E402
from scripts.house_deal_content import AGENT, render  # noqa: E402
from scripts.house_deal_preview import NAME, PROJECTS, SLUG  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
FOLDER = f"agentprojects/{SLUG}"  # under uploads/
POST_AT = time(18, 30)  # evening slot, IST
REEL_AT = time(12, 30)
CONSENT_NOTE = "verbal OK from House Deal after the pitch, relayed by the owner on 2026-10-03"


def at(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=IST).astimezone(timezone.utc)


def site_link(site: str, slug: str = "") -> str:
    return f"{site.rstrip('/')}/agent/{SLUG}" + (f"/projects/{slug}" if slug else "")


def captions(cap: str, site: str, slug: str = "") -> Tuple[str, str]:
    """(instagram, facebook) captions: 'Listed by House Deal' and where to see every fact."""
    by = f"Listed by {NAME}."
    ig = f"{cap}\n\n{by} Every fact with its source: link in our bio."
    fb = f"{cap}\n\n{by} Every fact with its source: {site_link(site, slug)}"
    return ig, fb


def compare_caption(projects: List[dict]) -> str:
    lo = min(p["price_min"] for p in projects)
    hi = max(p["price_max"] or p["price_min"] for p in projects)
    lines = [f"{len(projects)} projects in {cards.area_label(projects).replace(' · Pune', '')}, {cards.lakh(lo)} to {cards.lakh(hi)}, "
             "side by side: price, MahaRERA completion date and how many homes are already booked."]
    for p in projects:
        r = p["rera"]
        lines.append(f"• {p['name']}: from {cards.lakh(p['price_min'])}, MahaRERA date {cards.day(r['completion_now'])}, "
                     f"{p['booked_pct']}% booked")
    lines += ["Plan around the MahaRERA date, not the brochure date.",
              f"Prices as quoted by {NAME}; dates and bookings from MahaRERA's public record.",
              "Which one fits your budget? Comment the project name.",
              "#Pune #Wagholi #UpperKharadi #NewProjects #MahaRERA"]
    return "\n\n".join(lines)


def plan_rows(projects: List[dict], made: dict, start: date, site: str) -> List[dict]:
    """Calendar rows (not yet stored). One comparison post, then one project a day, then one reel a day."""
    rows = []
    ig, fb = captions(compare_caption(projects), site)
    imgs = [f"{FOLDER}/{f}" for f in made["compare"]]
    rows += [dict(slug=f"{SLUG}-compare", channel="instagram", caption=ig, images=imgs, due=at(start, POST_AT), kind="post"),
             dict(slug=f"{SLUG}-compare", channel="facebook_page", caption=fb, images=imgs[:1], due=at(start, POST_AT), kind="post")]
    for k, p in enumerate(projects, 1):
        d = start + timedelta(days=k)
        ig, fb = captions(cards.caption(p, AGENT), site, p["slug"])
        imgs = [f"{FOLDER}/{f}" for f in made["projects"][p["slug"]]]
        rows += [dict(slug=f"{SLUG}-{p['slug']}", channel="instagram", caption=ig, images=imgs, due=at(d, POST_AT), kind="post"),
                 dict(slug=f"{SLUG}-{p['slug']}", channel="facebook_page", caption=fb, images=imgs[:1], due=at(d, POST_AT), kind="post")]
    for k, p in enumerate(projects, 1):
        if p["slug"] not in made.get("reels", {}):
            continue
        d = start + timedelta(days=len(projects) + k)
        ig, _ = captions(cards.caption(p, AGENT), site, p["slug"])
        rows.append(dict(slug=f"{SLUG}-{p['slug']}-reel", channel="instagram", caption=ig, images=[], due=at(d, REEL_AT), kind="reel",
                         video=f"{FOLDER}/{made['reels'][p['slug']]}"))
    return rows


async def queue(store, rows: List[dict], agent_id: str, log: Callable[[str], None]) -> int:
    """Add the rows as 'planned' (owner approval needed); a (slug, channel) already in the calendar is left alone."""
    have = {(d["slug"], d["channel"]) for d in await store.all()}
    added = 0
    for r in rows:
        if (r["slug"], r["channel"]) in have:
            continue
        await store.add(r["slug"], r["channel"], r["caption"], r["images"][0] if r["images"] else "", r["due"], kind=r["kind"],
                        status="planned", images=r["images"], video=r.get("video"),
                        creative={"source": "agentprojects", "reel_key": r["slug"]}, extra={"agent_id": agent_id})
        added += 1
        log(f"  planned {r['channel']:<13} {r['kind']:<5} {r['due'].astimezone(IST):%a %d %b %H:%M} IST  {r['slug']}")
    return added


async def go_live(db, uploads: Path, site: str, start: date, now: datetime, reels: bool, log: Callable[[str], None],
                  check: bool = True) -> dict:
    profiles = db.get_collection("agent_public_profiles")
    profile = await profiles.find_one({"slug": SLUG})
    if not profile:
        raise SystemExit(f"/agent/{SLUG} does not exist: run scripts/house_deal_preview.py first")
    agent_id = profile["agent_id"]
    branding = {k: v for k, v in (profile.get("branding_data") or {}).items() if k != "preview"}
    await profiles.update_one({"_id": profile["_id"]}, {"$set": {"branding_data": branding, "updated_at": now}})
    log("site: preview flag removed, /agent/house-deal is public")

    agents = db.get_collection("concierge_agents")
    rec = await agents.find_one({"_id": agent_id})
    if rec and not (rec.get("consent") or {}).get("given"):
        await agents.update_one({"_id": agent_id}, {"$set": {"consent": {"given": True, "text": CONSENT_TEXT, "at": now,
                                                                         "recorded_by": "owner", "note": CONSENT_NOTE}}})
        await db.get_collection("concierge_audit").insert_one({"at": now, "by": "owner", "action": "consent.give",
                                                                "agent_id": agent_id, "keys": ["consent"], "note": CONSENT_NOTE})
        log("consent recorded")

    svc = ProjectService(db)
    for slug in PROJECTS if check else ():
        try:
            await svc.check_maharera(agent_id, slug)
        except ProjectError as e:
            log(f"  {slug}: MahaRERA check failed ({e}); keeping the last reading")
    projects = [p.model_dump(mode="json") for p in await svc.list_for_owner(agent_id)]
    made = render(projects, Path(uploads) / FOLDER, reels=reels)
    log(f"content: {sum(len(v) for v in made['projects'].values()) + len(made['compare'])} slides, {len(made['reels'])} reels")

    from app.modules.calendar.store import Store
    added = await queue(Store(db), plan_rows(projects, made, start, site), agent_id, log)
    log(f"calendar: {added} rows planned; approve them in Studio > Calendar")
    return {"agent_id": agent_id, "planned": added}


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--start", default="", help="first posting day, YYYY-MM-DD (default: tomorrow, IST)")
    ap.add_argument("--no-reels", action="store_true")
    a = ap.parse_args()
    start = date.fromisoformat(a.start) if a.start else (datetime.now(IST) + timedelta(days=1)).date()
    from app.core.config import settings
    if a.dry_run:
        print(f"would: remove the preview flag, record consent, re-read MahaRERA, render to uploads/{FOLDER}, "
              f"plan {2 + 2 * len(PROJECTS) + (0 if a.no_reels else len(PROJECTS))} calendar rows from {start} (status planned)")
        return
    from motor.motor_asyncio import AsyncIOMotorClient
    db = AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]
    out = await go_live(db, Path(settings.upload_directory), settings.public_site_url, start, datetime.now(timezone.utc),
                        not a.no_reels, print)
    print(f"done: agent {out['agent_id']}, {out['planned']} rows waiting for approval")


if __name__ == "__main__":
    asyncio.run(_main())
