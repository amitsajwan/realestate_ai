# Project pages: our own page for every MahaRERA project, before any link to MahaRERA (2026-10-06)

## Why
- Buyers search project names ("Rohan Abhilasha 4 possession"). A page per project on avasetu.in, with the facts and an "Ask about
  this project" form, wins that search and turns it into a lead an agent can call. MahaRERA stays the cited source, linked at the end.
- Marketing (e.g. Gulmohar City, Ranjangaon) must never point at nothing: the page exists first and shows every fact the posts use,
  from the same stored facts, so a corrected fact fixes page and posts together.

## Who owns what (owner, 2026-10-06)
- The project page and its content are Avasetu's: avasetu.in/projects/<slug>. The MahaRERA facts behind it (register, details,
  read dates) are ours and live in one place, the register.
- An agent's listing (House Deal's flat in that project) goes on the agent's own page (/agent/<agent>/...). It uses our RERA facts
  from the register (never its own copy) and links to our project page; our project page lists the agents with homes there.
- Today the shared catalog pages (agentprojects) read MahaRERA themselves; they move to reading the register (follow-up).

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

## Marketed projects sold under several registrations (2026-10-13)
Builders register a big project tower by tower under working names: Lodha Camelot (Upper Kharadi) is "Kharadi New Project -
Tower 1", "- Tower 2"... on MahaRERA, and nothing there says they are one project. The register keeps one record per number.

BUILT (branch work/project-groups, not deployed):
- The link lives on the project record (`agent_projects`, `ProjectIn`): `rera_no` stays the primary registration;
  `registrations: [{regno, tower, holds, maharera_id, completion, checked_at, source}]` lists every number the project is sold
  under (rera_no must be one of them); `candidates: [{regno, tower, maharera_id, why, source}]` are look-alikes (same promoter,
  pincode, naming) no trusted source puts in the project. Records without `registrations` are unchanged.
- Public reads show `registrations`; `candidates` are owner-only (OwnerProject): they never match, never feed chat, are never watched.
- `agentprojects.groups.Groups(db).resolve(regno, name)`: a member number, or the marketed name ("Lodha Camelot", "Camelot
  Kharadi", "Lodha Camelot Tower 11"; the distinctive word alone is not enough) -> {name, builder, promoter, locality, regno, tower,
  registrations, siblings}. Two different groups answering one name -> none. Reads drafts too (matching only, nothing published).
- Wired: propertyfacts `registration.lookup` for campaign runs and brochure kits (the marketed name with no number -> the tower
  it names, else its towers offered to pick; a member number is searched on MahaRERA under its working name); ai_listing brochure
  drafts (member number -> project name and locality from the group; name only -> the towers as one-tap picks); the register
  watch list (every member); chat grounding (all member numbers, brochure travel times); `pune_places.VERIFIED` places Camelot's
  5 numbers in Upper Kharadi (not towers 5, 6, 9).
- Seed: `backend/scripts/lodha_camelot.py` (draft; `--dry-run` prints it).

TARGET (not built):
- Register project pages (`/projects/<slug>` for a register record) and area pages say "part of Lodha Camelot" and link the group.
- The shared catalog and the frontend project page show the registrations and the brochure's travel times (`nearby[].minutes`).
- propertyfacts sheets stay one per registration; a listing named only "Lodha Camelot" keeps its own name-keyed sheet.
- Owner review in Studio: confirm or drop a candidate (today: edit the record and re-run the seed).
