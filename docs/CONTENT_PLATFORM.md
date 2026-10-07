# Content platform: target architecture and work items

Last updated 6 October 2026 (added the Listing content track — LC items — for the owner's five listing pains). Owner: Amit. This is
the plan for how Avasetu makes, publishes and learns from content (posts, reels, news) and turns it into buyer enquiries. It sits
inside `docs/ARCHITECTURE.md` (the modular monolith) and does not change it.

**How to use this page:** read sections 1 to 4 once (10 minutes), then pick an item from section 6. Put your name in the Owner
column in your PR. Every item is small enough for one person and says what "done" means.

## 1. What we are trying to do

Get more qualified buyer enquiries (and agent sign-ups) from content, not more views. We have little data and no properties of our own
yet, so for now we make **explainers that need no property**, measure what holds attention, and only then build more machinery.

Five rules the whole system follows (all already true in the code; keep them true):
1. **Code calculates, models write.** A price, a date, a tax or an infrastructure status comes from a record or a calculation, never from a model's memory.
2. **Every claim has a source and a date**, and expires. Unofficial sources are marked and confirmed by a person.
3. **A person approves everything before it posts.** No agent, script or schedule publishes on its own.
4. **One publishing path** (`social.distribution.send`, with the ledger). Nothing else talks to the Graph API to publish.
5. **Measure before building.** We do not build learning, agents or a second database until reels have results to learn from.

## 2. Today (what exists)

```
 SOURCES / FACTS           CREATIVE                      GATES                 PUBLISH                 AFTER
 newsroom  (news, checked) creative  (posts, layouts)    quality guards        calendar (planned ->    engage   (comment replies)
 agentprojects (MahaRERA)  marketing (captions, text)    (hook, no invented     approved -> published) interest (I'm interested taps)
 reels/trend FACTS (new)   reels     (tip, tour, pitch,   numbers, contrast)    social.distribution     chat / whatsapp (conversations)
 knowledge/areas (grounding)         slides, trend, music) human approval        + publish_ledger        inbox / leads (lead cards)
```

| Part | Where | State |
|---|---|---|
| Posts, carousels, layouts and checks | `modules/creative`, `modules/marketing`, `modules/calendar` | working; hooks and numbers checked |
| Reels: tip, tour, pitch, project, slides, trend; voice; Avasetu theme music | `modules/reels`, `modules/agentprojects` | working; voice needs `GOOGLE_TTS_API_KEY` |
| Approval calendar and publisher | `modules/calendar`, `modules/social`, `platform/meta_graph` | working; rows are `planned` until approved |
| News with sources | `modules/newsroom` | working; owner reviews |
| Comment replies, leads | `modules/engage`, `modules/interest`, `modules/chat`, `modules/whatsapp` | working |
| Public site: `/projects`, area guides, news, SEO | `frontend/app`, `modules/agentprojects` | live after deploy |
| **Reading results back from Instagram and Facebook** | nothing | **does not exist** |
| **A shared store of verified facts** | `reels/trend.py FACTS` and `knowledge/areas.py` separately | partial |

## 3. Target

```
 FACTS (verified_facts: text, source, url, as_of, valid_until, kind)  +  CALCULATORS (cost sheet, area for budget)
                                  |
            IDEA / EXPERIMENT (one idea, 3-5 hook variants, an experiment id)
                                  |
            CREATIVE (existing: layouts, reels, music)  ->  tags on the calendar row (hook type, format, area, price band)
                                  |
            GATES: guards (code)  ->  fact check (claims must come from verified_facts)  ->  human approval
                                  |
            PUBLISH (existing path)  ->  published post id + link
                                  |
            MEASURE: collector reads insights at 1h / 24h / 72h / 7d  ->  content_metrics
                                  |  + enquiries per post (interest hub)
            STUDIO "WHAT WORKED": a table, ranked by enquiries then retention, filtered by tags
                                  |
            (later) suggestions: "this hook held 3x the typical watch time (n=14)"  ->  next experiment
```

### Data (all MongoDB; no second database)
- `content_calendar` row, existing: a `tags` field on every row (done 2026-10-07, `calendar/tags.py`): derived in `Store.add` from what the row holds, so every writer gets it; `schema`, `audience`, `kind`, `format`, `pillar`, `hook_type`, `hook`, `cta`, `area`, `language`, plus `experiment`, `variant`, `engine`, `price_band` when the writer sets them, and `duration_s`, `render` (the look's version) once a reel is rendered. Older rows: `scripts/calendar_admin.py tag-backfill`. A top-level field rather than inside `creative`, so the insights queries filter on one place.
- `verified_facts` (new): `{_id, text, source, url, as_of, valid_until, kind: official|secondary, topics: []}`. Promotes `reels/trend.py FACTS` and `knowledge/areas.py`.
- `content_metrics` (new): `{post_id, channel, at, age_label: 1h|24h|72h|7d, plays, reach, avg_watch_s, shares, saves, comments, likes, profile_visits, retention: [..]}`; one row per snapshot, never updated.
- `content_enquiries`: not a collection: count `interest` events by the post's `ref` (they exist).

### Modules (import rules apply: `lint-imports` must stay at 7 kept)
- `modules/insights/` (new, a content module; add it to the content layer in `backend/.importlinter`): the collector and the table queries. Reads the post ids from the calendar and publications; it does not import `engage` or `chat`. Anything it needs from them is passed in by `app/wiring.py`.
- `reels/trend.py`: stays the owner of trend reel definitions; its facts move to the facts store when item N5 is done.
- Facts guard: one function `facts.cite(ids)` that creative code calls; a number not in the cited facts is refused (`reels.director.valid_script` already does this).

### Decisions, and when we would change them
| We use | We do not use (yet) | Change when |
|---|---|---|
| MongoDB for everything | PostgreSQL / Timescale | metric rows pass about a million, or we need heavy joins |
| Plain code in fixed order | LangGraph, agent loops | a flow branches more than about 3 ways (see ARCHITECTURE section 8) |
| The existing worker and leases | Redis queues | there is real queue load |
| Sorted tables and a person | Vector database, a "learning agent" | about 50 reels with results |
| Hand-written hooks per experiment | AI trend hunter, Google Trends, YouTube ingestion | we can already measure our own reels and still lack ideas |
| Graph API polling at set ages | Webhooks for metrics (Meta's webhooks cover comments and mentions; we have not found one for insights, check in X-1) | X-1 shows otherwise |

## 4. Working agreements
- Branch per item (`content/<id>-<short-name>`), draft PR into `cursor/analyze-and-fix-styling-issues-cacb`. Do not merge `main`.
- Before a PR: `cd backend && pytest -q` and `lint-imports` (7 kept, 0 broken); `cd frontend && npx tsc --noEmit && npx jest`.
- A new figure on screen or in a caption needs a fact with a source and a date, or a calculation with a test.
- No phone numbers in reels or public captions. No "don't buy" scare hooks. No "comment X for a DM" unless something answers X.
- Scripts in `backend/scripts/` must not run on import (only parse them in tests).
- Do not add a dependency or a service without writing why in the PR.

## 5. Open facts to confirm (blocks reels 1 and 3 only)
Confirmed against official pages on 5 October 2026, and now `official` in `FACTS`: registration 1% capped at Rs 30,000 (IGR Maharashtra,
Table of Fees under the Registration Act, amended 11 Sep 2014); GST on an under-construction home that is not affordable housing works out
to 5% of the price — 7.5% on two-thirds of it, one-third deemed land (CBIC notification 03/2019, in the GST Council's consolidated rate
notification) — and none when the whole price is paid after the completion certificate or first occupation. The metro facts were already
official (PIB Cabinet releases, including Line 4 Kharadi to Khadakwasla).

Still `secondary`, so a person confirms them in Studio before approving: the portal prices per sq ft for Wagholi and Kharadi, and stamp
duty 7% (man) / 6% (woman) inside Pune's municipal limits. There is no official URL to cite for stamp duty — igrmaharashtra.gov.in publishes
its registration fee table but no duty schedule, and India Code refuses automated downloads. Wagholi is inside PMC limits (merged 1 July
2021), which is what makes the 7% rate apply to it.

## 6. Work items

Sizes: S = under a day, M = 1 to 3 days, L = more. "Needs" lists what must exist first.

### Now (this week; no new data needed)
| ID | Item | What and where | Done when | Size | Needs | Owner |
|---|---|---|---|---|---|---|
| N-1 | Deploy and server settings | Deploy the live branch. Set `CONCIERGE_OWNER_IDS` (your user id), `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION`, optionally `GOOGLE_TTS_API_KEY`. | Join requests show a badge in Studio; the site verifies in Search Console | S | | |
| N-2 | Confirm the unofficial facts | Section 5. Update `FACTS` in `reels/trend.py` (`kind`, `as_of`, `url`) and `docs/TREND_REELS.md`. | Each fact has an official URL, or the reel using it is dropped | S | | |
| N-3 | Queue and approve the trend reels | `cd backend && PYTHONPATH=. python scripts/trend_reels.py --out trend-reels --queue`; approve one a day in Studio > Calendar. | Three reels posted on Instagram and Facebook | S | N-1, N-2 | |
| N-4 | Watch the first reels | After 24 h and 72 h, screenshot each reel's retention chart (Instagram and Facebook) into `docs/content/results/`. Note hook, length, plays, average watch time, saves, shares. | A table of 3 reels with real numbers | S | N-3 | |
| N-5 | Live site check | After deploy: `/robots.txt`, `/sitemap.xml` (news, agents, `/projects`), `/projects/<slug>` canonical, `/agent/demo` is noindex, HTTP to HTTPS, 404 page, Core Web Vitals on `/` and a project page, phone width. | A checklist in the PR with pass or fail per line | S | N-1 | |
| N-6 | Search Console | Verify, submit the sitemap, request indexing for `/`, `/projects`, the three area guides. Check "Pages" a week later. | Indexed pages count recorded | S | N-1 | |
| N-7 | Fix known site items | Make sure `/agent/avasetu` exists live (`backend/scripts/make_official_page.py`) or set `NEXT_PUBLIC_DEFAULT_AGENT_SLUG`; replace the sample photo showing a "BILVAM REGENCY" signboard; give tip and pitch reels the same hook treatment as the slide reels. | The three items closed | S | | |
| N-8 | More trend reels | 6 to 10 more topics, each from sourced facts: how to check a MahaRERA number in 3 minutes; builder's date vs MahaRERA date; ready vs under construction; carpet vs saleable area; what a site visit checklist covers; Kharadi vs Upper Kharadi vs Wagholi in one line each. Add each fact to `FACTS` with its source. | Each reel passes `trend.check` and has a source line in its caption | M each | N-2 | |
| N-9 | Hook variants | For EXP-001 add variants A (price reveal), C (myth), D (first-person) over the same facts, so hooks can be compared fairly. | Four variants rendered, tagged with `experiment` and `variant` | S | N-8 | |

### Next (after about 10 reels have run)
| ID | Item | What and where | Done when | Size | Needs | Owner |
|---|---|---|---|---|---|---|
| X-1 | Check what the APIs give us | Read-only spike: for one published reel on each channel, which insights the Graph API returns with our current token (plays, reach, average watch time, shares, saves, retention curve) and which permissions are missing (`instagram_manage_insights`, `read_insights`). Write the answer in `docs/META_SETUP.md`. | A table of metric, endpoint, permission, available yes/no | S | N-3 | Automatic since 2026-10-07: the insights collector checks each metric name by itself (`insights_capabilities`) and notifies the owners once if a permission is missing. `scripts/insights_check.py --write` shows the same answer by hand. |
| X-2 | Insights collector | `modules/insights/`: for every published post, read its insights at 1 h, 24 h, 72 h and 7 d and insert a row in `content_metrics`. Runs in the worker with a lease (`platform/leases`), obeys `posting_paused`, never writes to Meta. | Unit tests with a fake Graph; a real post shows 4 snapshots | M | X-1 | Built 2026-10-07 (`modules/insights/collector.py`, worker loop `insights`): on when not in dry run; a snapshot only inside its window, with the row's tags. Waiting for the first real posts. |
| X-3 | Tags on every post | Make the creative and calendar builders write the tags in section 3 on every new row (`hook_type`, `engine`, `locality`, `price_band`, `duration_s`), including carousels and news. | New rows carry all tags; a test asserts it | S | | Done 2026-10-07 (calendar rows; news posts publish outside the calendar and are not tagged yet). Run `tag-backfill` once on the server. |
| X-4 | Enquiries per post | Count interest events and comment leads by the post's `ref` and expose them next to the metrics. | A query returns enquiries per post | S | | |
| X-5 | Studio "What worked" | A Studio table: post, channel, hook, 24 h plays, average watch time, saves, shares, enquiries; sort and filter by tag; shows the sample size. | The owner can answer "which hook held people?" without opening Instagram | M | X-2, X-3, X-4 | |
| X-6 | Verified-facts store | Collection `verified_facts`; load `reels/trend.py FACTS` and `knowledge/areas.py` into it; `facts.cite(ids)` for creative code; a daily check that lists facts expiring within 14 days in the Admin screen. | No fact is defined twice; an expired fact blocks the reel that uses it | M | N-2 | |
| X-7 | Daily digest | One message to the owner each morning: yesterday's posts and their numbers, facts about to expire, requests waiting. In-app first (notifications exist). | The digest shows in Studio home | S | X-5 | |

### Later (when we have properties or enough results)
| ID | Item | What | Needs |
|---|---|---|---|
| L-1 | Property reels with measurement | The listing and project reels carry the same tags and appear in "What worked". | X-3 |
| L-2 | Experiment planner | Plan a set of variants for one idea in the calendar and compare them (same facts, different hooks) with their sample sizes. | X-5 |
| L-3 | Comment themes | Group the questions people ask under posts (`engage` already classifies intent) into a weekly list of content ideas. | X-2 |
| L-4 | Suggestions | Plain statements with counts ("this hook held 3x the typical watch time, 14 reels"); never an auto-publish. | about 50 reels with results |
| L-5 | Agent content | Each agent's own posts and reels measured the same way. | L-1 |

### Platform track (from `docs/MODERNIZATION.md`, independent of the above)
| ID | Item | Notes |
|---|---|---|
| P-6 | One writer per collection | Start with `listings` and `agent_public_profiles`. |
| P-7 | Frontend on the new API only | **Blocked on one answer from the owner: are the old pages still used?** Check production access logs first. |
| P-8 | Delete the old code | After P-6 and P-7. |

### Listing content track (owner pain points, added 6 Oct 2026)

Real agent listings currently bypass the LLM creative engine. Publishing a listing generates a fixed, deterministic pack — cards
`cover, facts, (amenities), cta, status` (`modules/marketing/images.py:580`), template copy (`modules/marketing/content.py`), and
Facebook gets the cover only (`modules/social/service.py:66`). The strategist -> copywriter -> art_director -> critic pipeline
(`modules/creative/pipeline.py`, 8 layouts) runs only for the owner's brand calendar via CLI (`modules/calendar/adapters.py:214-234`).
There is no edit -> regenerate path, and the detail pages that exist are not linked into a graph or consistently into posts. These
items fix the five pains the owner raised (a plot in Gulmohar City yields 3 basic posts, cannot be improved manually, LLM agents sit
idle, no linked detail page).

Rule 5 note: this track is content *generation, editing and linking* for listings the owner already posts — not the learning/agent
machinery, which still waits on measurement (X and L items). Keep the fact guards: the pipeline already refuses any number not in its
Brief, so "code calculates, models write" still holds.

**A — Listings into the creative engine (fixes "3 basic posts" and "LLM idle")**
| ID | Item | What and where | Done when | Size | Needs | Owner |
|---|---|---|---|---|---|---|
| LC-1 | Listing-aware Brief | `creative/models.py:12-34` Brief has no listing fields. Add optional listing context: transaction, property_type, price_inr, bhk, carpet_sqft, locality, project_name, rera_no, amenities, media refs. Numbers stay guard-checked. | A Brief built from a listing doc passes the existing no-invented-number guard in a test. | M | | |
| LC-2 | Angles per listing | New adapter (in `modules/marketing`, or a new `modules/listingcontent`) derives several angles — buyer, comparison, local, education, price-reveal — via `creative/strategist.py` and calls `creative.pipeline.make` per angle. Cap the count and add a daily LLM budget like `reels/listing_reel.py:375-378`. | One listing yields 3 to 6 varied, tagged pieces instead of the fixed pack; the deterministic fallback (`pipeline.py:77-79`) covers LLM failure. | L | LC-1 | |
| LC-3 | Generated set drives the cards | Let the generated pieces decide which cards/posts exist and their order, replacing the constant list at `marketing/images.py:580` and the fixed IG order / FB-cover-only at `social/service.py:24,66`. | A plot with no amenities still produces more than 3 distinct pieces; Facebook can carry more than the cover. | M | LC-2 | |
| LC-4 | Trigger and wiring | Pick the trigger (recommend an explicit agent "Make content" action, queued — not a silent auto-run on publish) and wire it in `app/wiring.py:6-37`, which has no listing -> creative wiring today. | An agent action produces creative-pipeline content for their listing; LLM cost is logged. | S | LC-2 | |
| LC-5 | Cost and latency guard | Follow `backend/LLM_COST_OPTIMIZATION_GUIDE.md`: per-listing budget, model choice, caching, deterministic fallback. | Cost per listing is bounded and observable; the fallback is verified by a test. | S | LC-2 | |

**B — Edit then regenerate (fixes "no way to improve it manually")**
| ID | Item | What and where | Done when | Size | Needs | Owner |
|---|---|---|---|---|---|---|
| LC-6 | Feedback input on regenerate | `marketing/schemas.py:10-12` (GenerateIn) accepts only `language` with `extra="forbid"`. Add optional `feedback`/`note` (and `edited_text`) and thread it into the pipeline's feedback attempt (`pipeline.py:77-79`). | Regenerate accepts a note and the output reflects it (fake-LLM test). | M | | |
| LC-7 | PATCH to persist manual edits | No PATCH exists on marketing_packs, publications or calendar creative. Add PATCH to save an agent's edits and mark the piece `human_edited` so a later regenerate does not silently clobber it. | An edited caption/piece persists and is what publishes. | M | | |
| LC-8 | Studio edit UI | `MarketingPackView.tsx` is copy/download-only; `MarketingScreen.tsx:100-113` "regenerate" is a language chip. Add an editable caption field plus a "note to improve" box wired to LC-6 and LC-7. | An agent edits text and re-runs generation from Studio. | M | LC-6, LC-7 | |
| LC-9 | Stale-on-edit | `PATCH /listings/{id}` (`listings/router.py:52-58`) does not refresh derived content. Mark the pack/reel stale when the listing changes and surface "regenerate?" rather than rebuilding silently. | Editing a listing flags its content stale in Studio. | S | | |

**C — Detail pages and links in posts (fixes "proper detail page, linked in the post")**
| ID | Item | What and where | Done when | Size | Needs | Owner |
|---|---|---|---|---|---|---|
| LC-10 | Fix the dead share link | `marketing/service.py:42` falls back to `{site}/listings/{id}` — no such route. Add a site-wide `/listings/{id}` (see LC-13) or repoint the fallback to the real agent-scoped page. | No share URL returns a 404. | S | | |
| LC-11 | Link the page graph | The listing page shows `project_name` as dead text (`frontend/app/agent/[slug]/listings/[id]/page.tsx:69`). Link it to `/projects/{slug}` when matched and to `/localities/{slug}`. | From a listing page you can reach its project and area pages. | S | | |
| LC-12 | Detail URL in every post | Standardize: FB captions keep the URL (`social/service.py:62-66`; note the structured `link` field is dropped for image posts at `meta_graph/graph.py:112-114`), IG uses "link in bio" plus the existing comment -> DM interest link (`engage/runner.py:33-46`), and project carousels — which carry no link today (`agentprojects/cards.py:271-282`) — get one. Point `calendar/adapters.py:396` at the shared `/projects/{slug}`. | Every published piece has a working path to a detail page. | M | | |
| LC-13 | Area page for any locality | `/localities/[slug]` only covers the static curated list (`frontend/lib/marketing/localities.ts`); non-curated areas such as Gulmohar City get no page. Generate area pages from `areastats` / `knowledge/areas` where data exists, with a graceful fallback. | A listing in a non-curated locality has a real, indexable area page to link to. | L | | |

**C progress note - 6 Oct 2026**
- LC-10 is implemented for the legacy share path: `frontend/app/listings/[id]/page.tsx` redirects `/listings/{id}` to `/agent/{agent_slug}/listings/{id}`, preserving `?src=`. Covered by `frontend/__tests__/site/route-params.test.tsx`.
- LC-11 is implemented: listing detail pages link the project to `/projects/{slug}` (RERA-first, then exact project name; the link text falls back to the catalog name when the listing has only a RERA number) and link every locality to `/localities/{slug}` — the curated guide when one exists, otherwise the LC-13 fallback page. Later: store a direct `catalog_slug` on listings and drop the lookup.
- LC-1 is implemented: `creative/listing_brief.py` `brief_from_listing(doc)` builds a Brief from a stored listing dict. Numbers are written as the copy would say them ("₹85 lakh", "1,050 sq ft carpet", "2 BHK") so the guard accepts listing facts and still rejects any other number; missing fields stay empty. `listing_media_refs` is carried but kept out of `corpus()` because URLs carry stray digits. Covered by `backend/tests/modules/creative/test_listing_brief.py`, including a full `pipeline.make` run. Note: a listing brief is only as rich as what the agent typed; richer posts need a verified project fact sheet (not yet a work item).
- LC-12 is partially implemented for project content: House Deal project carousel/reel captions and calendar project reel captions now point at canonical `/projects/{slug}` pages; public feed cards extract that URL. Remaining: audit every listing/social publishing caption after LC-2/LC-3 creates generated listing content, especially Instagram's link-in-bio hub and any non-House-Deal project scripts.
- LC-13 is partially implemented: `/localities/[slug]` now has a graceful fallback for non-curated locality slugs such as `/localities/gulmohar-city`, but only renders when public listing/project data exists for that locality. It shows live listings/projects plus generic buyer checks, and does not invent area-specific facts or sources. The sitemap now discovers these non-curated locality pages from listing/project locality data (`listings.service.sitemap_entries`, `frontend/app/sitemap.ts`). Covered by `frontend/__tests__/marketing/locality-area-pages.test.tsx`, `frontend/__tests__/marketing/localities.test.ts`, and `backend/tests/modules/test_listings_service.py`. Remaining: richer data from `areastats`/`knowledge/areas` when available.
- Verification used while making these changes: frontend focused Jest (`locality-area-pages`, `locality-area-feed`, `localities`, `route-params`, `catalog`) passed with 49 tests; backend focused pytest for project captions/public feed passed with 25 tests; backend listing service tests passed with 56 tests; `cd frontend && npx tsc --noEmit` passed.

Frontend caution for LC-8, LC-10, LC-11, LC-13: this repo's Next.js has breaking changes — read `node_modules/next/dist/docs/` before
writing any route or page code (per `frontend/agents.md`).

Suggested order: **C first** (low risk, mostly wiring, fixes links immediately), then **A** (the core payoff), then **B** (most
valuable once A produces richer pieces to edit). A and C can run in parallel.

### Property campaign track (owner direction, 6 Oct 2026; supersedes LC-2 to LC-5)

Marketing a property means many posts, not one pack. Goal: one listing -> a **campaign of 8 to 12 pieces over about 14 days**, each a
different angle on one fact sheet, each linking to the detail page, each tagged so enquiries per piece are known. A listing alone is
too thin (an agent types "Plot in Ranjangaon"), so the fact sheet is gathered **automatically**: project, builder, location,
surroundings, price, sizes, amenities. Automation comes first; manual fact checks are added later. The one-tap approval before a post
publishes (rule 3) stays.

**Trust without a person (replaces "confirmed by a person" in rule 2 for this track, for now).** Every fact keeps its sources and
gets a level computed by code:

| Level | Meaning | Used in posts? |
|---|---|---|
| official | from MahaRERA | yes |
| measured | computed by our code (OSM distance, price per sq ft, EMI) | yes |
| corroborated | the same value from two independent sources (for example 99acres and MagicBricks), within a tolerance | yes; prices said as "listed from Rs X", with the date |
| single | one portal only | no; stored and shown in Studio |
| conflict | sources disagree (for example possession "ready 2023" vs "Dec 2028") | no; becomes a project `Issue` |

| ID | Item | What and where | Done when | Size | Needs |
|---|---|---|---|---|---|
| PF-1 | Fact record | New `modules/propertyfacts`: a fact is `{key, value, sources: [{name, url, fetched_at}], level, as_of, valid_until}`; the level is a pure function of the sources. Add the module to `.importlinter` in the content layer. | Unit tests cover every level, including conflicts. | S | |
| PF-2 | MahaRERA identity | Resolve a listing to its registration: by `rera_no`, else MahaRERA search by project name (+ pincode) via the parser in `newsroom/sources/maharera.py`; read the general details with `agentprojects/maharera.py` (possession original and revised, units total and booked). Store the project slug on the listing (drops the LC-11 lookup). | A listing with only a project name gets official facts and a project link. | M | PF-1 |
| PF-3 | Builder record | MahaRERA search by promoter -> their registered projects; per project, original vs current completion date. Numbers only ("9 registered projects, 3 with a revised completion date"), no ratings, organisations only (the existing `_ORG` rule). | A builder line with counts and the MahaRERA link. | M | PF-2 |
| PF-4 | Location and surroundings | Place the project (MahaRERA address/pincode, then Nominatim), then Overpass for schools, hospitals, stations, bus stands, MIDC and IT parks, highways and malls within 5 km; road distance by OSRM. Cache, rate limit and identify ourselves per the OSM usage policies. Fills `Nearby` with `source="osm"`. | A Ranjangaon project shows its 8 nearest useful places with measured km. | M | PF-1 |
| PF-5 | Portal readers | 99acres, MagicBricks, Housing.com project pages: configurations, sizes, price range, amenities, possession. Parsers tested on saved HTML; rate limited and cached; a blocked or changed page is a normal "no data", never an error. Portal photos are never reused (copyright). Each portal can be switched off by config. | Two portals return parsed facts for Gulmohar City. | L | PF-1 |
| PF-6 | Cross-check and assemble | Merge PF-2 to PF-5 and the listing; compute levels; conflicts -> `Issue`; build the Brief from usable facts only (extends `creative/listing_brief.py`). | The sheet for Gulmohar City lists usable, held-back and conflicting facts with sources. | M | PF-2, PF-4, PF-5 |
| PF-7 | Calculators | Price per sq ft, EMI (stated rate and its date), size in everyday terms. Code calculates, the model writes. | Each has a test; results enter the sheet as "measured". | S | |
| CA-1 | Angle catalogue and planner | Angles (price reveal, budget framing, size made real, commute, MahaRERA check, myth vs fact, comparison, checklist, EMI, poll, walkthrough), each declaring the fact keys it needs. The planner picks angles whose facts are usable, makes 2 to 3 hook variants each and runs `creative.pipeline.make`; per-listing LLM budget; deterministic fallback. | Gulmohar City yields 8+ distinct pieces, all passing the guards. | L | PF-6, PF-7 |
| CA-2 | Campaign schedule | A "Make campaign" action queues the pieces as planned calendar rows over 14 days with tags (X-3) and `?src=` detail links (LC-12, X-4), plus a WhatsApp pack (status images and a forward message). The fixed pack in `marketing/images.py` stays as the fallback. | One action fills two weeks of the calendar for a listing. | M | CA-1 |
| CA-3 | Reels from the campaign | Turn the best carousels into slide reels (`reels/slides.py`); add the walkthrough from `reels/listing_reel.py`. | Each campaign has at least 2 reels. | M | CA-1 |

Order: PF-1, PF-2, PF-4 and PF-7 first (official and measured data; no scraping risk), then a first CA-1 on those facts, then PF-5
and PF-6 (portal data), then CA-2 and CA-3. First milestone: Gulmohar City's sheet and 8 pieces produced by one script, with no
manual input. Risk: portals may block or change pages, and scraping may break their terms (the owner accepted this on 6 Oct 2026);
the readers stay in one place so they can be switched off.

**PF progress, 6 Oct 2026:** PF-1 and PF-2 are implemented in `backend/app/modules/propertyfacts` (`facts.py` trust levels, `place.py` Nominatim taluka lookup, `registration.py` MahaRERA name search + taluka/RERA disambiguation + official details, `gather.py` one sheet per listing). The agent's own listing counts as official for its own offer. A MahaRERA outage is reported as "did not answer", never as "no such project". Run live: `cd backend && PYTHONPATH=. python scripts/property_facts.py --project "Gulmohar City" --locality Ranjangaon --type plot` -> matched P52100076768 by name and taluka, 13 official facts, possession moved 4 months. Tests: `tests/modules/propertyfacts` (18). Not yet: storing the sheet and the project slug on the listing; a RERA-number-only listing (needs the newsroom register lookup, since MahaRERA search ignores `regno`).

**Showcase, 6 Oct 2026 (quick first version; improve in place):** PF-4 `propertyfacts/surroundings.py` (Overpass, with a Nominatim fallback because the public Overpass server often answers 504/406; straight-line km), PF-7 `propertyfacts/calc.py` (price per sq ft, guntha, EMI with stated assumptions), CA-1 `propertyfacts/campaign.py` (11 angles; each is one function, add to `ANGLES`; hand-written hooks name the project; the card chip shows the project). Creative gained `Brief.kicker` and real photo files / `photo="none"` (a plot is not a tower). Run: `cd backend && PYTHONPATH=. python scripts/property_campaign.py --project "Gulmohar City" --locality Ranjangaon --type plot --price 3230000 --sqft 1927 --out <dir> [--llm]` -> 12 guard-clean posts; output in `docs/content/showcase/gulmohar-city/`. Next to improve: road distance (OSRM), the listing's own photos, LLM copy by default, builder record (PF-3), portals (PF-5), queue into the calendar (CA-2), reels (CA-3).

**Register first, keep every sheet (6 Oct 2026):** `registration.lookup` now asks our MahaRERA register (newsroom `projects`, kept fresh by the areastats sweep) before MahaRERA, by RERA number or by name + taluka, when the record's details are under 45 days old; this also makes a RERA-number-only listing work. The register stays read-only for this track (it feeds the area stats and the newsroom). Every gathered sheet is kept in `property_facts` (`propertyfacts/store.py`): each fact with its level, sources and read time. `scripts/property_campaign.py --db` uses both. Limit: the register covers only our 8 areas' pincodes, so Ranjangaon still comes live from MahaRERA.

**On the website (6 Oct 2026):** listing pages show a "Checked for you" box (`frontend/components/site/VerifiedFacts.tsx`) from `GET /api/v1/public/property-facts?rera=&project=&locality=` (`propertyfacts/router.py`, `public.py`): the MahaRERA record (with "was <date>" when the completion date moved and a link to check it), up to 5 nearby places (straight-line, OSM credit) and worked-out numbers (rate per sq ft, guntha, an EMI example with its assumptions). Usable facts only; nothing renders when no sheet is kept. A sheet exists only after `scripts/property_campaign.py --db` (or a later automatic trigger) ran for that property.

**Start marketing from Studio (6 Oct 2026; replaces the CA-2 trigger idea):** the marketing screen has a "Start marketing" card (`frontend/components/app/MarketingRunCard.tsx`). `POST /api/v1/listings/{id}/campaign` queues one run in `marketing_runs`; the worker loop `marketing_runs` (`propertyfacts/jobs.py`, in `app/worker.py`) does **step 1** (gather and keep the fact sheet; the listing page then shows "Checked for you") and only then **step 2** (the campaign posts, as drafts under `/uploads/campaigns/<listing>/`; nothing publishes without approval). A failed step 2 keeps step 1. Kept sheets with a MahaRERA number feed the register's watch list (`app/wiring.py`, source `property_facts`), so their details stay fresh. Next: queue the drafts into the approval calendar, a per-listing LLM budget (LC-5), reels from the posts (CA-3).

**Calendar, reels, edit and improve (6 Oct 2026):** after the posts, the run makes up to 2 slides reels from its carousels (`reels.slides.make_slides_reel`, opening on the hook) and queues the walkthrough reel (`reels.listing_reel`, needs 2+ photos); a reel failure never loses the posts. "Send to calendar for approval" (`POST /listings/{id}/campaign/calendar`, `propertyfacts/schedule.py`) adds planned rows, one a day at 7 pm IST, 12 h from other posts on the channel: every post on Instagram and Facebook (Facebook's caption carries the page link with `?src=fb_<angle>`), slides reels on Instagram only (Facebook turns carousels into reels itself), the walkthrough on both once rendered (send again to add it). Slugs are `campaign-<listing>-<angle>` with the agent's id, so the calendar's interest link counts enquiries per post. Per post, Studio can edit the caption (`PATCH .../campaign/posts/{angle}`; the checks come back as warnings) or make it again with a note (`POST .../posts/{angle}/redo`; the note is the copywriter's feedback, `pipeline.make(note=)`); planned calendar rows follow, approved ones never change (`calendar.store.set_planned`). Campaign captions name the property (`Brief.intro`, `link_line`, `writer_note`).

**Live source check, 6 Oct 2026 (Gulmohar City, Ranjangaon):**
- MahaRERA search by name: works. Two projects are called "Gulmohar City" (P52100076768, pincode 412209 Ranjangaon; P52100077275,
  410501 Chakan), so a name match must also check pincode or locality. The Ranjangaon card shows no promoter name (an individual,
  or not given), so PF-3 must handle a missing builder.
- MahaRERA details (id 46398): plotted, registered 2024-06-28, completion 2028-12-31 at registration and **2029-04-30 now**, 123
  units, 0 reported booked. A web AI answer the owner pasted said "December 2028", already out of date: the official reading is
  the product's edge.
- Nominatim and Overpass: work, but OSM is sparse around Ranjangaon (5 km gave 1 hospital and 3 industrial sites: MIDC, Cummins,
  IndoSpace). PF-4 needs wider radii and categories by place type, and must say "nearest X: none found within N km" rather than
  imply there is none.
- Portals: 99acres answered 403 (bot block), Housing.com 406, MagicBricks search returned a 4 KB script shell (the listing is
  rendered in the browser). Plain HTTP will not do: PF-5 needs a headless browser (Playwright is already a dev dependency) or a
  search API to find each project page, and is the least reliable source. Keep it last, as ordered above.

### Prompt track (6 Oct 2026)

Code chooses the facts, angles, segments and order; the LLM writes hook variants and copy; the guards check every number and
name against the facts. All system prompts live in `backend/app/modules/creative/prompts.py`, built from a `Voice` (who speaks,
in which area) and a mode: `brand` (explainers, no prices) or `listing` (markets one property; its price, project, builder and
MahaRERA details only exactly as the facts state them).

| ID | Item | Done when | Size | Needs |
|---|---|---|---|---|
| PM-1 | Prompts take a voice and a mode | Brand prompts byte-identical (snapshot); listing prompts name the listing's area and allow its listed facts | S | |
| PM-2 | Prompt registry and version tags | Each pack and calendar row records `copywriter@1/listing`-style tags; a test pins each version's text | S | PM-1 |
| PM-3 | Golden test for Gulmohar City | A fake LLM's invented number, superlative, prediction, phone and builder name never reach the copy | S | PM-1 |
| PM-4 | Fact ids and citation | Copy returns the fact keys it used; a number from an uncited fact is refused | M | PM-1 |
| PM-5 | Hook writer, 3 variants per angle | Each angle gets up to 3 guarded hooks of different patterns, tagged `experiment`/`variant`, none repeated in the campaign | M | PM-4 |
| PM-6 | Segments as a code table | Each angle names its segment (plot: investor, end user who builds, NRI); copywriter and critic get it | S | |
| PM-7 | Sibling check | No two pieces of a campaign share a near-identical opening line (word overlap, code) | S | |
| PM-8 | Reel script prompt | Scene lines tied to fact keys; two campaign reels pass `valid_script` | M | CA-3 |
| PM-9 | WhatsApp forward prompt | Hinglish forward with the `?src=whatsapp` link passes the number guard | S | CA-2 |
| PM-10 | LLM budget per listing | Call count capped per campaign; the deterministic path fills the rest (test with a counting fake) | S | |

**PM progress, 6 Oct 2026:** PM-1, PM-3 and PM-2 are implemented. `prompts.py` builds the strategist, copywriter, translator
and critic prompts; brand mode matches the pre-change text byte for byte (`tests/modules/creative/fixtures/brand_prompts.json`).
Campaign briefs (`propertyfacts/campaign.py`, optional `voice=`) and `creative/listing_brief.py` are `mode="listing"` with the
listing's area; the sign-off follows the voice. New guard: a builder or company name (`... Developers`, `Realty`, `Pvt`, ...)
not in the facts is refused (`guards.unsupported_orgs`). `CreativePack.prompts` lists the tags of the prompts whose output was
kept; campaign posts, their calendar rows and brand calendar rows carry them. Changing a prompt's text means bumping
`prompts.VERSIONS` and adding its hash to `fixtures/prompt_versions.json` (the test says so). Tests:
`tests/modules/creative/test_prompts.py`, `tests/modules/propertyfacts/test_campaign_prompts.py`. Not yet: a reviewed snapshot of
a real `--llm` run for Gulmohar City in `docs/content/`.

## 7. What good looks like in three months
Thirty or more reels with results; a Studio table the owner opens each morning; each post's facts traceable to a source; enquiries per
post known; the first two or three hook patterns that hold attention written down with their counts. Anything beyond that (agents,
learning loops, a second database) is justified by what that table shows, not by this page.
