# Contributing

## Branching
- main: stable
- feature/*: new features
- fix/*: bug fixes
- chore/*: docs, ci, lint

## Pull Requests
- Link issues; use PR template
- Include tests for behavior changes
- At least 1 approval (2 for risky changes)

## Code Style
- Python: black, isort, ruff (to be added)
- JS/TS: prettier/eslint (UI subprojects)
- EditorConfig enforced

## Testing
- Unit tests in tests/unit
- Integration/E2E in tests/integration
- Keep CI smoke tests green

## Docs
- Update README, CODEMAP, USER_MANUAL when public behavior changes
- Add/Update ADRs for architectural decisions
