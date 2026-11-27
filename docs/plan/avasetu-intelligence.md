# Avasetu Intelligence: what to build and what not

**Status:** TARGET. Written 2026-11-27 from the Nov 25-26 "Avasetu Intelligence" vision (four engines: Property Truth,
Intelligence, Agentic, Marketplace), read against what already runs. Branch `intelligence/know-before-you-buy`. Nothing here
is built yet.

## The finding: most of the vision already runs

The vision reads like a new product. It is mostly a description of Avasetu as it stands. What it asks for, and where it lives:

| Vision | What already runs (LIVE unless marked) | Gap |
|---|---|---|
| **Truth: MahaRERA records** | the register (`areastats.refresh`, `projects`), dated readings (`readings.py`), all-Pune first reads, new-launch lane, discovery by number (`discover.py`) | none worth a project |
| **Truth: builder history** | builder pages, "builder's other projects and how many moved their date" (`/check`), `samegroup.py`, `brands.py` | not shown as one track record on the project page |
| **Truth: approvals, OC** | nothing held; the page says "ask for the OC" when the date has passed | the MahaRERA record has documents we do not read |
| **Truth: court cases, complaints** | nothing | see "not now" |
| **Truth: construction progress** | Esri past pictures (`esripast.py`), from space (`fromabove.py`), site visits by a person (`sitevisits.py`) | declared vs seen is not put side by side |
| **Truth: sources and evidence** | `propertyfacts.Fact` levels, checked web facts (`webfacts.py`), sources panel, listing vs MahaRERA check | no single per-project list of "claim, source, date, level", and no "what we don't know" |
| **Intelligence: compare projects, areas** | `compare.py` (area vs area), top lists, price table, cautions (`cautions.py`), sales pace (`pagefacts.sales`), area rate | project vs project not built |
| **Intelligence: asking vs registered prices** | price idea bands (`priceidea.py`); IGR Index-II pilot finds by document number only | IGR property search does not work, so no transaction prices |
| **Intelligence: supply, demand, trends** | area stats, booked-homes readings, hot projects, demand (`demand.py`), new launches | fine |
| **Agentic: answer buyer questions** | site chat (RAG, `knowledge`), WhatsApp bot, project page ask box, BuyerMind briefs | fine |
| **Agentic: monitor changes** | trackers, newsroom, readings, date-moved follow-ups | fine |
| **Agentic: buyer brief to shortlist** | BuyerMind writes a brief; nothing turns it into a ranked list of projects | **the main gap** |
| **Marketplace** | agent network, MahaRERA-verified agents, lead board, points pick (`docs/plan/agent-network.md`, steps 1-2 built, unmerged) | being built today; do not fork it |

So "Avasetu Intelligence" should be how we **name and package** what runs, plus two missing pieces. It is not a rebuild.

## What we should do

1. **Know Before You Buy report, one per project, free and public.** Put together what we already hold into one page section
   (and a `/check` result): MahaRERA status and date moves, the builder's track record, sales pace, price band, cautions,
   pictures over time, site visit. Every line carries its **source, date read and trust level**, and the report ends with
   **"What we could not check"** (OC, litigation, title, construction stage when no picture or visit). Code writes every line,
   as `cautions.py` and `compare.py` do; a model may only phrase the summary under the copy guards (rule 7). This is the
   differentiator in the vision ("evidence and limitations, not guarantees") and it is mostly assembly.
2. **Buyer brief to shortlist.** "₹1.5 Cr, 3 BHK, Kharadi or Wagholi, office at EON, possession within 2 years" becomes a
   short list from the register: filter by price table, BHK, possession date, commute to the hub (`pagefacts.commute`), and
   rank by fixed rules (as the agent points are), each with its reasons and its unknowns. The model only reads the buyer's words
   into the filter fields; the list is code. It answers in chat, WhatsApp and on a `/shortlist` page, and the brief rides along
   when the lead is passed to an agent, which is what makes a lead worth asking for on the board.
3. **Project vs project.** Two or three projects side by side, from the same fields as the report. Comes almost free after 1.
4. **Builder track record on the page.** Projects delivered, how many moved their date and by how much, from the register.
5. **Agents get the report as a tool.** The agent network promises "project research"; this is it. An agent can send a
   project's report to a buyer under their own page. No new pricing.

Order: 1, then 2, then 3-5. The agent network work stays first in line; this does not touch its files.

## What we should not do (now)

- **No new platform, no LangGraph, no microservices.** We already have the modular monolith, the LLM gateway with guards and
  fallbacks, worker loops with leases and budgets. A graph framework adds a dependency and hides the rules that make output
  safe. The "research workflow" (identify, acquire, extract, match, validate, contradict, review, report) is what the enrich
  lanes already do.
- **No second repository or rewrite.** The vision itself said to audit `realestate_ai` first. This is the audit.
- **No litigation or court-record scraping.** Matching an SPV promoter to an eCourts case by name is unreliable (we already saw
  SPV promoter names hide builders), a wrong match says a builder is in court, and that is a defamation risk on a money page.
  Revisit only with a source keyed by MahaRERA number (MahaRERA complaints on the project record) and a person checking.
- **No "overpriced" or "good deal" labels.** We have no transaction prices (IGR searches by document number only) and the
  price rule stands: one-site portal ranges are not reliable. Show bands and the area rate; let the buyer judge.
- **No "safe", "verified project" or investment-return claims.** Evidence and limits only. MahaRERA-verified applies to agents
  (their registration), never to a project's quality.
- **No paid reports, enterprise API or institutional tier yet.** No traffic to sell to and no data licence for it. The free
  report is the SEO and trust asset; agents pay later for tools (`agent-network.md` already decided free to start).
- **No new cities.** All of Pune first; the register and the rules are Pune- and MahaRERA-shaped.
- **No AI agent that publishes or picks an agent.** Rules 6 and 7 stand: the shortlist and the agent pick are code.

## Why: the SEO differentiator (owner 2026-11-27)

All of this exists to rank. Portals have more listings; what they cannot copy is **a dated record of each project, kept by us
over time**: what MahaRERA said each month, how many homes sold, when the date moved, and what the pictures showed. That
history cannot be rebuilt later by a newcomer (`seo-system.md` 8b). Every piece above should leave a public, dated, linkable
fact on a project or area page.

## MahaRERA history: sales per month (owner 2026-11-27)

**What we hold today:** `booked_history`, which is one dated homes-booked count each time the count changes. It is read by the
register refresh (`areastats.refresh`), about once every 30 days per project (180 for finished ones), plus whenever page
enrichment reads it. `completion_history` records every date move. `hot.py` and `pagefacts.sales` already use both. The
history only goes back to October 2026, so most projects have one or two readings. That is too thin for a sales-per-month
figure today.

**What to do:**
1. **Read selling projects weekly, starting now.** A project that is under construction and has unsold homes gets details every
   7 days instead of 30; finished and sold-out projects stay as they are. Each week of delay is history we can never get
   back. Cost: MahaRERA requests only (still PAUSE apart), no money. First count how many Pune projects are "selling", so
   we know the per-day reads fit in the current steps.
2. **Look for MahaRERA's own history.** Promoters file quarterly progress reports (units booked, construction stage) on the
   project record. If the public portal serves past quarters without login or captcha, one backfill gives years of quarterly
   sales for each project at once, and the construction stage MahaRERA has on file (the "declared" side of declared vs seen).
   This is a one-day spike: find the endpoint or the document, read 3 projects by hand, and decide. If it needs a login or
   captcha, we do not use it (the same rule as the other closed endpoints).
3. **Monthly sales, from the readings.** A code-only function: homes booked per month between readings, spread evenly across
   the gap and labelled with the dates read ("about 12 a month between 3 Nov and 1 Dec, from MahaRERA's count"). Never a
   figure when the gap is long or a count went down (a cancellation or a corrected filing is shown as is).
4. **Use it everywhere it is a fact:** a sales line and small chart on the project page and the report, "selling fastest this
   month" lists per area (an indexable page), area totals sold per month for the newsroom and number-of-the-week reels, and a
   sales-pace point in the shortlist. Each says when we read it.

Order: 1 and the spike (2) first, because they start the clock. Monthly sales (3-4) after the report's first version.

### Built 2026-11-27 (branch `intelligence/know-before-you-buy`)

- **Weekly reads of selling projects.** `areastats.refresh._due` now re-reads a project with homes still to sell
  (`0 <= units_booked < units_total`, not finished) every `SELLING_MAX_AGE_DAYS = 7`, where sold-out and finished stay on 30/180.
  This is the clock for the only sales history we can have. Self-throttling: `details()` still reads at most `limit` per step,
  PAUSE apart, so a longer due queue just stretches the cadence; it never floods MahaRERA.
- **MahaRERA status flag.** `refresh.details` takes a `fetch_status` (`maharera.make_fetch_status`, the open
  `getProjectCurrentStatus`) and keeps `maharera_status` / `maharera_deregistered` / `maharera_abeyance` / `maharera_status_at`
  on the record. `pages.status_flag` turns that into `'deregistered'` / `'abeyance'` / None; the project view sends it as
  `maharera_status`. The site (`RegisterProjectPage` `StatusWarning`) leads a flagged page with a red alert stating MahaRERA's
  record, the date read and a link, and drops every enquiry CTA (an agent's own listing of it is left alone). Active projects
  are unchanged.
- **Not built:** complaints-by-project (endpoint open but we have not seen a populated response to parse safely — find one
  first), and the monthly-sales figure (needs a few weeks of the new weekly readings).

### Spike result, 2026-11-27: what MahaRERA serves without login

The public pages' code (`publicpage/main.js`) lists many endpoints. We called each once for project 43848 (Kosmic Kourtyard
Phase 2), 2 s apart. Base: `/api/maha-rera-public-view-project-registration-service/public/projectregistartion/`, POST
`{"projectId": <id>}`.

| Endpoint | Open? | What it gives |
|---|---|---|
| `getProjectGeneralDetailsByProjectId` | open (already used) | today's sold and total units, dates, status |
| `getBuildingWingUnitSummary` | open (already used) | per-building counts |
| `getProjectPreviousExtensionDetails` | **open, new** | every extension: original date, revised date, delay reason, application number. This is the **full date-move history back to registration**, which our `completion_history` (since Oct 2026) lacks |
| `getProjectCurrentStatus` | **open, new** | Active, deregistered, in abeyance (a buyer's red flag, not read today) |
| `getComplaintDetailsByProjectId` | **open, new** | complaints, misc complaints and recovery warrants **keyed by the project**, not by builder name. Empty for 43848; the shape still needs a project that has some |
| complaint service `getComplaintByProjectId` | open, new | "NO_RECORDS_FOUND" for 43848; same need |
| `getLastQPRFormDetails`, `getUploadedDocumentsWithQPR`, `getUploadedDocuments` | **401** | quarterly progress reports and documents need a signed-in token |
| `getProjectSoldUnsoldInventory`, `getProjectFinanceInventoryDetails`, `getProjectBuildingWingsFloorUnit` | **401** | inventory over time, unit by unit: closed |
| `getProjectLitigationDetails` | **401** | litigation the promoter declared: closed |

What this means:
- **No past sales from MahaRERA.** The quarterly reports and the sold/unsold inventory sit behind a login, so we don't use them
  (same rule as before). The only sales history there will ever be is the one we keep ourselves, so step 1 (weekly reads)
  matters more, not less. The sold count likely moves when the builder files the quarterly report, so the honest grain is
  "sold this quarter, filed on <date>". Weekly reads tell us within a week when each filing lands, and that date is itself
  a fact. Check this against `booked_history` before promising a monthly figure.
- **Full date-move history: yes, backfill it.** One read per project gives every extension since registration. That feeds
  the report, `/check`, cautions, the builder record ("N of 12 projects extended, by 7 months on average") and the date-watch
  reels, with years of depth on day one.
- **Complaints and warrants: yes, by project.** This answers the "no litigation scraping" worry: matched by MahaRERA project
  id, not by name. Show a count and MahaRERA's own words with the date read, never a judgement. Find a project that has
  complaints to pin the response shape first.
- **Status: yes.** Deregistered or in abeyance goes at the top of the report and turns off the enquiry form.
- Cost: three more requests per project per read, still 2 s apart; the extension history only needs a re-read when the
  completion date changes.

## Money and the ₹5,000/month budget

The vision's ₹5,000 a month is already below what runs: the VM alone was estimated at about $67 a month from list prices
when it was resized to e2-standard-2 on 2026-11-19 (not read from the bill; check Billing for the real figure), and Gemini has its
own caps (enrich ₹50/day lane, AI Studio prepaid credit). Both pieces above cost close to nothing extra because they read the
register; the only model call is reading a buyer's words into filters (cheap model, one call per brief). The budget line in
the vision should be read as "no new paid sources", not as the platform's whole cost.

## The vision's targets, kept honest

15 verified agents, 5 buyer-agent matches and ₹10K MRR were pilot targets, not results. The live targets are in
`agent-network.md` (15 signed up by 31 December 2026, 5 active). No MRR target until agents pay for something.

## Step 1 to build: the report

- Backend `areastats.evidence` (code only, no reads of its own, like `pagefacts`): from what `pages` already loaded, a list of
  `{topic, says, source, read_on, level}` lines and a `not_checked` list. Topics: registration, possession date, homes booked,
  builder record, price, pictures, site visit, cautions. Tests pin each line against fixture records, including a project
  with nothing beyond MahaRERA (the report must say what is missing, not hide it).
- Sent with the project view; the site shows it as "Know before you buy" on the project page and in `/check`.
- `docs/plan/seo-system.md` updated in the same commit, since it changes what a project page says.
