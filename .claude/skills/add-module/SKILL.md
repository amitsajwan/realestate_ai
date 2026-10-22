---
name: add-module
description: Add a new backend domain module, or a new HTTP endpoint to an existing module, following docs/ARCHITECTURE.md. Use when the task adds a feature, collection, or route to backend/app/modules.
---

# Add a module or endpoint

## 1. Place it

- Read `docs/ARCHITECTURE.md` §2 and §4, then pick the **domain** the feature belongs to (identity, inventory, buyers,
  distribution, content, conversations, or apps). If an existing module in that domain fits, extend it rather than
  creating a new one.
- List what it must import. Every import has to point at the same layer or lower (`backend/.importlinter`). If it needs
  something from a higher module, plan a callback that `app/wiring.py` passes in, using `newsroom/pipeline.py` and
  `newsroom/adapters.py` as the pattern.
- If it writes to a collection, confirm this module owns that collection. If another module owns it, call the owner's
  function.

State the domain, the module, and any callbacks in one line before writing code.

## 2. Build it

New module `backend/app/modules/<name>/`:
- `__init__.py`: a docstring saying what the module does and which collection it owns, plus the public names other modules
  may import. Other modules import only from the package, never from its files.
- `config.py` with `load()` if it has settings. No bare `os.environ` reads elsewhere.
- `service.py` (logic, taking `db` as an argument so tests can pass a fake) and `router.py` (`router` for authed routes,
  `public_router` for public ones). Auth comes from `current_active_user`.
- Add the router to `backend/app/api/v1/router.py`: one import and one `include_router` line.
- New module: add it to the right layer in the `domains` contract in `backend/.importlinter`.
- Indexes, if any: `app/core/indexes.py`.

## 3. Test it

- Put tests in `backend/tests/modules/<name>/`. Use the in-memory collections in `tests/modules/fakes.py`, a fixed `NOW`,
  and no network.
- Cover the service logic directly and each route once (status code and response shape), including the unauthenticated case
  for authed routes.
- `tests/test_imports.py` picks the new module up automatically. Make sure it passes.

## 4. Verify (from `backend/`)

```bash
PYTHONPATH=. lint-imports
python -m pytest tests/modules/<name>/ -q
python -m pytest tests/ -q --tb=short
```

If the frontend calls the new route, add the client in `frontend/lib/` and run `npx jest --ci --silent && npm run build` in
`frontend/`.

## 5. Document it

If it adds a domain-level concept or collection, update the ARCHITECTURE §4 table. If it's a product feature, update the
matching `docs/*.md`.
