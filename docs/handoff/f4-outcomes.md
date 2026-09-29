# F4 handoff: deal outcomes (frontend)

Codes to `docs/contracts/outcomes.md` (frozen). Fixture mode implements the whole contract, so the app works with no backend.

## What changed

- `lib/app/types.ts`: `LostReason`, `LeadOutcome`, `OutcomeInput`; `LeadPatch.outcome`; `outcome` on `Lead`/`LeadDetail`;
  `LeadDetail.suggest_listing_status` (PATCH response only); `BusinessToday.results` (`TodayResults`);
  `deals`, `deal_value_inr`, `deals_by_source` on `PerformanceItem`. All new response fields are optional so an older backend still works.
- `lib/app/outcomes.ts` (new): `outcomePatchError` (the contract's 422 rules), `outcomeSummary`, `lostHint`, `resultsEmpty`, `dealListings`, `LOST_REASONS`.
- `lib/app/api.ts`: `updateLead` refuses locally (ApiError 422, no request) an `outcome` without stage won/lost, won fields with lost,
  `lost_reason` with won, a non-integer or non-positive price, or an unknown reason. Every existing call shape sends the same body as before.
- `lib/app/fixtures.ts` + `fixtures-outcomes.ts` (new): outcome stored on won/lost, cleared when leaving won/lost, listing defaults to
  `first_listing_id`, price never guessed, unknown listing -> 422, `suggest_listing_status` (`rented` for rent listings; the listing itself is never changed),
  `results` on `getToday` (30 days by `closed_at`, `top_source` ties alphabetical), deals fields on performance rows.
  Storage key bumped to `app_fixture_state_v4` (the one existing test that seeds the old key was updated).
- `components/app/OutcomeSheets.tsx` (new): `BottomSheet`, `DealClosedSheet`, `LostReasonSheet`, `MarkSoldPrompt`, `OutcomeSummary`, `OutcomeBadge`.
- `LeadDetailView`: Won opens "Deal closed" (price pre-filled from the enquired listing and editable, property select, both optional),
  Lost opens "Why was it lost?" (reason chips, Skip). Dismissing (backdrop or Escape) applies nothing. After a Won with a listing and
  `suggest_listing_status`, "Mark {listing} as sold/rented?" with Yes (calls `setListingStatus`) or Not now. Stored outcome shows as a summary card with Reopen
  (moves the lead to Contacted; the API clears the outcome).
- `app/studio/leads/page.tsx`: Won/Lost badge on lead cards.
- `BusinessToday`: `ResultsCard` ("This month": deals won, deal value, "Best channel: X", "Most lost on price"); hidden when there are no
  won or lost deals or when `results` is absent.
- `ListingCard`: `DealsLine` ("2 deals · ₹1.72 Cr") when `deals > 0`.
- All copy is in `lib/app/strings.ts`.

## Behaviour worth knowing

- Saving a note no longer sends the current stage (it used to send `{stage, note}`); it sends `{note}` only. Otherwise a note on a won lead
  would be a "mark won without outcome" and could wipe the stored deal.
- The Won sheet sends `outcome` only when a price or a property is chosen; with both empty it sends just `{stage: 'won'}`.
- The Lost sheet saves on tapping a reason (one tap); Skip sends `{stage: 'lost'}`.
- The mark-sold prompt is skipped when the loaded listing is already in the suggested state.
- Picker lists live, under offer, sold and rented listings, plus the lead's first listing whatever its status.
- Deal price uses the existing `parseInr`/`formatInr` ("85 lakh", "1.2cr", "₹85,00,000", bare rupees). The field shows what it understood ("= ₹85 L").
- Home "best channel" uses `sourceLabel` on `results.top_source`.

## Tests

`__tests__/app/outcomes-api.test.ts`, `outcomes-fixtures.test.ts`, `outcomes-ui.test.tsx` (sheets, prefill, optional fields, dismiss, parsing, mark-sold Yes/Not now,
summary and undo, list badge, home card, listing card deals).
Run: `cd frontend && npx tsc --noEmit && npx jest --testMatch "**/__tests__/app/**/*.test.{ts,tsx}"`.

## For the integrator

- Won sends `outcome.listing_id` only when the agent picked one (the select defaults to the lead's first listing, so normally it is sent).
  The API should still default a missing `listing_id` to `first_listing_id` as the contract says.
- The client sends no `outcome` at all for Skip / empty sheets, so "won/lost without outcome" must store `{result, closed_at}` as in the contract.
