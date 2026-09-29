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
