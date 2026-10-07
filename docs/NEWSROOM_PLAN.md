# Newsroom: the content agent

Goal: keep the Avasetu Page and site fresh with accurate, useful, original content about Kharadi, Upper Kharadi, Wagholi and the things that change life there (roads, metro, approvals, new registrations, rules). Trust comes first: a wrong claim costs more than a missed post.

This plan makes the editorial decisions so the owner does not have to. The owner only approves or rejects.

## 1. Editorial policy (lives in one file: `policy.py`)

**Pillars** (what we cover, in priority order)
1. **Infrastructure and approvals**: metro, roads, ring road, airport, bridges, PMRDA/PMC notices. Why: changes daily life and prices, and news here is frequent.
2. **New supply (MahaRERA registrations)**: project name, locality, promoter, registered possession date. Facts only.
3. **Rules and money**: RERA rules, stamp duty and registration changes, home-loan rate moves. Explained simply.
4. **Locality life**: schools, hospitals, office and IT-park news, civic issues (water, traffic) in our three areas.
5. **Buyer education (evergreen)**: checklists, myth vs fact, "how to read" guides. Fills gaps when there is no news.
6. **Weekly digest**: one post a week, "Kharadi and Wagholi this week", 3 to 5 items.

**Formats**: short Page post (ends with a question), explainer article on the site, weekly digest, myth-vs-fact, poll. Each pillar maps to the formats that suit it.

**Rules a draft must pass** (enforced in code, not only in the prompt)
- Every claim traces to a source sentence. Every number, date and name in the draft appears in the source text.
- Our own words. Quotes of 15 words or fewer, with attribution. Always a source name plus link. Never copy headlines or paragraphs.
- No price predictions, no "invest now", no guarantees, no endorsing or criticising a named builder. Transport follows "approved is not running".
- "As of" date on every news item. Items older than 14 days are dropped, except for evergreen pieces.
- No phone numbers or personal names (existing `HYPE` and `PHONE` guards are reused).
- Our own view ("what this means for a buyer") is labelled as such and stays hedged.
- Corrections: if a source is later updated, the item is flagged for review and the published post gets a correction line.

**Article shape**: what happened (1 to 2 sentences) → why it matters to someone buying or renting here → what to check → sources → as-of date and the standing disclaimer.

**Cadence**: 3 to 4 Page posts a week, one digest, 1 to 2 site explainers a week. A daily cap stops runaway output. No news means an evergreen post, never filler.

## 2. Architecture: small parts, one direction, one place for state

The rule that keeps it maintainable: **stages never call each other**. They only read and write items in one store, moving each item along a status. Replace or test any stage without touching the others.

```
Source plugins ──► [collect] ─► store ─► [filter] ─► [extract] ─► [draft] ─► [check] ─► review queue
                                                                                          │ approve
                                                   Page / Site (via ports) ◄── [publish] ◄┘
                                                                ▲
                                                   [measure] ───┘ (reads reactions back)
```

Item status: `new → relevant → extracted → drafted → checked → pending_review → approved → scheduled → published`. Side exits: `dropped` (irrelevant, stale, duplicate), `rejected` (by owner), `failed` (with a safe reason).

**Module layout** (`backend/app/modules/newsroom/`)
```
policy.py            pillars, formats, rules, banned phrases, caps. Plain data, no I/O.
sources/             one small file per source, all implement Source.fetch() -> list[RawItem]
  base.py            the Protocol and RawItem
  google_news.py     RSS searches
  maharera.py        new registrations
  rss.py             any official or news feed from config
stages/              pure functions: text in, typed result out. The LLM is passed in.
  filter.py  extract.py  draft.py  check.py
store.py             the ONLY file that touches Mongo (collection newsroom_items)
ports.py             narrow interfaces the newsroom needs from outside: Publisher, SiteWriter, Clock, Llm
adapters.py          connects the ports to the existing social module and LLM chain
runner.py            the loop, same pattern as the comment assistant: enabled flag, never crashes
router.py            owner-only API: queue, approve, edit, reject, status
```

**Coupling rules**
- `newsroom` imports nothing from `engage`, `chat`, `listings` or `onboarding`. It reaches Facebook only through the `Publisher` port and the LLM only through the `Llm` port. Other modules never import `newsroom`.
- The site reads published articles from a public endpoint (`GET /public/insights`), so the frontend depends on an API contract, not on the pipeline.
- Sources are plugins. Adding one is one new file plus one config line. Turning one off is a setting.
- Every stage is idempotent: running it twice does not duplicate or corrupt anything.
- Settings: `NEWSROOM_ENABLED`, per-source enable flags, daily cap, interval. Default off.

## 3. Quality and safety controls
- **Verification is code**: a `check` stage compares every figure, date and proper noun in the draft with the source text, plus the existing guards. A failing draft never reaches the owner's queue as "ready".
- **Two-source rule for big claims**: a milestone (for example a metro opening date) needs an official source or two independent reports, otherwise it is labelled "reported".
- **Fetch hygiene**: prefer RSS and official pages, obey robots.txt, identify ourselves, rate-limit, cache. No login-walled or paywalled scraping.
- **Kill switches**: one flag stops all publishing. The owner can pause a pillar.
- **Audit trail**: each item keeps its sources, the extracted facts, the draft versions and who approved it.

## 4. Tests (how it stays understandable)
- Recorded fixtures per source, so tests never hit the network.
- Golden articles per stage: known input, expected facts, expected draft properties.
- Adversarial cases: article with conflicting numbers, an old article re-shared, a press release full of hype, a prediction phrased as a fact. The check stage must reject each.
- Contract test for each Port, so swapping an adapter cannot silently break a stage.

## 5. Delivery phases
| Phase | What ships | Done when |
|---|---|---|
| N1 slice | Google News and MahaRERA sources, filter, extract, check, draft Page posts, review queue in Studio, scheduling to the Page | Owner approves real drafts from live sources; every published post passes the checks |
| N2 site | Articles stored in the database, `/insights` renders them, sitemap updated | New article appears on the site with sources and as-of date |
| N3 digest and learning | Weekly digest, read reactions and comments back, rank pillars and formats by response | Digest goes out weekly; a report shows what worked |
| N4 scale | More sources, auto-publish for low-risk types (official source, factual) after about 20 approvals with few edits | Approval rate above 80 percent with minimal edits |
| N5 later | Instagram (once linked), Reels from cards, Hindi and Marathi variants | After Instagram is Professional |

## 6. Risks and answers
| Risk | Answer |
|---|---|
| Wrong claim published | Code-level verification, approval gate, corrections flow |
| Copyright complaint | Own words, tiny quotes, link to the source |
| Builder or defamation issue | No named-builder praise or criticism; facts from official registrations only |
| Sources change format | Plugin per source with fixture tests; failures are logged and skipped, never fatal |
| Free-model quality drops | Stages have small prompts; the existing provider failover applies; output is verified, not trusted |
| Complexity creep | The store is the only state, stages are pure, and ports keep boundaries. Each new idea is a stage or a source, not a change to the core |
