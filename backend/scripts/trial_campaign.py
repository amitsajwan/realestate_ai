"""Free-trial campaign week (organic, nothing paid): one new agent-recruitment post or reel a day, 19:30 IST, Facebook + Instagram.

Oct 10-11 are the agent reels A3 and B3 (already approved, scripts/agent_reels.py). This adds Oct 12-16:
  Sun 12  post  agent-consistent-posting   "Too busy showing flats to keep posting?"
  Mon 13  reel  E1                         details message -> ready post (reels/transform_reels.py)
  Tue 14  post  agent-buyer-summary        "Which enquiry is serious? Know at a glance"
  Wed 15  reel  E2                         many properties, all their posts in one place
  Thu 16  post  agent-hindi                the Hindi offer card "एक प्रॉपर्टी दीजिए, पूरा मार्केटिंग कैंपेन पाइए"

  PYTHONPATH=. python scripts/trial_campaign.py plan [--start 2026-10-12] [--time 19:30]

Rows are PLANNED: nothing posts until the owner approves each one in Studio > Calendar. Facebook links carry ?src=camp_<slug>_fb
so a request can be traced to its post; the reels use the agent-reel tags (reel_e1_fb). Re-running skips rows already there.
On the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/trial_campaign.py plan
"""
import argparse
import asyncio
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

CHANNELS = ("facebook_page", "instagram")
DAYS = (("post", "agent-consistent-posting"), ("reel", "E1"), ("post", "agent-buyer-summary"), ("reel", "E2"), ("post", "agent-hindi"))


def post_caption(entry, channel: str) -> str:
    if channel == "instagram":
        return entry.ig_caption
    return entry.fb_caption.replace("/trial", f"/trial?src=camp_{entry.slug.replace('-', '_')}_fb")


async def plan(start: date, at: time, say=print) -> int:
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    from app.modules.calendar.config import uploads_dir
    from app.modules.calendar.library import BY_SLUG
    from app.modules.calendar.render import ensure_card
    from app.modules.calendar.schedule import IST
    from app.modules.calendar.store import Store
    from app.modules.reels import transform_reels as tr

    store = Store(AsyncIOMotorClient(settings.mongodb_url)[settings.database_name])
    uploads = uploads_dir()
    have = {(ch, slug) for ch, slug, _ in await store.existing()}
    n = 0
    for i, (kind, ref) in enumerate(DAYS):
        due = datetime.combine(start + timedelta(days=i), at, IST)
        for ch in CHANNELS:
            if kind == "reel":
                s = tr.BY_CODE[ref]
                slug = f"agent-reel-{ref.lower()}"
                creative = {"role": "agent", "source": "agent_reels", "template": "agent", "reel_key": slug.replace("agent-reel-", "agent-"),
                            "ref": ref, "reel_code": ref, "group": "before_after", "theme": s.theme, "hook": s.hook.replace("*", ""),
                            "layout": "reel", "ok": True, "path": "transform_reels", "campaign": "trial-week-1",
                            "script": [s.hook, s.input_line, s.screen_line, s.output_line, s.result]}
                args = (slug, ch, tr.caption(ref, ch), "", due)
                extra = dict(kind="reel", creative=creative)
            else:
                e = BY_SLUG[ref]
                slug = ref
                img = str(ensure_card(e, uploads, ch).relative_to(uploads)).replace("\\", "/")
                creative = {"role": "agent", "source": "library", "layout": "card", "ok": True, "campaign": "trial-week-1"}
                args = (slug, ch, post_caption(e, ch), img, due)
                extra = dict(kind="post", images=[img], creative=creative)
            if (ch, slug) in have:
                say(f"{slug} {ch}: already in the calendar")
                continue
            await store.add(*args, status="planned", **extra)
            n += 1
            say(f"{due.isoformat()[:16]} IST {ch:13} {kind:4} {slug}")
    say(f"{n} rows planned. Approve them in Studio > Calendar; nothing posts before that.")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--start", default="2026-10-12", help="first day, YYYY-MM-DD")
    p.add_argument("--time", default="19:30", help="IST, HH:MM")
    a = ap.parse_args()
    asyncio.run(plan(date.fromisoformat(a.start), time.fromisoformat(a.time)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
