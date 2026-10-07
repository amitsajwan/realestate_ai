# N2c Article reader handoff

`backend/app/modules/newsroom/stages/read.py`: optional stage that appends an article's main text to `RawItem.text` when the source gave only a headline and a line, so `extract` has something to quote.

## Use
- Off by default. Set `NEWSROOM_READ_ARTICLES=true` (`NewsroomConfig.read_articles`) and `default_stages()` registers `read` (with one shared `RobotsCache` and a 2 s per-host `polite_get`).
- `pipeline._extract` calls `stages["read"](raw, stages["get"])` when both exist, persists changed text via `Store.update_raw(id, text)` (status and history untouched), then extracts. A reader exception is logged and ignored.
- API: `read(item, get, robots=None)`, `RobotsCache`, `polite_get(get, min_gap_s, clock, sleep)`, `main_text(html)`.

## Rules
Enrich only if: text < 300 chars; URL is not news.google.com (Google News redirects are skipped, no request); robots.txt allows agent `PunePropertyNewsroom`; page yields >= 400 chars of main text. Otherwise the same item object is returned. If body extraction fails but `og:description` / `meta description` adds something not already in the text, that (max 600 chars) is appended.
Extraction: paragraphs inside `<article>` when >= 400 chars, else the densest group of sibling `<p>`s. Dropped: script, style, nav, aside, footer, header, form, iframe, buttons, and any element whose id/class/role looks like comments, cookie/consent, newsletter/subscribe, sidebar, related, share, promo, paywall. Short paragraphs (<= 250 chars) with cookie/subscribe/sign-in/read-more style phrases are removed. Capped at 6000 chars on a sentence boundary.

## Tests
`tests/modules/newsroom/test_read.py` (22 tests; 163 pass in the folder), fixtures in `fixtures/pages/`: clean article, nav heavy, paywall teaser, cookie banner, og-description only. Covers robots allow/disallow/error/404/cache expiry, google skip, 300 threshold, politeness with a fake clock, pipeline wiring and crash isolation.

## Limits
- Static HTML only: JS-rendered pages (empty shell) yield nothing or only the og description.
- Paywalls: only the free teaser is seen; if under 400 chars the item is unchanged. No paywall or login bypass is attempted.
- Robots: a fetch error fails closed; 404/410 (detected via `exc.response.status_code`, as httpx raises) counts as no robots.txt. A fetcher that hides status codes will block those hosts.
- Densest-block heuristic can pick a related-stories list on odd layouts; `check` still requires quotes to be verbatim from the stored text.
- Politeness is per-process (in-memory); the robots cache lasts 1 hour.

## Copyright and ethics
Text is used only internally so `extract` can quote short factual sentences; drafts are our own words with attribution and a link to the source, and the stored raw text is not published. We identify ourselves (`PunePropertyNewsroom/1.0`), obey robots.txt, rate limit per host, fetch one page per item only when needed, cap the amount kept, and skip comments (user content), paywalled and Google-redirect URLs.
