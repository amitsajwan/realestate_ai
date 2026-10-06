# Project pages: our own page for every MahaRERA project, before any link to MahaRERA (2026-10-06)

## Why
- Buyers search project names ("Rohan Abhilasha 4 possession"). A page per project on avasetu.in, with the facts and an "Ask about
  this project" form, wins that search and turns it into a lead an agent can call. MahaRERA stays the cited source, linked at the end.
- Marketing (e.g. Gulmohar City, Ranjangaon) must never point at nothing: the page exists first and shows every fact the posts use,
  from the same stored facts, so a corrected fact fixes page and posts together.

## Rules
- Facts only, each with source and read date. The paragraph is written by code from the facts (no model, no adjectives, no prices
  unless a labelled source gives one). MahaRERA dates are "filed", "listed or updated"; never "newly registered".
- A page is listed for Google (sitemap, index) only when it has enough real facts: filed completion date AND homes booked/total.
  Thinner pages exist (links work) but carry `noindex` until their details arrive. No thin template pages in the index.
- The slug never changes once given (stored on the register record as `page_slug`); collisions get a short registration-number suffix.
- Projects outside our 8 areas (watched ones) get pages too, listed under no area.

## Streams
| Owner | Part |
|---|---|
| realestate-ai-f6 | Register project pages: slug, public API, `/projects/<slug>` page for register projects, area pages / news / replies link to our page first, sitemap. |
| property-facts owner (realestate-ai-0a / -37) | Page first for campaigns: a campaign for a property needs its page; the page shows the property's usable facts (prices, sizes...) labelled with their source. |

## Contract
Python (any module, read-only):
- `app.modules.areastats.pages.page_for(db, regno) -> Optional[dict]`: `{"slug", "path": "/projects/<slug>", "url", "indexable": bool}`
  for a project in the register (in our areas or watched); None when the register does not have it. To get a page for a project the
  register does not have yet, add it to the watch list first (`areastats.watch`, needs its MahaRERA id); the page exists at once.

HTTP (public, no auth):
- `GET /api/v1/public/register/projects/{slug}` -> the page data: name, regno, promoter, area {key, slug, name} | null, pincode,
  completion_now, completion_at_registration, units_total, units_booked, details_read_at, listed_or_updated, maharera_url,
  paragraph, indexable, same_area (up to 6 other projects in the area: name, slug, completion_now). 404 when unknown.
- `GET /api/v1/public/register/by-regno/{regno}` -> `{"slug", "path", "indexable"}` or 404.
- `GET /api/v1/public/register/projects?area=<key>&limit=` -> list for area pages and the sitemap (indexable ones by default).

Frontend:
- `/projects/<slug>`: today it serves the shared agent project pages (agentprojects catalog). It keeps doing that when the slug is a
  catalog project; otherwise it renders the register page. A catalog project that is also in the register keeps its catalog page.
- Property facts block (property-facts owner): the page asks `GET /api/v1/public/property-facts/by-regno/{regno}` (to be provided by
  the property-facts owner) and, when it returns usable facts, shows them as "From the agent's sheet" with each fact's source.
