# Avasetu (realestate_ai)

Real estate platform for Pune agents and buyers. A FastAPI + MongoDB backend built as a modular monolith (`backend/`) and two
Next.js 16 / React 19 apps on one address: the public site (`frontend/`) and Studio, the agents' app (`studio/`). The architecture we're moving to is `docs/ARCHITECTURE.md` and the steps to get
there are `docs/MODERNIZATION.md`. Read those two before any structural change. Operating and deploying: `docs/operator/OPERATOR_GUIDE.md`.
SEO and AI search (what runs, the owner's upkeep, the plan): `docs/plan/seo-system.md`, kept current in the same commit as any SEO change.

## Commands

CI runs exactly these (`.github/workflows/architecture.yml`, `ci.yml`). Run them before calling work done.

Backend, from `backend/` (Python 3.11):
```bash
pip install -r requirements.txt pytest pytest-asyncio import-linter==2.15
PYTHONPATH=. lint-imports                        # import rules (backend/.importlinter)
python -m pytest tests/ -q --tb=short            # full suite; no Mongo needed (tests use tests/modules/fakes.py)
python -m pytest tests/modules/<module>/ -q      # one module while iterating
```

Public site, from `frontend/`, and Studio, from `studio/` (Node 22; the same commands in each):
```bash
npm ci --no-audit --no-fund
npx jest --ci --silent                           # unit tests (__tests__/)
npm run build                                    # also the type check
```
A change to `shared/` needs both.
`npm run lint` (`next lint`) does not work on Next 16, so don't use it to check your work. Playwright e2e (`npm run test:e2e`)
needs a running app and only runs when started by hand.

Run locally: `docker compose -f docker-compose.dev.yml up`, or the backend with `uvicorn app.main:app --reload` (from
`backend/`) plus `npx next dev --webpack` in `frontend/` (port 3000) and in `studio/` (`-p 3001`). Open everything through
port 3000: the site forwards `/studio` and `/join` to Studio. (Plain `npm run dev` uses Turbopack, which rejects the Tailwind
CSS today.) Background loops: `python -m app.worker --role <conversations|newsroom|media>`.

## Repo map

- `backend/app/platform/`: shared building blocks with no business knowledge (llm gateway, meta_graph, media, text, controls,
  leases, heartbeats). It must never import `app.modules`.
- `backend/app/modules/<name>/`: the domains. Each one is a package whose `__init__.py` is its public API, with routers in
  `router.py`.
- `backend/app/wiring.py`: the composition root. A lower module that needs something from a higher one gets a callback here.
- `backend/app/worker.py`: the background loop table and worker roles.
- `backend/app/{api,routers,services,repositories,schemas}`: **the old layer**. Don't add to it. New code goes in `modules/`.
- `backend/tests/modules/<name>/`: tests sit with their module. `tests/modules/fakes.py` holds the in-memory Mongo stand-ins.
- `frontend/app/`: the public site's App Router pages. `frontend/components/`, `lib/` and `__tests__/` are what they sound like.
- `studio/`: Studio (`/studio/*` and its sign-in `/join`), its own Next.js app, image and container (ARCHITECTURE §9). Screens in
  `studio/app/studio/`, components in `studio/components/app/`, API client and rules in `studio/lib/app/`.
- `shared/`: plain TypeScript both apps import as `@shared/*` (brand, site types, localities, Studio's strings, the login token).
  No React, no Next, only relative imports inside it.
- `deploy/gcp/`: the production deploy. Older scripts at the repo root (`deploy*.sh`, `*.ps1`, ngrok files) don't match production.

Don't touch:
- `frontend/AGENTS.md` (`next dev` writes it)
- `.env*` files with real values
- `frontend/package-lock.json` except through npm
- `docs/archive/`

## Rules that CI or reviewers enforce

1. **Layers.** Imports go `apps > domains > platform`. Between domains the order is
   `identity < inventory < buyers < distribution < content | conversations`. `content` and `conversations` never import each
   other. To use something from above, take a callback that `wiring.py` passes in. There's no event bus.
2. **Import baseline only shrinks.** Never add a line to `ignore_imports` in `.importlinter`. Fix the import instead.
3. **No function-level imports to dodge a cycle.** They're allowed only for heavy optional libraries (ffmpeg, vision).
   `tests/test_imports.py` resolves every one of them.
4. **One writer per collection.** Only the module that owns a collection writes to it (ARCHITECTURE §4 table). Other modules
   read through its query functions.
5. **Config comes from the settings objects.** Don't add new `os.environ` reads in modules. Use the module's `config.py`
   `load()` or `app.core.config`.
6. **Publishing goes through `social.distribution.send`** (idempotency ledger, pause switches). No AI agent ever publishes.
   Dry run is the default outside production.
7. **AI output is guarded.** Rules come before the model, every output gets checked (`platform.text` copy guards), and when
   the model fails there's a deterministic fallback.
8. **Moves are separate from fixes.** When code moves, pin its behaviour with tests first, leave a shim at the old path, and
   don't change behaviour in the same commit.
9. **Login (`core/auth_backend.py`) is not rewritten.**
10. **The site and Studio do not import each other.** What both need goes in `shared/` as plain TypeScript. A link from one app
    to a page of the other is a plain `<a>`, never Next's `<Link>`.

## Conventions

- Python: `log = logging.getLogger(__name__)`, type hints on public functions, and async Motor calls throughout.
- Tests: plain `pytest` functions named after the behaviour (`test_bookings_are_homes_sold_inside_the_window`), fixed `NOW`
  datetimes instead of the clock, and fakes rather than mocks of Mongo. No network: stub `httpx`.
- Docstrings and comments: plain sentences saying *why*, in the voice of the surrounding file.
- Commit subjects describe behaviour in plain English ("Hot banner reads agent-listed slugs with a 5-minute cache"), not
  `feat:` prefixes.

## Definition of done

- `lint-imports` passes and the full backend suite passes (and jest + build in `frontend/` or `studio/`, whichever changed;
  both if `shared/` changed).
- A new behaviour has a test, and a bug fix has a test that failed before the fix.
- No test was skipped, weakened, or added to `collect_ignore` to get green.
- The relevant doc (ARCHITECTURE / MODERNIZATION progress log / module doc in `docs/`) is updated if the shape changed.
- Your final message lists what you ran, what passed, and anything you could not verify.

## Skills

The procedures live in `.claude/skills/`: `add-module` (a new domain module or endpoint), `add-background-loop` (a worker
loop), `fix-failing-test`, `deploy` (a push to `main` goes live by itself once its images and both test runs are green;
deploying or rolling back by hand; checking a release), `seo-upkeep` (SEO and AI-search health, a ranking drop, any SEO
change).
