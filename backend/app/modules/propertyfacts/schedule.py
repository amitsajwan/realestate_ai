"""Send a finished campaign to the approval calendar: one `planned` row per post and channel, one post a day.

Nothing publishes from here: the owner approves each row in Studio > Calendar (calendar.store PUBLISHABLE is the gate).
Each row's slug is unique per listing and angle and carries the listing's agent, so the calendar's interest link
(calendar.adapters.with_interest, keyed by slug) counts enquiries per post. Facebook captions also carry the listing page link
with `?src=`, so visits per post show in tracking; Instagram keeps "link in bio"."""
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Sequence, Tuple

from app.modules.calendar.store import Store as CalendarStore, aware

IST = timezone(timedelta(hours=5, minutes=30))
POST_AT = time(19, 0)          # 7 pm IST: after work, when buyers browse
MIN_GAP = timedelta(hours=12)  # the calendar's own rule: posts on a channel at least 12 hours apart
CHANNELS = ("instagram", "facebook_page")
SEARCH_DAYS = 60


def slug_for(listing_id: str, angle: str) -> str:
    return f"campaign-{listing_id}-{angle}"[:80]


def facebook_caption(caption: str, link_line: str, page_url: str, angle: str) -> str:
    """The Instagram caption with its "link in bio" line replaced by the listing page link (tagged per post)."""
    url = f"{page_url}{'&' if '?' in page_url else '?'}src=fb_{angle}"
    line = f"Full details and the MahaRERA record: {url}"
    return caption.replace(link_line, line) if link_line and link_line in caption else caption.rstrip() + "\n\n" + line


def slots(start: date, n: int, taken: Sequence[datetime]) -> List[datetime]:
    """n daily 7 pm IST times from `start`, each at least MIN_GAP from `taken` and from each other."""
    out: List[datetime] = []
    busy = [t if t.tzinfo else t.replace(tzinfo=timezone.utc) for t in taken]
    d = start
    for _ in range(SEARCH_DAYS + n):
        if len(out) == n:
            break
        at = datetime.combine(d, POST_AT, tzinfo=IST).astimezone(timezone.utc)
        if all(abs(at - b) >= MIN_GAP for b in busy + out):
            out.append(at)
        d += timedelta(days=1)
    return out


def _rel(path: str) -> str:
    return path[len("/uploads/"):] if path.startswith("/uploads/") else path.lstrip("/")


def items(run: dict, link_line: str) -> List[Dict]:
    """What goes into the calendar, in campaign order: every post on both channels; each slides reel on Instagram only
    (Facebook already turns a carousel into a reel when it posts it, calendar.runner); the walkthrough reel, once rendered,
    on both. Each: {slug, channel, kind, caption, images, video, angle, creative}."""
    lid, page = run["listing_id"], run.get("page_url") or ""
    out: List[Dict] = []

    def add(slug, channel, kind, caption, images, video, angle, extra_creative):
        if channel != "instagram":
            caption = facebook_caption(caption, link_line, page, angle)
        creative = {"role": "listing", "source": "campaign", "path": "campaign", "angle": angle, "ok": True,
                    "hook": (caption.splitlines() or [""])[0], **extra_creative}
        out.append({"slug": slug, "channel": channel, "kind": kind, "caption": caption, "images": images, "video": video,
                    "angle": angle, "creative": creative})

    for channel in CHANNELS:
        for p in run.get("posts") or []:
            add(slug_for(lid, p["angle"]), channel, "post", p["caption"], [_rel(i) for i in p["images"]], None, p["angle"],
                {"layout": p.get("layout"), "format": p.get("format"), "llm": p.get("used_llm"), "prompts": p.get("prompts") or []})
        for r in run.get("reels") or []:
            if not r.get("video"):
                continue
            if r["kind"] == "slides" and channel == "instagram":
                add(slug_for(lid, f"{r['angle']}-reel"), channel, "reel", r["caption"], [], _rel(r["video"]), f"{r['angle']}-reel",
                    {"layout": "slides_reel", "template": "campaign"})
            elif r["kind"] == "walkthrough" and r.get("status") == "done":
                caption = r.get("caption") or (run["posts"][0]["caption"] if run.get("posts") else "")
                add(slug_for(lid, "walkthrough"), channel, "reel", caption, [], _rel(r["video"]), "walkthrough",
                    {"layout": "walkthrough_reel", "template": "campaign"})
    return out


async def queue(store: CalendarStore, run: dict, link_line: str, start: date) -> List[Dict]:
    """Add the run's posts and reels as planned rows; returns [{angle, channel, kind, row_id, due_at}]. Rows already in the
    calendar for this listing are not added again (pressing twice adds nothing; a reel rendered later is added then)."""
    # only rows still waiting, approved or published block a post: a campaign run made again after its earlier rows were
    # skipped (or removed, or failed) must be able to send its new posts (live 2026-10-06, Gulmohar: "sent" added nothing)
    existing = [(d["channel"], d["slug"], aware(d["due_at"])) for d in await store.all()
                if d.get("status") in ("planned", "approved", "scheduled", "published")]
    used = {(ch, slug) for ch, slug, _ in existing}
    added: List[Dict] = []
    todo = [it for it in items(run, link_line) if (it["channel"], it["slug"]) not in used]
    for channel in CHANNELS:
        mine = [it for it in todo if it["channel"] == channel]
        taken = [at for ch, _, at in existing if ch == channel]
        for it, at in zip(mine, slots(start, len(mine), taken)):
            rid = await store.add(it["slug"], channel, it["caption"], it["images"][0] if it["images"] else "", at, kind=it["kind"],
                                  status="planned", images=it["images"], video=it["video"], creative=it["creative"],
                                  extra={"agent_id": run["agent_id"], "listing_id": run["listing_id"], "campaign_run": run["_id"]})
            added.append({"angle": it["angle"], "channel": channel, "kind": it["kind"], "row_id": rid, "due_at": at})
    return added
