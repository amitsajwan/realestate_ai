# Modernization plan

How we get from today's code to the target in `docs/ARCHITECTURE.md`. Work happens on the `modernization` branch and lands in
small pull requests, one step (or part of a step) at a time. Each step has a "done when"; a step is not done until it is met.

## Rules while this runs

1. **Product work continues.** New features (TASKS.md) go straight into their target domain (ARCHITECTURE §4). In particular:
   the partner importer goes in inventory, alert sign-up in buyers, the publish queue in distribution.
2. **Behaviour does not change during a move.** Moves and renames are separate commits from fixes. Before code moves, tests pin
   its current output.
3. **Old import paths keep working while a move is in progress.** A shim at the old path re-exports from the new one and is
   deleted once nothing uses it.
4. **The full backend suite and the import rules stay green on every commit.** From `backend/`:
   `python -m pytest tests/` and `PYTHONPATH=. lint-imports` (rules in `backend/.importlinter`). Both run on every pull
   request (`.github/workflows/architecture.yml`).
5. **Login is not rewritten.** `core/auth_backend.py` moves into the platform as is.

## Baseline (3 October 2026)

| Measure | Today | Target |
|---|---|---|
| Modules caught in one import cycle | 16 of 22; 10 after step 2; **0 after step 3** | 0 |
| Imports between modules / of them hidden inside functions | 165 / 100; 109 / 68 after step 2; 98 / 58 after step 3 | only from public APIs / 0 (except heavy optional libraries) |
| Modules touching `listings` / `agent_public_profiles` / `contacts` | 16 / 12 (+4 old services) / 7 | 1 writer each |
| Old code (`services`, `api/v1`, `routers`, `schemas`, `repositories`, `models`, `utils`, `core`) | about 38,500 lines (26,000 after step 1) | platform keepers only |
| … of which never imported | about 11,400 lines (40 files); 0 after step 1 | 0 |
| Import-rule exceptions in `backend/.importlinter` | 8 (step 1); 4 after step 2; 1 after step 3; **0 after step 5** | 0 |
| Background loops guarded against running twice | 0 of 4 | 4 of 4 (step 0) |
| Background loops in their own process, with heartbeats | 0 of 4 | 4 of 4 (step 4, once deployed) |
| Publishing paths that post each item at most once | 0 of 5 | 5 of 5 (step 5) |

## Steps

### Step 0: Safety (in progress)
- One runner per background loop: `app/platform/leases.py`; engage, newsroom, calendar and listing reels start through it.
  The reel worker's startup clean-up no longer fails renders another process is running.
- Production refuses to start without its database (it used to carry on with "mock database").
- `deploy-production.sh` starts one process, like the Docker image (it started 4, which ran every loop 4 times).
- **Done when:** lease tests pass (two runners, one loop; step-down before expiry; hand-over on shutdown); the startup test
  passes; after deploy, `worker_leases` shows one holder per loop and no post ID appears twice in a week.

### Step 1: Delete dead code, turn on the import check (done)
- Delete the 40 never-imported files (list in the review, regenerate before deleting), `backend/modules/auth/`, the
  `*.fragment` file, the one-off scripts in `backend/` root, the mock Facebook and demo endpoints.
- Add `import-linter` to CI with the three layers and the domain order; record today's violations as the baseline.
- **Done when:** the app starts and the suite is green; CI fails on any new violation.
- **Result:** 14,568 lines deleted, every route except the 17 demo and mock ones unchanged. Three rules in
  `backend/.importlinter`: the platform imports no business code; new modules never import the old layer; domains import only
  downward. 8 baseline exceptions, each labelled with the step that removes it. A baseline line that no longer matches fails the
  check, so the list can only shrink. Content and conversations share one layer for now; making them independent siblings
  is part of step 3.

### Step 2: Extract the platform (done)
- Pin first: tests that record today's output of the copy guards, INR/sq ft/BHK formatting, phone normalising and grounding.
- Move into `app/platform/`: `llm`, `meta_graph`, `text`, `media`, `controls`, `config`, `db`, `auth` (ARCHITECTURE §3), with
  shims at the old paths.
- **Done when:** pinned tests unchanged; the cycle count is re-measured and recorded here; no module imports another module only
  for one of these helpers.
- **Result:** `controls`, `text`, `media`, `llm` and `meta_graph` are in `app/platform/`, pinned by 72 new tests plus the existing
  suites. `config`, `db`, `auth`, `region`, `brand` stay in `app/core/` for now: moving them touches about 150 files (half of
  them old-layer files deleted in step 8) and would collide with product work in progress, for no change in behaviour. A
  fourth import rule holds them to the platform rule where they are; the move itself is part of step 8.

### Step 3: Fix the wrong-way dependencies (done)
- `social → concierge.attribution`, `photoquality router → newsroom/calendar/concierge`, `admin → concierge.router` internals,
  `knowledge → calendar.library`, `interest → showcase.samples`. Replace each with a callback passed in at wiring time or a
  query function on the owner.
- Add a test that imports every module and calls every route once.
- **Done when:** the import check shows no upward edge; no function-level import is left to dodge a cycle.
- **Result:** no import cycle is left. `app/wiring.py` is the composition root: at startup it passes callbacks and data into
  lower modules (concierge's attribution into social, an operator check and per-kind review lookups into the quality route,
  showcase's sample catalogue into the interest hub, sample homes and evergreen posts into knowledge grounding, the listing
  facts builder into the comment assistant). The API wires when its route list loads, the worker at start, and the tests
  through a session fixture. Two new import rules keep content and conversations independent. `tests/test_imports.py`
  imports every module and resolves every import written inside a function; it found two broken imports in an old router
  that was never mounted, now deleted. The 58 imports left inside functions no longer dodge a cycle; moving them to the top
  of their files is cleanup for whoever next edits each file. `admin` still uses `concierge`'s route helpers: both are the
  operator console, the same layer, so this is allowed.

### Step 4: Worker process (done; verify after deploy)
- `python -m app.worker` from the same image runs the loops; the api process stops starting them.
- Heartbeat per loop; `deploy/gcp/health_check.sh` alerts when one is older than twice its interval.
- **Done when:** restarting the api does not interrupt a loop; stopping the worker raises an alert.
- **Result:** `python -m app.worker` runs engage, newsroom, calendar and listing reels, each under its runner lease; on
  SIGTERM it cancels them (releasing the leases), then closes the database. It applies the startup wiring before the loops
  start (caught in review: without it the comment assistant would crash on listing comments; a test covers it). Production
  refuses to start without its database. `RUN_BACKGROUND_LOOPS` (default true) decides whether the API also starts them; the
  GCP compose file sets it false on the backend and adds a `worker` service from the same build. Rollback:
  `RUN_BACKGROUND_LOOPS=true` in `.env`, then `docker compose up -d backend`. Each loop records start, success and error per
  cycle in `worker_heartbeats` (`app/platform/heartbeats.py`; never raises). `health_check.sh` checks the worker container and
  runs `python -m app.worker --check` in the backend container, alerting when a loop switched on in `.env` has had no
  heartbeat for twice its interval (for reels, twice the 15-minute render limit). Not yet run on the VM.

### Step 5: One publishing path (done in code; verify after deploy)
- Distribution owns the queue and the publication log; newsroom, calendar, showcase and reels hand it posts instead of calling
  the Graph API.
- Idempotency key per (item, channel); approval, daily caps and pause switches enforced in the queue; dry run outside production.
- **Done when:** a dry-run replay of a week of calendar and newsroom data makes the same decisions as today; rollback is a flag;
  no module other than distribution imports `platform.meta_graph` for publishing.
- **Result:** `app/modules/social/distribution.py` is the one way out. `send(db, key, publish)` posts each key at most once,
  recorded in `publish_ledger`: the claim is a unique document, a key already `sent` returns its post without posting, a
  `failed` key is retried, and a key still `sending` (an earlier attempt never finished) is refused with "may already be
  live". All five paths use it: listing packs (`social:<publication>`), calendar slots incl. reels and showcase posts
  (`calendar:<slot>`, with the posting pause), news (`news:<item>:<channel>`) and concierge reels (`reel:<job>:<channel>`).
  The reel publisher moved into social; newsroom, showcase and the calendar get their publisher from distribution; a 7th
  import rule forbids any other module from importing the Graph client. Social takes marketing's link line by wiring, which
  cleared the last import-rule exception. A calendar test shows the case this closes: the post went out, saving
  'published' failed, and the retry posted it again; with the ledger it does not.
  - **Rollback:** `PUBLISH_LEDGER=off` in `.env` (send posts directly, as before).
  - **When a post is refused with "may already be live":** check the Page / Instagram. If the post is there, nothing to
    do: mark the item done in its screen. If not, delete its document from `publish_ledger` (the key is in the error)
    and retry.
  - **Not moved, on purpose:** each caller keeps its own decision rules (approval, consent, the newsroom's daily cap, the
    calendar's one-post-per-channel-per-run). They already work and are tested; distribution guarantees at-most-once,
    dry-run and the pause on top. Newsroom does not pass its pause to `send`, because a failed news item is final (its
    runner checks the pause every cycle). The dry-run replay is not needed for this change: no decision rule moved.
  - **Still outside the ledger:** the operator scripts in `backend/scripts/` (`post_samples.py`, `brand_posts.py`,
    `schedule_text_posts.py`, `post_voiced_reels.py`), run by hand.

### Step 6: One writer per collection
- One collection at a time, starting with `listings` (inventory) and `agent_public_profiles` (identity). The owner gets query
  functions; other modules switch to them.
- **Done when:** a CI check finds no insert/update/delete on that collection outside its owner.

### Step 7: Frontend on the new API only
- Route inventory: list every old endpoint the frontend calls and decide per page: move or delete. Check production access logs
  for the old routes first.
- Keep the public site's `agent/public` API until the site's server-rendering rewrite, so it is migrated once.
- Group frontend code by feature (`features/<domain>`).
- **Done when:** nothing in `frontend/` calls an old endpoint; 404/401 rates per route are unchanged after the switch.

### Step 8: Delete the old code
- Remove the old endpoints, services, schemas and repositories, and the three old API clients.
- Move the platform parts of `app/core/` (config, database, auth, region, brand, indexes) and `app/models/user.py` into
  `app/platform/`.
- **Done when:** `backend/app/{services,routers,repositories,schemas}` and `api/v1/endpoints` are gone or hold only shims with
  no users.

### Alongside (AI gateway, any time after step 2)
- Per-task model routing, schema-checked outputs, the `llm_calls` log, distinct outcomes for quota/timeout/bad output.
- CI AI test sets for engage, newsroom, knowledge and the creative critic.
- **Done when:** every AI call goes through `platform.llm` and appears in `llm_calls`.

## Progress log

| Date | Step | Change |
|---|---|---|
| 2026-10-03 | 5 | Publish ledger (`distribution.send`): every post at most once per key, across all 5 publishing paths; only distribution imports the Graph client (7th import rule); last import-rule exception cleared; rollback `PUBLISH_LEDGER=off` |
| 2026-10-03 | 3 | No import cycles left: wrong-way imports replaced by callbacks and data passed in by `app/wiring.py`; content and conversations independent (2 new import rules); every module and function-level import checked by a test, which found and removed an unmounted broken router. Exceptions 4 -> 1 |
| 2026-10-03 | 4 | Worker process (`python -m app.worker`), `RUN_BACKGROUND_LOOPS` flag (API default unchanged; false in deploy/gcp), per-loop heartbeats in `worker_heartbeats`, stale-heartbeat alert in `health_check.sh`; built in parallel with step 3, merged, and fixed so the worker applies the startup wiring |
| 2026-10-03 | 2 | Step 2 closed: core's platform parts held to the platform rule in place by a 4th import rule; their physical move is deferred to step 8 |
| 2026-10-03 | 2 | Meta Graph client moved to `platform.meta_graph` (`config`, `graph`, `publisher`, files moved unchanged with history); 35 files across modules, tests and scripts import it from there; `social` keeps only its publish service and routes |
| 2026-10-03 | 2 | AI gateway moved to `platform.llm` (providers, model failover, json/text, speech-to-text, `default_llm`); the listing prompts stay in `ai_listing` as `ListingLLM` on top of it. 9 modules and 6 scripts use the gateway from the platform. Every kept definition is identical to before (checked by comparing the code); one new test covers the about-suggest endpoint's use of the same client. The `social -> marketing.content` exception is re-labelled to step 5 (it is pack building, not a shared helper) |
| 2026-10-03 | 2 | Media URL helpers moved to `platform.media` (`upload_path`, `display_url`, `public_media`, enhanced-copy names), pinned first by 24 tests; listings and marketing use them from there; photo analysis stays in photoquality. 1 import-rule exception removed |
| 2026-10-03 | 2 | Text helpers moved to `platform.text` (copy guards, INR/sq ft/BHK formatting, Indian mobile numbers, LLM output clean-up), pinned first by 48 tests; 14 modules and 2 scripts import them from there; `onboarding/phone.py` deleted. Note: `money(9_999_999)` gives '₹100 Lakh', pinned as is, to fix separately |
| 2026-10-03 | 2 | Pause switches moved to `platform.controls` (the 3 runners and admin now import them from there): 3 import-rule exceptions removed |
| 2026-10-03 | 1 | Deleted 40 never-imported files, the demo and mock Facebook endpoints, `backend/modules/auth` and 12 debug scripts (14,568 lines); import rules in CI with 8 baseline exceptions |
| 2026-10-03 | 0 | Runner leases for the 4 background loops; production needs its database; one process in `deploy-production.sh`; target and plan written |
