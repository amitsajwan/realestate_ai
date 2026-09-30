# Contract: social publishing to the PUNE Property brand accounts (Sprint 5, frozen)

Scope: publish a listing's MARKETING PACK (docs/contracts/marketing.md) to ONE brand Facebook Page and its linked Instagram
Business account, using the Meta Graph API with a Page access token. This works without Meta App Review because the token
belongs to a person who is an admin/developer of the Meta app. It is NOT publishing to each agent's own accounts (that needs App
Review and Business Verification; later).

Safety rules (non-negotiable):
1. HUMAN APPROVAL for every post. Nothing is ever posted without an explicit `approve: true` request from the agent who owns the listing.
2. CONSENT. The agent must also send `consent: true` ("I agree to post this listing, on the PUNE Property
   Page"); it is stored with the publication. Only the owning agent's own live listings can be posted.
3. DRY RUN by default. `SOCIAL_DRY_RUN` defaults to true: nothing leaves the server, publications are recorded with status `dry_run`.
4. SECRETS. Tokens live only in environment variables. Never log them, never return them, never store them in Mongo, and strip
   `access_token=...` from any error text before storing or returning it.
5. No silent failure: every attempt has a stored record with status and error.
6. No fabricated engagement: never generate or display made-up views/likes/follower numbers.

## Configuration (env, read through app.core.config.settings or os.environ; never committed)
```
SOCIAL_DRY_RUN=true|false           default true
META_GRAPH_VERSION=v23.0            default v23.0 (configurable; Meta retires old versions)
META_PAGE_ID, META_PAGE_ACCESS_TOKEN            Facebook Page publishing
META_IG_BUSINESS_ID                              Instagram publishing (uses the same Page token)
PUBLIC_MEDIA_BASE_URL=https://...                public HTTPS base that serves our /uploads (e.g. a Cloudflare tunnel); required for real posts
```
A channel is "configured" only when its ids/token are set. Real (non dry-run) posting additionally requires `PUBLIC_MEDIA_BASE_URL` to be
https; image urls sent to Meta are the pack's image paths re-based onto that URL (Meta fetches the image; Instagram requires it).

## Publication record  (collection `publications`)
```
Publication { id, listing_id, agent_id, channel: "facebook_page" | "instagram", pack_version: int,
              status: "queued" | "published" | "failed" | "dry_run",
              external_id: string | null, permalink: string | null, error: string | null,
              consent: { given_at, text }, approved_at, created_at, updated_at, attempts: int,
              payload: { text: string, image_urls: string[] } }      snapshot of exactly what was/would be posted
```
Idempotency: a listing + channel + pack_version that is already `published` (or `dry_run`) is not posted again unless `force: true`
(409 otherwise); a `failed` one can be retried.

## Content per channel (from the stored MarketingPack)
- facebook_page: text = pack.facebook.post + "\n" + pack.share_url; one photo (the cover image card) with that caption when an image is
  available, else a plain feed post with the link.
- instagram: caption = pack.instagram.caption + "\n\n" + hashtags joined by spaces; a carousel of pack.instagram.images (2-10 items) or a
  single image when only one exists; Instagram requires at least one image (400 with a clear message if the pack has none).
Graph flow: Page photo -> `POST /{page-id}/photos` (url, caption, published=true) or `POST /{page-id}/feed` (message, link).
Instagram -> create item containers (`POST /{ig-id}/media` image_url, is_carousel_item=true), then the carousel container (`media_type=CAROUSEL`,
children, caption) or a single image container (image_url, caption), poll `GET /{container-id}?fields=status_code` until FINISHED (max ~60 s,
ERROR/EXPIRED -> failed), then `POST /{ig-id}/media_publish` (creation_id). Fetch the permalink with `GET /{media-id}?fields=permalink` best effort.

## API (bearer auth, mounted by the integrator at prefix /social; owner scoped; other agents get 404)
```
GET  /social/status                          -> { dry_run: bool, channels: { facebook_page: bool, instagram: bool }, brand: "PUNE Property",
                                                   media_url_ok: bool }        (no secrets)
POST /social/listings/{listing_id}/publish   body { channels: ["facebook_page"|"instagram", ...], approve: true, consent: true, force?: bool }
                                             -> { publications: Publication[] }     422 unless approve and consent are both true; 409 when there is no
                                                marketing pack yet or the listing is not live/under_offer; a channel that is not configured is recorded as
                                                failed with the error "channel not configured" (dry run ignores configuration and records dry_run)
GET  /social/listings/{listing_id}/publications -> { items: Publication[] }         newest first
POST /social/publications/{id}/retry         -> Publication                          only for status failed
```

## Ownership (Sprint 5)
- B  backend/app/modules/social/** and backend/tests/modules/test_social*.py (integrator mounts router at /social and adds settings)
- F  frontend/components/app/**, frontend/lib/app/**, frontend/app/studio/**, frontend/__tests__/app/** (the "Post to PUNE Property" section on the marketing screen)
