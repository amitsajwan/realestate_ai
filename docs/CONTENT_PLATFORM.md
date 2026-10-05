# Content platform: target architecture and work items

Last updated 5 October 2026. Owner: Amit. This is the plan for how Avasetu makes, publishes and learns from content (posts, reels,
news) and turns it into buyer enquiries. It sits inside `docs/ARCHITECTURE.md` (the modular monolith) and does not change it.

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
- `content_calendar` row, existing: add to `creative` the tags `experiment`, `variant`, `hook_type`, `engine`, `locality`, `price_band`, `duration_s` (trend reels already write these).
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
Portal prices per sq ft; stamp duty 7% (man) / 6% (woman) and whether Wagholi is inside municipal limits; registration 1% capped at Rs 30,000;
GST 5% on two-thirds of the price (under construction), none when ready. Official pages: igrmaharashtra.gov.in and the GST Council.
The metro reel uses official sources (PIB) only.

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
| X-1 | Check what the APIs give us | Read-only spike: for one published reel on each channel, which insights the Graph API returns with our current token (plays, reach, average watch time, shares, saves, retention curve) and which permissions are missing (`instagram_manage_insights`, `read_insights`). Write the answer in `docs/META_SETUP.md`. | A table of metric, endpoint, permission, available yes/no | S | N-3 | |
| X-2 | Insights collector | `modules/insights/`: for every published post, read its insights at 1 h, 24 h, 72 h and 7 d and insert a row in `content_metrics`. Runs in the worker with a lease (`platform/leases`), obeys `posting_paused`, never writes to Meta. | Unit tests with a fake Graph; a real post shows 4 snapshots | M | X-1 | |
| X-3 | Tags on every post | Make the creative and calendar builders write the tags in section 3 on every new row (`hook_type`, `engine`, `locality`, `price_band`, `duration_s`), including carousels and news. | New rows carry all tags; a test asserts it | S | | |
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

## 7. What good looks like in three months
Thirty or more reels with results; a Studio table the owner opens each morning; each post's facts traceable to a source; enquiries per
post known; the first two or three hook patterns that hold attention written down with their counts. Anything beyond that (agents,
learning loops, a second database) is justified by what that table shows, not by this page.
