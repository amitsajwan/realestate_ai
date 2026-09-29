# Handoff: M (marketing pack backend)

Branch `v2/m-marketing`, based on 0fed337. Implements docs/contracts/marketing.md section 1 exactly (contract untouched).

## What shipped (`backend/app/modules/marketing/`)
- `facts.py` listing facts, money (`Rs 85 L`, `Rs 1.25 Cr`, `Rs 45,000/month`), budget bucket, en/hi/mr word tables.
- `content.py` deterministic copy: angle, headline (<=90), Instagram caption (<=900, ends with CTA) + hashtags (<=12,
  sanitised, unique), Facebook post, WhatsApp message + status_text, 5-beat reel script (~15 s). Built only from listing facts.
- `polish.py` optional `Polish = Callable[[str, str], Awaitable[str]]`, applied per field, rejected when a protected fact
  (price text, BHK, locality, area, RERA) or the share link that the draft contained is missing, when empty/over the limit,
  or when the callable raises. NOT wired by default (`MarketingService(polish=None)`).
- `images.py` Pillow cards: cover, facts, amenities (only with amenities), cta at 1080x1080 and status at 1080x1920, JPEG q85
  (steps down to stay < 380 KB), written to `<uploads>/marketing/<listing_id>/<kind>.jpg`. Text-fit helper `fit_text`,
  `Card.boxes` records every drawn text box (tests assert margins).
- `service.py`, `router.py`, `schemas.py`. Collection `marketing_packs` (`_id` = listing_id, plus `agent_id`).

## Mount line for the integrator
```python
from app.modules.marketing.router import router as marketing_router
api_router.include_router(marketing_router, prefix="/listings", tags=["marketing"])
```
Routes: `POST /listings/{id}/marketing` (body optional `{language}`), `GET /listings/{id}/marketing`. Cannot shadow the
listings routes (path ends in `/marketing`); mount order does not matter.

## Config / env
No new env. Uses `settings.public_site_url` (share_url) and `settings.upload_directory` (default `uploads`, the same
directory the `/uploads` static mount serves). No new dependencies (Pillow already installed).

## Behaviour notes
- Owner only: unknown or other agent's listing -> 404 (also for GET). Status must be live/under_offer, else 409
  ("Only live or under-offer listings can be marketed. Publish this listing first."). GET with no pack -> 404.
- Regenerate: `version += 1`, `generated_at` refreshed, images overwritten, stale `amenities.jpg` removed.
- Image `url`s are stored as relative paths and made absolute from `request.base_url` on every response (host changes are safe).
- Photo background only when the first image's URL path is exactly `/uploads/images/<safe-name>` and the file exists (host part
  is ignored, nothing is ever fetched; symlinks escaping the dir, `..`, `%`, subdirs, backslashes all rejected). Otherwise a
  gradient card with a palette picked by md5(agent_name|locality).

## Deviations / gaps
- hi/mr: templates cover headline, Instagram caption, Facebook post, WhatsApp message + status_text, reel. `angle` stays English
  in every language (contract example is English). Amenity names, locality, "sq ft" and "Rs" are kept as entered/Latin.
  Unsupported language -> English and `language` reports "en" (the API only accepts en/hi/mr, so this is a service-level safety net).
- Agent without a public profile: share_url falls back to `<site>/listings/<id>?src=whatsapp` and the copy uses no agent name.
- Image text is Latin only; non-Latin agent names are dropped from images (no tofu boxes).
- `Facts.area` prefers carpet, else super built-up (labelled). Money rounds to 2 decimals in lakh/crore.
- Version bump is read-then-write (not atomic); fine for a single owner clicking regenerate.
- Reel visuals are generic shooting directions (not facts). Nothing is posted to any external network.
