"""Marketing pack generation + storage (`marketing_packs`, _id = listing_id, owner scoped by agent_id)."""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .content import build_content
from .facts import Facts
from .images import render_all
from .polish import Polish, polish_content
from .schemas import MarketingPack

MARKETABLE = ("live", "under_offer")


class MarketingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class MarketingService:
    def __init__(self, db, uploads_dir, public_site_url: str, polish: Optional[Polish] = None,
                 now: Callable[[], datetime] = datetime.utcnow):
        self.listings = db.get_collection("listings")
        self.profiles = db.get_collection("agent_public_profiles")
        self.packs = db.get_collection("marketing_packs")
        self.uploads_dir = Path(uploads_dir)
        self.site = (public_site_url or "").rstrip("/")
        self.polish = polish  # not wired by default
        self.now = now

    async def _listing(self, agent_id: str, listing_id: str) -> dict:
        doc = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise MarketingError("Listing not found", 404)
        return doc

    def _share_url(self, slug: Optional[str], listing_id: str) -> str:
        if slug:
            return f"{self.site}/agent/{slug}/listings/{listing_id}?src=whatsapp"
        return f"{self.site}/listings/{listing_id}?src=whatsapp"  # agent has no public profile yet

    @staticmethod
    def _asset(kind: str, meta: dict, base_url: str) -> dict:
        return {"kind": kind, "url": f"{base_url.rstrip('/')}{meta['path']}", "width": meta["width"], "height": meta["height"]}

    def _out(self, doc: dict, base_url: str) -> MarketingPack:
        imgs = doc.get("images", {})
        order = ["cover", "facts", "amenities", "cta"]
        ig = {**doc["instagram"], "images": [self._asset(k, imgs[k], base_url) for k in order if k in imgs]}
        wa = {**doc["whatsapp"], "status_image": self._asset("status", imgs["status"], base_url) if "status" in imgs else None}
        return MarketingPack.model_validate({**{k: doc[k] for k in (
            "language", "version", "generated_at", "angle", "headline", "facebook", "reel", "share_url")},
            "listing_id": doc["_id"], "instagram": ig, "whatsapp": wa})

    async def generate(self, agent_id: str, listing_id: str, language: str, base_url: str) -> MarketingPack:
        listing = await self._listing(agent_id, listing_id)
        if listing.get("status") not in MARKETABLE:
            raise MarketingError("Only live or under-offer listings can be marketed. Publish this listing first.", 409)
        profile = await self.profiles.find_one({"agent_id": agent_id})
        facts = Facts.from_docs(listing, profile, self._share_url((profile or {}).get("slug"), listing_id))
        content = await polish_content(build_content(facts, language), facts, self.polish)
        try:
            images = await asyncio.to_thread(render_all, facts, listing.get("media") or [], self.uploads_dir, listing_id)
        except Exception as e:  # disk full, permissions...: surface as a clean error
            raise MarketingError(f"Could not render images: {e}", 500)
        prev = await self.packs.find_one({"_id": listing_id, "agent_id": agent_id})
        doc = {**content, "agent_id": agent_id, "images": images, "share_url": facts.share_url,
               "version": (prev.get("version", 0) if prev else 0) + 1,
               "generated_at": self.now().replace(microsecond=0).isoformat() + "Z"}
        if prev:
            await self.packs.update_one({"_id": listing_id, "agent_id": agent_id}, {"$set": doc})
        else:
            await self.packs.insert_one({"_id": listing_id, **doc})
        return self._out({"_id": listing_id, **doc}, base_url)

    async def get(self, agent_id: str, listing_id: str, base_url: str) -> MarketingPack:
        await self._listing(agent_id, listing_id)
        doc = await self.packs.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise MarketingError("No marketing pack yet for this listing", 404)
        return self._out(doc, base_url)
