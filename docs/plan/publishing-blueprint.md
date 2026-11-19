# The 12-month publishing blueprint, read against what runs (2026-11-19, PROPOSED)

Owner, 2026-11-19, pasted an outside "Avasetu SEO & publishing ecosystem: 12-month blueprint" (one domain, ₹5,000 a month, six
content pillars, a 60:25:15 publishing mix, a CMS with keyword fields, a 30-day task list, and as its first deliverable a
page-by-page audit). This page says, row by row, what of it we already run, what it adds, and where it would undo a decision in
[seo-system.md](seo-system.md). When the two disagree, seo-system.md is right.

The blueprint's direction matches ours: one domain, no satellite sites, no bought links, no mass AI pages, a structured database
of projects, builders, localities and MahaRERA records as the asset. Most of its technical checklist has been live since October.
What it adds of value is a **hand-researched publishing rhythm** (locality guides with photos, comparisons, a quarterly report)
and **money for outreach**, which are exactly the levers we lack (seo-system.md section 1: the bottleneck is outside trust).

## First deliverable: the page-by-page audit (BUILT 2026-11-19)

`backend/scripts/page_audit.py` (logic in `seo/pageaudit.py`, read-only). One row per page Google showed in 28 days or the
daily index check knows, with clicks, impressions, CTR, position, the 28 days before (`trend`), index state, whether it is in
the sitemap, the search that shows it most, and one bucket and action. It answers the blueprint's five questions:

| Blueprint asks | Bucket | Action the script prints |
|---|---|---|
| Which pages already attract clicks | `earning` (and `low_ctr`: page one, 100+ impressions, under 1% clicked) | keep steady, change only through the doctor; `low_ctr` gets a title and description once the title hold ends (`actions.HOLD_UNTIL`, 2026-12-15) |
| Which have impressions but poor rankings | `near_page_one` (8-20), `seen_far` (20+ impressions, past 20) | the doctor's queue; compare the page with its top search |
| Which are indexed but have no traffic | `indexed_silent` | merge with a 301 into the page that earns for the same search, or give it a fact nobody else has |
| Which to merge, improve or remove | `not_indexed` by state, `outside_sitemap` | Crawled: add facts or keep out of search; Discovered: Request indexing and link it; taken out: check the 301 or noindex. **Never "delete"** (section 9) |
| Which new pages have the best opportunity | not here: the weekly search gaps report and `demand_report.py` already list searches with no page | |

Run on the VM (the Search Console key lives in the newsroom container):
`sudo docker exec gcp-newsroom-1 sh -c "PYTHONPATH=. python scripts/page_audit.py --csv /tmp/audit.csv"`, then
`sudo docker cp gcp-newsroom-1:/tmp/audit.csv .`. The printed "Most seen 20" is the blueprint's week-one "top 20 pages by
impressions"; the `top_search` column is its keyword-to-URL map. Not yet run against production (2026-11-19): the owner runs it.

## The blueprint, row by row

| Blueprint item | Here today | Verdict |
|---|---|---|
| One domain, no satellites, no bought links or DA | section 9 rules | AGREE, already the rule |
| Six pillars: projects, localities, builders, research, news, guides | `/projects/`, `/localities/`, `/builders/`, `/news/` (+ `/news/track/`), `/guides/`, `/insights/` and `/pune-maharera-tracker` for research | AGREE with the sections; **no new `/research/` path**: research goes to `/insights/` and the tracker, so no page moves |
| URLs like `/localities/kharadi-pune`, `/projects/lodha-camelot-kharadi` | `/localities/kharadi`; project slugs set by the register and hand corrections, members 301 to the primary | DROPPED: renaming URLs is the churn search-recovery.md R1 stopped. Keep every URL as it is |
| Technical checklist (SSR, unique titles, canonicals, sitemap per type, robots, breadcrumbs, Article/Organization data, Core Web Vitals, related links) | LIVE (sections 4-6); weekly live audit; page speed is section 8 item 8 | AGREE, nothing new; page speed stays item 8 |
| A CMS with `primary_keyword`, `meta_title`, `canonical_url`, `status` per page | target search per project page (`seo/targets.py`), titles by rule, canonicals by code, noindex until a page holds a fact, sitemap only of pages in search | DROPPED as a new system: hand-typed titles and canonicals would fight the doctor's measured fixes. The **checks** it lists already run (duplicate slugs and titles, thin pages noindex, sitemap eligibility, stale prices and dates: page check, freshness row) |
| "AI for research assistance, human verification before publishing" | rule: model text only from checked facts, never a model's own number | AGREE; hand-written guides and reports are welcome, AI-written pages are not |
| Locality guides: connectivity, employers, schools, hospitals, roads, projects, prices, pros and cons, **original dated photos**, last verified | `/localities/<area>` guides (who it suits, getting around, what to check, MahaRERA counts), [area-pictures.md](area-pictures.md), [area-maps.md](area-maps.md) | TARGET B1 below: the hand-researched layer (photos, schools, hospitals, a dated "verified on") is what code cannot do |
| Localities to start with: Kharadi, Upper Kharadi, Wagholi, Mundhwa, Lohegaon, Viman Nagar, Hadapsar, Baner | our 8 areas: Upper Kharadi, Kharadi, Wagholi, Keshav Nagar, Lohegaon, Baner, Wakad, Hinjawadi | owner to decide. Mundhwa, Viman Nagar, Hadapsar fit "east Pune first"; adding them now goes against visibility-base step 0 (no new areas while the filter lasts). Suggest: after the 2026-12-15 judgement |
| Project page sections (overview, configuration, verified price and date, carpet area, MahaRERA link, amenities, connectivity, photos, similar projects, last verified) | all LIVE, plus what portals do not show: homes booked over time, possession filed vs promised, the builder's date record | AGREE, nothing new. "Original photos" = H7 (agents' dated site-visit photos), owner's call |
| Research articles with methodology, sample size, source, date | H4 monthly report (TARGET), the MahaRERA tracker | AGREE: B2 below builds H4 first, the hand-written comparisons on top |
| 60:25:15 mix; 4 new project pages, 2 research, 2 guides/news, 4 improvements a month | project pages come from the register (hundreds, by the loops), news from the newsroom | the mix only applies to **hand-written** pieces: 2 research + 2 guides a month is right for one person; project pages are not hand-written |
| ₹5,000 a month: content ₹2,000, photos and local research ₹1,000, outreach ₹1,500, tools ₹500 | today's spend: Serper, Gemini inside daily caps; visibility-base step 2 proposes ₹3,000-5,000 a month of Google Ads | owner to decide between the two uses of the same money. Suggest: outreach and photos first (they build links and facts that last), Ads only for the brand searches test |
| Search Console, GA4, Ahrefs/Semrush dashboard | Rankings tab, weekly note, scoreboard, AI search counts | AGREE; referring domains are the one gap (no backlink source). Ahrefs Webmaster Tools is free for a verified site: owner, once |
| Traffic goal 4,000 clicks a month in a year from ~1,200 per 28 days | section 1 scorecard | add as a row to the section 1 scorecard once the owner agrees |

## What to build or do from it (TARGET, waiting for the owner)

- **B0. Run the audit** (owner, 10 minutes): the command above, monthly. Its counts per bucket go on the scorecard.
- **B1. Hand layer on the 8 locality guides** (owner + ₹1,000/month photos): a dated photo set per area (who took it, when), schools
  and hospitals named with distances measured from the map, one "verified on <date>" line. Code: a hand-facts file per area beside
  `pune_places.VERIFIED`, shown on `/localities/<area>`.
- **B2. H4 monthly report first, then a quarterly "Pune residential report"** (seo-system.md 8b H4): code writes the numbers; the
  owner writes the 300 words of reading around them and pitches it (₹1,500/month outreach).
- **B3. Comparisons** ("Kharadi vs Wagholi for a family"): hand-written `/guides/<slug>` topic files with figures read from our own
  pages and their sources, 1-2 a month. Not before the 2026-12-15 judgement (no new indexable pages while the filter lasts).
- **B4. Referring domains on the scorecard** (owner): Ahrefs Webmaster Tools, free, once; a monthly count.

Not doing, from the blueprint: new URL scheme, a separate CMS, a `/research/` section, eight new areas at once.
