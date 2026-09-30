"""Process new comments on the Page. State lives in `engage_comments` (_id = Facebook comment id), so every comment is handled once.

Guard rails: the whole thing is off unless ENGAGE_ENABLED; in dry-run mode it only records what it WOULD say; replies are capped per hour and
per person per day; our own comments, threaded replies, spam and abuse are never answered; questions the post cannot answer go to a person.
"""
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from urllib.parse import quote

from app.modules.marketing.facts import Facts

from .brain import Decision, decide
from .config import EngageConfig
from .graph import EngageGraphError

log = logging.getLogger(__name__)
MAX_COMMENT_AGE = timedelta(days=7)


def with_source(url: str, source: str = "facebook_comment") -> str:
    """Add ?src=<source> before any #fragment."""
    if not url:
        return url
    base, _, frag = url.partition("#")
    base += ("&" if "?" in base else "?") + "src=" + quote(source)
    return base + ("#" + frag if frag else "")


def parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:  # Graph returns e.g. 2026-09-30T01:37:15+0000
        return datetime.strptime(value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
    except ValueError:
        return None


class EngageService:
    def __init__(self, db, graph, llm, cfg: EngageConfig, now: Callable[[], datetime] = datetime.utcnow):
        self.cfg, self.graph, self.llm, self.now = cfg, graph, llm, now
        self.comments = db.get_collection("engage_comments")
        self.pubs = db.get_collection("publications")
        self.listings = db.get_collection("listings")
        self.profiles = db.get_collection("agent_public_profiles")

    # ---- context for a post ---------------------------------------------------------------------------------
    async def _publication(self, post_id: str) -> Optional[dict]:
        tail = post_id.split("_")[-1]
        for p in await self.pubs.find({"channel": "facebook_page"}).to_list(300):
            ext = str(p.get("external_id") or "")
            if ext and (ext == post_id or ext == tail or ext.endswith("_" + tail)):
                return p
        return None

    async def _context(self, post: dict) -> Dict:
        """(facts text, link, listing_id, agent_id) for a post. Listing posts use the listing's facts; other posts use the post's own text."""
        message = (post.get("message") or "")[:900]
        pub = await self._publication(post["id"])
        listing = await self.listings.find_one({"_id": pub["listing_id"]}) if pub else None
        if listing:
            profile = await self.profiles.find_one({"agent_id": listing.get("agent_id")}) or {}
            slug = profile.get("slug")
            base = f"{self.cfg.site_url}/agent/{slug}/listings/{listing['_id']}#enquire" if slug and self.cfg.site_url else self.cfg.landing_url
            f = Facts.from_docs(listing, profile, "")
            facts = "\n".join(x for x in (f.title_line("en"), f.price_text, f.area_text, f.possession_text("en"), f.floor_text("en"),
                                          f"RERA {f.rera}" if f.rera else None, "Amenities: " + ", ".join(f.amenities) if f.amenities else None, message) if x)
            return {"facts": facts, "link": with_source(base), "listing_id": listing["_id"], "agent_id": listing.get("agent_id")}
        return {"facts": message, "link": with_source(self.cfg.landing_url), "listing_id": None, "agent_id": self.cfg.owner_agent_id or None}

    # ---- limits ------------------------------------------------------------------------------------------------
    async def _hourly_full(self) -> bool:
        since = self.now() - timedelta(hours=1)
        return await self.comments.count_documents({"status": "replied", "replied_at": {"$gte": since}}) >= self.cfg.max_replies_per_hour

    async def _person_capped(self, from_id: str) -> bool:
        if not from_id:
            return False
        since = self.now() - timedelta(days=1)
        return await self.comments.count_documents({"from_id": from_id, "status": {"$in": ["replied", "dry_run"]}, "processed_at": {"$gte": since}}) >= self.cfg.max_replies_per_person_per_day

    # ---- one comment -------------------------------------------------------------------------------------------
    async def _handle(self, post: dict, c: dict, ctx: Dict) -> Optional[dict]:
        cid, sender = c["id"], c.get("from") or {}
        base = {"_id": cid, "post_id": post["id"], "listing_id": ctx["listing_id"], "agent_id": ctx["agent_id"], "from_id": sender.get("id"),
                "from_name": sender.get("name"), "permalink": c.get("permalink_url"), "text": (c.get("message") or "")[:1000], "created_time": c.get("created_time"),
                "processed_at": self.now(), "reply": None, "reply_id": None, "error": None}
        t = parse_time(c.get("created_time"))
        if sender.get("id") == self.cfg.page_id or c.get("parent") or (t and self.now() - t > MAX_COMMENT_AGE):
            return {**base, "intent": "other", "language": "en", "status": "ignored", "needs_human": False, "reason": "own comment, thread reply or old"}
        d: Decision = await decide(c.get("message") or "", sender.get("name"), ctx["facts"], ctx["link"], self.llm)
        doc = {**base, "intent": d.intent, "language": d.language, "reply": d.reply, "needs_human": d.needs_human, "reason": d.reason, "status": "ignored"}
        if d.needs_human and not d.reply:
            doc["status"] = "needs_human"
        if not d.reply:
            return doc
        if await self._person_capped(sender.get("id")):
            return {**doc, "status": "capped", "reason": "per-person daily limit"}
        if self.cfg.dry_run:
            return {**doc, "status": "dry_run"}
        try:
            doc["reply_id"] = await self.graph.reply(cid, d.reply)
            doc.update(status="replied", replied_at=self.now())
        except EngageGraphError as e:
            doc.update(status="failed", error=str(e))
        return doc

    async def run_once(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        try:
            posts = await self.graph.recent_posts_with_comments()
        except EngageGraphError as e:
            log.warning("engage: could not read comments: %s", e)
            return {"error": 1}
        for post in posts:
            items = (post.get("comments") or {}).get("data") or []
            new = [c for c in items if not await self.comments.find_one({"_id": c["id"]})]
            if not new:
                continue
            ctx = await self._context(post)
            for c in new:
                if not self.cfg.dry_run and await self._hourly_full():
                    log.info("engage: hourly reply cap reached; remaining comments wait for the next cycle")
                    return counts
                doc = await self._handle(post, c, ctx)
                if doc:
                    await self.comments.insert_one(doc)
                    counts[doc["status"]] = counts.get(doc["status"], 0) + 1
                    log.info("engage: comment %s intent=%s status=%s%s", c["id"], doc["intent"], doc["status"], f" error={doc['error']}" if doc["error"] else "")
        return counts

    async def recent(self, agent_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        flt = {"agent_id": agent_id} if agent_id else {}
        docs = await self.comments.find(flt).sort("processed_at", -1).limit(limit).to_list(limit)
        return docs
