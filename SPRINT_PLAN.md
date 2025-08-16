# Tech Debt Sprint Plan (2 Weeks)

## Goals
- Reduce technical debt across code, tests, and docs
- Modularize foundations (without breaking current CRM on 8004)
- Establish team processes: reviews, naming, docs, CI linting

## Team & Roles
- Backend (4): API, data layer, services, tests
- UI (3): Dashboard, components, client JS cleanup
- UX (1+): Flows, accessibility, microcopy, consistency
- Project Manager: Planning, standups, blockers
- Product/Program Manager: Scope, acceptance, priorities

## Cadence
- Daily standup (15 min), Slack updates by EOD
- Code review SLA: < 24h; at least 2 approvals for risky/behavioral changes
- Demo: end of Week 2; PM sign-off on acceptance criteria

## Backlog (high-level)
- Architecture & code structure
  - Extract templates/static from `complete_production_crm.py`
  - Introduce app modules: routes, services, repositories, schemas
  - Add server-side auth guard for HTML routes
- Testing
  - Finalize tests/ layout; migrate root tests gradually
  - Add API unit tests for leads/properties MongoDB paths
  - Expand Playwright E2E smoke; wire into CI (phase 2)
- Quality gates
  - Add ruff/black/isort configs; optional CI checks (non-blocking at first)
  - Add EditorConfig; enforce naming conventions
- Documentation
  - CONTRIBUTING, CODEOWNERS, PR/Issue templates
  - Architecture overview + ADR-0001 (modularization)
  - TESTING.md, NAMING_CONVENTIONS.md
- DevOps
  - Keep docker-compose.crm.yml canonical; add health checks
  - Prep for adding pytest in CI after stabilizing tests

## Deliverables & Acceptance Criteria
- App still runs: http://localhost:8004, demo login works
- Lint configs present; CI runs optional lint checks
- New docs in repo root and .github; CODEOWNERS active
- `tests/` hierarchy in place with wrappers
- Architecture doc + ADR-0001 merged

## Assignments (suggested)
- Backend Dev A/B: repositories/services split & tests
- Backend Dev C: auth guard + leads/properties API parity
- Backend Dev D: DB adapter enhancements + migrations doc
- UI Dev A/B: extract inline JS/CSS; components cleanup
- UI Dev C: Playwright test stabilization
- UX: audit flows; propose small, high-impact fixes
- PM: track burndown; unblockers
- P/PM: Acceptance criteria & scope tradeoffs

## Timeline
- Week 1: configs, docs, test structure, start modular skeleton
- Week 2: migrate selective routes/templates; finish docs; demo + sign-off

---

# Execution Checklist
- [ ] Lint configs added and CI optional checks
- [ ] CONTRIBUTING, CODEOWNERS, PR/Issue templates
- [ ] Architecture + ADR-0001
- [ ] tests/ structure finalized; wrappers ready
- [ ] Modular app skeleton created (no breakage)
- [ ] Demo & sign-off
