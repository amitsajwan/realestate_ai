# C1 handoff: listing activity, freshness, inquiry abuse protection (Sprint 6)

Contract: `docs/contracts/activity.md` (frozen, implemented as written). Branch `v2/c1-activity`.

## What was built

### 1. Listing activity: `GET /api/v1/inbox/listings/{listing_id}/activity?limit=50`
- Code: `backend/app/modules/tracking/activity.py`, route in `tracking/router.py`, `TrackingService.listing_activity`.
- Counting rules are shared with `GET /inbox/performance`: `performance.py` now exposes `blank_counts`, `tally_enquiry`
  and `tally_deal` (the old inline code was replaced by them; performance output is unchanged, its tests are untouched).
  Deals use `outcomes.attributed_listing`, so a won deal counts for the listing it was closed on.
- `feed` covers listing_view, whatsapp_click, call_click, share and inquiry events (mapped to `enquiry`), newest first.
  `limit` is 1..100 (422 outside that range, default 50).
- Privacy: visitors are "Visitor N", numbered by first appearance over all fetched events (so numbers do not shift with
  `limit`). An event whose `contact_id` (or whose anon id, via the lead's `anon_ids`) belongs to a lead shows the lead's
  name with `kind: "lead"` and `lead_id`. Events with no anon id are labelled "A visitor". Anon ids, IPs and user agents are
  never in the response (tested).
- `daily`: 14 India (IST) dates ending today, oldest first, zero filled. Views bucket by event time, enquiries by the lead's
  `created_at`. Events older than the window are ignored in the series (but still count in totals).
- `people`: leads who enquired on this listing (first_listing_id) or have an event on it, hottest first (score desc, then most
  recent activity), max 10.
- Other agent's / unknown listing: 404. Empty listing: zero totals, `{}` by_source, 14 zero days, empty feed and people.

**Limits (bounded queries):** the newest `MAX_EVENTS = 5000` events of the listing (all five types together) and the agent's
`MAX_CONTACTS = 5000` leads (same cap as performance). A listing with more than 5000 events reports totals for the newest
5000 (views, unique visitors, clicks, feed and daily all derive from the same set). Counts of enquiries, qualified,
site_visits and deals come from leads, not events, so they are not affected by the event cap. The `events` index
(`agent_id, type, listing_id`) serves the query filter; a `(agent_id, listing_id, ts)` index would serve the sort better
if activity pages get slow (indexes live in `app/core/indexes.py`, not in this owner's scope).

### 2. Freshness
- Code: `backend/app/modules/listings/freshness.py` (pure rules), `schemas.py` (`Listing.freshness`,
  `Listing.days_since_confirmed`), `service.py`, `router.py`.
- Computed on every agent-side read/write response (`GET /listings`, `GET /listings/{id}`, PATCH, publish, status,
  confirm-available); never stored, not on `PublicListing`. Uses the service's injectable `now`.
- Age in whole days from `freshness_confirmed_at`, else `published_at`, else `created_at`: `<21` fresh, `21..44` confirm,
  `>=45` hidden (tested at exactly 21 and 45 days and one second before). Only `live` / `under_offer` can be confirm/hidden;
  all other statuses return `fresh` and `days_since_confirmed: null`.
- `POST /listings/{id}/confirm-available`: owner only (404 otherwise), 409 unless live/under_offer, sets
  `freshness_confirmed_at` and `updated_at` to now, returns the Listing. Editing (PATCH) does not confirm.
- Public reads (`GET /public/agents/{slug}/listings`, `GET /public/listings/{id}`) exclude hidden listings (404 for a single
  one). `public_list` now pages in Python over the agent's newest `MAX_PUBLIC = 500` public listings (instead of
  Mongo skip/limit) because the hidden check needs the fallback chain; `total` counts only visible listings.
- **Hidden listings still have `status: "live"`** in the database and on the agent side. Marketing and social modules read the
  listing straight from the collection and check the status only, so they are NOT blocked for hidden listings by this change
  (as instructed, those modules were not touched). If the product wants them blocked, marketing/social must read
  `freshness` (import `app.modules.listings.freshness.is_hidden`).

### 3. Inquiry abuse protection: `POST /api/v1/t/inquiry`
- Code: `tracking/limits.py`, `TrackingService.capture_inquiry`, optional `website` on `InquiryIn`.
- Honeypot: a non-blank `website` returns `{received: true, new_lead: false}` immediately, before consent, agent lookup or any
  write. Nothing is stored (no contact, event or log row) and it never counts toward the limits.
- Limits use a small `inquiry_log` collection (`{agent_id, phone, anon_id, ts}`), one row per accepted attempt, written
  before the lead is created/updated, so an inquiry that only updates an existing lead is counted too. Windows are rolling:
  a row exactly one hour old no longer counts. Per (agent, phone): 3; per anon_id: 5. Over the limit: HTTP 429,
  detail "Too many messages. Please try again later". Rejected attempts (and inquiries refused for missing consent) are not
  logged, so nothing is extended by hammering.
- Deployment note: `inquiry_log` has no index and no cleanup. Suggested (outside this owner's files): index
  `(agent_id, phone, ts)` and `(anon_id, ts)`, and a TTL index on `ts` (e.g. `expireAfterSeconds: 86400`).

## Tests
New: `test_activity.py`, `test_activity_router.py`, `test_freshness.py`, `test_inquiry_limits.py`, helper
`activity_helpers.py`. No existing test needed changing (all 458 previous tests pass unchanged).
