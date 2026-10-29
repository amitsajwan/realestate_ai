# Google SEO at Avasetu: the one page

Everything we have, run, do by hand and still plan for Google search, in one place. **Keep it current:** any change to SEO
code, pages or plans updates this page in the same commit (section 11 gets a line). The other SEO plans (section 12) are design
history; when they and this page disagree, this page is right.

Labels: **LIVE** = running in production · **TARGET** = to build · **OWNER** = done by hand · **DROPPED** = decided against.
Last updated 2026-10-29 (the live area-list list (`/facets`) works again after two days of errors; photos copied from other sites leave every page, no longer count as a page's own content and are no longer downloaded; the buyers' home is the brand's page: "Avasetu: Search New Projects in Pune…", the team's agent page names it as canonical, agents' sign-up pages out of search; Search Console check of the 10-26 drop: site-wide, indexed, positions held, impressions gone); 2026-10-27 (enrichment concentrates on east Pune; area pages, area lists, neighbourhood articles, locality stubs and post pages out of search; project
pages in search only with content of their own, after the site-wide drop of 2026-10-26;
before that 2026-10-26: Top lists rank homes a buyer can still buy, section 8a keeping the lead, section 8b what a competitor cannot copy).

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

**Owner's check, 2026-10-26:** ChatGPT names our project pages first for "top projects in Kharadi / Upper Kharadi / Wagholi",
and Google ranks them well. One person's check by hand, not a measurement: AI answers change with the wording, the login and
the place. Measuring it every week is section 8a, step 2.

## 2. Where to look

| What | Where |
|---|---|
| Weekly numbers, MagicBricks scoreboard, Indexed by area, Ask Google to index, doctor results, fixes (with Undo), targets, conflicts, gaps | Studio → Newsroom → Insights → **Rankings** (`/studio/newsroom/insights?tab=rankings`) |
| Area list pages that grew from searches (hold / never) | Insights → **Pages** |
| Hot projects, refresh a page now | Insights → **Hot** |
| What Google shows for our areas | Insights → **Found on Google** |
| Loop health, Serper credits and searches per day (rank checks + prices round) | Insights → **System** |
| Weekly SEO note | Studio **Home** → "To do" (once a week; opening Rankings clears it) |
| Google's own view | Search Console, property `sc-domain:avasetu.in` (owner's Google account) |
| Weekly site audit | GitHub → Actions → "SEO audit (live site)" |
| AI search: assistants that read us, pages they use, visits from AI answers | Insights → **Rankings** → "AI search"; one line in the weekly note |
| Loops stopped, pages going old | Studio → Admin → **Health**: "SEO loop", "Project page refresh", "Project pages up to date" |
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
| Project | `/projects/<slug>` | "<name people search> <area>: 3 & 4 BHK from ₹1.99 Cr, possession Feb 2031"; no price: "…: MahaRERA <regno>, possession <Mon YYYY>" (`frontend/lib/site/projectSeo.ts`, at most 65) | ApartmentComplex (+ an Offer per priced size with its floor size, the builder as Organization), FAQPage, BreadcrumbList, WebPage | ~~noindex while thin (`pages.indexable`)~~ until 2026-10-27; now in search only with content beyond the register: written sections, prices read, web facts or the builder's highlights/pictures/plans (`pages.searchable`; ~400 of 11,700 on 10-27; AI illustrations never counted, and from 2026-10-29 neither do pictures copied from other sites), every listable page still on the area lists; towers/phases of one project are one page, the others 301 to it |
| Place (all projects) | `/projects/area/<place>` | "New Projects & Flats in <place>, Pune …" → "Flats & Residential Projects in <place>" once its new-launches page is live; "Flat prices in <place>" by size; "Also spelt …" | ItemList (+ Place with `alternateName`) | ~~listed once a project in it has real facts~~ until 2026-10-27; now once a project in it is in search (`pages.places` counts `searchable`), else noindex |
| Area list (grown from searches) | `/projects/area/<place>/<intent>[/<n>-bhk][/possession-YYYY][/by-builder]` | new launches / top / "Ready to Move Flats" | ItemList, FAQPage | ~~3+ projects~~ until 2026-10-27; now 3+ of its projects in search (`facets.in_search`), else noindex; the list still shows every project |
| Size (from published prices) | `/projects/area/<place>/<n>-bhk` (1-4; "2 BHK" takes in 2.5) | "2 BHK Flats in Lohegaon, Pune (Oct 2026): 7 Projects, Prices" | ItemList, FAQPage | 3+ projects with a published price for that size (a read price is content of its own, so `facets.in_search` holds), else noindex |
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
| top / best / popular / most booked | `/projects/area/x/top` | top residential projects; ranked only among projects with 10+ homes open, sold out ones in their own table below (2026-10-26) |
| ready to move / ready possession / completed | `/projects/area/x/ready-to-move` | "Ready to Move Flats" |
| possession 2027 | `/projects/area/x/possession-2027` | possession year |
| under 50 lakh, 50-75 lakh … | `/price/<band>/x` (agents' listings) | budget |
| living in X, X review | `/localities/x` | guide |
| rent, resale, plots, villas, commercial | none: kept on the data-gaps list (Insights → Pages) | |

**Spelling.** People type place names by ear ("lohegoan", "vagholi", "hinjwadi", "kharedi"). `pune_places.in_search` names
the place when the words sound like exactly one place's name and are spelt close to it (never a guess between two places);
the parser, the demand classifier and the gaps report use it, so a misspelt search counts toward the right page. Pages show
the real other spellings ("Also spelt Lohgaon") and put them in the Place `alternateName`; never a misspelling in a title.

| Locality guide + neighbourhoods | `/localities/<area>`, `/localities/<area>/<community>` | "<area>, Pune: projects, MahaRERA records and buyer guide" | Place | from 2026-10-27 only the curated guides (`LOCALITIES`) are in search: a place name without a guide ("live listings and projects" stub) and every neighbourhood article (a model writes its paragraphs) are noindex and out of the sitemap; an area with its own guide (`/guides/<same slug>`, today Upper Kharadi) names the guide as canonical and is left out of the sitemap (2026-10-27: both ranked for "upper kharadi", guide at 5, locality at 10) |
| Builder | `/builders/<slug>` | "<builder> projects in Pune: N on MahaRERA" | Organization | 2+ projects in search (`pages.searchable`, from 2026-10-27; was 2+ listable), else noindex |
| Guide / topic | `/guides/<slug>` (`/guides/upper-kharadi`, `/guides/mhada-pune-lottery`) | from `calendar/topics/<slug>.json` | Article, FAQPage | |
| Tracker | `/news/track/<slug>` (`/news/track/purandar-airport`, 8 live) | `newsroom/tracker_data/<slug>.json` + attached reports | Article, BreadcrumbList | durable "<thing> status" page; area pages link the ones that touch them ([news-strategy.md](news-strategy.md)) |
| News | `/news`, `/news/<id>` | | NewsArticle | withdrawn story 301s to its area page; `/news` leads with the trackers |
| Posts | `/posts/<slug>` | | Article | ~~in the sitemap~~ until 2026-10-27; now noindex and out of the sitemap, `/posts` too: each repeats one of our Facebook/Instagram posts |
| Insights articles | `/insights/<slug>` | | Article | |
| MahaRERA tracker | `/pune-maharera-tracker` | | Dataset | meant to earn links |
| Agent sites | `/agent/<slug>/…` | | RealEstateAgent | an agent's copy of a shared project names the shared page as canonical; the team's own site `/agent/avasetu` ("Avasetu Homes": a few listings, the enquiry form every buyer button opens) names the buyers' home as canonical, is out of the sitemap, links the home page under its hero, and its RealEstateAgent has `parentOrganization` Avasetu (2026-10-29); its listing and project pages keep their own |
| Buyers' home | `/` | ~~"New Projects in Pune, MahaRERA Checked: Possession, Bookings, Builders"~~ until 2026-10-29; now "Avasetu: Search New Projects in Pune, Checked Against MahaRERA" (the brand's page, buyer-first); description "Search every new project in …" | Organization (`sameAs` Facebook Page + Instagram from `lib/marketing/social`, `alternateName` आवासेतु), WebSite (same `alternateName`, a buyer description, SearchAction → `/projects?q=`, which answers on the server without JavaScript; Google retired the sitelinks search box in 2024, so no box shows) | links hot projects, every area's list and guide, live new-launch and ready lists, builders with pages; H1 unchanged ("New projects in Pune, checked against MahaRERA"): the header above it already reads "Avasetu" |
| Agents' home | `/agents` (the home page until 2026-10-22); `/for-agents` stays as the printable one-page pitch | "Free trial for real estate agents in Pune \| Avasetu" (the brand last since 2026-10-29) | | the agents' one page in search; `/trial`, `/request-invite`, `/for-agents` and `/for-agents/guide` are noindex and out of the sitemap from 2026-10-29 (reached from our links and WhatsApp, never the brand's face) |
| Fixed pages | `/projects`, `/localities`, `/builders`, `/privacy`, `/terms` | | | |

Kept out (robots.txt `PRIVATE_PATHS`): `/api/`, `/studio`, `/join`, `/login`, `/register`, `/i/` and the old app paths.

### AI search (BUILT 2026-10-21, not deployed)

How the assistants pick sources: ChatGPT search reads its own index (OAI-SearchBot) and Bing's; Copilot is Bing; Google's AI
Overviews come from Google's index; Perplexity crawls (PerplexityBot) and searches. They cite pages that already rank and that hold
a short, dated, quotable answer. So for AI search the levers are the same as for Google, plus being in **Bing**, being readable by
their fetchers, and leading each page with the answer. What we run:

| Piece | What it does | Code |
|---|---|---|
| AI visit log | every page request from an AI fetcher (ChatGPT-User / Perplexity-User / Claude-User = "read to answer a question"; OAI-SearchBot, PerplexityBot, Bingbot, Googlebot = search crawlers; GPTBot, ClaudeBot, CCBot = training) and every visit from an AI answer (chatgpt.com, perplexity.ai, copilot, gemini, claude.ai, `utm_source=chatgpt.com`), counted per day with the pages for answers and referrals. By user agent as sent (no reverse DNS): trends, not proof | `frontend/proxy.ts` → `/internal/seo/visit` (outside `/api`, so never reachable from the public site) → `seo/aivisits.py` |
| AI fetcher audit | the weekly site audit reads 12 sampled pages again as OAI-SearchBot, ChatGPT-User, PerplexityBot and bingbot: error on a robots.txt block, another status, another page (bot shield) or no `<h1>` text in the HTML | `seo/audit.py` |
| robots.txt | every crawler allowed, AI ones included (decision: being read beats being private; GPTBot training kept allowed so models know the brand) | `frontend/app/robots.ts` |
| `/llms.txt` | a map of the site for assistants (our areas, their lists, up to 60 project pages in our areas, guides, the MahaRERA tracker), from the sitemap's lists. Projects: agent-listed first, then the register's being built (not sold out), priced ones and the newest changes first, each with builder, possession, homes booked, MahaRERA number and price. A hint some read, not a ranking signal | `frontend/app/llms.txt/route.ts` |
| Bing | IndexNow sends changes (LIVE); `NEXT_PUBLIC_BING_SITE_VERIFICATION` puts the `msvalidate.01` tag in every page | `seo/indexnow.py`, `frontend/app/layout.tsx` |
| Quotable pages | place pages open with a paragraph written by code from the numbers ("As of 21 Oct 2026, MahaRERA lists 14 housing projects in Lohegaon … 2 BHK flats start from ₹69 lakh"), then a FAQ from the same lists (FAQPage) and "Updated <day>" (WebPage dateModified); list pages already had both. Project pages (2026-10-25) open "About" (register pages) or the header (agent-listed pages) with the same kind of paragraph from their own record ("As of 3 Oct 2026, Rohan Abhilasha 4 by Rohan Builders in Wagholi, Pune is registered with MahaRERA as P52100080076. The completion date filed … moved from … 244 of its 416 homes are booked. 2 BHK from ₹69 L, as listed on …"), dated by the day the record was read, with "Updated <page_updated>" and WebPage dateModified; MahaRERA's 2026 blanket extension is named so a 4-month move does not read as a delay | `frontend/lib/site/placeFacts.ts`, `frontend/lib/site/projectFacts.ts` |
| News → projects | a story's page links the projects it clearly names (the newsroom's existing match: MahaRERA number, or the full specific name in a story about that area, kept in `projects.news`): `GET /public/news/{id}` returns `projects` [{regno, slug}], the page names each from its own project page, once per project | `newsroom/public.py`, `newsroom/store.projects_named_by`, `frontend/lib/news/projects.ts` |

## 5. On-page rules every page follows (LIVE)

- **One page per project**: tower and phase records are grouped (`areastats/clusters.py`); members answer 301 to the primary.
  The primary is a homes registration before a shops/offices one (PC numbers), so a housing project is never described as
  commercial (2026-10-22, Venkatesh Vanaya).
- **Only this project's pages feed it** (2026-10-22): web facts, highlights, prices and pictures are read only from pages that
  print the MahaRERA number or read as a home listing in Pune (BHK/RERA/carpet-area words and Pune or the area), or that were
  checked by hand (`builder_pages`); travel, health and directory sites never. Buyers' names set by hand in
  `marketed_name_override` (Purple Park Eden). Hand-placed projects (`pune_places.VERIFIED`) take that area as `locality`.
- **Titles from real searches**: a page's target search (Search Console) becomes its title only when every word is the project's
  own name, area or builder (`seo/targets.py`); MahaRERA's spelling stays in the body and JSON-LD.
- **Text from facts**: page writer v3 (summary + "The homes and the building", "Location", "Amenities and features" + search
  line), checked against the record; banned sales words (best, luxury, premium, hurry…) (`areastats/enrich.py`).
- **Web facts** only when quoted on the builder's site or two sites agree; MahaRERA values never taken from the web
  (`areastats/webfacts.py`). **Prices** per BHK from the builder's site or two agreeing sites, kept 45 days (`areastats/prices.py`).
- **Nearby places** measured from the project's own Google pin, never the locality centre (`areastats/pin.py`).
- **Buyer FAQ** from "People also ask" questions our facts answer, with FAQPage data (`seo/questions.py`); price questions never
  answered from the web.
- **Search description**: the doctor's when set, else the page summary; at most 160 characters and titles built by code at most 70
  (`fitDescription` / `fitTitle` in `frontend/lib/site/format.ts` drop the least useful clauses first, never cut mid-word).
- **Freshness**: a page's sitemap date moves only on a real change (`pages.page_updated`), never MahaRERA's own dates; IndexNow
  sends what changed.
- **Links**: every page within 3 clicks of home (measured 2026-10-18): home → areas → place page → every project; each project
  → 6 neighbours, its builder, its place, its area lists, nearest neighbourhood guide; "Most active projects" on area pages.
- **Canonical** on every page; agent copies point to the shared page.
- **No 5xx for Google**: the page loader retries the API once; the sitemap never replaces a good build with an empty one; a
  branded 404.
- **Marketer sites and scores never appear on public pages.**
- **Pictures are the builder's or the brochure's** (2026-10-29): pictures copied from other sites' pages (source `web`: housiey,
  magicbricks, squareyards and other agents) stay on the record but are never shown (`pages.shown_pictures`, read by
  `profile.public` and the cards' `areamap._photo`); a project without one shows the skyline. AI illustrations only on pages out
  of search. Enrichment no longer downloads other sites' pictures (`areastats/profile.py`, 2026-10-29).

## 6. What runs by itself (LIVE)

All in the `newsroom` worker role (seo loop every 30 minutes; each step runs only when due) unless noted.

| Job | When | What it does | Code |
|---|---|---|---|
| Sitemap | rebuilt every 10 min | index + ~99 child sitemaps (core, agents, builders, one per Pune place); noindex pages left out; a build without area sitemaps is not served | `frontend/lib/site/sitemap.ts` |
| IndexNow | every 30 min | sends pages changed since the last send | `seo/indexnow.py` |
| Search Console read | daily | per-page and per-search numbers onto project records and `search_demand`; marks pages near page one (position 8-20, 20+ impressions) | `areastats/searchconsole.py` |
| Index coverage | daily, ~1 hour | URL Inspection of 1,800 pages (never checked first), so the whole sitemap is covered about once a week; a stale sitemap right after a deploy is skipped; per-area counts (`by_sitemap`) | `seo/coverage.py` |
| Target searches + titles | daily | target search per project page; title rule above; site snapshot for the weekly numbers **On hold until 2026-11-17** (`seo/actions.HOLD_UNTIL`): no new titles while the site settles after the 2026-10-26 drop. | `seo/targets.py` |
| Page doctor | daily, at most 15 pages | one fix per page per 28 days, measured at 14 and 28 days, title/description undone if the page lost 5+ places. Fixes: title, buyer questions, link slot, refresh facts, description, **rival** (MagicBricks just above: description led by the facts their result shows; if they show a price we lack, refresh first) **On hold until 2026-11-17** (`seo/actions.HOLD_UNTIL`): earlier fixes are still measured and undone, no new ones. | `seo/doctor.py`, `seo/actions.py`, `seo/rival.py` |
| Google searches | daily, ~25 | 6 area (7 phrasings per area: new launch, upcoming, top, ready to move, flats, 2 BHK flats, property rates) + 8 project searches, 6 re-checks of doctored pages, 5 **panel** target searches (every target once in 14 days); new MahaRERA numbers found go to the register | `areastats/websearch.py` |
| Search gaps | weekly | buyer searches where we are not in the top 20: Search Console's, and our own Serper searches of the last 28 days where we are absent (judged by the phrase's words, so one project's name is not a gap); each matched to an existing page type, our areas first | `seo/gaps.py` |
| Area list pages grow | weekly, at most 10 new | from real searches once they pass demand, supply (3+ projects) and overlap checks (a size page is compared only with pages of the same size); seeds: new launches, top, ready to move, 1/2/3 BHK for every place; autocomplete seeds take turns: new projects / flats / 2 bhk flats / property in <area> | `seo/grow.py`, `seo/facets.py`, `seo/phrases.py` |
| MagicBricks scoreboard | weekly | our place vs MagicBricks, 99acres, Housing for every search run in 28 days; "win next" list; history per week | `seo/scoreboard.py` |
| Prices round | one project every 15 min (`PRICES_EVERY_MINUTES`), inside the enrich loop | prices only (builder's site, or two agreeing sites); Upper Kharadi → Kharadi → Wagholi → Keshav Nagar → Lohegaon → Baner → Wakad → Hinjawadi → everywhere else, new launches and hot projects first in each area, 90%+ booked last, completed projects never; never read first, re-read every 30 days (before a price lapses at 45), 14 days after a read that found none; at most 10 new Serper searches a day (`PRICES_SEARCHES_PER_DAY`), waits while the free model tiers rest; coverage per area on Insights → Pages | `areastats/pricing.py` |
| AI visit log | every page request (proxy, after the response) | AI fetchers and visits from AI answers, per day; on Rankings and in the weekly note | `frontend/proxy.ts`, `seo/aivisits.py` |
| Fresh pages count | daily | live project pages in our 8 areas re-read in the last 35 days, per area, the oldest five; Admin → Health | `seo/freshness.py` |
| Owner's SEO note | weekly | Studio notification with the week's numbers, how many pages wait for Request indexing, and the enquiries from AI answers | `seo/note.py` |
| Page writer | every 5 min (cheap rewrite), full re-read at most 1 per 30 min | project text on free LLM tiers; skipped while most providers are resting From 2026-10-27 a page in Google keeps its text 14 days before a newer writer version takes it again (`enrich.REST_DAYS`; 87 of 503 were rewritten in one day); its date (`page_text_at`, the sitemap's lastmod) moves only when the text changed, never for a round that found the same facts; no AI illustrations on a page in Google. | `areastats/enrich.py` |
| Hot projects refresh | every 14 days per hot project | facts, prices and text re-read | `areastats/hot.py`, `enrich.py` |
| Site audit | weekly, Mondays 08:47 IST (GitHub Actions) | 300 sitemap pages read like Googlebot: status, robots, noindex, canonical, title, JSON-LD; a 5xx is read again after 30 s; 12 of them again as 4 AI fetchers (same page, `<h1>` in the HTML, robots.txt) | `seo/audit.py`, `.github/workflows/seo-audit.yml` |

## 7. What the owner does by hand (OWNER)

- **Request indexing, ~10 a day**: Search Console → URL inspection → paste → Request indexing, from Rankings → "Ask Google to
  index" (in order: our areas' place pages and guides, their area lists, hot projects in our areas, builders and other areas,
  other projects, neighbourhood guides last). The only way to jump the crawl queue.
- **Resubmit `/sitemap.xml`** after a deploy that adds a page type.
- **Outside links** (the biggest lever): Google Business Profile for Avasetu; Pune property directories; agents' own sites
  linking to their project pages; offer the MahaRERA tracker to journalists and bloggers.
- **Social → site**: Instagram website + WhatsApp button, captions link the project or area page (visits bring crawls).
- **Validate fix** in Search Console when it reports an error group we fixed.
- **Bing Webmaster Tools, once** (ChatGPT search and Copilot lean on Bing): bing.com/webmasters → add avasetu.in → "Import from
  Google Search Console" (or put the HTML meta tag value in `NEXT_PUBLIC_BING_SITE_VERIFICATION` in `deploy/gcp/.env` and
  redeploy) → submit `/sitemap.xml`. Then check its Index and Search Performance reports monthly.
- **Be talked about** (AI answers lean on brands the web mentions): answer Pune property threads on Reddit and Quora with the
  project or area page that answers them, offer the MahaRERA tracker to journalists, keep the Google Business Profile current.

### Weekly and monthly upkeep (OWNER, 2026-10-26)

What keeps the lead (section 8a). About 1–2 hours a week, no money.

| When | Do | Where |
|---|---|---|
| Every week, Monday | Read the SEO note; check that the Rankings numbers moved and that the AI search counts are not zero | Studio Home, Insights → Rankings |
| Every week | Check that Health shows no BAD rows (keys, IndexNow, Search Console; the loop and freshness rows once 8a step 1 is built) | Studio → Admin → Health |
| Every week | Check that the Monday "SEO audit (live site)" run is green | GitHub → Actions |
| Every week | Ask the same 5 questions in ChatGPT, Perplexity and Gemini while logged out ("top projects in Kharadi", "Upper Kharadi", "Wagholi", "new launch 2 BHK Wagholi", "is <a hot project> delayed") and note who is cited, until the AI answer panel (8a step 2) does it | a notes sheet |
| Every week | 2–3 honest answers on Reddit (r/pune) or Quora, each linking the one page that answers the question; no copy-paste, never more than one link | Reddit, Quora |
| Every week | Ask Google to index the top of the list (~10 a day when there is time) | Rankings → "Ask Google to index" |
| Every month | Send the "Pune MahaRERA report" from `/pune-maharera-tracker` to local journalists and property bloggers | e-mail |
| Every month | Google Business Profile: a post, answer reviews, check the links to the area pages | Google Business Profile |
| Every month | Bing Webmaster Tools: the Index and Search Performance reports | bing.com/webmasters |
| Every month | Check Serper credits and the Gemini bill; read the price lines in 8a again if a provider changed its pricing | Insights → System, provider consoles |
| Every quarter | Ask agents to link their own agent page from their WhatsApp Business and Instagram bios, and their posts to `/projects/<slug>`, never a portal | agents |

## 8. To build (TARGET, in order)

1. ~~Prices area by area~~ BUILT 2026-10-21 (`areastats/pricing.py`, the prices round above). Watch "Prices by area" on
   Insights → Pages; if a first area stays under 3 priced projects per size after a week, the gap is sites that state no price
   ("none found"), not turns.
2. **Budget pages from published prices**: `/projects/area/<place>/under-50-lakh` like the size pages, so budget searches are
   answered for every place, not only where agents list; then the agents' `/price/<band>/<area>` 301s like `/N-bhk/<area>`.
3. **Read the search families in Search Console** (28 days after deploy, ~2026-11-20): for each area, impressions and position
   for "flats", "property", "2 bhk", "price" searches on the owner page; a phrasing whose impressions land on a non-owner page
   goes on the conflicts list (R2).
4. **Page writer goes area by area** (index-everything I4): never-written pages are taken newest first today
   (`enrich.priority`); take our 8 areas' pages first, so each page Google reads there has a summary, dates and nearby places.
5. **Target searches for list pages**: only project pages get a target search and title from Search Console; give place, area
   list, BHK and budget pages the same (rank-loop R1 left them out).
6. ~~News stories link the projects they name~~ BUILT 2026-10-25 (insights-and-seo S4; "News → projects" above).
7. **Area list pages, weeks 3-4** (area-intent-pages section 11): retire with 301 after 180 idle days, learn which page types
   earn, landmark lists, Pune-wide lists, a monthly round-up story, vocabulary proposals; a "New launches by area" strip on home.
8. **Page speed**: the Baner place page is 0.9 MB; uncached project pages 0.45-0.8 s.
9. **Weekly note on WhatsApp/email**: needs an email sender or an approved WhatsApp template (`report.week_lines` is unused;
   section 8a step 5).
10. **Coverage off the loop**: its hour holds the seo loop's later steps once a day; give it its own task if they must run first.
11. **Tidy the SEO code** (seo-review S2-S5): one `_aware` (31 copies today), one Search Console client, one sitemap parser,
   `pages` out of `areastats`, an import-linter contract.

AI search, next (TARGET):
- **AI answer panel** (needs a paid key, owner to decide; now section 8a step 2, on Gemini grounding): weekly, 20 buyer questions ("2 bhk flats in Lohegaon", "is <project>
  delayed") asked through the Perplexity Sonar API or Gemini with Google Search grounding, recording which sites the answer cites;
  our share of citations beside MagicBricks/99acres/Housing on the scoreboard. ~80 calls a month.
- **Bing Webmaster API** (needs the API key from Bing Webmaster Tools; section 8a step 4): Bing's searches and positions for our pages into
  `search_demand` like Search Console (source "bing"), so the doctor and the gaps report see Bing too.
- **Marathi searches**: the phrase parser drops Devanagari ("लोहगाव मध्ये फ्लॅट"); read it with the Marathi place names we hold
  (`reels/spoken_names.py`) and a Marathi vocabulary, then decide Marathi place pages from the counts.
- **Verified bots**: reverse-DNS check for Googlebot, Bingbot and OAI-SearchBot before counting, if spoofed names ever skew the log.

## 8a. Keeping the lead (TARGET, 2026-10-26)

We are cited because our pages are the **freshest correct source**: each one opens with a dated answer from the register,
prices and plans ("As of 3 Oct 2026 …"), and the loops in section 6 keep that true. So the lead is kept by keeping the loops
alive and the facts right, not by writing more by hand. The risk is quiet decay, where nothing fails loudly: a key or credit
runs out, the `newsroom` worker stops, or MahaRERA, a model or a builder's site changes, so pages keep old text and old dates.

Checked against the code on 2026-10-26:
- Admin → Health has rows for IndexNow and Search Console (`admin/health.seo_rows`), and none for a stalled seo or enrich
  loop or for old page dates. Stalls show only in `python -m app.worker --check` on the VM, which nobody reads every day.
- Nothing calls a model with search grounding today (no `google_search` tool in `backend/app`), so the AI answer panel has the
  whole Gemini grounding allowance to itself.
- A lead's source (`tracking/origin.REFERRER_SOURCES`) knows `chatgpt` and `perplexity` but not Copilot, Gemini or Claude
  (they show as the bare host, e.g. `gemini.google.com`), and does not read ChatGPT's `utm_source=chatgpt.com`.
  `seo/aivisits.REFERRERS` already knows all of them, so we count AI visits but cannot add up leads from AI answers.
- `seo/report.week_lines` is still unused (item 9 above).

The build, in order (cheapest and most protective first):

| Step | What | Code | Needs | Cost a month |
|---|---|---|---|---|
| ~~1~~ BUILT 2026-10-26 | **Freshness and stalled-loop rows** on Admin → Health: the seo and project_enrich heartbeats (BAD when stale, from `heartbeats.stale` and the `expected_intervals` `--check` uses), and "pages in our 8 areas updated in the last 14 days" (`pages.page_updated`); WARN under 60%, BAD under 30% (to tune once we see the real share) | `admin/health.py`, `seo/coverage.py` or a new `seo/freshness.py` | nothing | ₹0 |
| 2 | **AI answer panel** (was "AI search, next" above): weekly, 20 fixed buyer questions ("top projects in Upper Kharadi", "2 BHK under 80 lakh in Wagholi", "is <project> delayed"), asked through Gemini with Google Search grounding; record the sites each answer cites, keep our share of citations beside MagicBricks, 99acres and Housing on the scoreboard, and show any question we drop out of on Rankings | new `seo/answers.py`, `seo/scoreboard.py`, `RankingsTab.tsx`; key from `app.core.config`, off until set | a billing-enabled Gemini key (grounding is paid-tier only) | ₹0–20 |
| ~~3~~ BUILT 2026-10-26 | **AI answers → leads**: add Copilot, Gemini, Claude and the other `aivisits.REFERRERS` hosts to `origin.REFERRER_SOURCES`, read `utm_source` as the source when no `src=` is set, and add a line to the weekly note ("AI answers: 40 visits, 6 enquiries") | `tracking/origin.py` (one list for both, so they cannot drift), `seo/note.py` | nothing | ₹0 |
| 4 | **Bing Webmaster API** (was "AI search, next" above): Bing's searches and positions into `search_demand` (source "bing") | `areastats/` beside `searchconsole.py` | the API key from Bing Webmaster Tools (section 7) | ₹0 |
| 5 | **Weekly note on WhatsApp** (item 9 above): `report.week_lines` plus the freshness share and the AI panel line, once a week to the owner | `seo/note.py`, `whatsapp` | an approved utility template | ~₹2 |

Prices, checked 2026-10-26 against the providers' own documentation (through search: their pages are blocked from our build
machine). Read them again before switching a paid step on:
- **Gemini grounding** (Gemini 3 and newer): 5,000 search queries a month free, shared by every Gemini 3 model on the project,
  then $14 per 1,000. Billed per search the model runs, not per question, so one question can use two or three. 20 questions a
  week is about 87 a month, roughly 200–300 searches: inside the free allowance, so we pay only for the tokens (a few rupees on
  Flash). Gemini 2.5 models bill per prompt, at $35 per 1,000 after the free tier, so the panel uses a Gemini 3 model.
- **Perplexity Sonar** (kept as an option: its answers sit closer to ChatGPT search than Google's do): about $1 per million
  tokens plus $5–12 per 1,000 requests (Sonar Pro $3/$15 per million and $6–14 per 1,000), so about ₹100–250 a month for the
  panel. Sonar's Chat Completions API is being retired in favour of the Agent API (a third-party guide gives 27 Sept 2026);
  check which one is current before building on it.
- **WhatsApp**: Meta charges per delivered template message by the recipient's country, and since 1 Oct 2026 utility messages
  inside an open customer service window are charged too (they used to be free). The India utility rate is on Meta's INR rate
  card (not read here; third-party guides give ₹0.12–0.35). Four messages a month costs under ₹2 either way, plus 18% GST.
- **Bing Webmaster API**, step 1 and step 3: free.

As built (2026-10-26):
- Step 1: `seo/freshness.py` (daily, in the seo loop) counts the live project pages in our 8 areas (indexable, a group's primary,
  not finished) whose `page_updated` is within **35 days**, not 14: the details read comes back every 30 days by design
  (`refresh.DETAILS_MAX_AGE_DAYS`), so 14 would be amber on a healthy site. Health shows "Project pages up to date" (amber under
  70%, red under 40%, with the oldest pages), "SEO loop" (red when its heartbeat is stale, shown only while the loop is on) and
  "Project page refresh" (the `project_enrich` heartbeat; amber when `PROJECT_ENRICH_ENABLED` is off). `admin/health.loop_row`,
  `freshness_row`. The 70/40 limits are a first guess: read the real share for two weeks and set them.
- Step 3: one list of assistants, `tracking/origin.AI_REFERRERS` (+ `AI_UTM`), read by both the lead sources and
  `seo/aivisits`. AI hosts are matched before the search engines (a Gemini visit was counted as "google" before). A lead's
  source takes an AI `utm_source` before the referrer (ChatGPT's app often sends none). The weekly note says "N enquiries
  from AI answers (ChatGPT 2, Gemini 1)" (`origin.leads_from_ai`, read only). Leads stored before this keep the source they
  were given (an old Gemini lead stays "google").

Off-page upkeep (OWNER, no money, 1–2 hours a week): see section 7, "Weekly and monthly upkeep".

## 8b. Hard to replace (TARGET, 2026-10-26)

**Can a competitor replace us?** The pages and the code, yes: the MahaRERA register is public, our page format (dated answer,
FAQ, JSON-LD, `/llms.txt`) is visible in the HTML, and the seo loop is a few months of engineering. MagicBricks, 99acres and
Housing have far more domain authority, and a first place in ChatGPT can change within weeks. What they cannot copy:

| Ours | Why it cannot be copied |
|---|---|
| **History** read over time: homes booked (`booked_history`), filed completion dates (`completion_history`), prices, Search Console | MahaRERA and the builders show only today's value. A newcomer starts from zero, and the gap grows every month we keep reading. |
| **Hand corrections**: `builder_pages`, `marketed_name_override`, `pune_places.VERIFIED`, towers merged (`clusters.py`), checked pins | Thousands of small fixes; a copy inherits MahaRERA's mistakes |
| **Neutral facts**: "the date moved 4 months", "244 of 416 booked" | The portals are paid by builders; facts that are bad for a builder are bad for their business. They have had the data for years and do not show it. |
| **Agents and leads**: agents on the platform, leads passed to them, their posts linking our pages | Grows with use; a newcomer has none |
| **Links, mentions and the doctor's measured fix results** | Earned over time |

Threats, most likely first: (1) we let it go stale (section 8a); (2) a portal takes the format for Pune: we lose some broad
searches, keep the register long tail; (3) a copycat scrapes our pages: Google usually credits the page it indexed first,
which our sitemap dates and IndexNow help; blocking scrapers would also block the AI crawlers we want, so we do not;
(4) Google or the assistants change how they choose. Facts with their sources tend to survive that.

**Checked against the code on 2026-10-26: we are throwing part of the history away.**
- Prices: every read replaces `prices` on the record (`areastats/prices.py`: `{"prices": {at, name, rows, read}}`). No earlier
  price is kept anywhere.
- Homes booked: `booked_history` keeps the last `refresh.BOOKED_HISTORY` = 24 readings (one per change, read every 30 days),
  so readings older than about two years fall off.
- Completion dates: `completion_history` is pushed and never cut. Kept in full.
- Search Console: `gsc_history` and `rank_history` keep the last `HISTORY` = 60 readings (`searchconsole.py`, `demand.py`);
  the site totals are on the daily snapshot. Enough for the 28-day comparisons, so left as is.
- Already on pages: homes booked in the last window (`pagefacts.sales`), months the date moved net of the 2026 blanket
  extension (`pages.months_later`), and a builder's date record (`pages.delivery`: `moved_later`, `avg_months_later`). Not shown: the
  readings themselves (dates and values).

The build, in order. H0 is urgent: a day we do not keep a reading is lost for good.

| Step | What | Code (owner of the data) | Cost |
|---|---|---|---|
| ~~H0~~ BUILT 2026-10-26 (enrichment's read fixed the same day) | **Keep every reading.** Each price read appends `{at, size, low, high, source}` to `price_history` (the current `prices` stays as it is); `booked_history` is no longer cut at 24 (one reading a month is ~12 small rows a year; cut only past 120); a test pins that no reading is lost | `areastats/prices.py`, `areastats/refresh.py`, writes through the `projects` store as today (inventory owns `projects`, ARCHITECTURE §4) | ₹0, a few MB a year |
| ~~H1~~ BUILT 2026-10-26 | **History on the project page**: "Homes booked" as a small month-by-month chart with the dated readings in text below it ("312 booked on 3 Jul, 344 on 2 Oct: 32 in 3 months"), and "Completion date" as a timeline of every filed change ("16 Aug 2032 → 16 Dec 2032, MahaRERA's 2026 extension for every project; → 16 Feb 2033, the builder"). Shown only with 2+ readings; server-rendered SVG, no script; one sentence of it in the dated answer | `pages.view` (`booked_readings`, `completion_moves`), `frontend/components/site/` new `ProjectHistory.tsx`, `projectFacts.ts` | ₹0 |
| **H2** | **Price history** once a size has 2 readings 30+ days apart from the same kind of source: "2 BHK asked from ₹69 L (Jul) → ₹72 L (Oct), builder's site". Never mixed sources in one line; prices older than 45 days stay out of the "today" price as now | `pages.view`, `ProjectHistory.tsx` | ₹0 |
| ~~H3~~ BUILT 2026-10-26 | **Builder record over time** on `/builders/<slug>`: every project's filed date moves in one list, with the share moved and the average months, from the same rules as `pages.delivery` | `hubs.builder_page`, `app/builders/[slug]/page.tsx` | ₹0 |
| **H4** | **A monthly Avasetu report**: "Pune possession dates, <Month YYYY>": date moves seen this month by area and builder, homes booked by area, written by code from H0's data (no model), as a page on `/pune-maharera-tracker` with a dated URL, a Dataset JSON-LD and a CSV download; the owner sends it to journalists (section 7) | `areastats/` new `report_month.py`, `frontend/app/pune-maharera-tracker/` | ₹0 |
| ~~H5~~ BUILT 2026-10-26 (searches by name; the source named on H1's readings) | **Name the source**: every number in a dated answer and in H1–H4 says "read by Avasetu from MahaRERA on <day>"; the weekly note shows branded searches ("avasetu", any spelling) from `search_demand`, the sign that people look for us by name | `projectFacts.ts`, `placeFacts.ts`, `seo/note.py` | ₹0 |
| H6 (a) BUILT 2026-10-26, (b) TARGET | **Watch for a copy**: (a) from the stored Serper results (`websearch.RESULTS`), flag when a portal's result for our target searches starts showing homes booked or a date move (they took the format); (b) once a month, search 2 sentences unique to our pages and list any other site that shows them | `seo/rival.py`, `seo/scoreboard.py`; 2 Serper searches a month | ~₹0 |
| **H7** | **Facts people bring** (owner to decide each): dated site-visit photos from agents on the project page, buyer reviews (moderated, the copy guards before showing), verified agent listings first in their area | `listings`, `showcase`, new review flow | ₹0 code; owner time to moderate |

Marathi pages stay under "AI search, next" above. H0 first and alone (it changes what we store, so it ships with its tests
before anything reads it; BUILT 2026-10-26: `prices.history` adds a reading per size when the price is new or changed, never on
a round that kept the last good prices; `refresh.BOOKED_HISTORY` 24 → 120, and `prices.PRICE_HISTORY` = 400);
H1 BUILT 2026-10-26: `pagefacts.booked_readings` (one per day, the latest 12, only with 2+) and `pages.completion_moves` (each
change seen, `blanket` when it is MahaRERA's 2026 order: 4 months later, registered before the order, from a date it covers)
in the page data; `components/site/ProjectHistory.tsx` under the possession date ("<name>: what changed, as we read it": a
server-drawn bar chart, the readings in text, each date change named as the builder's or MahaRERA's, "Read by Avasetu from
MahaRERA on each date shown"); the opening answer adds "N of them were booked since <first reading>, by Avasetu's readings of
MahaRERA" when the count rose. H3 BUILT 2026-10-26: `hubs.date_moves` (the builder's later filings, the order left out, newest
first, at most 30) on `GET /public/builders/{slug}`, shown by `components/site/BuilderDateMoves.tsx` in the date record; H5 BUILT 2026-10-26: `seo/note.branded` adds up Search
Console's fresh 28-day numbers for every phrase naming us (`note.BRAND`: avasetu, ava setu, avsetu, awasetu, aavasetu,
avasethu, आवासेतु) into "Searches for Avasetu by name" in the weekly note; H1's readings and sentence already say "read by
Avasetu from MahaRERA" (the place and project answers do not yet); H6a BUILT 2026-10-26: `scoreboard.portal_format` counts
portal results (MagicBricks, 99acres, Housing) whose title or snippet shows homes booked or a moved completion date, kept as
`format` on the weekly scoreboard mark, and the note says "Watch: <portal> results now show …" from 3 such results
(`FORMAT_ALERT`). Not shown on the Rankings tab yet; H6b (searching our own sentences) is not built. The weekly note is now
sent as two Studio notifications (three with the watch): one text was longer than a notification (300 characters) and lost
its AI line; H1–H3 after 2 readings exist on most pages; H4 after H0 has run a month; H5 and H6 any time; H7
when the owner decides.

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
| 2026-10-22 | (this) | Homes registration as group primary; this-project-only page gate; hand-checked builder pages, names, places |
| 2026-10-21 | 9cbba482, 0d55a7ca | Doctor rival fix (+ price refresh), Indexed by area, panel of target searches |
| 2026-10-25 | 20d88ba7..6e68f483 | Ask-Google list ordered by value; gaps from our own Serper searches; descriptions within 160 characters; Serper per day counts the prices round (35) |
| 2026-10-21 | 886047b | Place pages say "flats" in title, H1 and description |
| 2026-10-21 | aaf7c45 | Search phrases name a place however it is spelt (`pune_places.in_search`) |
| 2026-10-21 | f43252f, 1ab4a00 | Every way buyers search: size pages from published prices, "Flat prices in X", Place `alternateName`, flats wording and links, owner map, rank watch for the families |
| 2026-10-21 | 7720a6d, d730c5c, 7abbe6f + this | AI search: AI visit log, AI fetcher audit, `/llms.txt`, Bing verification tag, quotable place pages (answer, FAQ, updated date) |
| 2026-10-21 | this | Prices round (own turn, every 15 min); enrichment and prices skip completed projects, put 90%+ booked last, and go area by area outward from Kharadi with new launches and hot projects first |
| 2026-10-25 | this | Project pages open with a dated answer + "Updated" (WebPage dateModified); news stories link the projects they name; `/llms.txt` lists project pages |
| 2026-10-22 | this | `/` is the buyers' home (one topic: new projects in Pune); the agents' home moved to `/agents`. Hot projects banner on every buyer page, set in Studio (`hot-projects.md`); robots guard test |
| 2026-10-25 | this | Tracker pages `/news/track/<slug>` (8) in the sitemap at 0.8, linked from `/news` and from the area pages they touch |
| 2026-10-26 | this | H5 and H6a: searches for Avasetu by name and a watch on portals showing our kind of fact, in the weekly note; the note sent in parts so none is cut off |
| 2026-10-27 | — | Owner, after the AI-referral list (31 visits in a week from ChatGPT answers, ~12 on west Pune area pages and lists that may now be noindex): "for now just concentrate on east Pune". West pages stay as merged (no Google-only noindex). Enrichment: a hot project outside east Pune no longer jumps the queue; east Pune's hot projects, Top lists and banner picks first, then area by area outward from Kharadi, so east area pages and lists reach their projects-in-search counts first |
| 2026-10-27 | — | Templated-page audit after the 10-26 drop, what was still asked of search besides project pages. Cut from search (noindex, out of the sitemap, still served): place pages with no project in search, area lists with fewer than 3 projects in search (both were the same template over register-only rows), neighbourhood articles (one model prompt per neighbourhood), locality stubs for any place name an agent typed ("We do not have a full buyer guide for X yet"), and `/posts` pages (copies of our social posts). Kept: curated locality guides, topic guides, trackers, the MahaRERA tracker, builder pages with 2+ projects in search, news. Merge: none in code; Upper Kharadi locality → guide was done earlier today. Not changed: news stories (50 newest listed; recheck if impressions stay at zero), agent sites (their own listings) |
| 2026-10-27 | — | Less machine-made: page doctor and title targets on hold until 2026-11-17; a page in search keeps its text 14 days; lastmod moves only with a real text change (was every enrichment round: 421 of 503 pages re-dated in a week); AI illustrations left off pages in search and no longer count as a page's own content (41 pages had them). Open: 123 pages in search show photos copied from property sites (MagicBricks and others) |
| 2026-10-27 | — | Indexed-but-not-ranking checklist against Search Console (28 days): 160 of 2,563 searches show 2+ of our pages (12% of impressions). Area: /localities/upper-kharadi and /guides/upper-kharadi both ranked for "upper kharadi"; the locality page now names the guide as canonical and leaves the sitemap. Towers and duplicates (Mihir Amara, Gulmohar Park Dehu, Krishna Prabha Aangan: no promoter, so never grouped) are all noindex since `pages.searchable`; grouping rule unchanged. Site CTR 2.3% at position 9.4 is normal; locality pages 0.3% |
| 2026-10-27 | — | Checked, nothing changed: owner saw /projects/area/upper-kharadi gone for "new projects in upper kharadi". All loops OK, pages 200 and indexed (URL inspection PASS, crawled 10-24). Search Console: that query had 2–3 impressions/day at average 8–8.5 (bottom of page one); 10-27 it is outside the top 20 (Serper, Pune), with Housiey, Housing, VJ, 360realtors, NoBroker, 99acres, MagicBricks above. Brand: on 10-27 Google answers "avasetu" with "results for Seva Setu"; the home page had been at position 1–2 on 10-17/18 and 10-22/23 (brand searches are too rare for Search Console to name, so they show only as home-page impressions); no knowledge panel, so the Business Profile is not showing. Site-wide: still indexed (site: query, URL inspection); traffic is long tail (≈1,500 pages a day at positions 5–8); head searches were never ours (new projects in kharadi 13–49, Ivara 0 impressions, Camelot ~90); 10-26 reads 3,046 impressions on 1,208 pages vs 4,221 on 1,512 the day before, positions unchanged; recheck when 10-26/27 data is final. Later 10-27: site-wide drop confirmed. 0 of the 13 searches where we were at positions 3–6 on 10-23/25 show us in the top 20; with "avasetu" added to the search our page is first, so pages are indexed but ranked nowhere (manual action or a site-wide filter). Not blocked: Google crawled fine until 10-26 15:32 UTC. No announced Google update after the September spam update (ended 10-08). 13,181 URLs in our sitemaps on a weeks-old domain, ~500 of them enriched: the likely cause is the "scaled content" policy. Owner checked: no manual action, no security issue, so an automatic site-wide filter. Fix: project pages in search only with content of their own (`pages.searchable`), builder pages need 2 of them; ~11,300 project and most builder pages leave the sitemap and turn noindex. Recovery takes weeks. Fixes are 8a/brand items, not a broken page |
| 2026-10-26 | d7443ae | H1 and H3: project pages show the dated booking readings and every date change we saw (builder or MahaRERA's order); builder pages list the dates each builder filed later |
| 2026-10-26 | 563361e | 8a steps 1 and 3: Health rows for the seo and enrich loops and for fresh pages (`seo/freshness.py`); AI assistants as lead sources from one list, Gemini no longer counted as Google, enquiries from AI answers in the weekly note |
| 2026-10-26 | 203a3d3 | H0: every price change kept, dated, in `price_history`; homes-booked readings kept to 120 (were cut at 24) |
| 2026-10-26 | this | Top page as the buyer's shortlist: 10 ranked cards (picture with its source, stage, price or "Get the price", homes open), rows of cards into Just launched / Move in now / 2 BHK, a "Sold out or nearly" table with a resale ask, FAQ on why a sold out project is not ranked. Area pages get rows of cards (Top, Just launched, Move in now); the home page links every area's Top list and shows the biggest as cards. Rows are swiped on phones, never move by themselves, hidden under 3 cards |
| 2026-10-26 | this | Top lists (`/projects/area/x/top`) rank only projects with 10+ homes open (`facets.OPEN_MIN`); sold out and nearly sold out projects move to `sold_out` (shown apart, with a resale ask). Kharadi's first 7 were 100% booked. Every list row carries stage, cheapest published price and one picture for the cards; the answer counts the whole list, not the 30 shown |
| 2026-10-26 | this | H0 fix: the page enrichment's own MahaRERA read now keeps the homes-booked reading and a moved date too (`areastats/readings.py`, shared with the register refresh). It refreshed `details_checked_at`, so the refresh skipped those records and their readings were lost: on 26 Oct no Pune record had two booked readings and Kharadi had none, so "booked in 90 days" never fired |
| 2026-10-26 | 96d4dcd | Plan only: section 8b (what a competitor cannot copy; prices and old booking readings are thrown away today; H0 keeps every reading, H1–H7 show the history and widen the lead) |
| 2026-10-26 | 0f19643 | Plan only: section 8a (keeping the lead: freshness and stalled-loop rows, AI answer panel on Gemini grounding, AI answers → leads, Bing API, WhatsApp note, with checked costs) and the owner's weekly and monthly upkeep (section 7) |
| 2026-10-26 | this | Owner: "our main target is east Pune", "top projects should be totally enriched", "why Move in now when no flats are left". Home page lists our areas first in the area list's order (east Pune leads), so its row of cards is Kharadi's Top list, not Moshi's (the biggest). The rule moves to `areastats.pages.buyable` (homes, not finished, 10+ open); offices and shops (MahaRERA type Commercial) leave Top and Move in now. Move in now (`ready-to-move`) lists only finished projects with 10+ homes not booked (Kharadi had 0 of 142 and unknown counts). East Pune Top-list projects (`pricing.on_top`) are enriched and priced with the hot ones, premium model budget, pictures read even after the completion date while homes are left |
| 2026-10-26 | this | Owner: "is it link to new projects", "projects on main pages enriched quickly on priority". Home area cards count projects being built or finished within a year (`places.current`; Kharadi said 303, every registration ever), the link stays the area page. The owner's banner picks (`spotlight.picked_slugs`, through wiring) are enriched with the hot ones and the east Top lists (`enrich.featured`) |
| 2026-10-26 | this | Review of home, Top and area pages: size lists show their size's price (96 Arrcade's 1 BHK ₹34.99 L sat on the 2 BHK row) and leave out projects with every home booked; web pictures say "Photo from the web" (was "Not checked by us"); Top lines say "most homes booked first" (booked lately needs two MahaRERA readings, not there yet); the ranked card no longer repeats the homes-open line; the home area count matches the area page (one per project, 136 vs 110) |
| 2026-10-26 | this | Designer review of `/projects/area/kharadi` (only the parts that fit our data; dark map, 3D and time slider not taken): area pages open with a strip of four numbers (projects, % booked, 2 BHK from, past completion date) above the answer sentence, which stays word for word; the second paragraph stays, smaller. The ready-to-move row is "Completion date passed" and its cards say "Due <month> · ask for OC" (the list page and chip keep "Ready to move", the searched words). Row cards without a price show homes booked and an "Ask the price" button that opens the chat about that project; a launch with nothing booked says "booking just opened"; no picture shows the skyline, not a letter. The map's H2 is "Busy lately in <area>, on the map" (was "Most active projects", a second ranking beside Top). MahaRERA names in capitals are shown in normal case on cards, map and lists |
| 2026-10-29 | this | Enrichment stops downloading other sites' pictures (the 2026-10-22 "best we can find, from the web" fallback): no page shows them, so it was up to 40 image downloads per project round and a scan of every project's pictures (`others_pictures`, the stock-picture check that only web pictures needed) for nothing. Model calls and the Gemini budget are unchanged (pictures are code). Other sites' pages are still read for highlights and web facts. The stored web photos stay and still keep a project from getting illustrations; a new project with no builder or brochure picture now goes straight to AI illustrations, shown only on pages out of search |
| 2026-10-29 | this | Photos copied from other sites leave the pages (rule 9: no copied portal data). 663 photos with source `web` on 131 of the 215 pages in search with pictures (housiey 201, magicbricks 106, aurumproptech 66, squareyards 53, reraspace 40, other agents). `pages.shown_pictures` leaves them (and web floor plans) out of the project page, the agent pages' profile, the cards on area pages, Top lists and the map; JSON-LD, OG and the hero already took the builder's only. `has_own_content` no longer counts them. Measured in production before the change: all 131 had web photos only (never beside the builder's), so those 131 pages now show no picture (the skyline on cards, no gallery), and 0 leave search. The photos stay stored (section 8b: never throw a reading away). The "Photo from the web" labels and credits are gone |
| 2026-10-29 | this | Buyers first (owner: "our main goal is now end users, not agents. When someone searches avasetu, it should be able to search projects"). A home-page brand change, not a page-doctor title fix, so the 11-17 title hold does not apply. Google answered "avasetu pune" with `/agent/avasetu` ("Avasetu Homes \| Real estate in Pune") then `/trial`; no title on `/` named us. Home title "Avasetu: Search New Projects in Pune, Checked Against MahaRERA" (62 of 70), description and Organization/WebSite description buyer-first, `alternateName` आवासेतु (the repo's Devanagari form; "Ava Setu" is only a misspelling we count, so left out), `sameAs` stays the Facebook Page and Instagram (no WhatsApp: a chat link, not a profile). H1 unchanged. `/agent/avasetu` keeps working (2 listings, Lodha Camelot, the enquiry form every buyer button opens, so no 301) and names `/` as canonical, leaves the sitemap, links `/` under its hero, credits Avasetu with a link to `/`. `/agents` puts the brand last; `/trial`, `/request-invite`, `/for-agents`, `/for-agents/guide` noindex. The house page's About text ("The official Avasetu page") is its bio in the data: owner to edit in Studio |
| 2026-10-29 | — | Checked, nothing changed: Search Console API diagnostic (dataState all). Impressions per day rose from 87 (10-10) to 4,223 (10-25), then 3,098 (10-26), 116 (10-27), 82 (10-28). Every page type fell about 97% between 10-26 and 10-27 (project pages 2,474 → 72, builders 433 → 34, localities 129 → 2), and pages shown per day went from 1,649 to 96. Pages still shown keep their old positions (Maitri Meadows 7.6 → 7.3, Prasun Elara 7.8 → 6.9): the site is shown for far fewer searches rather than pushed down. URL inspection on home, Kharadi area page, Kharadi top, Upper Kharadi guide and two former top project pages: all PASS, indexed, Google canonical = ours. The drop came before the 10-27 noindex cut could take effect, so the cut did not cause it. No brand query is listed (too rare). Sitemap index read 10-29 13:48 but still reports 7,357 URLs (live: 506); leave it to refresh. Loops OK, key set. Wait; recheck about 11-10 |
| 2026-10-29 | this | Fix: `grow.live_pages` handed bare records to `facets.in_search`, which takes (record, reason) pairs (since 5fa45feb on 10-27 evening), so `GET /api/v1/public/facets` answered 500 on every call: the area-list chips on place and project pages and the list's sitemap entries were empty for two days. Test `test_the_live_page_list_counts_each_pages_projects_and_says_whether_search_may_index_it` |
| 2026-10-29 | this | Search boxes (home hero, header, /projects) answer areas: a search naming one of our places shows its area page first, or its live size or kind list ("2 bhk kharadi" → /projects/area/kharadi/2-bhk, "top projects wagholi" → its Top list; `seo/placesearch.py`, `GET /api/v1/public/search/place`). Search or Enter opens that page, or the one project found, else /projects?q= (the hero's button did nothing). A word of a project's name ranks before letters inside another word ("ivara": Godrej Ivara before Bhide Nivara) |

## 12. Detail and history

Design and reasoning behind the pieces above (read for the why; this page holds the current state):
[rank-loop.md](rank-loop.md) (doctor, targets), [index-everything.md](index-everything.md) (indexing, scoreboard),
[area-intent-pages.md](area-intent-pages.md) (area list pages), [insights-and-seo.md](insights-and-seo.md) (owner screens),
[seo-review.md](seo-review.md) (code review), [seo.md](seo.md) (first plan, 2026-10-04), [topic-pages.md](topic-pages.md),
[project-pages.md](project-pages.md).
