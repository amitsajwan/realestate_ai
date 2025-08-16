# Product Discovery, Architecture, and Roadmap

Date: 2025-08-16
Owners: Product (PO/PM), Business (Agents), BA, Tech Architect, Eng, QA

## Executive summary
- We stabilized a production-like CRM on port 8004, added auth, leads/properties, a working dashboard, and baseline AI features.
- We containerized CI with MongoDB and automated tests (unit/integration + UI e2e with Playwright).
- We completed MongoDB-only implementation and refactored Facebook endpoints; remaining 500s on FB endpoints must be fixed.
- This document aligns business goals with a phased roadmap, backlog, and architecture guardrails.

## Workshop decisions & priorities (2025-08-16)
- Priorities
  - P0: Fix 500s on Facebook endpoints and complete MongoDB-only implementation
  - P0: Stabilize JWT issuance/verification (python-jose) and add smoke tests
  - P1: Add Facebook Graph API mocks + feature flag for external calls; expand integration tests
  - P1: Strengthen CI artifacts (coverage, Playwright traces); health endpoint for probes
  - P2: Lead reminders/queue MVP; tags/saved filters; templates
- Environment baseline
  - Ensure MONGO_URI configured for local, CI, and container runtime; unify config via core/settings
  - Keep app bound to port 8004; docker-compose provides Mongo 6
- Delivery approach
  - Feature-flag external integrations (default: mock in CI)
  - Treat “Now / Next / Later” as board columns; map Week 1→Now, Week 2→Next, Weeks 3–4→Later
  - Update this doc and backlog on every review

## What’s live in the repo today
- Application runtime
  - FastAPI app `complete_production_crm:app` (port 8004)
  - JWT auth (demo: demo@mumbai.com / demo123)
  - UI dashboard with Leads and Properties CRUD (browser SPA served from FastAPI)
- Data & storage
  - MongoDB as primary store (fully implemented)
  - Collections: users, leads, properties (ObjectId-based)
- AI features
  - AI localization endpoints: languages/translate
  - Listing templates and generation endpoints
- Social integrations
  - Facebook OAuth flow and page posting endpoints present; WIP after Mongo refactor
- DevEx & QA
  - Pytest with integration tests under `tests/`
  - Playwright UI e2e configured in CI
  - GitHub Actions workflow runs: build, docker-compose (Mongo + app), readiness wait, tests, and artifact logs
  - `scripts/clean.ps1` for cleanup; VS Code tasks wired

## Stakeholders and goals
- Agents (primary users): capture leads quickly, manage properties, post to social, respond faster, close deals.
- Sales Managers: visibility into pipeline, performance dashboards, SLAs.
- Marketing: social publishing, brand consistency, campaign reporting.
- Admin/Compliance: roles/permissions, audit, data retention, PII handling.

## Current architecture (high level)
- Monolithic FastAPI app (modular folders: `app/`, `core/`, `services/`, `repositories/`) + HTML UI served by the app
- Persistence: MongoDB 6 (pymongo, bson ObjectId)
- Auth: JWT (python-jose) with HS256
- Tests: pytest + Playwright; CI via GitHub Actions with docker-compose for Mongo + app
- Config: `.env` via pydantic-settings in `core/config.py`

### Key modules
- `complete_production_crm.py`: primary production app, endpoints and UI
- `db_adapter.py`: Mongo-only adapter, `UserRepository`, hashing (passlib)
- `core/config.py`: settings (MONGO_URI, secrets, FB config)
- `docker-compose.crm.yml`: Mongo + app for CI
- `tests/`: integration for AI, listings, Facebook; UI e2e via Playwright

### Data model (concise)
- users: { _id, email, password_hash, name fields, phone, fb_* fields, timestamps }
- leads: { _id, agent_id, contact info, preferences, status, score, timestamps }
- properties: { _id, agent_id, title, type, location, price, bedrooms, status, timestamps }

## Quality status (as of today)
- Build: passes locally and in CI (Python deps installed; Windows may need VC++ build tools)
- Tests: unit/integration mostly green; Facebook endpoints returning 500 in integration tests
- UI e2e: configured and runs in CI; local Windows may require extra setup

## Known gaps and risks
- Facebook endpoints returning 500 post Mongo migration (user lookup/token/state handling)
- MongoDB implementation completed; all legacy database artifacts removed
- Secrets management (FB keys) not centralized; need secure env handling per environment
- Observability minimal (logs only); no metrics/tracing
- No rate limiting, no DoS protections

## Product backlog (prioritized epics)
1) Finish Mongo-only migration + stabilize Facebook
- MongoDB-only codebase completed
- Fix /api/facebook/config, /pages, /select_page, /post_property to handle empty/first-time states gracefully
- Tests: add happy-path FB mocks and negative cases

2) Agent productivity features
- Smart lead scoring and follow-up reminders
- Tagging/segments, saved filters, bulk actions
- Templates for emails/WhatsApp; quick replies

3) Marketing/social suite
- Facebook end-to-end with page selection and posting history
- Add Instagram (via FB Graph), WhatsApp Business deep link helpers
- UTM tracking and campaign reporting

4) Collaboration & permissions
- Roles: Agent, Manager, Admin; team sharing and approvals
- Activity log/audit trail; immutable history

5) Analytics & dashboards
- Team dashboards, funnels, conversion metrics
- Property performance (views, inquiries)

6) Reliability & ops
- Centralized logging, metrics (OpenTelemetry), health checks
- Rate limiting, input validation hardening, security headers
- Backups and restore playbooks; DR drills

## Near-term roadmap and timelines (indicative)
- Week 1 (Now)
  - Resolve FB 500s (return 200 with connected:false for config; 400 for pages when not connected)
  - Repository cleanup completed; finalize Mongo adapter optimizations
  - Stabilize JWT issuance/verification and add smoke tests
  - Add health endpoint /health for probes
- Week 2 (Next)
  - FB happy-path demo (mocked Graph API; feature flag live calls)
  - Lead reminders + simple follow-up queue (in-app only)
  - CI artifacts for coverage and Playwright video traces
- Weeks 3–4 (Later)
  - Roles & permissions (RBAC) and basic audit trail
  - Analytics MVP (per-agent dashboard cards)
  - Observability: structured logs + minimal metrics

## Technical architecture guardrails
- Modular monolith today; extract services only when scale/teams require
- Strong boundaries: API layer -> services -> repositories -> Mongo
- Config via environment; no secrets in code
- Tests first for contract changes (integration and UI e2e where user-facing)

## Acceptance criteria examples
- Facebook config
  - Given a logged-in agent without FB, GET /api/facebook/config returns 200 {connected:false}
  - When FB is connected (mock), pages list returns 200 with page ids/names
- JWT/auth
  - Invalid token → 401 with {detail:"Invalid token"}; expired → 401 with {detail:"Token expired"}
- Health
  - GET /health returns 200 {status:"ok"}
- Leads
  - Create, list, and dashboard stats update within a second under test conditions

## Non-functional requirements
- Performance: p95 API < 250ms for core endpoints under 100 RPS test
- Security: JWT expiry/refresh, input validation, basic rate limiting
- Availability: target 99.9% for hosted offering (future), with health probes

## RACI / team allocation
- PO/PM: priorities, acceptance, release scope
- BA: user journey mapping, requirements traceability
- Tech Architect: architecture decisions, guardrails, threat modeling
- Eng: implementation, tests, CI/CD
- QA: test plans, automation, regression suite

## Open questions (decision log input)
- FB Graph API: use live keys in non-prod or mock by default?
- Multi-tenant model now or later? (org_id on users/leads/properties)
- Email/SMS provider selection (SES, SendGrid, Twilio)

## Appendix A: endpoints and ports
- App: http://localhost:8004 (complete_production_crm)
- Auth: /api/login, /api/register
- Leads: /api/leads (GET, POST)
- Properties: /api/properties (GET, POST)
- AI: /api/ai-localization/languages, /translate; /api/listings/templates, /generate
- Facebook: /auth/facebook/login, /callback; /api/facebook/config, /pages, /select_page, /post_property/{id}

## Appendix B: environment variables (selected)
- SECRET_KEY, MONGO_URI, FB_APP_ID, FB_APP_SECRET, FB_REDIRECT_URI
- In CI: docker-compose provides Mongo; app listens on 8004

---
This document is the single source of truth for discovery and delivery: update after each planning/review.
