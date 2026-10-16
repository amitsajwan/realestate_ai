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
- **Result:** `python -m app.worker` runs all 14 loops, each under its runner lease; on SIGTERM it cancels them (releasing the
  leases), then closes the database. It applies the startup wiring before the loops start. Production refuses to start without
  its database. `RUN_BACKGROUND_LOOPS` (default true) decides whether the API also starts them. The GCP compose deployment
  uses the same image for `conversations`, `newsroom` and `media`, with `--role` selecting each loop set and configurable CPU
  and memory limits. `--loops` selects an operational subset. `--check --role` checks only that role's heartbeats.
  Rollback: `RUN_BACKGROUND_LOOPS=true` in `.env`, then `docker compose up -d backend`; leases make overlap safe.

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

### Deployment phase 0: role workers on one VM (done in code; deploy and verify)
- The same backend image runs three independently restartable roles: conversations, newsroom and media.
- Each role has configurable CPU and memory limits; the media role can consume resources without killing comment replies.
- Work that lived only in a process's memory became loops with heartbeats, so a restart loses nothing: Meta webhooks
  (WhatsApp, Messenger, Instagram) are saved to `conversation_webhook_jobs` before the quick 200 and handled by
  `inbound_messages` (3 attempts; handled jobs expire after 30 days); calendar reel pre-rendering is `calendar_reels`; token
  clean-up is `token_cleanup`. With `RUN_BACKGROUND_LOOPS=true` the API starts the worker's whole table, so development and
  rollback run the same 14 loops.
- **Done when:** the VM runs all three role containers, each role's health check is green, and stopping media does not interrupt
  engage or answer gaps. Rollback is the API running all loops or one worker with no role selection.

### Deployment phase 1: move shared state off the VM
- Put upload reads, writes and public URLs behind `platform.media`; use Cloud Storage in production and keep local storage for
  development. Preserve old `/uploads/...` URLs with a redirect or proxy.
- Move MongoDB to a managed replica set and secrets from the VM `.env` to Secret Manager.
- Replace HTTP-process `BackgroundTasks`, fire-and-forget tasks and standalone cleanup loops with Mongo-backed queued items
  (done in phase 0 for Meta webhooks, calendar reel pre-render and token clean-up).
- Count AI and Meta quotas in Mongo rather than per-process memory.
- **Done when:** api and each worker role can run on different machines with no shared filesystem, process-local work queue or
  duplicated quota allowance, and a restart loses no accepted work.
- **Status (2026-10-16): TARGET, deferred by the owner.** Start it when a second machine is actually needed. Exception: start
  the Cloud Storage move earlier if the VM disk fills up.

#### Phase 1 costs (checked 2026-10-16)
Sizes measured on the VM that day: uploads 2 GB (2,929 files); Mongo data volume 496 MB; a compressed nightly backup 17 MB.
VM `e2-medium` (4 GB RAM), 30 GB disk at 79% used, mostly uploads.

| Item | Monthly cost | Notes |
|---|---|---|
| Cloud Storage (uploads) | ~$0.05 (₹5) now; ~$1 (₹90) at 50 GB | Standard class, asia-south1, $0.023/GB-month. Read and write charges are negligible. Bandwidth for reels and images is already paid from the VM today, so it moves rather than grows. Frees the VM disk. |
| Secret Manager | ~$1 (₹90) | About 20 keys. |
| MongoDB Atlas Flex | $8-30 (₹700-2,600) | 5 GB storage and 100 ops/s included, usage-based, capped at $30. Fits today's data. |
| MongoDB Atlas M10 | ~$57 (₹5,000) plus backups | Dedicated replica set; needed only once traffic grows. |
| MongoDB Atlas M0 (free) | $0 | 512 MB limit and no backups. Not usable: we are already at that size. |

Plan when phase 1 starts:
1. Move uploads to Cloud Storage first (cheap, frees the disk).
2. Keep Mongo on the VM, with the nightly backups, until a container actually runs on a second machine.
3. Then move Mongo to Atlas Flex in GCP Mumbai (asia-south1), in the same region as the VM. Watch the ops/s for the first
   week: the worker roles poll often (`inbound_messages` every second, lease renewals). Move to M10 only if Flex keeps
   reaching its $30 cap.

Phase 1 adds no servers. Phase 2 does: each extra machine the size of today's VM costs roughly ₹2,000-2,500 a month.
Recheck prices before buying: the Atlas figures come from third-party summaries
([OneUptime](https://oneuptime.com/blog/post/2026-03-31-mongodb-atlas-flex-cluster-pricing-model/markdown),
[CloudZero](https://www.cloudzero.com/blog/mongodb-pricing), [MongoDB pricing](https://www.mongodb.com/pricing.md)), and the
storage figure comes from [Google's pricing page](https://cloud.google.com/storage/pricing).

### Deployment phase 2: orchestration
- Run web and api on Cloud Run. Run one always-on instance of each worker role, with a second lease-protected replica only where
  failover is needed; use a small compose VM or GKE Autopilot when literal pods justify the operational cost.
- CI builds one image per commit and deploys each role independently. Centralize logs and add OpenTelemetry across process
  boundaries; worker heartbeats remain the loop alert.

### Deployment phases 3-4: boundaries, then optional extraction
- Finish steps 6-8 below. Keep the modular monolith while domains share release pace and ownership.
- Extract only after a concrete trigger: media first for compute scaling, then conversations for webhook latency, then newsroom.
  Start with the existing Mongo status machines; add a broker only if they become the bottleneck.
- Do not add Kafka, Temporal, a database per service, split Next.js apps or rewrite login for this move.

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
| 2026-10-16 | Deployment 0 | One backend image split into conversations, newsroom and media roles; role-scoped heartbeat checks and per-role resource limits; Meta webhooks, calendar reel pre-render and token clean-up moved to durable loops; the API's rollback mode runs the worker's full loop table. Built, not yet deployed |
| 2026-10-07 | 7, 8 (marketing part) | Old posting stack deleted: 6 endpoint groups (`/social-publishing`, `/publishing`, `/publishing-logs`, `/content`, `/enhanced-posts` and `/enhanced-post-management`, `/enhanced-templates`), 13 services, 4 schemas, 3 quarantined tests; the old dashboard's Property Marketing Hub, AI posting hub and publish workflow with the old clients that only they used (27 frontend files). None of it used the ledger. Studio and the public site never called it. The rest of the old app (`/dashboard`, `/login`, old Facebook connect, analytics, branding, ai-unified) is still to do. `docs/MARKETING.md` describes what remains |
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
