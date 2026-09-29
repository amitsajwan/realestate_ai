# Handoff: C2 listing activity page and freshness prompts (Sprint 6)

Branch `v2/c2-activity`. Coded to `docs/contracts/activity.md` sections 1 and 2 (frozen, untouched). Section 3 (inquiry abuse
protection) is backend and public-site only; nothing to do in the agent app.

## What was added

- **Client** (`lib/app/api.ts`, `types.ts`): `getListingActivity(id, limit?)` -> `GET /inbox/listings/{id}/activity[?limit=]`,
  `confirmAvailable(id)` -> `POST /listings/{id}/confirm-available`. `Listing` gains optional `freshness` and
  `days_since_confirmed` (an older backend that omits them is treated as "fresh", so nothing is asked). Types
  `ListingActivity`, `ActivityFeedItem`, `ActivityPerson`, `Freshness`. `ListingInput` omits the two computed fields.
  `RecommendedActionType` gains `confirm_listing`.
- **Fixtures** (`fixtures.ts`, new `fixtures-activity.ts`): both methods implemented. Storage key bumped to
  `app_fixture_state_v6`. Seed listings: l1 fresh, l3 "confirm" (30 days), l4 "hidden" (52 days), l5 fresh, l2 draft.
  Freshness is computed on read with the contract's rule (<21 fresh, 21..44 confirm, >=45 hidden; only live / under offer).
  `confirmAvailable` is 409 unless live/under offer; reactivating from paused/expired re-stamps freshness. Activity is
  derived from the same data as `getPerformance` (totals match), with a zero-filled 14-day IST series, sources, "Visitor N"
  feed entries mixed with named buyers, and people hottest first.
- **Activity screen** `/studio/listings/[id]/activity` (`app/studio/listings/[id]/activity/page.tsx`,
  `components/app/ListingActivityView.tsx`): header (title, price, status), six tiles plus a secondary row (WhatsApp taps,
  Calls, Shares), 14-day bar chart in plain SVG (views bars, amber dot on days with enquiries, axis dates, text summary
  used as the SVG `aria-label` and shown below), "Where they came from", "Interested people" (tap opens the lead),
  "Recent activity" (named buyers link to the lead, anonymous visitors do not). Empty state leads with a share-the-link card.
- **Entry points**: "Activity" button on every non-draft `ListingCard` (a sibling of the card link, not nested inside it)
  and on the listing detail screen.
- **Freshness UX** (`components/app/FreshnessPrompt.tsx`, `lib/app/freshness.ts`): `FreshnessSection` renders a card per listing
  that needs an answer, hidden ones first. "Is this still available?" (amber) for `confirm`, red "Hidden from buyers until
  you confirm" for `hidden`, same three big buttons: Yes, still available (`confirmAvailable`), It is sold / It is rented
  (`setListingStatus` sold / rented), Pause it (`paused`). Shown at the top of the Listings screen and the listing detail
  screen; the card and chip update from the returned listing and a green status line confirms what happened. Listing cards
  show a small "Confirm" (amber) or "Hidden" (red) chip.
- **Home**: a client-side `confirm_listing` item ("Listings that need your confirmation") is added to "AI recommends"
  from `listListings()` unless the backend already sent one. Priority 1 when any listing is hidden, else 2. One listing
  links to `/studio/listings/{id}`; several link to `/studio/listings#confirm` (the Listings screen scrolls to the cards).
  If listings cannot be loaded, home works as before.
- Helpers: `lib/app/activity.ts` (relative time, chart scaling, summary text, axis labels, source rows, IST date key),
  `lib/app/freshness.ts`. All strings are in `lib/app/strings.ts` (keys `act*`, `fresh*`).

## Notes for the backend / integration

- The detail screen strips `freshness` and `days_since_confirmed` before PATCH; the server should still ignore them.
- The activity page requests `limit=50`. Feed rows with `who.kind === "lead"` and a `lead_id` link to `/studio/leads/{id}`.
- The empty state is shown when totals views and enquiries are 0 and the feed is empty. Missing `people` / `feed` arrays
  are tolerated.
- Home makes one extra `GET /listings?limit=100` call (failure is ignored).

## Tests

`__tests__/app/activity-api.test.ts` (client + fixtures), `activity-helpers.test.ts` (relative time, chart scaling,
freshness rules, confirm action), `activity-ui.test.tsx` (tiles, chart summary, sources, people, feed, empty state,
entry points), `freshness-ui.test.tsx` (each button, hidden state, older backend, detail screen, home action).
Existing tests updated only for the storage key (`app_fixture_state_v6`).
