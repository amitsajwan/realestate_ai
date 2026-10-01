"""Chat sessions (`chat_sessions`, _id = session id from the visitor's browser), rate limits, hand-off of a confirmed lead to the tracking module,
matching homes (the agent's own live listings, through tracking.matching), agent alerts (notifications) and the optional WhatsApp hand-over."""
import logging
import os
import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from app.core import brand
from app.modules.knowledge.grounding import Ref, facts_for
from app.modules.listings.freshness import is_hidden
from app.modules.marketing.facts import money
from app.modules.notifications.service import notify
from app.modules.tracking import matching
from app.modules.tracking import requirement as rq
from app.modules.tracking.schemas import InquiryIn
from app.modules.tracking.service import TrackingError

from . import engine

log = logging.getLogger(__name__)
SESSION_RX = re.compile(r"^[A-Za-z0-9_-]{12,64}$")
ID_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
AREA_RX = re.compile(r"^[A-Za-z][A-Za-z _-]{1,39}$")
MAX_TEXT = 500
MAX_PER_HOUR = 60
MAX_MESSAGES_KEPT = 40
PUBLIC = {"status": {"$in": list(matching.LIVE)}, "visibility": {"$in": ["public", "network"]}}
CARD_MIN_PCT = 60  # tracking.matching's 'recommend this to the buyer' level: a 40-59% 'maybe' is not shown as a fit
MAX_LISTINGS_SCANNED = 200


def platform_whatsapp_number() -> Optional[str]:
    """The platform's public WhatsApp number as wa.me digits (WHATSAPP_PUBLIC_NUMBER, else NEXT_PUBLIC_WHATSAPP_NUMBER), or None: then the chat
    never offers 'Continue on WhatsApp'."""
    raw = (os.environ.get("WHATSAPP_PUBLIC_NUMBER") or os.environ.get("NEXT_PUBLIC_WHATSAPP_NUMBER") or "").strip()
    d = re.sub(r"\D", "", raw)
    if re.fullmatch(r"[6-9]\d{9}", d):
        d = "91" + d
    return d if 11 <= len(d) <= 15 else None


def is_sample(doc: dict) -> bool:
    return (doc.get("title") or "").strip().lower().startswith("sample") or bool(doc.get("sample_key"))


def card(doc: dict, slug: str) -> dict:
    """A home card for the chat. Samples carry no price (they are illustrations); the title drops the 'Sample:' prefix (the card says Sample)."""
    sample = is_sample(doc)
    imgs = sorted([m for m in (doc.get("media") or []) if isinstance(m, dict) and m.get("kind", "image") == "image" and m.get("url")],
                  key=lambda m: m.get("order") or 0)
    title = re.sub(r"^\s*sample\s*[:\-]\s*", "", doc.get("title") or "", flags=re.I).strip() or "Home"
    if sample:  # 'Sample: 2 BHK apartment for sale in Kharadi' -> '2 BHK apartment in Kharadi' (a sample is never for sale)
        title = re.sub(r"\s+for\s+(sale|rent)\b", "", title, flags=re.I)
    rent = (doc.get("transaction") or "sale") == "rent"
    price = doc.get("price_inr")
    return {"id": str(doc["_id"]), "title": title[:90], "locality": doc.get("locality"), "bhk": doc.get("bhk"), "carpet_sqft": doc.get("carpet_sqft"),
            "price_text": None if sample or not isinstance(price, int) else money(price, rent), "sample": sample,
            "url": f"/agent/{slug}/listings/{doc['_id']}", "image_url": imgs[0]["url"] if imgs else None}


class ChatError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class ChatService:
    def __init__(self, db, tracking, llm=None, now: Callable[[], datetime] = datetime.utcnow):
        self.sessions = db.get_collection("chat_sessions")
        self.profiles = db.get_collection("agent_public_profiles")
        self.db, self.listings, self.calendar = db, db.get_collection("listings"), db.get_collection("content_calendar")
        self.tracking, self.llm, self.now = tracking, llm, now

    async def conversations(self, agent_id: str, limit: int = 30) -> list:
        """The agent's recent website chats: which need a person, which became leads. Never includes phone numbers (leads hold those)."""
        profile = await self.profiles.find_one({"agent_id": agent_id})
        if not profile:
            return []
        docs = await self.sessions.find({"agent_slug": profile["slug"]}).sort("updated_at", -1).limit(limit).to_list(limit)
        return [{"id": d["_id"][-8:], "updated_at": d.get("updated_at"), "needs_human": bool(d.get("needs_human")) and not d.get("lead_created"),
                 "lead_created": bool(d.get("lead_created")), "summary": engine.summary(d["data"]), "questions": d["data"].get("questions", [])[-3:], "missing": d["data"].get("missing", [])[-3:],
                 "name": d["data"].get("name"), "messages": len(d.get("messages", []))} for d in docs if d.get("messages")]

    async def _public_listing(self, lid) -> Optional[dict]:
        if not lid or not ID_RX.match(str(lid)):
            return None
        return await self.listings.find_one({"_id": str(lid), **PUBLIC})

    async def grounding_for(self, context: Optional[dict]):
        """What we know about the page the visitor is on: a public listing, a published post, or an area (in that order). None when unknown.
        The context comes from the browser, so every id is looked up and checked here; nothing in it is trusted."""
        ctx = context or {}
        lid, pid, loc = ctx.get("listing_id"), ctx.get("post_id"), ctx.get("locality")
        try:
            if await self._public_listing(lid):
                return await facts_for(Ref.listing(str(lid)), self.db)
            if pid and ID_RX.match(str(pid)):
                doc = await self.calendar.find_one({"_id": str(pid), "status": "published"})
                if doc:
                    return await facts_for(Ref.calendar(str(pid)), self.db)
            if loc and AREA_RX.match(str(loc)):
                return await facts_for(Ref.area(str(loc)), self.db)
        except Exception as e:  # knowledge is a help, never a reason to fail a chat message
            log.info("chat grounding failed: %s", e)
        return None

    async def page_for(self, context: Optional[dict], grounding) -> Optional[dict]:
        """The engine's view of the page (for the greeting and 'similar homes'): only checked, public data."""
        ctx = context or {}
        doc = await self._public_listing(ctx.get("listing_id"))
        if doc:
            return {"kind": "listing", "listing_id": doc["_id"], "agent_id": doc.get("agent_id"), "bhk": doc.get("bhk"), "locality": doc.get("locality"),
                    "carpet_sqft": doc.get("carpet_sqft"), "transaction": doc.get("transaction") or "sale", "sample": is_sample(doc),
                    "title": doc.get("title")}
        if grounding is not None and getattr(grounding, "kind", None) == "area" and grounding.locality:
            return {"kind": "area", "locality": grounding.locality}
        return None

    async def homes_agent(self, profile: dict, page: Optional[dict]) -> tuple:
        """-> (agent_id, slug) whose homes are shown: the site's agent; on a page about another agent's home (platform or demo pages), that agent."""
        if page and page.get("agent_id") and page["agent_id"] != profile.get("agent_id"):
            other = await self.profiles.find_one({"agent_id": page["agent_id"], "is_public": True})
            if other:
                return other["agent_id"], other["slug"]
        return profile.get("agent_id"), profile["slug"]

    def finder(self, agent_id: Optional[str], slug: str):
        async def find(req: dict, exclude: Optional[str]) -> List[dict]:
            if not agent_id:
                return []
            docs = await self.listings.find({"agent_id": agent_id, **PUBLIC}).to_list(MAX_LISTINGS_SCANNED)
            now = self.now()
            docs = [d for d in docs if d["_id"] != exclude and not is_hidden(d, now)]
            by_id = {d["_id"]: d for d in docs}
            tx = req.pop("transaction", "sale")
            top = matching.top_matches(req, docs, tx, limit=10)
            return [card(by_id[m["listing_id"]], slug) for m in top if m["match_pct"] >= CARD_MIN_PCT and m["listing_id"] in by_id][:3]
        return find

    async def whatsapp_url(self, data: dict, page: Optional[dict]) -> Optional[str]:
        """wa.me link to the platform number with a prefilled message naming the home (its interest code when one exists, which the WhatsApp
        module routes on) or the requirement. Never the buyer's phone number."""
        number = platform_whatsapp_number()
        if not number:
            return None
        if page and page.get("kind") == "listing":
            link = await self.db.get_collection("interest_links").find_one({"kind": "listing", "ref": page["listing_id"]})
            what = (page.get("title") or "this home")[:80]
            msg = f"Hi {brand.NAME}, I am interested in {what}" + (f" (ref {link['code']})" if link and link.get("code") else f" ({page['listing_id']})") + "."
        else:
            want = ", ".join(x for x in (rq.bhk_text(data.get("bhk")), data.get("locality") if data.get("locality") != "Other" else None,
                                        engine._budget_text(data)) if x)
            msg = f"Hi {brand.NAME}, I am looking for a home" + (f": {want}" if want else "") + "."
        return f"https://wa.me/{number}?text={urllib.parse.quote(msg, safe='')}"

    async def _contact_id(self, agent_id: str, phone: str) -> Optional[str]:
        doc = await self.db.get_collection("contacts").find_one({"agent_id": agent_id, "phone": phone})
        return doc["_id"] if doc else None

    async def message(self, session_id: str, agent_slug: str, text: str, source: Optional[str] = None, context: Optional[dict] = None) -> dict:
        if not SESSION_RX.match(session_id or ""):
            raise ChatError("Invalid session")
        text = (text or "").strip()
        if not text or len(text) > MAX_TEXT:
            raise ChatError("Please send a short message (up to 500 characters)")
        profile = await self.profiles.find_one({"slug": agent_slug, "is_public": True})
        if not profile:
            raise ChatError("Unknown site", 404)
        now = self.now()
        s = await self.sessions.find_one({"_id": session_id}) or {
            "_id": session_id, "agent_slug": agent_slug, "created_at": now, "data": engine.new_data(localise=True), "messages": [], "hits": []}
        s["hits"] = [h for h in s.get("hits", []) if h > now - timedelta(hours=1)]
        if len(s["hits"]) >= MAX_PER_HOUR:
            return {"reply": "You have sent a lot of messages in a short time. Please try again a little later.", "quick_replies": [], "lead_created": False,
                    "cards": [], "follow_up": None, "whatsapp_url": None}
        s["hits"].append(now)

        grounding = await self.grounding_for(context)
        page = await self.page_for(context, grounding)
        data = s["data"]
        data["page"] = page
        homes_agent, homes_slug = await self.homes_agent(profile, page)
        wa_number = platform_whatsapp_number()
        had_name = bool(data.get("name"))
        t = await engine.turn(data, text, self.llm, grounding, finder=self.finder(homes_agent, homes_slug), whatsapp=bool(wa_number))
        agent_id = profile.get("agent_id")
        ref = {"conversation_id": session_id[-8:], "channel": "chat"}
        lead_created = False
        if t.lead:
            try:
                await self.tracking.capture_inquiry(InquiryIn(
                    agent_slug=agent_slug, anon_id=("chat-" + session_id)[:64], source=(source or "chat")[:40], consent=True,
                    listing_id=(page or {}).get("listing_id"), **t.lead))
                lead_created = True
            except TrackingError as e:  # e.g. too many enquiries from this number: keep chatting, tell the visitor kindly
                log.info("chat lead not stored: %s", e)
                t.reply = "Thanks! We already have your details, and our team will be in touch soon."
            if lead_created:
                who = data.get("name") or "A website visitor"
                ref = {**ref, "lead_id": await self._contact_id(agent_id, data["phone"])}
                await self._notify(agent_id, "new_chat_lead", f"{who} shared their number in the website chat. {engine.summary(data)}", ref, now)
        elif data.get("name") and not had_name and data.get("lead_done") and data.get("phone"):
            # a name given after the number: put it on the lead if it still has the placeholder
            await self.db.get_collection("contacts").update_one({"agent_id": agent_id, "phone": data["phone"], "name": "Website visitor"},
                                                                {"$set": {"name": data["name"]}})
        if t.notify_needs_you:
            who = data.get("name") or "A website visitor"
            asked = (data.get("questions") or [text])[-1]
            await self._notify(agent_id, "chat_needs_you", f"{who} asked something in the website chat we could not answer: \"{asked[:120]}\"", ref, now)

        s["messages"] = (s.get("messages", []) + [
            {"role": "user", "text": text, "ts": now}, {"role": "bot", "text": " ".join(x for x in (t.reply, t.follow_up) if x), "ts": now, **({"cards": [c["id"] for c in t.cards]} if t.cards else {})}])[-MAX_MESSAGES_KEPT:]
        s.update(updated_at=now, needs_human=bool(data.get("needs_human")), lead_created=bool(s.get("lead_created") or lead_created))
        if await self.sessions.find_one({"_id": session_id}):
            await self.sessions.update_one({"_id": session_id}, {"$set": {k: v for k, v in s.items() if k != "_id"}})
        else:
            await self.sessions.insert_one(s)
        wa = await self.whatsapp_url(data, page) if wa_number and engine.WHATSAPP_LABEL in t.quick else None
        quick = [q for q in t.quick if q != engine.WHATSAPP_LABEL or wa]
        return {"reply": t.reply, "quick_replies": quick, "lead_created": lead_created, "cards": t.cards, "follow_up": t.follow_up or None,
                "whatsapp_url": wa}

    async def _notify(self, agent_id: Optional[str], kind: str, summary: str, ref: dict, now: datetime) -> None:
        if not agent_id:
            return
        try:
            await notify(self.db, agent_id, kind, engine.PHONE_RX.sub("[number]", summary), ref, now)
        except Exception as e:  # an alert must never break the chat
            log.warning("chat notification not stored: %s", type(e).__name__)
