# Project enrichment: facts often, the model by budget (2026-10-25, BUILT)

Owner, 2026-10-25: "we want no-LLM calls to be very frequent, and the LLM we will run as per LLM cost effectiveness", then
"50 rs per day is fine" on Gemini. Code: `areastats/enrich.py` (the rounds), `areastats/budget.py` (the model budget),
`platform/llm.py` (`USAGE`, `gemini_llm`, `free_llm`). Background: docs/plan/project-pages.md.

## Why

Before, one round did everything for one project every 30 minutes (about 48 a day): MahaRERA's record and buildings, the facts
gatherer, the place check, then the web facts, profile and prices (one model call per page each, up to 4 pages), then the page
text. So:
- work that needs no model waited on the model's pace: our ~1,180 projects took about 25 days for one pass;
- without a key the pictures were lost too (`profile.gather` stopped before `pictures()`, which is all code), and "no LLM key"
  counted as a service failure, so those projects came back every day and MahaRERA was read again for nothing;
- the model was asked again every round even when the page or the facts it read had not changed;
- MahaRERA's general record was read twice: by the register's refresh (every 30 days) and by the round.

## What runs now

**Facts round, every 5 minutes** (`PROJECT_ENRICH_EVERY_MINUTES`, about 288 a day: our areas in about 4 days), in the same
order as before (urgent, hot, Google-shown, our areas outward from Kharadi, new launches first). No model needed:
- MahaRERA's general record: the register's own read is used while under 30 days old (`DETAILS_FRESH_DAYS`); the
  buildings are read again after 30 days (`BUILDINGS_FRESH_DAYS`). A campaign's urgent request always reads both fresh.
- the facts gatherer and the place check, as before. Refresh stays every 60 days (14 for hot projects): each gathering asks
  Google Places for what is nearby (8 calls, not cached), so a faster pace does not mean more rounds per project.
- the pictures (builder's site, brochure, other sites, illustrations): run with or without a model.
- the model steps run in the same round when the budget has room for the project; otherwise they are **put off**: the last
  results stay, the round notes "reading put off (...)" and sets `reading_due`. Nothing counts as failed.

**Reading round, every 10 minutes** (`PROJECT_READ_EVERY_MINUTES`): one project with `reading_due`, premium first (hot, then
Google's impressions, then our areas outward from Kharadi), when the budget has room. It reads the web pages, highlights and
prices and writes the text from the facts the facts round kept (`configure(view=...)`, no gathering again). A reading round
that crashes is not retried within 6 hours.

**The price round** (`areastats/pricing.py`, every 15 minutes) uses the same budget; a read put off is not recorded as tried.

## The model budget (`areastats/budget.py`)

- **No change, no call.** Every answer is kept in `enrich_answers` under the hash of the exact question (prompt + page lines or
  facts). The same question again (an unchanged page, unchanged facts) is answered from there. A page text that fails its
  checks is forgotten, so the next round asks again. Answers not used for 120 days are pruned daily.
- **Gemini, at most Rs 50 a day** (`ENRICH_GEMINI_INR_PER_DAY`, India's day). Each answer's tokens come back through
  `platform.llm.USAGE` (thinking counted as output, as Gemini bills it) and are priced per model at `USD_INR`. An unlisted
  Gemini model is priced high, so an alias moving to a dearer model cannot overspend. Half the rupees are kept for premium
  work; the rest may use Gemini only up to the other half.
- **Free tiers, at most 400 calls a day** (`ENRICH_FREE_CALLS_PER_DAY`), and none while most of them are resting.
- **Who gets what** (`budget.route`):

  | Project | Page reads (facts, highlights) | Prices | Page text |
  |---|---|---|---|
  | Urgent (a campaign about to post) | Gemini, then free | Gemini, then free | Gemini, then free |
  | Premium (hot, shown by Google, Upper Kharadi / Kharadi / Wagholi) | free, then Gemini Lite | Gemini, then free | Gemini, then free |
  | The rest | free, then Gemini Lite | Gemini Lite, then free | free, then Gemini Lite |

What Rs 50 buys (list prices on 2026-10-25; the meter has the real numbers after a few days): a page read is about 3,300
tokens in and 1,600 out, the text about 3,500 in and 1,900 out. On Gemini 3 Flash ($0.50 in, $3.00 out per 1M) that is about
Rs 0.55 a page and Rs 0.65 a text: about 85 calls a day; on Flash-Lite about twice that. Projects whose pages did not change
cost nothing, so most of it goes to new and changed pages.

**Owner's view.** `GET` Studio > Newsroom > Project pages (`status_list`) now also returns `budget` (today's rupees and calls
against the caps, answers served from the kept ones, questions put off, per step), `reading_waiting` (projects waiting for
the model) and per project `reading_due` / `read_at`. Chat and the creative room use the same Gemini key and are not counted
by this meter: a budget alert on the key in Google Cloud stays the real guard on the bill.

## Data

- `projects` (the register): new fields `reading_due`, `read_at`, `read_failed_at`; written through `Store.set_project` as before.
- `enrich_answers` (areastats): {_id: question hash, answer, step, at, used_at}.
- `enrich_llm_usage` (areastats): {_id: India's day, gemini_inr, gemini_calls, free_calls, cached, deferred, tokens_in,
  tokens_out, steps.<step>}.

## Not built (yet)

- **One model call per page** for facts, highlights and prices together (about 5 calls a project instead of about 13). It
  changes three prompts at once, so it needs a side-by-side run on ~30 real projects first.
- **A rule-only price reader** for a line with one BHK size and one amount; measure on real pages how many projects it
  prices alone before building it.
- The Studio screen shows the new `budget` numbers only once the frontend reads them; the API returns them already.
