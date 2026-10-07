# S3 handoff: public agent site

Branch `v2/s3-site`. Replaces the old client-rendered `frontend/app/agent/[agentName]/*` tree.

## Routes (all React Server Components, `generateMetadata`, JSON-LD)
- `/agent/<slug>`: hero (name, tagline, photo, city, WhatsApp/Call), listings grid with Buy/Rent + BHK filters (client-side), about, contact + enquiry form. Emits `page_view`.
- `/agent/<slug>/listings/<id>`: swipe gallery, price (lakh/crore), key facts, amenities, EN/HI/MR description switch (only languages present), share (`navigator.share`, copy fallback, `?src=share`), sticky mobile bar (WhatsApp/Call/Enquire), enquiry form with listing id. Emits `listing_view`.
- `app/agent/[slug]/not-found.tsx`: 404 for unknown slug/listing (a listing under another agent's slug also 404s).
- Removed: `/agent/<x>/contact`, `/posts`, `/posts/<id>`, `/properties`, `/properties/<id>`. Anything else linking to them (dashboard "view site" links etc.) must use `agentPath()` from `lib/site/slug.ts`.

## Code map
- `lib/site/`: `api.ts` (server fetch, fixtures fallback), `fixtures.ts`, `format.ts`, `phone.ts`, `slug.ts` (slug + host resolution, `agentPath`), `theme.ts` (CSS vars), `seo.ts`, `links.ts` (wa.me/tel/share url), `tracking.ts` (client).
- `components/site/`: `SiteShell` (theme vars on server-rendered wrapper), `Hero`, `ListingBrowser`, `ListingCard`, `Gallery`, `ListingFacts`, `DescriptionSwitch`, `ShareButton`, `StickyBar`, `ContactButtons`, `TrackedLink`, `TrackingBeacon`, `EnquiryForm`.
- Tests: `frontend/__tests__/site/*` (32 tests).

## Env vars
- `SITE_API_URL` (server-only, absolute, e.g. `http://backend:8000`): falls back to `NEXT_PUBLIC_API_URL`, then `http://localhost:8000`. The relative `''` from `lib/config/api.ts` is not usable server-side.
- Client beacons/inquiry use `API_BASE_URL` from `lib/config/api.ts` (relative when empty, so it needs the nginx proxy or `NEXT_PUBLIC_API_URL`).
- `NEXT_PUBLIC_SITE_URL`: public origin used for canonical/OG/share URLs (default `http://localhost:3000`). Must be set in real environments.
- `SITE_USE_FIXTURES=1`: serve fixtures. Slugs `priya-deshmukh-pune` and `demo` exist; all others 404. In non-production the site also falls back to fixtures when the API is unreachable (not on 404s).

## Data contract used
- `GET /api/v1/agent/public/{slug}` (agent_name, slug, bio, photo, phone, languages, specialties, office_address, branding_data{tagline, colors}). No `city` in the real shape, so the hero city is taken from the first listing (or `agent.city` if it ever exists).
- `GET /api/v1/public/agents/{slug}/listings?limit=60`, `GET /api/v1/public/listings/{id}` per contract (revalidate 30s).
- `POST /api/v1/t/event`, `POST /api/v1/t/inquiry` per tracking schemas. Inquiry phone is sent as normalized 10 digits.

## Verification
- `tsc --noEmit`: no errors in S3 files. 76 pre-existing errors elsewhere; 3 old tests (`__tests__/unit/pages/agent_posts|agent_properties|property_detail.test.tsx`) import the deleted `[agentName]` pages and now fail. They are outside S3 ownership: integrator should delete them.
- `jest`: 32/32 pass. On Windows worktree paths containing `\.claude` the configured `testMatch` matches nothing (micromatch escape); run `npx jest --testMatch "**/__tests__/site/*.test.{ts,tsx}"`.
- `next lint` is broken repo-wide (eslint option mismatch), not run.
- `next build`: compiles, then fails type-check on pre-existing `components/property/shared/PropertyImageUpload.tsx` (`uploadImages`). Dev server smoke test with fixtures: both pages 200, OG image + JSON-LD + theme vars present, unknown slug/listing 404.

## Gaps / notes
- Images are plain `<img loading=lazy width height>` because `next.config.js` has `images.unoptimized`, no remote patterns. Root layout still wraps pages in global `Navigation`/`main` (Navigation hides itself on `/agent/*`).
- No sitemap (skipped). No video media rendering. Filters are client-side only (no query params). Tracking `src` is remembered per tab session so later clicks/enquiry keep attribution.
- Contact section shows buttons only if the agent phone is a valid Indian mobile.

## Host-based routing plan
Pages already resolve slugs via `normalizeSlug` and build links via `agentPath`. Add `frontend/middleware.ts`: read `Host`, call `slugFromHost(host, NEXT_PUBLIC_ROOT_DOMAIN)` (implemented, tested) and `NextResponse.rewrite('/agent/<slug><path>')`; for custom domains look up host -> slug via a backend endpoint. Then make `agentPath` return the path without the `/agent/<slug>` prefix when serving on an agent host, and set `NEXT_PUBLIC_SITE_URL`-derived canonical to the agent host. Needs wildcard DNS + TLS.
