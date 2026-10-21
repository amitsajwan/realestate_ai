# SEO system: what runs, what the owner does, what to build next (2026-10-21)

The one map of our SEO. Details live in the plans it links: [rank-loop.md](rank-loop.md), [index-everything.md](index-everything.md),
[area-intent-pages.md](area-intent-pages.md), [insights-and-seo.md](insights-and-seo.md), [seo-review.md](seo-review.md).
Labels: **LIVE** = running in production, **TARGET** = to build.

## 1. Where we are (measured on production 2026-10-21)

| | |
|---|---|
| Pages in the sitemap | 11,027 (index of 99 sitemaps: core, agents, builders, one per Pune place) |
| Inspected by our coverage loop | 1,050 so far: 337 indexed, 480 "Discovered - not indexed", 185 unknown to Google, 38 noindex, 8 5xx (old) |
| Search Console, last 28 days | 5,022 impressions, 92 clicks on project pages; 694 project pages seen; 36 pages near page one (position 8-20) |
| Pages with a target search | 71 (24 titles changed); 83 fixes logged since 2026-10-14, first 14-day results due 2026-10-28 |
| Google searches we ran (Serper) | 261 stored; we show in 45; above MagicBricks in 23 (scoreboard, section 3) |
| Area list pages grown from searches | 28 live, 210 waiting on their gates |

**Indexing is the bottleneck**, not page quality: Google spends little crawl on a new domain with 11k URLs. The levers are
outside links, visits from our posts, and every page Google reads being worth indexing (thin pages stay noindex).

## 2. The Search Console key (the "token")

A Google service account the owner added in Search Console as a **Restricted (read-only)** user. Its key is only in the VM's
`.env` as `GSC_SA_KEY_B64` (base64 key file), never in git or chat; the property is `sc-domain:avasetu.in` (`GSC_SITE`). It is
set and working (read daily, last 2026-10-20 14:11 UTC). With read-only access it can:

- read clicks, impressions and positions per page and per search (Search Analytics API), and
- inspect any URL's index state (URL Inspection API, 2,000 a day).

It cannot submit sitemaps or request indexing: those need a Full user, and Google's Indexing API is only for job posts and
livestreams. So "Request indexing" and sitemap resubmits stay with the owner (section 4).

## 3. What runs by itself (LIVE)

All in the `newsroom` worker role unless noted. One `pipeline=seo step=<name> outcome=…` log line per step per round.

| Job | When | What it does | Code |
|---|---|---|---|
| Sitemap | rebuilt every 10 min | index + 99 child sitemaps; a page's date moves only on a real change; noindex pages are left out | `frontend/lib/site/sitemap.ts` |
| IndexNow | every 30 min | sends changed pages to Bing, Yandex and the engines that read Bing (121 sent today) | `seo/indexnow.py` |
| Search Console read | daily | per-page and per-search numbers onto the project records and `search_demand`; marks pages near page one | `areastats/searchconsole.py` |
| Index coverage | daily | URL Inspection of 1,800 pages (was 200 until 2026-10-21), never-checked first, so all 11k are covered in about a week; a stale sitemap after a deploy is skipped, not counted | `seo/coverage.py` |
| Target searches + titles | daily | one target search per page from Search Console; the title takes it when every word is the project's own | `seo/targets.py` |
| Page doctor | daily, at most 15 pages | one fix per page per 28 days (title, buyer questions, link slot, refresh facts, description), measured at 14 and 28 days, undone if it lost | `seo/doctor.py`, `seo/actions.py` |
| Google searches | daily, ~20 | area and project searches through Serper: who ranks, related searches, "People also ask", new MahaRERA numbers | `areastats/websearch.py` |
| Search gaps | weekly | searches that show us with no page in the top 20 | `seo/gaps.py` |
| Area list pages grow | weekly, at most 10 new | new-launches / top / ready-to-move pages per place, made from real searches once they pass demand, supply and overlap checks | `seo/grow.py`, `seo/facets.py` |
| MagicBricks scoreboard | weekly (new 2026-10-21) | for every stored search: our place, MagicBricks', 99acres', Housing's; count above MagicBricks, the searches to win next, history per week | `seo/scoreboard.py` |
| Page writer | every 5 min (cheap rewrite), full re-read at most 1 per 30 min | summary + sections + search line on project pages, free LLM tiers | `areastats/enrich.py` |
| Hot projects refresh | every 14 days per hot project | facts and page text re-read for the projects buyers look at | `areastats/hot.py` |
| Owner's SEO note | weekly (new 2026-10-21) | one Studio notification on Home ("Needs you now"): clicks, impressions, page one, indexed, above MagicBricks, each beside last week; opens Insights → Rankings, which lists the not-indexed pages most worth a Request indexing (list/guide pages, then hot, then seen) | `seo/note.py` |
| Site audit | weekly, Mondays 08:47 IST (GitHub Actions) | reads 300 sitemap pages like Googlebot: status, noindex, canonical, title, JSON-LD; a 5xx is read again after 30 s, so a restart during the run is a warning, not a failure (new 2026-10-21) | `seo/audit.py`, `.github/workflows/seo-audit.yml` |

Owner sees all of it in Studio → Newsroom → Insights (Rankings: week numbers, MagicBricks scoreboard, doctor results, fixes with
Undo, targets, conflicts, gaps; Pages: area list pages; System: loop health and Serper credits).

## 4. What the owner does by hand (no API allows it)

- **Search Console → URL Inspection → Request indexing, about 10 a day**, from the list on Insights → Rankings ("Ask Google to
  index": list and guide pages first, then hot projects, then pages already seen). This is the only way to jump the crawl queue.
- After a big deploy that adds page types: resubmit `/sitemap.xml` (Sitemaps report).
- **Outside links** (the biggest lever for a new domain): Google Business Profile for Avasetu; listings on Pune property
  directories; agents' own sites linking to their project pages; the MahaRERA tracker page offered to journalists/bloggers.
- Instagram website + WhatsApp button set (project_instagram_to_lead), so post visits reach the pages.

## 5. What to build next (TARGET, in order)

1. **Weekly SEO note on WhatsApp/email too.** LIVE in Studio only (`seo/note.py`); there is no email sender, and WhatsApp
   to the owner outside 24 hours needs an approved template. `report.week_lines` (unused) can then be removed or reused.
2. **Crawl push for "Discovered - not indexed" pages.** 480 known pages wait for a crawl. Put the fullest of them (summary,
   dates, nearby) in the link slots of pages Google crawls most (indexed, high impressions: the 8 place pages, Wakad guide),
   rotating weekly, and let coverage measure how many get indexed in 14 days. Today link slots only go to pages that already
   have impressions.
3. **Doctor fix "beat MagicBricks"** (I6 second half): for a "win next" search, compare what MagicBricks' result shows in its
   title/snippet (price, BHK, possession) with ours and add the fact we hold that they don't. Never copy their text.
4. **Coverage per area** on Insights: indexed share per child sitemap (from `seo_index`), so the lagging area gets the
   Request-indexing turns and the crawl push first.
5. **Scoreboard covers every target search**: the Serper turn spends ~6 searches a day on target checks; give pages with a
   target and MagicBricks near them a turn every 14 days so the scoreboard is a fixed panel, not whatever was searched.

## 6. Rules

- No page is dropped to make numbers look better; thin pages are noindex and out of the sitemap until they hold a real fact.
- One fix per page per 28 days, measured; a fix that lost is undone and never applied again.
- No Indexing API, no copying of portal text, no paid links.
- Marketer sites and scores never appear on public pages.
