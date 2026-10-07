"""Start marketing a listing (Studio): one queued job, two steps in order.

    1. facts  - gather the property's knowledge base (our MahaRERA register first, then MahaRERA, OpenStreetMap, calculators)
                and keep it; the listing's page then shows "Checked for you" (VerifiedFacts) from it.
    2. posts  - only once step 1 is done: the campaign (one post per angle the facts support), rendered as drafts.
                Nothing publishes from here: posting goes through approval.

Jobs live in `marketing_runs`; the worker loop "marketing_runs" (app/worker.py) runs one at a time under its runner lease.
A job interrupted by a restart is marked failed after STALE_AFTER, keeping whatever step already finished."""
import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import campaign, identity
from .facts import USABLE
from .gather import Clients, gather
from .store import FactsStore, facts_of

log = logging.getLogger(__name__)

COLLECTION = "marketing_runs"
MARKETABLE = ("live", "under_offer")
ACTIVE = ("queued", "facts", "posts")
SLIDE_REELS = 2  # slides reels per campaign, from its first carousel posts
CAPTION_MAX = 2200  # Instagram's caption limit
NOTE_MAX = 300
STALE_AFTER = timedelta(minutes=20)
HEARTBEAT_EVERY_S = 60.0
HEARTBEAT_INTERVAL_S = STALE_AFTER.total_seconds()


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
    posts = [{**p, "images": [base + i if base and i.startswith("/") else i for i in p.get("images", [])]}
             for p in doc.get("posts") or []]
    return {"id": doc["_id"], "listing_id": doc["listing_id"], "status": doc["status"], "step": doc.get("step"),
            "language": doc.get("language") or "en",
            "facts": doc.get("facts"), "page_url": doc.get("page_url"), "listing_url": doc.get("listing_url"), "posts": posts, "dropped": doc.get("dropped") or {},
            "error": doc.get("error") or "", "created_at": _iso(doc.get("created_at")),
            "calendar": [{**c, "due_at": _iso(c.get("due_at"))} for c in doc.get("calendar") or []],
            "reels": [{**r, "video": (base + r["video"] if base and (r.get("video") or "").startswith("/") else r.get("video"))}
                      for r in doc.get("reels") or []],
            "facts_done_at": _iso(doc.get("facts_done_at")), "finished_at": _iso(doc.get("finished_at"))}


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(s))[:40] or "x"


def _rel(url_path: str) -> str:
    return url_path[len("/uploads/"):] if url_path.startswith("/uploads/") else url_path.lstrip("/")


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
                 slides_renderer: Optional[Callable] = None, reel_jobs: Any = None, facts_store: Any = None,
                 page_for: Optional[Callable] = None, enrich_now: Optional[Callable] = None):
        """`slides_renderer(paths, out, hook=, kicker=)` makes a slides reel (default reels.slides.make_slides_reel);
        `reel_jobs` (reels.listing_reel.ReelJobs) queues the walkthrough reel; None skips it;
        `page_for(db, regno)` finds a project's own page (default areastats.pages.page_for); `enrich_now(db, regno, by=)` asks
        for that page's text to be written soon (default areastats.enrich.enrich_now)."""
        self.db = db
        self.runs = db.get_collection(COLLECTION)
        self.listings = db.get_collection("listings")
        self.profiles = db.get_collection("agent_public_profiles")
        self.uploads_dir, self.site = Path(uploads_dir), site.rstrip("/")
        self.clients_factory, self.llm_factory, self.now = clients_factory, llm_factory, now
        self.slides_renderer, self.reel_jobs = slides_renderer, reel_jobs
        self.facts_store = facts_store or FactsStore(db)
        self.page_for, self.enrich_now = page_for, enrich_now

    async def _listing(self, agent_id: str, listing_id: str) -> dict:
        doc = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise RunError("Listing not found", 404)
        return doc

    async def _latest(self, flt: dict) -> Optional[dict]:
        docs = await self.runs.find(flt).sort("created_at", -1).limit(1).to_list(1)
        return docs[0] if docs else None

    async def create(self, agent_id: str, listing_id: str, again: bool = False, language: str = "en") -> tuple:
        """(job, created). A running job is returned as it is; a finished one too unless `again`, the listing changed or
        another language is asked for (en, mr, hi: the posts' language)."""
        listing = await self._listing(agent_id, listing_id)
        if listing.get("status") not in MARKETABLE:
            raise RunError("Publish this listing first: only live or under-offer listings can be marketed.", 409)
        flt = {"listing_id": listing_id, "agent_id": agent_id}
        active = await self._latest({**flt, "status": {"$in": list(ACTIVE)}})
        if active:
            return active, False
        if not again:
            done = await self._latest({**flt, "status": "done"})
            changed = listing.get("updated_at")
            if done and (done.get("language") or "en") == language and not (isinstance(changed, datetime) and changed > done["created_at"]):
                return done, False
        doc = {"_id": uuid.uuid4().hex, **flt, "status": "queued", "step": "facts", "language": language, "facts": None, "page_url": None, "posts": [],
               "dropped": {}, "error": None, "created_at": self.now(), "started_at": None, "facts_done_at": None,
               "finished_at": None}
        await self.runs.insert_one(doc)
        return doc, True

    async def latest(self, agent_id: str, listing_id: str) -> Optional[dict]:
        await self._listing(agent_id, listing_id)
        return await self._with_walkthrough(await self._latest({"listing_id": listing_id, "agent_id": agent_id}))

    async def to_calendar(self, agent_id: str, listing_id: str, start=None) -> dict:
        """Send the latest finished run's posts to the approval calendar as planned rows (schedule.queue). Idempotent."""
        from app.modules.calendar.store import Store as CalendarStore

        from . import schedule
        run = await self.latest(agent_id, listing_id)
        if not run or run["status"] != "done" or not run.get("posts"):
            raise RunError("Make the posts first: start marketing and wait until the posts are ready.", 409)
        first = start or (self.now() + timedelta(days=1)).date()
        added = await schedule.queue(CalendarStore(self.db), run, run.get("link_line") or "", first)
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
        """Planned calendar rows of this post take the new caption (Facebook's with its page link) and images."""
        from app.modules.calendar.store import Store as CalendarStore

        from .schedule import _rel, facebook_caption
        cal, n = CalendarStore(self.db), 0
        for c in run.get("calendar") or []:
            if c.get("angle") != angle or c.get("kind", "post") != "post":
                continue
            text = caption if c["channel"] == "instagram" else facebook_caption(caption, run.get("link_line") or "",
                                                                                 run.get("page_url") or "", angle)
            n += await cal.set_planned(c["row_id"], caption=text, images=[_rel(i) for i in images] if images else None)
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
        briefs = dict(campaign.plan(await self._facts(run, listing), **self._who(run, who)))
        corpus = briefs[angle].corpus() if angle in briefs else ""
        checked = "\n".join(line for line in caption.splitlines() if line.strip() not in who.contact)  # code-made contact block
        problems = [p for p in problems_in(checked, corpus, allow_url=True) if p != "url"] if corpus else []
        posts = list(run["posts"])
        posts[idx] = {**posts[idx], "caption": caption, "edited": True, "edited_at": self.now()}
        await self._set(run["_id"], posts=posts)
        synced = await self._sync_calendar(run, angle, caption)
        return {**run, "posts": posts, "synced": synced}, problems

    async def redo_post(self, agent_id: str, listing_id: str, angle: str, note: str) -> dict:
        """Make this post again with the agent's note (the copywriter's feedback), from the kept facts, under every guard."""
        note = (note or "").strip()[:NOTE_MAX]
        run, idx = await self._done_run(agent_id, listing_id, angle)
        listing = await self._listing(agent_id, listing_id)
        briefs = dict(campaign.plan(await self._facts(run, listing), self._photo(listing), run.get("page_url") or "",
                                    **self._who(run, await self._identity(run))))
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
                      "edited": False, "redos": n,
                      "note": note, "redone_at": self.now()}
        await self._set(run["_id"], posts=posts)
        synced = await self._sync_calendar(run, angle, pack.caption, imgs)
        return {**run, "posts": posts, "synced": synced}

    # ---- worker side ------------------------------------------------------------------------------------------------
    async def fail_stale(self) -> None:
        cutoff = self.now() - STALE_AFTER
        for d in await self.runs.find({"status": {"$in": ["facts", "posts"]}}).to_list(100):
            if isinstance(d.get("started_at"), datetime) and d["started_at"] < cutoff:
                await self.runs.update_one({"_id": d["_id"], "status": d["status"]}, {"$set": {
                    "status": "failed", "error": "Marketing was interrupted. Please start it again.", "finished_at": self.now()}})

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
        return {"voice": who.voice, "card_brand": who.card_brand, "contact": who.contact, "language": run.get("language") or "en"}

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
        name = sheet.facts["project_name"].value if "project_name" in sheet.facts else ""
        try:
            from app.modules.areastats.watch import WatchItem, watch
            from app.modules.newsroom.store import Store as Register
            await watch(Register(self.db), WatchItem(regno, int(m.group(1)) if m else None, name), "property_facts", self.now())
        except Exception:
            log.warning("marketing: could not add %s to the register's watch list", regno, exc_info=True)
        await self._enrich_soon(regno)
        page_for = self.page_for
        if page_for is None:
            try:
                from app.modules.areastats.pages import page_for
            except ImportError:  # project pages not deployed yet: nothing is marketed without its page
                return regno, None
        page = await page_for(self.db, regno)
        return regno, (page or {}).get("url")

    def _photo(self, listing: dict) -> str:
        """The listing's first photo as a local file for the cards, or "none" (never a stock photo of something else)."""
        from app.modules.marketing.images import first_photo_url, local_upload_path
        p = local_upload_path(first_photo_url(listing.get("media") or []), self.uploads_dir)
        return str(p) if p and Path(p).is_file() else "none"

    async def _reels(self, job: dict, listing: dict, posts: List[dict], out: Path, project: str, link_line: str) -> List[dict]:
        """Slides reels from up to SLIDE_REELS carousel posts, and the walkthrough reel job. Each one that fails is skipped."""
        render = self.slides_renderer
        if render is None:
            from app.modules.reels.slides import make_slides_reel as render
        reels: List[dict] = []
        for p in [p for p in posts if len(p["images"]) >= 3][:SLIDE_REELS]:
            dest = out / "reels" / f"{_safe(p['angle'])}.mp4"
            try:
                await asyncio.to_thread(render, [self.uploads_dir / _rel(i) for i in p["images"]], dest,
                                        hook=(p["caption"].splitlines() or [""])[0], kicker=(project or "").upper()[:28] or None)
                reels.append({"kind": "slides", "angle": p["angle"], "caption": p["caption"],
                              "video": "/uploads/" + dest.resolve().relative_to(self.uploads_dir.resolve()).as_posix()})
            except Exception:
                log.warning("marketing run %s: slides reel %s failed", job["_id"], p["angle"], exc_info=True)
        if self.reel_jobs is not None:
            try:
                from app.modules.reels.listing_reel import caption as reel_caption
                doc, _ = await self.reel_jobs.create(job["agent_id"], job["listing_id"], "en")
                reels.append({"kind": "walkthrough", "job_id": doc["_id"], "status": doc["status"], "video": doc.get("video_path"),
                              "caption": reel_caption(listing, "") + "\n\n" + link_line})
            except Exception as e:  # fewer than 2 photos, the daily limit...: the campaign goes on without it
                reels.append({"kind": "walkthrough", "status": "skipped", "note": str(getattr(e, "detail", "") or "not made")})
        return reels

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
        try:
            listing = await self.listings.find_one({"_id": job["listing_id"], "agent_id": job["agent_id"]})
            if not listing:
                return await self._set(jid, status="failed", error="The listing was removed.", finished_at=self.now())
            # step 1: the knowledge base and the page
            clients = self.clients_factory() if self.clients_factory else Clients(facts_store=self.facts_store)
            sheet = await gather({**listing, "id": listing["_id"]}, clients, self.now())
            listing_url = await self._page_url(job["agent_id"], job["listing_id"])
            # page first (docs/plan/project-pages.md): a registered project is marketed only once its own page exists
            regno, project_url = await self._project_page(sheet)
            if regno and not project_url:
                return await self._set(jid, status="failed", step="facts", facts=_summary(sheet), page_url=listing_url,
                                       listing_url=listing_url, facts_done_at=self.now(), finished_at=self.now(),
                                       error=f"The facts are saved, but the project page for {regno} is not ready yet, so no "
                                             "posts were made. Please start marketing again in a few minutes.")
            page = project_url or listing_url
            await self._set(jid, status="posts", step="posts", facts=_summary(sheet), page_url=page, listing_url=listing_url,
                            facts_done_at=self.now())
            # step 2: the posts, only now that the facts are kept
            step = "posts"
            out = self.uploads_dir / "campaigns" / _safe(job["listing_id"]) / jid[:8]
            dropped: Dict[str, Any] = {}
            llm = self.llm_factory() if self.llm_factory else None
            packs = await campaign.make(sheet.facts, out, llm=llm, photo=self._photo(listing), link=page, dropped=dropped,
                                        **self._who(job, await self._identity(job)))
            posts: List[dict] = []
            for aid, p in packs:
                imgs = ["/uploads/" + Path(i).resolve().relative_to(self.uploads_dir.resolve()).as_posix() for i in p.images]
                posts.append({"angle": aid, "layout": p.design.get("layout"), "format": p.design.get("format"), "images": imgs,
                              "caption": p.caption, "used_llm": p.used_llm, "prompts": p.prompts})
            ctx = campaign.Ctx(sheet.facts)
            where = ctx.where or "this property"
            await self._set(jid, posts=posts, dropped={k: str(v)[:300] for k, v in dropped.items()},
                            link_line=campaign.link_line_for(where, job.get("language") or "en"))
            # step 3 (best effort, never fails the run): reels from the best carousels, and the walkthrough reel
            step = "reels"
            reels = await self._reels(job, listing, posts, out, ctx.project, campaign.link_line_for(where, job.get("language") or "en"))
            await self._set(jid, status="done", reels=reels, error=None, finished_at=self.now())
        except Exception:
            log.exception("marketing run %s failed in step %s", jid, step)
            msg = ("Could not gather the property facts. Please try again." if step == "facts"
                   else "The facts are saved, but the posts could not be made. Please try again." if step == "posts"
                   else "The posts are ready, but the reels could not be made.")
            if step == "reels":  # the posts are made: the run is usable without reels
                return await self._set(jid, status="done", reels=[], error=msg, finished_at=self.now())
            await self._set(jid, status="failed", error=msg, finished_at=self.now())

    async def run_once(self) -> bool:
        job = await self.claim()
        if not job:
            return False
        await self.run(job)
        return True


# ---- the background worker --------------------------------------------------------------------------------------------
def default_runs() -> MarketingRuns:
    from app.core.config import settings
    from app.core.database import get_database
    from app.modules.newsroom.store import Store
    from app.platform.llm import default_llm
    db = get_database()
    from app.modules.reels.listing_reel import ReelJobs
    return MarketingRuns(db, Path(settings.upload_directory), settings.public_site_url,
                         clients_factory=lambda: Clients(register=Store(db), facts_store=FactsStore(db)), llm_factory=default_llm,
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
