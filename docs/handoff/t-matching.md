# Handoff: stream T (reverse matching, performance, recommended actions)

Branch `v2/t-matching`. Implements marketing.md sections 2-4 in `backend/app/modules/tracking`. No router.py / config / fakes.py changes.

## Routes (all on the existing `/inbox` mount, agent auth)
- `GET /inbox/matching-leads?listing_id=` -> `reverse.py`. 404 for unknown or other agents' listings; 422 without listing_id.
- `GET /inbox/performance` -> `performance.py`.
- `GET /inbox/today` -> now also returns `actions` (`actions.py`); all previous fields unchanged.

## Behaviour notes / decisions
- Reverse matching reuses `matching.match_listing` (extracted `matching.match_context` for transaction/type inference, shared with lead -> listing). Buyers need at least one requirement signal (bhk, budget or locality); >= 60 only, max 10, sorted by match_pct, score, id.
- Non-live listings (draft etc.) return `buyers: []` (contract silent). under_offer counts as live, as elsewhere.
- Draft: "Hi {first}, I have {label} at {price}; it fits your {budget} budget. Details: {url}". The budget clause appears only when `followup.fits_budget` is true. Link uses `settings.public_site_url` + slug from `agent_public_profiles`; with no slug, `share_url` is null and the link is omitted.
- Performance: includes all of the agent's listings (drafts too, zeros when idle). `qualified` = warm/hot by decayed score, OR any budget bound, OR a timeline on the stored requirement. Site-visit stages: site_visit, negotiating, won. Lost leads still count as enquiries.
- Limits (Python aggregation): 500 listings, 5000 leads, 50000 most recent listing_view events per agent. Beyond that, views/unique visitors cover only the newest events. If volumes grow, move to a Mongo `$group` pipeline.
- Actions: call = hot and stage new (priority 1); follow_up = overdue and open (1; a lead already getting a `call` is not duplicated); send_property = status `live` listing with `created_at` in the last 3 days and >= 1 buyer (2); create_marketing = status `live` listing with no `marketing_packs` doc (3). Sorted by priority then recency (lead last activity / listing created_at, newest first), max 6. A missing or empty `marketing_packs` collection means "no pack", so agents see create_marketing actions until the marketing stream ships packs.
- Existing test `test_qualification_router.py::test_today_endpoint` updated: the key set of `/today` now includes `actions`.

## Tests
New: `test_matching_reverse.py`, `test_matching_reverse_router.py`, `test_performance.py`, `test_tracking_actions.py`, helper `reverse_helpers.py`. Full suite: 276 passed.
