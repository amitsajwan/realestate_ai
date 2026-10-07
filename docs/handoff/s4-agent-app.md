# Handoff: S4 Agent app (mobile web)

Branch `v2/s4-agent-app`. Phone-first agent app: sign up, post a listing by typing or speaking, work leads.

## Routes
| Route | What |
|---|---|
| `/join` | phone -> OTP (30s resend, dev-code hint + autofill) -> name/city/languages/specialties -> "Your website is live" (WhatsApp share, copy, add first listing). Existing users with a site go straight to `/studio`. |
| `/studio` | greeting, big "+ Add listing", my-site card (open/share), stats (live/total listings, leads by temperature) |
| `/studio/listings` | my listings with status chips |
| `/studio/listings/[id]` | edit (PATCH), publish (with an explicit confirm), status actions (under offer / sold / rented / pause / make live), share link |
| `/studio/listings/new` | capture (text + mic + photos) -> AI draft -> review (low confidence highlighted, missing fields block publish, warnings, lakh/crore price, EN/HI/MR tabs) -> "Confirm & post" -> success + WhatsApp share |
| `/studio/leads`, `/studio/leads/[id]` | inbox hottest first with stage filter; detail with Call (tel:), WhatsApp (wa.me), stage change + note, activity timeline |

Code: `lib/app/` (types, api, client, fixtures, session, format, validate, leads, share, strings, hooks), `components/app/`, tests in `__tests__/app/`.

## Fixture mode
`NEXT_PUBLIC_APP_FIXTURES=1`, or `localStorage app_fixtures=1`, or automatic in development when the OTP request fails with a network/5xx error. `lib/app/fixtures.ts` implements the same `AppApi` interface (state in localStorage). Demo OTP is `123456`. The fake AI draft is a small regex parser (BHK, price, known Pune/Mumbai localities) that deliberately yields some low-confidence and missing fields. Fixture photos are downscaled to data URLs.

## Contract notes and API gaps found
- **Photo upload**: no listing-scoped upload exists. The client uses the legacy `POST /api/v1/uploads/images` (multipart field `files`, max 20, JPEG/PNG/WebP/GIF, 10 MB each, rate limit 10/min) and reads `files[].url`. Gaps: (1) it silently skips files it cannot process, so the client fails if fewer URLs come back than files sent; (2) `url` is built from `request.base_url`, so behind the Next proxy it may be `http://localhost:8000/...` (absolute, not portable); (3) `uploaded_at` is hard-coded; (4) no HEIC support (iPhone camera default), no video. Recommend a proper `/listings/{id}/media` endpoint.
- **AI draft images**: the contract says `images[]` multipart, the task said `image_count`. The client sends `text`, `audio` (`voice.webm`) and `image_count` only, never the image bytes (photos are uploaded separately at confirm time). The ai_listing module must accept that.
- **422 shape on publish** is not specified. `parseErrorBody` accepts `{detail:{missing:[..]}}`, `{detail:[..names..]}`, `{missing:[..]}` and FastAPI `[{loc,msg}]`. Field names follow the contract, `description.en` for the English description and `media` for photos.
- **Route order**: `POST /listings/ai/draft` must be registered before any `/listings/{id}` route.
- `GET /listings` is assumed to return `{items}`; inbox returns `{leads}` (matches built module). Inbox lead has no listing title, so screens join `first_listing_id` and timeline `listing_id` against `GET /listings`. Timeline event `type` also includes `inquiry`.
- "Make live" from paused/expired uses `POST /status {status:'live'}`; the contract does not list resume transitions explicitly.
- Publishing is only reachable from an explicit "Confirm & post" (new) or a two-step confirm (detail). The flow never auto-publishes. A failed publish keeps the created draft id and retries via PATCH (no duplicates).

## Deviations and things to know
- The root `layout.tsx` renders the legacy `Navigation`; `/studio` and `/join` sit in a `fixed inset-0 z-50` overlay to own the viewport. Long term a route-group layout would be cleaner (needs a shared-file change).
- Jest: the repo's `testMatch` glob does not match files under a dot-directory (this worktree lives in `.claude/worktrees`), so I ran tests with a wrapper config in a temp dir (`testRegex` for `__tests__/app`). In a normal checkout `npx jest __tests__/app` works.
- `next build` compiles our code but fails at type-check on a pre-existing legacy error (`components/property/shared/PropertyImageUpload.tsx`: `uploadImages` missing on `CentralizedAPIClient`). Not touched. `next dev` renders all four main routes with 200 in fixture mode.
- Hindi strings exist for a handful of labels; Marathi table is empty (falls back to English).

## Next steps
Real-backend pass once S1/S2 land (verify 422 shape, upload URLs); listing photo reorder/delete on the detail page; installable PWA manifest/service worker (needs a shared-file change); lead reply templates; Hindi/Marathi copy review; e2e (Playwright) against fixture mode.
