# S1 Listings backend - handoff

Branch `v2/s1-listings`. Implements docs/contracts/listing.md (unchanged).

## Shipped
- `backend/app/modules/listings/`: `schemas.py`, `service.py` (ListingService), `router.py` (`router`, `public_router`, `get_service`).
- Tests: `tests/modules/test_listings_service.py`, `test_listings_router.py`, helper `listings_fakes.py` (adds `$in`, `$ne`, `skip()`; fakes.py untouched).
- Mongo collection `listings` (`_id` == `id` == uuid hex). Public reads resolve `agent_public_profiles` (slug, agent_id, is_public).

## Router mount lines (backend/app/api/v1/router.py)
```python
from app.modules.listings.router import router as listings_router, public_router as listings_public_router
api_router.include_router(listings_router, prefix="/listings", tags=["listings"])
api_router.include_router(listings_public_router, prefix="/public", tags=["public"])
```
Routes are declared with path "" (no trailing slash), so `POST /listings` needs no redirect.

## /listings/ai/draft
Own routes are `POST/GET ""`, `GET/PATCH /{listing_id}`, `POST /{listing_id}/publish|status`. `/ai/draft` has two segments and
its second is the literal `draft`, so `/{listing_id}` and `/{listing_id}/publish|status` never match it; mount order is irrelevant
(covered by a router test that mounts a stand-in `/listings/ai/draft` after). Caveat: a listing id of `ai` cannot exist (ids are uuid hex).

## Behaviour notes
- Errors: 404 for missing or not-yours (never 403); 409 illegal transition / re-publish; 422 publish with missing fields:
  `detail = {"message": "...", "missing": ["title", "media", "description.en", ...]}` ("media" = no image).
- Transitions via `POST /{id}/status`: live -> under_offer/sold/rented/paused/expired; under_offer -> live/sold/rented/paused/expired;
  paused -> live/expired; expired -> live; draft -> live only via `publish`; sold/rented terminal. paused/expired -> live re-stamps
  `freshness_confirmed_at`.
- `fingerprint` (`city|locality|project|bhk|carpet bucket(50 sqft)|transaction`, normalised) stored on the doc at publish and refreshed
  when a non-draft listing's key fields are patched. Not part of the API response.
- Public list: status in (live, under_offer), visibility in (public, network), newest `published_at` first, `limit` 1..100 (default 20), `offset`.
  Unknown or `is_public: false` agent -> 404. Public get also 404s if the owner has no public profile.

## Deviations / questions
- PublicListing also omits `agent_id` and `fingerprint` (contract only lists visibility/freshness); it keeps `status` so the UI can flag under_offer.
- Timestamps use naive `datetime.utcnow` (same as the other modules); serialised as ISO without a `Z`. Integrator may want a tz-aware convention.
- Drafts may be sparse (all fields optional on create); PATCH rejects `null` for title/description/media/amenities/visibility and unknown fields (422).
- Indexes for the integrator: `listings(agent_id, created_at)`, `listings(agent_id, status, visibility, published_at)`, `listings(fingerprint)`.
- Not implemented (later): the 30-day auto-expire job; duplicate detection using the fingerprint.
