"""Agent-recruitment reels (app/modules/reels/agent_reels.py): check them, preview them, put them in the content calendar, report.

  PYTHONPATH=. python scripts/agent_reels.py check
        the script checks (claims, hook length, screens); no rendering
  PYTHONPATH=. python scripts/agent_reels.py preview [--codes A1 B2] [--out uploads/agentreels]
        render the MP4s (about 40 s each) and a contact sheet per reel: for review, or to share in WhatsApp/Facebook groups by hand
  PYTHONPATH=. python scripts/agent_reels.py plan --start 2026-10-06 [--time 19:30] [--channels facebook_page instagram]
        add the 10 reels to the calendar as PLANNED rows, one a day in ORDER. Nothing posts until the owner approves each row in
        Studio. Default channel: the Facebook Page only (the Instagram account's followers are mostly buyers).
  PYTHONPATH=. python scripts/agent_reels.py report [--no-insights]
        per reel: views, average watch time as a share of the reel, agent comments answered, invite requests, sign-ups, first property.
        Instagram's 1/3/5-second retention is NOT in the API: read the hold / skip rate in the Instagram app and note it by hand.
On the server (plan, report):  docker compose exec -T -e PYTHONPATH=. backend python scripts/agent_reels.py report
"""
import argparse
import asyncio
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.reels import agent_reels as ar  # noqa: E402

REEL_SECONDS = 11.4  # every agent reel has the same five scenes


def cmd_check(_) -> int:
    bad = [p for s in ar.SCRIPTS for p in ar.check_script(s)]
    print("\n".join(bad) if bad else f"all {len(ar.SCRIPTS)} scripts pass")
    return 1 if bad else 0


def cmd_preview(a) -> int:
    from app.modules.reels import compose, ffmpeg
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for code in a.codes or ar.ORDER:
        mp4 = ar.render(code, out / f"agent-{code.lower()}.mp4")
        compose.contact_sheet(mp4, out / f"agent-{code.lower()}-sheet.png")
        p = ffmpeg.probe(mp4)
        print(f"{code}: {mp4} {p.duration:.1f}s {p.size_bytes / 1e6:.1f} MB  hook: {ar.BY_CODE[code].hook.replace('*', '')}")
    return 0


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    return AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]


def plan_rows(start: date, at: time, channels) -> list:
    """(slug, channel, caption, due, creative) for every reel and channel, one reel a day in ORDER."""
    from app.modules.calendar.schedule import IST
    rows = []
    for i, code in enumerate(ar.ORDER):
        s = ar.BY_CODE[code]
        due = datetime.combine(start + timedelta(days=i), at, IST)
        for ch in channels:
            creative = {"role": "agent", "source": "agent_reels", "template": "agent", "reel_key": f"agent-{code.lower()}", "ref": code,
                        "reel_code": code, "group": s.group, "theme": s.theme, "hook": s.hook.replace("*", ""), "layout": "reel",
                        "ok": True, "path": "agent_reels", "script": [s.hook, s.pain, s.screen_line, s.result]}
            rows.append((f"agent-reel-{code.lower()}", ch, ar.caption(code, ch), due, creative))
    return rows


async def plan(store, start: date, at: time, channels, say=print) -> int:
    have = {(ch, slug) for ch, slug, _ in await store.existing()}
    n = 0
    for slug, ch, caption, due, creative in plan_rows(start, at, channels):
        code = creative["reel_code"]
        if (ch, slug) in have:
            say(f"{code} {ch}: already in the calendar")
            continue
        await store.add(slug, ch, caption, "", due, kind="reel", status="planned", creative=creative)
        n += 1
        say(f"{code} {ch}: planned for {due.isoformat()[:16]} IST ({creative['group']}: {creative['theme']})")
    say(f"{n} rows planned. Approve them in Studio > Calendar; nothing posts before that.")
    return n


async def _insights(doc, cfg) -> dict:
    """Views and watch time from the Graph API for a published Instagram reel (a Facebook Page reel: views only)."""
    import httpx
    ext = doc.get("external_id")
    if not ext or not cfg.page_token:
        return {}
    url = f"https://graph.facebook.com/{cfg.graph_version}/{ext}"
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            if doc["channel"] == "instagram":
                r = await c.get(url + "/insights", params={"metric": "views,reach,shares,saved,ig_reels_avg_watch_time",
                                                           "access_token": cfg.page_token})
                vals = {m["name"]: (m.get("values") or [{}])[0].get("value") for m in (r.json().get("data") or [])}
                avg = (vals.get("ig_reels_avg_watch_time") or 0) / 1000
                return {"views": vals.get("views"), "watched": f"{avg:.1f}s {100 * avg / REEL_SECONDS:.0f}%" if avg else "-"}
            r = await c.get(url, params={"fields": "views", "access_token": cfg.page_token})
            return {"views": r.json().get("views", "-")}
    except Exception as e:  # insights are a nice-to-have; never print the token
        return {"views": f"err:{type(e).__name__}"}


async def report(a) -> None:
    from app.platform.meta_graph.config import load as load_social
    db = _db()
    rows = await db.get_collection("content_calendar").find({"creative.source": "agent_reels"}).to_list(None)
    ids = {r["_id"]: r["creative"]["reel_code"] for r in rows}
    comments = [{**c, "reel_code": ids.get(c.get("calendar_id"))}
                for c in await db.get_collection("engage_comments").find({"calendar_id": {"$in": list(ids)}}).to_list(None)]
    requests = await db.get_collection("invite_requests").find({"source": {"$regex": "^reel_"}}).to_list(None)
    users = await db.get_collection("users").find({}, {"phone": 1}).to_list(None)
    listings = await db.get_collection("listings").find({}, {"agent_id": 1}).to_list(None)
    f = ar.funnel(comments, requests, users, listings)
    cfg = load_social()
    print(f"{'code':4} {'group':12} {'channel':13} {'status':11} {'views':>6} {'watched':>10} | {'cmts':>4} {'req':>4} {'join':>4} {'prop':>4}  hook")
    for code in ar.ORDER:
        s = ar.BY_CODE[code]
        mine = sorted((r for r in rows if r["creative"]["reel_code"] == code), key=lambda r: r["channel"]) or [None]
        for k, r in enumerate(mine):
            ins = await _insights(r, cfg) if (r and r["status"] == "published" and not a.no_insights) else {}
            fu = f[code] if k == 0 else {}
            print(f"{code:4} {s.group:12} {(r or {}).get('channel', '-'):13} {(r or {}).get('status', 'not planned'):11} "
                  f"{str(ins.get('views', '-')):>6} {str(ins.get('watched', '-')):>10} | "
                  f"{str(fu.get('comments', '')):>4} {str(fu.get('requests', '')):>4} {str(fu.get('signed_up', '')):>4} "
                  f"{str(fu.get('added_property', '')):>4}  {s.hook.replace('*', '') if k == 0 else ''}")
    print("\nFunnel columns count both channels of a reel. Add the Instagram app's 3-second hold / skip rate by hand.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("preview")
    p.add_argument("--codes", nargs="*", choices=ar.ORDER)
    p.add_argument("--out", default="uploads/agentreels")
    p = sub.add_parser("plan")
    p.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    p.add_argument("--time", default="19:30", help="IST, HH:MM")
    p.add_argument("--channels", nargs="+", default=["facebook_page"], choices=["facebook_page", "instagram"])
    p = sub.add_parser("report")
    p.add_argument("--no-insights", action="store_true")
    a = ap.parse_args()
    if a.cmd == "check":
        return cmd_check(a)
    if a.cmd == "preview":
        return cmd_preview(a)
    if a.cmd == "plan":
        from app.modules.calendar.store import Store
        hh, mm = (int(x) for x in a.time.split(":"))
        asyncio.run(plan(Store(_db()), date.fromisoformat(a.start), time(hh, mm), a.channels))
        return 0
    asyncio.run(report(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
