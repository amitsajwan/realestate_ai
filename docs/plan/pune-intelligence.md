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

| Researcher | What | Source | Refresh |
|---|---|---|---|
| `commute` | drive times to the nearest work hubs, 9 am and 6 pm | Google Routes API, typical traffic | 30 days |
| `schools` **BUILT** | schools with board, level, affiliation number, distance; hidden under 3 within 3 km, /schools page with 8+ within 5 km | CBSE SARAS district list (357 schools, read from the VM) + details page per school for the pincode; CISCE locator (52 Pune schools with the council's own positions; Cloudflare refuses the VM, so a saved reading of 2026-11-28 stands until a live read works); placed by Google Places Text Search (name + pincode checks), re-read by id after 30 days | lists 90 days; runs every 6 h until all placed (300 Places calls a run) |
| `rent` **BUILT** | asked rent by flat size: low, median, high, listings, gross yield on new projects' asking prices; rows shown with 10+ listings, /rent page with 2 such rows | MagicBricks (30 a size), NoBroker (~25), Square Yards (~24) pages read politely (robots, 2 s a site), our agents' rent listings; 99acres (403) and Housing.com (406) refuse readers; Serper finds a page whose address cannot be guessed (cap a cycle) | 30 days |
| `profile` | home mix being built, homes finished by year, nearby work/college/hospital/government/defence/industrial | MahaRERA register, places | 30 days |
| `being_built` | projects and homes being built within 2 km, due years, biggest | MahaRERA register | 7 days |
| `jobs` | companies at each work hub, homes near it | the hubs' own tenant lists | 90 days |

Public reads: `/public/research/places/{place}`, `/public/research/projects/{slug}`, `/public/research/hubs[/{slug}]`, shapes in
`frontend/lib/site/research.ts`.

### C. Pages
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
| 2026-11-28 | pi/schools-rent | `schools` and `rent` researchers BUILT. Measured from the VM: CBSE list 357 Pune schools, 14 of 16 sample schools placed by Google (2 refused: name and pincode); rent 132-138 listings per place for Kharadi, Wagholi, Hinjawadi (1/2/3 BHK each 35+): Kharadi 2 BHK median Rs 38,000 (33,000-43,500), Wagholi Rs 25,000, Hinjawadi Rs 29,000. Contract: optional `SchoolsBlock.all` (the /schools page list) and `RentBlock.listings_within_km`. |
