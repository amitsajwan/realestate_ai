"""Interest links: one short public URL per (kind, ref, channel) that tells the agent 'someone is interested'.

Depends only on tracking's public service (TrackingService / InquiryIn). Every public input is validated here; no phone
number or name ever appears in a URL.

Other streams call `interest_url(db, kind=..., ref=..., agent_id=..., channel=...)` to get the URL for a caption.
"""
import hashlib
import logging
import os
import uuid
from datetime import datetime
from typing import Callable, Optional

from app.modules.tracking import limits
from app.modules.tracking.schemas import InquiryIn
from app.modules.tracking.service import TrackingError, TrackingService

from .store import Store

logger = logging.getLogger(__name__)

KINDS = ("listing", "post", "page")
CHANNELS = ("facebook", "instagram", "website", "whatsapp")
MAX_INTEREST_PER_CODE_PER_HOUR = 3   # per visitor IP and code
MAX_CLICKS_PER_HOUR = 60             # per visitor IP, all codes
CONSENT_WORDING = "I agree to be contacted about this by the agent."


class InterestError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def site_url() -> str:
    return (os.environ.get("PUBLIC_SITE_URL") or "http://localhost:3000").rstrip("/")


def _anon(ip: Optional[str], code: str, anon_id: Optional[str]) -> str:
    """The browser's own random id when there is one; else a stable hash (the no-JS form post has none)."""
    if anon_id and len(anon_id.strip()) >= 8:
        return anon_id.strip()[:64]
    return "ip-" + hashlib.sha256(f"{ip or 'unknown'}|{code}".encode()).hexdigest()[:24]


class InterestService:
    def __init__(self, db, now: Callable[[], datetime] = datetime.utcnow, samples: Optional[Callable] = None,
                 owner_agent_id: Optional[Callable] = None):
        """`samples(ref)` returns {title, locality, image_url, subtitle} for a labelled sample home, else None.
        `owner_agent_id()` (async) is the platform owner agent that receives interest in samples and educational posts."""
        self.db = db
        self.store = Store(db)
        self.tracking = TrackingService(db, now=now)
        self.now = now
        self.samples = samples or (lambda ref: None)
        self.owner_agent_id = owner_agent_id

    # ---- links ----
    async def create_link(self, kind: str, ref: str, agent_id: str, channel: str, *, title: str = "", locality: str = "",
                          image_url: str = "", subtitle: str = "") -> dict:
        if kind not in KINDS or channel not in CHANNELS:
            raise InterestError("Unknown kind or channel", 422)
        ref = (ref or "").strip()
        if not ref or not agent_id:
            raise InterestError("ref and agent_id are required", 422)
        existing = await self.store.find_link(kind, ref, channel)
        if existing:
            return existing
        sample = self.samples(ref) if kind == "listing" else None
        listing = None
        if kind == "listing" and not sample:
            listing = await self.db.get_collection("listings").find_one({"_id": ref})  # read-only title lookup
        subject = sample or {}
        doc = {
            "kind": kind, "ref": ref, "agent_id": agent_id, "channel": channel, "created_at": self.now(),
            "sample": bool(sample),
            "title": (title or subject.get("title") or (listing or {}).get("title") or "")[:140],
            "locality": (locality or subject.get("locality") or (listing or {}).get("locality") or "")[:80],
            "subtitle": (subtitle or subject.get("subtitle") or "")[:200],
            "image_url": image_url or subject.get("image_url") or "",
        }
        return await self.store.insert_link(doc)

    async def links_for(self, ref: str) -> list:
        return [self.public_link(d) for d in await self.store.links_for_ref(ref)]

    def public_link(self, d: dict) -> dict:
        return {"code": d["code"], "kind": d["kind"], "ref": d["ref"], "channel": d["channel"],
                "url": f"{site_url()}/i/{d['code']}", "created_at": d["created_at"]}

    async def resolve(self, code: str) -> dict:
        link = await self.store.by_code(code.strip().lower()) if code else None
        if not link:
            raise InterestError("This link is not valid", 404)
        return link

    async def view(self, code: str) -> dict:
        link = await self.resolve(code)
        agent_id = await self._target_agent(link)
        profile = await self.tracking.profiles.find_one({"agent_id": agent_id}) or {}
        return {
            "code": link["code"], "kind": link["kind"], "channel": link["channel"], "title": link.get("title") or "",
            "subtitle": link.get("subtitle") or "", "locality": link.get("locality") or "", "image_url": link.get("image_url") or "",
            "agent_name": profile.get("agent_name") or profile.get("display_name") or "PUNE Property",
            "sample": bool(link.get("sample")), "consent_wording": CONSENT_WORDING,
        }

    async def _target_agent(self, link: dict) -> str:
        """Samples and educational pages are not any agent's home: their interest goes to the platform owner."""
        if link.get("sample") or link["kind"] == "page":
            if self.owner_agent_id:
                owner = await self.owner_agent_id()
                if owner:
                    return owner
        return link["agent_id"]

    # ---- public events ----
    async def record_click(self, code: str, ip: Optional[str] = None, anon_id: Optional[str] = None) -> dict:
        link = await self.resolve(code)
        now = self.now()
        key = ip or "unknown"
        if await self.store.attempts("click", key, now - limits.WINDOW) >= MAX_CLICKS_PER_HOUR:
            raise InterestError(limits.TOO_MANY, 429)
        await self.store.log_attempt("click", key, now)
        await self.store.add_event(link["code"], "click", _anon(ip, link["code"], anon_id), now)
        return {"recorded": True}

    async def record_interest(self, code: str, *, name: Optional[str] = None, phone: Optional[str] = None,
                              note: Optional[str] = None, consent: bool = False, website: Optional[str] = None,
                              anon_id: Optional[str] = None, ip: Optional[str] = None) -> dict:
        if limits.is_honeypot(website):  # a bot: look successful, store nothing
            return {"received": True, "new_lead": False, "details_saved": False}
        link = await self.resolve(code)
        name, phone, note = (name or "").strip(), (phone or "").strip(), (note or "").strip()
        if (name or phone or note) and not consent:
            raise InterestError("Please tick the box so we can keep your details", 400)
        now = self.now()
        key = f"{ip or 'unknown'}|{link['code']}"
        if await self.store.attempts("interest", key, now - limits.WINDOW) >= MAX_INTEREST_PER_CODE_PER_HOUR:
            raise InterestError(limits.TOO_MANY, 429)
        agent_id = await self._target_agent(link)
        profile = await self.tracking.profiles.find_one({"agent_id": agent_id})
        if not profile:
            raise InterestError("This link is not available right now", 404)
        anon = _anon(ip, link["code"], anon_id)
        context = self._context(link)
        listing_id = link["ref"] if link["kind"] == "listing" and not link.get("sample") else None
        if phone:
            try:
                res = await self.tracking.capture_inquiry(InquiryIn(
                    agent_slug=profile["slug"], anon_id=anon, name=name or "Interested visitor", phone=phone,
                    message=(f"{note}\n\n" if note else "") + context, consent=True, source=link["channel"],
                    listing_id=listing_id))
            except ValueError as e:
                raise InterestError(str(e).replace("Value error, ", ""), 422)
            except TrackingError as e:
                raise InterestError(str(e), e.status_code)
            await self._drop_placeholder(agent_id, anon)
            new_lead, details_saved = res["new_lead"], True
        else:
            new_lead = await self._anonymous_lead(agent_id, link, anon, name, note, consent, context, listing_id, now)
            details_saved = bool(name or note)
        await self.store.log_attempt("interest", key, now)
        await self.store.add_event(link["code"], "interest", anon, now)
        return {"received": True, "new_lead": new_lead, "details_saved": details_saved}

    @staticmethod
    def _context(link: dict) -> str:
        what = {"listing": "home", "post": "post", "page": "page"}[link["kind"]]
        label = f"Interested via {link['channel'].title()} {what}: {link.get('title') or link['ref']}"
        if link.get("sample"):
            return f"PLATFORM INTEREST (sample home, not a live listing). {label}"
        if link["kind"] != "listing":
            return f"PLATFORM INTEREST (educational {what}). {label}"
        return label

    async def _anonymous_lead(self, agent_id, link, anon, name, note, consent, context, listing_id, now) -> bool:
        """A one-tap interest with no contact details still lands in the agent's inbox, as an anonymous lead."""
        contacts = self.tracking.contacts
        existing = await contacts.find_one({"agent_id": agent_id, "anon_ids": anon, "phone": ""})
        message = (f"{note}\n\n" if note else "") + context
        if existing:
            changes = {"last_activity_at": now, "last_message": message}
            if name:
                changes["name"] = name
            await contacts.update_one({"_id": existing["_id"]}, {"$set": changes})
            return False
        platform = context.startswith("PLATFORM INTEREST")
        await contacts.insert_one({
            "_id": uuid.uuid4().hex, "agent_id": agent_id,
            "name": name or ("Platform interest" if platform else "Interested visitor"),
            "phone": "", "message": message, "anon_ids": [anon], "stage": "new", "source": link["channel"], "utm": {},
            "first_listing_id": listing_id,
            "consent": {"given_at": now, "purpose": "interest follow-up"} if consent else None,
            "score_base": 8, "created_at": now, "last_activity_at": now, "last_message": message,
            "notes": [], "requirement": None, "interest_code": link["code"],
        })
        return True

    async def _drop_placeholder(self, agent_id: str, anon: str) -> None:
        """When the visitor adds a number after the one-tap, the anonymous placeholder is replaced by the real lead."""
        col = self.tracking.contacts
        placeholder = await col.find_one({"agent_id": agent_id, "anon_ids": anon, "phone": ""})
        if placeholder and hasattr(col, "delete_one"):
            await col.delete_one({"_id": placeholder["_id"]})


async def interest_url(db, *, kind: str, ref: str, agent_id: str, channel: str, title: str = "", locality: str = "",
                       image_url: str = "", subtitle: str = "", samples: Optional[Callable] = None) -> str:
    """THE function other streams call: returns `<SITE>/i/<code>` for a post or listing, creating the link if needed
    (idempotent per (kind, ref, channel))."""
    svc = InterestService(db, samples=samples)
    link = await svc.create_link(kind, ref, agent_id, channel, title=title, locality=locality, image_url=image_url,
                                 subtitle=subtitle)
    return f"{site_url()}/i/{link['code']}"


# ---- hub items (filled by the integrator) ----
async def upsert_hub_item(db, kind: str, ref: str, title: str, image_url: str = "", subtitle: str = "",
                          interest_code: str = "", permalink: str = "", sample: bool = False) -> None:
    """Shape of a hub_items doc: {_id: '<kind>:<ref>', kind: 'listing'|'post', ref, title, image_url, subtitle,
    interest_code, permalink, sample, updated_at}. Newest `updated_at` first on /go (up to 12 shown)."""
    col = db.get_collection("hub_items")
    _id = f"{kind}:{ref}"
    fields = {"kind": kind, "ref": ref, "title": title, "image_url": image_url, "subtitle": subtitle,
              "interest_code": interest_code, "permalink": permalink, "sample": sample, "updated_at": datetime.utcnow()}
    if await col.find_one({"_id": _id}):
        await col.update_one({"_id": _id}, {"$set": fields})
    else:
        await col.insert_one({"_id": _id, **fields})
