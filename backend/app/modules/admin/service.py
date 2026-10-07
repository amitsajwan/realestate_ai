"""Admin home aggregation: one overview for the owner, and the website invite-request queue.

Counts are read straight from the collections the other modules write (contacts, interest_events, engage_comments, content_calendar,
publications, newsroom_items, invite_requests). Only simple equality / range filters are sent to Mongo; grouping happens here
(pilot volumes are small). Phone numbers never leave this module unmasked.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from bson import ObjectId

from app.modules.concierge.service import mask_phone

from app.platform import controls

IST = timezone(timedelta(hours=5, minutes=30))
CAP = 5000  # documents read per collection for a 7-day window


class AdminError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _iso(dt) -> Optional[str]:
    if isinstance(dt, datetime):
        return dt.isoformat() + ("Z" if dt.tzinfo is None else "")
    return dt


def _naive(dt) -> Optional[datetime]:
    if not isinstance(dt, datetime):
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def day_start(now: datetime) -> datetime:
    """Midnight today in India, as naive UTC (how the app stores times)."""
    local = now.replace(tzinfo=timezone.utc).astimezone(IST)
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)


def _oid(id: str):
    return ObjectId(id) if ObjectId.is_valid(id) else id


class AdminService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow):
        self.db, self.now = db, now

    def c(self, name: str):
        return self.db.get_collection(name)

    async def _since(self, coll: str, field: str, since: datetime, **eq) -> List[dict]:
        return await self.c(coll).find({**eq, field: {"$gte": since}}).to_list(CAP)

    # ---- counts ------------------------------------------------------------------------------------------------
    async def counts(self) -> Dict:
        now = self.now()
        windows = {"today": day_start(now), "week": now - timedelta(days=7)}
        week = windows["week"]
        contacts = await self._since("contacts", "created_at", week)
        taps = await self._since("interest_events", "ts", week, type="interest")
        answered = await self._since("engage_comments", "replied_at", week, status="replied")
        cal = await self._since("content_calendar", "published_at", week, status="published")
        pubs = await self._since("publications", "updated_at", week, status="published")
        news = await self._since("newsroom_items", "published_at", week, status="published")

        def window(since: datetime) -> Dict:
            def within(docs, field):
                return [d for d in docs if (_naive(d.get(field)) or datetime.min) >= since]
            leads = within(contacts, "created_at")
            posts = Counter(d.get("channel") for d in within(cal, "published_at") + within(pubs, "updated_at"))
            return {
                "leads": len(leads),
                "leads_by_source": dict(Counter((d.get("source") or "website") for d in leads)),
                "chat_leads": sum(1 for d in leads if any(str(a).startswith("chat-") for a in d.get("anon_ids") or [])),
                "whatsapp_leads": sum(1 for d in leads if d.get("source") == "whatsapp"),
                "interest_taps": len(within(taps, "ts")),
                "comments_answered": len(within(answered, "replied_at")),
                "posts_published": {"facebook_page": posts.get("facebook_page", 0), "instagram": posts.get("instagram", 0)},
                "news_published": len(within(news, "published_at")),
            }

        return {k: window(v) for k, v in windows.items()}

    async def waiting(self) -> Dict:
        return {
            "posts": await self.c("content_calendar").count_documents({"status": "planned"}),
            "news": await self.c("newsroom_items").count_documents({"status": "pending_review"}),
            "invite_requests": await self.c("invite_requests").count_documents({"status": "new"}),
        }

    # ---- health inputs -----------------------------------------------------------------------------------------
    async def meta_status(self) -> Dict[str, Optional[dict]]:
        out = {}
        for ch in ("facebook", "instagram"):
            d = await self.c("engage_status").find_one({"_id": ch})
            out[ch] = {"ok": bool(d.get("ok")), "reconnect": bool(d.get("reconnect")), "code": d.get("code"),
                       "checked_at": d.get("checked_at")} if d else None
        return out

    async def run_status(self, coll: str) -> dict:
        d = await self.c(coll).find_one({"_id": "runner"}) or {}
        return {"last_run_at": d.get("last_run_at"), "last_error": d.get("last_error")}

    # ---- invite requests ---------------------------------------------------------------------------------------
    @staticmethod
    def _request_view(r: dict) -> dict:
        return {"id": str(r["_id"]), "name": r.get("name") or "", "mobile": mask_phone(r.get("phone")), "city": r.get("city") or "",
                "message": r.get("message") or "", "created_at": _iso(r.get("created_at")), "status": r.get("status") or "new"}

    async def invite_requests(self, limit: int = 50) -> List[dict]:
        rows = await self.c("invite_requests").find({"status": "new"}).sort("created_at", 1).limit(limit).to_list(limit)
        return [self._request_view(r) for r in rows]

    async def _new_request(self, id: str) -> dict:
        doc = await self.c("invite_requests").find_one({"_id": _oid(id)})
        if not doc:
            raise AdminError("Invite request not found", 404)
        if doc.get("status") != "new":
            raise AdminError(f"This request is already {doc.get('status')}", 409)
        return doc

    async def invite(self, id: str, owner_id: str, concierge) -> dict:
        """Create the agent (login, site, code) through the concierge, then mark the request invited."""
        doc = await self._new_request(id)
        label = f"{doc.get('name') or ''}, website request".strip(", ")[:80]
        created = await concierge.create_agent(owner_id, (doc.get("name") or "Agent").strip()[:100], doc["phone"], label)
        now = self.now()
        await self.c("invite_requests").update_one({"_id": doc["_id"]}, {"$set": {
            "status": "invited", "updated_at": now, "invited_at": now, "invited_by": owner_id, "agent_id": created["agent"]["id"]}})
        return {**created, "request": {**self._request_view(doc), "status": "invited"}}

    async def dismiss(self, id: str, owner_id: str) -> dict:
        doc = await self._new_request(id)
        now = self.now()
        await self.c("invite_requests").update_one({"_id": doc["_id"]}, {"$set": {
            "status": "dismissed", "updated_at": now, "dismissed_at": now, "dismissed_by": owner_id}})
        return {**self._request_view(doc), "status": "dismissed"}

    async def controls(self) -> dict:
        return await controls.get_controls(self.db)
