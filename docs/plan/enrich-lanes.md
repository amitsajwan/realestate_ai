# Project enrichment in two lanes: facts often, the model when it pays (2026-10-25, PLAN)

Owner, 2026-10-25: "we want no-LLM calls to be very frequent, and the LLM we will run as per LLM cost effectiveness."
This plan splits `areastats/enrich.py` (docs/plan/project-pages.md) into a facts lane that never calls a model and a reading
lane that calls one only when the answer is new and worth it. Nothing here is built yet; the steps at the end say in what order.

## Why

Today one round does everything for one project, one project every 30 minutes (`EVERY_MINUTES`, about 48 a day):
MahaRERA's record and buildings, the facts gatherer, the place check, then the web facts, profile and prices (one model call
per page each, up to 4 pages: about 12 calls), then the page text (1 call). So:
- Work that needs no model waits on the model's pace. Our ~1,180 projects in our areas take about 25 days for one pass.
- Without a key the code-only work is lost too: `profile.gather` returns "no LLM key" before `pictures()`, which is all code.
  A missing key counts as "the service did not answer" (`enrich.unanswered`), so those projects come back every day and
  MahaRERA is read again for nothing.
- The model is asked again every round even when the page it reads has not changed since the last answer.
- The same page goes to the model three times (facts, highlights, prices).
- MahaRERA's general record is read twice: by the register's details step (`areastats/refresh.py`, every 30 days) and by
  the enrichment round.

## The shape

```
            facts lane (no model)                         reading lane (model, by budget)
  every FACTS_EVERY (5 min), one project          when the budget and the providers have room,
  ------------------------------------------       the most valuable due work item first
  register record (refresh's copy if fresh)        -----------------------------------------
  buildings/wings (MahaRERA, PAUSE apart)          read_page(url)   one call per changed page:
  facts gatherer (place, nearby, numbers)    --->                   facts + highlights + price rows
  place check (NEAR_KM)                     kept    write_text(project)  one call when the facts
  Google results (Serper, quota)            pages                   the text uses have changed
  fetch pages -> cut lines -> hash          + hashes
  pictures (builder, brochure, web, FLUX)
  code paragraph, code price lines
```

The facts lane leaves everything the model would need on disk with a hash. The reading lane only looks at hashes: a page
whose cut text has the hash it was last read with costs nothing.

## Facts lane (no model)

A new loop `project_facts` (areastats), one project every `FACTS_EVERY` (env `PROJECT_FACTS_EVERY_MINUTES`, default 5,
about 288 a day: our areas in about 4 days). Its order is today's `enrich.priority` (urgent, hot, Google-shown, our areas
outward from Kharadi, new launches first; finished and nearly sold projects last).
For one project:
1. **Register record.** Use the copy `refresh.details` keeps when it is under `DETAILS_MAX_AGE_DAYS`; read MahaRERA only when
   it is older or missing. Buildings/wings are read here (refresh does not), `PAUSE` after any MahaRERA read.
2. **Facts gatherer** (`propertyfacts.enrich.gather_project` through wiring, unchanged) and the **place check**.
3. **Google results** (`webfacts.results_for`): unchanged, stored once, Serper's daily cap applies.
4. **Pages.** Each source page is fetched (`webfacts.fetch_page`), checked to be about the project (`about_project`), cut to
   its useful lines (`relevant`) and kept in `project_web_pages` with a hash of the cut text. A page is fetched again after
   `PAGE_REFRESH_DAYS` (14 for hot projects, 30 otherwise). The price lines are marked by code (Rs / lakh / crore), as now.
5. **Pictures** (`profile.pictures`, the brochure, other sites' pictures, FLUX illustrations as the last resort): moved out
   of the model step, so they run with no key. They are taken from the raw HTML right after the fetch in 4 (`pictures` needs
   the raw page, the store keeps only the cut text).
6. **Code paragraph** (`pages.paragraph`) is always current; the page shows it until a checked model text exists.
7. **Inputs hash.** A hash of what the text writer would be given (`facts_text` without the model's own parts) is stored as
   `text_inputs_hash`. The reading lane compares it with the hash the current text was written from.

Score: `enrichment.facts` = {maharera_general, buildings, places, pages, pictures}, each {ok, at, checked}. A failed source
is a failed step of this lane only; a missing model key never touches it.

## Reading lane (the model, by cost)

The existing `project_enrich` loop becomes this lane. It does no fetching: it reads `project_web_pages` and the register.

**Work items**, worked out on each turn from stored state (no separate queue to drift):
- `read_page(project, url)` is due when the page's hash differs from the hash it was last read with
  (`web_reads.<url>.hash`), or a reading step's version was raised (`enrich.VERSIONS`).
- `write_text(project)` is due when `text_inputs_hash` differs from `page_text_inputs_hash`, the writer's version
  (`TEXT_VERSION`) was raised, or the text is older than `REFRESH_DAYS` and the project is hot.

**One call per page.** One prompt returns the page's facts (`webfacts.KEYS`), highlights (`profile.TOPICS`) and price rows,
each with its quote. The existing checks run on each part unchanged: quote on the page, every number read by code from the
quote, the agreement rules between sites, the sales-word and price plausibility checks. A page with no price lines is not
asked for prices. This takes a full project from about 13 calls to about 5 (4 pages + the text), and a project whose pages
did not change to 0 or 1.

**Which model.** Extraction (`read_page`) goes to the cheapest provider that does it well enough (Groq / Cloudflare /
GitHub Models through `default_llm`). The text writer stays on `default_llm`. Prices today go to Gemini first
(`prices._model`); in the merged call that preference is kept only when the page has price lines. Whether the cheaper
models read prices well enough is measured before the switch (step 6 below).

**Budget.** Owner, 2026-10-25: "we can spend 20 rs per day on Gemini" (for enrichment). Two pools:
- **Gemini, paid: ₹20 a day** (`ENRICH_GEMINI_INR_PER_DAY=20`). Each Gemini answer's `usage` (prompt, completion and
  thinking tokens; Gemini bills its thinking as output) is priced from a table in the module's config (per model, USD per
  1M tokens in and out, and `USD_INR`) and added to `enrich_llm_usage`. When today's rupees reach the cap, Gemini is not
  asked again until midnight IST; the work goes to the free pool or waits. The meter counts only enrichment's calls: chat
  and the creative room share the same key, so a Google Cloud budget alert on the key stays the real guard on the bill.
- **Free tiers** (Groq, GitHub Models, Cloudflare, SambaNova through `default_llm`, Gemini left out):
  `ENRICH_FREE_CALLS_PER_DAY`, set from those tiers' daily limits with room left for chat, the newsroom and campaigns,
  which come first; and only while `enrich.busy(llm)` is false.

What ₹20 buys (estimates from list prices on 2026-10-25, to be replaced by the meter's real numbers after a week): a page
read is about 3,300 tokens in (9,000 characters of page and the prompt) and 1,600 out (the JSON and low-effort thinking);
the text about 3,500 in and 1,900 out. On Gemini 3 Flash ($0.50 in, $3.00 out per 1M) that is about ₹0.55 a page and ₹0.65
a text: **about 35 calls a day**, roughly 6 full projects. On Flash-Lite ($0.25 / $1.50) about twice that. So Gemini is the
quality pool, not the bulk one. It is spent, in this order, on:
1. urgent requests (a campaign about to post): its pages and its text;
2. price pages (lines with Rs / lakh / crore) of hot projects and of Upper Kharadi, Kharadi and Wagholi, where a wrong price
   costs most;
3. the text of hot projects and of pages Google shows;
4. whatever is left by evening: the next items in value order, on Flash-Lite.
Everything else goes to the free pool. When the free pool is resting and Gemini's rupees are spent, the lane waits.
Within the budget the most valuable items go first: urgent (a campaign about to post), hot, pages Google shows (Search
Console impressions), new launches, then the rest; `read_page` of a project before its `write_text`, so the text is
written once from all its pages. A project whose items are all done costs nothing until a hash changes.

**Without a key** the lane simply does nothing: no failure is written, no project is retried, and the pages show the
facts lane's work (facts, pictures, code paragraph, code-read prices where the rule-only reader finds them, see below).

## Owner's view

Studio > Newsroom > Project pages shows the two lanes apart: facts (n/5, when) and reading (pages read / pages kept, text
written from the current facts or not), and today's model calls against the budget. `status_list` gains the reading
backlog: how many pages and texts are due, so the owner can see what a bigger budget would buy.

## Data and ownership

- `projects` (the register): the enrichment fields stay where they are (`enrichment`, `web_facts`, `profile`, `prices`,
  `page_text`...). New: `enrichment.facts`, `text_inputs_hash`, `page_text_inputs_hash`, `web_reads`. Written only through
  `newsroom.store.Store.set_project`, as today.
- `project_web_pages` (new, areastats): {_id: url, regno, site, official, cut text, hash, price_lines, fetched_at, why}.
  Written by the facts lane only; pruned when a project has not used the page for 90 days.
- `enrich_llm_usage` (new, areastats): written by the reading lane only.
- ARCHITECTURE §4 gets both new collections under areastats.

## Steps (each its own PR; moves separate from fixes)

1. **Pictures without a key (fix).** In `profile.gather`, move the `llm is None` check below the pictures; a test that a
   project with no key still gets the builder's pictures (fails today). Small, independent, worth doing first.
2. **"No LLM key" is not a service failure (fix).** Drop it from `enrich._UNANSWERED` so those projects wait
   `REFRESH_DAYS`, with a test.
3. **Pin today's round with tests** (`tests/modules/areastats/test_enrich.py`) for what each step stores, then **move**
   steps 0, 1 and the place check into `areastats/facts.py` with no change of behaviour; `enrich_one` calls it.
4. **Page store.** `project_web_pages` with the cut text and hash; the round reads from it (fetching when missing or old).
5. **Facts loop.** `project_facts` in the worker's newsroom role (`add-background-loop` skill: lease, heartbeat,
   `expected_intervals`, health check), refresh's register record reused; the enrich round stops doing those steps.
6. **Hashes and the budget.** `web_reads` / `text_inputs_hash`, the usage meter (tokens from each answer's `usage`,
   priced per model), the two pools (`ENRICH_GEMINI_INR_PER_DAY`, `ENRICH_FREE_CALLS_PER_DAY`), value order. From here an
   unchanged project costs no call and Gemini never passes ₹20 a day for enrichment. The gateway (`platform/llm.py`) has
   to hand back the answer's `usage` for this; today it returns only the JSON.
7. **One call per page.** Built behind a switch (`ENRICH_ONE_CALL_PER_PAGE`), run on a sample of 30 projects next to the
   three separate calls, compared fact by fact and price by price; switched on only when it is as good.
8. **Rule-only price reader (optional).** A line naming one BHK size and one amount is read by code without the model;
   measured on the kept pages first (how many projects it prices alone).

## Open for the owner

- Gemini: ₹20 a day, decided 2026-10-25. Still open: the free pool's daily calls (`ENRICH_FREE_CALLS_PER_DAY`), given
  what chat and campaigns use.
- The facts lane's pace: 5 minutes is gentle for MahaRERA (2 reads per project at most, usually 1); faster is possible.
- Whether prices may come from the same (cheaper) model as the facts once step 7's comparison is in.
