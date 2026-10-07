"""Process new comments on the Page and on the linked Instagram account. State lives in `engage_comments` (_id = Facebook comment id; Instagram
ids are stored as "instagram:<id>"), so every comment is handled once.

Guard rails: the whole thing is off unless ENGAGE_ENABLED; in dry-run mode it only records what it WOULD say; replies are capped per hour and
per person per day; our own comments, threaded replies, spam and abuse are never answered; questions the post cannot answer go to a person.
"""
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote

from app.modules.knowledge.grounding import Ref, facts_for

from app.platform.text import normalize_indian_mobile

from .brain import Decision, decide, dm_text
from .config import EngageConfig
from .graph import EngageGraphError

log = logging.getLogger(__name__)

# Passed in at startup (app/wiring.py): listing_facts(listing, profile, share_url) -> the listing's display facts
# (title_line, price_text, area_text, ...), marketing's Facts.from_docs.
_listing_facts: Dict[str, Any] = {"from_docs": None}


# who a calendar post speaks to ('agents' for our recruitment posts, else 'buyers'); content's rule, passed in by app/wiring.py
# (calendar.reach.audience) because conversations do not import content
_audience_of: Dict[str, Callable[[dict], str]] = {"fn": lambda doc: "buyers"}


def _audience(doc: dict) -> str:
    return _audience_of["fn"](doc)


def configure(listing_facts: Callable[[dict, dict, str], Any], audience: Optional[Callable[[dict], str]] = None,
              reel_source: Optional[Callable[[str, str], str]] = None) -> None:
    """`reel_source(code, channel)`: the ?src= tag that traces a sign-up back to an agent reel (reels.agent_reels.source_tag)."""
    _listing_facts["from_docs"] = listing_facts
    if audience is not None:
        _audience_of["fn"] = audience
    if reel_source is not None:
        _audience_of["reel_source"] = reel_source
LEAD_INTENTS = ("interested", "question")
MAX_COMMENT_AGE = timedelta(days=7)
UNKNOWN_PER_POST_PER_DAY = 6  # commenters whose identity Meta does not show us
DM_PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?|0)?[6-9](?:[\s-]?\d){9}(?!\d)")  # as people type it: "98765 43210", "+91-98765-43210"


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
    def __init__(self, db, graph, llm, cfg: EngageConfig, now: Callable[[], datetime] = datetime.utcnow, ig_graph=None, interest_url: Optional[Callable] = None):
        """`interest_url(ctx, channel)` (sync or async), when given, returns the tap-to-show-interest URL for the post's listing or post; without
        it the listing page (or the landing page) is used, as before."""
        self.cfg, self.graph, self.llm, self.now, self.ig_graph = cfg, graph, llm, now, ig_graph
        self.db, self.interest_url = db, interest_url
        self.calendar = db.get_collection("content_calendar")
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

    async def _calendar_item(self, post_id: str) -> Optional[dict]:
        """The calendar row (an evergreen post or a showcase sample home) that was published as this Page / Instagram post."""
        tail = post_id.split("_")[-1]
        for ext in dict.fromkeys([post_id, tail]):
            doc = await self.calendar.find_one({"external_id": ext})
            if doc:
                return doc
        return None

    async def _context(self, post: dict, channel: str = "facebook") -> Dict:
        """{facts, link, listing_id, agent_id, grounding} for a post. Listing posts use the listing's facts; calendar posts use their verified
        text (or the sample home); other posts use the post's own text. `grounding` is what a question about the post may be answered from."""
        ctx = await self._base_context(post, channel)
        if self.interest_url is not None and ctx.get("audience") != "agents":  # agents get the free-trial link, not a buyer interest link
            url = self.interest_url(ctx, channel)
            url = await url if hasattr(url, "__await__") else url
            if url:
                ctx["link"] = url
        return ctx

    async def _base_context(self, post: dict, channel: str = "facebook") -> Dict:
        message = (post.get("message") or "")[:900]
        source = f"{channel}_comment"
        pub = await self._publication(post["id"], channel)
        listing = await self.listings.find_one({"_id": pub["listing_id"]}) if pub else None
        item = None if listing else await self._calendar_item(post["id"])
        grounding = await facts_for(Ref.listing(listing["_id"]), self.db) if listing else (
            await facts_for(Ref.calendar(item["_id"]), self.db) if item else None) or await facts_for(Ref.text(message), self.db)
        if listing:
            profile = await self.profiles.find_one({"agent_id": listing.get("agent_id")}) or {}
            slug = profile.get("slug")
            base = f"{self.cfg.site_url}/agent/{slug}/listings/{listing['_id']}#enquire" if slug and self.cfg.site_url else self.cfg.landing_url
            f = _listing_facts["from_docs"](listing, profile, "")
            facts = "\n".join(x for x in (f.title_line("en"), f.price_text, f.area_text, f.possession_text("en"), f.floor_text("en"),
                                          f"RERA {f.rera}" if f.rera else None, "Amenities: " + ", ".join(f.amenities) if f.amenities else None, message) if x)
            return {"facts": facts, "link": with_source(base, source), "listing_id": listing["_id"], "agent_id": listing.get("agent_id"), "grounding": grounding}
        landing = self.cfg.landing_url
        if item:  # a calendar post made from an agent's builder project answers from the project record
            from app.modules.knowledge.grounding import calendar_project_grounding
            grounding = await calendar_project_grounding(item, self.db, self.cfg.site_url) or grounding
        if grounding is not None and grounding.links.get("page"):  # a builder project post: its own facts and its own page
            message = "\n".join(grounding.facts)[:1400]
            landing = grounding.links["page"] + "#enquire"
        agents = bool(item) and _audience(item) == "agents"
        if agents and self.cfg.site_url:  # our recruitment posts: agents asking "how do I use this" go to the free-trial page
            landing = f"{self.cfg.site_url}/trial"
            code = (item.get("creative") or {}).get("reel_code")
            reel_source = _audience_of.get("reel_source")
            if code and reel_source:  # an agent reel: the sign-up is traced back to this reel (scripts/agent_reels.py report)
                source = reel_source(code, channel)
        return {"facts": message, "link": with_source(landing, source), "listing_id": None, "agent_id": self.cfg.owner_agent_id or None,
                "grounding": grounding, "calendar_id": item["_id"] if item else None, "audience": "agents" if agents else "buyers"}

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
        d: Decision = await decide(c.get("message") or "", sender.get("name"), ctx["facts"], ctx["link"], self.llm, grounding=ctx.get("grounding"),
                                   audience=ctx.get("audience") or "buyers", **extra)
        doc = {**base, "audience": ctx.get("audience") or "buyers", "calendar_id": ctx.get("calendar_id"), "intent": d.intent, "language": d.language, "reply": d.reply, "needs_human": d.needs_human, "reason": d.reason, "status": "ignored",
               "answer_basis": d.basis, "missing": d.missing, "gaps": d.gaps}
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
        if only_ids is None:
            try:
                n = await self.collect_dm_replies()
                if n:
                    counts["dm_phone"] = n
            except Exception:  # reading the inbox must never stop replies
                log.exception("engage: could not read private replies")
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
                    await self._private_reply(doc, post, ctx, graph)
                    await self.comments.insert_one(doc)
                    counts[doc["status"]] = counts.get(doc["status"], 0) + 1
                    if doc["intent"] in LEAD_INTENTS and doc.get("audience") != "agents" \
                            and doc["status"] in ("replied", "needs_human", "dry_run", "capped"):  # an agent asking about the free trial is not a buyer lead
                        try:
                            await self._record_lead(doc, post)
                        except Exception:  # a lead problem must never stop replies
                            log.exception("engage: could not record a lead for comment %s", c["id"])
                    log.info("engage: %s comment %s intent=%s status=%s%s", channel, c["id"], doc["intent"], doc["status"], f" error={doc['error']}" if doc["error"] else "")
        return True

    async def _private_reply(self, doc: dict, post: dict, ctx: Dict, graph) -> None:
        """Interested or asking commenters also get one private message (Messenger / Instagram DM) asking for their WhatsApp number,
        budget and timing: the public reply is seen by everyone, the DM is what turns a commenter into someone an agent can call.
        One per person a week; a failure (e.g. the messaging permission is missing) is recorded and never stops the public reply."""
        if not self.cfg.private_reply or doc["intent"] not in LEAD_INTENTS or not doc.get("from_id") \
                or doc["status"] not in ("replied", "needs_human", "dry_run"):
            return
        if await self.comments.find_one({"channel": doc["channel"], "from_id": doc["from_id"], "dm_status": {"$in": ["sent", "dry_run"]},
                                         "processed_at": {"$gte": self.now() - MAX_COMMENT_AGE}}):
            doc["dm_status"] = "skipped"
            return
        topic = ((post.get("message") or "").splitlines() or [""])[0].strip()
        topic = topic if len(topic) <= 60 else topic[:60].rsplit(" ", 1)[0]
        doc["dm"] = dm_text(doc.get("language") or "en", doc.get("from_name"), ctx["link"], topic, ctx.get("audience") or "buyers")
        if self.cfg.dry_run:
            doc["dm_status"] = "dry_run"
            return
        try:
            doc["dm_recipient"] = await graph.private_reply(doc["comment_id"], doc["dm"])
            doc.update(dm_status="sent", dm_at=self.now())
        except EngageGraphError as e:
            doc.update(dm_status="failed", dm_error=str(e))
            log.warning("engage: private reply to %s comment %s failed: %s", doc["channel"], doc["comment_id"], e)

    async def collect_dm_replies(self) -> int:
        """Answers to our private messages: when a commenter-lead without a phone writes back a mobile number, it goes onto the lead
        (with everything they wrote, e.g. budget and timing) so the agent can call or WhatsApp them. Returns the number of leads updated."""
        if not self.cfg.private_reply or self.cfg.dry_run:
            return 0
        contacts = self.db.get_collection("contacts")
        waiting = [c for c in await contacts.find({"phone": ""}).to_list(500) if (c.get("dm") or {}).get("id")]
        updated = 0
        for channel, graph in self.channels():
            mine = {c["dm"]["id"]: c for c in waiting if c["dm"].get("channel") == channel}
            if not mine:
                continue
            try:
                convs = await graph.inbox()
            except EngageGraphError as e:
                log.warning("engage: could not read the %s inbox: %s", channel, e)
                continue
            for conv in convs:
                said: Dict[str, List[str]] = {}
                for m in reversed((conv.get("messages") or {}).get("data") or []):  # oldest first
                    who = str((m.get("from") or {}).get("id") or "")
                    if who in mine and (m.get("message") or "").strip():
                        said.setdefault(who, []).append(m["message"].strip())
                for who, lines in said.items():
                    text = "\n".join(lines)[:1000]
                    found = DM_PHONE.search(text)
                    if not found:
                        continue
                    try:
                        phone = normalize_indian_mobile(found.group(0))
                    except ValueError:
                        continue
                    now, lead = self.now(), mine.pop(who)
                    message = f"{channel.title()} message: “{text}”"
                    await contacts.update_one({"_id": lead["_id"]}, {"$set": {
                        "phone": phone, "last_message": message, "message": f"{lead.get('message', '')}\n\n{message}".strip(),
                        "last_activity_at": now, "score_base": max(int(lead.get("score_base") or 0), 25),
                        "consent": {"given_at": now, "purpose": "enquiry follow-up", "how": f"shared their number in a {channel} message"}}})
                    updated += 1
        return updated

    async def _record_lead(self, doc: dict, post: dict) -> None:
        """An interested or asking commenter becomes a lead in the agent's inbox (no phone yet: the agent can reply or DM on the platform)."""
        agent = doc.get("agent_id") or self.cfg.owner_agent_id
        who = (doc.get("from_name") or "").strip()
        if not agent or not who:
            return
        contacts = self.db.get_collection("contacts")
        key = f"{doc['channel']}:{doc.get('from_id') or who}"
        topic = ((post.get("message") or post.get("caption") or "").splitlines() or [""])[0][:120]
        message = f"{doc['channel'].title()} comment: “{doc.get('text', '')[:300]}”" + (f"\nOn the post: {topic}" if topic else "")
        now = self.now()
        dm = {"channel": doc["channel"], "id": doc["dm_recipient"]} if doc.get("dm_recipient") else None
        existing = await contacts.find_one({"agent_id": agent, "anon_ids": key})
        if existing:
            await contacts.update_one({"_id": existing["_id"]}, {"$set": {"last_activity_at": now, "last_message": message,
                                                                         **({"dm": dm} if dm else {})}})
            return
        await contacts.insert_one({
            "_id": uuid.uuid4().hex, "agent_id": agent,
            "name": f"@{who}" if doc["channel"] == "instagram" else who,
            "phone": "", "message": message, "anon_ids": [key], "stage": "new", "source": f"{doc['channel']}_comment", "utm": {},
            "first_listing_id": doc.get("listing_id"), "consent": None,
            "score_base": 10 if doc["intent"] == "interested" else 6, "created_at": now, "last_activity_at": now, "last_message": message,
            "notes": [], "requirement": None, "social": {"channel": doc["channel"], "handle": who, "comment_link": doc.get("permalink")},
            "dm": dm,  # who we privately messaged; their answer (a phone number) is filled in by collect_dm_replies
        })

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
