# Handoff: F-social (Sprint 5 frontend, "Post to PUNE Property")

Branch `v2/f-social`, built against `docs/contracts/social.md` (frozen). Never pushed.

## What was built
- Marketing pack screen (after posting, and `/studio/listings/[id]/marketing`): new section **Post to PUNE Property**, above the disabled
  "Publish everywhere / Coming soon" block. That block is kept; its intro (`publishNote`) now says it is about connecting the agent's OWN
  accounts later. No route changes were needed: the section lives inside `MarketingPackView`.
- `components/app/SocialPublishSection.tsx`: explanation, channel checkboxes (Facebook Page, Instagram), required consent checkbox with the
  exact contract text, primary button. The button is disabled until at least one channel and the consent are chosen. The request is sent only
  on the button tap; nothing is sent on load.
- Test mode: banner "Test mode: nothing is posted publicly." and button "Approve and test post" when `status.dry_run` is true.
- A channel not configured in `GET /social/status` is disabled with "Not set up yet".
- After posting: per-channel result rows (Posted / Test post / Failed / Queued chips), permalink link, friendly failure text (raw text kept
  under "Details") with "Try again" (retry). Channels and consent reset after each post (approval is per post).
- History: `GET publications` list (newest first, as given by the API) under "Earlier posts", excluding rows already shown as results.
- Already-posted (published or dry_run, same `pack_version`) channels show "Done", are disabled, and have "Post again", which selects the
  channel and sends `force: true`. A failed post or an older pack version is not "done".
- 409 on publish: friendly message ("cannot be posted yet", or "already posted" when the detail says so). 422 is never sent by the UI.

## Client and fixtures
- `lib/app/types.ts`: `Publication`, `SocialStatus`, `SocialChannel`, `PublicationStatus`, `SocialPublishRequest`; four new `AppApi` methods.
- `lib/app/api.ts`: `getSocialStatus` (GET /social/status), `publishToSocial(listingId, {channels, approve, consent, force})`
  (POST /social/listings/{id}/publish, always sends `force`, unwraps `publications`), `listPublications` (unwraps `items`),
  `retryPublication` (POST /social/publications/{id}/retry). All under `/api/v1`, bearer auth.
- `lib/app/fixtures.ts` + `fixtures-social.ts`: status with `dry_run: true` and both channels configured; publish records `dry_run`
  publications with a payload snapshot (404 unknown listing, 409 no pack / not live / already posted without force, 422 without
  approve+consent); list newest first; retry only for failed. Storage key bumped to `app_fixture_state_v5` (exported as
  `FIXTURE_STATE_KEY`). Fixtures never produce failures on their own; tests seed one through storage.
- `lib/app/social.ts`: pure labels, done-channel logic, friendly error mapping. All UI strings are in `lib/app/strings.ts` (`social*`).

## Tests (`frontend/__tests__/app`)
`social-api.test.ts`, `social-fixtures.test.ts`, `social-ui.test.tsx` (new); `marketing-screen.test.tsx` mock extended;
`outcomes-fixtures` / `qualification-fixtures` updated for the v5 storage key.

## Notes for the integrator
- Real backend behaviour assumed from the contract: a failed channel is a normal 200 with a `failed` publication (shown with Try again).
- The UI disables a channel that `GET /social/status` reports as not configured, even in dry-run mode (where the backend would accept it).
- The dry-run banner has no `role="status"` on purpose (an existing test looks up a single status region on the pack screen).
