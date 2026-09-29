# Contract: deal outcomes (Sprint 4, frozen)

Purpose: learn what actually closes. When an agent marks a buyer Won or Lost, capture the result (price, which property,
why lost). Results then feed property performance, "this month" on the home screen and, later, what to recommend.
Everything is optional-first: marking Won with no price still works.

## PATCH /api/v1/inbox/leads/{id}   (extends the existing body)
```
{ stage?, note?, follow_up_at?,                                   existing
  outcome?: { deal_price_inr?: integer > 0,                        stage "won" only
              listing_id?: string,                                 stage "won" only; defaults to the lead's first_listing_id;
                                                                   must be one of the agent's own listings (else 422)
              lost_reason?: "price" | "bought_elsewhere" | "not_responding" | "changed_mind" | "other" }   stage "lost" only
}
```
- `outcome` is only accepted together with `stage` = won or lost (422 otherwise; won fields with lost and vice versa -> 422).
- Won: stored `outcome = { result: "won", deal_price_inr | null, listing_id | null, closed_at }`. If `deal_price_inr` is omitted and a listing is known
  it stays null (the UI pre-fills the listing price; the API never guesses).
- Lost: stored `outcome = { result: "lost", lost_reason | null, closed_at }`.
- Moving a lead OUT of won/lost (to any other stage) clears its outcome. Marking won/lost without `outcome` stores `{result, closed_at}` only.
- Response = the lead detail (below) plus, when the lead was marked won with a listing: `suggest_listing_status: { listing_id, status: "sold" | "rented" }`
  ("rented" when the listing's transaction is rent). The API never changes the listing itself; the app offers to call the existing
  POST /listings/{id}/status.

## Lead detail and list items gain
`outcome: { result, deal_price_inr, listing_id, lost_reason, closed_at } | null`

## Performance (GET /inbox/performance) items gain
`deals` (won leads attributed to the listing: outcome.listing_id, else first_listing_id), `deal_value_inr` (sum of deal_price_inr, nulls ignored),
`deals_by_source: { <source>: count }`.

## Results (GET /api/v1/inbox/today gains `results`)
```
results: { period_days: 30, deals_won, deal_value_inr, deals_lost, top_source: string | null,
           lost_reasons: { <reason>: count } }        // won/lost closed within the last 30 days (closed_at)
```
`top_source` = the source with the most won deals in the period (ties: alphabetical), null when none.

## Ownership (Sprint 4)
- Backend: backend/app/modules/tracking/** and tests (integrator)
- F  frontend/components/app/**, frontend/lib/app/**, frontend/app/studio/**, frontend/__tests__/app/**
