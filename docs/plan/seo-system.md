# Google SEO at Avasetu: the one page

Everything we have, run, do by hand and still plan for Google search, in one place. **Keep it current:** any change to SEO
code, pages or plans updates this page in the same commit (section 11 gets a line). The other SEO plans (section 12) are design
history; when they and this page disagree, this page is right.

Labels: **LIVE** = running in production · **TARGET** = to build · **OWNER** = done by hand · **DROPPED** = decided against.
Last updated 2026-10-21 (search families).

## 1. Goal and scorecard

Goal (owner, 2026-10-18): **every real page indexed, and above MagicBricks on the searches our pages target.** We can't win broad
searches ("flats in Pune") this year; we win the long tail where we hold facts portals don't show (MahaRERA register, homes
booked, possession filed vs promised, towers merged, nearby measured from the pin).

| Measure | 2026-10-14 | 2026-10-21 | Target 2026-11-15 | Target 2026-12-31 |
|---|---|---|---|---|
| Pages in the sitemap | 8,611 | ~11,300 | all real pages | all real pages |
| Indexed, of pages checked | 84 of 223 (38%) | 848 of 2,760 (31%) | 50% | 75% |
| Impressions / clicks, 28 days (project pages) | 61 / 3 | 5,022 / 92 | | |
| Project pages averaging top 10 | 17 | 598 of 694 seen | | |
| Searches where we are above MagicBricks | not measured | 23 of 261 (10 of 155 where MagicBricks shows) | baseline x1.5 | baseline x2 |

**The bottleneck is indexing**, not page quality: a new domain with 11k URLs gets a small crawl budget. Levers: outside links,
visits from our posts, Request indexing, and every page Google reads being worth indexing (thin pages stay noindex).
By area (2026-10-21, of pages checked): core pages 21/25, Wagholi 26/76, Kharadi 14/66, outer places (Talegaon, Dhayari) 0.

## 2. Where to look

| What | Where |
|---|---|
| Weekly numbers, MagicBricks scoreboard, Indexed by area, Ask Google to index, doctor results, fixes (with Undo), targets, conflicts, gaps | Studio → Newsroom → Insights → **Rankings** (`/studio/newsroom/insights?tab=rankings`) |
| Area list pages that grew from searches (hold / never) | Insights → **Pages** |
| Hot projects, refresh a page now | Insights → **Hot** |
| What Google shows for our areas | Insights → **Found on Google** |
| Loop health, Serper credits and searches per day | Insights → **System** |
| Weekly SEO note | Studio **Home** → "Needs you now" (once a week; opening Rankings clears it) |
| Google's own view | Search Console, property `sc-domain:avasetu.in` (owner's Google account) |
| Weekly site audit | GitHub → Actions → "SEO audit (live site)" |
| Raw loop log | VM: `docker compose logs newsroom \| grep pipeline=seo` (one line per step per round) |

## 3. Accounts and keys (all LIVE, all only in the VM's `.env`, never in git or chat)

| Key | What it is | Can | Cannot |
|---|---|---|---|
| `GSC_SA_KEY_B64` (+ `GSC_SITE`, default `sc-domain:avasetu.in`) | Google service account, added by the owner in Search Console as a **Restricted (read-only)** user | read clicks/impressions/positions per page and search; URL Inspection (2,000 a day) | submit sitemaps, Request indexing (needs a Full user); Google's Indexing API is only for job posts and livestreams |
| `SERPER_API_KEY` | Google results through Serper.dev (Google's own search API is closed to new customers, ends 2027-01-01) | ~25 searches a day: our rank and others' for a search, related searches, "People also ask" | |
| `INDEXNOW_KEY` | IndexNow key, served at `/indexnow-key.txt` | tell Bing, Yandex and the engines reading Bing about changed pages within minutes | Google (does not read IndexNow) |
| `PUBLIC_SITE_URL` / `SITE_HOST` | `https://avasetu.in` | | |

`/sitemap.xml` is submitted in Search Console (owner, 2026-10-18).

## 4. The pages we put in Google (LIVE)

| Page | Path | Title pattern (example) | Structured data | Index rule |
|---|---|---|---|---|
| Project | `/projects/<slug>` | "<name people search>, <area>: Price, Possession <Mon YYYY>" | ApartmentComplex, FAQPage, BreadcrumbList | noindex while thin (`pages.indexable`); towers/phases of one project are one page, the others 301 to it |
| Place (all projects) | `/projects/area/<place>` | "New Projects & Flats in <place>, Pune …" → "Flats & Residential Projects in <place>" once its new-launches page is live; "Flat prices in <place>" by size; "Also spelt …" | ItemList (+ Place with `alternateName`) | listed once a project in it has real facts |
| Area list (grown from searches) | `/projects/area/<place>/<intent>[/<n>-bhk][/possession-YYYY][/by-builder]` | new launches / top / "Ready to Move Flats" | ItemList, FAQPage | 3+ projects, else noindex |
| Size (from published prices) | `/projects/area/<place>/<n>-bhk` (1-4; "2 BHK" takes in 2.5) | "2 BHK Flats in Lohegaon, Pune (Oct 2026): 7 Projects, Prices" | ItemList, FAQPage | 3+ projects with a published price for that size, else noindex |
| BHK / budget (agents' listings) | `/2-bhk/<area>`, `/3-bhk/<area>`, `/price/<band>/<area>` | "2 BHK in Wagholi" | | only with enough live listings, else 404; a `/N-bhk/<area>` URL 301s to the size page once that is in search |

### Every way buyers search for an area (LIVE, 2026-10-21)

Google showed the Lohegaon place page for "new projects in lohegaon" and "projects in lohegaon" but not for "flats in lohegaon"
or "properties in lohegaon": every word on the page said "projects". The fix is a rule, not one page: **every phrasing of an area
search has exactly one owner page, and that page's title, H1, description, first paragraph and the links into it use the
phrasing's words.** The owner map (code: `seo/phrases.py` + `vocabulary.json`; rank watch: `areastats/websearch.AREA_QUERIES`):

| Buyers type (any spelling of the place) | Owner page | Words the owner page carries |
|---|---|---|
| projects / new projects / residential projects / flats / apartments / homes / property / properties / under construction in X | place page `/projects/area/x` (its new-launches list once that is live) | projects, flats, apartments, property |
| property rates / flat price / cost in X | place page, "Flat prices in X" section | prices by size, with sources |
| 1 / 2 / 3 / 4 BHK (flats, flat price) in X | size page `/projects/area/x/2-bhk` | "2 BHK Flats", prices |
| new launch / upcoming / pre-launch / latest | `/projects/area/x/new-launches` | new launch projects and flats |
| top / best / popular / most booked | `/projects/area/x/top` | top residential projects |
| ready to move / ready possession / completed | `/projects/area/x/ready-to-move` | "Ready to Move Flats" |
| possession 2027 | `/projects/area/x/possession-2027` | possession year |
| under 50 lakh, 50-75 lakh … | `/price/<band>/x` (agents' listings) | budget |
| living in X, X review | `/localities/x` | guide |
| rent, resale, plots, villas, commercial | none: kept on the data-gaps list (Insights → Pages) | |

**Spelling.** People type place names by ear ("lohegoan", "vagholi", "hinjwadi", "kharedi"). `pune_places.in_search` names
the place when the words sound like exactly one place's name and are spelt close to it (never a guess between two places);
the parser, the demand classifier and the gaps report use it, so a misspelt search counts toward the right page. Pages show
the real other spellings ("Also spelt Lohgaon") and put them in the Place `alternateName`; never a misspelling in a title.

| Locality guide + neighbourhoods | `/localities/<area>`, `/localities/<area>/<community>` | "<area>, Pune: projects, MahaRERA records and buyer guide" | Place | |
| Builder | `/builders/<slug>` | "<builder> projects in Pune: N on MahaRERA" | Organization | 2+ indexable projects, else noindex |
| Guide / topic | `/guides/<slug>` (`/guides/upper-kharadi`, `/guides/mhada-pune-lottery`) | from `calendar/topics/<slug>.json` | Article, FAQPage | |
| News | `/news`, `/news/<id>` | | NewsArticle | withdrawn story 301s to its area page |
| Posts | `/posts/<slug>` | | Article | |
| Insights articles | `/insights/<slug>` | | Article | |
| MahaRERA tracker | `/pune-maharera-tracker` | | Dataset | meant to earn links |
| Agent sites | `/agent/<slug>/…` | | RealEstateAgent | an agent's copy of a shared project names the shared page as canonical |
| Fixed pages | `/`, `/projects`, `/localities`, `/builders`, `/for-agents`, `/privacy`, `/terms` | | Organization | |

Kept out (robots.txt `PRIVATE_PATHS`): `/api/`, `/studio`, `/join`, `/login`, `/register`, `/i/` and the old app paths.

## 5. On-page rules every page follows (LIVE)

- **One page per project**: tower and phase records are grouped (`areastats/clusters.py`); members answer 301 to the primary.
- **Titles from real searches**: a page's target search (Search Console) becomes its title only when every word is the project's
  own name, area or builder (`seo/targets.py`); MahaRERA's spelling stays in the body and JSON-LD.
- **Text from facts**: page writer v3 (summary + "The homes and the building", "Location", "Amenities and features" + search
  line), checked against the record; banned sales words (best, luxury, premium, hurry…) (`areastats/enrich.py`).
- **Web facts** only when quoted on the builder's site or two sites agree; MahaRERA values never taken from the web
  (`areastats/webfacts.py`). **Prices** per BHK from the builder's site or two agreeing sites, kept 45 days (`areastats/prices.py`).
- **Nearby places** measured from the project's own Google pin, never the locality centre (`areastats/pin.py`).
- **Buyer FAQ** from "People also ask" questions our facts answer, with FAQPage data (`seo/questions.py`); price questions never
  answered from the web.
- **Search description**: the doctor's when set, else the page summary.
- **Freshness**: a page's sitemap date moves only on a real change (`pages.page_updated`), never MahaRERA's own dates; IndexNow
  sends what changed.
- **Links**: every page within 3 clicks of home (measured 2026-10-18): home → areas → place page → every project; each project
  → 6 neighbours, its builder, its place, its area lists, nearest neighbourhood guide; "Most active projects" on area pages.
- **Canonical** on every page; agent copies point to the shared page.
- **No 5xx for Google**: the page loader retries the API once; the sitemap never replaces a good build with an empty one; a
  branded 404.
- **Marketer sites and scores never appear on public pages.**

## 6. What runs by itself (LIVE)

All in the `newsroom` worker role (seo loop every 30 minutes; each step runs only when due) unless noted.

| Job | When | What it does | Code |
|---|---|---|---|
| Sitemap | rebuilt every 10 min | index + ~99 child sitemaps (core, agents, builders, one per Pune place); noindex pages left out; a build without area sitemaps is not served | `frontend/lib/site/sitemap.ts` |
| IndexNow | every 30 min | sends pages changed since the last send | `seo/indexnow.py` |
| Search Console read | daily | per-page and per-search numbers onto project records and `search_demand`; marks pages near page one (position 8-20, 20+ impressions) | `areastats/searchconsole.py` |
| Index coverage | daily, ~1 hour | URL Inspection of 1,800 pages (never checked first), so the whole sitemap is covered about once a week; a stale sitemap right after a deploy is skipped; per-area counts (`by_sitemap`) | `seo/coverage.py` |
| Target searches + titles | daily | target search per project page; title rule above; site snapshot for the weekly numbers | `seo/targets.py` |
| Page doctor | daily, at most 15 pages | one fix per page per 28 days, measured at 14 and 28 days, title/description undone if the page lost 5+ places. Fixes: title, buyer questions, link slot, refresh facts, description, **rival** (MagicBricks just above: description led by the facts their result shows; if they show a price we lack, refresh first) | `seo/doctor.py`, `seo/actions.py`, `seo/rival.py` |
| Google searches | daily, ~25 | 6 area (7 phrasings per area: new launch, upcoming, top, ready to move, flats, 2 BHK flats, property rates) + 8 project searches, 6 re-checks of doctored pages, 5 **panel** target searches (every target once in 14 days); new MahaRERA numbers found go to the register | `areastats/websearch.py` |
| Search gaps | weekly | searches that show us with no page in the top 20 | `seo/gaps.py` |
| Area list pages grow | weekly, at most 10 new | from real searches once they pass demand, supply (3+ projects) and overlap checks (a size page is compared only with pages of the same size); seeds: new launches, top, ready to move, 1/2/3 BHK for every place; autocomplete seeds take turns: new projects / flats / 2 bhk flats / property in <area> | `seo/grow.py`, `seo/facets.py`, `seo/phrases.py` |
| MagicBricks scoreboard | weekly | our place vs MagicBricks, 99acres, Housing for every search run in 28 days; "win next" list; history per week | `seo/scoreboard.py` |
| Owner's SEO note | weekly | Studio notification with the week's numbers and how many pages wait for Request indexing | `seo/note.py` |
| Page writer | every 5 min (cheap rewrite), full re-read at most 1 per 30 min | project text on free LLM tiers; skipped while most providers are resting | `areastats/enrich.py` |
| Hot projects refresh | every 14 days per hot project | facts, prices and text re-read | `areastats/hot.py`, `enrich.py` |
| Site audit | weekly, Mondays 08:47 IST (GitHub Actions) | 300 sitemap pages read like Googlebot: status, robots, noindex, canonical, title, JSON-LD; a 5xx is read again after 30 s | `seo/audit.py`, `.github/workflows/seo-audit.yml` |

## 7. What the owner does by hand (OWNER)

- **Request indexing, ~10 a day**: Search Console → URL inspection → paste → Request indexing, from Rankings → "Ask Google to
  index" (our areas first, list and guide pages before projects). The only way to jump the crawl queue.
- **Resubmit `/sitemap.xml`** after a deploy that adds a page type.
- **Outside links** (the biggest lever): Google Business Profile for Avasetu; Pune property directories; agents' own sites
  linking to their project pages; offer the MahaRERA tracker to journalists and bloggers.
- **Social → site**: Instagram website + WhatsApp button, captions link the project or area page (visits bring crawls).
- **Validate fix** in Search Console when it reports an error group we fixed.

## 8. To build (TARGET, in order)

1. **Prices area by area** (fuel for the size pages and "Flat prices in X"): prices are read on the page writer's turn,
   Upper Kharadi first; take our 8 areas' projects first, so each area has 3+ priced projects per size. Read the size pages'
   `gate.supply` on Insights → Pages to see which wait on prices.
2. **Budget pages from published prices**: `/projects/area/<place>/under-50-lakh` like the size pages, so budget searches are
   answered for every place, not only where agents list; then the agents' `/price/<band>/<area>` 301s like `/N-bhk/<area>`.
3. **Read the search families in Search Console** (28 days after deploy, ~2026-11-20): for each area, impressions and position
   for "flats", "property", "2 bhk", "price" searches on the owner page; a phrasing whose impressions land on a non-owner page
   goes on the conflicts list (R2).
4. **Page writer goes area by area** (index-everything I4): never-written pages are taken newest first today
   (`enrich.priority`); take our 8 areas' pages first, so each page Google reads there has a summary, dates and nearby places.
5. **Target searches for list pages**: only project pages get a target search and title from Search Console; give place, area
   list, BHK and budget pages the same (rank-loop R1 left them out).
6. **News stories link the projects they name** (insights-and-seo S4): a story about a project links its page.
7. **Area list pages, weeks 3-4** (area-intent-pages section 11): retire with 301 after 180 idle days, learn which page types
   earn, landmark lists, Pune-wide lists, a monthly round-up story, vocabulary proposals; a "New launches by area" strip on home.
8. **Page speed**: the Baner place page is 0.9 MB; uncached project pages 0.45-0.8 s.
9. **Weekly note on WhatsApp/email**: needs an email sender or an approved WhatsApp template (`report.week_lines` is unused).
10. **Coverage off the loop**: its hour holds the seo loop's later steps once a day; give it its own task if they must run first.
11. **Tidy the SEO code** (seo-review S2-S5): one `_aware` (31 copies today), one Search Console client, one sitemap parser,
   `pages` out of `areastats`, an import-linter contract.

Results to read: doctor's first 14-day results **2026-10-28**; rival and price refreshes from **2026-11-04**.

DROPPED: Google Indexing API (not allowed for our pages); a "priority" sitemap (Google ignores `<priority>`); crawl push via
more internal links (link graph already complete; revisit only if one area's linked pages stay unindexed while others index).

## 9. Rules

- No real page is dropped to make the numbers look better; thin pages are noindex and out of the sitemap until they hold a fact.
- One fix per page per 28 days, measured; a fix that lost is undone and never applied again.
- Facts only from MahaRERA, the builder's site or two agreeing sites; never a number from a model's own knowledge.
- No copying of portal text or data (we compare positions and what kind of fact their result shows); no paid links.
- No year in URLs; a month in a title only on a real change.

## 10. How the loop fits together

measure (Search Console, Serper, URL Inspection) → choose (near page one, MagicBricks just above, rising, hot) → improve the page
(doctor, writer, prices, FAQ, lists) → tell (sitemap date, IndexNow, owner's Request indexing) → measure again 14 and 28 days later.

## 11. Change log

| Date | Commit | Change |
|---|---|---|
| 2026-10-14 | 941c39ad | Web facts, buyer FAQ, search titles on project pages |
| 2026-10-14 | d9598fe6 | Rank loop: target searches, page doctor, towers merged with 301s, builder pages, gaps, Rankings tab |
| 2026-10-14 | 588474f3 | Nearby measured from the project's Google pin |
| 2026-10-15 | 71ea05bf | Area list pages that grow from searches (28 live) |
| 2026-10-17 | fe50763e | Page writer v2 (summary + sections + search line) |
| 2026-10-18 | 0b602943 | Sitemap index by area (99 sitemaps), no 5xx for Google |
| 2026-10-20 | e2b36b07, c59b8eef | Builder brands on pages; site polish (branded 404, old CSS removed) |
| 2026-10-20 | 7c6ef9cd | Price sheet on project pages |
| 2026-10-21 | 81263539..02d8154b | Coverage 1,800/day, MagicBricks scoreboard, weekly owner note + Ask Google to index, audit second read |
| 2026-10-21 | 9cbba482, 0d55a7ca | Doctor rival fix (+ price refresh), Indexed by area, panel of target searches |
| 2026-10-21 | 886047b | Place pages say "flats" in title, H1 and description |
| 2026-10-21 | aaf7c45 | Search phrases name a place however it is spelt (`pune_places.in_search`) |
| 2026-10-21 | f43252f + this | Every way buyers search: size pages from published prices, "Flat prices in X", Place `alternateName`, flats wording and links, owner map, rank watch for the families |

## 12. Detail and history

Design and reasoning behind the pieces above (read for the why; this page holds the current state):
[rank-loop.md](rank-loop.md) (doctor, targets), [index-everything.md](index-everything.md) (indexing, scoreboard),
[area-intent-pages.md](area-intent-pages.md) (area list pages), [insights-and-seo.md](insights-and-seo.md) (owner screens),
[seo-review.md](seo-review.md) (code review), [seo.md](seo.md) (first plan, 2026-10-04), [topic-pages.md](topic-pages.md),
[project-pages.md](project-pages.md).
