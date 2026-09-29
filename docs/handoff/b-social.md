# Handoff: B (social publishing backend, Sprint 5)

Branch `v2/b-social`. Implements docs/contracts/social.md exactly (contract untouched).

## What shipped (backend/app/modules/social/)
- `config.py`: `SocialConfig` read from `os.environ` at call time (`load()`); `SOCIAL_DRY_RUN` defaults to true (only an explicit false/0/no/off disables it);
  token field has `repr=False`. `META_GRAPH_VERSION` is validated (`vNN.N`), else v23.0.
- `publisher.py`: `Publisher` protocol, `DryRunPublisher` (fake `dryrun_...` id, no network), `sanitize()` (strips the configured token, `access_token=`/`token=`
  values, JSON `"access_token"`, `Bearer/OAuth <long token>`, `EA...` tokens; collapses whitespace; truncates to 300 chars), `PublishError`.
- `graph.py`: `GraphPublisher` (injectable httpx `transport`, `sleep`, `clock`). Facebook photo (`POST /{page}/photos` url/caption/published=true) or feed
  (`POST /{page}/feed` message/link); Instagram single image or carousel (item containers, carousel container, poll `GET /{container}?fields=status_code`
  every 2 s up to 60 s, ERROR/EXPIRED/timeout -> failed, then `media_publish`, best-effort permalink). Only https media urls are ever sent (refused again inside the publisher).
- `service.py`: approve+consent (422), owner scoping (404), live/under_offer + pack (409), Instagram needs an image (400), idempotency per
  listing+channel+pack_version (409 unless `force`), publication records with attempts/payload snapshot/consent, sanitized failures, retry (failed only).
- `schemas.py`, `router.py`: `GET /status`, `POST /listings/{id}/publish`, `GET /listings/{id}/publications`, `POST /publications/{id}/retry`.

## Integrator: mount line
```python
from app.modules.social.router import router as social_router
api_router.include_router(social_router, prefix="/social", tags=["social"])
```
No settings changes are needed: config is read straight from the environment (add the vars to `.env.example` / deployment if desired).

## Env vars
`SOCIAL_DRY_RUN` (default true), `META_GRAPH_VERSION` (default v23.0), `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN`, `META_IG_BUSINESS_ID`,
`PUBLIC_MEDIA_BASE_URL` (https, public; pack image paths from `/uploads/...` are re-based onto it).

## Behaviour notes / small deviations
- Publish again after a `failed` attempt (same listing/channel/pack_version, no `force`) re-attempts that same record (attempts+1, fresh consent) instead of adding a
  duplicate row. `force: true` always creates a new record. A `queued` record younger than 2 minutes counts as an in-flight duplicate (409); older ones do not block.
- Retry additionally returns 409 if the listing is no longer live/under_offer, or if the same listing/channel/pack_version was already published in the meantime.
- Validation happens for all channels before anything is posted: one duplicate (409) or an Instagram pack without images (400) aborts the whole request with nothing recorded.
- The stored payload snapshot carries one extra internal key `link` (used for the Facebook feed post on retry); it is not returned (response payload is exactly `{text, image_urls}`).
- The token is sent as the `access_token` request parameter (form body for POST, query for GET), the widely used Graph form, not as an Authorization header.
  Every stored/returned/logged error passes through `sanitize()`; only the sanitized error text is logged (info line per attempt).
- In dry run the payload image urls are re-based if `PUBLIC_MEDIA_BASE_URL` is set, else left as `/uploads/...` paths.
- The publisher for an unknown/unexpected exception records only the exception type name, never its text.
- Item containers of a carousel are not polled individually, only the carousel container (per contract); the carousel is capped at 10 images.

## Not verified without a real Meta token
Everything is tested against `httpx.MockTransport`; nothing has run against graph.facebook.com. Unverified: that the Page token has `pages_manage_posts`,
`instagram_content_publish` etc.; real Graph error shapes/rate limits; that Instagram accepts the carousel when item containers are not polled first
(if Meta returns "media not ready" add per-item polling in `_instagram`); that Meta can fetch the tunnel-hosted `/uploads` images (size/type limits: JPEG, < 8 MB);
the exact `permalink_url`/`link` fields for Page photos; the Facebook `post_id` -> `facebook.com/{post_id}` permalink form.

## Tests
`backend/tests/modules/test_social_{service,graph,router}.py` + `test_social_helpers.py` (fixtures, no tests). Full suite: 434 passed, 2 skipped.
