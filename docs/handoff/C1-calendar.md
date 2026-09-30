# C1: content calendar and evergreen library

Keeps the Facebook Page (PUNE Property) and Instagram (@kharadi_prop) posting on a steady rhythm without news. New module `backend/app/modules/calendar/`, loosely coupled: it imports only `marketing.images`, `marketing.brand_posts` (the brand card renderer), `marketing.polish` (HYPE and PHONE guards) and `social` (config, `GraphPublisher`, `Post`, `sanitize`). No existing file was edited.

## What was built

| File | Purpose |
|---|---|
| `library.py` | 40 evergreen posts (`Entry`): slug, pillar, card kicker/title/points, shared caption body, hashtags, `review` note, optional site link. Facebook and Instagram captions are derived from the body |
| `guards.py` | Safety checks (HYPE, PHONE, price and prediction wording, no URL in Instagram, length and hashtag limits, link exists, ends with a question or save/share prompt) |
| `schedule.py` | Pure layout: Facebook 4 a week, Instagram 3 a week, 10:00 or 19:00 IST, varied weekdays, 12 h minimum gap per channel, pillar rotation, no slug repeat on a channel within 60 days, idempotent against existing rows |
| `render.py` | Brand cards. Facebook: 1080x1080 at `uploads/calendar/<slug>.jpg`. Instagram: 4:5 portrait 1080x1350 at `uploads/calendar/ig/<slug>.jpg` |
| `store.py` | The only Mongo file. Collections `content_calendar` and `calendar_status` |
| `runner.py` | Loop every 5 minutes, idle unless `CALENDAR_ENABLED=true` |
| `router.py` | Owner-only `GET /calendar/upcoming`, `GET /calendar/status`, `POST /calendar/items/{id}/skip` |
| `config.py` | Env settings |
| `backend/scripts/calendar_admin.py` | `preview`, `seed`, `list`, `skip`, `status`, `--dry-check` |
| `backend/tests/modules/calendar/` | 50 tests, no network |

Library: 40 posts. Pillars: 7 myth vs fact, 11 explainers (how to read a RERA page, cost sheet, agreement, carpet area, loan basics, registration steps, possession and OC, defect window, separate account, payment plan), 10 checklists (water and power, commute test, society and maintenance, questions for agents, red flags in ads, resale vs new, documents, rainy-day visit, possession snag list, monthly outgoings), 5 polls and 3 local-life posts, 4 agent pitches (2 English, Hindi, Marathi; free invite-only pilot).

Runner behaviour: publishes rows with `due_at <= now` through `GraphPublisher`, at most 1 per channel per pass. `SOCIAL_DRY_RUN` (the default) marks the row published with a `dryrun_...` id and touches no network. A failure stores a sanitised reason; the row is retried after 10 minutes, at most twice (3 attempts total), then marked `failed`. A row overdue by more than `CALENDAR_STALE_HOURS` (48) is marked `skipped` so a server outage never bursts old posts out. Run status goes to `calendar_status` (`last_run_at`, `last_counts`, `last_error`).

Design change applied: Instagram cards are 4:5 portrait (1080x1350) and use their own file; Facebook keeps the square. `marketing.render_brand_post` has no `size` argument in this base, so `render.py` draws the same layout with a size argument (it calls the marketing function instead when it gains a `size` parameter). Tests check every IG card is 1080x1350, every FB card 1080x1080, all text inside the 84 px margins and no text cut with an ellipsis. Known limitation: the Hindi and Marathi pitch cards exist only as pre-rendered square Chrome images (Pillow cannot shape Devanagari), so their IG version is the square centred on a portrait canvas with the top and bottom rows stretched. Text stays in the original margins, but it looks less filled than the others. Re-render them in Chrome at 1080x1350 via `frontend/e2e/render-static-cards.js` if wanted and adjust `_to_portrait`.

## Wiring snippet for the integrator (not applied)

`backend/app/api/v1/router.py`:
```python
from app.modules.calendar.router import router as calendar_router
api_router.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
```

`backend/app/core/application.py`, in the lifespan next to the newsroom task:
```python
        # Content calendar (idle unless CALENDAR_ENABLED=true)
        from app.modules.calendar.runner import loop as calendar_loop
        app.state.calendar_task = asyncio.create_task(calendar_loop())
```
and add `"calendar_task"` to the shutdown tuple `("engage_task", "newsroom_task", "calendar_task")`.

Environment: `CALENDAR_ENABLED` (default off), `CALENDAR_INTERVAL_SECONDS` (300), `CALENDAR_STALE_HOURS` (48), `CALENDAR_OWNER_IDS` (comma-separated user ids; superusers always allowed). It also uses the existing `SOCIAL_DRY_RUN`, `META_PAGE_ID`, `META_IG_BUSINESS_ID`, `META_PAGE_ACCESS_TOKEN`, `PUBLIC_MEDIA_BASE_URL`, `UPLOAD_DIRECTORY`, and optionally `PUBLIC_SITE_URL` (default is the sslip.io site used by the brand posts) for the Facebook links. The uploads directory must be served at `/uploads` as it is for the brand posts.

## Running it on the server

```
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py --dry-check
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py preview --out /tmp/calendar-preview   # look at the cards and captions first
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py seed --start 2026-10-06 --weeks 8
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py list --status scheduled
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py skip <id>
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py status
```
`seed` refuses to run if `--dry-check` fails, and is idempotent: a slot (channel and time) that already has a row is not filled again, slugs already used are not repeated within 60 days, so running it twice writes nothing new and `--weeks 12` later only adds the extra weeks. Start with `SOCIAL_DRY_RUN=true CALENDAR_ENABLED=true`: rows turn `published` with fake ids and nothing is posted, which proves the loop. For real posting set `SOCIAL_DRY_RUN=false`; note that this switch is global (it also un-dries agents' listing posts). Cards are rendered on demand into `uploads/calendar/` on first publish, so nothing has to be pre-uploaded.

Before the first real run, have a Hindi and a Marathi reader approve `agent-hindi` and `agent-marathi` (adapted from the already published brand copy), and re-check `loan-prepay-rule` against rbi.org.in (see below). To drop a post from the plan, `skip` its row, or delete the entry from `library.py` before seeding.

## Sources verified (and cited in each entry's `review`)

- RERA Act 2016 text as reproduced on ibclaw.in, taxguru.in, iPleaders and summaries (indiacode.nic.in PDF returned 403): Sec 2(k) carpet area (net usable floor area; includes internal partition walls; excludes external walls, service shafts, exclusive balcony/verandah, exclusive open terrace); Sec 13(1) (no more than 10% advance or application fee without a registered written agreement for sale); Sec 14(3) (defects reported within five years of possession to be rectified within thirty days free of charge); Sec 4(2)(l)(D) (70% of receipts in a separate scheduled-bank account, withdrawn in proportion to completion, certified by architect, engineer and chartered accountant); Sec 19(10) (take physical possession within two months of the occupancy certificate).
- maharera.maharashtra.gov.in (fetched): registered project search, project progress, make a complaint, guidance for home buyers. Only those features are mentioned.
- igrmaharashtra.gov.in (fetched): e-ASR, e-Registration 2.0, e-Appointment, e-Search, GRAS e-payment. Only named generally, no fees.
- Registration Act 1908 Sec 23: present a document for registration within four months of execution (legalserviceindia.com, bcasonline.org).
- Maharashtra stamp duty charged on the higher of agreement value and ready reckoner value (cleartax.in, godrejcapital.com, propnewz.com; secondary only, official tool is e-ASR). Presented without any rate.
- CC vs OC (maharera.maharashtra.gov.in/possession-stage; nobrokerage.com, marathon.in on PMC and PCMC practice; secondary).
- RBI Directions on Pre-payment Charges on Loans, 2025: no prepayment charge on floating-rate loans to individuals for non-business use, sanctioned or renewed on or after 1 January 2026 (BusinessToday, AngelOne; the RBI PDF was not machine-readable). Kept with the date caveat; re-check on rbi.org.in, and delete `loan-prepay-rule` if it cannot be confirmed.
- Metro posts reuse the facts already on our own site pages (Corridor 2B and Line 4 approved by the Union Cabinet, approved is not running); no dates or forecasts.

## Claims dropped (not used, because unverifiable or unstable)

- The RERA Sec 3 size threshold (500 sq m or 8 apartments): sources disagree on whether it is "and" or "or", and courts have interpreted it, so no size rule is stated.
- Any stamp duty percentage, registration fee amount or fee cap (Maharashtra 1% capped at a flat amount): only secondary sources, and rates and concessions change by notification.
- The name of the planning authority issuing the OC for each locality (PMC, PCMC or PMRDA differs by area).
- Legal timelines for society or conveyance formation, and any statement about a locality's water supply, roads, distances, commute times, schools or hospitals.
- Prices, price comparisons between areas, appreciation or returns, builder names, statistics, phone numbers, personal names.

## Notes and follow-ups

- The Instagram caption for a post with a site link ends with "link in our bio"; the Facebook caption carries the real URL. Hindi and Marathi Instagram captions use a mixed-language line that still contains "link in our bio".
- Rotation: explainers and myths are most frequent, agent pitches about one slot in ten. The same slug may appear on both channels (a soft preference keeps them at least two days apart).
- The runner does not use the Facebook dedupe used elsewhere; do not run `scripts/brand_posts.py` and this calendar over the same slugs (`agent-hindi` and `agent-marathi` reuse the brand cards but carry new captions).
