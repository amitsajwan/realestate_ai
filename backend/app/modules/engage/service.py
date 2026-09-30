"""Process new comments on the Page and on the linked Instagram account. State lives in `engage_comments` (_id = Facebook comment id; Instagram
ids are stored as "instagram:<id>"), so every comment is handled once.

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
UNKNOWN_PER_POST_PER_DAY = 6  # commenters whose identity Meta does not show us


def with_source(url: str, source: str = "facebook_comment") -> str:
    """Add ?src=<source> before any #fragment."""
    if not url:
        return url
    base, _, frag = url.partition("#")
    base += ("&" if "?" in base else "?") + "src=" + quote(source)
    return base + ("#" + frag if frag else "")


def stored_id(channel: str, comment_id: str) -> str:
    """Facebook ids are stored as they are (existing rows); Instagram ids get a prefix so the two platforms can never collide."""
    return comment_id if channel == "facebook" else f"{channel}:{comment_id}"


def parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:  # Graph returns e.g. 2026-09-30T01:37:15+0000
        return datetime.strptime(value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
    except ValueError:
        return None


class EngageService:
    def __init__(self, db, graph, llm, cfg: EngageConfig, now: Callable[[], datetime] = datetime.utcnow, ig_graph=None):
        self.cfg, self.graph, self.llm, self.now, self.ig_graph = cfg, graph, llm, now, ig_graph
        self.comments = db.get_collection("engage_comments")
        self.pubs = db.get_collection("publications")
        self.listings = db.get_collection("listings")
        self.profiles = db.get_collection("agent_public_profiles")
        self.status = db.get_collection("engage_status")

    # ---- context for a post ---------------------------------------------------------------------------------
    def channels(self) -> List[tuple]:
        out = [("facebook", self.graph)]
        if self.ig_graph is not None and self.cfg.instagram_enabled:
            out.append(("instagram", self.ig_graph))
        return out

    async def _publication(self, post_id: str, channel: str = "facebook") -> Optional[dict]:
        tail = post_id.split("_")[-1]
        for p in await self.pubs.find({"channel": "instagram" if channel == "instagram" else "facebook_page"}).to_list(300):
            ext = str(p.get("external_id") or "")
            if ext and (ext == post_id or ext == tail or ext.endswith("_" + tail)):
                return p
        return None

    async def _context(self, post: dict, channel: str = "facebook") -> Dict:
        """(facts text, link, listing_id, agent_id) for a post. Listing posts use the listing's facts; other posts use the post's own text."""
        message = (post.get("message") or "")[:900]
        source = f"{channel}_comment"
        pub = await self._publication(post["id"], channel)
        listing = await self.listings.find_one({"_id": pub["listing_id"]}) if pub else None
        if listing:
            profile = await self.profiles.find_one({"agent_id": listing.get("agent_id")}) or {}
            slug = profile.get("slug")
            base = f"{self.cfg.site_url}/agent/{slug}/listings/{listing['_id']}#enquire" if slug and self.cfg.site_url else self.cfg.landing_url
            f = Facts.from_docs(listing, profile, "")
            facts = "\n".join(x for x in (f.title_line("en"), f.price_text, f.area_text, f.possession_text("en"), f.floor_text("en"),
                                          f"RERA {f.rera}" if f.rera else None, "Amenities: " + ", ".join(f.amenities) if f.amenities else None, message) if x)
            return {"facts": facts, "link": with_source(base, source), "listing_id": listing["_id"], "agent_id": listing.get("agent_id")}
        return {"facts": message, "link": with_source(self.cfg.landing_url, source), "listing_id": None, "agent_id": self.cfg.owner_agent_id or None}

    # ---- limits ------------------------------------------------------------------------------------------------
    async def _hourly_full(self) -> bool:
        since = self.now() - timedelta(hours=1)
        return await self.comments.count_documents({"status": "replied", "replied_at": {"$gte": since}}) >= self.cfg.max_replies_per_hour

    async def _person_capped(self, key: str, limit: int) -> bool:
        """Replies to one person in the last day. Meta hides some commenters' identity, so those share a per-post key with a higher limit."""
        since = self.now() - timedelta(days=1)
        return await self.comments.count_documents({"cap_key": key, "status": {"$in": ["replied", "dry_run"]}, "processed_at": {"$gte": since}}) >= limit

    # ---- one comment -------------------------------------------------------------------------------------------
    async def _handle(self, post: dict, c: dict, ctx: Dict, channel: str = "facebook", handle: str = "", graph=None) -> Optional[dict]:
        cid, sender = c["id"], c.get("from") or {}
        graph = graph or self.graph
        base = {"_id": stored_id(channel, cid), "channel": channel, "comment_id": cid, "post_id": post["id"], "listing_id": ctx["listing_id"], "agent_id": ctx["agent_id"], "from_id": sender.get("id"), "cap_key": sender.get("id") or f"unknown:{post['id']}",
                "from_name": sender.get("name"), "permalink": c.get("permalink_url") or post.get("permalink"), "text": (c.get("message") or "")[:1000], "created_time": c.get("created_time"),
                "processed_at": self.now(), "reply": None, "reply_id": None, "error": None}
        t = parse_time(c.get("created_time"))
        own = c.get("own") or (channel == "facebook" and sender.get("id") == self.cfg.page_id)
        if own or c.get("replied") or c.get("parent") or (t and self.now() - t > MAX_COMMENT_AGE):
            return {**base, "intent": "other", "language": "en", "status": "ignored", "needs_human": False, "reason": "own comment, already answered, thread reply or old"}
        extra = {"channel": channel, "handle": handle} if channel != "facebook" else {}
        d: Decision = await decide(c.get("message") or "", sender.get("name"), ctx["facts"], ctx["link"], self.llm, **extra)
        doc = {**base, "intent": d.intent, "language": d.language, "reply": d.reply, "needs_human": d.needs_human, "reason": d.reason, "status": "ignored"}
        if d.needs_human and not d.reply:
            doc["status"] = "needs_human"
        if not d.reply:
            return doc
        limit = self.cfg.max_replies_per_person_per_day if sender.get("id") else UNKNOWN_PER_POST_PER_DAY
        if await self._person_capped(base["cap_key"], limit):
            return {**doc, "status": "capped", "reason": "per-person daily limit"}
        if self.cfg.dry_run:
            return {**doc, "status": "dry_run"}
        try:
            doc["reply_id"] = await graph.reply(cid, d.reply)
            doc.update(status="replied", replied_at=self.now())
        except EngageGraphError as e:
            doc.update(status="failed", error=str(e))
        return doc

    async def run_once(self, only_ids: Optional[set] = None) -> Dict[str, int]:
        """One cycle over every enabled channel. `only_ids` (used by verification scripts) restricts it to exactly those comment ids (raw
        platform ids, or stored ids); nothing else is read or answered."""
        counts: Dict[str, int] = {}
        for channel, graph in self.channels():
            if not await self._run_channel(channel, graph, only_ids, counts):
                break
        return counts

    async def _run_channel(self, channel: str, graph, only_ids: Optional[set], counts: Dict[str, int]) -> bool:
        """Process one channel. Returns False when the hourly cap is reached (no channel should reply any more this cycle)."""
        try:
            posts = await graph.recent_posts_with_comments()
            handle = await graph.own_username() if channel == "instagram" else ""
        except EngageGraphError as e:
            log.warning("engage: could not read %s comments: %s", channel, e)
            await self._set_status(channel, False, e)
            counts["error"] = counts.get("error", 0) + 1
            return True
        await self._set_status(channel, True)
        for post in posts:
            items = (post.get("comments") or {}).get("data") or []
            new = [c for c in items if (only_ids is None or c["id"] in only_ids or stored_id(channel, c["id"]) in only_ids)
                   and not await self.comments.find_one({"_id": stored_id(channel, c["id"])})]
            if not new:
                continue
            ctx = await self._context(post, channel)
            for c in new:
                if not self.cfg.dry_run and await self._hourly_full():
                    log.info("engage: hourly reply cap reached; remaining comments wait for the next cycle")
                    return False
                doc = await self._handle(post, c, ctx, channel, handle, graph)
                if doc:
                    await self.comments.insert_one(doc)
                    counts[doc["status"]] = counts.get(doc["status"], 0) + 1
                    log.info("engage: %s comment %s intent=%s status=%s%s", channel, c["id"], doc["intent"], doc["status"], f" error={doc['error']}" if doc["error"] else "")
        return True

    async def _set_status(self, channel: str, ok: bool, err: Optional[EngageGraphError] = None) -> None:
        """Remember whether Meta accepts our token, per channel, so the app can tell the owner when it stops (error 190 = reconnect needed)."""
        doc = {"ok": ok, "checked_at": self.now(), "code": getattr(err, "code", 0), "reconnect": bool(err and err.code == 190)}
        if not ok:
            doc["message"] = str(err)[:200]
        if await self.status.find_one({"_id": channel}):
            await self.status.update_one({"_id": channel}, {"$set": doc})
        else:
            await self.status.insert_one({"_id": channel, **doc})

    async def recent(self, agent_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        flt = {"agent_id": agent_id} if agent_id else {}
        docs = await self.comments.find(flt).sort("processed_at", -1).limit(limit).to_list(limit)
        return docs
