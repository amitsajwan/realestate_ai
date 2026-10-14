# Rank loop: every page gets a target search, a fix, and a measured result

Status: **BUILT, not deployed** (2026-10-14): R0 to R9 are in the code (see section 9 for what differs from the plan). Builds on `docs/plan/insights-and-seo.md` (S1 to S7) and replaces its order for the SEO
items. Labels: **LIVE** = running in production, **BUILT** = in the code, not deployed, **NEW** = to build.

## 1. The idea

Today we **measure** well (Search Console every day, Serper 20 searches a day, index coverage, hot scores) and we **tell** search
engines well (sitemap dates, IndexNow). What is missing is the middle: nothing reads "our Kharadi page is #14 for 'venkatesh
vanaya kharadi'" and changes that page, and nothing checks afterwards whether the change helped.

The rank loop closes it, one page at a time:

```
measure ──► target ──► diagnose ──► fix ──► tell ──► wait 14 / 28 days ──► measure again ──► keep what worked
(GSC, Serper)  (one search   (fixed      (menu of   (IndexNow,                (position and clicks
               phrase per    checklist)  safe fixes) sitemap)                  before vs after)
               page)
```

Three things make it work better than ordinary SEO tooling:
1. **One target per page.** Each page aims at the search people already use to reach it (Search Console), not at a guessed
   keyword. That phrase drives the title, H1, FAQ and the anchor text of links into the page.
2. **Fixes come from a fixed menu and are logged.** Every change records the position and impressions before. 14 and 28 days
   later the loop reads them again, so we learn which fix moves pages on *our* site and the doctor prefers those.
3. **We stop competing with ourselves.** Two of our pages showing for the same search split Google's trust. Tower pages merge
   (S1), and the loop flags any other pair.

## 2. What exists (do not rebuild)

| Piece | Where | State |
|---|---|---|
| Phrase → our pages, impressions, position, rising (`search_demand`, `gsc.pages`) | `areastats/demand.py` `from_gsc` | LIVE |
| Our rank for every Serper search, related searches, "People also ask" | `areastats/demand.py` `from_results`, `websearch.py` | LIVE |
| Per-page impressions/position (`gsc_*` on the record), near page one (8-20, 20+ impressions) enriched first | `searchconsole.py`, `enrich.priority` | LIVE |
| Tower/phase clusters (`cluster_id`, `cluster_primary`), dry-run report | `areastats/clusters.py`, `pages.assign_all` | BUILT, stored; **no redirects yet** |
| Marketed name and aliases (`pages.names`) | `areastats/pages.py` | LIVE |
| Search title "<name>, <area>: Price, Possession <Mon YYYY>", buyer FAQ with FAQPage data, web facts | `frontend/lib/site/seo.ts`, `webfacts.ts`, `areastats/webfacts.py` | LIVE (941c39ad) |
| 2 BHK, 3 BHK, budget, area and place pages | `frontend/app/2-bhk`, `3-bhk`, `price`, `projects/area` | LIVE |
| IndexNow, sitemap `page_updated`, coverage, weekly audit | `seo/` | LIVE |

## 3. The build, in order

### R0. One page per project: switch on the redirects (S1 / T3 step 3) | NEW, first

Clusters are already computed. What's left:
- `pages.project_page`: a member with `cluster_primary` returns `{"redirect_to": <primary slug>}` instead of a page.
- `frontend/app/projects/[slug]/page.tsx`: `permanentRedirect('/projects/' + redirect_to)` (301).
- The primary page gets a **Towers and phases** section: each member's registration number, tower name, completion date, units
  booked, with MahaRERA as the source. Bookings and units add up across the members, and each line names its source.
- `sitemap.ts` (via `pages.listing`): members are left out, only primaries are listed. The primary's `page_updated` is the newest of
  its members.
- Safety: the existing rules hold (no promoter → no merge; different promoters → no merge). Run `clusters --report` on
  production and read the in-area list before deploying. A wrong merge is undone with `cluster_skip: true` on the record
  (new field: `assign_clusters` leaves it alone).
- **Done when:** every member slug answers 301 to its primary, the primary lists its towers, and only primaries are in the sitemap.

### R1. A target phrase for every page | NEW

New `backend/app/modules/seo/targets.py`, run daily after the Search Console read:
- For each indexable project page, pick the target from `search_demand` phrases whose `gsc.pages` include the page's path:
  the one with the most impressions that **names the project** (`websearch.mentions` with any alias from `pages.names`).
  If there is none, use `"<marketed name> <area>"`. Area, BHK and budget pages get their target the same way, with their own path.
- Store it on the record as `seo_target: {phrase, impressions, position, source: "search_console" | "name", at}`.
- A target can change at most once every 28 days, because Google needs time to settle and churning titles hurts.
- `pages.view` returns `search_name`: the target phrase written the way people type it, kept only when it contains the project's
  name (a target like "rera pune" never becomes a title).
- `frontend/lib/site/seo.ts` leads the title and H1 with `search_name`
  ("Venkatesh Vanaya Kharadi: Price, Possession Jun 2027"). The MahaRERA legal name stays in the body and JSON-LD.
- **Done when:** project pages with Search Console data carry `seo_target`, and their title begins with how people search for them.

### R2. Self-competition check | NEW

In `seo/targets.py`, alongside R1: a phrase whose `gsc.pages` holds **2 or more of our paths**, each with impressions.
- Both paths in one cluster: R0 already fixes it.
- A register page and an agent listing for the same project: this is already handled. The register page redirects to the shared
  agent page (`listedRegnos` in the sitemap), so we only verify it.
- Anything else goes on a report (`seo_conflicts`) for the owner tab. Nothing is merged automatically outside clusters.

### R3. The page doctor | NEW, the core

New `backend/app/modules/seo/doctor.py`, run as a step in the `seo` worker loop once a day, at most `DOCTOR_PER_DAY` = 15 pages.

**Which pages, in order:** near page one (positions 8-20) → a rising phrase whose page sits below 20 → hot projects with
impressions but position worse than 20 → pages with impressions and zero clicks (title problem). A page treated in the last 28
days is skipped.

**Diagnosis**, a fixed checklist with one cause per line:

| Check | Fix (from the menu) |
|---|---|
| Title/H1 do not lead with the target phrase | R1 target applied (title change, logged) |
| "People also ask" questions seen for the target or its project that our facts can answer, missing from the FAQ | Add the answer (see R4) |
| Fewer than 3 internal links into the page | Give it a link slot (R5) |
| Facts older than 30 days (`enriched_at`) or no web facts | Urgent enrichment (`enrich.enrich_now(..., by="doctor")`) |
| Not indexed (`seo_index`) | Resend through IndexNow. If the cause is "crawled, not indexed", flag the page as thin for the owner |
| Impressions but no clicks while the position is 1-10 | Rewrite the description from facts: price band, possession, homes booked |

**Log** every fix in `seo_actions`:
`{path, phrase, fix, at, before: {position, impressions, clicks}, after14: null, after28: null}`.
The same daily run fills `after14` and `after28` from Search Console. `doctor.results()` gives each fix type its count, the
median change in position and the share of pages that improved. The doctor tries fix types with better results first, with
a floor of 2 per type per day so every fix keeps being measured.

**Undo:** every title or description change stores the old value, and `doctor.revert(path)` puts it back. A fix whose page lost
more than 5 positions after 28 days is reverted automatically.

### R4. FAQ answers from real questions (S3) | NEW

`frontend/lib/site/webfacts.ts` `catalogFaq` today asks fixed questions. Extend it on the backend: `seo/questions.py` maps a
stored question to a fact we hold, using a small fixed table (patterns → fact key):

| Question pattern | Answer from |
|---|---|
| possession / completion / "when will … be ready" | `completion_now` and `completion_history` (MahaRERA) |
| rera number / registration | registration numbers (MahaRERA) |
| price / cost / rate | listing prices, else the web fact with its source, else skip |
| carpet area / sizes / bhk | listings, brochure document, web facts |
| builder / developer / "who is" | promoter + track record (MahaRERA) |
| distance / how far / near | `place_fill` distances (OpenStreetMap) |
| how many units / booked | units total and booked (MahaRERA) |

An unmatched question is skipped and nothing is invented. At most 8 questions per page, and each answer names its source.
`pages.view` returns `faq: [{q, a, source}]`, and the page renders them with FAQPage JSON-LD (replacing the fixed list
where they overlap).

### R5. Internal links that go where they help (S4, B2, B3) | NEW

- **"Most active projects in <area>"** on `/localities/<area>` and `/projects/area/<place>`: 8 projects ordered by
  `(doctor link slot first, hot_score)`, each with one fact line ("38 homes booked in 90 days, MahaRERA"). It never shows a score
  or the word "hot". New public route `GET /public/areas/{key}/active`.
- **Project ↔ neighbourhood guide**: on the project page, "Near <neighbourhood>" (the nearest guide within 2 km, using `geo` and the
  `communities` lat/lon). On the guide, "Projects nearby".
- **Anchor text = target phrase**: links into a project page use its `search_name`, not the legal name.
- Link slots: the doctor marks up to 20 pages a day `seo_link_slot: true` (14 days). Those pages come first in the area lists.

### R6. Builder pages (B6) | NEW, after R0

`/builders/<promoter slug>`: every Pune project of the promoter (primaries only), homes booked, completion dates and how often
they moved, all from MahaRERA. This targets "<builder> projects in Pune", a phrase with real volume. Each builder page links to
its project pages and each project page links back. A builder page is indexable only with 2 or more indexable projects.

### R7. Pages for real searches, without thin pages (S5) | NEW

`seo/gaps.py`, weekly: `search_demand` phrases with 30+ impressions (or rising) where no page of ours ranks in the top 20.
Each one is matched to an **existing template** (2 BHK / 3 BHK / budget / area / place / builder) by fixed rules.
- The template exists but the page is not linked or not in the sitemap: add the link (most gaps are this).
- No template fits: list it for the owner (Insights → Search demand, O3). We never auto-write a page from AI text.

### R8. Spend Serper on the pages we're working on | change in `websearch.py`

Keep 20 searches a day, split as: area searches 6, project discovery 8, and **6 target checks**: the target phrase of a page
the doctor treated 14 or 28 days ago. Search Console shows our position, but not who is above us. The check stores the top 10
so the owner tab can show "above us: housiey.com, 99acres" for each page. Constants live in `websearch.py`,
`AREA_PER_DAY`/`PROJECT_PER_DAY`/`TARGET_PER_DAY`. `owner.system`'s `serper_per_day` sums all three.

### R9. Owner tab and weekly report (O3, O4, S7) | NEW

Studio → Newsroom → Insights → **Rankings**:
- **This week:** clicks, impressions, pages on page one (position ≤ 10), pages near page one, each with the change from last week.
- **Doctor:** today's pages with diagnosis and fix, and the fix-type results table (count, median position change, % improved).
- **Self-competition** (R2) and **search gaps** (R7) lists.
- **Targets:** page → target phrase → position history (sparkline), and who is above us (R8).

The weekly audit e-mail (`seo/audit.py`) gets the same "this week" numbers.

## 4. Order

| Week | Build | Why |
|---|---|---|
| 1 | R0 redirects + towers section; R1 targets and titles | Biggest gain with the least code: no more self-competition, titles in buyers' words |
| 2 | R3 doctor (title, enrichment, IndexNow, description fixes) + `seo_actions` log; R2 report | The loop starts measuring from day one |
| 3 | R4 FAQ from questions; R5 area "most active", guide links, anchor text | The doctor's two strongest fixes |
| 4 | R6 builder pages; R8 Serper split; R9 Rankings tab | Builders need R0; the tab needs a few weeks of `seo_actions` |
| 5+ | R7 search gaps; tune the doctor from the measured results | Only once the data shows what works |

## 5. How we'll know it works

- **Baseline on day 1** (`scripts/demand_report.py` + Search Console): clicks per week, impressions, pages on page one, pages near
  page one. Write the numbers into this file.
- **Week 4:** pages that went from near page one to page one; the doctor's fix-type results table has 28-day data.
- **Week 8:** clicks per week up against the baseline; long-tail project searches ("<project> possession", "<project> rera")
  on page one for the projects we have treated.

## 6. Rules

- Facts only with their source on public pages. No hype words (`creative/guards.py`, `enrich.BANNED`). No AI-written pages. AI
  text only where it already exists (enrichment paragraph, neighbourhood guides) behind the existing checks.
- No thin pages: every new indexable page needs real register or listing facts (Google's scaled-content rule; see `seo.md`).
- A title changes at most once per 28 days per page, and every change is logged with the old value.
- Backlinks are never automated (no bought links, networks or comment spam). Off-page work is the owner's checklist below.
- Every new job logs one `trace.event` line per step and shows in `python -m app.worker --check`.
- Serper stays at about 20 searches a day. Search Console is free.

## 7. Off-page (owner, alongside)

- Every agent post, reel caption and WhatsApp share links to **our** project page (`/projects/<slug>`), never a portal.
- Google Business Profile for Avasetu (Pune), linking to the area pages.
- A monthly "Pune MahaRERA report" (from `/pune-maharera-tracker`) sent to local journalists and property bloggers: the page that
  earns links on its own.
- Agents on the platform link their own agent page from their WhatsApp Business and Instagram bios.

## 8. Files per step (for parallel work)

| Step | Owns |
|---|---|
| R0 | `areastats/pages.py` (`project_page`, `listing`), `areastats/clusters.py` (`cluster_skip`), `frontend/app/projects/[slug]/page.tsx`, `frontend/components/site/RegisterProjectPage.tsx`, `frontend/app/sitemap.ts` |
| R1, R2 | new `seo/targets.py`, `areastats/pages.py` (`view`: `search_name`), `frontend/lib/site/seo.ts` |
| R3 | new `seo/doctor.py`, `seo/runner.py` (one more step) |
| R4 | new `seo/questions.py`, `areastats/pages.py` (`view`: `faq`), `frontend/lib/site/webfacts.ts`, `ProjectDetails.tsx` |
| R5 | `areastats/router.py` (`/areas/{key}/active`), `frontend/app/localities/[slug]/page.tsx`, `frontend/app/projects/area/[place]/page.tsx`, `frontend/app/localities/[slug]/[community]/page.tsx` |
| R6 | new `frontend/app/builders/[slug]/page.tsx`, `areastats/pages.py` (`builder_page`), `areastats/router.py` |
| R7 | new `seo/gaps.py` |
| R8 | `areastats/websearch.py`, `areastats/owner.py` |
| R9 | `areastats/owner.py` or `seo/router.py` (rankings), `frontend/app/studio/newsroom/insights/`, `seo/audit.py` |

R0 and R1 both touch `pages.py` (different functions): build them in one branch or one after the other.

## 9. As built (2026-10-14)

| Step | Code | Notes |
|---|---|---|
| R0 | `areastats/clusters.py` (primary = a served page first, `cluster_skip`), `pages.primary_of`, `towers`, `cluster_updated`; `listing` leaves members out | A member slug gets the primary's page from the API, and the existing slug check in `app/projects/[slug]/page.tsx` sends the 301. The agent-listing redirect matches any tower's number. |
| R1, R2 | `seo/targets.py` (daily), `search_name` in `pages.view` / `listing`, `displayName` and `registerTitle` in `lib/site/register.ts` | Project pages only. Area, BHK and budget pages show up in R2 conflicts and R7 gaps, but get no target yet. Also keeps a daily snapshot of the site's numbers for R9. |
| R3 | `seo/doctor.py` (daily, 15 pages), log `seo_actions` | "Not indexed" is part of `refresh`: enrichment rewrites the page and moves its sitemap date, which is what gets it recrawled. |
| R4 | `seo/questions.py`, `seo_faq` on the record, `faq` in `pages.view`, merged in `projectFaq` | A real question replaces our own question on the same topic. Price questions are never answered from the web. |
| R5 | `areastats/hubs.py` `active`, `near_guide`, `near_projects`; `components/site/ActiveProjects.tsx` on `/localities/<area>`, `/projects/area/<place>` and the guide pages | Links into project pages use `search_name`. |
| R6 | `hubs.builders`, `builder_page`; `GET /public/builders[/{slug}]`; `app/builders/[slug]/page.tsx`; sitemap | Noindex below 2 indexable projects. Linked from "About the builder". |
| R7 | `seo/gaps.py` (weekly) | |
| R8 | `websearch.target_checks`: 6 area + 8 project + 6 target searches a day | |
| R9 | `seo/report.py`, `GET /newsroom/insights/rankings`, `POST .../rankings/revert`, `app/studio/newsroom/insights/RankingsTab.tsx` | The weekly e-mail numbers are **not** added: `seo/audit.py` runs in GitHub Actions without the database. `report.week_lines` is ready for a digest (O7). |

All steps run in the `seo` worker loop and need `GSC_SA_KEY_B64`. Without it they do nothing.

**Before the first deploy:** run `python -m app.modules.areastats.clusters --report` on production and read the in-area clusters.
Every member there answers 301 once deployed. Set `cluster_skip: true` on any record that must stay alone.
**Baseline:** after the first daily round, copy Insights → Rankings → This week into section 5.

