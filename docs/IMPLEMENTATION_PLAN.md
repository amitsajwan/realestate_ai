# Implementation Plan (multi-agent execution)

Companion to ARCHITECTURE.md and ROADMAP.md. Goal of the first release ("MVP-1"):
an India-focused agent signs up, gets a live website in a few clicks, posts a listing
from photos/voice/WhatsApp, it lands on their site + our marketplace pool + social, and
every view/inquiry is tracked and attributed.

## 1. Working rules for parallel agents
- **One integration branch** `v2/integration` off the stabilized branch. Each workstream works in its own git worktree/branch `v2/<ws>-<topic>` and merges via PR into integration. Nobody pushes to `main`.
- **Strict directory ownership** (below). An agent never edits files outside its ownership; cross-cutting changes go through the contract owner (WS-0).
- **Contracts first.** Wave 0 freezes: Mongo collection schemas, the `Event` schema, REST route table + Pydantic models, and `SiteConfig`. Frontend/backend agents code against these; changes need a contract PR reviewed by WS-0.
- **Definition of done per PR:** tests pass in CI, no new file over ~400 lines, no new endpoint outside the module router, tenant/owner scoping tested, docs line updated.
- **New code lives in `backend/app/modules/<name>/`** (router.py, service.py, models.py, schemas.py, tests/). Legacy code is only removed by WS-0 or ported by the owning workstream.
- Every workstream ends with a short handoff note in `docs/handoff/<ws>.md` (what shipped, gaps, follow-ups).

## 2. Waves and dependencies
```
Wave 0 (serial, ~1 wk):  WS-0 Stabilize + contracts
Wave 1 (parallel, 2-3 wks): WS-1 Identity/Onboarding | WS-2 Listings+Pool | WS-3 Tracking core | WS-7 CI/QA
Wave 2 (parallel, 2-3 wks): WS-4 Agent Website (SSR) | WS-5 AI Listing Creation | WS-8 Agent Dashboard
Wave 3 (parallel, 3 wks):   WS-6 Distribution (IG/FB/WhatsApp) | hardening | pilot with 10 agents
Later: Marketplace matching/agent-to-agent, billing, buyer app
```

## 3. Workstreams

### WS-0 Stabilize + contracts (blocking; me/one agent)
Owns: repo root, `backend/app/main.py`, `core/`, `docs/`, CI config.
- Commit current tree on `cursor/analyze-and-fix-styling-issues-cacb`; create `v2/integration`.
- Fix env (venv -> valid Python, install requirements) so `pytest` runs, incl. `test_unified_property_service_queries.py`.
- Collapse to ONE router (`api/v1/router.py`), remove duplicate mounts in `main.py`/`api.py`.
- Delete dead endpoints/services/frontend test routes; move root status docs to `docs/archive/`.
- Choose auth: single flow, phone OTP + JWT (fastapi-users only if it fits OTP; else thin custom). Remove mock/demo/bypass paths.
- Publish contracts in `docs/contracts/` (schemas.md, events.md, api.md, siteconfig.json).
- Accept: `pytest` green, one router, app boots, contracts merged.

### WS-1 Identity + onboarding (`modules/identity`, `modules/agents`)
- User/Agent/Agency models, roles, phone OTP (provider abstraction; console provider in dev, MSG91/Twilio later), JWT + refresh.
- One onboarding endpoint: creates agent, slug (reserved-word + uniqueness checks), default `SiteConfig`, triggers AI branding (reuse `branding.py` logic).
- Agent KYC + RERA number fields (status: unverified/pending/verified; manual review queue for now).
- Accept: signup to live slug in one API call; role guards tested; owner-scoping helper shared via `platform/`.

### WS-2 Listings + marketplace pool (`modules/listings`, `modules/marketplace`)
- Canonical `Listing` (core facts only; AI/automation blobs move to a separate `listing_enrichment` doc). Port and preserve the tested query behaviour (active+published public filter, `status` param handling).
- Migration script from current `properties` collection (idempotent, dry-run flag).
- Pool capture: on publish, listing gets `visibility` (default `network`), `fingerprint`, `cluster_id`; dedupe clustering; freshness expiry job.
- Pool search API (city/locality/BHK/budget), agent-only; public search returns `public` visibility only.
- Accept: create -> appears in pool; duplicate posted by 2 agents lands in one cluster; visibility respected in every query (tests).

### WS-3 Tracking core (`modules/tracking`, `modules/crm` minimal)
- `POST /t/event` (public, rate limited, bot-filtered) + server-side emit helper; append-only `events`; anonymous id cookie; identify/merge on inquiry.
- Contact + Lead creation from inquiries with source/UTM/listing attribution; per-agent lead inbox API.
- Lead score v1 (rules: recency, repeat views, inquiry, WhatsApp click).
- DPDP: consent capture on contact creation, erasure endpoint.
- Accept: view -> click -> inquiry produces one Contact with ordered event timeline; per-agent isolation tested.

### WS-4 Agent website (`frontend/app/(site)/`, `frontend/components/site/`)
- Next.js server components + `generateMetadata`, OG images, sitemap, JSON-LD; ISR with revalidate on publish.
- Host-based routing (middleware): `<slug>.<domain>` and `/agent/<slug>` fallback; custom domain hook (later).
- Renders `SiteConfig` (theme, hero, sections, languages) and the agent's listings + "network picks" from pool with attribution.
- Contact/WhatsApp CTA -> tracking events; INR lakh/crore formatting; mobile-first; Hindi/Marathi strings.
- Accept: Lighthouse SEO >= 90 and mobile perf >= 80 on a sample site; WhatsApp link preview correct; events land in WS-3.

### WS-5 AI listing creation (`modules/ai`, `modules/listings/ai_intake`)
- Single `ai` interface (Groq now, swappable); consolidate the duplicate `unified_ai_content_service(_v2)` into it.
- Intake: photos/voice note/WhatsApp text/pasted link -> structured draft with per-field confidence -> confirm UI payload.
- Multilingual copy (En/Hi/Mr) + channel creative variants; anomaly flags (price outlier, duplicate).
- Accept: golden set of 30 sample inputs, >= 85% field accuracy on BHK/area/locality/price; every draft requires human confirm before publish.

### WS-6 Distribution (`modules/distribution`, `modules/social`)
- Connector interface (`publish`, `fetch_comments`, `fetch_messages`, `handle_webhook`). Port existing FB/IG/LinkedIn code into it.
- WhatsApp Business Cloud API: opt-in, templates, click-to-chat with tracking id, inbound webhook -> lead.
- Instagram Graph publishing (feed/reel), Facebook Page posts; comment/DM ingestion -> Events.
- Retry/outbox + per-channel status; token lifecycle (reuse `token_lifecycle_manager`).
- Not doing: Facebook Marketplace (no API); revisit via partner program.
- Accept: one confirm publishes to site + pool + selected channels; each post has a tracking id; inbound comment creates an attributed lead.

### WS-7 CI/QA/infra (`.github/`, `docker/`, `tests/e2e`)
- CI: backend pytest + ruff, frontend tsc/lint/jest, Playwright smoke; docker-compose dev with Mongo + Redis; seed data script.
- Contract tests (schemathesis/OpenAPI diff) so frontend/backend can't drift.
- Accept: PRs blocked on red CI; `docker compose up` gives a working demo with seeded agent + site.

### WS-8 Agent dashboard (`frontend/app/(app)/`)
- Mobile-first: my site, my listings (AI create flow), leads inbox with timeline and score, pool search, channel connections.
- Reuse the existing design system components; delete unused ones as found.
- Accept: the full MVP-1 journey runs in Playwright end to end.

## 4. Integration milestones
| Milestone | Gate |
|---|---|
| M0 Baseline | WS-0 accept criteria; contracts frozen |
| M1 Skeleton E2E (end Wave 1) | signup -> slug -> create listing -> in pool -> event recorded (API only) |
| M2 Site live (end Wave 2) | public SSR site + AI-created listing + tracked inquiry in dashboard |
| M3 Reach (end Wave 3) | one confirm posts to site+pool+IG/FB+WhatsApp; comments/DMs return as leads |
| M4 Pilot | 10 real agents, RERA manual review, feedback loop |

## 5. Risks and mitigations
- Meta/WhatsApp app review and business verification take weeks: start applications during Wave 1 (non-code task for you).
- AI extraction quality: keep human confirm; measure against the golden set before widening.
- Dedupe false merges: cluster, don't delete; agents keep their listing.
- Scope creep into matching/agent messaging: explicitly post-MVP-1.
- Data migration from legacy `properties`: dry-run + backup before any write.

## 6. Decisions still needed from you
1. RERA verification: manual review for the pilot (recommended) vs automation.
2. Domain name for `<slug>.<domain>` (needed by WS-4).
3. WhatsApp Business / Meta developer accounts: who owns them (needed by WS-6, long lead time).
4. SMS/OTP provider preference (default: provider abstraction, console in dev).
