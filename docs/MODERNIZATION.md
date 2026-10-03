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
| Modules caught in one import cycle | 16 of 22 | 0 |
| Imports between modules / of them hidden inside functions | 165 / 100 | only from public APIs / 0 (except heavy optional libraries) |
| Modules touching `listings` / `agent_public_profiles` / `contacts` | 16 / 12 (+4 old services) / 7 | 1 writer each |
| Old code (`services`, `api/v1`, `routers`, `schemas`, `repositories`, `models`, `utils`, `core`) | about 38,500 lines (26,000 after step 1) | platform keepers only |
| … of which never imported | about 11,400 lines (40 files); 0 after step 1 | 0 |
| Import-rule exceptions in `backend/.importlinter` | 8 (step 1) | 0 |
| Background loops guarded against running twice | 0 of 4 | 4 of 4 (step 0) |

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

### Step 2: Extract the platform
- Pin first: tests that record today's output of the copy guards, INR/sq ft/BHK formatting, phone normalising and grounding.
- Move into `app/platform/`: `llm`, `meta_graph`, `text`, `media`, `controls`, `config`, `db`, `auth` (ARCHITECTURE §3), with
  shims at the old paths.
- **Done when:** pinned tests unchanged; the cycle count is re-measured and recorded here; no module imports another module only
  for one of these helpers.

### Step 3: Fix the wrong-way dependencies
- `social → concierge.attribution`, `photoquality router → newsroom/calendar/concierge`, `admin → concierge.router` internals,
  `knowledge → calendar.library`, `interest → showcase.samples`. Replace each with a callback passed in at wiring time or a
  query function on the owner.
- Add a test that imports every module and calls every route once.
- **Done when:** the import check shows no upward edge; no function-level import is left to dodge a cycle.

### Step 4: Worker process
- `python -m app.worker` from the same image runs the loops; the api process stops starting them.
- Heartbeat per loop; `deploy/gcp/health_check.sh` alerts when one is older than twice its interval.
- **Done when:** restarting the api does not interrupt a loop; stopping the worker raises an alert.

### Step 5: One publishing path
- Distribution owns the queue and the publication log; newsroom, calendar, showcase and reels hand it posts instead of calling
  the Graph API.
- Idempotency key per (item, channel); approval, daily caps and pause switches enforced in the queue; dry run outside production.
- **Done when:** a dry-run replay of a week of calendar and newsroom data makes the same decisions as today; rollback is a flag;
  no module other than distribution imports `platform.meta_graph` for publishing.

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
- **Done when:** `backend/app/{services,routers,repositories,schemas}` and `api/v1/endpoints` are gone or hold only shims with
  no users.

### Alongside (AI gateway, any time after step 2)
- Per-task model routing, schema-checked outputs, the `llm_calls` log, distinct outcomes for quota/timeout/bad output.
- CI AI test sets for engage, newsroom, knowledge and the creative critic.
- **Done when:** every AI call goes through `platform.llm` and appears in `llm_calls`.

## Progress log

| Date | Step | Change |
|---|---|---|
| 2026-10-03 | 1 | Deleted 40 never-imported files, the demo and mock Facebook endpoints, `backend/modules/auth` and 12 debug scripts (14,568 lines); import rules in CI with 8 baseline exceptions |
| 2026-10-03 | 0 | Runner leases for the 4 background loops; production needs its database; one process in `deploy-production.sh`; target and plan written |
