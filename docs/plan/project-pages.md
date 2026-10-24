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

BUILT (branch work/group-pages, not deployed; LIVE once deployed is the owner's call):
- Public reads (`/public/agents/{agent}/projects[/{slug}]`, `/public/projects[/{slug}]`) carry `registrations` as
  `PublicRegistration` {regno, tower, holds, maharera_id, completion, checked_at, source, url}; `url` is the MahaRERA view link
  built from maharera_id like `rera.url` ('' without one). Never `candidates` or `issues`. One-registration records: `[]`, page as
  before. `nearby[].minutes` is public (it was already in the model).
- Agent project page and `/projects/<slug>` (shared `ProjectDetails`): a "MahaRERA registrations" block (`RegistrationsBox`, only
  with 2+ registrations): per tower, what it holds, the number linked to MahaRERA, "Completion filed with MahaRERA: Jul 2030";
  the MahaRERA box names its tower ("PR1260002501386 (Tower 1)") and "When could you move in?" says whose date it is. Nearby shows
  minutes ("Podar International School · 1 min") with "Travel times as per the builder; not measured by us".
  JSON-LD `ApartmentComplex.identifier`: one PropertyValue per registration (only with 2+).
- Register project pages: `GET /public/register/projects/{slug}` has `group` {name, tower, towers, path} from
  `agentprojects.groups.public_group(db, regno)` -- only when the group's record is `live` on a public agent page and has 2+
  registrations (drafts never show). `path` is `/projects/<slug>` when the shared catalog carries it (indexable agent and a MahaRERA
  reading), else `/agent/<agent>/projects/<slug>`. The page's hero says "Sold as Lodha Camelot (Tower 11) -- see all 5 towers";
  JSON-LD adds `containedInPlace` (the group). The primary registration's register page still redirects to the catalog page when
  an agent lists it.

TARGET (not built):
- Area pages say "part of Lodha Camelot" and link the group.
- propertyfacts sheets stay one per registration; a listing named only "Lodha Camelot" keeps its own name-keyed sheet.
- Owner review in Studio: confirm or drop a candidate (today: edit the record and re-run the seed).

## From the web (2026-10-14, LIVE)

Owner, 2026-10-14: Google's AI answer shows more about a project than our page, so pages also use the web, checked.
- `areastats/webfacts.py`, one step of the enrichment loop (`steps.web`, not in the score). Sources: the Google results stored
  for the project under the name buyers use (one Serper search when there are none); the builder's own site first
  (lodhagroup.com: domain = builder word + company suffix; microsites are not official), then sites naming the project, up to
  4 pages that answer out of 8 tried.
- One model call per page for a fixed list (towers, floors, land, open space, homes, clubhouse, architect, partners), each
  with its sentence. Kept only when the sentence is on the page and holds the value. Published when the builder's site says
  it, or two sites agree (numbers within 5%); text facts only from the builder's site. Disagreements stay owner-only.
  MahaRERA dates, bookings and numbers are never read from the web.
- Stored as `web_facts` on the tower group's primary record. Shown on register pages (`web_facts` in the page payload) and on
  agent-listed pages (`GET /public/register/web-facts/{regno}`), each fact linked to its sources with the read date.
- Agent-listed pages (/projects/<slug>) also got buyer questions (price, each tower's MahaRERA date, registration numbers,
  bookings, size) with FAQ data, and a title aimed at searches: "<name>, <area>: Price <from>, Possession <Mon YYYY>".
- First trial, Lodha Camelot: 10 acres (lodhagroup.com, nobroker.in, magicbricks.com) and 80% open space (lodhagroup.com)
  published; towers held back (nobroker 6, magicbricks 7). 99acres and housing.com refuse the reader.

## Project profile (2026-10-15, LIVE eb551855)

Owner, 2026-10-15: a new enrichment phase: a summary with bullet points, pictures from the builder (or real ones), floor plans;
read again and again, but only for projects whose completion date is still to come; hot projects first.
- `areastats/profile.py`, step `steps.profile` of the enrichment loop (not in the score), after the web facts and from the
  same pages (each page fetched once per round, `webfacts.memo`). Skipped once MahaRERA's filed completion date has passed
  (the page keeps what it had). Every enrichment round reads it again (60 days, hot 14).
- Hot first: a hot project (hot_score >= HOT_MIN) still being built with no `profile` is taken right after urgent requests,
  even when its last enrichment is recent (`enrich.needs_profile`).
- Highlights: one model call per page over a fixed topic list (homes, amenities, clubhouse, open space, towers, design,
  specifications, green, parking, security), each with its sentence. Kept when the sentence is on the page, every number of
  the bullet is in it and it has no sales words. Published from the builder's site, or when two sites state the topic.
  Never prices, possession dates or travel times. The highlights also go to the page-text model, so the summary names them.
- Pictures: only the builder's own site, only its page for this project (the path names the project) plus that page's own
  gallery / plans sub-pages (up to 3). Junk (logos, icons, maps, awards) left out by address; photos >= 800x450 landscape,
  plans >= 500 px; near-duplicates dropped (dHash); up to 8 photos and 8 plans, saved as WebP <= 1600 px under
  uploads/project_media/<regno>/ (the new set replaces the old; a round that finds nothing keeps the last good set). Plan
  captions from the file name ("3 BHK with study floor plan", "master plan").
- Shown on register pages (`profile` in the page payload) and agent-listed pages (`GET /public/register/profile/{regno}`):
  "<name> at a glance" bullets with their sources, a picture grid, floor plans; credit "From the builder's website" with the
  page linked, "renders are artist's impressions; plans indicative, check the sanctioned plans".
- Not taken: portal pictures (watermarked, theirs). Google Places photos need the owner's OK: Google's terms forbid storing
  them, so each page view would call (and bill) Google.
- Trial, Lodha Camelot (lodhagroup.com/.../lodha-camelot-kharadi): 6 photos (gallery renders + banner) and 4 plans (3 BHK,
  3 BHK with study, 4 BHK with study, master plan).

### Hot first, pictures always, plans behind a form (2026-10-22, LIVE)

Owner, 2026-10-22: "first just hot projects, even outside Kharadi, all 4 stages done; if we don't find images add illustrative
ones; floor plans locked, ask for the form; else AI or the best unverified from the web". Before: 76 hot projects still being
built, all with model text, 40 with highlights, 2 with photos, 1 with plans.
- Queue: a hot project comes before every non-hot one in any area (`enrich.priority`, first key). A hot page that is not
  `complete` (all 4 STEPS ok and photos, or read on its group's primary) is retried after RETRY_DAYS (1), not HOT_REFRESH_DAYS.
- Pictures, in order: the builder's site (source "builder") -> other sites' pages whose address names the project (source "web",
  badge "Not checked by us", credit names the sites) -> illustrations drawn once by Cloudflare FLUX-1-schnell from MahaRERA's
  facts (towers, floors, homes or offices; source "ai", badge "AI illustration", heading "What <name> could look like", saved
  under project_media/<regno>-ai). A real picture found later replaces them. Only "builder" pictures go into JSON-LD and og:image.
- Floor plans: always behind `FloorPlansLock` (name, mobile, consent -> a lead "Floor plans of <project>" to the page's agent).
  Our plans show after the form (once per browser); without any, the agent sends them on WhatsApp. Plans are never drawn by AI:
  a made-up layout of a registered project would mislead. The chat bot never describes layouts; it says the agent sends them.
- OTP brochure forms on builder sites: not automated. Checked 2026-10-22: the top hot projects are small builders with no site
  (Maitri Meadows, Prasun Elara), and Ekaanta's forms sit behind reCAPTCHA, which we do not get around.
- Floor plans from agents' brochures (2026-10-22, LIVE): `profile.brochure_pictures` reads the latest brochure kit
  (propertyfacts.brochure) whose MahaRERA number MahaRERA returned ("verified"; an agent's unchecked word never) and is this
  project or one of its group's registrations. Floor and master plans join the plans (first, they are the builder's own),
  renders are pictures after the builder's site and before other sites (badge "Artist's impression"). Pages the agent dropped are
  left out, and brochure pictures are read from the kit every round (never carried over), so a drop leaves the page. An upload,
  a registration answer or a dropped page asks the project for a round at once (`enrich_now`, by "brochure").

### Top Kharadi / Upper Kharadi projects by hand (2026-10-22)

Owner: "Kharadi and Upper Kharadi projects that launched recently or are very hot, top 10, extra care, on priority". Checked by hand:
Lodha Camelot, My Home Upper Kharadi, Venkatesh Vanaya, Ekaanta, Purple Park Eden (MahaRERA "Park Eden Phase I", I Estates Infra
LLP), August Towers Ph 2, Hemant, The Monarch, Prasun Adara, Ganga Avanta A2. Found and fixed:
- Pages from other things with the same name fed three pages: a Chakan hotel (The Monarch: photos + 5 highlights), a Kharadi
  dental clinic (Hemant: photos), a Haridwar retreat (Ekaanta). Now `webfacts.about_project` gates every source; bad pictures,
  highlights and web facts already stored were purged and the pages rewritten.
- Venkatesh Vanaya's page was its shops' wing (commercial). The group primary is now a homes registration.
- Lodha Camelot and Godrej Ivara pages said Wagholi: `locality` now follows the hand-placed list.
- Pictures from other sites: kept only when the picture's own address names the project (`profile.names_project`; squareyards'
  Sai Hemant page carried Godrej Aqua Vista, Raichandani One and Lodha Camelot pictures) and no unrelated project shows the same
  picture (`profile.generic`; magicbricks "created by AI" banners on 25 projects). Squareyards page furniture (map, compare box)
  is junk.
- Text: a section that only says nothing is known is left out; a kept text that misspells the project is dropped for the
  code-written paragraph when the rewrite fails ("Prusin Adara").
- Bramhacorp's site refuses crawlers; we identify ourselves and respect it (August Towers waits for a brochure).
- Register fields set by hand: `builder_pages` (URLs checked to be the builder's page of THIS project, read first, count as
  official) and `marketed_name_override`.

TARGET: the owner's status list shows the profile check but no picture review yet.

## Learning from Housiey (2026-10-20)

Owner, 2026-10-20: "learn from housiey.com". Housiey is a big channel partner (MahaRERA agent A51900001761, builders pay it). Its
project pages show per-unit all-in prices with a minimum down payment, one honest con, a litigation line, documents, builder
stats and related projects; area pages filter by construction stage, hide sold out, litigation-free. Its data is sloppy (Wagholi
landmarks on a Kharadi page, sizes that disagree, test.housiey.com indexed). Shortlist, in order:

1. LIVE once deployed: project page.
   - "Check before you book" (`areastats/cautions.py`, `cautions` in the register page payload): up to 4 weak points worked
     out by code, each a fact plus what to ask: date passed (ask for OC), date moved >= 3 months (net of the 2026 blanket
     extension), completion >= 4 years away (rent + pre-EMI), < 25% booked 2+ years after registration, >= 150 homes per acre
     (land from published web facts) else a 1,500+ home township, towers >= 30 floors, 20+ shops/offices. Never model-written.
   - "Your own cash" (`frontend/lib/site/upfront.ts`): price minus the most a home loan covers (RBI: 90% to a ₹30 L loan, 80%
     to ₹75 L, 75% above) + stamp duty 7% + registration up to ₹30,000. A column in the agent price table, a line in the
     register page's offer box.
   - NOT POSSIBLE: litigation, documents (CC, title report) and inventory. MahaRERA's endpoints for them answer 401 without
     its login and captcha (checked 2026-10-20 on Godrej Ivara, id 61337); we do not get around that. Pages keep linking the record.
2. LIVE once deployed: stage by dates (`pages.stage`: new = registered within 6 months, early < 40% of the time from
   registration to the filed completion date gone, mid < 75%, advanced, passed) and `sold_out` (booked = total), in the page
   payload and the register list. Project page header: "<Stage> (by dates)" chip and "Sold out on MahaRERA". Place pages
   (/projects/area/<place>): "Being built" grouped by stage with jump chips; sold-out projects in a closed section at the end.
   MahaRERA's quarterly progress (getBuildingWingsActivityDetails, getLastQPRFormDetails) answers 401 without its login, so
   the stage is labelled "by dates", never "construction progress".
3. LIVE once deployed: builder pages by brand with a date record.
   - Brands (`areastats/brands.py`): MahaRERA files projects under one company per project or land (Godrej Ivara: Manjari
     Housing Projects LLP), so 29 Pune brands group their companies: a record joins when the company name says the brand, or the
     project name starts with a brand word no other builder uses (and a promoter is on record). Per record: Manjari LLP's
     "Sarita Niketan" stays out. Checked on the register 2026-10-20: 854 of 12,835 records in a brand; Godrej 42 projects over
     15 companies. `pages.builder_key` = brand slug, else the promoter slug; /builders/<company> whose projects all moved to a
     brand answers 301 to the brand page.
   - Record (`pages.delivery`): moved = filed completion date 3+ months later than at registration, net of the 2026 blanket
     extension. COVID extensions are not in these dates (72% of 2,652 projects built through 2020 show no move, no 6/9-month
     spike), so nothing else is netted. Stated only with 5+ projects with both dates. MahaRERA's `projectStatusName` says "New"
     even for finished projects, so no "overdue/completed" figure; handover dates are not published.
   - SEO: brand page title "<Brand> Projects in Pune (N): Possession Dates and Delays", FAQPage (how many projects, on time?,
     which being built, which companies), breadcrumb Home > Builders; /builders index (brands first, then 200 others) linked from
     the header menu and footer, in the sitemap; brand pages at priority 0.8. `seo.gaps` sends brand searches ("godrej projects
     pune", "vj palladio") to the brand page; facet lists and project pages link the brand page.

## Prices from the web (2026-10-20, LIVE)

Owner: "enrichment by our agent/crawler, Upper Kharadi is priority". Reverses the earlier "never prices from the web" rule,
under the same checks as the highlights.
1. LIVE: `areastats/prices.py`, enrichment step 2d, on the same pages as the web facts and profile (each fetched once). Only
   the lines with ₹/lakh/crore go to the model; it says which size and which sentence, code reads every amount from that
   sentence (the model never supplies a number). Per-sq.ft rates, booking amounts, EMIs, offers and rents are refused.
   Published per size when the builder's site states it, or two sites within 15% (the lower). Read for finished projects
   too. Kept 45 days at most, then the price goes.
2. LIVE: project pages show "Prices of <name>" (per size, sources, read date, "ask for the all-in cost"); place pages show
   "from ₹X" per project.
3. LIVE: property sites are named, not linked (web facts, highlights, prices); only the builder's own site and MahaRERA are
   links. We do not send buyers to portals.
4. TARGET: agent price sheets (agentprojects configurations) first on the register page and in "from ₹X" when a project has one.

## Enrichment that improves, fails forward and sells (2026-10-20, LIVE)
Owner, 2026-10-20: enrichment runs again when we improve it, get more info or a better model; a project that fails is noted
and the loop moves on (fixed offline later), with a cut-off; think SEO always; make the paragraph, lines and highlights better.
- **Runs again on improvement.** Each reading step has a version (`enrich.VERSIONS`: web, profile, prices) and the writer has
  `TEXT_VERSION`. Raising a number re-reads every project that step read with an older one: hot projects with the hot ones,
  the rest after all other work. A better model or a new rule = raise the number. Kept per project in `enrichment.versions`.
  Now: profile 2 (builder's site through the brand, on the domain's own name), text 3.
- **Fails forward.** Each reading step stops after `STEP_SECONDS` (240 s), a round after `ROUND_SECONDS` (15 min). A crashed or
  over-long round is noted (`enrich_error`, `enrich_fails`) and the next project goes; a project is never taken again within
  `MIN_GAP` (6 h, urgent requests aside); after `MAX_FAILS` (3) failed rounds in a row it is parked `PARK_DAYS` (14). Studio >
  Newsroom > Project pages has a Parked tab with the reason: that is the offline list. An urgent request is cleared even when
  its round fails, and is taken even outside our areas.
  Found 2026-10-20: Hollyhock City redone every minute all day (hot, no profile because no web results), Gera's Avive request
  never taken (no locality) and keeping the loop at full speed.
- **Builder's site through the brand.** MahaRERA files many projects under a company formed for them (Godrej Ivara: Manjari
  Housing Projects LLP; My Home Upper Kharadi: Godiva Promoters LLP). `webfacts.builder_words` adds the brand's word
  (`brands.py`, new brand Goyal Properties (My Home)); the domain's own name must match, not a sub-domain.
- **Page and search.** Names MahaRERA filed in capitals are shown as buyers write them (`pages.nice_case`; legal name stays an
  alias and on "Filed on MahaRERA as"). The brand is named with the filing company. When we publish asked prices: the title
  leads with "2, 3 BHK from ₹96 L, Possession Apr 2029", the description and the price FAQ use them (the FAQ said "no agent has
  quoted a price" under a price table), the header shows "from". The builder's pictures come right after the header, are the
  page's image in JSON-LD and the shared-link preview. Highlights sit under the text; the writer (v3) no longer repeats them
  and writes no amenities section when there are highlights. Floor plans sit after the prices.
- TARGET: builder sites that load pictures by script (godrejproperties.com gives none): read them in a browser; per-step model
  name on the record.

## Asking without scrolling to the end (2026-10-24)

The enquiry form sat after every section (about 15 on a register page), and phones had no bar, so a buyer who read the
possession date and homes booked had to scroll the whole page to ask. Both kinds of project page now ask where the facts are read:
- `AskPrompt` ("Planning to buy here?", a button to `#enquire`, WhatsApp only when the page has a number) right after "The record"
  on a register page and after the project details on an agent-listed page; on desktop a compact copy tops the register page's
  sticky side column.
- On phones the `StickyJoinBar` ("Ask about this project", plus WhatsApp when there is a number) shows once the header has
  scrolled away and hides while the form is on screen. `MarketingShell stickyBar` lifts the chat bubble above it.
- WhatsApp: the site's public number (`whatsappUrl`, from `NEXT_PUBLIC_CONTACT_WHATSAPP`) on register pages; the main
  agent's number on agent-listed pages, only when direct contact is shown (`NEXT_PUBLIC_SHOW_AGENT_PHONE`).
- MahaRERA tracker (2026-10-24, page review): right under the hero, `ProjectTracker` shows the filed date's path
  (at registration ➔ filed now, split into Order 66/2026's blanket months and the builder's own `completion_moved_months`, or
  "Not moved since registration") and homes booked as a bar (95%+ "nearly sold out: mostly resale", under 30% "most homes not
  yet booked", the guides' bands). "Not moved" is about the completion date only; it says nothing about sales. The side column
  ends with `AgentBridge`, a link to `/trial?src=project-page` for agents who sell the project.
