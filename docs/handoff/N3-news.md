# N3: news presentation (site page, social cards, two-channel publishing, weekly digest, Studio preview)

Approved news no longer goes out as a bare text post with a Google redirect. It now has a page on our own site, a designed card, a Facebook photo post and an Instagram image post, plus a weekly digest. Editorial rules are unchanged and still enforced by `check`; approval still comes first.

## What was built (all under `backend/app/modules/newsroom/` unless noted)
| File | Purpose |
|---|---|
| `presentation.py` | Pure helpers over the stored item: `split_text` (summary / our view / what to check / question / source line / tags), `headline`, `hook` (max 12 words, cut at a clause), `support_line`, `figure`, `as_of_label`, `source_name`, `news_url`, `hashtags` (max 8) |
| `captions.py` | Exact final captions per channel. Facebook: summary, our view, what to check when there is room, `Source: X, as of D`, question, `Read more: <our /news/<id>>` (never the Google link), 5 hashtags, footer. Instagram: same with no URL, `Read more: link in our bio.`, up to 8 hashtags, footer. All under 900 chars. `verify` runs the `check` stage over each final caption |
| `cards.py` | 1080x1350 (`-ig.jpg`) and 1080x1080 (`-fb.jpg`) cards saved under `uploads/news/<id>-...`; digest carousel (cover, a slide per story, tip, closing; max 10). **One of the two files that import `creative`** (drawing kit: Canvas, palettes, bundled photos) |
| `public.py` | `GET /public/news?limit=` and `GET /public/news/{id}`: approved, scheduled or published only; headline, summary, our view, what to check, pillar, areas, source name and link, as-of, card image, Page/Instagram permalinks, disclaimer; no phone numbers |
| `digest.py` | `compose` / `build`: 2 to 5 stories of the last 7 days (max 2 per pillar, most important first) plus an evergreen tip; id `digest-<isoyear>-wNN` (once a week); passes the same `check`; stored as a normal `pending_review` item |
| `preview.py` | What Studio shows before Approve: card URLs, channels, captions, caption problems, dry-run flag |
| `adapters.py` | `SocialPublisher.publish_item(doc)`: Facebook Page photo post + Instagram image/carousel through `GraphPublisher`, each channel recorded separately (`ok`, `id`, `permalink`, `error`, `skipped`, `dry_run`); `render_cards`, `card_stage`, `register_hub` (best effort, `NEWS` subtitle, interest link), `after_publish` |
| `pipeline.py` | optional `cards` stage after check; `_publish` uses `publish_item` when the publisher has it (old text publisher path untouched); partial failure still counts as published; all channels failing marks `failed`; items with a future `scheduled_for` wait (Instagram cannot schedule) and then post on both channels together; daily cap unchanged |
| `router.py` | `GET /queue` now carries `card`, `channels`, `captions`, `caption_problems`, `dry_run`; new `POST /items/{id}/preview` (captions for edited text, nothing saved). Missing cards are drawn on demand (5 per request) |
| `runner.py` | after each cycle, Sunday from 18:00 IST: build the digest (needs at least 2 stories) |
| `samples.py` | 8 realistic review items; `python -m app.modules.newsroom.samples <dir>` renders cards, digest and contact sheet |
| `stages/draft.py` | post drafts now keep the model's headline as `Draft.title` when it is short, not the source headline and adds no capitalised word the source lacks (else the first fact is used). Needed for a good website and card headline |
| `store.py` | `insert_item`, `recent_done`, `public`, `update`, `db` |

Frontend: `app/news/page.tsx`, `app/news/[id]/page.tsx`, `loading.tsx`, `components/news/*`, `lib/news/*` (data, SEO, fixtures); footer link, sitemap `/news`, Navigation hide-list; Studio `components/app/newsroom/PostPreview.tsx`, `QueueCard.tsx` (live caption preview after an edit, Approve blocked while a caption fails), `lib/app/newsroom.ts` (`preview`, `normalizePreview`).

## Wiring snippet (integrator): `backend/app/api/v1/router.py`
```python
from app.modules.newsroom.public import router as newsroom_public_router
api_router.include_router(newsroom_public_router, prefix="/public", tags=["public"])
```
Caddy already routes `/api/*` and `/uploads/*` to the backend. The existing newsroom router (`/newsroom`) already carries the new preview route.

## Settings to turn on
`NEWSROOM_ENABLED=true`, `NEWSROOM_DAILY_CAP` (default 2), `PUBLIC_MEDIA_BASE_URL=https://<site>` (https, used for card URLs on Meta and on the site), `PUBLIC_SITE_URL=https://<site>` (our /news links in captions; falls back to the sslip address), `META_IG_BUSINESS_ID` (turns Instagram on), `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN`, `SOCIAL_DRY_RUN=false` only when ready (start with true: fake ids, no network), `INTEREST_OWNER_AGENT_ID` (hub item and interest link; without it the hub step is skipped). Frontend: `SITE_API_URL` as for /posts.

## Verification
- Backend `tests/modules/newsroom`: 296 passed (new: public, cards, publishing, digest, captions and router). Frontend: `__tests__/news` 17, `__tests__/app/newsroom*` 28 passed; `npx tsc --noEmit` clean. `test_router` route count changed 4 to 5 (preview).
- Visual review in `docs/brand/news-samples/`: `contact-news-instagram.jpg` (8 cards), `contact-news-facebook.jpg`, `digest-carousel.jpg` (8 slides), three single cards, `page-news-390.jpg`, `page-news-item-390.jpg`, `studio-newsroom-preview-390.jpg` (Playwright, system Chrome, 390x844 at 2x; fixtures mode; script `frontend/e2e/news-shots.js`). Review changes that came out of looking: removed support lines that restate the hook, added a dateline, text now shrinks to fit the free band, overlap detection, smaller Studio thumbnails.
- Not tested against the live Meta APIs.

## Deviations and known limits
- The spec said to use creative's `big_number`, `photo_led`, `quote_tip` layouts. Their fixed brand bar cannot carry the source name and as-of date, so `cards.py` draws three news layouts (figure, photo, headline) with creative's Canvas, palettes and photos and the same rule idea (figure when the hook carries a rupee amount or percentage, photo for infrastructure, else typographic). Proposal for creative: a `footer_lines` option on `brand_bar` would let the stock layouts do this.
- Photo cards use bundled generic stock (labelled "Illustrative photo").
- Sitemap lists `/news` only (the existing sitemap function is sync and tested as such); item pages are not listed.
- Interest strip links to `/localities/<area>` and `/go` (the hub item is registered with `NEWS`), not to a per-item `/i/<code>`, because the public API has no code.
- Scheduling: for the two-channel path a chosen time means "stay approved until due, then post both" (no Facebook-side scheduling).
- The digest tip list lives in `digest.py` (six general tips, no figures); its source text is chunked so the copied-words rule does not fire on our own tip.
- Cards are text in English/Latin only (Pillow, as in creative).
