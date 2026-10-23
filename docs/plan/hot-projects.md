# Hot projects: find what buyers are chasing in our areas and work on it first (2026-10-12)

## Why
MahaRERA tells us every project, not which ones matter this month. A new tower launch (Lodha Camelot, Kharadi), a project selling
fast, one in the news or one people suddenly search for is where buyers, agents and Google searches go. Those pages must be the
first ones with fresh facts, and agents should hear about them first.

## What runs (backend/app/modules/areastats/hot.py)
Once a day, inside the enrichment loop, every project in our areas or on the watch list gets `hot_score` (0-100) and
`hot_signals`: each signal with its evidence, source and date, so an agent sees why, and nothing is a number without a source.

| Signal | Source | Needs |
|---|---|---|
| launch | MahaRERA registration date within a year | nothing (register details) |
| bookings | homes booked in 90 days, from the dated `booked_history` the details step now keeps | a few monthly reads |
| news | stories the newsroom linked to the project in 30 days | nothing |
| search | Search Console impressions and growth over the 28 days before (`gsc_history`) | GSC key (already set up) |
| google | place in Google's top 10 for buyers' area searches ("new launch projects in Kharadi Pune"), and how many sites market it (and with ads) | `SERPER_API_KEY` (areastats/websearch.py) |
| youtube | videos naming the project in 30 days, and which channels made them | `YOUTUBE_API_KEY` (official Data API) |

### Google search (areastats/websearch.py)
Google's own web-search API (Custom Search JSON) is closed to new customers and ends on 2027-01-01, so results come from a paid
results provider: Serper.dev today (2,500 free searches, then about $50 per 50,000); another provider is one function.
About 20 searches a day: 8 area searches in turn (3 phrases x 8 areas, a full round every 3 days) and up to 12 searches for the
hottest projects not searched in 7 days. From the results:
- the score: places in area searches' top 10 (a higher place counts more) and distinct sites marketing the project;
- `web_marketers` / `web_advertisers` on the project: who markets it, for agents (`hot.top` gives them as `marketed_by`), never on
  the public page;
- `discovered_projects`: MahaRERA numbers in results that the register lacks, with where they were seen, for the lookup job.
The score is out of a fixed SCALE, so turning a source on or off never moves every other project's score.

Keys (SERPER_API_KEY, YOUTUBE_API_KEY and the others) are set on the VM with `deploy/gcp/keys.ps1`: it shows which keys are set
or empty, checks a new one against its service and writes it only into the VM's private .env.

Hot projects (score >= HOT_MIN) go first in page enrichment, after urgent campaign requests, and are rewritten every 14 days
instead of 60. `hot.top(store, area)` gives the list with reasons, for agents' briefs.

Also fixed: the register refresh step never gave new projects their page slug (a `pages` batch-size argument hid the pages
module), so newly swept projects got no /projects page and were never enriched.

## Hot projects banner on every buyer page (areastats/spotlight.py, 2026-10-22)
A rolling strip of up to 6 project links under the header (`components/site/HotStrip.tsx`, in `MarketingShell`). The owner sets
it in Studio > Admin > Hot projects banner: picked projects first (each optionally for one area's pages only, with a short note
and a last day), then, with "Fill up with hot projects" on, the hottest ones (hot_score >= HOT_MIN), the page's area first.
- Public: `GET /api/v1/public/register/spotlight?area=<slug>`; owner: `GET`/`PUT /api/v1/admin/spotlight` (stored in
  `site_settings`, `_id: spotlight`).
- SEO: plain server-rendered links in an `<aside>` with no heading, so they are internal links Google follows into the hottest
  project pages, adding no headings or text to the page. Only live, indexable, not-finished project pages are shown (a pick that
  is not in search is refused on save), an agent-listed project links its shared page directly (never through the 301), and the
  page's own project is left out. Each entry shows the owner's note or one MahaRERA fact, never a score.
- Never breaks a page: the read has no retries and an empty answer hides the strip. Not on loading screens, legal pages or the
  agents' trial page. robots.txt and the sitemaps are unchanged (`__tests__/marketing/robots-guard.test.ts` keeps every public
  page family open).

## Next (same pattern: one `hot.add_signal(name, fn)` each)
1. Instagram: hashtag search through the Graph API on our business account (30 hashtags a week): reels and posts per project.
2. Done (areastats/discover.py): each register step looks up one `discovered_projects` number on MahaRERA by names taken from
   the result titles that showed it, takes a card only when its number is exactly the one seen, and hands found ones to the
   watch list (source `web_discovered`): the register reads its details, the area rules place it, it gets its page. Numbers no
   name finds stay open for new titles; `discover.pending()` lists them for a person.
3. Marketing partner pages: read a page (found through search or given by an agent), keep its project numbers, agent RERA
   number, claimed prices and offers as labelled claims; a project number we do not have goes to the watch list.
4. Discovery: a project named in news, social or Search Console queries that the register lacks becomes a lookup task, so a
   project like Camelot is added the day people start talking about it.
5. Agent alerts: a weekly WhatsApp brief per agent from `hot.top` for their areas.

## Search demand (areastats/demand.py)
One list of search phrases, `search_demand`, for the page work that answers them:
- from Search Console, daily: the searches that showed our pages (query and page), impressions, clicks, position, and the 28
  days before; a phrase is `rising` at 1.5x the 28 days before (with at least 10 impressions), or when it is new this week;
- from our Google searches, daily and free with them: Google's related searches and "People also ask" questions, and our own
  place in each search's results (`rank`, with a dated history), so "top on Google" is a number we watch;
- each phrase is placed by the rules: `project` (names a register project the way people write it), `area` or `topic`.
`demand.top(store, kind, area, rising_only)` lists them; `scripts/demand_report.py` prints them on the VM (`--missing` lists the
project numbers MahaRERA search did not find). The sitemap now dates a project page by its last change (`pages.updated`: MahaRERA's
date, our details read, our page text), so Google re-reads a page after we improve it.

Next: answers on project and area pages for project and area phrases (automatic, from checked facts only), topic drafts in the
Newsroom (owner approves), rising phrases in agents' briefs; then telling search engines (Search Console sitemap submit,
IndexNow for Bing) and checking that hot pages are indexed (URL Inspection API).

## Rules
Official APIs and public records only; no scraping against a site's terms, no captcha solving. The one exception, chosen by the
owner (2026-10-12): Google results come from a paid results provider, since Google offers no web-search API any more; those
providers collect results from Google themselves, which Google's terms do not allow, so the provider is one replaceable function. Claims from marketers are labelled
as claims. Promoter and competitor details stay in the agent view, not on public pages.
