# Handoff S5 (stream B): buyer qualification, matching, follow-ups, "today"

Implements sections 1-5 of `docs/contracts/qualification.md` in `backend/app/modules/tracking/`. No new dependencies,
no LLM needed anywhere (an optional polish hook exists). `app/api/v1/router.py` untouched (existing `/t` and `/inbox` mounts).

## Shipped
- `requirement.py` Requirement model (bhk 0.5-10, budget min<=max, enums), message parser (budget `80-90L`, `under 1 crore`,
  `85 lakh`, `1.2cr`, `Rs 85,00,000`, Devanagari lakh/crore; BHK digits and Hinglish words `do/teen/ek bhk`; timeline;
  financing), provenance-aware merge, formatting (`80L-1.2Cr`, `requirement_line`).
- `matching.py` transparent scoring: type 10, BHK 25, budget 40, locality 25. Unstated dimension earns half credit and
  lists no reason. Budget: inside range = full, within 10% above (or below) = half. Only live/under_offer listings of the
  lead's own agent, >= 40, top 3, ties cheaper first. No match at all when the buyer stated no bhk/budget/locality.
- `summary.py` deterministic `ai_summary` + `next_action`. `followup.py` drafts (en, plus simple hi/mr templates),
  `wa.me` URL, `based_on`, `polish_safely`. `today.py` for `/inbox/today`.

## Endpoints
- `POST /t/inquiry` new optional `bhk, budget_min_inr, budget_max_inr, timeline, financing`; response unchanged.
- `GET /inbox/leads` items gain `requirement_line`; `GET /inbox/leads/{id}` gains `requirement, ai_summary, next_action,
  matches, follow_up{due_at, overdue}` (also `requirement_line`).
- `PATCH /inbox/leads/{id}` body `{stage?, note?, follow_up_at?}` (at least one required, else 422). Moving to `contacted`
  sets `follow_up_due_at = now + 2 days` unless `follow_up_at` is given.
- `POST /inbox/leads/{id}/followup-draft` `{language?: en|hi|mr}` (body optional) -> `{message, whatsapp_url, language, based_on}`.
- `GET /inbox/today` -> `{counts, hot_buyers (max 5), follow_ups (max 10, oldest due first), headline}`.

## Storage
`contacts.requirement` = fields + `field_sources` (per field: stated | inferred | default); the API returns the contract
shape with a derived `source`. Also `follow_up_due_at`, `contacted_at`. Rules: stated beats inferred beats listing default;
newer of equal rank wins; budget min/max move as a pair; localities are unioned (max 5).

## Deviations / decisions
- `next_action` has an extra first rule: won/lost leads get `follow_up` ("Deal closed" / "Marked as lost") instead of
  chasing. Otherwise the contract order is followed.
- Requirement has no transaction field: matching uses the enquired listing's transaction and property type, else
  "rent" when the message says rent/kiraya, else sale.
- A plain enquiry on a listing stores a requirement made of listing defaults (locality, bhk) with `source: inferred`.
- A single bare budget ("85 lakh", "1.5 cr max") is stored as max only (`under 85L`); "above X" as min only.
- `PATCH` with only `follow_up_at` also bumps `last_activity_at` (same as other patches).
- LLM polish: `TrackingService(db, now, polish=async fn(draft, lang))`; the result is used only if name, listing title,
  budget text, match title and price all survive verbatim, else the template. `get_service` in the router does not
  wire an LLM yet.
- `hi`/`mr` drafts omit the "for a 2 BHK in Baner" phrase (budget only) to avoid mixed-script sentences.

## Gaps
- Rent budgets ("25k per month") are not parsed; the parser only understands lakh/crore/rupee amounts.
- Matching does not use city, carpet area, possession or furnishing.
- `/today` loads up to 2000 contacts and 500 listings per agent into memory (fine for MVP; needs indexes/aggregation later).
- `follow_ups_due` uses the server's UTC "end of today", not the agent's IST day.
- Tests use `tests/modules/listings_fakes.ListingsDb` for `$in/$ne`; shared helpers live in `tests/modules/qual_helpers.py`.
