# SEO: every post and story findable, all linked to the area pages (2026-10-04)

## Why
Google Search Console is set up for avasetu.in, but the sitemap has 44 URLs. Our daily posts and reels have no page of their own
(only the /posts feed), news URLs are hashes (`/news/f5ddeef0…`), and the home page links only to /localities, not to the 8 area
pages. Buyers search by area ("2 BHK Wagholi", "Hinjawadi projects"), so the area pages are the hubs: posts, news and projects
link to their area page, and the area page links to them.

## Rules
- Same content rules as docs/plan/pune-areas.md: facts only with sources, no invented prices or claims, MahaRERA dates are
  "listed or updated". Areas come from backend/app/core/areas.py only.
- Old URLs never break: an old news id permanently redirects to its new address.
- Pages must work at phone width. `.grid`/`.flex` trap: use `[display:grid]` / `sm:[display:grid]` for responsive display.
- Tests for everything new; full backend suite and `npm run build` pass before handing over. No deploys, VM access or posting.

## Streams (each owns its files)
| | Stream | Owns |
|---|---|---|
| S1 | A page per post + sitemap | `backend/app/modules/calendar/public.py` (+ its tests), `frontend/app/posts/**`, `frontend/lib/posts/**`, `frontend/components/site/PostCard.tsx`, `frontend/app/sitemap.ts` |
| S2 | Readable news addresses | `backend/app/modules/newsroom/public.py` (+ store/codec only if needed, + tests), `frontend/app/news/**`, `frontend/lib/news/**`, `frontend/components/news/**` |
| S3 | Area hubs | `frontend/app/localities/**`, `frontend/components/localities/**`, `frontend/lib/marketing/localities.ts` |
| main | Home page copy + "Explore Pune" row | `frontend/app/page.tsx`, `frontend/lib/marketing/strings.ts`, `frontend/components/site/*Section*` used only by the home page |

## Contracts
### Posts (S1 provides, S3 uses)
- `GET /api/v1/public/posts?limit=12&area=<key>`: as today, plus on every item `slug` (readable, stable, unique, lower-case words
  and hyphens, e.g. `wagholi-41-projects-in-maharera-records`) and `area` (an area key from app/core/areas.py or null: the row's
  `area` field, else the first area named in the caption). `area=` filters to that area; unknown key gives [].
- `GET /api/v1/public/posts/{slug}`: one post (same shape plus the full caption text as `text`), 404 if unknown.
- Page `/posts/<slug>`: title, images/reel still, text, date, source links (Facebook/Instagram), a link to its area page
  ("More about <Area>: /localities/<slug>") and to its project when it has one; Article JSON-LD; canonical URL.
- Frontend helper for others: `fetchPosts(limit, area?)` in `frontend/lib/posts/data.ts`; `postPath(slug)`.

### News (S2 provides, S1 and S3 use)
- Every news item's `id` in the API becomes a readable slug: `<headline words>-<6 chars of the old id>` (e.g.
  `lohegaon-hospital-opd-awaiting-approval-f5ddee`); digests keep readable ids (`digest-2026-w40`, `maharera-20261003-103729`).
- `GET /api/v1/public/news/{id}` accepts the new slug AND every old id; the reply's `id` is always the new slug, so the page
  can permanently redirect old addresses.
- `GET /api/v1/public/news?limit=20&area=<area key>` filters to stories about that area (items already carry `areas`).
- Page `/news/<slug>` links to each of its areas' pages; NewsArticle JSON-LD; canonical URL.
- Frontend helper: `fetchNews(limit, area?)` in `frontend/lib/news/data.ts`.
- The sitemap (S1) keeps using `n.id`, which becomes the slug with no sitemap change.

### Area hubs (S3)
- Each `/localities/<slug>` page gets "Latest from <Area>": up to 6 posts (`fetchPosts(6, key)`), up to 5 news stories
  (`fetchNews(5, key)`) and its projects (exists). Each list hides itself when empty or when the call fails. Until S1/S2 merge,
  code against these contracts with the helpers' current signatures guarded (an extra optional `area` argument).
