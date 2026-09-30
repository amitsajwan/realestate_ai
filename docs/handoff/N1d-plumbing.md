# N1d Plumbing handoff

Built under `backend/app/modules/newsroom/`: `store.py`, `config.py`, `pipeline.py`, `runner.py`, `adapters.py`, `router.py`, plus a small pure `codec.py` (stored doc <-> dataclasses). Tests in `backend/tests/modules/newsroom/` (30 pass; `helpers.py` holds shared fakes).

## Wiring (integrator)
```python
# backend/app/api/v1/router.py
from app.modules.newsroom.router import router as newsroom_router
api_router.include_router(newsroom_router, prefix="/newsroom", tags=["newsroom"])

# app startup/lifespan, next to the engage loop
from app.modules.newsroom import runner as newsroom_runner
tasks.append(asyncio.create_task(newsroom_runner.loop()))   # idle unless NEWSROOM_ENABLED=true
```
Posting really needs SOCIAL_DRY_RUN=false, META_PAGE_ID, META_PAGE_ACCESS_TOKEN (dry run returns a fake `dry-run-...` id).

## Behaviour notes
- Pipeline moves items by status: new -> relevant|dropped -> extracted|dropped -> drafted|dropped -> checked -> pending_review; failed check = `dropped` with problems in history and `check`. Approved -> `scheduled` (future time) or `published`.
- `stages` dict keys: `filter, extract, draft, check`, optional `get` (Fetcher for sources; runner supplies an httpx one). Filter and check may be sync or async.
- No LLM key => extract/draft wait (items stay put). No publisher => nothing published.
- Daily cap = rolling 24h count of scheduled/published items (`published_at`); extras stay `approved`. Approved `when` under 10 min ahead publishes now; over 30 days ahead fails the item.
- `runner.load_sources(names)` imports `newsroom.sources.<name>` and uses `SOURCE`, `build()`, or the first class with `fetch`. Source streams should follow one of those.
- Router auth is `current_active_user` like engage (any signed-in user).

## Proposed contract changes
1. Owner-only: any active user can approve posts to the Page. Propose `current_superuser` or an `NEWSROOM_OWNER_IDS` allow-list on these routes.
2. Add `Store.published_since(dt)`, `get(id)`, `set_run`, `get_run` to the contract (extras beyond the five listed).
3. Specify how sources are exported (`SOURCE` / `build()`), and that `RawItem` datetimes are timezone-aware UTC.
4. `dropped` is used for check failures and `rejected` only for owner rejections; document it.
5. Known gap: if the process dies between a successful Facebook post and the status update, the item would be retried and double posted. Facebook has no idempotency key; acceptable at 2 posts a day, but worth a "publishing" status later.
