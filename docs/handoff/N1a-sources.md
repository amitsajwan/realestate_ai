# N1a Sources: handoff

Code: `backend/app/modules/newsroom/sources/` (`google_news.py`, `maharera.py`, `rss.py`, `_util.py`, `__init__.py` with `build_sources`).
Tests: `backend/tests/modules/newsroom/test_sources.py`, `test_sources_maharera.py`; fixtures in `fixtures/sources/`.
Run (venv lives in the main checkout; set PYTHONPATH when running from a worktree):
`PYTHONPATH=backend backend/.venv/Scripts/python.exe -m pytest backend/tests/modules/newsroom -q -c backend/pytest.ini`

## Registry
`build_sources(names, rss_feeds=None)` maps `google_news`, `maharera`, `rss` to instances (order kept, duplicates and unknown names ignored).
`rss` fetches nothing until the runner passes `rss_feeds=[(name, url), ...]`; there is no env setting for feeds yet (integrator to decide, e.g. `NEWSROOM_RSS_FEEDS`).

## Google News
- ~25 queries per run (every AREA_KEYWORDS and CORRIDOR_KEYWORDS phrase, plus four combinations such as `Pune metro Kharadi`), each suffixed `when:14d` (policy.MAX_AGE_DAYS). The runner should keep the 3-hour cadence; one sequential request per query, no concurrency.
- Item url is the `news.google.com/rss/articles/...` redirect link as given; nothing is resolved. id = sha1 of the canonical url. Source is `Google News / <Publisher>`.
- The feed description is only headline + publisher, so `text` is usually just the title. The extract stage therefore has little to quote from; for real facts the pipeline would need the publisher page (not done, out of scope: no network resolving).
- Fixture: the headline/link/pubDate/source of three items were captured from the live feed on 2026-09-30 via WebFetch (which summarises, so description markup and the two broken entries were added by hand to match the known live format).

## MahaRERA (what works, what does not)
- Verified on 2026-09-30: `https://www.maharera.maharashtra.gov.in/projects-search-result` is a public Drupal page, no login or captcha, plain GET with query string, server-rendered HTML, 10 projects per page. `project_state=27` is Maharashtra, `project_district=521` is Pune (12,920 projects at capture time; other guessed ids returned nothing, so 521 was found by probing, not from a documented list).
- Ordering is ascending by registration, so the newest projects are on the last page. The source reads page 0 only to get the total ("Showing Final N Result"), then the last 2 pages (20 projects). No date filter exists on the page, and "Last Modified" (used as `published_at`) is the record's last edit, not the registration date. So an old project that was edited recently can look new; the filter stage's age rule handles staleness but not this. Treat items as "recently listed or updated", and the draft should say "listed on MahaRERA", not "registered today".
- Fields used: registration number, project name, location (MahaRERA gives the taluka or city, e.g. Shirur, Haveli, NOT the locality, so Kharadi/Wagholi keyword matching in the filter will rarely fire on text; pincode is included, Kharadi 411014 and Wagholi 412207 could be matched by the filter stage), district, pincode, last modified, promoter.
- Personal data: promoters can be individuals. The promoter is named only if it looks like an organisation (Ltd, LLP, Builders, Developers, Society, ...); otherwise omitted.
- Detail link `maharerait.maharashtra.gov.in/public/project/view/<n>` is used as the item url (id derived from it). The detail pages and the older `maharerait.mahaonline.gov.in` site were not usable: the mahaonline host refused connections (ECONNREFUSED) from the capture machine, and detail pages are JS/modal driven. No detail data (carpet area, units, completion date) is fetched.
- Robustness: a failed page 0, missing total, changed markup or any exception returns `[]`; a bad card is skipped. Format drift will silently yield zero items, so the runner should log when maharera returns `[]` several runs in a row.
- Fixtures `maharera_pune_first.html` and `maharera_pune_last.html` are the real results region of the live pages (page 0 and page 1291), captured by HTTP GET on 2026-09-30. They contain real public project records (project names, promoter names that are in the public register).

## Generic RSS
`RssSource([(name, url)])`: RSS 2.0 and Atom, bad entries skipped, malformed document gives `[]`, tracking params stripped, de-duplicated by canonical url across feeds. Fixtures are hand-written samples.

## Tests
12 passing, no network. Note that pytest from the repo root needs `PYTHONPATH=backend` (and `-c backend/pytest.ini` for asyncio auto mode); the contract's bare command may need that adjusting.
