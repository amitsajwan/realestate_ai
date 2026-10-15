# Area intent pages: new launches, top projects and ready-to-move, one page per search intent per area (2026-10-15)

Status: **BUILT, not deployed** (2026-10-15): weeks 1 and 2 of section 8. Weeks 3 and 4 (retire with 301, learning per
type, landmarks, Pune-wide, round-up story, vocabulary proposals) are still **NEW**. What differs from the plan is in section 12. Labels: **LIVE** = running in production, **BUILT** = in the code, not deployed, **NEW** = to build.
Builds on `rank-loop.md` (R1 targets, R2 self-competition, R5 links, R7 gap pages) and `hot-projects.md` (launch and bookings
signals). Nothing here replaces those; it adds the area-level pages they point at.

## 1. Why

Buyers in Pune don't search for a project they haven't heard of. They search for a **list**: "new launch projects in Kharadi",
"upcoming projects in Wagholi", "top projects in Hinjewadi", "ready to move flats in Wakad". The portals rank for these with thin
lists of whoever paid them. We have something they don't: the MahaRERA register for every project, with registration
date, filed possession date (and whether it moved) and homes booked, read on a known date. A list ranked on those facts is
the most useful answer to a list search, and it's hard to copy.

The area list pages are also how we solve the **indexing bottleneck** (`rank-loop.md`, 2026-10-14 baseline: 100 project pages
"Discovered, not indexed"). Strong hub pages that Google crawls often, each linking 10 to 30 project pages, are the normal way
project pages get crawled and indexed.

## 2. What exists (do not rebuild)

| Piece | Where | State |
|---|---|---|
| All projects in a place: "New Projects in <place>, Pune: Price, Possession, MahaRERA (N)" | `frontend/app/projects/area/[place]` | LIVE |
| Locality guide: "<area>, Pune: projects, MahaRERA records and buyer guide" | `frontend/app/localities/[slug]` | LIVE |
| 2 BHK, 3 BHK and price-band pages per area | `frontend/app/2-bhk/[area]`, `3-bhk`, `price/[band]/[area]` | LIVE |
| Most active projects box (a fact and its source, never a score) | `areastats/hubs.py` `active` | LIVE |
| `launch` and `bookings` signals with dates | `areastats/hot.py` | LIVE |
| Our Google rank for "new launch projects in {area} Pune", "upcoming residential projects in {area} Pune" and one more phrase per area | `areastats/websearch.py` `AREA_QUERIES` | LIVE |
| Target phrase per page, self-competition report, page doctor | `seo/targets.py` and the rest of `rank-loop.md` | BUILT/LIVE per that plan |

## 3. Which searches we target (the intent map)

Each search intent gets **one** URL per area. Two of our pages must never answer the same intent, so this table is also the
rule for titles.

| Intent | How people search (examples) | Our page | Ranked by (public, factual) |
|---|---|---|---|
| New launches | new launch / new / upcoming / latest / pre-launch projects in Kharadi | `/projects/area/kharadi/new-launches` NEW | MahaRERA registration date, newest first (last 12 months) |
| Top projects | top / best / top 10 / popular / most booked projects in Kharadi | `/projects/area/kharadi/top` NEW | Homes booked in the last 90 days (MahaRERA), then total booked % |
| Ready to move | ready to move flats / ready possession / completed projects Kharadi | `/projects/area/kharadi/ready-to-move` NEW | Completion filed or OC on MahaRERA, newest first |
| Possession soon | possession 2026 / 2027 projects in Kharadi | section on ready-to-move (a page only if R7 shows demand) | Filed completion date |
| All projects | projects in Kharadi, residential projects, under construction projects Kharadi | `/projects/area/kharadi` LIVE (retitled, see 5) | Name A to Z (as today) |
| BHK and budget | 2 bhk flats in Kharadi, flats under 80 lakh Kharadi | LIVE pages, unchanged | as today |
| Living there | Kharadi pune review, is Kharadi good to live | `/localities/kharadi` LIVE | n/a |
| City level | new launch projects in Pune, top projects Pune east | `/projects/new-launches`, `/projects/top` NEW (week 3) | same rules, across our 8 areas |

**Pre-launch.** MahaRERA forbids advertising before registration, so we never list unregistered "pre-launch" projects. The
new-launches page answers the search honestly instead: a short block "Pre-launch offers in Kharadi: what's allowed" and the
projects registered in the last 90 days, which is what those buyers actually want. Portals can't write this paragraph
without hurting their own ads. This is a trust angle, and it's also what Google's AI answers tend to quote.

**Year and month.** URLs never carry a year (they stay the same for years and keep their rank). Titles do carry the month,
because people click "Oct 2026" over an undated list: "New Launch Projects in Kharadi, Pune (Oct 2026): 7 registered with
MahaRERA". The month changes only when the data changed that month (see 6).

## 4. What's on each page (the anatomy that wins)

Top to bottom, the same component for all three intents (`AreaIntentPage`, one file, intent as a prop):

1. **H1 + answer paragraph** (40 to 60 words, numbers first): "As of 15 Oct 2026, 7 projects in Kharadi were registered
   with MahaRERA in the last 12 months. The newest is Lodha Camelot T7 (Sep 2026). 3 of them complete by 2028." This paragraph
   is what featured snippets and AI answers quote, so it's written from the data by code, never by the model.
2. **The ranked list as a table**: project (link), builder (link to `/builders/<slug>`), registered, possession filed (and
   moved by N months), homes booked %, configurations and price from (only when `webfacts` or a listing has it, with the source).
   On phones it turns into cards. Our listings get a small "Listed with Avasetu" link, never a higher rank.
3. **What changed this month**: new registrations, possession dates that moved, the biggest booking jumps, each one dated.
   This is the real freshness Google rewards, and it gives the sitemap date an honest reason to move.
4. **Filter chips to sibling pages**: New launches · Top · Ready to move · 2 BHK · 3 BHK · Under 80 L · All projects ·
   About Kharadi. These are the internal links that tie the cluster together.
5. **FAQ** from Google's "People also ask" for this phrase (`search_demand` questions), answered from the data only; R4 rules.
6. **How we ranked this list**: one paragraph, the MahaRERA source and the read date. This builds trust (E-E-A-T), and it's
   also our answer if anyone asks why their project isn't first.
7. **Nearby areas**: the same intent in neighbouring areas ("New launches in Wagholi, Viman Nagar"), from `app/core/areas.py`.

Structured data: `ItemList` (each project's URL in order), `BreadcrumbList`, `FAQPage`, and `dateModified` = the last real change.
FAQ rich results only show for government and health sites since 2023, but the markup still helps AI answers read the page.

**Thin-page rule**: a page with fewer than 3 projects is `noindex, follow`, and the sitemap leaves it out until it has 3. Wagholi
will have plenty; a quiet area won't, and a near-empty list hurts the whole site.

## 5. Not competing with ourselves

- `/projects/area/<place>` today has the title "**New** Projects in <place>", which is the new-launches intent. Once the
  new-launches page exists, the area page is retitled "Residential Projects in <place>, Pune: all N on MahaRERA" and links
  to it from the top. **Check first**: if Search Console shows the area page already ranks for "new projects in <place>"
  (R1 target), move that phrase to the new page with a link swap and watch it for 28 days; don't redirect.
- The locality guide keeps "living in / review" intent and drops "projects" from its title's lead.
- R2 (`seo_conflicts`) watches the new paths like any other; a phrase showing two of our paths goes on the owner report.

## 6. Staying on top (the freshness engine)

Ranking for a list search is won by the page that's **right this month** and that Google trusts to stay right.

| Lever | How | Cost |
|---|---|---|
| Data refresh | Pages render from the register on each request (`revalidate = 300`, like today) | none |
| Honest dates | `page_updated` for an intent page = newest real change among its listed projects (registration, booking read, possession move), never a timer. IndexNow on change. | small, reuses `seo/` |
| Month in title | Changes only when "What changed this month" isn't empty | none |
| Monthly round-up | On the 1st, an `/insights/<area>-new-launches-<month-year>` story (newsroom pipeline, facts only) that links to the evergreen page. It catches "new launches October 2026" searches and sends a fresh link to the hub every month. | one LLM call per area per month |
| Social links | The morning MahaRERA reel and posts link to the intent page, not the home page (`reach-captions`) | none |
| Rank watch | `AREA_QUERIES` gains "top projects in {area} Pune" and "ready to move flats in {area} Pune" (Serper budget stays at ~20 a day; the rotation just gets longer) | none extra |
| Page doctor | The three intent pages per area go into R3's queue like project pages | none |

## 7. Architecture

- **Backend** `areastats/intents.py` NEW: `intent_list(db, place, intent) -> {items, answer, changes, counts, updated}`, one
  function per ranking rule, pure functions over the register so they're easy to test. Route
  `GET /public/areas/{place}/intents/{intent}` in `areastats/router.py`. No new collection: everything comes from fields
  we already store (`registered_on`, `booked_history`, completion, `gsc_*`).
- **Frontend** `frontend/app/projects/area/[place]/[intent]/page.tsx` NEW + `components/site/AreaIntentPage.tsx`;
  `generateStaticParams` over places x 3 intents; titles in `lib/site/seo.ts` beside the project titles.
- **Sitemap** `sitemap.ts`: the intent pages that pass the 3-project rule, with `page_updated` as lastmod.
- **Links in**: home page "New launches by area" strip, area page chips, every project page gets "More new launches in
  <area>" (launched in 12 months) or "Top projects in <area>", and the newsroom stories link to the intent page for their area.
- **Rules held**: facts with sources only, no hot score or badge in public (decision 2026-10-13), guards on any generated
  text, areas only from `app/core/areas.py`.

## 8. Order

The three intents are built as the first **facets** of the growth engine (section 11), not as three hand-made pages, so
the site starts growing on its own from week 1.

| Week | Build | Done when |
|---|---|---|
| 1 | Facet model, `seo_pages`, one renderer (`AreaIntentPage`) and its route; new-launches and top seeded for every register place; the gates (11.3); sitemap; links from area and project pages | seeded pages that pass the gates are live and in the sitemap; the rest wait as `candidate` |
| 1 | Retitle `/projects/area/<place>` after the R1 check (section 5) | no phrase shows both paths in `seo_conflicts` |
| 2 | Phrase parser and vocabulary (11.2); the weekly `grow` job (discover, gate, create, cap); facets for ready-to-move, possession year and BHK x budget; the change block; FAQ | the first pages grown from real phrases show on the owner tab |
| 3 | Pruning and retiring with 301 (11.5); learning per facet type (11.6); landmark facets from Google pins; Pune-wide facets; monthly round-up | the job both adds and retires pages with no one touching it |
| 4 | Vocabulary proposals from unknown words (11.2); owner review on the tab (11.7) | new words go from the report to live pages with no code changes |

## 9. How we'll know it works

Baseline on the deploy day, then at 14 and 28 days, for the 8 areas:
- indexed intent pages / submitted (target: all within 14 days);
- project pages indexed (today 84 of 223 inspected): the hubs should pull this up;
- our Serper rank for "new launch projects in {area} Pune" (today: record on day 1), target top 20 at 28 days, top 10 at
  90 days for the affordable belt (Wagholi, Lohegaon, Keshav Nagar, Upper Kharadi), where portals are weakest;
- clicks from the intent pages to project pages and to agent WhatsApp.

## 10. Decisions (owner delegates, taken 2026-10-15)

1. URLs nest under the area (`/projects/area/<place>/<intent>`), not top-level slugs like `/new-launch-projects-in-kharadi`:
   one cluster per area, cleaner links, and keywords in the path matter far less than the title.
2. "Top" is ranked by homes booked in 90 days (MahaRERA), shown as the reason on each row. It's a fact, not our score.
3. No year in URLs; month in titles only when the data changed.
4. Fewer than 3 projects means noindex, not a thin page.
5. Never list unregistered pre-launch projects; answer the search with the rules and the newest registrations.
6. The system grows by itself (section 11). Pages come from real search phrases and our data, pass fixed checks, are capped
   per week and retire on their own. A person only reviews the weekly report and can undo any page with one click.
7. A new page must list a set of projects that differs from every existing page (overlap under 70%). Otherwise the phrase
   becomes a target of the existing page instead. This stops growth from turning into the mass-produced thin pages that
   Google's scaled content abuse policy (2024) penalises.
8. Growth starts slow: at most 10 new indexable pages a week, raised only when 70% or more of the last batch got indexed.

## 11. The system grows by itself

The pages in sections 3 and 4 are the **seed**. From then on, a weekly job finds new searches and decides which ones deserve
a page. It makes those pages, watches them and retires the ones that don't earn. No one writes a page by hand.

```
 discover ──► parse ──► gate ──► create (capped) ──► tell Google ──► measure 14/28/90 d ──► keep / improve / retire
 (GSC, Serper    (phrase →    (demand,     (renderer +     (sitemap,           (impressions, clicks,      (page doctor,
  related, PAA,   facet)       supply,      seo_pages)      IndexNow)           index status)              301 to parent)
  autocomplete)                no overlap)                                                │
                    ▲                                                                     │
                    └──────────── learn which facet types earn (budget for next week) ◄───┘
```

### 11.1 A page is a facet, not a file

Every list page is a **facet**: `{place, intent, filters}`, e.g. `{kharadi, new-launches, {}}`,
`{wagholi, all, {bhk: 2, price_max: 6000000}}`, `{near: eon-it-park, ready-to-move, {}}`, `{pune, top, {builder: lodha}}`.
- One renderer draws any facet from the register, so a new page costs no code.
- Each facet has one **canonical key** (sorted fields). "2 bhk flats under 60 lakh Wagholi" and "Wagholi 2BHK below 60L" are
  the same page, so a new phrase can never make a second copy.
- The URL comes from the key: `/projects/area/<place>/<intent>[/<filter-slug>]`, e.g.
  `/projects/area/wagholi/all/2-bhk-under-60-lakh`. The LIVE 2 BHK, 3 BHK and price pages are registered as existing
  facets and keep their own URLs, so the engine knows about them and never duplicates them.
- New `seo_pages` collection: `{key, path, facet, phrases[], target, status, created_at, reason, metrics{...}, history[]}`.
  Status goes `candidate` → `live` → `retired`. Seeded and grown pages are the same kind of record.

### 11.2 Discover and parse phrases

Sources (all LIVE except one):
- Search Console queries (`search_demand`, daily): the searches that showed our pages;
- Serper related searches and "People also ask", from the searches we already run;
- **Serper autocomplete** (NEW): one call per area per week on seed phrases ("new projects in Kharadi", "flats in Kharadi").
  It returns up to 10 of the exact phrases Google suggests. That's 8 calls a week, inside the current budget.

`seo/phrases.py` (NEW) parses each phrase using a **vocabulary** kept in a data file, not in code:
- places: register places and their aliases (`kharadi`, `kharadi pune`, `eon kharadi`);
- intents: `new launch|new|upcoming|latest|pre launch` → new-launches; `top|best|popular|top 10` → top;
  `ready to move|ready possession|completed` → ready-to-move; `projects|flats|apartments` → all;
- filters: `2 bhk`, `under|below N lakh|cr`, `possession 2027`, `by <builder>`, `near <landmark>`, `plots`, `villas`.

Words the vocabulary doesn't know go on a weekly **unknown words** list, if the phrase had impressions. A model proposes
which existing filter each word maps to ("2bhk" → bhk 2; "below 50l" → price_max). The proposal is accepted automatically
when it maps to a filter we already have and a sample of the phrase's results checks out. A word that needs data we don't
hold ("gated community", "lake view") goes on the data gaps list for the owner and never becomes a page.

### 11.3 Gates: a candidate becomes a page only when it passes all of them

| Gate | Rule | Why |
|---|---|---|
| Demand | 10+ impressions in 28 days for the phrase (or all of the facet's phrases together), or 2+ sources show it (autocomplete, related, PAA) | no pages for searches nobody makes |
| Supply | 3+ projects match, each with real facts (`indexable`) | no thin pages (decision 4) |
| Distinct | its set of projects overlaps under 70% with every live page's set. If not, the phrase is added to that page's `phrases` (its title and FAQ can use it) | no self-competition, no doorway pages |
| Answerable | every filter maps to a field we hold, with a source | facts only |
| Budget | at most 10 new indexable pages a week (decision 8), most demand first | a site this young must grow steadily, not in bursts |

A candidate that fails waits and is checked again the next week. So, for example, an area's new-launches page appears on
its own once the area gets its third new launch.

### 11.4 Create and tell

A candidate that passes becomes `live`: the renderer serves it, the sitemap lists it, IndexNow sends it, and the parent page
links to it. The filter chips are built from the facet's children in `seo_pages`, so internal links grow along with the
pages. Each page made logs one `trace.event` line with the phrase and the numbers that passed the gates.

### 11.5 Watch, improve, retire

- At 14 and 28 days a page joins the page doctor's queue (R3) like any other page.
- At 90 days, a page that isn't indexed, or is indexed with under 5 impressions, gets `noindex, follow` and leaves the
  sitemap. It stays reachable, so no links break.
- If a page drops under 3 projects (projects completed or merged), it gets noindex until it has 3 again.
- At 180 days, a page that is still idle is **retired**: it answers 301 to its parent facet (`/2-bhk-under-60-lakh` →
  `/all`). A URL we made is never left to 404.
- If one phrase shows two of our pages (R2), the newer page is merged into the older one with a 301.

### 11.6 Learn which pages earn

Every facet type (intent x filter kind, e.g. "new-launches", "all + budget", "near landmark") keeps a running score: clicks
per page over 28 days, and its index rate. Each week's budget from 11.3 is shared out by those scores, with 2 of the 10
slots kept for types that have little data yet. Types that keep failing get fewer slots each week, so nobody has to switch
them off. This is the page doctor's "keep what worked" rule (R3), applied to whole types of page.

### 11.7 What the owner sees (Studio → Insights → Pages)

A weekly list of:
- pages grown: the phrase, the checks it passed and how many projects it lists;
- pages retired, and why;
- unknown words and data gaps;
- each page type's score.

Each page has two buttons: **Hold** (noindex now) and **Never** (never make this facet again). Everything else runs
without a person. The `SEO_GROW_ENABLED` kill switch stops new pages from being made; live pages keep working.

### 11.8 New places grow too

Places come from the register (`getRegisterPlaces`), not from the 8 focus areas in `app/core/areas.py`. Any place in Pune
gets its facets as soon as it passes the gates. If a phrase names a place the register doesn't know (say, a new township
name), it goes to the `discover.py` lookup the same way an unknown project does. The 8 focus areas still come first in
social posts and links, but they don't limit which pages get made.

### 11.9 Where it lives

| File | What |
|---|---|
| `backend/app/modules/seo/facets.py` NEW | facet model, canonical key, URL, and the project query for a facet (pure functions) |
| `backend/app/modules/seo/phrases.py` + `seo/vocabulary.yaml` NEW | phrase parser and vocabulary |
| `backend/app/modules/seo/grow.py` NEW | the weekly job: discover, gate, create, watch, retire, learn; logs to `trace` and reports in `--check` |
| `backend/app/modules/areastats/intents.py` NEW | rankings, the answer paragraph and the change block for a facet |
| `frontend/app/projects/area/[place]/[...facet]/page.tsx` NEW | one renderer for every facet; answers 301 when `seo_pages` says retired |
| `frontend/app/sitemap.ts` | lists live facets, with `page_updated` as the date |
| Studio Insights → Pages | section 11.7 |

## 12. Built 2026-10-15 (weeks 1 and 2), and where it differs from the plan

| Piece | Where |
|---|---|
| Facet model, URL grammar, rankings, answer paragraph, change block, titles | `backend/app/modules/seo/facets.py` (the plan's `areastats/intents.py` lives here instead: one module) |
| Phrase parser + word list | `backend/app/modules/seo/phrases.py`, `seo/vocabulary.json` (JSON, not YAML: no new dependency) |
| Weekly round: autocomplete, parse, gates, budget, `seo_pages`, owner view, hold/never | `backend/app/modules/seo/grow.py`, step `grow` in `seo/runner.py` |
| Public API | `GET /api/v1/public/facets`, `GET /api/v1/public/facets/{place}/{rest}` (`seo/router.py`) |
| Owner API | `GET /api/v1/newsroom/insights/pages`, `POST .../insights/pages/status` |
| Page | `frontend/app/projects/area/[place]/[...facet]/page.tsx`, chips `components/site/FacetChips.tsx`, `lib/site/facets.ts` |
| Links in | place page chips, project page links (`RegisterProjectPage` `lists`), sitemap |
| Owner tab | Studio → Insights → Pages (`app/studio/newsroom/insights/PagesTab.tsx`) |
| Rank watch | `websearch.AREA_QUERIES` adds "ready to move flats in {area} Pune" |

Differences:
- **Filters are what MahaRERA holds**: possession year and builder. BHK and budget come from agents' listings, so those
  searches attach to the LIVE 2 BHK / price pages (`existing` on the owner tab) and never become facets.
- **Ready to move** = filed completion date passed in the last three years; MahaRERA has no OC field, so every such page
  says to ask for the occupancy certificate.
- **Seeds**: new-launches, top and ready-to-move for every place with an indexable project; the 8 focus areas' seeds go live
  without using the weekly budget, other places' seeds take budget slots like searches do.
- **Place page title** (section 5): it changes to "Residential Projects in <place>" automatically once the place's
  new-launches page is live and indexable, instead of after a manual Search Console check. Place pages had very few
  impressions (61 for all project pages, 2026-10-14 baseline), so there was little rank to lose.
- **FAQ** is written by code from the page's numbers (two or three questions per intent); "People also ask" wording is not
  used on these pages yet.
- **Month in title** = the month of the newest dated change among the listed projects (registration, completion move,
  bookings), so it never changes on a timer.
