# Scrum board

Product owner: Amit. Integrator/scrum master: Claude (main session). Developers: parallel Claude agents, one per stream, each in its own git worktree and branch.

## Working agreement
- Branch per stream `v2/<stream>`; integrator merges to the current branch after review. No pushes.
- Directory ownership per stream (below). Shared files (`backend/app/api/v1/router.py`, `docs/contracts/*`) are edited only by the integrator.
- Definition of done: tests written and passing (`backend/.venv/Scripts/python.exe -m pytest` for backend; `npx tsc --noEmit` and lint for frontend), no file over ~400 lines, owner/tenant scoping tested, a handoff note in `docs/handoff/<stream>.md`.
- Assumptions taken (change any by telling the PO): mobile web app first; placeholder domain; pilot city Pune; Indian numbers only; AI output always confirmed by the agent.

## Sprint 1 goal
An agent signs up with a phone number, gets a live site, posts a listing from typed or spoken text, and an enquiry shows up as a scored lead in their inbox. (Mobile web, dev environment.)

| Stream | Story | Owns | Depends on |
|---|---|---|---|
| S1 Listings backend | Create/edit/publish listings with lifecycle; public listing endpoints | `backend/app/modules/listings/`, `backend/tests/modules/test_listings*.py` | contracts/listing.md |
| S2 AI listing draft | Turn typed or spoken text (and image count) into an AIDraft | `backend/app/modules/ai_listing/`, `backend/tests/modules/test_ai_listing*.py` | contracts/listing.md |
| S3 Public agent site | Server-rendered site, listing pages, tracking beacon, enquiry form | `frontend/app/agent/` (replace the existing tree in place), `frontend/components/site/`, `frontend/lib/site/` | onboarding, tracking, listing public API |
| S4 Agent app | Phone login, create-site, add listing (type/voice), lead inbox | `frontend/app/join/`, `frontend/app/studio/` (agent app at /studio), `frontend/components/app/`, `frontend/lib/app/` | onboarding, tracking, listings, ai draft |
| S0 Integrator | Router wiring, Docker/Mongo e2e, merges, contract changes | shared files | all |

## Backlog after Sprint 1
Distribution (IG/FB/WhatsApp) with tracked links (needs Meta/WhatsApp approvals - start applications now) · notifications · listing freshness job and per-listing activity page · marketplace pool (dedupe, search, intro requests) · conversations (comments/DMs) · AI concierge (suggested replies first) · billing/boosts.

## Risks
Meta/WhatsApp approvals (weeks) · AI extraction quality on Hinglish · legacy code tangle (contained by new modules) · real-Mongo verification pending (Docker Desktop not running locally).

---

# Sprint 2: Newsroom (content agent) + hardening

Plan: `docs/NEWSROOM_PLAN.md`. Contract every stream codes against: `docs/contracts/newsroom.md` (types in `backend/app/modules/newsroom/types.py`, policy in `policy.py`).
Same working agreement as Sprint 1: one git worktree and branch `s2/<stream>` per stream, disjoint directories, integrator (Claude main session) merges and owns shared files, no pushes, tests and a handoff note in `docs/handoff/<stream>.md` before "done".

## Sprint goal
Drafts built from real Kharadi/Wagholi news and MahaRERA registrations appear in the owner's review queue, every draft has passed the code checks, and an approved draft is scheduled to the Page. Nothing publishes without approval.

## Board

| ID | Stream | Story | Owns (only these paths) | Depends on | Status |
|---|---|---|---|---|---|
| N0 | Integrator | Contract, shared types, policy, board | `docs/contracts/newsroom.md`, `newsroom/types.py`, `newsroom/policy.py`, shared routers | - | Done |
| N1a | Sources | Google News RSS, MahaRERA, generic RSS source plugins with recorded fixtures | `newsroom/sources/`, `tests/modules/newsroom/test_sources*.py`, `tests/modules/newsroom/fixtures/sources/` | N0 | Done |
| N1b | Understand | `filter.assess` and `extract.extract` with golden and adversarial tests | `newsroom/stages/filter.py`, `stages/extract.py`, their tests and fixtures | N0 | Done |
| N1c | Write and verify | `draft.draft` and `check.check` (the safety net) with adversarial tests | `newsroom/stages/draft.py`, `stages/check.py`, their tests | N0 | Done |
| N1d | Plumbing | `Store`, runner loop, router (queue/status/approve/reject), adapters to the social Publisher and LLM, settings, scheduler port | `newsroom/store.py`, `runner.py`, `router.py`, `adapters.py`, their tests | N0 | Done |
| N1e | Review UI | Studio "Newsroom" tab: queue cards, edit, approve, reject, status, against the HTTP contract with fixtures | `frontend/app/studio/newsroom/`, `frontend/components/app/newsroom/`, `frontend/lib/app/newsroom.ts` | N0 | Done |
| P1 | Ops (parallel, unrelated) | Nightly Mongo backup with restore test, uptime and token health alert script, runbook update | `deploy/gcp/backup*`, `deploy/gcp/health*`, `docs/PILOT_RUNBOOK.md` (ops section only) | - | Done |
| N1f | Integrate | Wire router and runner, end-to-end run on fixtures, deploy with `NEWSROOM_ENABLED=false`, dry-run on the VM, first real drafts | shared files | N1a to N1e | In progress: wired, integration test passing; deploy (off) and dry-run next |

## Next sprint candidates (not started)
N2 database-backed articles on `/insights` · N3 weekly digest and reaction learning · N4 more sources and auto-publish for low-risk types · Instagram once the account is Professional · Reels · Hindi/Marathi variants · domain purchase and first 3 pilot agents (owner actions in `docs/AGENT_INVITE_KIT.md`).

## Definition of done (every story)
Tests written first or alongside and passing · no network in tests · no file over about 300 lines · only owned paths changed · no secrets or phone numbers in fixtures · handoff note written.
