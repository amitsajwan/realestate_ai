"""Concierge service: the owner sets up and manages agents on their behalf.

Collections: `concierge_agents` (one row per managed agent: consent, who added him), `concierge_audit` (every change:
who, when, what, agent, changed KEYS only). Everything else goes through the existing services (invites, onboarding,
listings, marketing, social), so all their validation and owner scoping apply unchanged.

Phone numbers: stored only where the app already keeps them (invites, profile, this agent row); responses mask them,
except the invite response, which goes to the owner who must send the code.
"""
from app.core import brand
import urllib.parse
from datetime import datetime
from types import SimpleNamespace
from typing import Callable, List, Optional

from pydantic import ValidationError

from app.modules.listings.schemas import ListingCreate, ListingUpdate
from app.modules.listings.service import ListingError

CONSENT_TEXT = (f"I agree that {brand.NAME} may feature me and my listings on the {brand.NAME} Facebook Page, Instagram "
                "and website, with my name and RERA number, and that buyers' interest comes to my inbox.")

# Price sanity (INR): catches a missed zero or a monthly rent typed as a sale price. Not a market opinion.
SALE_RANGE = (500_000, 5_000_000_000)
RENT_RANGE = (1_000, 1_000_000)

CHECKLIST = (("logo", "Logo"), ("banner", "Banner"), ("rera_no", "RERA agent number"), ("areas", "Areas"),
             ("photo", "Photo"), ("first_listing", "First listing"), ("three_listings", "3 listings"),
             ("consent", "Consent to be featured"))


class ConciergeError(Exception):
    def __init__(self, message: str, status_code: int = 400, detail=None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail if detail is not None else message


def mask_phone(phone: str) -> str:
    digits = "".join(c for c in str(phone or "") if c.isdigit())[-10:]
    return f"{digits[:2]}******{digits[-2:]}" if len(digits) == 10 else ""


def check_price(transaction: Optional[str], price: Optional[int]) -> None:
    if not price or transaction not in ("sale", "rent"):
        return
    lo, hi = SALE_RANGE if transaction == "sale" else RENT_RANGE
    if not lo <= price <= hi:
        raise ConciergeError(f"Price looks wrong for a {transaction}: check the zeros (allowed Rs {lo:,} to Rs {hi:,})", 422)


def _iso(dt) -> Optional[str]:
    return dt.isoformat() + ("Z" if isinstance(dt, datetime) and dt.tzinfo is None else "") if isinstance(dt, datetime) else dt


class ConciergeService:
    def __init__(self, db, *, invites, onboarding, users, listings, social=None, marketing=None, site_url: str = "",
                 now: Callable[[], datetime] = datetime.utcnow, reels=None):
        self.db = db
        self.reels = reels  # app.modules.reels.listing_reel.ReelJobs (listing reels made on the agent's behalf)
        self.agents = db.get_collection("concierge_agents")
        self.audit_col = db.get_collection("concierge_audit")
        self.profiles = db.get_collection("agent_public_profiles")
        self.listing_docs = db.get_collection("listings")
        self.invites, self.onboarding, self.users = invites, onboarding, users
        self.listings, self.social, self.marketing = listings, social, marketing
        self.site = site_url.rstrip("/")
        self.now = now

    # ---- helpers -------------------------------------------------------------------------------------------
    async def _audit(self, owner_id: str, action: str, agent_id: Optional[str], keys: List[str] = (), **extra) -> None:
        """Who/when/what, and which KEYS changed. Never values, codes or phone numbers."""
        await self.audit_col.insert_one({"at": self.now(), "by": owner_id, "action": action, "agent_id": agent_id,
                                         "keys": sorted(keys), **extra})

    async def _agent(self, agent_id: str) -> dict:
        doc = await self.agents.find_one({"_id": agent_id})
        if not doc:
            raise ConciergeError("Agent not found", 404)
        return doc

    def _site_url(self, profile: Optional[dict]) -> Optional[str]:
        return f"{self.site}/agent/{profile['slug']}" if profile else None

    async def _summary(self, rec: dict) -> dict:
        agent_id = rec["_id"]
        profile = await self.profiles.find_one({"agent_id": agent_id}) or {}
        branding = profile.get("branding_data") or {}
        docs = await self.listing_docs.find({"agent_id": agent_id}).to_list(500)
        live = [d for d in docs if d.get("status") in ("live", "under_offer")]
        consent = rec.get("consent") or {}
        done = {
            "logo": bool(branding.get("logo")), "banner": bool(branding.get("banner")),
            "rera_no": bool(branding.get("rera_agent_no")),
            "areas": bool(branding.get("areas") or profile.get("specialties")),
            "photo": bool(profile.get("photo")), "first_listing": len(live) >= 1, "three_listings": len(live) >= 3,
            "consent": bool(consent.get("given")),
        }
        checklist = [{"key": k, "label": label, "done": done[k]} for k, label in CHECKLIST]
        stamps = [x for x in [profile.get("updated_at"), rec.get("created_at"), consent.get("at")]
                  + [d.get("updated_at") for d in docs] if isinstance(x, datetime)]
        last = max(stamps) if stamps else None
        return {"id": agent_id, "name": rec["name"], "label": rec.get("label", ""), "slug": profile.get("slug"),
                "mobile": mask_phone(rec.get("phone")), "site_url": self._site_url(profile),
                "checklist": checklist, "progress": {"done": sum(done.values()), "total": len(checklist)},
                "listing_count": len(live), "consent_given": done["consent"], "last_activity": _iso(last)}

    # ---- agents --------------------------------------------------------------------------------------------
    async def create_agent(self, owner_id: str, name: str, mobile: str, label: str = "", reissue: bool = False) -> dict:
        """Create (or reuse) the agent: his login user, his site and his invite code. The code is stored hashed, so an
        existing agent only gets a fresh code when `reissue` is true (the old one then stops working)."""
        from app.modules.onboarding.schemas import SiteCreate
        phone = mobile  # already normalised (+91XXXXXXXXXX) by the request model
        existing = await self.agents.find_one({"phone": phone})
        user = await self.users.get_by_phone(phone) or await self.users.create(phone)
        await self.onboarding.create_site(user, SiteCreate(name=name, city="Pune", whatsapp=phone))
        agent_id = str(user.id)
        now = self.now()
        if not existing:
            await self.agents.insert_one({"_id": agent_id, "phone": phone, "name": name, "label": label,
                                          "created_by": owner_id, "created_at": now, "consent": None})
            await self._audit(owner_id, "agent.create", agent_id, ["name", "label"])
        code = None
        if not existing or reissue:
            code = await self.invites.issue(phone, label or name)
            await self._audit(owner_id, "invite.issue", agent_id, ["invite"])
        rec = await self.agents.find_one({"_id": agent_id})
        out = {"agent": await self._summary(rec), "created": not existing, "code": code, "reissued": bool(existing and reissue),
               "whatsapp_message": None, "whatsapp_url": None}
        if code:
            first = (name.split() or [name])[0]
            msg = (f"Hi {first}, welcome to {brand.NAME}! Open {self.site}/join, enter {phone[3:]} and your personal "
                   f"code {code}. Please don't share it.")
            out["whatsapp_message"] = msg
            out["whatsapp_url"] = f"https://wa.me/{phone.lstrip('+')}?text={urllib.parse.quote(msg)}"
        return out

    async def list_agents(self, limit: int = 200) -> List[dict]:
        recs = await self.agents.find({}).sort("created_at", -1).limit(limit).to_list(limit)
        return [await self._summary(r) for r in recs]

    async def get_agent(self, agent_id: str) -> dict:
        rec = await self._agent(agent_id)
        out = await self._summary(rec)
        listings = await self.listings.list_mine(agent_id)
        out["listings"] = [x.model_dump(mode="json") for x in listings]
        out["consent"] = {"text": CONSENT_TEXT, **{k: _iso(v) for k, v in (rec.get("consent") or {}).items() if k != "text"}}
        return out

    async def record_consent(self, owner_id: str, agent_id: str, given: bool = True, text: Optional[str] = None) -> dict:
        rec = await self._agent(agent_id)
        if text is not None and text.strip() != CONSENT_TEXT:
            raise ConciergeError("Consent text does not match the current wording", 422)
        now = self.now()
        consent = ({"given": True, "text": CONSENT_TEXT, "at": now, "recorded_by": owner_id} if given
                   else {**(rec.get("consent") or {}), "given": False, "revoked_at": now, "revoked_by": owner_id})
        await self.agents.update_one({"_id": agent_id}, {"$set": {"consent": consent}})
        await self._audit(owner_id, "consent.give" if given else "consent.revoke", agent_id, ["consent"])
        return {"text": CONSENT_TEXT, **{k: _iso(v) for k, v in consent.items() if k != "text"}}

    async def has_consent(self, agent_id: str) -> bool:
        return bool(((await self._agent(agent_id)).get("consent") or {}).get("given"))

    # ---- listings on behalf --------------------------------------------------------------------------------
    async def create_listing(self, owner_id: str, agent_id: str, body: ListingCreate) -> dict:
        await self._agent(agent_id)
        check_price(body.transaction, body.price_inr)
        listing = await self.listings.create(agent_id, body)
        await self._audit(owner_id, "listing.create", agent_id, list(body.model_dump(exclude_defaults=True)), listing_id=listing.id)
        return listing.model_dump(mode="json")

    async def patch_listing(self, owner_id: str, agent_id: str, listing_id: str, body: ListingUpdate) -> dict:
        await self._agent(agent_id)
        current = await self.listings.get_mine(agent_id, listing_id)
        changes = body.model_dump(exclude_unset=True)
        check_price(changes.get("transaction", current.transaction), changes.get("price_inr", current.price_inr))
        listing = await self.listings.patch(agent_id, listing_id, body)
        await self._audit(owner_id, "listing.update", agent_id, list(changes), listing_id=listing_id)
        return listing.model_dump(mode="json")

    async def publish_listing(self, owner_id: str, agent_id: str, listing_id: str) -> dict:
        await self._agent(agent_id)
        current = await self.listings.get_mine(agent_id, listing_id)
        check_price(current.transaction, current.price_inr)
        listing = await self.listings.publish(agent_id, listing_id)
        await self._audit(owner_id, "listing.publish", agent_id, ["status"], listing_id=listing_id,
                          before_status=current.status, after_status=listing.status)
        return listing.model_dump(mode="json")

    # ---- branding ------------------------------------------------------------------------------------------
    async def get_branding(self, agent_id: str) -> dict:
        await self._agent(agent_id)
        profile = await self.profiles.find_one({"agent_id": agent_id}) or {}
        return {**(profile.get("branding_data") or {}), "agent_name": profile.get("agent_name"), "photo": profile.get("photo", "")}

    async def update_branding(self, owner_id: str, agent_id: str, data: dict) -> dict:
        """Delegates to the onboarding service. Uses its full branding update when available (A1), else the existing
        site update (logo, photo, Instagram, Facebook)."""
        await self._agent(agent_id)
        who = SimpleNamespace(id=agent_id)
        try:
            from app.modules.onboarding.schemas import SiteUpdate
            result = await self.onboarding.update_site(who, SiteUpdate(**data))
        except ConciergeError:
            raise
        except ValidationError as e:
            raise ConciergeError(e.errors()[0].get("msg", "Invalid branding"), 422)
        except Exception as e:
            if getattr(e, "status_code", None):
                raise ConciergeError(str(e), e.status_code)
            raise
        await self._audit(owner_id, "branding.update", agent_id, list(data))
        return result

    # ---- posting to the Avasetu pages ----------------------------------------------------------------------
    def _need_social(self):
        if not self.social:
            raise ConciergeError("Posting is not configured", 503)
        return self.social

    async def make_pack(self, owner_id: str, agent_id: str, listing_id: str, base_url: str, language: str = "en") -> dict:
        await self._agent(agent_id)
        if not self.marketing:
            raise ConciergeError("Marketing is not configured", 503)
        from app.modules.marketing.service import MarketingError
        try:
            pack = await self.marketing.generate(agent_id, listing_id, language, base_url)
        except MarketingError as e:
            raise ConciergeError(str(e), e.status_code)
        await self._audit(owner_id, "pack.generate", agent_id, ["pack"], listing_id=listing_id)
        return pack.model_dump(mode="json")

    async def captions(self, agent_id: str, listing_id: str, channels: List[str]) -> dict:
        from app.modules.social.service import SocialError
        await self._agent(agent_id)
        try:
            return await self._need_social().captions(agent_id, listing_id, channels)
        except SocialError as e:
            raise ConciergeError(str(e), e.status_code)

    async def post_listing(self, owner_id: str, agent_id: str, listing_id: str, channels: List[str]) -> List[dict]:
        """The owner approves on the agent's behalf, which requires the agent's recorded consent."""
        from app.modules.social.schemas import PublishIn
        from app.modules.social.service import SocialError
        await self._agent(agent_id)
        if not await self.has_consent(agent_id):
            raise ConciergeError("Record the agent's consent before posting his listings", 409)
        try:
            pubs = await self._need_social().publish(agent_id, listing_id, PublishIn(channels=channels, approve=True, consent=True))
        except SocialError as e:
            raise ConciergeError(str(e), e.status_code)
        await self._audit(owner_id, "listing.post", agent_id, ["publications"], listing_id=listing_id,
                          channels=list(channels), statuses=[p.status for p in pubs])
        return [p.model_dump(mode="json") for p in pubs]

    # ---- listing reels on behalf -----------------------------------------------------------------------------
    def _need_reels(self):
        if not self.reels:
            raise ConciergeError("Reels are not configured", 503)
        return self.reels

    async def make_reel(self, owner_id: str, agent_id: str, listing_id: str, lang: str = "en", again: bool = False):
        from app.modules.reels.listing_reel import ReelJobError
        await self._agent(agent_id)
        try:
            doc, created = await self._need_reels().create(agent_id, listing_id, lang, again)
        except ReelJobError as e:
            raise ConciergeError(e.detail, e.status_code)
        if created:
            await self._audit(owner_id, "reel.make", agent_id, ["reel"], listing_id=listing_id, lang=lang)
        return doc, created

    async def reels_for(self, agent_id: str, listing_id: str) -> dict:
        from app.modules.reels.listing_reel import ReelJobError
        await self._agent(agent_id)
        try:
            return await self._need_reels().latest(agent_id, listing_id)
        except ReelJobError as e:
            raise ConciergeError(e.detail, e.status_code)

    async def post_reel(self, owner_id: str, agent_id: str, listing_id: str, lang: str, channels: List[str], publish_fn=None,
                        config_loader=None) -> List[dict]:
        """Post the finished listing reel on the Avasetu Instagram / Facebook Page as a Reel. Needs the recorded consent;
        SOCIAL_DRY_RUN (the default) checks everything and publishes nothing. The caption carries the 'Listed by' line."""
        from app.modules.reels import listing_reel
        from app.modules.social import reel_publish
        from app.platform.meta_graph.config import load as load_config
        from app.modules.social.distribution import send
        from app.platform.meta_graph.publisher import PublishError
        from .attribution import attribution_text, register_hub_item
        await self._agent(agent_id)
        if not await self.has_consent(agent_id):
            raise ConciergeError("Record the agent's consent before posting his listings", 409)
        listing = await self.listing_docs.find_one({"_id": listing_id, "agent_id": agent_id})
        if not listing:
            raise ConciergeError("Listing not found", 404)
        if listing.get("status") not in ("live", "under_offer"):
            raise ConciergeError("Only live listings can be posted", 409)
        job = await self._need_reels().latest_done(agent_id, listing_id, lang)
        if not job or not job.get("video_path"):
            raise ConciergeError("Make the reel first, then post it", 409)
        cfg = (config_loader or load_config)()
        publish_fn = publish_fn or reel_publish.publish_reel
        name = job["video_path"].rsplit("/", 1)[-1]
        file_path = self.reels.uploads_dir / "reels" / name
        done = {p["channel"]: p for p in (job.get("posts") or []) if p.get("status") == "published"}
        results = []
        for ch in channels:
            if ch in done:
                results.append({**done[ch], "status": "already_posted"})
                continue
            text = listing_reel.caption(listing, await attribution_text(self.db, agent_id, listing, ch))
            try:
                try:
                    url = reel_publish.public_url(cfg, name)
                except PublishError:
                    if not cfg.dry_run:
                        raise
                    url = job["video_path"]  # test mode never sends it anywhere
                extra = {}
                if ch == "instagram" and reel_publish.cover_file(file_path) is not None:  # the hook still as the reel's cover
                    try:
                        extra["cover_url"] = reel_publish.staged_cover_url(cfg, file_path, self.reels.uploads_dir, name)
                    except PublishError:
                        if not cfg.dry_run:
                            raise
                        extra["cover_url"] = job["video_path"].rsplit("/", 1)[0] + "/" + reel_publish.cover_name(name)
                # one reel job is posted at most once per channel, even if saving the outcome fails and it is posted again
                res = await send(self.db, f"reel:{job['_id']}:{ch}",
                                 lambda: publish_fn(ch, url, text, cfg=cfg, file_path=file_path if ch == "facebook_page" else None, **extra),
                                 dry_run=cfg.dry_run)
                status = "dry_run" if cfg.dry_run else "published"
                results.append({"channel": ch, "status": status, "external_id": res.external_id, "permalink": res.permalink,
                                "error": None, "caption": text})
                if status == "published" and ch == "instagram":
                    try:
                        await register_hub_item(self.db, agent_id, listing, {}, cfg.media_base_url, res.permalink or "")
                    except Exception:
                        pass  # the reel is out; the link-in-bio hub is best effort
            except PublishError as e:
                results.append({"channel": ch, "status": "failed", "external_id": None, "permalink": None, "error": str(e), "caption": text})
        keep = [p for p in (job.get("posts") or []) if p["channel"] not in {r["channel"] for r in results if r["status"] != "already_posted"}]
        await self.reels.jobs.update_one({"_id": job["_id"]}, {"$set": {"posts": keep + [
            {k: r[k] for k in ("channel", "status", "external_id", "permalink", "error")} for r in results if r["status"] != "already_posted"]}})
        await self._audit(owner_id, "reel.post", agent_id, ["reel"], listing_id=listing_id, lang=lang,
                          channels=list(channels), statuses=[r["status"] for r in results])
        return results


def listing_http(e: ListingError):
    return e.status_code, e.detail
