"""Builds GET /report/weekly. Read-only over other modules' collections (events, contacts, listings, engage_comments, chat_sessions). Deterministic:
every number is a count from the last 7 days and every tip is a rule over the agent's own data, so nothing is invented."""
from app.core import brand
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from app.modules.listings.freshness import freshness_of
from app.modules.tracking import scoring
from app.modules.tracking.performance import VISIT_STAGES, is_qualified

DAYS = 7
LIVE = ("live", "under_offer")


class ReportService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow):
        self.now = now
        self.events = db.get_collection("events")
        self.contacts = db.get_collection("contacts")
        self.listings = db.get_collection("listings")
        self.comments = db.get_collection("engage_comments")
        self.chats = db.get_collection("chat_sessions")
        self.profiles = db.get_collection("agent_public_profiles")

    async def weekly(self, agent_id: str) -> Dict:
        now = self.now()
        since = now - timedelta(days=DAYS)
        listings = await self.listings.find({"agent_id": agent_id}).to_list(500)
        live = [l for l in listings if l.get("status") in LIVE]
        events = [e for e in await self.events.find({"agent_id": agent_id}).sort("ts", -1).limit(20000).to_list(20000) if e.get("ts") and e["ts"] >= since]
        contacts = await self.contacts.find({"agent_id": agent_id}).to_list(5000)
        new = [c for c in contacts if c.get("created_at") and c["created_at"] >= since]
        profile = await self.profiles.find_one({"agent_id": agent_id}) or {}
        comments = [c for c in await self.comments.find({"agent_id": agent_id}).to_list(1000) if c.get("processed_at") and c["processed_at"] >= since]
        chats = [c for c in await self.chats.find({"agent_slug": profile.get("slug")}).to_list(1000)
                 if profile.get("slug") and c.get("updated_at") and c["updated_at"] >= since and c.get("messages")]

        views: Dict[str, int] = {}
        visitors = set()
        for e in events:
            if e.get("anon_id"):
                visitors.add(e["anon_id"])
            if e.get("type") == "listing_view" and e.get("listing_id"):
                views[e["listing_id"]] = views.get(e["listing_id"], 0) + 1
        enquiries: Dict[str, int] = {}
        for c in new:
            if c.get("first_listing_id"):
                enquiries[c["first_listing_id"]] = enquiries.get(c["first_listing_id"], 0) + 1
        qualified = sum(1 for c in new if is_qualified(c, scoring.temperature(scoring.score(c.get("score_base", 0), c["last_activity_at"], now))))
        interest = [c for c in comments if c.get("intent") in ("interested", "question")]
        numbers = {
            "visitors": len(visitors), "listing_views": sum(views.values()), "new_enquiries": len(new), "qualified_enquiries": qualified,
            "site_visits": sum(1 for c in contacts if c.get("stage") in VISIT_STAGES and (c.get("last_activity_at") or now) >= since),
            "facebook_interest": len(interest), "chats": len(chats), "chat_leads": sum(1 for c in chats if c.get("lead_created")),
            "live_listings": len(live),
        }
        top = None
        if views:
            lid = max(views, key=views.get)
            doc = next((l for l in listings if l["_id"] == lid), None)
            if doc:
                top = {"listing_id": lid, "title": doc.get("title"), "views": views[lid], "enquiries": enquiries.get(lid, 0)}

        todo: List[Dict] = []
        no_photo = [l for l in live if not [m for m in (l.get("media") or []) if (m.get("kind") or "image") == "image"]]
        if no_photo:
            todo.append({"kind": "photos", "text": f"Add photos to {len(no_photo)} live listing{'s' if len(no_photo) > 1 else ''}: posts with real photos look far better.", "count": len(no_photo)})
        stale = [l for l in live if freshness_of(l, now)[0] in ("confirm", "hidden")]
        if stale:
            todo.append({"kind": "freshness", "text": f"Confirm availability on {len(stale)} listing{'s' if len(stale) > 1 else ''} so buyers keep seeing {'them' if len(stale) > 1 else 'it'}.", "count": len(stale)})
        waiting = [c for c in contacts if c.get("stage") == "new" and c.get("created_at") and c["created_at"] <= now - timedelta(hours=24)]
        if waiting:
            todo.append({"kind": "followup", "text": f"{len(waiting)} enquir{'ies have' if len(waiting) > 1 else 'y has'} not been contacted for over a day. Reply while they are still interested.", "count": len(waiting)})
        human = [c for c in comments if c.get("needs_human")] + [c for c in chats if c.get("needs_human") and not c.get("lead_created")]
        if human:
            todo.append({"kind": "answer", "text": f"{len(human)} question{'s' if len(human) > 1 else ''} from Facebook or the website chat need{'' if len(human) > 1 else 's'} your answer.", "count": len(human)})
        if not live:
            todo.append({"kind": "post", "text": "Post your first listing: it takes a minute and gives you a website page and ready-made posts.", "count": 0})
        elif not new and not interest and not chats:
            todo.append({"kind": "share", "text": "No enquiries yet this week. Share your listing links in your WhatsApp groups and Status to get the first ones.", "count": 0})

        return {"period_days": DAYS, "from": since, "to": now, "numbers": numbers, "top_listing": top, "todo": todo[:4],
                "share_text": self._share_text(numbers, top, profile)}

    @staticmethod
    def _share_text(n: Dict, top: Optional[Dict], profile: Dict) -> str:
        lines = [f"My week on {brand.NAME}:"]
        lines.append(f"• {n['listing_views']} listing views from {n['visitors']} visitors")
        lines.append(f"• {n['new_enquiries']} new enquir{'y' if n['new_enquiries'] == 1 else 'ies'}" + (f" ({n['qualified_enquiries']} with budget or timeline)" if n["new_enquiries"] else ""))
        if n["facebook_interest"] or n["chats"]:
            lines.append(f"• {n['facebook_interest']} people interested on Facebook, {n['chats']} website chats")
        if top and top["views"]:
            lines.append(f"• Most viewed: {top['title']} ({top['views']} views)")
        slug = profile.get("slug")
        if slug:
            lines.append(f"My listings: /agent/{slug}")
        return "\n".join(lines)
