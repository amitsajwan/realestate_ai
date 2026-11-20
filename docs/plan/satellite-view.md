# The site from above: a satellite view on project pages (2026-11-16; step 2 LIVE 2026-11-19; steps 3-4 BUILT 2026-11-20, by hand, 4 projects)

Owner, 2026-11-16: "can we get live images of project, like satellite images", then "let's add satellite, create a plan and
developers will follow". Nothing here is built yet. Each step is marked code or owner, and steps are in the order to build them.

Background: [seo-system.md](seo-system.md) section 11 (2026-11-16: a median project page's own text is a third of it; two pages
in three have no checked position), [project-pages.md](project-pages.md) (the location section and the street map picture),
[location-checks.md](location-checks.md) (how a position is checked).

## What we can and cannot have

| Source | How old | Detail | Cost | May we keep the picture? | Use |
|---|---|---|---|---|---|
| Google satellite, shown through Maps Embed | 6 months to 3 years | sharp: the plot, roads, neighbours | free with a browser key | no: shown from Google only, never downloaded | step 2 |
| Sentinel-2 (Copernicus, public) | a pass about every 5 days | coarse, 10 m a pixel: a tower is a few pixels | free | yes, with its credit line | step 3, a trial first |
| Planet, Maxar and other paid imagery | days to weeks | sharp | contracts per area | by licence | not doing |

- Nothing sharp is live. For a project being built, Google's picture often shows bare land. The page must say so, with no date
  we cannot prove: Maps Embed gives no capture date.
- What only we can have is **the same site over time** (Sentinel-2): land cleared, a footprint appearing. That is a dated
  reading of our own, the kind section 8b of seo-system.md says a portal cannot copy. Whether 10 m shows anything a buyer
  understands is not known: step 3 starts with five projects and the owner looks at the pictures.
- For Google ranking the gain is indirect: a real view on pages that have no picture, and one more thing on the page that is
  this project's alone. It is not a ranking signal by itself.

## Rules

- **Only at a checked position.** A satellite view is shown only where `pages.own_position` is true (the project's own Google
  pin, passed by the places check), the same rule as the nearby list. An area's or a pincode's centre shows somebody else's
  land: no view. The wrong plot is worse than no picture.
- **Google's imagery is never downloaded, stored, drawn on or used in a reel or post.** Embed only, with Google's own credit
  as it renders. The server's `google_maps_api_key` never reaches the browser: the embed uses its own key (step 2).
- **Sentinel pictures carry their credit** ("Contains modified Copernicus Sentinel data <year>") on the picture and in the
  caption, and their capture date. A cloudy pass is not shown.
- **Never throw a reading away** (seo-system.md section 9): each Sentinel picture kept is appended, dated, beside the earlier ones.
- No sentence about construction progress is written from a picture by a model. A statement such as "building visible since
  <month>" is made only by code from a measured change, and only after step 3's trial shows the measure is right.
- Config comes from the settings objects, the loop step has its own on/off setting, off until its key is set, and a row on
  Admin → Health if it can fail quietly (CLAUDE.md rule 5, seo-upkeep section 3).
- Before a paid or keyed service is switched on, read its price and terms on the provider's own page and write the date read
  into section 8a of seo-system.md. The figures in the table above are from memory, not from such a read.

## The plan, in order

### 1. More pages with a checked position (code, written 2026-11-16, not yet released)

Nothing below works without a pin, and 26 of 40 sampled pages had none. Cause found: `propertyfacts/pin.py` asked Google Maps
for the registered name and refused a place whose name lacked the tower's code ("Kumar Primeview G2" against "Kumar Primeview").

- `pin.sold_as` cuts the tower, wing and phase labels from the end of a registered name; `pin.also_known` adds the names the
  register knows (`mappins.names_for`, passed in through `wiring.py`); `Pins.find` judges the first search's places against all
  of them and asks once more under the first other name. Pincode, distance and "not a shop or office" checks are unchanged.
- A "not found" kept before the change is asked again on the project's next enrichment round, once.
- Cost: at most one more Text Search per project not found, per 30 days.
- Tests: `tests/modules/propertyfacts/test_pin.py`, and one in `tests/modules/areastats/test_enrich.py`.
- After release, count pages with `map` set on Admin → Health (or from the page check) a week later; write the before and
  after into seo-system.md section 11. Target: more than half of the project pages in search.

### 2. "Map / Satellite" on the location section (BUILT 2026-11-16)

Owner's part done 2026-11-16 (key `avasetu-maps-embed`, GitHub variable `NEXT_PUBLIC_MAPS_EMBED_KEY`). The switch still did not
show until 2026-11-19: `frontend/Dockerfile` had no `ARG` for the key, so the build dropped it. Any new `NEXT_PUBLIC_*` setting
needs its `ARG` and `ENV` there as well as in images.yml.

| Part | What | Where |
|---|---|---|
| Owner | In the Google Cloud project the site uses: enable **Maps Embed API**; create a second API key restricted to HTTP referrers `https://avasetu.in/*` and to Maps Embed API only. Add it as `NEXT_PUBLIC_MAPS_EMBED_KEY` with `deploy/gcp/keys.ps1` | Google Cloud console, `deploy/gcp/.env` |
| ~~Code~~ BUILT | In `LocationSection`, when `p.map` is set and the key is present, two buttons above the map: **Map** (today's OpenStreetMap embed, the default) and **Satellite** (`https://www.google.com/maps/embed/v1/view?key=…&center=<lat>,<lon>&zoom=17&maptype=satellite`). The satellite frame is created on the first tap, not before: no request to Google and no cost to page speed for a reader who never asks | `frontend/components/site/LocationMapSwitch.tsx` |
| ~~Code~~ BUILT | Under the satellite frame: "Google's satellite picture of the checked position. It can be months or years old, so a site being built may look emptier than it is today." | same |
| ~~Code~~ BUILT | No key, or no checked position: the section renders exactly as today | same |
| ~~Code~~ BUILT | No frame-source rule exists today (none in `next.config` or `deploy/gcp/`, read 2026-11-16), so nothing to allow. If one is added later it must list `www.google.com` | — |
| ~~Tests~~ BUILT | jest: with a pin and a key the switch is there and the satellite frame is absent until tapped; without a pin or without a key there is no switch; the note is shown with the frame | `frontend/__tests__/site/location-map-switch.test.tsx` |

Not in this step: the satellite picture as the hero image or the social card. Those would need a stored picture, which
Google's terms do not give us.

### 3 and 4, as built (2026-11-20): measured, said in code, on four project pages

Owner, 2026-11-20: "use ai to sharpen the images", "3 projects each for our main areas", "can we write some text ... how
building or construction happened over time", then "lets go for it, the best". Trial on 9 large projects in Kharadi, Upper
Kharadi and Wagholi; owner decided yes.

- **Sharpening is not generative.** A generative upscaler would draw towers that are not there. `areastats.pictures.enhance`:
  one colour stretch over all of a place's pictures (`stretch_for`), slight gamma and colour, optional 2x Lanczos, unsharp
  mask. Used by the area script, the `area_pictures` loop and the project script. The page says "nothing is drawn in".
- **The measure** (`areastats/sitepics.py`): one January to March pass a year since 2021 (same sun angle, least cloud); per
  10 m pixel inside 100 m of the pin, Copernicus classes built / bare / green / other from NDBI, NDVI and visible colour, and
  drops cloud by its scene classification. **Haze**: thin winter smog is not in that classification and reads as concrete
  (2026-01-05: AOT 0.6, every project 20 to 30 points "more built"); of up to 8 cloud-free passes the least hazy is used, none
  over AOT 0.4. Colour alone (no infrared) was tried first and was too noisy to write from.
- **The sentence** (`sitepics.story`): code only. Claims a change of 15 points or more; "began to spread by" only from the
  year the rise holds every later year; says "within 100 m of the map pin" and, under it, that the circle takes in
  neighbouring plots and sees ground cover, not floors. Tests: `tests/modules/areastats/test_sitepics.py`.
- **Files, not a store yet**: `backend/scripts/project_from_above.py <slug> ...` writes `frontend/public/from-above/
  <slug>-<year>.webp` and `<slug>.json`; the page reads them (`lib/site/fromAbove.ts`) and shows "<name> from above, 2021
  to 2026" under the location section with ImageObject data, only while the checked pin is within 50 m of where the
  pictures were taken. jest: `__tests__/site/from-above.test.tsx`.
- **On the site**: Yashwin Enchante (4% to 53%), Kohinoor Riverdale (cleared 2023-24, 0% to 22%), VTP Flamante (cleared
  2023-24, 3% to 19%), The Strand (15% to 41%). **Held back**: Palladio (pin on a junction in built-up streets; the new
  towers are outside the circle), My Home Upper Kharadi and Gera 343 Crest (numbers rise but the pictures do not show it
  plainly), Rohan Abhilasha 4 (its pin is on the finished earlier phases: a wrong pin, and no screen corrects a project pin
  yet; `propertyfacts/pin.py` finds them).
- **Next**: a daily pass (`enrich.add_daily`, step 4 above) only for projects of 300+ homes with a Google pin, after a check
  on 20 more sites including finished ones (they must say nothing). Until then, re-run the script by hand each February.

### Timelapse: month by month (2026-11-20)

Owner, 2026-11-20: "images per quarter would have been good.. and a video, with images changing on right side, showing
landscape changing". Costs nothing: a project's ~45 months are a few hundred small Process API requests, inside the free
Copernicus quota.

- **Months**: one pass a dry month, October to May, since Jan 2021 (`sitepics.dry_months`). June to September is left out:
  under cloud on nearly every pass, and the clear ones are green with rain. Per month, of the 4 least cloudy passes, the
  least hazy whose whole 600 m picture shows no cloud (`sitepics.frame_clear`, `clearest_frame`). About 40 months a project.
- **No numbers on months.** The monthly picture carries its date only; the season changes plant cover month to month. The
  measured shares and the sentence stay with the same-season yearly passes above.
- **Drawn in code** (`calendar/site_timelapse.py`): key frames (one a month, the date and a timeline ticking), short
  cross-fades, then the measured sentence held 3.5 s. Two shapes: a 960x540 silent loop for the page (text left, ground
  right, about 1 MB) and a 1080x1920 reel with the brand music (text above, ground below, under 29 s). Tests:
  `tests/modules/calendar/test_site_timelapse.py`.
- **Made by hand**: `project_from_above.py --timelapse <slug> ... [--reels DIR] [--cache DIR]` writes `<slug>.mp4` and its
  poster `<slug>.webp` beside the yearly pictures and records `"video"` in `<slug>.json`; with `--reels`, the reel and its
  code-written caption. The page plays the loop (muted, looping) only once it is near the screen, with VideoObject data.
- **The credit line** "Contains modified Copernicus Sentinel data <years>" is the Copernicus licence's condition for
  using the pictures; it stays, small, on the page, in the video and in the post.

### The video, second look (2026-11-20)

Owner on the first: "too fast and repetition", "is text readable", "with every image change we need interpretation", "minor
image enhancement". Now: one picture a dry season (Oct-Dec, Jan-Mar, Apr-May; `sitepics.by_season`, a year's measured pass
kept), about 17 since 2021, each held about 1.5 s with a 0.5 s fade; square 720 px for the page with the date (58 px) and a
line (32 px) across the top of the picture, readable on a phone; the words switch halfway through a fade, never overlap.
Each line comes from the yearly measure (`sitepics.captions`: "Measured: 22% roofs and concrete" on a year's own pass,
else "Plants and open ground", "Ground being cleared", "Cleared ground, little built yet", "Roofs and concrete
spreading"), not from a model looking at a 10 m picture, which would guess. `pictures.even_out` moves each picture's
brightness and colour towards the set's average so haze does not flicker; linear per channel, nothing added. On the page
the video plays once, stops on the sentence, and has controls to replay. Videos of the first look are made again
(`fromabove.VIDEO_VERSION`). Sharper pictures would need paid satellites (3 m and finer); Google's sharp view is the
Map/Satellite switch, today's only.

### The look that went live: monthly medians, season lines by Gemini (2026-11-20, LIVE)

Decided with the owner by looking, on 15 sites (sheets in docs/content/from-above/: check-core, check-more-1/2,
enhance-ai-trial, llm-pack-*, gemini-v2-lines, sample-yashwin.mp4):

- **What the satellite can and cannot tell.** All bands for 5 sites, 6 years: plants it tells well (near-infrared); "roofs
  and concrete" it does not: a cleared site's pale dry ground reads as concrete and finished towers read dark (Yashwin
  "75% built" while being built, 53% once finished). No percentage is said anywhere.
- **Pictures: the median of every clear pass**, a request a dry month (`MONTH_EVALSCRIPT`: true colour, infrared, passes
  per pixel). Over 15 sites single passes gave 4 false "plants cleared"; the median none. Seasons and each year's picture
  are medians of the months, made here. About 45 requests a project, then a few a season.
- **Sharper by classic means** (`pictures.classic`: Lanczos, CLAHE, unsharp). Tried and refused: an AI upscaler (EDSR, no
  gain) and Gemini's image model, which drew sheds and blue roofs that are not in the data.
- **The ring is 100 m around the pin**, the ground the words cover.
- **Words: Gemini, given everything** (owner: "send all details we have"): every MahaRERA registration behind the page
  with its dates, homes and buildings, every season's picture and each year's infrared, all in one call
  (`fromabove.describe`, gemini-3.8-flash first). A line a season, a summary, a pin check. Every line goes through
  `checked` (no floors, slabs, progress, rapid, rising, taller, planned...; at most 18 words); a failed line falls back to
  the code's (plants on the ground / being cleared / ground cleared), a failed summary to `sitepics.sentence`. A pin
  Gemini calls doubtful (buildings standing before the first registration: Rohan Abhilasha 4) hides the section. Trial
  v2 on 4 sites matched what we saw; about Rs 2 a project.
- **No Gemini, no publishing.** A busy Gemini (503) is asked again after 90 s; still nothing, the pass stops for the day
  and says so (`MARK.stopped`). Studio > Admin > Health "Site from above" goes red after 2 days and the system watch alerts.
- **Two Copernicus accounts** (owner's choice): `COPERNICUS_CLIENT_ID_2`/`_SECRET_2`; when one refuses for quota the pass
  carries on with the next, and stops only when all are spent. Parallel runs split pages by `in_shard`.
- **Video**: a picture a month dissolving into the next (~0.5 s each), the date and the season's line large over the
  picture, the summary at the end, plays once on the page with controls.
- **On the page**: right after the prices, with a "Watch the site from space" link in the hero; the newest six season lines
  as page text (earlier ones fold away), the yearly row, then today's sharper view through Google's own satellite embed.
- **For search** (the selling point): the season lines are the VideoObject's transcript, /video-sitemap.xml lists every
  video (robots.txt names it), and /projects/from-space lists every project with its timeline (linked from /projects and
  from each section).

### Kept, growing, and new launches (2026-11-20)

Owner: "why we decreased images, more is better??", "for new launches we can have current satellites, and we grow with
project", "we are saving the images?? we can reuse??".

- **Kept**: every pass read (its cloud, haze and circle shares) in `uploads/from_above/<regno>/reads.json` with the last
  day searched, and every month's true-colour picture as fetched in `raw/<day>.png` (about 2 MB a project; 13 GB free on
  2026-11-20). A later look searches only passes after `searched_to`, reads only days not read, fetches only pictures not
  kept (`fromabove.read_new`, `picture`): about 10 requests instead of about 150. A new video style or a slider through
  every month costs nothing. A pin moved over 50 m starts afresh.
- **Growing**: a page with pictures is looked at again every 85 days (`REDO_DAYS`), so each season adds a picture; a page
  with no change every 120 (`REDO_NONE_DAYS`).
- **Why a season per picture in the video**: more pictures in the same length flash by (the first version), and 41 at a
  readable pace would run past a minute; at 10 m consecutive months look alike but for the season's green. Every month is
  kept for a slider a buyer drives (next).
- **New launches** (registered in the last 548 days, `fromabove.new_launch`) show their ground from the first season even
  with no change measured: `sitepics.baseline` says when it registered and that a picture is added each season, no claim
  of building. The captions still come from the measure.

### On every page that qualifies: the daily pass (2026-11-20)

Owner, 2026-11-20: "lets get it for all pages". `areastats/fromabove.py`, a once-a-day pass inside the enrichment loop
(`enrich.add_daily("site from above")`, wired in `wiring.py`, which also passes in the video drawer
`calendar.site_timelapse.page_video`). On by itself wherever the Copernicus keys are set.

- **Which pages**: a checked Google pin of its own (`pages.own_position`), 300+ homes across the project's registrations,
  not finished. 232 on 2026-11-20 (33 in our 8 areas). Our areas first, then by hot score. Redone after 330 days, or at
  once when the pin moves more than 50 m.
- **Cost**: one class map a pass over the whole 600 m square serves both the month's cloud check and the year's measure;
  then the true-colour pictures. About 130 requests a project, about the same when nothing changed (the class maps are
  most of it). No project starts once 2,000 are spent that day (`REQUESTS_PER_DAY`; the free account gives 30,000 requests a month, not 10,000 as first read, owner's dashboard 2026-11-20); a started one may run 200 past it
  (`OVERRUN`) so its requests are not wasted. About two projects a day, about 8,000 of the free 10,000 requests a month:
  the first round of 232 takes about four months. A quota refusal (HTTP 402/403/429) ends the day. First live round
  2026-11-20: 229 due, the first (no change) took 129 requests.
- **Stored** as `from_above` on the register record (`{lat, lon, at, story, where, credit, frames, video}`, or
  `{none: true}` when there is no change of 15 points); files under `uploads/from_above/<regno>/` (`<year>.webp`,
  `months.mp4`, `months.webp`). `areastats/fromabove_view.py` turns it into the page's `from_above` (URLs only, only
  within 50 m of the page's pin); the site reads it with `lib/site/fromAbove.ts fromRecord`. The four hand-made projects'
  files in `public/from-above/` take precedence on their pages.
- **Faster**: Copernicus grants extended quotas on request; the same Sentinel-2 pictures are also on AWS open data with no
  quota (needs an image library on the server).
- Tests: `tests/modules/areastats/test_fromabove.py`, `__tests__/site/from-above.test.tsx`.

### 3. The site over time, from Sentinel-2: a trial on five projects (code, then the owner decides)

1. A script, not a loop: `backend/scripts/sentinel_trial.py --regno <n>`. For the checked pin, a 1 km square, it asks the
   Copernicus Data Space for the least cloudy true-colour picture of each quarter since the project's registration date, and
   writes them side by side as one PNG with dates and the credit line. Stub `httpx` in its test; no network in tests.
2. Run it for five large projects being built in Kharadi, Upper Kharadi and Wagholi whose registration is 2 or more years old
   (enough passes to show change). The owner looks at the five pictures.
3. **Owner decides.** If a buyer can see the site change: step 4. If it is a blur: mark this step DROPPED here with the five
   pictures' date, and stop. Nothing on the site changes in this step.

### 4. If the trial passes: "Seen from space" on the page (code, about three days)

- A daily step inside the enrichment loop (`add-background-loop` skill is not needed: it is a pass added with
  `enrich.add_daily`, like `locmap`), `areastats/sitepics.py`: for up to N projects a day with a checked pin, being built, the
  hottest first, keep one picture a quarter. Stored as an appended list `site_pictures` = [{path, at, cloud, lat, lon}] on the
  register record (areastats owns it); a pin that moves 50 m starts a new series (`pages.MAP_MOVED`).
- The page shows the first and the newest picture side by side with their months ("Jan 2024" / "Oct 2026"), the credit, and a
  line of method. `ImageObject` data with `contentUrl`, `datePublished` and the credit, so image search can read it.
- For a page with no picture of its own, the newest site picture may replace the street map as the hero (it is ours to store).
- Setting `SITE_PICTURES` (off by default), a Health row "site pictures: newest within 120 days", and a line in the operator guide.
- Tests: fixed `NOW`, fakes for the store, a stubbed tile response; a cloudy pass is skipped; a moved pin starts a new series;
  a reading is appended, never replaced.

## What the owner does

1. Step 2: enable Maps Embed API and create the restricted browser key (10 minutes).
2. Step 3: look at five pictures and say yes or no.

## How we judge it (four weeks after step 2 is live)

- Share of project pages in search with a checked position: above a half (step 1).
- Studio → Leads → visits: readers who tap **Satellite**, and enquiries from those visits against the rest (the tap is sent
  as a tracking event, `satellite_open`).
- Search Console: no fall in the pages' Core Web Vitals (the frame loads on tap, so none is expected).

## Not doing

- Downloading or screenshotting Google, Bing or Esri imagery; paid imagery; drone pictures we do not own.
- A satellite view at an area's centre for a page without its own pin.
- Any model-written sentence about what a picture shows.
- **Project boundary overlay.** MahaRERA gives survey numbers and a text description of what lies on each side, not a shape. A boundary drawn in the wrong place on a money-decision page is the kind of checkable error we have been removing; a wrong boundary is worse than none. It also cannot be drawn on Google's free embedded map — it needs a paid map product or a different satellite source with its own terms. A checked pin on the right plot gives most of the value with none of that risk. If a builder's own layout plan is available for a specific project, a boundary for that project could come later.
