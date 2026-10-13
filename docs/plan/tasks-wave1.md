# Insights and SEO, wave 1: briefs for parallel agents

Parent plan: `docs/plan/insights-and-seo.md` (decisions taken 2026-10-13). Each task below is one agent, in its own git worktree,
on top of `cursor/analyze-and-fix-styling-issues-cacb` (the only branch). Facts here were read from production on 2026-10-13.

## Rules for every agent

- Touch only the files your task owns (table below). If you need a change in another task's file, stop and say so in your report.
- Every number a buyer sees names its source (MahaRERA, a publisher). No hype words (`creative/guards.py`, `areastats/enrich.BANNED`).
- New background steps log one `trace.event` line per step (`app/platform/trace.py`).
- Import contracts must stay as they are (`backend/.venv/Scripts/lint-imports.exe`: 2 contracts are already broken by older code;
  break no new ones). Modules never import `app.worker`; the API layer composes.
- Tests: update the tests your change breaks and add the few that pin the new rule; run only the test files for your modules
  (`backend/.venv/Scripts/python.exe -m pytest -q <files>`), never the full suite (~40 min). Frontend: `npx tsc --noEmit -p .`.
- Commit in your worktree with `git -c user.name="Amit Sajwan" -c user.email="amitsajwan@gmail.com" commit`, ending the
  message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Do not deploy, push or merge: the coordinating session does.
- Report: what changed (files), what you checked and how, anything left open.

## File ownership (no two tasks share a file)

| Task | Owns |
|---|---|
| T1 MahaRERA read health | `backend/app/modules/areastats/refresh.py` (details step, `status`), its tests |
| T2 Who else sells | new `backend/app/modules/areastats/sellers.py`, a new route file under `backend/app/api/v1/endpoints/`, one line in `backend/app/api/v1/router.py`, new `frontend/lib/app/sellers.ts`, new `frontend/components/app/SellersCard.tsx`, the one insertion in `frontend/app/studio/listings/[id]/page.tsx` |
| T3 One page per project | `backend/app/modules/areastats/pages.py`, `backend/app/modules/areastats/router.py`, `frontend/app/projects/[slug]/page.tsx`, `frontend/components/site/RegisterProjectPage.tsx`, `frontend/app/sitemap.ts`, new `backend/app/modules/areastats/clusters.py`, their tests |

---

## T1. MahaRERA detail reads: keep the reason, warn on what is live

**Found:** `worker --check` says "WARN rera details: … last read failed 2140". All 2,140 failures were read Oct 9–12, before the
TLS chain fix (cbc708e9, memory `reference_maharera_tls`); on Oct 13, 718 reads succeeded and 1 failed. None is in our areas
(all rest-of-Pune). Failed reads retry after `DETAILS_RETRY_DAYS` = 1, 15 per step, so the backlog clears by itself. Problems:
the reason a read failed is not kept (`details_ok=False` only), and the warning compares all-time failures with all-time successes.

**Do:**
1. In `refresh.details`, keep why a read failed on the record: `details_error` = one of `no_id` (no MahaRERA id in `source_url`),
   `no_answer` (fetch returned None), `refused` (parse raised `MahaReraError`: keep its short message), `other`. Clear it on success.
2. In `refresh.status`, judge health on the last 24 hours (reads with `details_checked_at` in the last day: ok vs failed, with the
   reasons counted), and report the old backlog as information ("1,9xx failed before, retrying 15 a step"). WARN only when
   recent failures outnumber recent successes.
3. One `trace.event(log, "register", regno, "details", outcome, reason=...)` per read.

**Done when:** the status lines show the recent picture and failure reasons; tests for refresh pass.

---

## T2. Who else sells this project (for agents)

**Why:** agents want to know who else is selling a project they market: other agents and channel partners first.
**Data (live, 2026-10-13):** `projects.web_marketers` (domains) is set on 101 projects; `web_search_results` (kind `project`,
`regno`, `results[]` with `type` organic/ad, `title`, `link`, `position`) holds the Google results for each project search (~12
projects a day, hot first: `areastats/websearch.py`). Examples: 31 Palma Drive Phase 2 → 31palma-drive.com,
31palmadrive-kharadi.in, bhandariassociates.co.in, housiey.com, jllhomes.co.in, upcomingprop.com, 99acres.com. Neoworld →
sparkleneoworld.com (builder), ghar.tv, nobroker.in, housing.com, magicbricks.com, 99acres.com.

**Do:**
1. `areastats/sellers.py`: `sellers(db, regno) -> {searched_at, query, groups: {agents: [...], builder: [...], portals: [...],
   platform: [...]}}`. Each site row: `site`, `title`, `link`, `position` (best organic position; ads marked `ad: true`).
   Classify: **portals** from a fixed list (99acres, housing.com, magicbricks, nobroker, squareyards, makaan, proptiger, ghar.tv,
   commonfloor, nestaway, quikr, beyondwalls, bookmywing, housiey? decide and document each), **builder** when the domain carries
   the promoter's key word or the project's name and the page title names the builder (`pages.promoter_key`), **agents** = every
   other marketer (channel partners, microsites like 31palmadrive-kharadi.in). Exclude `websearch.NOT_MARKETERS` and our own site.
   **platform** = agents on our platform whose listings or agent projects carry the same MahaRERA number (names and profile links
   only, never phone numbers).
2. A route `GET /api/v1/listings/{id}/sellers` (or by regno) for the signed-in agent who owns the listing; 404 without a
   MahaRERA number; an empty result says "not searched yet" rather than "nobody".
3. `SellersCard` on `/studio/listings/[id]`: "Who else sells this project", the four groups, agents first, each with its Google
   position ("#3 on Google for 'Prasun Elara Lohegaon Pune'") and link; the date of the search; one line on the limits ("only
   sellers with a website that ranks; MahaRERA publishes no agent list").
4. Agents only: never on a public page (decision 2).

**Done when:** the card shows real groups for a listing whose project has results; tests for sellers classification pass.

---

## T3. One page per project (towers and phases merged)

**Found on production (2026-10-13):** 12,784 project pages; 845 clusters of 2+ pages that share builder (`pages.promoter_key`),
base name and pincode, holding 2,317 pages; 99 clusters / 285 pages in our areas. Largest: Gulmohar Villas (10, **no promoter**),
Lodha "Kharadi New Project" Tower 1-8 (= Lodha Camelot), Venkatesh Vanaya (7, phases 1-8 with wings), Manhattan (7, spelling
and "H building"), Majestique Towers East phase 1-5, Majestique Marbella phase I-IV, Joyville Hinjawadi phase 1-6, Lodha
"Hinjewadi Project" towers. **140 base-name + pincode pairs have different promoters: never merge across promoters.**
`hot.search_name` is too aggressive for a key ("Majestique Towers East" → "Majestique"): write your own.

**Do:**
1. `areastats/clusters.py`: a cluster key = promoter key + base name (tower, wing, building, phase and their labels removed;
   roman and letter phase tokens; "-I", "–", "&" variants) + pincode. No promoter → no merge. Plus the confirmed groups in
   `agentprojects/groups.py` (`registrations`: Camelot's towers) which win over the name rule. Store `cluster_id` and
   `cluster_primary` on each record; recompute in the register step that assigns slugs.
2. The primary page (`/projects/<slug>`): the oldest registration's slug, or the marketed name's. It shows the project once,
   with **a section per tower/phase** (registration number, homes, booked, completion date and its moves, each MahaRERA-sourced),
   totals across towers, and every registration number listed (buyers search them).
3. Every other member's URL answers **301** to the primary (backend says `redirect_to`; the Next page calls `permanentRedirect`).
   The sitemap lists primaries only; IndexNow sends the primary when any member changes (`pages.page_updated` = the newest member's).
4. JSON-LD on the primary names the project once; each tower as a part (`containsPlace` or an `ItemList`), no duplicate entities.
5. Safety: a dry-run report first (`python -m app.modules.areastats.clusters --report`): clusters in our areas with members,
   so the coordinator checks the 285 pages before the 301s go live.

**Done when:** the report lists the clusters; a member slug redirects to its primary; the primary shows its towers; tests pass.
