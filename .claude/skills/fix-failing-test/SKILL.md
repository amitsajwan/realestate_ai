---
name: fix-failing-test
description: Diagnose and fix a failing backend or frontend test, or a red CI job, by reproducing it and finding the root cause. Use when a test, lint-imports, jest, or the Next build fails.
---

# Fix a failing test

## 1. Reproduce first

Run the exact failing command locally, as CI runs it (`.github/workflows/architecture.yml`, `ci.yml`):

```bash
cd backend && python -m pytest <path>::<test> -q --tb=long     # or: PYTHONPATH=. lint-imports
cd frontend && npx jest <path> --ci                           # or: npm run build
```

If it passes locally, compare against CI: Python 3.11 / Node 22, environment variables, test order (run the whole file and
then the whole suite), and dates (look for code that reads the real clock).

## 2. Find the root cause

- Read the assertion and the code under test. Decide which side is wrong: did the behaviour change on purpose (so the test is
  stale), or did a change break it (so the code is wrong)?
- `git log -p -S'<symbol>'` and `git log --oneline -- <file>` show what changed recently.
- Usual causes in this repo:
  - a module moved and a function-level import now points at nothing (`tests/test_imports.py`)
  - an upward import (`lint-imports` names the chain)
  - `wiring.py` not passing a callback
  - a fake in `tests/modules/fakes.py` missing a Mongo operator
  - a test relying on the real clock instead of a fixed `NOW`
- "Flaky" isn't a root cause. Find what makes it nondeterministic.

## 3. Fix the smallest thing that's actually wrong

- If the code is wrong, fix the code. If the test is stale because behaviour changed on purpose, update the assertion and
  say why in the commit.
- Never skip a test, mark it xfail, add it to `collect_ignore`, loosen an assertion to make it pass, or add a line to
  `ignore_imports`.
- If the fix needs a missing Mongo operator, add it to `fakes.py` matching Mongo's real semantics.
- Don't refactor unrelated code in the same change.

## 4. Verify

Re-run the originally failing command and show it passing. Then run the full checks for the side you touched:
`PYTHONPATH=. lint-imports && python -m pytest tests/ -q --tb=short` (backend), or `npx jest --ci --silent && npm run build`
(frontend). Report the before and after output and anything you could not reproduce.
