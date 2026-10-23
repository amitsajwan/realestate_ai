---
name: add-background-loop
description: Add a recurring background job (a worker loop) to the backend, with its lease, heartbeat, worker role and health check. Use when work must run on a schedule or drain a queue rather than inside a request.
---

# Add a background loop

Loops are status machines stored in Mongo and run by `python -m app.worker`. Don't add Celery, Temporal, or a new job
framework (ARCHITECTURE §6).

## 1. Write the loop in its module

In `backend/app/modules/<module>/runner.py` (or `jobs.py`):
- Write an `async def loop()` that runs forever: do one cycle, then sleep `INTERVAL_S`. Expose `INTERVAL_S` (or
  `POLL_SECONDS`) as a module constant.
- Make it switchable from config with an `enabled()` or a `config.load().enabled` flag, off by default when it calls a
  paid or external service.
- Wrap each cycle in `app.platform.heartbeats.heartbeat(name, get_database)` so `last_ok_at`/`last_error_at` get recorded.
  A failed cycle logs the error and carries on with the next one. It never kills the loop.
- Keep each cycle idempotent: pick up work by status, move it to the next status, and leave it safe to re-run after a crash.
  Anything it publishes goes through `social.distribution.send`.
- Don't take a lease yourself. The worker runs every loop under `run_as_leader`.

## 2. Register it in `backend/app/worker.py`

1. Add the name to `ALL_LOOP_NAMES`.
2. Add it to exactly one role in `ROLE_LOOPS`: `conversations` for replies and messaging, `newsroom` for content and data
   refresh, `media` for CPU-heavy rendering.
3. Add `name: loop` in `loops()`. The import inside the function is the established pattern there.
4. Add its interval in `expected_intervals()`, returning `None` when config switches it off, so `--check` doesn't alert on it.

## 3. Test it

- Test one cycle directly against `tests/modules/fakes.py` collections, with a fixed `NOW`: work in the right status gets
  picked up, finished work isn't redone, and an error in one item doesn't stop the others.
- Check that `backend/tests/test_worker.py` still passes, and extend it if it lists loop names or roles.

## 4. Verify (from `backend/`)

```bash
PYTHONPATH=. lint-imports
python -m pytest tests/test_worker.py tests/modules/<module>/ -q
python -m pytest tests/ -q --tb=short
python -m app.worker --role <role> --check      # needs a Mongo; skip and say so if none is available
```

## 5. Document it

Add the loop to the role list in `docs/ARCHITECTURE.md` §1 and add any new env flag to `docs/operator/OPERATOR_GUIDE.md`.
