# Contract: newsroom

Owner of this file and of `backend/app/modules/newsroom/types.py`, `policy.py`: the integrator. Streams may propose changes, not make them.
Design and editorial rules: `docs/NEWSROOM_PLAN.md`.

## Stage signatures (pure: no database, no network except the injected ports)
| Module | Signature | Notes |
|---|---|---|
| `sources/<name>.py` | `class X: name: str; async def fetch(self, get: Fetcher) -> list[RawItem]` | Uses only `get(url)`. Never raises for one bad entry: skip it. Stable `id`. |
| `stages/filter.py` | `def assess(item: RawItem, now: datetime) -> Relevance` | Keyword/rules based, no LLM. Drops items older than `policy.MAX_AGE_DAYS`, off-topic items, duplicates of the same story title. |
| `stages/extract.py` | `async def extract(item: RawItem, llm: Llm) -> Optional[Facts]` | JSON from the LLM; every `Fact.quote` must be a verbatim substring of the item text or title, else the fact is discarded. None if no facts survive. |
| `stages/draft.py` | `async def draft(item: RawItem, facts: Facts, relevance: Relevance, fmt: str, llm: Llm) -> Optional[Draft]` | Own words, source attribution and link, ends a post with a question. Uses `policy` for tone and formats. |
| `stages/check.py` | `def check(draft: Draft, facts: Facts, item: RawItem) -> CheckResult` | Code, no LLM. Every number, date and proper noun in the draft is in the source text. Rejects predictions, hype (`marketing.polish.HYPE`), phones (`PHONE`), copied runs of more than 15 words, missing source or link, stale items. |
| `policy.py` | constants and small pure helpers | `MAX_AGE_DAYS`, `KEYWORDS` per area and pillar, `BANNED`, `FORMATS_BY_PILLAR`, `DISCLAIMER`, `DAILY_CAP`. |

## Store (only `store.py` touches Mongo; collection `newsroom_items`)
Document: `_id` (= RawItem.id), `status` (see `STATUSES`), `raw` (RawItem fields), `relevance`, `facts`, `draft`, `check`, `history` (list of `{at, status, note}`), `review` (`{by, at, edits}`), `publish` (`{platform_id, scheduled_for}`).
```
class Store:
    async def add_new(items: list[RawItem]) -> int                      # skips ids already present
    async def next_batch(status: str, limit: int) -> list[dict]
    async def move(id: str, status: str, note: str = "", **fields) -> None   # appends to history
    async def queue(limit: int = 50) -> list[dict]                     # status pending_review, newest first
    async def counts() -> dict[str, int]
```

## HTTP API (owner only, prefix `/api/v1/newsroom`)
| Method and path | Purpose |
|---|---|
| `GET /queue` | items pending review: `[{id, title, pillar, areas, draft, facts, check, sources, age_days}]` |
| `GET /status` | `{enabled, counts, last_run_at, last_error}` |
| `POST /items/{id}/approve` | body `{text?: string, when?: iso}` (edited text allowed; re-checked) |
| `POST /items/{id}/reject` | body `{reason?: string}` |
| `GET /public/insights` (no auth) | published articles: `[{slug, title, summary, updated, sections, sources}]` (N2) |

## Settings (env, all default off or safe)
`NEWSROOM_ENABLED=false`, `NEWSROOM_INTERVAL_SECONDS=10800`, `NEWSROOM_DAILY_CAP=2`, `NEWSROOM_SOURCES=google_news,maharera`.

## Rules for every stream
- Import only from `newsroom.types`, `newsroom.policy` and the standard library or already-installed packages (httpx, feedparser only if already in requirements; otherwise parse with the standard library `xml.etree`).
- No imports from `engage`, `chat`, `listings`, `onboarding`. `marketing.polish` (HYPE, PHONE) may be imported by `stages/check.py` only.
- Tests live in `backend/tests/modules/newsroom/` (or `frontend/` for the UI), use recorded fixtures under `backend/tests/modules/newsroom/fixtures/`, no network.
- Run: `backend/.venv/Scripts/python.exe -m pytest backend/tests/modules/newsroom -q` (from the repo root; adjust if the venv path differs).
- Files under about 300 lines; one handoff note in `docs/handoff/<stream>.md`.
