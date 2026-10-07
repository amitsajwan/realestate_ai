# Avasetu: target architecture

Status: **agreed target**, October 2026. The plan for getting here, step by step, is `docs/MODERNIZATION.md`.
Product decisions (governance, India requirements, business model, Facebook Marketplace limits) from the earlier proposal still
stand: `docs/archive/ARCHITECTURE_v2_proposal.md`. Product direction: `docs/PRODUCT_PLAN.md` and `docs/TASKS.md`.
How content is made, published, measured and learned from, and the work items for the team: `docs/CONTENT_PLATFORM.md`.

## 1. Shape

**One backend app, one database, clear internal modules (a modular monolith).** FastAPI + MongoDB + Next.js on one VM.
Splitting into services is premature for a 3-10 agent pilot and a small team.

Two processes run from the same Docker image:
- **api**: serves HTTP.
- **worker** (`python -m app.worker`): runs the background loops (newsroom, calendar, comment assistant, listing reels, later
  freshness and the publish queue). `RUN_BACKGROUND_LOOPS=true` makes the api run them instead (the default where no worker is
  deployed); runner leases keep one copy of each loop either way.

**Constraints we design for:** MongoDB is a single server (`mongo:7`, no replica set). No multi-document transactions, no change
streams and no Atlas Vector Search. Nothing in this design may depend on them.

## 2. Layers

Three layers. Code may import from its own layer or a lower one, never a higher one.

```
apps / http   routers (one list, each module adds its own), operator console, public site API
domains       identity, inventory, buyers, distribution, content, conversations
platform      config, db, auth, runner leases, jobs, llm gateway, meta graph client, media, text, controls
```

Inside `domains` there is an order too (lower first). A domain may import the public API of a domain to its left, never to its right:

```
identity < inventory < buyers < distribution < content
                                             < conversations
```

`content` and `conversations` are siblings: neither imports the other.

When a lower module needs something from a higher one (for example, Distribution needs the "Listed by" attribution that the
operator console knows), the higher module **passes a callback in at wiring time**. There is no event bus.
`newsroom/pipeline.py` (`default_stages`) and `newsroom/adapters.py` already work this way, and they are the pattern to copy.
All such wiring lives in one place, `backend/app/wiring.py` (the composition root), called by the api's route list, by the
worker at start and by the tests.

## 3. Platform (`backend/app/platform/`)

Shared building blocks with no business knowledge. Nothing here imports from `app.modules`.

`config`, `db`, `auth`, `region` and `brand` are platform code that still lives in `app/core/` and `app/models/user.py`; CI already
holds them to the platform rule. They move into `app/platform/` in step 8, when the old layer that also imports them is gone.

| Package | What | Comes from |
|---|---|---|
| `config` | One settings object; no `os.environ` reads elsewhere | `core/config.py`, the env reads in `ai_listing/llm.py` and module `config.py` files |
| `db` | Connection, `get_database`, indexes | `core/database.py`, `core/indexes.py` |
| `auth` | `current_active_user`, `User`, roles | `core/auth_backend.py`, `models/user.py` (moved as is; never rewritten during the refactor) |
| `leases` | One runner per background loop | new, **done** (step 0) |
| `jobs` | Worker entry point, heartbeats per loop | `app/worker.py`, `platform/heartbeats.py`, **done** (step 4) |
| `llm` | AI model access: per-task model routing, schema-checked outputs, failover, call log | `ai_listing/llm.py` (gateway moved, **done** step 2; routing, schemas and call log still to come) |
| `meta_graph` | Facebook/Instagram Graph client and settings, `sanitize`, publish errors | `social/graph.py`, `social/publisher.py`, `social/config.py`, **done** (step 2) |
| `media` | Upload storage, public URLs | `photoquality/store.py` (URL helpers **done**, step 2), `endpoints/uploads.py` |
| `text` | Copy guards (hype words, phone numbers), INR/lakh/crore, sq ft, BHK, Indian mobile numbers, LLM output clean-up | `marketing/polish.py`, `marketing/facts.py`, `onboarding/phone.py`, **done** (step 2) |
| `controls` | Owner pause switches | `admin/controls.py`, **done** (step 2) |
| `region`, `brand` | Where we operate; the brand name and site URL | `core/region.py`, `core/brand.py` |

## 4. Domains

Each domain is a package under `backend/app/modules/`. A domain is made of one or more of today's modules.

| Domain | What it does | Today's modules | Owns (only writer) |
|---|---|---|---|
| **identity** | Users, phone OTP, invites, agent profile and site settings | onboarding, waitlist, old `agent_public` | `users`, `otp_codes`, `invites`, `invite_requests`, `agent_public_profiles` |
| **inventory** | Listings, freshness, the MahaRERA project register, partner imports (T3) | listings, newsroom's `register.py`, the importer | `listings`, `projects` |
| **buyers** | Contacts, requirements, events, scoring, matching, alerts (T2.4), agent reports | tracking, interest, report | `contacts`, `events`, `inquiry_log`, `interest_*`, `hub_items` |
| **distribution** | One way out (`send` + publish ledger), one adapter per channel (Facebook, Instagram, WhatsApp, YouTube), publication log, tracked links | social (incl. the reel publisher; **only it** imports the Graph client) | `publications`, `publish_ledger` |
| **content** | Sources → drafts → review → ready to publish; the render kit (brand, layouts, cards, reels) | newsroom, calendar, showcase, marketing packs, creative, reels, photoquality | `newsroom_*`, `content_calendar`, `calendar_status`, `marketing_packs`, `reel_jobs` |
| **conversations** | Comment replies, website chat, WhatsApp inbound, grounded answers, notifications | engage, chat, whatsapp, knowledge, notifications | `engage_*`, `chat_sessions`, `whatsapp_*`, `notifications` |

**Apps** (top layer, may use any domain): operator console (concierge, admin), public site API, HTTP routers.
The operator console owns `concierge_agents` and `concierge_audit`; the platform owns `admin_settings` (controls) and
`worker_leases`.

## 5. Module rules

1. **Public API.** A module's `__init__.py` lists what other modules may use (functions and data types). Everything else in the
   folder is private. Other modules import only from the package, never from its files.
2. **One writer per collection.** Only the owning module inserts, updates or deletes. Others read through the owner's query
   functions. We do not rename collections or reshape documents during the pilot.
3. **No upward imports.** Use a callback passed in at wiring time.
4. **No function-level imports to dodge a cycle.** They are allowed only for heavy optional libraries (ffmpeg, vision models).
5. **Routes come from the module.** Each module exports its routers; `api/v1/router.py` is a short list.
6. **Tests live with the module** under `backend/tests/modules/<module>/`, and every module has a test that imports it.

Enforcement: `import-linter` in CI with today's violations recorded as a baseline that may only shrink (step 1).

## 6. Background work

- Every loop is started through `app.platform.leases.run_as_leader(name, loop, get_database)`: whichever process holds the lease
  document `worker_leases/<name>` runs the loop; the others wait. A leader that cannot renew steps down before the lease can
  expire, so two copies never run at once.
- The loops are already status machines stored in Mongo (newsroom items, calendar slots, reel jobs). That is our durable workflow.
  We do not add Temporal, Inngest or a general job framework.
- Each loop records a heartbeat (last cycle start, last success, last error) in `worker_heartbeats`. `deploy/gcp/health_check.sh`
  alerts when a heartbeat is older than twice the loop's interval (`python -m app.worker --check`).

## 7. Publishing

All posts go through Distribution (`app/modules/social/distribution.py`, `send(db, key, publish)`):
- one idempotency key per (item, channel), recorded in `publish_ledger`, so a retry never posts twice; a post whose
  outcome is unknown is refused, never repeated (built in step 5; `PUBLISH_LEDGER=off` is the rollback);
- pause switches are checked in `send` as well as by the runners; approval, consent and daily caps stay with each caller,
  which decides what to post;
- dry run is the default outside production;
- every post carries a tracked link back to a page on our site (TASKS T2.1);
- **no AI agent ever publishes.** Publishing is deterministic.

## 8. AI

Today's design is right and stays: fixed pipelines, rules before the model, a guard on every output, a deterministic fallback when
the model fails, and a human approving anything published.

**Gateway (`platform/llm`):**
- `llm.json(task, system, user, schema)`: the reply is validated against a Pydantic model, with one repair retry.
- Model chosen per task in config: a small fast model for classifying comments and filtering news, a stronger one for drafts and
  the critic. Provider failover as today.
- Every call is logged to `llm_calls` (task, prompt version, model, provider, time, tokens, outcome, which guard rejected it and
  why), with old rows expiring automatically. This is our tracing.
- A quota outage, a timeout and a bad output are reported as different outcomes, never all as `None`.

**Tests:** fixed-answer AI test sets run in CI for listing extraction (exists), engage replies (EN/HI/MR), the newsroom filter and
check (MahaRERA fixtures exist), knowledge refusing to answer beyond its facts, and the creative critic.

| Adopt now | Later, when the product needs it | Avoid |
|---|---|---|
| Schema-checked outputs, per-task models, `llm_calls` log, CI AI tests | Buyer advisor (Phase 3): a hand-written tool-calling loop with the grounding guard on its answer; LangGraph only if it branches more than about 3 ways | Agents or LangGraph in newsroom, calendar, creative, engage or chat |
| | AI extraction for the partner importer (T3) and WhatsApp qualification (Phase 5) | Any agent allowed to publish |
| | Langfuse cloud free tier; OpenTelemetry once there is a second service | Self-hosted Langfuse (needs ClickHouse, Redis, S3) |
| | Vector search once there are hundreds of guides and projects (in-process embeddings or self-hosted Mongo search) | Retrieval search (RAG) for comment replies: closed, verified facts stay the source |
| | An MCP server for the operator team (project register, review queue) | An AI model as the final judge: the rule-based critic blocks, the AI critique advises |
| | | Temporal or Inngest |

## 9. Frontend

- The studio (`lib/app`, `app/studio`) and the public site (`app/agent`, `app/localities`, `app/news`, `app/insights`) use the
  new API only.
- Code is grouped by feature, matching the backend domains: `features/<domain>/{api, hooks, components}`.
- The old pages (`/dashboard`, `/properties`, `/profile`, `/analytics`) and the three old API clients (`lib/api.ts`,
  `lib/api/centralized-client.ts`, `lib/api/unified-client.ts`) are retired (step 7).
- Fixtures move out of `lib/app` into test folders.

## 10. Not doing

- Microservices, an event bus, a second database.
- Rewriting login during the refactor.
- Moving data between collections or reshaping documents during the pilot.
