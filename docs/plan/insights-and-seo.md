# Insights and SEO: turning the data we collect into buyer pages, agent tools, an owner view and rankings

Status: **plan, not started** (2026-10-13). Owner decisions are marked **DECIDE** with a recommendation; confirm them with the
owner before building those parts. Labels: **LIVE** = built and running in production, **DATA ONLY** = collected and stored but
shown nowhere, **NEW** = to build.

## 1. What we already collect

| Data | Where it is stored | Written by | State |
|---|---|---|---|
| 12,781 MahaRERA projects; completion dates and moves (`completion_history`); homes booked over time (`booked_history`) | `projects` | `areastats/refresh.py` | LIVE on project pages; booking pace DATA ONLY |
| Hot score and its reasons (`hot_score`, `hot_signals`: bookings, Google results, news, Search Console, YouTube) | `projects` | `areastats/hot.py` (daily, mark `newsroom_status/hot_projects`) | DATA ONLY: 26 hot on 2026-10-13 |
| Sites marketing each project (`web_marketers`) | `projects` | `areastats/websearch.py` (Serper, ~20 searches a day) | DATA ONLY |
| Every Google result per search: organic, ads, related searches, **People also ask** questions | `web_search_results` | `areastats/websearch.py` | DATA ONLY |
| MahaRERA numbers seen in Google results that we lack | `discovered_projects` | `websearch.py`, added by `areastats/discover.py` | runs; no screen |
| Search phrases, our rank, rising phrases | demand data | `areastats/demand.py` | script only: `scripts/demand_report.py` |
| Impressions and position per page (`gsc_impressions`, `gsc_position`) | `projects` | `areastats/searchconsole.py` | used to order page refreshes; no screen |
| Index coverage (indexed or not, why) | seo collections | `seo/coverage.py` (daily) | no screen |
| IndexNow sends | mark in `newsroom_status` | `seo/indexnow.py` (every 30 min) | LIVE |
| Neighbourhood guides | `communities` | `communities/` (3 a day) | LIVE: `/localities/<area>/<neighbourhood>` |
| Pipeline health: one `pipeline=… step=… outcome=…` line per step | worker logs; `worker_heartbeats` | `app/platform/trace.py` | LIVE in logs and `python -m app.worker --check` |

Ready to use: `hot.top(store, area, limit)` already returns `{regno, name, area, page, hot_score, why[], marketed_by[]}`.
No route serves it yet.

## 2. Buyer (public site)

Rule: show **facts with their source**, never "hot" or "trending" (**DECIDE**, recommended). A buyer trusts "38 homes booked
in 90 days (MahaRERA)" more than a badge.

| # | What | State | Notes |
|---|---|---|---|
| B1 | **Activity box on the project page**: homes booked in the last 90 days, completion date moves ("Dec 2026 → Jun 2027"), news stories | NEW | From `booked_history`, `completion_history`, `news`. Each line names MahaRERA or the publisher. Hide the box when nothing is known. |
| B2 | **"Most active projects in <area>"** on area pages (`/projects/area/<place>`, `/localities/<area>`) | NEW | Order by `hot_score`, show the B1 fact line, never the score. Also gives hot pages internal links (S4). |
| B3 | **Neighbourhood guides linked both ways**: project page → "Near <neighbourhood>"; guide → "Projects nearby" | NEW | `communities` has lat/lon; projects have `geo`. Nearest guide within 2 km. |
| B4 | **One page per project, not per tower** (see S1) | NEW | Hinjewadi Phase 3 has 16 near-identical tower pages today. |
| B5 | **"Follow this project" on WhatsApp**: a message when the completion date moves or bookings jump | NEW, later | Needs `WHATSAPP_PUBLIC_NUMBER` live. Doubles as lead capture with consent. |

Not to build: "also listed on 99acres or Housing.com" on public pages. It sends buyers to competitors (**DECIDE**,
recommended: never public).

## 3. Agent (studio)

| # | What | State | Notes |
|---|---|---|---|
| A1 | **"Projects buyers are looking at in your area"**: hot projects in the agent's localities, with the reason and a **Start a campaign** button prefilled with the project and its MahaRERA facts | NEW | `hot.top(store, area)`; reasons are `why[]`. |
| A2 | **Who else markets this project**: on the agent's own project or listing, "11 sites rank for this project" with the domains | DATA ONLY → show to agents only | `marketed_by` from `hot.top`, or `web_marketers` on the project. |
| A3 | **Real search phrases for posts**: the post writer uses phrases people search ("2 BHK Wagholi under 60 lakh") in the search line and hashtags | NEW | From `demand.py`. Ties into `docs/plan/reach-captions.md` (segment hashtags, search line). |

## 4. Owner (Studio → Insights)

One owner-only screen with tabs, read-only from stored data. Studio already has **Newsroom → Project pages**
(`frontend/app/studio/newsroom/`); add **Insights** beside it or as tabs there.

| # | Tab | Shows | Action |
|---|---|---|---|
| O1 | **Hot projects** | score, reasons, marketers, last page refresh (`enriched_at`), next due (`HOT_REFRESH_DAYS` = 14) | Refresh page now (sets the enrichment urgent request) |
| O2 | **Found on Google** | `discovered_projects`: number, where it was seen, added or not | Add now / Ignore |
| O3 | **Search demand** | phrases, our rank, rising phrases (what `demand_report.py` prints) | "Make a page" for a phrase with no page (S5) |
| O4 | **Pages and Google** | indexed or not and why (coverage), impressions, near page one, last IndexNow send | Refresh page |
| O5 | **Neighbourhoods** | found, published, refused with the reason (`write_notes`) | Hide / write again |
| O6 | **System** | one row per pipeline from heartbeats and the latest trace line: last ok, last failure, Serper credits left | none |
| O7 | **Daily digest** (WhatsApp or email), only when something changed: "3 new hot projects, 1 found on Google, a page near page one, Serper 2,340 credits left" | NEW | |

Build O1, O2 and O6 first: the data is already stored and the owner cannot see it today.

## 5. SEO: how the data drives rankings

The loop: **measure** (Search Console + Serper) → **decide** (hot + near page one + demand) → **improve the page** →
**tell search engines** (IndexNow + sitemap date) → measure again. Measure, decide and tell are running; improve is mostly NEW.

| # | What | State | Notes |
|---|---|---|---|
| S1 | **Consolidate duplicate pages.** Towers and phases of one project become one project page with the towers as sections; old tower URLs answer 301 to it; spelling variants likewise. | NEW, highest value | 16 thin Hinjewadi Phase 3 tower pages compete with each other. Group by promoter + marketed name (`pages.names`) + pincode. The sitemap lists the project page only. |
| S2 | **Titles and H1s from real searches.** Lead with the phrase buyers search ("Venkatesh Vanaya Kharadi"), not MahaRERA's wording ("VENKATESH VANAYA-WING-D-PHASE -5") | NEW | Phrases from `web_search_results` and Search Console queries; keep the MahaRERA name in the body and JSON-LD. |
| S3 | **Answer the questions buyers ask.** Google's "People also ask" questions are stored (`type: "question"`); answer the ones MahaRERA facts can answer, with FAQ structured data | NEW | Facts only; skip a question the data cannot answer. |
| S4 | **Internal links.** Area page → most active projects (B2); project ↔ neighbourhood guide (B3); news story → projects it names | NEW | |
| S5 | **Pages for real searches with no page.** A phrase with impressions but no matching page ("plots in Ranjangaon") becomes a landing page from the register and live listings | NEW | Only when there is enough real data; no thin pages. |
| S6 | **Freshness.** The sitemap date moves only on real change (`pages.page_updated`: enrichment, details read, page text; never MahaRERA's own dates); IndexNow sends changed pages | LIVE | Keep this rule for every new page type. |
| S7 | **Weekly SEO report**: pages indexed, impressions, clicks, average position for target phrases, week on week | NEW | The weekly audit (`seo/audit.py`) exists; add the trend numbers. |

## 6. Order

| Week | Build | Why first |
|---|---|---|
| 1 | O1 Hot projects, O2 Found on Google, O6 System | Data already stored; the owner sees it the same day |
| 1 | S1 tower and phase consolidation | Biggest SEO problem; every later step depends on one page per project |
| 2 | B1 activity box, B2 most active in area, B3 + S4 links | Buyer value and internal links in one change |
| 2 | S2 titles and H1s from searches | Cheap ranking gain |
| 3 | A1, A2, A3 agent tools | Feeds campaigns |
| 3 | O3 Search demand + S5 pages for searches | Content gaps |
| 4 | O4, O5, O7 digest, S3 FAQs, S7 weekly report | Polish |
| later | B5 follow a project on WhatsApp | Needs the WhatsApp number live |

## 7. Decisions to confirm with the owner

1. Public pages show factual activity lines, not a "hot" badge or score. Recommended: yes.
2. Marketer sites (`web_marketers`) are for the owner and agents only, never public. Recommended: yes.
3. Merge towers and phases into one page per project, with the old URLs answering 301. Recommended: yes.
4. Start with week 1 (O1, O2, O6, S1).

## 8. Rules that hold for all of it

- Every number on a public page names its source (MahaRERA, a publisher, OpenStreetMap). No invented or rounded-up numbers.
- No hype words; the existing guards (`creative/guards.py`, `areastats/enrich.BANNED`) apply to every new text.
- Every new job logs one `trace.event` line per step, like the other pipelines, and reports in `python -m app.worker --check`.
- Serper budget: about 20 searches a day (`websearch.AREA_PER_DAY`, `PROJECT_PER_DAY`). The free 2,500 last about 4 months;
  show the remaining credits in O6.
