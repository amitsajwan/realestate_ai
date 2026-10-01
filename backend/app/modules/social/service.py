"""Social publishing service: approval/consent, owner scoping, idempotency, publication records (`publications`).

Reads `listings` and `marketing_packs` READ-ONLY; writes only `publications`. Tokens never reach Mongo, logs or responses.
"""
from app.core import brand
import logging
import uuid
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from app.modules.marketing.content import P as content_phrases, resolve_language

from .config import BRAND, SocialConfig, load as load_config
from .graph import GraphPublisher
from .publisher import DryRunPublisher, Post, PublishError, Publisher, sanitize
from .schemas import Publication, PublishIn

log = logging.getLogger(__name__)

CONSENT_TEXT = f"I agree to post this listing on the {brand.NAME} Page"
MARKETABLE = ("live", "under_offer")
DONE = ("published", "dry_run")
IN_FLIGHT = timedelta(minutes=2)  # a `queued` record younger than this is treated as an attempt in progress
IG_ORDER = ("cover", "facts", "amenities", "cta")


class SocialError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def default_publisher(cfg: SocialConfig) -> Publisher:
    return DryRunPublisher() if cfg.dry_run else GraphPublisher(cfg)


def rebase(url: str, base: str) -> str:
    """Re-base a pack image url onto PUBLIC_MEDIA_BASE_URL, keeping the path from `/uploads/`."""
    i = (url or "").find("/uploads/")
    if i < 0:
        return url
    path = url[i:].split("?", 1)[0]
    return f"{base.rstrip('/')}{path}" if base else path


def build_payload(pack: dict, channel: str, base: str, attribution: str = "") -> dict:
    """`attribution` (concierge: 'Listed by ...' lines, never a phone number) goes between the caption and the link/hashtags."""
    imgs = pack.get("images") or {}

    def urls(kinds) -> List[str]:
        return [rebase(imgs[k]["path"], base) for k in kinds if k in imgs and imgs[k].get("path")]

    share = pack.get("share_url") or ""
    if channel == "facebook_page":
        post = (pack.get("facebook") or {}).get("post", "")
        link_line = content_phrases[resolve_language(pack.get("language") or "en")]["link"].format(url=share) if share else ""
        text = (f"{post}\n\n{attribution}\n\n{link_line}" if attribution else f"{post}\n\n{link_line}").strip()
        return {"text": text, "image_urls": urls(("cover",)), "link": share or None}
    ig = pack.get("instagram") or {}
    tags = " ".join(ig.get("hashtags") or [])
    caption = f"{ig.get('caption', '')}\n\n{attribution}" if attribution else ig.get("caption", "")
    return {"text": f"{caption}\n\n{tags}".strip(), "image_urls": urls(IG_ORDER)[:10], "link": None}


class SocialService:
    def __init__(self, db, publisher_factory: Callable[[SocialConfig], Publisher] = default_publisher,
                 config_loader: Callable[[], SocialConfig] = load_config, now: Callable[[], datetime] = datetime.utcnow):
        self.db = db
        self.listings = db.get_collection("listings")
        self.packs = db.get_collection("marketing_packs")
        self.pubs = db.get_collection("publications")
        self.publisher_factory, self.load_config, self.now = publisher_factory, config_loader, now

    def _ts(self) -> str:
        return self.now().isoformat() + "Z"

    def status(self) -> dict:
        cfg = self.load_config()
        return {"dry_run": cfg.dry_run, "channels": {c: cfg.configured(c) for c in ("facebook_page", "instagram")},
                "brand": BRAND, "media_url_ok": cfg.media_url_ok}

    # ---- queries ---------------------------------------------------------------------------------------------
    async def _listing(self, agent_id: str, listing_id: str) -> dict:
        doc = await self.listings.find_one({"_id": listing_id, "agent_id": agent_id})
        if not doc:
            raise SocialError("Listing not found", 404)
        return doc

    @staticmethod
    def _out(doc: dict) -> Publication:
        return Publication.model_validate({**doc, "id": doc["_id"]})

    async def list(self, agent_id: str, listing_id: str) -> List[Publication]:
        await self._listing(agent_id, listing_id)
        docs = await self.pubs.find({"listing_id": listing_id, "agent_id": agent_id}).sort("created_at", -1).to_list(200)
        docs = sorted(reversed(docs), key=lambda d: d["created_at"], reverse=True)  # stable: newest first even on ties
        return [self._out(d) for d in docs]

    def _in_flight(self, doc: dict) -> bool:
        try:
            return self.now() - datetime.fromisoformat(doc["updated_at"].rstrip("Z")) < IN_FLIGHT
        except (KeyError, ValueError):
            return False

    async def _same_key(self, listing_id: str, agent_id: str, channel: str, version: int) -> List[dict]:
        return await self.pubs.find({"listing_id": listing_id, "agent_id": agent_id, "channel": channel,
                                     "pack_version": version}).to_list(200)

    def _blocking(self, docs: List[dict]) -> bool:
        return any(d["status"] in DONE or (d["status"] == "queued" and self._in_flight(d)) for d in docs)

    # ---- attempts --------------------------------------------------------------------------------------------
    async def _attempt(self, cfg: SocialConfig, doc: dict) -> dict:
        """Run one attempt for the stored publication `doc`, persist the outcome and return the updated doc."""
        payload, channel = doc["payload"], doc["channel"]
        try:
            if not cfg.dry_run:
                if not cfg.configured(channel):
                    raise PublishError("channel not configured")
                if payload["image_urls"] and not (cfg.media_url_ok and all(u.lower().startswith("https://") for u in payload["image_urls"])):
                    raise PublishError("PUBLIC_MEDIA_BASE_URL must be a public https address for real posts; media urls must be https")
            res = await self.publisher_factory(cfg).publish(
                Post(channel, payload["text"], list(payload["image_urls"]), payload.get("link")))
            out = {"status": "dry_run" if cfg.dry_run else "published", "external_id": res.external_id,
                   "permalink": res.permalink, "error": None}
        except PublishError as e:
            out = {"status": "failed", "external_id": None, "permalink": None, "error": sanitize(e, cfg.secrets)}
        except Exception as e:  # never a 500 to the agent: record the failure (type only, text may echo secrets)
            out = {"status": "failed", "external_id": None, "permalink": None,
                   "error": sanitize(f"Unexpected error while posting ({type(e).__name__})", cfg.secrets)}
        out["updated_at"] = self._ts()
        await self.pubs.update_one({"_id": doc["_id"]}, {"$set": out, "$inc": {"attempts": 1}})
        log.info("social publication %s channel=%s status=%s%s", doc["_id"], channel, out["status"],
                 f" error={out['error']}" if out["error"] else "")
        return {**doc, **out, "attempts": doc["attempts"] + 1}

    async def _start(self, doc: dict, cfg: SocialConfig) -> Publication:
        await self.pubs.update_one({"_id": doc["_id"]}, {"$set": {"status": "queued", "updated_at": self._ts()}})
        return self._out(await self._attempt(cfg, {**doc, "status": "queued"}))

    async def _attribution(self, agent_id: str, listing: dict, channel: str) -> str:
        """Concierge attribution lines for an agent's listing on the Avasetu pages ('' for the owner's own)."""
        from app.modules.concierge.attribution import attribution_text
        return await attribution_text(self.db, agent_id, listing, channel)

    async def captions(self, agent_id: str, listing_id: str, channels: List[str]) -> dict:
        """The exact text each channel would post, without posting or recording anything."""
        listing = await self._listing(agent_id, listing_id)
        pack = await self.packs.find_one({"_id": listing_id, "agent_id": agent_id})
        if not pack:
            raise SocialError("Create the marketing pack for this listing first", 409)
        base = self.load_config().media_base_url
        return {c: build_payload(pack, c, base, await self._attribution(agent_id, listing, c)) for c in dict.fromkeys(channels)}

    # ---- publish ---------------------------------------------------------------------------------------------
    async def publish(self, agent_id: str, listing_id: str, body: PublishIn) -> List[Publication]:
        if not (body.approve and body.consent):
            raise SocialError("Both approve and consent must be true to post", 422)
        listing = await self._listing(agent_id, listing_id)
        if listing.get("status") not in MARKETABLE:
            raise SocialError("Only live or under-offer listings can be posted", 409)
        if (listing.get("title") or "").strip().lower().startswith("sample"):  # illustrations are never posted, in any mode
            raise SocialError("Sample listings are illustrations and cannot be posted to social media", 409)
        pack = await self.packs.find_one({"_id": listing_id, "agent_id": agent_id})
        if not pack:
            raise SocialError("Create the marketing pack for this listing first", 409)
        cfg, version = self.load_config(), int(pack.get("version") or 1)
        channels = list(dict.fromkeys(body.channels))
        payloads = {c: build_payload(pack, c, cfg.media_base_url, await self._attribution(agent_id, listing, c)) for c in channels}
        if "instagram" in channels and not payloads["instagram"]["image_urls"]:
            raise SocialError("Instagram needs at least one image and this marketing pack has none", 400)
        existing = {c: await self._same_key(listing_id, agent_id, c, version) for c in channels}
        if not body.force:
            dup = [c for c in channels if self._blocking(existing[c])]
            if dup:
                raise SocialError(f"Already posted for pack version {version} on: {', '.join(dup)}. Use force to post again", 409)
        now = self._ts()
        consent = {"given_at": now, "text": CONSENT_TEXT}
        results = []
        for c in channels:
            failed = [d for d in existing[c] if d["status"] == "failed"]
            if failed and not body.force:  # re-attempt the failed record rather than piling up duplicates
                doc = {**failed[-1], "payload": payloads[c], "consent": consent, "approved_at": now}
                await self.pubs.update_one({"_id": doc["_id"]}, {"$set": {"payload": payloads[c], "consent": consent, "approved_at": now}})
            else:
                doc = {"_id": uuid.uuid4().hex, "listing_id": listing_id, "agent_id": agent_id, "channel": c, "pack_version": version,
                       "status": "queued", "external_id": None, "permalink": None, "error": None, "consent": consent,
                       "approved_at": now, "created_at": now, "updated_at": now, "attempts": 0, "payload": payloads[c]}
                await self.pubs.insert_one(doc)
            res = await self._start(doc, cfg)
            if c == "instagram" and res.status == "published":
                from app.modules.concierge.attribution import register_hub_item
                await register_hub_item(self.db, agent_id, listing, pack, cfg.media_base_url, res.permalink or "")
            results.append(res)
        return results

    async def retry(self, agent_id: str, publication_id: str) -> Publication:
        doc = await self.pubs.find_one({"_id": publication_id, "agent_id": agent_id})
        if not doc:
            raise SocialError("Publication not found", 404)
        if doc["status"] != "failed":
            raise SocialError("Only failed publications can be retried", 409)
        listing = await self._listing(agent_id, doc["listing_id"])
        if listing.get("status") not in MARKETABLE:
            raise SocialError("Only live or under-offer listings can be posted", 409)
        others = [d for d in await self._same_key(doc["listing_id"], agent_id, doc["channel"], doc["pack_version"]) if d["_id"] != doc["_id"]]
        if self._blocking(others):
            raise SocialError("This listing was already posted on this channel for this pack version", 409)
        return await self._start(doc, self.load_config())
