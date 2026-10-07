# N1b Understand: filter and extract

Built: `newsroom/stages/filter.py` (`assess`, `same_story`) and `stages/extract.py` (`extract`). No imports beyond `newsroom.types` and `newsroom.policy`.

## filter.assess (no LLM)
Order: stale (publish date, else fetched_at, more than MAX_AGE_DAYS) then off-topic (no AREA_KEYWORDS hit and no CORRIDOR_KEYWORDS hit together with a PUNE_HINT), then non-news: horoscope, classified or phone number, crime (in title, or 2+ distinct crime words), hype (BANNED hit plus a promo phrase, or 2+ BANNED hits). Matching is word-boundary, so "Kharadian" or "Kharadigaon" do not count. Pillar: title hits weigh 2, body hits 1, default `locality_life`. `Relevance.reason` starts with `stale`, `off-topic`, or `non-news` on drops. Naive datetimes are treated as UTC.
Note "upper kharadi" text yields both `kharadi` and `upper_kharadi` in `areas`.

## filter.same_story
Normalised titles (publisher suffix removed, stop words dropped): true when Jaccard >= 0.6, or sequence ratio >= 0.85, or >= 5 shared tokens with overlap >= 0.75. The orchestrator should compare a new item to recent titles and drop it as a duplicate (status `dropped`, note "duplicate of <id>").

## extract.extract
One JSON prompt (`SYSTEM`). Code keeps a fact only if: quote is >= 12 chars and a substring of the whitespace- and curly-quote-normalised text or title; every number in the fact text (commas ignored) appears in its quote. Duplicate quotes removed, cap 6, `as_of` = published_at else fetched_at. None on LLM exception, junk, or no surviving facts. Only the first 6000 chars of the body are sent.

## Tests
`backend/tests/modules/newsroom/test_filter.py`, `test_extract.py`, 15 fixtures in `fixtures/articles/*.json` (each carries an `expect` block). Run from repo root with `PYTHONPATH=backend`: `PYTHONPATH=backend backend/.venv/Scripts/python.exe -m pytest backend/tests/modules/newsroom -q` (without it `app` is not importable from a worktree). 38 pass.

## Proposals (not applied)
- `Relevance.reason` could carry a machine code (`stale`, `off_topic`, `non_news`) separately from prose.
- `same_story` could live in policy or a shared util if the orchestrator and sources both need it.
- Contract doc: add that quotes are compared after whitespace and typographic-quote normalisation, and that fact numbers must appear in their quote.
- Policy: add crime/horoscope/classified patterns to `policy.py` so editors can tune them; they are private regexes in `filter.py` for now.
- `PILLAR_KEYWORDS` has no `education` entry, so that pillar is never chosen by the filter (only by another path).
