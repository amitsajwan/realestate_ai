"""Start marketing a listing (Studio): one queued job, two steps in order.

    1. facts  - gather the property's knowledge base (our MahaRERA register first, then MahaRERA, OpenStreetMap, calculators)
                and keep it; the listing's page then shows "Checked for you" (VerifiedFacts) from it.
    2. posts  - only once step 1 is done: the campaign (one post per angle the facts support), rendered as drafts.
                Nothing publishes from here: posting goes through approval.

Jobs live in `marketing_runs`; the worker loop "marketing_runs" (app/worker.py) runs one at a time under its runner lease.
A job cut off by a restart (a deploy) is queued again once when the runner starts; cut off twice, it fails with a message."""
import asyncio
import hashlib
import json
import logging
import os
import re
import time
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from app.platform import trace

from . import campaign, identity, points, room, understand
from .brochure import Brochures, usable_images
from .facts import USABLE
from .gather import Clients, gather
from .store import FactsStore, facts_of

log = logging.getLogger(__name__)

COLLECTION = "marketing_runs"
MARKETABLE = ("live", "under_offer")
ACTIVE = ("queued", "facts", "asking", "posts")  # asking: waiting for the agent's answers (understand.py)
AD_REELS = 6  # ad reels per campaign (ad_reel.py): one per post, in campaign order
WALKTHROUGH_NOTE = "Add 2 photos to get a walkthrough reel with voiceover"
# The walkthrough reel's style, split by listing so the two can be compared on real results (schedule.WALKTHROUGH_EXPERIMENT
# tags the calendar rows; the insights collector reads them back). Fixed per listing: a campaign made again keeps its style.


def walkthrough_style(listing_id: str) -> str:
    return ("tour", "stack")[int(hashlib.sha1(str(listing_id).encode()).hexdigest(), 16) % 2]
CAPTION_MAX = 2200  # Instagram's caption limit
NOTE_MAX = 300
STALE_AFTER = timedelta(minutes=20)
HEARTBEAT_EVERY_S = 60.0
HEARTBEAT_INTERVAL_S = STALE_AFTER.total_seconds()
# listing fields the posts are made from: a change to one of them remakes the posts that say it
FACT_FIELDS = ("transaction", "property_type", "listing_scope", "price_inr", "carpet_sqft", "plot_sqft", "size_min_sqft",
               "size_max_sqft", "sizes_sqft", "bhk", "units_total", "total_acres", "locality", "city", "project_name", "rera_no",
               "rera_status", "possession_date")
LOCKED = ("approved", "scheduled", "published")   # calendar rows the owner already passed: their post is never replaced


def _choices(match) -> List[dict]:
    """MahaRERA projects for the agent to pick from: close names in our register, or same-named ones the locality does not
    tell apart. A search that found no such name offers none."""
    if not match or match.project or not ("close names" in match.how or match.how.endswith("does not say which")):
        return []
    return [{"regno": c.regno, "name": c.name, "taluka": c.location} for c in match.candidates[:3]]


class RunError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail, self.status_code = detail, status_code


def _iso(dt) -> Optional[str]:
    """UTC, as "2026-10-07T13:30:00Z" (stored times may be naive UTC or aware)."""
    if not isinstance(dt, datetime):
        return dt
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(microsecond=0).isoformat() + "Z"


def run_out(doc: Optional[dict], base_url: str = "") -> Optional[dict]:
    """The job as the API returns it; image URLs absolute when `base_url` is given."""
    if not doc:
        return None
    base = base_url.rstrip("/")
    absolute = lambda imgs: [base + i if base and i.startswith("/") else i for i in imgs or []]
    posts = [{**p, "images": absolute(p.get("images")),
              **({"newer": {**p["newer"], "images": absolute(p["newer"].get("images"))}} if p.get("newer") else {})}
             for p in doc.get("posts") or []]
    return {"id": doc["_id"], "listing_id": doc["listing_id"], "status": doc["status"], "step": doc.get("step"),
            "language": doc.get("language") or "en",
            "facts": doc.get("facts"), "page_url": doc.get("page_url"), "listing_url": doc.get("listing_url"), "posts": posts, "dropped": doc.get("dropped") or {},
            "error": doc.get("error") or "", "created_at": _iso(doc.get("created_at")),
            "calendar": [{**c, "due_at": _iso(c.get("due_at"))} for c in doc.get("calendar") or []],
            "reels": [{**r, "video": (base + r["video"] if base and (r.get("video") or "").startswith("/") else r.get("video"))}
                      for r in doc.get("reels") or []],
            "facts_done_at": _iso(doc.get("facts_done_at")), "finished_at": _iso(doc.get("finished_at")),
            "files": doc.get("files") or {}, "questions": doc.get("questions") or [],
            "plan": doc.get("plan") or [], "skipped": doc.get("skipped") or {},
            "mode": doc.get("mode") or "full", "changes": doc.get("changes") or [], "base_run": doc.get("base_run"),
            "redone": doc.get("redone") or [], "stale": [p["angle"] for p in doc.get("posts") or [] if p.get("stale")],
            "reels_state": doc.get("reels_state"), "reels_error": doc.get("reels_error") or "",
            "boost": boost_out(doc.get("boost"), base), "room": room_out(doc.get("room")), "pick": doc.get("pick")}


def room_out(r: Optional[dict]) -> Optional[dict]:
    """The creative room for Studio: the brief, every pitch with its score, the chosen campaign (the fact book stays inside)."""
    if not r:
        return None
    scores = {s.get("pitch"): s for s in r.get("scores") or []}
    return {"brief": r.get("brief") or {}, "chosen": r.get("chosen"), "why": r.get("why") or "",
            "pitches": [{**p, "score": (scores.get(i + 1) or {}).get("score"), "note": (scores.get(i + 1) or {}).get("note") or ""}
                        for i, p in enumerate(r.get("pitches") or [])],
            "campaign": r.get("campaign") or {}, "facts": len(r.get("book") or []), "discussion": r.get("discussion") or None}


def boost_out(b: Optional[dict], base: str = "") -> Optional[dict]:
    """The run's boost pair as the API returns it (None before one was made): URLs absolute, times ISO."""
    if not b:
        return None
    ab = lambda u: base + u if base and isinstance(u, str) and u.startswith("/") else u
    reel, car = b.get("reel") or {}, b.get("carousel") or {}
    return {"state": b.get("state"), "error": b.get("error") or None, "ready_at": _iso(b.get("ready_at")),
            "reel": {"video_url": ab(reel.get("video_url")), "poster_url": ab(reel.get("poster_url")),
                     "duration_s": reel.get("duration_s")} if reel else None,
            "carousel": {"images": [ab(i) for i in car.get("images") or []], "zip_url": ab(car.get("zip_url"))} if car else None,
            "copy": b.get("copy"), "wa_prefill": b.get("wa_prefill"), "wa_link": b.get("wa_link"),
            "tracked_link": b.get("tracked_link"), "codes": b.get("codes"), "guide": b.get("guide"),
            "meta_open_url": b.get("meta_open_url") or "https://business.facebook.com/latest/home",
            "reel_permalink": b.get("reel_permalink"), "boosted_at": _iso(b.get("boosted_at")),
            "daily_spend_inr": b.get("daily_spend_inr"), "days": b.get("days")}


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(s))[:40] or "x"


def _rel(url_path: str) -> str:
    return url_path[len("/uploads/"):] if url_path.startswith("/uploads/") else url_path.lstrip("/")


def _post_page(run: dict) -> str:
    """Where a post's link goes: this listing's own page (its photos, as in the post), else the project page."""
    return run.get("listing_url") or run.get("page_url") or ""


def _summary(sheet) -> dict:
    """What step 1 found, for Studio: counts, the MahaRERA match and anything that could not be found."""
    usable = [k for k, f in sheet.facts.items() if f.level in USABLE]
    return {"usable": len(usable), "held": len(sheet.facts) - len(usable),
            "maharera": (sheet.match.project.regno if sheet.match and sheet.match.project else None),
            "how": sheet.match.how if sheet.match else "", "nearby": sum(1 for k in usable if k.startswith("nearby.")),
            "notes": list(sheet.notes)}


class MarketingRuns:
    def __init__(self, db, uploads_dir, site: str = "", clients_factory: Optional[Callable[[], Any]] = None,
                 llm_factory: Optional[Callable] = None, now: Callable[[], datetime] = datetime.utcnow,
                 ad_renderer: Optional[Callable] = None, reel_jobs: Any = None, facts_store: Any = None,
                 page_for: Optional[Callable] = None, enrich_now: Optional[Callable] = None,
                 boost_renderer: Optional[Callable] = None):
        """`ad_renderer(script, pictures, out, kicker)` makes an ad reel (default ad_reel.render);
        `reel_jobs` (reels.listing_reel.ReelJobs) queues the walkthrough reel; None skips it;
        `page_for(db, regno)` finds a project's own page (default areastats.pages.page_for); `enrich_now(db, regno, by=)` asks
        for that page's text to be written soon (default areastats.enrich.enrich_now)."""
        self.db = db
        self.runs = db.get_collection(COLLECTION)
        self.listings = db.get_collection("listings")
        self.profiles = db.get_collection("agent_public_profiles")
        self.uploads_dir, self.site = Path(uploads_dir), site.rstrip("/")
        self.clients_factory, self.llm_factory, self.now = clients_factory, llm_factory, now
        self.ad_renderer, self.reel_jobs = ad_renderer, reel_jobs
        self.facts_store = facts_store or FactsStore(db)
        self.page_for, self.enrich_now = page_for, enrich_now
        self.boost_renderer = boost_renderer   # the boost reel's renderer; None: boost.default_reel_renderer

    async def _listing(self, agent_id: str, listing_id: str) -> dict:
        doc = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise RunError("Listing not found", 404)
        return doc

    async def _latest(self, flt: dict) -> Optional[dict]:
        docs = await self.runs.find(flt).sort("created_at", -1).limit(1).to_list(1)
        return docs[0] if docs else None

    async def create(self, agent_id: str, listing_id: str, again: bool = False, language: str = "en",
                     pick: Optional[int] = None) -> tuple:
        """(job, created). A running job is returned as it is; a finished one too unless `again`, the listing changed or
        another language is asked for (en, mr, hi: the posts' language). A change to a finished run's `inputs` (facts,
        brochure, video, photos) makes an update run: that run's posts, remaking only what the change touches. Posts the
        agent edited or the owner approved are never replaced, only marked `stale` with the `newer` version."""
        listing = await self._listing(agent_id, listing_id)
        if listing.get("status") not in MARKETABLE:
            raise RunError("Publish this listing first: only live or under-offer listings can be marketed.", 409)
        flt = {"listing_id": listing_id, "agent_id": agent_id}
        active = await self._latest({**flt, "status": {"$in": list(ACTIVE)}})
        if active and again and active["status"] == "asking":  # a run left waiting on questions: start again closes it
            await self.runs.update_one({"_id": active["_id"], "status": "asking"},
                                       {"$set": {"status": "cancelled", "finished_at": self.now()}})
        elif active:
            return active, False
        done = await self._latest({**flt, "status": "done"})
        if done and (done.get("language") or "en") != language:
            done = None
        doc = {"_id": uuid.uuid4().hex, **flt, "status": "queued", "step": "facts", "language": language, "facts": None, "page_url": None, "posts": [],
               "dropped": {}, "error": None, "created_at": self.now(), "started_at": None, "facts_done_at": None,
               "finished_at": None, "mode": "full", "base_run": done["_id"] if done else None}
        if pick:   # the agent chose another of the room's pitches: the director writes the campaign from it
            earlier = await self._latest({**flt, "room": {"$ne": None}})
            if not earlier or not earlier.get("room") or pick > len(earlier["room"].get("pitches") or []):
                raise RunError("That pitch is no longer available. Start marketing again.", 409)
            doc.update(pick=pick, earlier_room=earlier["room"])
        if done and not again:
            changes = self._changes(done["inputs"], self._inputs(listing)) if done.get("inputs") else None
            changed = listing.get("updated_at")
            if changes == [] or (changes is None and not (isinstance(changed, datetime) and changed > done["created_at"])):
                return done, False
            if changes and done.get("posts") and not done.get("room"):   # a room campaign is pitched again, not patched
                keep = ("facts", "page_url", "listing_url", "posts", "reels", "calendar", "link_line", "files", "plan", "skipped",
                        "dropped", "inputs", "facts_done_at", "boost")
                doc.update({k: done[k] for k in keep if k in done}, mode="update", changes=changes)
        if done and done.get("calendar") and not doc.get("calendar"):
            # the rows still waiting for approval take the new posts; removed, skipped and published ones stay with the old
            # run (2026-10-15: a new run carried yesterday's removed reels, hid "Send to calendar" and showed old links)
            doc["calendar"] = await self._open_rows(done["calendar"])
        await self.runs.insert_one(doc)
        if again:
            await self._withdraw(flt)
        return doc, True

    async def _open_rows(self, rows: List[dict]) -> List[dict]:
        """The calendar rows that have not gone out, been skipped or been removed (planned, approved or scheduled)."""
        from app.modules.calendar.store import OPEN, Store as CalendarStore
        cal, out = CalendarStore(self.db), []
        for c in rows:
            row = await cal.get(c["row_id"])
            if row and row.get("status") in OPEN:
                out.append(c)
        return out

    async def _withdraw(self, flt: dict) -> int:
        """Marketing made again: the earlier runs' approved posts and reels that have not gone out yet are skipped, so the old
        campaign stops publishing beside the new one (2026-10-14: two approved Camelot reels went out after a remake).
        Planned rows stay: they wait for approval and take the new posts (_keep_edited)."""
        from app.modules.calendar.store import Store as CalendarStore
        cal, n = CalendarStore(self.db), 0
        for r in await self.runs.find(dict(flt)).to_list(200):
            for c in r.get("calendar") or []:
                row = await cal.get(c["row_id"])
                if row and row.get("status") in ("approved", "scheduled") and await cal.skip(c["row_id"], "withdrawn: marketing made again"):
                    n += 1
        if n:
            trace.event(log, "marketing", flt["listing_id"], "withdrawn", trace.OK, rows=n)
        return n

    def _inputs(self, listing: dict) -> dict:
        """What a run's posts are made from: a hash of the fact fields, the brochure, the video and the photos."""
        from app.modules.reels.listing_reel import listing_photos

        from . import files
        pdf, video = files.brochure_pdf(listing, self.uploads_dir), self._video(listing)
        facts = json.dumps({k: listing.get(k) for k in FACT_FIELDS}, sort_keys=True, default=str)
        return {"facts": hashlib.sha1(facts.encode("utf-8")).hexdigest()[:16], "brochure": pdf.name if pdf else None,
                "video": video.name if video else None, "photos": [p.name for p in listing_photos(listing, self.uploads_dir)]}

    @staticmethod
    def _changes(before: dict, now: dict) -> List[str]:
        """What changed between two `inputs`: some of facts, brochure, video, photos."""
        return [k for k in ("facts", "brochure", "video", "photos") if (before or {}).get(k) != now.get(k)]

    async def _locked(self, run: dict) -> set:
        """Angles whose calendar post the owner already approved (or that went out): never replaced."""
        from app.modules.calendar.store import Store as CalendarStore
        cal, out = CalendarStore(self.db), set()
        for c in run.get("calendar") or []:
            if c.get("kind", "post") == "post" and c.get("angle") not in out:
                row = await cal.get(c["row_id"])
                if row and row.get("status") in LOCKED:
                    out.add(c["angle"])
        return out

    async def _place(self, run: dict, old: dict, new: dict, locked: set) -> dict:
        """The post that stays: `new`, its planned calendar rows synced; or, for a post the agent edited or the owner
        approved, `old` kept and marked stale with `newer` to pick up."""
        if old.get("edited") or old["angle"] in locked:
            return {**old, "stale": True, "newer": {**{k: v for k, v in new.items() if k not in ("angle", "newer", "stale")},
                                                    "made_at": self.now()}}
        await self._sync_calendar(run, new["angle"], new["caption"], new.get("images"))
        return new

    async def latest(self, agent_id: str, listing_id: str) -> Optional[dict]:
        await self._listing(agent_id, listing_id)
        return await self._with_boost(await self._with_walkthrough(await self._latest({"listing_id": listing_id, "agent_id": agent_id})))

    async def to_calendar(self, agent_id: str, listing_id: str, start=None) -> dict:
        """Send the latest finished run's posts to the approval calendar as planned rows (schedule.queue). Idempotent."""
        from app.modules.calendar.store import Store as CalendarStore

        from . import schedule
        run = await self.latest(agent_id, listing_id)
        if not run or run["status"] != "done" or not run.get("posts"):
            raise RunError("Make the posts first: start marketing and wait until the posts are ready.", 409)
        first = start or (self.now() + timedelta(days=1)).date()
        listing = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id}) or {}
        prop = schedule.property_of(listing, await self._facts(run, listing) if listing else {})
        added = await schedule.queue(CalendarStore(self.db), {**run, "property": prop}, run.get("link_line") or "", first)
        rows = (run.get("calendar") or []) + [{**a, "due_at": a["due_at"]} for a in added]
        await self._set(run["_id"], calendar=rows, calendar_at=self.now())
        return {**run, "calendar": rows}

    # ---- edit and improve one post (Studio) ----------------------------------------------------------------------------
    async def _done_run(self, agent_id: str, listing_id: str, angle: str) -> tuple:
        run = await self.latest(agent_id, listing_id)
        if not run or run["status"] != "done":
            raise RunError("Make the posts first.", 409)
        idx = next((i for i, p in enumerate(run.get("posts") or []) if p["angle"] == angle), None)
        if idx is None:
            raise RunError("No such post in this campaign.", 404)
        return run, idx

    async def _facts(self, run: dict, listing: dict) -> Dict[str, Any]:
        doc = await self.facts_store.find((run.get("facts") or {}).get("maharera") or "", listing.get("project_name") or "",
                                             listing.get("locality") or "")
        return facts_of(doc)

    async def _sync_calendar(self, run: dict, angle: str, caption: str, images: Optional[List[str]] = None) -> int:
        """Planned calendar rows of this post take the new caption (Facebook's with its page link) and images; its ad reel's rows
        take the caption under the reel's hook (the video stays)."""
        from app.modules.calendar.store import Store as CalendarStore

        from . import ad_reel
        from .schedule import _rel, facebook_caption, instagram_caption
        cal, n = CalendarStore(self.db), 0
        ad = next((r for r in run.get("reels") or [] if r.get("kind") == "ad" and r.get("angle") == angle and r.get("script")), None)
        for c in run.get("calendar") or []:
            if c.get("angle") == angle and c.get("kind", "post") == "post":
                text = caption if c["channel"] == "instagram" else facebook_caption(caption, run.get("link_line") or "",
                                                                                     _post_page(run), angle)
                n += await cal.set_planned(c["row_id"], caption=text, images=[_rel(i) for i in images] if images else None)
            elif ad and c.get("angle") == f"{angle}-ad":
                text = ad_reel.caption(ad_reel.Script(**{k: ad["script"][k] for k in ("format", "hook", "beats", "payoff", "cta")}),
                                       caption)
                link, page = run.get("link_line") or "", _post_page(run)
                text = (instagram_caption(text, link, page) if c["channel"] == "instagram"
                        else facebook_caption(text, link, page, c["angle"]))
                n += await cal.set_planned(c["row_id"], caption=text)
        return n

    async def edit_post(self, agent_id: str, listing_id: str, angle: str, caption: str) -> tuple:
        """Save the agent's own caption. Returns (run, problems): the checks' findings are warnings, the text is kept as written
        (the owner still approves every post)."""
        from app.modules.creative.guards import problems_in
        caption = (caption or "").strip()
        if not caption:
            raise RunError("The caption cannot be empty.", 422)
        if len(caption) > CAPTION_MAX:
            raise RunError(f"Keep the caption under {CAPTION_MAX} characters.", 422)
        run, idx = await self._done_run(agent_id, listing_id, angle)
        listing = await self._listing(agent_id, listing_id)
        who = await self._identity(run)
        briefs = dict(campaign.plan(await self._facts(run, listing), follow_ups=None, images=await self._brochure_images(agent_id, listing_id),
                                    kit=await self._kit(listing_id, agent_id), **self._who(run, who)))
        if angle not in briefs and run.get("room"):
            briefs.update(await self._room_briefs(run, listing, angle, idx))
        corpus = briefs[angle].corpus() if angle in briefs else ""
        checked = "\n".join(line for line in caption.splitlines() if line.strip() not in who.contact)  # code-made contact block
        problems = [p for p in problems_in(checked, corpus, allow_url=True) if p != "url"] if corpus else []
        posts = list(run["posts"])
        posts[idx] = {**posts[idx], "caption": caption, "edited": True, "edited_at": self.now()}
        await self._set(run["_id"], posts=posts)
        synced = await self._sync_calendar(run, angle, caption)
        return {**run, "posts": posts, "synced": synced}, problems

    async def _room_briefs(self, run: dict, listing: dict, angle: str, idx: int) -> Dict[str, Any]:
        """The room campaign's briefs for a post edit or redo: the same pieces, this post keeping its own picture."""
        who = self._who(run, await self._identity(run))
        images = await self._brochure_images(run["agent_id"], run["listing_id"])
        ctx = campaign.Ctx(await self._facts(run, listing), await asyncio.to_thread(self._photo, listing), run.get("page_url") or "",
                           who.get("voice"), who.get("card_brand"), who.get("contact") or (), "en", (), who.get("names"),
                           who.get("claims") or (), None, images, await self._kit(run["listing_id"], run["agent_id"]))
        own = run["posts"][idx].get("photo")
        photos = [own] if own and own != "none" and Path(own).is_file() else []
        return dict(room.briefs(run["room"], ctx, photos, images))

    async def redo_post(self, agent_id: str, listing_id: str, angle: str, note: str) -> dict:
        """Make this post again with the agent's note (the copywriter's feedback), from the kept facts, under every guard."""
        note = (note or "").strip()[:NOTE_MAX]
        run, idx = await self._done_run(agent_id, listing_id, angle)
        listing = await self._listing(agent_id, listing_id)
        photo = await asyncio.to_thread(self._photo, listing)
        briefs = dict(campaign.plan(await self._facts(run, listing), photo, run.get("page_url") or "", follow_ups=None,
                                    images=await self._brochure_images(agent_id, listing_id),
                                    kit=await self._kit(listing_id, agent_id),
                                    **self._who(run, await self._identity(run))))
        if angle not in briefs and run.get("room"):
            briefs.update(await self._room_briefs(run, listing, angle, idx))
        if angle not in briefs:
            raise RunError("The facts for this post are no longer available. Start marketing again.", 409)
        n = int(run["posts"][idx].get("redos") or 0) + 1
        out = self.uploads_dir / "campaigns" / _safe(listing_id) / run["_id"][:8] / _safe(angle) / f"redo{n}"
        llm = self.llm_factory() if self.llm_factory else None
        pack = await campaign.pipeline.make(briefs[angle], "buyer", "instagram", llm, seed=31 * n + idx, out_dir=out, reviewer=None,
                                            note=note)
        if not pack.report.get("ok"):
            raise RunError("Could not make a version that passes the checks. Try a different note.", 422)
        imgs = ["/uploads/" + Path(i).resolve().relative_to(self.uploads_dir.resolve()).as_posix() for i in pack.images]
        posts = list(run["posts"])
        posts[idx] = {**posts[idx], "images": imgs, "caption": pack.caption, "layout": pack.design.get("layout"),
                      "format": pack.design.get("format"), "used_llm": pack.used_llm, "prompts": pack.prompts,
                      "edited": False, "stale": False, "newer": None, "redos": n,
                      "note": note, "redone_at": self.now()}
        await self._set(run["_id"], posts=posts)
        synced = await self._sync_calendar(run, angle, pack.caption, imgs)
        return {**run, "posts": posts, "synced": synced}

    # ---- worker side ------------------------------------------------------------------------------------------------
    async def fail_stale(self) -> None:
        """At the runner's start (one runner, under its lease): a run still in "facts" or "posts" was cut off by a restart
        (a deploy). It is queued again once, from the start; cut off a second time, it fails with a message."""
        for d in await self.runs.find({"status": {"$in": ["facts", "posts"]}}).to_list(100):
            if d.get("resumed"):
                change = {"status": "failed", "error": "Marketing was interrupted. Please start it again.", "finished_at": self.now()}
            elif d.get("mode") == "update":   # its posts are the earlier run's: kept
                change = {"status": "queued", "step": "facts", "resumed": True, "started_at": None, "reels": [], "error": None}
            else:
                change = {"status": "queued", "step": "facts", "resumed": True, "started_at": None, "posts": [], "reels": [], "error": None}
            await self.runs.update_one({"_id": d["_id"], "status": d["status"]}, {"$set": change})
        for d in await self.runs.find({"status": "done", "boost.state": "making", "boost_queued": False}).to_list(100):
            await self.runs.update_one({"_id": d["_id"]}, {"$set": {"boost": {**d["boost"], "state": "failed",
                                                                            "error": "Interrupted. Please make it again."}}})

    async def claim(self) -> Optional[dict]:
        docs = await self.runs.find({"status": "queued"}).sort("created_at", 1).limit(1).to_list(1)
        if not docs:
            return None
        res = await self.runs.update_one({"_id": docs[0]["_id"], "status": "queued"},
                                         {"$set": {"status": "facts", "started_at": self.now()}})
        if res is not None and getattr(res, "modified_count", 1) == 0:
            return None  # another process took it
        return {**docs[0], "status": "facts"}

    async def _set(self, jid: str, **fields) -> None:
        await self.runs.update_one({"_id": jid}, {"$set": fields})

    async def _identity(self, run: dict) -> identity.Identity:
        """Whose posts these are: the listing owner's profile (an agent's name, logo, phone), or ours."""
        prof = await self.profiles.find_one({"agent_id": run["agent_id"]})
        return identity.identity(prof, self.site, self.uploads_dir, run.get("language") or "en")

    @staticmethod
    def _who(run: dict, who: identity.Identity) -> Dict[str, Any]:
        """campaign.plan/make keyword arguments for this run's language and owner."""
        return {"voice": who.voice, "card_brand": who.card_brand, "contact": who.contact, "language": run.get("language") or "en",
                "names": run.get("names") or None, "claims": tuple(run.get("claims") or ())}

    async def _page_url(self, agent_id: str, listing_id: str) -> str:
        prof = await self.profiles.find_one({"agent_id": agent_id})
        slug = (prof or {}).get("slug")
        return f"{self.site}/agent/{slug}/listings/{listing_id}" if slug else f"{self.site}/listings/{listing_id}"

    async def _enrich_soon(self, regno: str) -> None:
        """Ask for the project page's text to be written soon (areastats.enrich.enrich_now, urgent, about a minute). Best
        effort and not waited for: the page already shows this sheet's facts; only the written paragraph arrives later."""
        enrich_now = self.enrich_now
        try:
            if enrich_now is None:
                from app.modules.areastats.enrich import enrich_now
            await enrich_now(self.db, regno, by="campaign")
        except Exception:  # not deployed yet, loop off, project unknown: the campaign goes on
            log.info("marketing: no urgent page enrichment for %s", regno, exc_info=True)

    async def _project_page(self, sheet) -> tuple:
        """(regno, project page url) for a property with a MahaRERA number: the project is put on the register's watch list
        now (so its page can be made), then its page is looked up (areastats.pages.page_for). (None, None) without a number;
        (regno, None) while the page does not exist yet."""
        f = sheet.facts.get("rera_no")
        if not (f and f.usable):
            return None, None
        regno = str(f.value).upper()
        url = sheet.facts.get("maharera_url")
        m = re.search(r"/view/(\d+)", str(url.value)) if url and url.usable else None
        name = next((sheet.facts[k].value for k in ("maharera_name", "project_name") if k in sheet.facts), "")
        try:
            from app.modules.areastats.watch import WatchItem, watch
            from app.modules.newsroom.store import Store as Register
            await watch(Register(self.db), WatchItem(regno, int(m.group(1)) if m else None, name), "property_facts", self.now())
        except Exception:
            log.warning("marketing: could not add %s to the register's watch list", regno, exc_info=True)
        await self._enrich_soon(regno)
        try:   # a tower of a marketed project (Lodha Camelot): the project's own page, once it is public
            from app.modules.agentprojects.groups import public_group
            group = await public_group(self.db, regno)
            if group and group.get("path"):
                return regno, self.site + group["path"]
        except Exception:
            log.info("marketing: no project group page for %s", regno, exc_info=True)
        page_for = self.page_for
        if page_for is None:
            try:
                from app.modules.areastats.pages import page_for
            except ImportError:  # project pages not deployed yet: nothing is marketed without its page
                return regno, None
        page = await page_for(self.db, regno)
        return regno, (page or {}).get("url")

    async def _brochure_images(self, agent_id: str, listing_id: str) -> List[dict]:
        """The floor plans and renders the agent said to use from this listing's brochure (brochure.usable_images). They go
        into posts only (campaign.floor_plan, first_look), never into the walkthrough reel, which uses the agent's photos."""
        try:
            kit = await Brochures(self.db, self.uploads_dir).current(listing_id)
        except Exception:
            log.warning("marketing: could not read the brochure kit of %s", listing_id, exc_info=True)
            return []
        if not kit or kit.get("agent_id") != agent_id:
            return []
        return usable_images(kit, self.uploads_dir)

    async def _kit(self, listing_id: str, agent_id: Optional[str] = None) -> Optional[dict]:
        """The listing's brochure kit (its registration answer decides the MahaRERA badge with the facts); None without one, or
        when it is another agent's (the same rule as its images)."""
        try:
            kit = await Brochures(self.db, self.uploads_dir).current(listing_id)
        except Exception:
            log.info("marketing: no brochure kit read for %s", listing_id, exc_info=True)
            return None
        return kit if kit and (agent_id is None or kit.get("agent_id") == agent_id) else None

    def _photo(self, listing: dict) -> str:
        """The listing's best photo (marketing.images.cover_photo_path) as a local file for the cards, or "none" (never a
        stock photo of something else)."""
        from app.modules.marketing.images import cover_photo_path
        p = cover_photo_path(listing.get("media") or [], self.uploads_dir)
        return str(p) if p and Path(p).is_file() else "none"

    async def _reels(self, job: dict, listing: dict, posts: List[dict], out: Path, project: str, link_line: str,
                     pool: Sequence[str] = (), facts: Optional[Dict[str, Any]] = None) -> List[dict]:
        """An ad reel per post (up to AD_REELS), the video reel, and the walkthrough reel job. Each one that fails is skipped.
        The walkthrough: none for a listing with a video (its video reel covers the place); from the listing's
        photos when it has 2; else from the run's ranked pictures (`pool`: stills, brochure pages) when 2 are usable; else a
        note asking for photos. Its style (tour or stack) is fixed per listing (walkthrough_style), spoken in the posts' language."""
        reels = await self._ad_reels(job, posts, out, project, pool, facts or {})
        video = self._video(listing)
        if video:
            reels.append(await self._video_reel(job, listing, video, out, project, link_line, facts))
            await self._set(job["_id"], reels=reels)
        if self.reel_jobs is not None and not video:
            from app.modules.reels.listing_reel import MIN_PHOTOS, listing_photos
            from . import pictures
            extra: Dict[str, Any] = {}
            if len(listing_photos(listing, self.uploads_dir)) < MIN_PHOTOS:
                usable = pictures.walkthrough_pictures(pool)
                if len(usable) < MIN_PHOTOS:
                    reels.append({"kind": "walkthrough", "status": "skipped", "note": WALKTHROUGH_NOTE})
                    trace.event(log, "marketing", job["_id"], "walkthrough_reel", trace.SKIPPED, reason=WALKTHROUGH_NOTE)
                    return reels
                extra = {"photos": usable}
            try:
                from app.modules.reels.listing_reel import caption as reel_caption
                lang, style = job.get("language") or "en", walkthrough_style(job["listing_id"])
                doc, _ = await self.reel_jobs.create(job["agent_id"], job["listing_id"], lang, style=style, **extra)
                reels.append({"kind": "walkthrough", "job_id": doc["_id"], "status": doc["status"], "video": doc.get("video_path"),
                              "style": style, "language": lang, "caption": reel_caption(listing, "", lang) + "\n\n" + link_line})
                trace.event(log, "marketing", job["_id"], "walkthrough_reel", trace.OK, reel_job=doc["_id"], status=doc["status"],
                            lang=lang, style=style)
            except Exception as e:  # fewer than 2 photos, the daily limit...: the campaign goes on without it
                note = str(getattr(e, "detail", "") or "not made")
                reels.append({"kind": "walkthrough", "status": "skipped", "note": note})
                trace.event(log, "marketing", job["_id"], "walkthrough_reel", trace.SKIPPED, reason=note if note != "not made" else
                            (str(e) or type(e).__name__))
        return reels

    async def _ad_reels(self, job: dict, posts: List[dict], out: Path, project: str, pool: Sequence[str],
                        facts: Dict[str, Any]) -> List[dict]:
        """One ad reel per post (ad_reel.py) in the format that says what the post says (ad_reel.for_posts), the words
        checked against the facts, each opening on a different one of the best pictures. Own photos first."""
        from . import ad_reel
        render = self.ad_renderer or ad_reel.render
        llm = self.llm_factory() if self.llm_factory else None
        ctx = campaign.Ctx(facts)
        written = room.scripts(job.get("room"))   # the creative room's reels: the director chose which pieces get one
        if written:
            todo = [p for p in posts if p["angle"] in written][:room.MAX_REELS]
            formats = ["story"] * len(todo)
        else:
            todo = posts[:AD_REELS]
            formats = ad_reel.for_posts([p["angle"] for p in todo], ad_reel.eligible(ctx), await ad_reel.scores(self.db))
        pics = [p for p in pool if Path(p).is_file()]
        kicker = (project or "").upper()[:28] or None
        reels: List[dict] = []
        for i, (p, fmt) in enumerate(zip(todo, formats)):
            if fmt is None:
                continue
            dest = out / "reels" / f"ad-{_safe(p['angle'])}.mp4"
            try:
                if p["angle"] in written:
                    script = written[p["angle"]]
                    if llm is not None:
                        await ad_reel.speak(script, llm)
                else:
                    script = await ad_reel.write(fmt, ctx, llm)
                order = pics[i % len(pics):] + pics[:i % len(pics)] if pics else []
                made = await asyncio.to_thread(render, script, order, dest, kicker)
                made = made if isinstance(made, dict) else {}
                reels.append({"kind": "ad", "angle": p["angle"], "format": fmt, "script": script.out(),
                              "caption": ad_reel.caption(script, p["caption"]), "voice": made.get("voice"),
                              "seconds": made.get("seconds"),
                              "video": "/uploads/" + dest.resolve().relative_to(self.uploads_dir.resolve()).as_posix()})
                trace.event(log, "marketing", job["_id"], "ad_reel", trace.OK, angle=p["angle"], format=fmt,
                            voice=made.get("voice"), seconds=made.get("seconds"))
                await self._set(job["_id"], reels=reels)   # Studio shows each reel as it lands; an interrupted run keeps them
            except Exception as e:
                trace.event(log, "marketing", job["_id"], "ad_reel", trace.FAILED, angle=p["angle"], format=fmt,
                            reason=str(e) or type(e).__name__, exc_info=True)
        return reels

    async def remake_reels(self, agent_id: str, listing_id: str) -> dict:
        """Make only the ad reels again from the finished run's posts, facts and pictures (the worker does it; reels_state
        "making" meanwhile). The posts, the walkthrough and the video reel are kept as they are."""
        run = await self.latest(agent_id, listing_id)
        if not run or run["status"] != "done" or not run.get("posts"):
            raise RunError("Make the posts first.", 409)
        if run.get("reels_state") == "making":
            return run
        await self._set(run["_id"], reels_state="making", reels_queued=True)
        return {**run, "reels_state": "making"}

    async def claim_reels(self) -> Optional[dict]:
        doc = await self.runs.find_one({"reels_queued": True})
        if not doc:
            return None
        res = await self.runs.update_one({"_id": doc["_id"], "reels_queued": True}, {"$set": {"reels_queued": False}})
        if res is not None and getattr(res, "modified_count", 1) == 0:
            return None
        return doc

    async def run_reels(self, job: dict) -> None:
        """A reels remake: the kept facts and the property's pictures, then an ad reel per post; earlier slides/ad reels are
        replaced, the others kept. Planned calendar rows are brought up to date when the run was sent there. Never raises."""
        try:
            listing = await self.listings.find_one({"_id": job["listing_id"], "agent_id": job["agent_id"]})
            if not listing:
                raise RunError("The listing was removed.")
            out = self.uploads_dir / "campaigns" / _safe(job["listing_id"]) / job["_id"][:8]
            # the project's kept sheet (nearby places, MahaRERA) under this listing's own fields: the sheet is shared by the
            # project's listings and can hold another one's price (live 2026-10-10: a Ranjangaon plot's ₹30 lakh went into
            # Gulmohar City's ₹2.99 lakh reels)
            from .facts import Fact
            facts = {**await self._facts(job, listing),
                     **{k: Fact(k, listing[k], "official", [], []) for k in FACT_FIELDS if listing.get(k) not in (None, "", [])}}
            ctx = campaign.Ctx(facts)
            pool = await self._photo_pool(listing, out)
            if not pool:   # no photos of its own: the brochure pages the posts used
                pool = [str(self.uploads_dir / _rel(i)) for p in job.get("posts") or [] if p.get("photo") == "brochure"
                        for i in p.get("images", [])[:1]]
            ads = await self._ad_reels(job, [p for p in job.get("posts") or [] if not p.get("stale")], out, ctx.project, pool, facts)
            reels = [r for r in job.get("reels") or [] if r.get("kind") not in ("slides", "ad")] + ads
            await self._set(job["_id"], reels=reels, reels_state="done", reels_error=None)
            if job.get("calendar"):
                await self.to_calendar(job["agent_id"], job["listing_id"])
        except Exception as e:
            log.warning("reels remake %s failed", job["_id"], exc_info=True)
            await self._set(job["_id"], reels_state="failed",
                            reels_error="The reels could not be made again: " + str(getattr(e, "detail", "") or e)[:200])

    def _brochure(self, listing: dict) -> Dict[str, Any]:
        """What the listing already knows from its brochure: the claims the AI draft read at creation (files.claims_for),
        never a fresh read. Posts and reels are made from the agent's listing, the gathered facts and the pictures the
        agent picked from the brochure kit; a run does not wait for, OCR or page through the PDF. {} without claims."""
        from . import files
        pdf = files.brochure_pdf(listing, self.uploads_dir)
        return (files.claims_for(listing, pdf) or {}) if pdf else {}

    async def _photo_pool(self, listing: dict, out: Path) -> List[str]:
        """The property's own pictures for the post cards, one per post, best first: its photos and the stills of its video
        ranked together by pictures.rank (clear place shots, sharp and colourful first; a
        presenter filling the frame, burned-in text and near-duplicates last or left out), so neighbouring cards never show
        the same scene. Never stock photos; [] keeps the plain cards. Ranking never fails the run: its fallback is the
        upload order (photos and stills alternating)."""
        from app.modules.reels.listing_reel import listing_photos

        from . import pictures
        own = [str(p) for p in listing_photos(listing, self.uploads_dir) if Path(p).is_file()]
        video = self._video(listing)
        stills: List[str] = []
        if video:
            from app.modules.reels.video_director import best_frames
            stills = await best_frames(video, out / "frames")
        pool: List[str] = []
        for i in range(max(len(own), len(stills))):
            pool += ([own[i]] if i < len(own) else []) + ([stills[i]] if i < len(stills) else [])
        try:
            return await asyncio.to_thread(pictures.rank, pool, set(own), pictures.shot_notes(out / "frames"))
        except Exception:
            log.warning("marketing: picture ranking failed, upload order kept", exc_info=True)
            return pool

    def _has_files(self, listing: dict) -> bool:
        """Something to show on the cards: a photo, a video or a brochure (its kit's renders and plans)."""
        from app.modules.reels.listing_reel import listing_photos

        from . import files
        return (files.brochure_pdf(listing, self.uploads_dir) is not None or self._video(listing) is not None
                or any(Path(p).is_file() for p in listing_photos(listing, self.uploads_dir)))

    def _video(self, listing: dict) -> Optional[Path]:
        """The listing's first uploaded video (media kind 'video', a file under <uploads>/videos), or None."""
        vids = sorted(((m.get("order") or 0, i, m) for i, m in enumerate(listing.get("media") or []) if m.get("kind") == "video"),
                      key=lambda t: (t[0], t[1]))
        root = (self.uploads_dir / "videos").resolve()
        for _, _, m in vids:
            m_ = re.search(r"/uploads/videos/([A-Za-z0-9._-]+)$", str(m.get("url") or ""))
            p = (root / m_.group(1)).resolve() if m_ else None
            if p and p.parent == root and p.is_file():
                return p
        return None

    async def _voice_video(self, dest: Path, facts: Dict[str, Any], speech: Sequence, ref: str) -> str:
        """A voice-over on the video reel when nobody speaks in the video (a builder's walkthrough with music or silence): the
        showcase reel's checked lines, spread over the clip, music under them. "take"|"lines" when added, "kept" when the video
        has its own speech, "off"/"failed" otherwise. Never raises."""
        from app.modules.reels import video_reel, voice

        from . import ad_reel
        if speech:
            return "kept"
        if not voice.available():
            return "off"
        try:
            ctx = campaign.Ctx(facts)
            fmt = "showcase" if "showcase" in ad_reel.eligible(ctx) else "three_reasons"
            script = await ad_reel.write(fmt, ctx, self.llm_factory() if self.llm_factory else None)
            how = await asyncio.to_thread(video_reel.voice_over, dest, script.voice())
            trace.event(log, "marketing", ref, "video_voice", trace.OK if how in ("take", "lines") else trace.SKIPPED, voice=how)
            return how
        except Exception as e:
            trace.event(log, "marketing", ref, "video_voice", trace.FAILED, reason=str(e)[:200] or type(e).__name__)
            return "failed"

    async def _video_reel(self, job: dict, listing: dict, video: Path, out: Path, project: str, link_line: str,
                          sheet_facts: Optional[Dict[str, Any]] = None) -> dict:
        """The reel from the listing's own video, in the agent's brand. Rendered here (a minute or two); a failure is kept as
        a skipped reel with its reason, the campaign goes on. `sheet_facts`: for a voice-over when the video has no speech."""
        from app.modules.reels import video_reel
        from app.modules.reels.listing_reel import caption as reel_caption
        prof = await self.profiles.find_one({"agent_id": job["agent_id"]}) or {}
        who = identity.identity(prof, self.site, self.uploads_dir, job.get("language") or "en")
        brand_ = who.card_brand
        title = ", ".join(x for x in (project or listing.get("project_name") or listing.get("title") or "", listing.get("locality") or "") if x)
        from app.modules.reels import video_director
        dest = out / "reels" / "video.mp4"
        language = job.get("language") or "en"
        facts = {"project": project or listing.get("project_name") or "", "locality": listing.get("locality") or "",
                 "city": listing.get("city") or "", "property type": listing.get("property_type") or "",
                 "agent": brand_.name if brand_ else ""}
        try:
            edit = await video_director.plan(video, facts=facts, language=language,
                                             llm=self.llm_factory() if self.llm_factory else None)
            res = await asyncio.to_thread(video_reel.render, video, dest, title=title[:60], segments=edit.segments, hook=edit.hook,
                                          agent_name=brand_.name if brand_ else "", agent_logo=(brand_.logo or None) if brand_ else None)
        except Exception as e:
            log.warning("marketing run %s: video reel failed", job["_id"], exc_info=True)
            return {"kind": "video", "status": "skipped", "note": str(getattr(e, "args", [""])[0] or "not made")[:200]}
        from . import files
        heard = await files.video_claims(edit.speech, self.llm_factory() if self.llm_factory else None)
        if heard:   # what the presenter says, for the assistant (the builder's claims)
            await files.save_claims(self.listings, listing["_id"], video=heard, now=self.now())
        spoken = await self._voice_video(dest, sheet_facts, edit.speech, job["_id"]) if sheet_facts else "off"
        caption = (edit.caption + "\n\n" + "\n".join(who.contact)) if edit.caption else reel_caption(listing, "")
        return {"kind": "video", "status": "done", "seconds": res["seconds"], "removed_strip": bool(res["removed_strip"]),
                "voice": spoken,
                "edit": {"by": edit.source, "segments": edit.segments, "hook": edit.hook, "notes": edit.notes},
                "heard": heard,
                "video": "/uploads/" + dest.resolve().relative_to(self.uploads_dir.resolve()).as_posix(),
                "caption": caption + "\n\n" + link_line}

    async def _with_walkthrough(self, doc: Optional[dict]) -> Optional[dict]:
        """The run with its walkthrough reel's current state (the listing reel worker renders it separately)."""
        if not doc or self.reel_jobs is None:
            return doc
        reels = []
        for r in doc.get("reels") or []:
            if r.get("kind") == "walkthrough" and r.get("job_id") and r.get("status") not in ("done", "failed"):
                j = await self.reel_jobs.jobs.find_one({"_id": r["job_id"]})
                if j:
                    r = {**r, "status": j["status"], "video": j.get("video_path")}
            reels.append(r)
        return {**doc, "reels": reels}

    async def run(self, job: dict) -> None:
        """Step 1, then step 2. Never raises: a failure is stored with a message safe to show, keeping a finished step 1."""
        jid, step = job["_id"], "facts"
        started = time.monotonic()
        trace.event(log, "marketing", jid, "start", trace.OK, listing=job["listing_id"], agent=job["agent_id"],
                    lang=job.get("language") or "en")
        try:
            listing = await self.listings.find_one({"_id": job["listing_id"], "agent_id": job["agent_id"]})
            if not listing:
                trace.event(log, "marketing", jid, "done", trace.FAILED, reason="listing removed")
                return await self._set(jid, status="failed", error="The listing was removed.", finished_at=self.now())
            if job.get("mode") == "update":
                step = "update"
                return await self._update(job, listing)
            # step 1: the knowledge base and the page
            clients = self.clients_factory() if self.clients_factory else Clients(facts_store=self.facts_store)
            sheet = await gather({**listing, "id": listing["_id"]}, clients, self.now())
            listing_url = await self._page_url(job["agent_id"], job["listing_id"])
            # page first (docs/plan/project-pages.md): a registered project is marketed only once its own page exists
            regno, project_url = await self._project_page(sheet)
            summary = _summary(sheet)
            trace.event(log, "marketing", jid, "facts", trace.OK, usable=summary["usable"], held=summary["held"],
                        maharera=summary["maharera"] or "none", nearby=summary["nearby"], notes="; ".join(map(str, summary["notes"])) or None)
            if regno and not project_url:
                trace.event(log, "marketing", jid, "done", trace.FAILED, reason=f"project page for {regno} not ready")
                return await self._set(jid, status="failed", step="facts", facts=summary, page_url=listing_url,
                                       listing_url=listing_url, facts_done_at=self.now(), finished_at=self.now(),
                                       error=f"The facts are saved, but the project page for {regno} is not ready yet, so no "
                                             "posts were made. Please start marketing again in a few minutes.")
            page = project_url or listing_url
            out = self.uploads_dir / "campaigns" / _safe(job["listing_id"]) / jid[:8]
            llm = self.llm_factory() if self.llm_factory else None
            brochure = self._brochure(listing)
            # what is on offer (one plot or a layout, sizes, MahaRERA): filled in when certain, asked when not
            if not job.get("understood"):
                questions, changed = await self._understand(listing, sheet, brochure, llm)
                if questions:
                    return await self._set(jid, status="asking", step="facts", facts=summary, page_url=page,
                                           listing_url=listing_url, facts_done_at=self.now(), questions=questions)
                if changed:  # the facts are gathered again with what was filled in
                    listing = await self.listings.find_one({"_id": job["listing_id"]}) or listing
                    sheet = await gather({**listing, "id": listing["_id"]}, clients, self.now())
            await self._set(jid, status="posts", step="posts", facts=summary, page_url=page, listing_url=listing_url,
                            facts_done_at=self.now(), questions=[])
            # step 2: the posts, only now that the facts are kept
            step = "posts"
            dropped: Dict[str, Any] = {}
            # the agent's photos and video stills; renders and plans reach posts only through the kit (campaign.first_look)
            photos = await self._photo_pool(listing, out)
            previous = await self._live_posts(job, listing)
            plan_rows: List[dict] = []

            async def on_plan(chosen: List[dict], skipped: Dict[str, str]) -> None:
                plan_rows[:] = [{**c, "state": "planned"} for c in chosen]
                await self._set(jid, step="plan", plan=plan_rows, skipped=skipped)

            async def on_post(aid: str, change: dict) -> None:   # content: headline written; design: card made or dropped
                for r in plan_rows:
                    if r["angle"] == aid:
                        r.update({k: v for k, v in change.items() if v or k == "was"})
                await self._set(jid, step="content" if change["state"] == "content" else "design", plan=plan_rows)

            used: Dict[str, str] = {}
            pf = sheet.facts.get("project_name")
            names = job.get("names") or await campaign.project_name_for(
                str(pf.value or "") if pf is not None and pf.usable else "", job.get("language") or "en", llm)
            claims = list(((listing.get("file_claims") or {}).get("brochure")) or [])
            await self._set(jid, names=names, claims=claims)
            job = {**job, "names": names, "claims": claims}
            who = self._who(job, await self._identity(job))
            photo = await asyncio.to_thread(self._photo, listing)
            images = await self._brochure_images(job["agent_id"], job["listing_id"])
            kit = await self._kit(job["listing_id"], job["agent_id"])
            # the creative room pitches and chooses the campaign; without it (no model, another language, too few facts
            # surviving the check) the fixed angles make the posts as before
            room_doc, room_ctx = await self._room(job, listing, sheet.facts, photo, page, who, photos, images, kit, previous, llm)
            planned = room.briefs(room_doc, room_ctx, photos, images) if room_doc else None
            job = {**job, "room": room_doc}
            packs = await campaign.make(sheet.facts, out, llm=llm, photo=photo, link=page, dropped=dropped,
                                        photos=photos, previous=previous, on_plan=on_plan, on_post=on_post, used=used,
                                        images=images, kit=kit, planned=planned, **who)
            keys = {aid: campaign.brief_key(b) for aid, b in (planned or campaign.plan(sheet.facts, follow_ups=None, images=images,
                                                                                          kit=kit, **who))}
            ctx = campaign.Ctx(sheet.facts)
            where = ctx.where or "this property"
            link_line = campaign.link_line_for(where, job.get("language") or "en", ctx.registered)
            posts = await self._keep_edited({**job, "page_url": page, "link_line": link_line},
                                            [self._post(aid, p, keys.get(aid), used.get(aid, "none")) for aid, p in packs])
            trace.event(log, "marketing", jid, "posts", trace.OK if posts and not dropped else trace.FALLBACK if posts else trace.FAILED,
                        made=len(posts), by_llm=sum(1 for p in posts if p["used_llm"]), photo="none" if photo == "none" else "listing",
                        dropped="; ".join(f"{k}: {v}" for k, v in dropped.items()) or None)
            await self._set(jid, posts=posts, dropped={k: str(v)[:300] for k, v in dropped.items()}, inputs=self._inputs(listing),
                            link_line=link_line)
            # step 3 (best effort, never fails the run): reels from the best carousels, and the walkthrough reel
            step = "reels"
            await self._set(jid, step="reels")
            reels = await self._reels(job, listing, posts, out, ctx.project, link_line, pool=photos, facts=sheet.facts)
            await self._set(jid, reels=reels)
            # the master boost pair (best effort: a failure is kept as boost.error, the run is done either way)
            step = "boost"
            await self._make_boost(job, listing, sheet.facts, out, own=photos)
            await self._set(jid, status="done", reels=reels, error=None, finished_at=self.now())
            trace.event(log, "marketing", jid, "done", trace.OK, posts=len(posts), reels=len(reels),
                        seconds=time.monotonic() - started)
        except Exception as e:
            log.exception("marketing run %s failed in step %s", jid, step)
            trace.event(log, "marketing", jid, "done", trace.FALLBACK if step == "reels" else trace.FAILED, failed_step=step,
                        error=type(e).__name__, reason=str(e) or type(e).__name__, seconds=time.monotonic() - started)
            msg = ("Could not gather the property facts. Please try again." if step == "facts"
                   else "The facts are saved, but the posts could not be made. Please try again." if step == "posts"
                   else "The posts are ready, but the reels could not be made.")
            if step == "boost":
                return await self._set(jid, status="done", error=None, finished_at=self.now())
            if step == "reels":  # the posts are made: the run is usable without reels
                return await self._set(jid, status="done", reels=[], error=msg, finished_at=self.now())
            if step == "update":  # the earlier run's posts are still there: usable as they are
                return await self._set(jid, status="done", error="The change could not be applied to the posts. Please try again.",
                                       finished_at=self.now())
            await self._set(jid, status="failed", error=msg, finished_at=self.now())

    async def _room(self, job: dict, listing: dict, facts: Dict[str, Any], photo: str, page: str, who: Dict[str, Any],
                    photos: Sequence[str], images: Sequence[Dict[str, Any]], kit: Optional[dict], previous: Sequence[str],
                    llm: Any) -> tuple:
        """(the creative room's work, the Ctx its briefs are made with), or (None, None): no model, a Marathi or Hindi run,
        CREATIVE_ROOM=off, or too little surviving the fact check. Kept on the run as `room` (Studio shows the brief, the
        pitches and the chosen campaign). A run made for a pitch the agent picked (`pick`) reuses the earlier brief and pitches."""
        live = getattr(self.llm_factory, "__name__", "") == "default_llm"   # the room meets on the real models only (tests use the angles)
        if llm is None or not live or (job.get("language") or "en") != "en" or os.environ.get("CREATIVE_ROOM", "on").lower() == "off":
            return None, None
        ctx = campaign.Ctx(facts, photo, page, who.get("voice"), who.get("card_brand"), who.get("contact") or (), "en", previous,
                           who.get("names"), who.get("claims") or (), None, images, kit)
        await self._set(job["_id"], step="room")
        try:
            from app.platform.llm import critical_llm   # Gemini first for the room
            llm = critical_llm() or llm
            doc = await room.convene(ctx, listing, llm, photos=len(photos), images=images, pick=job.get("pick"),
                                     earlier=job.get("earlier_room"))
        except Exception as e:
            trace.event(log, "marketing", job["_id"], "room", trace.FAILED, reason=str(e)[:200] or type(e).__name__, exc_info=True)
            return None, None
        if doc is None:
            trace.event(log, "marketing", job["_id"], "room", trace.FALLBACK, reason="no campaign survived the fact check")
            return None, None
        camp = doc["campaign"]
        trace.event(log, "marketing", job["_id"], "room", trace.OK, pitches=len(doc.get("pitches") or []), chosen=doc.get("chosen"),
                    campaign=camp["name"], pieces=len(camp["pieces"]), reels=sum(1 for p in camp["pieces"] if p.get("reel")))
        await self._set(job["_id"], room=doc)
        return doc, ctx

    def _post(self, aid: str, pack, key: Optional[str], photo: str) -> dict:
        """A post as kept on the run; `brief` (what it says) and `photo` (photo or none) let a later change remake only the
        posts it touches."""
        imgs = ["/uploads/" + Path(i).resolve().relative_to(self.uploads_dir.resolve()).as_posix() for i in pack.images]
        kind = "none" if photo in ("", "none") else "photo"
        return {"angle": aid, "layout": pack.design.get("layout"), "format": pack.design.get("format"), "images": imgs,
                "caption": pack.caption, "used_llm": pack.used_llm, "prompts": pack.prompts, "brief": key, "photo": kind}

    async def _keep_edited(self, job: dict, posts: List[dict]) -> List[dict]:
        """A full run made over an earlier one: the earlier posts the agent edited or the owner approved stay (stale, the new
        one as `newer`); planned calendar rows of the others take the new posts."""
        base = await self.runs.find_one({"_id": job["base_run"]}) if job.get("base_run") else None
        if not base:
            return posts
        old = {p["angle"]: p for p in base.get("posts") or []}
        locked = await self._locked(job)
        out = [await self._place(job, old[p["angle"]], p, locked) if p["angle"] in old else p for p in posts]
        made = {p["angle"] for p in posts}
        return out + [{**p, "stale": True} for a, p in old.items() if a not in made and (p.get("edited") or a in locked)]

    async def _update(self, job: dict, listing: dict) -> None:
        """An update run: the earlier run's posts, remaking only what changed since its `inputs`. New photos remake the posts
        without a photo; changed facts remake the posts whose text they change; a new video makes only the video reel. A new
        brochure remakes nothing (posts are not made from the PDF)."""
        jid = job["_id"]
        changes = self._changes(job.get("inputs") or {}, self._inputs(listing))
        out = self.uploads_dir / "campaigns" / _safe(job["listing_id"]) / jid[:8]
        posts, reels, redone = [dict(p) for p in job.get("posts") or []], list(job.get("reels") or []), []
        llm = self.llm_factory() if self.llm_factory else None
        sheet = None
        if set(changes) & {"facts", "photos"}:
            clients = self.clients_factory() if self.clients_factory else Clients(facts_store=self.facts_store)
            sheet = await gather({**listing, "id": listing["_id"]}, clients, self.now())
            await self._set(jid, status="posts", step="posts", changes=changes, facts=_summary(sheet), questions=[])
            who = self._who(job, await self._identity(job))
            briefs = dict(campaign.plan(sheet.facts, "none", job.get("page_url") or "", follow_ups=None, **who))
            own = await self._photo_pool(listing, out)
            locked = await self._locked(job)
            for i, p in enumerate(posts):
                b = briefs.get(p["angle"])
                key = campaign.brief_key(b) if b else None
                why = ("facts" if key and (key != p["brief"] if p.get("brief") else "facts" in changes) else
                       "photos" if "photos" in changes and p.get("photo") == "none" and own else "")
                if not (why and b):
                    continue
                photo = own[i % len(own)] if own else self._photo(listing)
                b = replace(b, photo=photo)
                if llm is not None and b.hooks:
                    b = await campaign.sharpen(b, llm)
                pack = await campaign.pipeline.make(b, "buyer", "instagram", llm, seed=i, out_dir=out / _safe(p["angle"]),
                                                    reviewer=None)
                if not pack.report.get("ok"):
                    log.info("marketing update %s: %s not remade: %s", jid, p["angle"], pack.report.get("problems"))
                    continue
                posts[i] = await self._place(job, p, self._post(p["angle"], pack, key, photo), locked)
                redone.append(p["angle"])
        if "video" in changes:
            video = self._video(listing)
            reels = [r for r in reels if r.get("kind") != "video"]
            if video:
                reels.append(await self._video_reel(job, listing, video, out, "", job.get("link_line") or ""))
        await self._set(jid, posts=posts, reels=reels, redone=redone)
        await self._update_boost(job, listing, sheet, out, changes)
        await self._set(jid, status="done", step="reels", changes=changes, posts=posts, reels=reels, redone=redone,
                        inputs=self._inputs(listing), error=None, finished_at=self.now())

    # ---- the master boost pair (boost.py) -------------------------------------------------------------------------------
    async def _make_boost(self, job: dict, listing: dict, facts: Dict[str, Any], out: Path, own: List[str]) -> None:
        """Make the boost pair and keep it on the run as `boost`; never raises (a failure is boost.error, state failed)."""
        from . import boost
        jid = job["_id"]
        before = (await self.runs.find_one({"_id": jid}) or job).get("boost") or {}
        await self._set(jid, boost={**before, "state": "making", "error": None}, boost_queued=False)
        try:
            prof = await self.profiles.find_one({"agent_id": job["agent_id"]}) or {}
            who = await self._identity(job)
            dest = out / "boost" / self.now().strftime("%Y%m%d%H%M%S")
            made = await boost.make(self.db, facts=facts, listing=listing, agent_id=job["agent_id"], out=dest,
                                    uploads_dir=self.uploads_dir, language=job.get("language") or "en", photos=own, profile=prof,
                                    brand_name=who.card_brand.name if who.card_brand else "", card_brand=who.card_brand,
                                    reel_renderer=self.boost_renderer, now=self.now)
            if before.get("state") in ("boosted", "finished") or before.get("boosted_at"):   # a remade pair keeps the spend
                made.update({k: before.get(k) for k in ("boosted_at", "daily_spend_inr", "days", "reel_permalink")})
                made["state"] = "boosted"
            await self._set(jid, boost=made)
        except Exception as e:
            log.warning("marketing run %s: boost pair failed", jid, exc_info=True)
            await self._set(jid, boost={**before, "state": "failed",
                                        "error": "The boost reel and carousel could not be made: " + str(e)[:200]})

    async def _update_boost(self, job: dict, listing: dict, sheet, out: Path, changes: List[str]) -> None:
        """An update run remakes the boost pair only when what it says or shows changed (boost.key); never raises."""
        from . import boost
        try:
            if not (set(changes) & {"facts", "photos", "video"}):
                return
            if sheet is None:
                clients = self.clients_factory() if self.clients_factory else Clients(facts_store=self.facts_store)
                sheet = await gather({**listing, "id": listing["_id"]}, clients, self.now())
            own = await self._photo_pool(listing, out)
            old = job.get("boost") or {}
            if old.get("key") and old["key"] == boost.key(sheet.facts, own, job.get("language") or "en"):
                return
            await self._make_boost(job, listing, sheet.facts, out, own)
        except Exception:
            log.warning("marketing update %s: boost pair not remade", job["_id"], exc_info=True)

    async def _with_boost(self, doc: Optional[dict]) -> Optional[dict]:
        """The boost pair with what time made of it: ready_at (48 h after the first post went out), the reel's permalink when
        it was posted through the calendar, and "finished" once the boost's days are over."""
        b = (doc or {}).get("boost")
        if not b or b.get("state") in ("making", "failed"):
            return doc
        from app.modules.calendar.store import Store as CalendarStore
        from .boost import READY_AFTER_H
        cal, first, permalink = CalendarStore(self.db), None, b.get("reel_permalink")
        naive = lambda t: t.astimezone(timezone.utc).replace(tzinfo=None) if t.tzinfo else t
        for c in doc.get("calendar") or []:
            row = await cal.get(c.get("row_id") or "")
            if not row or row.get("status") != "published":
                continue
            at = row.get("published_at")
            if isinstance(at, datetime):
                first = naive(at) if first is None or naive(at) < first else first
            if c.get("angle") == "boost_reel" and row.get("permalink"):
                permalink = row["permalink"]
        b = {**b, "ready_at": first + timedelta(hours=READY_AFTER_H) if first else None, "reel_permalink": permalink}
        at = b.get("boosted_at")
        if b.get("state") == "boosted" and isinstance(at, datetime) and b.get("days"):
            if self.now() >= naive(at) + timedelta(days=int(b["days"])):
                b["state"] = "finished"
        return {**doc, "boost": b}

    async def boost(self, agent_id: str, listing_id: str, daily_spend_inr: int, days: int) -> dict:
        """The agent boosted the pair on Meta (by hand, through meta_open_url): kept for the results' spend."""
        if not (1 <= int(daily_spend_inr) <= 100000 and 1 <= int(days) <= 90):
            raise RunError("Give a daily spend between 1 and 100000 rupees and 1 to 90 days.", 422)
        run = await self.latest(agent_id, listing_id)
        if not run or (run.get("boost") or {}).get("state") not in ("ready", "boosted", "finished"):
            raise RunError("The boost reel and carousel are not ready yet.", 409)
        kept = (await self.runs.find_one({"_id": run["_id"]}) or {}).get("boost") or {}
        b = {**kept, "state": "boosted", "boosted_at": self.now(), "daily_spend_inr": int(daily_spend_inr), "days": int(days)}
        await self._set(run["_id"], boost=b)
        return await self._with_boost({**run, "boost": b})

    async def remake_boost(self, agent_id: str, listing_id: str) -> dict:
        """Make only the boost pair again, in the background (the worker picks it up; state "making" meanwhile)."""
        run = await self.latest(agent_id, listing_id)
        if not run or run["status"] != "done":
            raise RunError("Make the posts first.", 409)
        if (run.get("boost") or {}).get("state") == "making":
            return run
        kept = (await self.runs.find_one({"_id": run["_id"]}) or {}).get("boost") or {}
        b = {**kept, "state": "making", "error": None}
        await self._set(run["_id"], boost=b, boost_queued=True)
        return {**run, "boost": b}

    async def claim_boost(self) -> Optional[dict]:
        doc = await self.runs.find_one({"boost_queued": True})
        if not doc:
            return None
        res = await self.runs.update_one({"_id": doc["_id"], "boost_queued": True}, {"$set": {"boost_queued": False}})
        if res is not None and getattr(res, "modified_count", 1) == 0:
            return None
        return doc

    async def run_boost(self, job: dict) -> None:
        """A remake asked from Studio: the facts again (kept, so quick), the property's pictures, then the pair. Never raises."""
        try:
            listing = await self.listings.find_one({"_id": job["listing_id"], "agent_id": job["agent_id"]})
            if not listing:
                raise RunError("The listing was removed.")
            clients = self.clients_factory() if self.clients_factory else Clients(facts_store=self.facts_store)
            sheet = await gather({**listing, "id": listing["_id"]}, clients, self.now())
            out = self.uploads_dir / "campaigns" / _safe(job["listing_id"]) / job["_id"][:8]
            await self._make_boost(job, listing, sheet.facts, out, await self._photo_pool(listing, out))
        except Exception as e:
            log.warning("boost remake %s failed", job["_id"], exc_info=True)
            await self._set(job["_id"], boost={**(job.get("boost") or {}), "state": "failed",
                                               "error": "The boost pair could not be made again: " + str(getattr(e, "detail", "") or e)[:200]})

    async def _live_posts(self, job: dict, listing: dict) -> List[str]:
        """Opening lines of this property's posts that are already published, newest first: those of this listing's earlier
        runs, and any live post that names the project (a listing made again for the same project). [] on any failure."""
        try:
            ids: List[str] = []
            async for r in self.runs.find({"listing_id": listing["_id"], "_id": {"$ne": job["_id"]}}, {"calendar": 1}):
                ids += [c["row_id"] for c in r.get("calendar") or [] if c.get("row_id")]
            flt: List[dict] = [{"_id": {"$in": ids}}] if ids else []
            name = (listing.get("project_name") or "").strip()
            if len(name) >= 4:
                flt.append({"caption": {"$regex": re.escape(name), "$options": "i"}})
            if not flt:
                return []
            rows = await self.db.get_collection("content_calendar").find(
                {"status": "published", "$or": flt}, {"caption": 1, "channel": 1}).sort("published_at", -1).to_list(40)
            out: List[str] = []
            for row in rows:
                first = next((ln.strip() for ln in (row.get("caption") or "").splitlines() if ln.strip()), "")
                if first and first not in out:
                    out.append(first[:160])
            return out[:12]
        except Exception:
            log.warning("marketing: could not read the live posts of listing %s", listing.get("_id"), exc_info=True)
            return []

    async def _understand(self, listing: dict, sheet, brochure: Dict[str, Any], llm) -> tuple:
        """(questions, changed): reads the listing and the builder's claims (understand.py), sets what is certain on the
        listing and returns what the agent must answer. Never raises: a failure asks nothing."""
        try:
            # a brochure only a small model could read: its numbers are not put to the agent as questions
            claims = [] if brochure.get("weak") else list(brochure.get("claims") or [])
            claims += list(((listing.get("file_claims") or {}).get("video")) or [])
            seen = await understand.read(listing, claims, llm)
            kind = (brochure.get("kind") or {}).get("kind")
            if kind:   # the brochure's own words, checked by code (brochure_doc.offer_kind), outrank the model's reading
                seen["property_type"] = kind
            listing = await self._selling_points(listing, brochure)
            rera = sheet.facts.get("rera_no")
            units = sheet.facts.get("units_total")
            files = self._has_files(listing)
            auto, questions = understand.decide(listing, seen, bool(rera and rera.usable),
                                                units.value if units and units.usable and isinstance(units.value, int) else None,
                                                has_files=files,
                                                candidates=_choices(sheet.match), points=points.pending(listing))
            if auto:
                await self.listings.update_one({"_id": listing["_id"]}, {"$set": auto})
            return questions, bool(auto)
        except Exception:
            log.warning("marketing: understanding listing %s failed", listing.get("_id"), exc_info=True)
            return [], False

    async def _selling_points(self, listing: dict, brochure: Dict[str, Any]) -> dict:
        """A listing without selling points whose brochure this run read (no AI draft made them): the same points the draft
        would offer, kept on the listing unconfirmed (the agent is asked before any is posted)."""
        if listing.get("selling_points") or brochure.get("weak") or not brochure.get("facts"):
            return listing
        sp = points.selling_points(brochure["facts"], brochure.get("language") or "en", listing.get("property_type"))
        if sp:
            sp = [{**p, "confirmed": False} for p in sp]
            await self.listings.update_one({"_id": listing["_id"]}, {"$set": {"selling_points": sp}})
            listing = {**listing, "selling_points": sp}
        return listing

    async def answer(self, agent_id: str, listing_id: str, key: str, value: Any) -> dict:
        """The agent's answer to one question: the listing gets the field, the question goes. The last answer queues the run
        again; it then gathers the facts with the answers and makes the posts without asking again."""
        listing = await self._listing(agent_id, listing_id)
        run = await self._latest({"listing_id": listing_id, "agent_id": agent_id})
        if not run or run["status"] != "asking":
            raise RunError("There is no question waiting for this listing.", 409)
        if key not in {q["key"] for q in run.get("questions") or []}:
            raise RunError("That question was already answered.", 409)
        if key == "files" and value == "added" and not self._has_files(listing):
            raise RunError("Nothing was uploaded yet. Add the brochure or video, or choose Go on without.", 422)
        try:
            fields = (understand.answer_points(listing, value) if key == "selling_points"
                      else understand.fill_size(listing, understand.apply_answer(key, value)))
        except ValueError as e:
            raise RunError(str(e), 422)
        if fields:
            await self.listings.update_one({"_id": listing_id}, {"$set": fields})
        left = [q for q in run["questions"] if q["key"] != key]
        change: Dict[str, Any] = {"questions": left, f"answers.{key}": value}
        if key == "files" and value == "added":  # start over: read the new files, then ask again only what they leave open
            change.update(status="queued", questions=[], understood=False, started_at=None, files={})
        elif not left:
            change.update(status="queued", understood=True, started_at=None)
        await self.runs.update_one({"_id": run["_id"], "status": "asking"}, {"$set": change})
        return await self.runs.find_one({"_id": run["_id"]})

    async def run_once(self) -> bool:
        job = await self.claim()
        if job:
            await self.run(job)
            return True
        job = await self.claim_boost()   # a boost pair asked again from Studio
        if job:
            await self.run_boost(job)
            return True
        job = await self.claim_reels()   # the ad reels asked again from Studio
        if job:
            await self.run_reels(job)
            return True
        return False


# ---- the background worker --------------------------------------------------------------------------------------------
def default_runs() -> MarketingRuns:
    from app.core.config import settings
    from app.core.database import get_database
    from app.modules.agentprojects.groups import Groups
    from app.modules.newsroom.store import Store
    from app.platform.llm import default_llm
    db = get_database()
    from app.modules.reels.listing_reel import ReelJobs
    from .pin import Pins
    from .surroundings import Nearby
    uploads = Path(settings.upload_directory)
    return MarketingRuns(db, uploads, settings.public_site_url,
                         clients_factory=lambda: Clients(register=Store(db), facts_store=FactsStore(db),
                                                         brochures=Brochures(db, uploads), groups=Groups(db),
                                                         pins=Pins(db, settings.google_maps_api_key),
                                                         nearby=Nearby(settings.google_maps_api_key)),
                         llm_factory=default_llm,
                         reel_jobs=ReelJobs(db, Path(settings.upload_directory), llm_factory=default_llm))


def _get_database():
    from app.core.database import get_database
    return get_database()


async def loop(make_runs: Callable[[], MarketingRuns] = default_runs, poll: float = 3.0, get_db: Callable = _get_database) -> None:
    """Run queued jobs one at a time, forever, under the 'marketing_runs' runner lease (app/worker.py)."""
    from app.platform.heartbeats import heartbeat
    try:
        await make_runs().fail_stale()
    except Exception:
        log.exception("marketing runs: could not clean up stale jobs")
    while True:
        try:
            async with heartbeat("marketing_runs", get_db, every_s=HEARTBEAT_EVERY_S):
                busy = await make_runs().run_once()
            if busy:
                continue
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("marketing runs loop error")
        await asyncio.sleep(poll)


_task: Optional[asyncio.Task] = None


def ensure_worker() -> Optional[asyncio.Task]:
    """Start the loop in this process when RUN_BACKGROUND_LOOPS is on (development); otherwise app/worker.py runs it."""
    global _task
    from app.core.config import settings
    if not settings.run_background_loops:
        return None
    if _task is None or _task.done():
        from app.core.database import get_database
        from app.platform.leases import run_as_leader
        _task = asyncio.get_running_loop().create_task(run_as_leader("marketing_runs", loop, get_database))
    return _task
