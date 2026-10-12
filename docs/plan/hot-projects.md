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
| youtube | videos naming the project in 30 days, and which channels made them | `YOUTUBE_API_KEY` (official Data API) |

Hot projects (score >= HOT_MIN) go first in page enrichment, after urgent campaign requests, and are rewritten every 14 days
instead of 60. `hot.top(store, area)` gives the list with reasons, for agents' briefs.

Also fixed: the register refresh step never gave new projects their page slug (a `pages` batch-size argument hid the pages
module), so newly swept projects got no /projects page and were never enriched.

## Next (same pattern: one `hot.add_signal(name, fn)` each)
1. Instagram: hashtag search through the Graph API on our business account (30 hashtags a week): reels and posts per project.
2. Marketing partner pages: read a page (found through search or given by an agent), keep its project numbers, agent RERA
   number, claimed prices and offers as labelled claims; a project number we do not have goes to the watch list.
3. Discovery: a project named in news, social or Search Console queries that the register lacks becomes a lookup task, so a
   project like Camelot is added the day people start talking about it.
4. Agent alerts: a weekly WhatsApp brief per agent from `hot.top` for their areas.

## Rules
Official APIs and public records only; no scraping against a site's terms, no captcha solving. Claims from marketers are labelled
as claims. Promoter and competitor details stay in the agent view, not on public pages.
