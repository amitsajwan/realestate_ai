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

## Next (same pattern: one `hot.add_signal(name, fn)` each)
1. Instagram: hashtag search through the Graph API on our business account (30 hashtags a week): reels and posts per project.
2. Look up `discovered_projects` on MahaRERA and add real ones to the watch list (the Lodha Camelot case).
3. Marketing partner pages: read a page (found through search or given by an agent), keep its project numbers, agent RERA
   number, claimed prices and offers as labelled claims; a project number we do not have goes to the watch list.
4. Discovery: a project named in news, social or Search Console queries that the register lacks becomes a lookup task, so a
   project like Camelot is added the day people start talking about it.
5. Agent alerts: a weekly WhatsApp brief per agent from `hot.top` for their areas.

## Rules
Official APIs and public records only; no scraping against a site's terms, no captcha solving. The one exception, chosen by the
owner (2026-10-12): Google results come from a paid results provider, since Google offers no web-search API any more; those
providers collect results from Google themselves, which Google's terms do not allow, so the provider is one replaceable function. Claims from marketers are labelled
as claims. Promoter and competitor details stay in the agent view, not on public pages.
