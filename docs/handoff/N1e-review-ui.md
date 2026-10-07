# Handoff: N1e (Newsroom review UI)

Implements the HTTP API section of `docs/contracts/newsroom.md` (queue, status, approve, reject). Built against fixtures; no backend needed.

## What shipped
- `frontend/app/studio/newsroom/page.tsx`: status strip, queue cards, empty state, disabled banner, error with retry. Approved or rejected cards leave the list and the "to review" count drops.
- `frontend/components/app/newsroom/`: `StatusStrip`, `QueueCard` (editable draft, schedule picker, reject reason), `CheckResult`, `FactsList` (collapsed).
- `frontend/lib/app/newsroom.ts`: types, `createNewsroomApi` (own small fetch client, bearer token, `ApiError`), `newsroomApi` (fixture mode aware via `isFixtureMode()`), `normalizeItem`, fixtures (`FIXTURE_QUEUE`, `FIXTURE_STATUS`, `createFixtureNewsroomApi`).
- `frontend/__tests__/app/newsroom.test.tsx`: 18 tests.

## Request behaviour
- Approve sends `{}` when unedited, `{text}` when edited (card says it will be re-checked), `{when}` as ISO (UTC) when a time is picked; empty time means the backend's next slot.
- Reject sends `{reason}` or `{}`. A failed call keeps the card and shows the error (403 owner only, 404/409 already handled, else the server detail).

## Assumptions to confirm with the backend (contract is loose)
- `facts` is `[{text, quote}]` (as `types.Fact`); `check` is `{ok, problems[]}`; `draft` is a string (an object with `text` is tolerated); `sources` is `[{name, url}]` (plain strings tolerated).
- `pillar` slugs: `infrastructure`, `new_supply`, `rules_money`, `locality`, `education`, `digest` (others are prettified).
- Approve of a draft whose check failed is not blocked in the UI; the backend re-check decides and its error is shown.

## Owner gating
There is no owner flag in the frontend session; the Interest tab is also shown to every Studio user. The tab is added the same way, and the backend enforces owner only: a 403 shows "The newsroom is only for the owner." If an `is_owner` flag is added to the session, filter this tab in `AppShell.tsx`.

## Edits outside owned paths
- `frontend/components/app/AppShell.tsx`: one line, the Newsroom tab (5 tabs now).
- `frontend/lib/app/strings.ts`: one line, `newsroom: 'Newsroom'` (the tab label goes through `t()`).

## Tooling notes
- `npx tsc --noEmit`: clean.
- `next lint` / eslint is broken in this repo independent of this change (eslintrc circular-config error; ESLint 9 wants a flat config), so lint could not run.
- Jest from a path containing `.claude/worktrees` finds no tests because the default ignore patterns match; run with `--testPathIgnorePatterns=NOPE --testMatch '**/__tests__/app/*.test.{ts,tsx}'` in a worktree. In the normal checkout `npx jest` works.
