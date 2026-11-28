# Pune intelligence: research on every page, topics that update themselves

Decided 2026-11-28 (owner). Avasetu becomes the place Pune buyers check what is around a home: drive times, schools, asked rent,
what is being built and what is changing nearby, who works here. Every line is measured from data with its source and date;
no model writes a fact. It grows by adding a researcher (one file) or a tracker (one JSON file). SEO page: seo-system.md.

Status labels as seo-system.md: **BUILT** (on main, not deployed) · **LIVE** · **TARGET**.

## Rules for everything here

- Facts only, each with its source and the day it was read. A block with too little to say is not shown (no thin blocks, no
  thin pages: a page of its own is indexed only when `page_ready`).
- **Never religion, caste or community**, not even by listing places of worship next to "who lives here" (owner 2026-11-28).
  Places of worship leave the nearby lists.
- No school fees and no ratings (fees are rarely published reliably; ratings are Google's and cannot be kept).
- Rent is **asked** rent from listings, a range with how many listings and which month, shown only with 10+ listings, never "you
  will earn".
- Drive times are Google's typical traffic for a weekday 9 am and 6 pm, measured once a month per place (not per project), capped
  at `NEIGHBOURHOOD_ROUTE_ELEMENTS_PER_MONTH` (about Rs 1,000 a month, owner 2026-11-28).
- Paid or outside calls are switched in `neighbourhood/config.py`; any failure keeps the last good data.

## The pieces

### A. Topics that update themselves (newsroom, trackers)
1. A tracker's suggested status line that passes the existing checks goes live by itself (the old line stays in the timeline). A
   move to a tracker's last stage ("open", "running") still waits for the owner in Studio.
2. Each tracker has its own Google News searches, so its news comes in even when no area is named.
3. From 8 trackers to about 20, written from the reports we already hold (roads, flyovers, metro phase 2, Patal Lok tunnel,
   PMC building rules, property tax, stamp duty, PMRDA plan, MHADA lotteries).
4. A weekly topic finder groups reports no tracker matches; a subject with 3+ reports in 30 days goes to Studio To do as a draft
   tracker, added with one click.
5. Every tracker names the place slugs it touches; `neighbourhood` shows them on those places and their projects (`changes`).
6. Tracker pages are status pages for search: what it is, where it stands, next date, route/stations, areas that gain, timeline,
   FAQ, Article + BreadcrumbList data, dateModified from the last status.

### B. Neighbourhood research (`backend/app/modules/neighbourhood`, owns `area_research`, `schools`, `work_hub_research`)
One researcher per kind of fact in `researchers/`, run by the `neighbourhood` loop (newsroom role) when due:

| Researcher | What | Source | Refresh | Status |
|---|---|---|---|---|
| `commute` | drive times to the nearest work hubs, 9 am and 6 pm | Google Routes API, typical traffic | 30 days | **BUILT**; off in effect until the key allows the Routes API (403 on 2026-11-28) |
| `schools` | schools with board, level, affiliation number, distance | CBSE (SARAS) and CISCE official lists, placed on the map | 90 days | schools workstream |
| `rent` | asked rent by flat size: low, median, high, listings, yield | rental listings on the portals and our agents' listings | 30 days | rent workstream |
| `profile` | home mix being built, homes finished by year, nearby work/college/hospital/government/defence/industrial | MahaRERA register, places | 30 days | **BUILT**; home mix empty (the register has no homes per size) |
| `being_built` | projects and homes being built within 2 km, due years, biggest | MahaRERA register | 7 days | **BUILT** |
| `jobs` | companies at each work hub, homes near it | the hubs' own tenant lists | 30 days | **BUILT**; no hub has a tenant list we can read yet, so companies are empty |

Public reads: `/public/research/places/{place}`, `/public/research/projects/{slug}`, `/public/research/hubs[/{slug}]`,
`/public/research/pages` (the place sub-pages worth indexing, for the sitemap), shapes in `frontend/lib/site/research.ts`.

How each is measured (BUILT 2026-11-28, branch pi/research):
- **Places and centres** (`places.py`): the site's place pages (areastats `pages.places`), those in search first. A centre is the
  median of the place's own Google pins (3+), else the area's checked middle (areastats.landmarks), else the median of 1-2 pins.
  Only 1,153 of 12,975 register records have a pin (2026-11-28).
- **Commute**: from the place centre to the 4 nearest hubs plus the airport. 9 am out, 6 pm back, next weekday; each asked with
  Google's OPTIMISTIC and PESSIMISTIC traffic models, so a row is Google's low-high minutes for that hour (4 reads a hub, 20 a
  place). A project page shows the place's times "from the <place> centre" with the straight-line km from its own pin.
- **Being built**: one row per project page (towers summed), projects filed under the place plus pinned ones within 2 km of its
  centre; on a pinned project page, pinned projects within 2 km of the pin when there are 3+.
- **Profile**: homes finished by year since 2015 (filed completion passed), checked places within 10 km (hubs, areastats
  landmarks, the nearest running metro), and 2-4 sentences by code. No government or defence list yet (no checked positions).
- **Jobs / hubs**: 14 hubs in `data/hubs.json` (positions from OpenStreetMap, each with how it was checked). Companies only
  from a hub's own published list (`companies_url` + `companies_pattern`); none found for any hub on 2026-11-28, so none shown.
  Homes for sale within 5 km from the project pages with pins; drive times from every place that measured the hub. A hub page
  is ready to index with 3+ companies or drive times from 3+ places.
- **Places of worship** left every nearby list: propertyfacts surroundings no longer gathers temples and its fact sheets,
  posts and the project page's Location "Nearby" (propertyfacts/public.py) drop old ones; an agent's listing text naming one
  is not kept (ai_listing/about.py); areastats' fact sheet skips them (areastats/enrich.py).
- **Chat**: each place's commute, schools, rent, being built and profile go into the knowledge index as one passage each
  (`views.knowledge_passages`, wired in `app/wiring.py`).

### C. Pages (BUILT 2026-11-28 on `pi/site`, not deployed; against fixtures until the researchers fill the data)
Built in `frontend/`: reads in `lib/site/research.ts` (`getPlaceResearch`, `getProjectResearch`, `getHubs`, `getHub`,
`getResearchPages`; a 404 is "nothing yet", an outage is never kept), words and structured data in `lib/site/researchPages.ts`,
blocks in `components/site/research/`. A sub-page needs its own block (404 without it) and is noindex until `pages.<kind>`.
The sitemap lists the sub-pages from one read, `GET /public/research/pages` -> `{ pages: [{ place, kind, updated? }] }`, which
the backend still has to add (until then none are listed); hubs carry optional `ready` and `updated`, a hub page optional
`page_ready`.
- Project page: **Around this project** (commute, schools, rent, being built, what is changing, jobs), measured from the pin.
- Place sub-pages beside /top and /new-launches: `/projects/area/<place>/schools`, `/commute`, `/rent`; indexed only when
  `page_ready`, in the sitemap, linked from the place page and its projects.
- Work hub pages `/work-hubs/<slug>` and `/work-hubs` (companies, commute from each place, homes nearby, rent nearby).
- Each with breadcrumbs, its own canonical, Article/ItemList/BreadcrumbList data, last-updated date and sources.
- The website chat and llms.txt learn the same facts.

## Progress log

| Date | Commit | What |
|---|---|---|
| 2026-11-28 | — | Plan; the `neighbourhood` module's frame (registry, store, loop, views, routes) and the site contract. |
| 2026-11-28 | pi/research | Places and centres, 14 work hubs, commute (Routes API, monthly cap), being built, profile, jobs; places of worship out of every nearby list; research passages in the chat; `/research/pages`, hub `ready`/`page_ready`. Routes API not enabled for the key yet. |
| 2026-11-28 | this | C built on the site: "Around <name>" on project pages, "Living in <place>" on place pages, `/schools`, `/commute`, `/rent` per place, `/work-hubs` and `/work-hubs/<slug>`, sitemap and llms.txt entries, places of worship out of Nearby. |
