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
1. **BUILT** A tracker's suggested status line that passes the existing checks goes live by itself (`trackers.apply_due`, the old
   line stays in the history), switch `NEWSROOM_TRACKER_AUTO` (on). A move to a tracker's last stage, or a line saying it opened,
   was inaugurated, runs or started operations, still waits for the owner in Studio (`needs_owner`, shown as "Waiting for you").
   The suggestions already waiting (Ring Road survey, Purandar stage 2, merged villages' water) apply on the first run.
2. **BUILT** Each tracker has its own Google News searches (`queries` in its JSON, `tracker_topics.queries()` added to
   `sources/google_news.py`), so its news comes in even when no area is named; its headlines pass the area gate as tracker news.
3. **BUILT** From 8 trackers to 20, written from the reports we hold: Vishrantwadi flyover, Keshavnagar-Kharadi bridge,
   Suncity-Karvenagar flyover, PMC bridges due in 2027, Patal Lok underground road, Metro phase 2, Swargate-Katraj metro, metro
   station parking, PMC FSI/TDR rules, PMC property tax, the merged villages' development plan, MHADA Pune lottery. Stamp duty
   stays inside `ready-reckoner` (one new dated line). No Mundhwa junction flyover: no report to write it from.
4. **BUILT** A weekly topic finder (`topic_finder.py`) groups the last 30 days' Pune reports no tracker matches; a subject with 3+
   reports from 2+ publishers shows on Studio's Trackers desk as "To do: new tracker?" with a draft (a guarded model draft, each
   part checked, else the headlines' shared words). Add is one click (it saves the definition on `newsroom_trackers`; the files
   and Mongo trackers merge in `trackers.definitions()`); "Not a tracker" keeps it from coming back.
5. **BUILT** Every tracker names the place slugs it touches (`places`); `newsroom.changes_for_place(db, place)` gives the
   neighbourhood pages their `changes` (wired in `app/wiring.py`).
6. **BUILT** Tracker pages are status pages for search: H1 "<name> status", "Where it stands (<date>)", next expected date, stages,
   places linking `/projects/area/<place>`, timeline, FAQ, Article (dateModified = last status) + BreadcrumbList + FAQPage,
   canonical, last-updated line; hub `/news/track`.

### B. Neighbourhood research (`backend/app/modules/neighbourhood`, owns `area_research`, `schools`, `work_hub_research`)
One researcher per kind of fact in `researchers/`, run by the `neighbourhood` loop (newsroom role) when due:

| Researcher | What | Source | Refresh |
|---|---|---|---|
| `commute` | drive times to the nearest work hubs, 9 am and 6 pm | Google Routes API, typical traffic | 30 days |
| `schools` | schools with board, level, affiliation number, distance | CBSE (SARAS) and CISCE official lists, placed on the map | 90 days |
| `rent` | asked rent by flat size: low, median, high, listings, yield | rental listings on the portals and our agents' listings | 30 days |
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
| 2026-11-28 | (pi/topics) | A built: trackers update themselves from checked lines (opening waits for the owner), per-tracker Google News searches, 20 trackers with places, weekly topic finder with Studio add, `changes_for_place`, tracker status pages and `/news/track`. |
