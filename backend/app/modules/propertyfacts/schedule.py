"""Send a finished campaign to the approval calendar: one `planned` row per post and channel, one post a day.

Nothing publishes from here: the owner approves each row in Studio > Calendar (calendar.store PUBLISHABLE is the gate).
Each row's slug is unique per listing and angle and carries the listing's agent, so the calendar's interest link
(calendar.adapters.with_interest, keyed by slug) counts enquiries per post. Facebook captions also carry the listing page link
with `?src=`, so visits per post show in tracking; Instagram keeps "link in bio"."""
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.modules.calendar.store import Store as CalendarStore, aware

WALKTHROUGH_EXPERIMENT = "walkthrough_style"   # calendar tag: experiment + variant tour | stack (jobs.walkthrough_style)

IST = timezone(timedelta(hours=5, minutes=30))
POST_TIMES = (time(11, 0), time(19, 0))   # 2 a day on each channel (owner, 2026-10-08): lunchtime and after work, IST
MIN_GAP = timedelta(hours=6)   # posts on a channel at least 6 hours apart (calendar.plan.daily_gap for more than one a day)
CHANNELS = ("instagram", "facebook_page")
SEARCH_DAYS = 60


def slug_for(listing_id: str, angle: str) -> str:
    return f"campaign-{listing_id}-{angle}"[:80]


BIO_LINE = re.compile(r"(link in (our )?bio|बायोमधील लिंक|बायो में लिंक)\.?\s*$", re.I)


def facebook_caption(caption: str, link_line: str, page_url: str, angle: str) -> str:
    """The Instagram caption with its "link in bio" line replaced by the listing page link (tagged per post). A "link in bio"
    line in another language than link_line (a caption rewritten later) is dropped: Facebook has no bio link."""
    url = f"{page_url}{'&' if '?' in page_url else '?'}src=fb_{angle}"
    line = f"Photos and full details: {url}"
    if link_line and link_line in caption:
        return caption.replace(link_line, line)
    caption = "\n".join(l for l in caption.split("\n") if not BIO_LINE.search(l))
    return re.sub(r"\n{3,}", "\n\n", caption).rstrip() + "\n\n" + line


def instagram_caption(caption: str, link_line: str, page_url: str) -> str:
    """Instagram links are not clickable in captions: the page's address is written out (typeable) next to "link in bio"."""
    if not page_url:
        return caption
    short = re.sub(r"^https?://(www\.)?", "", page_url).rstrip("/")
    if short in caption:
        return caption
    line = f"{link_line.rstrip('.')} · {short}" if link_line else short
    return caption.replace(link_line, line) if link_line and link_line in caption else caption.rstrip() + "\n\n" + line


def slots(start: date, n: int, taken: Sequence[datetime]) -> List[datetime]:
    """n times from `start` at POST_TIMES (IST) each day, each at least MIN_GAP from `taken` and from each other: a time
    too close to a post already on that channel is skipped, so the campaign takes the next free slot."""
    out: List[datetime] = []
    busy = [t if t.tzinfo else t.replace(tzinfo=timezone.utc) for t in taken]
    d = start
    for _ in range(SEARCH_DAYS + n):
        for hm in POST_TIMES:
            if len(out) == n:
                return out
            at = datetime.combine(d, hm, tzinfo=IST).astimezone(timezone.utc)
            if all(abs(at - b) >= MIN_GAP for b in busy + out):
                out.append(at)
        d += timedelta(days=1)
    return out


def _rel(path: str) -> str:
    return path[len("/uploads/"):] if path.startswith("/uploads/") else path.lstrip("/")


def property_of(listing: dict, facts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """What calendar.reach reads first for the hashtags (locality, project, type), so the tags do not depend on the caption's wording.
    The checked fact sheet wins ("Ranjangaon", "Gulmohar City" from MahaRERA); the listing as the agent typed it is the fallback
    ("Shikarapur maltan highway near ranjangaon midc", "Gulmohor city")."""
    from .facts import USABLE
    out: Dict[str, str] = {}
    for key in ("project_name", "locality", "property_type"):
        f = (facts or {}).get(key)
        val = f.value if f is not None and getattr(f, "level", None) in USABLE and isinstance(f.value, str) else listing.get(key)
        if val and str(val).strip():
            out[key] = str(val).strip()
    # who the post is for (calendar.reach.segment): as the listing says, never from the copy
    if isinstance(listing.get("price_inr"), (int, float)) and listing["price_inr"] > 0:
        out["price_inr"] = int(listing["price_inr"])
    if isinstance(listing.get("bhk"), (int, float)) and listing["bhk"] > 0:
        out["bhk"] = listing["bhk"]
    if listing.get("transaction") in ("sale", "rent"):
        out["transaction"] = listing["transaction"]
    if "onwards" in str(listing.get("title") or "").lower():
        out["price_from"] = True
    return out


def items(run: dict, link_line: str) -> List[Dict]:
    """What goes into the calendar, in campaign order, on both channels: each post's ad reel in place of the post (89.9% of
    our views come from the Reels tab), the overview also as a post (the Page grid), a post without an ad reel as a post; the
    walkthrough reel, once rendered, and the reel from the agent's own video. Older runs' slides reels go on Instagram only.
    Each: {slug, channel, kind, caption, images, video, angle, creative}."""
    lid, page = run["listing_id"], run.get("listing_url") or run.get("page_url") or ""
    out: List[Dict] = []

    def add(slug, channel, kind, caption, images, video, angle, extra_creative):
        caption = facebook_caption(caption, link_line, page, angle) if channel != "instagram" else instagram_caption(caption, link_line, page)
        creative = {"role": "listing", "source": "campaign", "path": "campaign", "angle": angle, "ok": True,
                    "hook": (caption.splitlines() or [""])[0], **(run.get("property") or {}), **extra_creative}
        out.append({"slug": slug, "channel": channel, "kind": kind, "caption": caption, "images": images, "video": video,
                    "angle": angle, "creative": creative})

    for channel in CHANNELS:
        # the overview takes the first slot (slots are in time order); the rest keep the campaign's order
        ads = {r["angle"]: r for r in run.get("reels") or [] if r.get("kind") == "ad" and r.get("video")}
        for p in sorted(run.get("posts") or [], key=lambda p: p["angle"] != "overview"):
            ad = ads.get(p["angle"])
            if ad:
                sc = ad.get("script") or {}
                add(slug_for(lid, f"{p['angle']}-ad"), channel, "reel", ad["caption"], [], _rel(ad["video"]), f"{p['angle']}-ad",
                    {"layout": "ad_reel", "template": "campaign", "experiment": "ad_reel", "variant": ad.get("format"),
                     "hook": sc.get("hook", "").replace("*", ""), "hook_type": sc.get("hook_type"), "script": sc.get("beats") or [],
                     "llm": sc.get("by") == "llm"})
                if p["angle"] != "overview":
                    continue
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
                style = r.get("style") or "tour"
                add(slug_for(lid, "walkthrough"), channel, "reel", caption, [], _rel(r["video"]), "walkthrough",
                    {"layout": "stacked_walkthrough_reel" if style == "stack" else "walkthrough_reel", "template": "campaign",
                     "experiment": WALKTHROUGH_EXPERIMENT, "variant": style, "language": r.get("language") or "en"})
            elif r["kind"] == "video" and r.get("status") == "done":   # the agent's own video, on both channels
                caption = r.get("caption") or (run["posts"][0]["caption"] if run.get("posts") else "")
                add(slug_for(lid, "video"), channel, "reel", caption, [], _rel(r["video"]), "video",
                    {"layout": "video_reel", "template": "campaign"})
    return out


async def queue(store: CalendarStore, run: dict, link_line: str, start: date) -> List[Dict]:
    """Add the run's posts and reels as planned rows; returns [{angle, channel, kind, row_id, due_at}]. Rows already in the
    calendar for this listing are not added again (pressing twice adds nothing; a reel rendered later is added then). A planned
    (not yet approved) row of this listing that the run no longer has - a post now going out as its ad reel, an old slides
    reel - is skipped, and the new row takes the earliest free slot."""
    wanted = items(run, link_line)
    slugs = {it["slug"] for it in wanted}
    for d in await store.all():
        if (d.get("status") == "planned" and d.get("listing_id") == run["listing_id"] and str(d.get("slug", "")).startswith("campaign-")
                and d["slug"] not in slugs):
            await store.skip(d["_id"], "replaced by its ad reel")
    # only rows still waiting, approved or published block a post: a campaign run made again after its earlier rows were
    # skipped (or removed, or failed) must be able to send its new posts (live 2026-10-06, Gulmohar: "sent" added nothing)
    existing = [(d["channel"], d["slug"], aware(d["due_at"])) for d in await store.all()
                if d.get("status") in ("planned", "approved", "scheduled", "published")]
    used = {(ch, slug) for ch, slug, _ in existing}
    added: List[Dict] = []
    todo = [it for it in wanted if (it["channel"], it["slug"]) not in used]
    for channel in CHANNELS:
        mine = [it for it in todo if it["channel"] == channel]
        taken = [at for ch, _, at in existing if ch == channel]
        for it, at in zip(mine, slots(start, len(mine), taken)):
            rid = await store.add(it["slug"], channel, it["caption"], it["images"][0] if it["images"] else "", at, kind=it["kind"],
                                  status="planned", images=it["images"], video=it["video"], creative=it["creative"],
                                  extra={"agent_id": run["agent_id"], "listing_id": run["listing_id"], "campaign_run": run["_id"]})
            added.append({"angle": it["angle"], "channel": channel, "kind": it["kind"], "row_id": rid, "due_at": at})
    return added
