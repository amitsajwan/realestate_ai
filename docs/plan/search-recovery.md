# Getting back into Google: steadier, fewer, more our own (2026-11-05, PROPOSED)

Owner, 2026-11-05: "Our pages are no where in google search. Are we missing something. Our algo how can we make it best. How
to read what we currently can't." Nothing here is built. Each step waits for the owner's call. Background: docs/plan/seo-system.md
(section 11 is the record of the drop), docs/plan/project-pages.md, docs/plan/enrich-lanes.md.

## Why we are nowhere

The pages are not broken. The change log says so, and in the logged checks every part of the site passed:
- From 2026-10-27, searches where we stood at positions 3 to 6 showed nothing of ours in the top 20, yet the same search with
  "avasetu" added put our page first. The pages are indexed and ranked nowhere.
- The site goes off and on as one: 3,098 impressions (10-26), 116, 84, about 4,000 (10-29 to 10-31), 273 (11-01). On 11-01 every
  page fell within one hour. No noindex of ours can do that, so it is Google's side.
- Search Console shows no manual action and no security issue. Robots.txt, status codes, titles and canonicals all checked
  out when the site was read as Googlebot.

The cause logged at the time: a domain a few weeks old put about 13,000 URLs in its sitemaps, about 500 of them enriched. That
reads as scaled content, and the filter judges the site, not one page. Three things keep feeding it.

1. **Churn.** Since then the sitemap went from about 13,000 to 243 to 343 project pages, pages go in and out of noindex as
   enrichment fills them, texts are rewritten every day (20 pages in search a day, plus night runs of 300 and more), and the
   page template, titles and opening block change every few days. To a classifier that is a site run by a machine and not yet
   settled. The title hold, moved to 2026-12-15 on 2026-11-07 (`seo/actions.HOLD_UNTIL`), is right; it covers titles only.
2. **Little Google does not already have.** A project page is MahaRERA's record (public, and on many sites), facts read from the
   sites that already rank for the project (marketers and portals), and 3 to 5 points a model writes from those. However well
   checked, the web facts are those sites' content in our words, and Google ranks the source. What exists nowhere else is small
   on the page: booking pace over time, completion dates moved, the builder's date record, the project beside its area.
3. **No trust from outside the site.** Almost no links to us, brand searches too rare for Search Console to name (Google answered
   "avasetu" with "Seva Setu" on 10-27), and an About page with no people named yet. A new domain with no one behind it and
   hundreds of like pages is what these filters are built to catch.

Better reading of other sites does not fix any of the three. It comes after.

## What changes

The algorithm's job moves from "read what others say and rewrite it" to "work out what nobody shows, and read the web to check it".

### R1. Stop the churn (BUILT 2026-11-05 except the template hold; tests `tests/modules/areastats/test_search_hold.py`)

- A page in search is rewritten only when one of its facts changes (homes booked, the filed date, a price, a building): the
  fact sheet's facts, not the text, decide. A newer writer version is not a reason. Today `rewrite_due` takes 20 pages a day
  for that alone (`enrich.REWRITES_PER_DAY`), and `REST_DAYS` only spaces it out.
- A page stays in or out of search for at least 30 days once decided, unless it breaks (an error page, a wrong project). Today
  a page goes back in as soon as enrichment fills it (`THIN_RETRY_DAYS`).
- The page template and titles stay as they are until the site is back. Widen the hold (2026-12-15) from titles to templates.
  (Not code: a rule for whoever changes the pages.)
- ~~Sitemap size moves in steps the owner decides, not with each night run. (The hold below slows it; the steps are the owner's.)~~
  DROPPED 2026-11-12 (owner): no cap; a fully enriched page goes into search when it qualifies.

Built:
- `enrich.REWRITES_PER_DAY` is 0: no page in search goes to a newer writer for that alone.
- `enrich.settled`: a page in search with model-written text keeps it while `own_facts_key` of its fact sheet stands, the
  fingerprint of the sheet's lines about the project itself. The area's lines (`area*`), the questions to ask (`ask*`) and the
  builder's record move with other projects and do not count. A page written before the key keeps its text and gets the key,
  so its next change of facts rewrites it. Points code wrote when a draft was refused (`page_text_by` "code") still give way.
  The stored `fact_sheet` stays the one the kept text was written from.
- `pages.searchable` holds a decision `SEARCH_HOLD_DAYS` (30): once a page has been in search it stays in, and once it then
  leaves it stays out, for 30 days from that decision (`search_state` {in, at}, stored by each enrichment round). A page never
  in search has no hold and goes in once ready, so new pages are not held back. A page held in still leaves at once when it
  is finished, offices or shops, not listable, or has no written text (`pages.must_leave`). The sitemap and the page's noindex
  read the same `searchable`, so both hold.
- Cost: a page that left search because a round emptied it by mistake (the 14 pages of the 2026-11-05 night run) waits out
  the 30 days once refilled.

### R2. Fewer pages, each the best on the web for its project (owner's call)

Pick 30 to 50 projects in Kharadi, Upper Kharadi and Wagholi: the Top lists' leaders and the projects buyers search for by name.
Each one gets:
- our own photos from a site visit, dated, which no other site has;
- prices from a call to the sales office, with the date and the size they are for;
- what is good and what is worth worrying about, said plainly and signed "Avasetu team" (owner, 2026-11-06: no personal name), with
  the date and what was checked, so a review never reads as a visit or a call that did not happen;
- the MahaRERA history below (R3).

Every other project page stays out of search (noindex, out of the sitemap) until it reaches that level. The area lists keep
showing every project as they do today. Fifty strong pages that hold still lift the site faster than 343 thin ones that move.

### R3. Lead with what only we have (code)

- Booking pace as a dated chart from `booked_history`, filed completion dates from `completion_history`, price readings from
  `prices.history`. MahaRERA and the portals show only today's figure; our history grows every month we keep reading.
- MahaRERA's construction progress (R5 below): "Tower A: 60% to 72% this quarter" is the line no portal prints.
- Web facts become checks on MahaRERA, not content: "marketer sites say 2,792 homes; the registrations filed so far add up to
  1,400" tells a buyer something; "2,792 homes" in our words does not.
- "Updated <date>" on every page, moving only when a fact moved (as `page_text_at` already does for the text).

### R4. Trust from outside the site (owner; not code)

- Google Business Profile for Avasetu.
- The About page says who stands behind the site as the Avasetu team (owner, 2026-11-06: no personal names, on the About page or on
  reviews). BUILT 2026-11-13: the team is House Deal (owner), with its office, phone, email and MahaRERA agent number on `/contact`,
  About and the footer.
- Monthly data stories pitched to Pune press and blogs ("Kharadi bookings, November 2026", from the MahaRERA tracker), each
  linking to its area's page.
- Links from House Deal and partner agents' sites to the projects they sell.
- Posts that send people to search "Avasetu", so brand searches become a figure Search Console can name.

## Reading what we cannot read today (code, after R1)

Best value first.

### R5. MahaRERA's own documents

We read the general record and the wing table (`agentprojects/maharera.py`), not the files filed with them: the quarterly
progress reports (construction % per building, signed by the architect, the engineer and the CA), the commencement certificate
and the sanctioned plans. They are the builder's word under law, they are dated, and almost no site reads them. Read the document
list on the project's MahaRERA page, download each new PDF once, extract its text (scanned ones through OCR), and keep the
progress per building and quarter on the record. The same rule as everything else: a figure counts only with the line it came
from, and code reads every number.

### R6. Builder sites built in the browser

Only 69 of 277 projects read their builder's site (2026-11-04), and that is the one source a fact needs alone. Many builder sites
send almost no text in their HTML. In this order, cheapest first:
1. structured data already in the HTML: JSON-LD (the Rathi page of Godrej Ivara has a `FAQPage` with towers, homes and floors),
   `__NEXT_DATA__` and other embedded state, `og:` and meta tags;
2. the JSON address the page itself calls, often a plain GET;
3. headless Chromium, only for the builder's own domain, only when 1 and 2 found nothing, about once a month per project.

### R7. Brochures and floor plans

Builder pages often link the brochure PDF directly even behind a form. Follow those links on the builder's own pages and reuse
`propertyfacts/brochure_parse.py`. Floor-plan images go to a vision model under the same rule: it quotes what it sees, and code
checks the number against the quote.

### R8. What the reader dropped (BUILT 2026-11-05; checked on the Rathi page of Godrej Ivara)

All in `areastats/webfacts.py`, and the highlights reader (`profile.relevant`, `profile.agree`) takes the same lines and rule.
Tests: `tests/modules/areastats/test_webfacts_reading.py`.
- Long blocks: `relevant` skipped any line over 600 characters, and on that page a 3,005-character block held "span 14 acres and
  rise in 11 towers". `fact_lines` now cuts such a block into its sentences ("Inc. of Taxes" is not a sentence's end).
- Labels: a short label line and the short value under it ("Land Area", "14 Acres"; a table row's cells; a fact strip's boxes)
  are read as one line. The quote stays on the page, since only spaces join them.
- Other projects: after a line printing another MahaRERA number, or a card heading ("Godrej Elaris Mundhwa, Pune": three or more
  words besides the place), lines are left out until one names the project or prints its number. On that page the comparison
  table and the carousel (Elaris, Aqua Vista, Kumar Prajwal: 12, 7 and 0.38 acres; 1,030, 1,532 and 47 homes) no longer reach
  the model, and every Ivara fact still does.
- robots.txt: the readers' default is `read_page`, which reads only what a site's robots.txt allows AvasetuBot (RFC 9309: no
  file or another 4xx allows all, a server error or no answer allows none, read again after an hour), with 2 seconds between
  two reads of one site, also across the areas the batch runs at once. A builder whose robots.txt shuts out every bot is no
  longer read; that is theirs to decide. `fetch_page` stays the plain read under it.
- Copies: two sites agreeing count as two sources only in their own words: a quote of 40 characters or more inside the other
  site's quote is one source (`copied`, `sources_in`). Short quotes ("Land Area 14 Acres") still count apart.
- Not done: widening `MARKETER_WORDS` to "for general informational purposes only". It only matters for pictures on a domain with
  the builder's name, and builders' own disclaimers use the same words, so it would cost real builder sites their pictures.

The first round after this asks the model again for every page (the lines it is given changed, so the kept answers do not
match): one pass of the budget.

### Not doing

- Working round portals that refuse our reader (99acres, Housing): they refuse on purpose, and their content is not ours to take.
- Taking facts from Google's snippets: a snippet only says which page to read.

## Order

R1 first (it costs nothing and every other step needs a settled site), R8 alongside it (small, with tests), then R3 and R5, then
R6 and R7. R2 and R4 run in parallel and are the owner's. Judge it in Search Console 28 days after R1 is live: impressions on the
R2 pages and brand searches, not the whole site's total.
