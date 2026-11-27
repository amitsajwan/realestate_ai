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

## Money and the ₹5,000/month budget

The vision's ₹5,000 a month is already below what runs: the VM alone is about $67 a month (2026-11-19), and Gemini has its
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
