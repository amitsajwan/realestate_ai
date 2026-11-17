# Area pages that show the place: landmarks, metro, the view from above, pictures (2026-11-17; steps 1 to 4 BUILT the same day, owner steps open)

Owner, 2026-11-17: "For area pages think creative.. can we add area images. Or major attractions like metro station, places
important ones etc. satellite view etc". Steps 1 to 4 were built on 2026-11-17 (owner: "Everything is live, so you can build"); what each needs from the owner is
under "What the owner does". Each step says what is code and what is the owner's, in the order they were planned.

Background: [area-maps.md](area-maps.md) (the drawn street maps, live for Kharadi, Upper Kharadi, Wagholi),
[satellite-view.md](satellite-view.md) (project pages' Map / Satellite switch, built, waiting for the owner's browser key),
[location-checks.md](location-checks.md) (why a distance from an area's centre once put a wrong fact on a page),
`propertyfacts/surroundings.py` (Google Places and our OpenStreetMap copy, already used for projects' "nearby" lists).

## What an area page has today, and what it lacks

`/localities/<area>` has a written guide (who it suits, getting around, checks), the MahaRERA counts, the area's projects
and, for three areas, a street map with the most active projects. It has **no picture of the place**, **no landmark a buyer
knows** (an IT park, the metro, a hospital, the airport) and **no metro station**, although buyers ask about these first:
"Getting around" is prose and says it does not quote travel times.

## Rules (from what already went wrong)

- **No AI pictures, no copied photos.** Both were removed from every page (seo-system.md, 2026-10-27 and 10-29). A picture
  on an area page is ours, shown from the provider that owns it (Google's embed), or free-licensed with its credit.
- **Every place on the page has a checked position.** A landmark is placed from Google's own place for it or OpenStreetMap,
  checked by hand once, the way the area maps' pins are. A distance never claims more than it is: "about 3 km from the
  middle of Kharadi" names where it is measured from; it is straight-line, rounded, and never a travel time.
- **What is being built says so.** A metro station or road not open yet is shown as planned, with the source and, where we
  track it, the tracker page (`/news/track/pune-metro-line-3` and the others).
- **Google imagery is never downloaded, stored, drawn on or used in a post** (as satellite-view.md). A picture we may keep
  (Sentinel-2, our own photos, licensed ones) carries its credit and date.
- **Fast pages.** Embeds load on tap, not with the page; a kept picture is sized and lazy.

## The plan, in order

### 1. Landmarks and the metro on every area page (BUILT 2026-11-17)

Built: `app/core/pune_metro.py`, 57 stations (Lines 1, 2, 3; 46 running, 11 being built), each with its OpenStreetMap object
(checked on Nominatim 2026-11-17) and source (Maha-Metro's station lists; Line 3 opened 4 Nov 2026 with 17 of 23 stations,
Hindustan Times, The Times of India, International Railway Journal). `areastats/landmarks.py`: 7 to 9 hand-picked places per
area with OSM ids. The middle is the drawn map's centre, else the boundary box's (`area_bounds`), else OSM's point for the
place. `GET /api/v1/public/areas/{slug}/landmarks` gives the nearest 1 or 2 running stations, a nearer being-built one said as
such, and the landmarks with rounded straight-line distances "from the middle of <area>"; the guide shows "Landmarks near
<area>" after Getting around (`AreaLandmarks.tsx`, `ItemList` of `Place`s with geo); the drawn maps draw the ones inside
their frame as square icons named under the map (`AreaMapLandmarks.tsx`, `landmarks` on `/register/map`). Not yet: Line 2A,
2B (Ramwadi to Wagholi, which matters for the east) and 1B stations, no checked positions yet; Phoenix Mall of the
Millennium; the missing street maps (Overpass is not reachable from the build machine: run
`python scripts/build_area_map.py <area>` on the VM for baner, hinjawadi, wakad, lohegaon, keshav-nagar). The Line 3 tracker
was a month behind (said "not open"); its 4 Nov opening was added the same day.


What a buyer sees, after "Getting around":

> **Landmarks near Kharadi**
> Metro: Ramwadi station (Aqua Line, running), about 3 km west of the middle of Kharadi · Line 3 and the rest: see the trackers
> Work: EON IT Park, World Trade Center Pune · Shopping: Phoenix Marketcity · Hospital: Columbia Asia, Manipal ·
> Airport: Pune airport, about 7 km · Railway: Pune Junction, about 11 km

- Each item opens the place on Google Maps (as the project pages' nearby list does). On the areas with a drawn map, the same
  landmarks are drawn on it as small icons (metro, office, hospital, shopping, airport), apart from the numbered project pins.
- Data:
  - **Metro stations**, a hand-checked table in the backend (`app/core/pune_metro.py`: name, line, status `running` /
    `being built`, position, source). About 30 stations on Lines 1 and 2 plus Line 3's. Our OpenStreetMap copy has some of
    them under "railway" with mixed names ("Kalyani Nagar Station", "Civil Court" and "District Court Metro Station" for one
    stop), so it seeds the table and each row is checked against Maha-Metro's list once.
  - **Landmarks per area**, a short hand-picked list (6 to 10) in `areastats/areamap.py`'s neighbour, each with its Google
    place id and how it was checked. Picked from `surroundings.known` (Google's most-reviewed open places) around the area's
    map box, then by hand: a buyer must know the name.
  - The **middle of an area** is the centre of its map box (areas with a drawn map) or of its projects with checked
    positions (5th to 95th percentile, the same way the boxes were made); it is named on the page as "the middle of <area>".
- One endpoint, `GET /api/v1/public/areas/{slug}/landmarks`, owned by `areastats`; the page leaves the section out when it
  answers nothing. JSON-LD: the area's `Place` gets the landmarks as `containsPlace` / nearby `Place`s with positions.
- **Draw the missing maps**: run `scripts/build_area_map.py` for Baner, Hinjawadi, Wakad, Lohegaon and Keshav Nagar so every
  guide has its street map (the script is free: OpenStreetMap). The project pins come in as their positions are checked.
- Tests: the table's stations all have a line, a status and a position inside Pune; a "being built" station is never said
  as running; an area with no landmarks shows no section; distances are rounded and name where they are measured from.

Why first: it answers the questions buyers ask first, needs no key and no owner decision, and it is text and links Google
and AI assistants read ("nearest metro to Kharadi" is a common search).

### 2. The area from above, on tap (BUILT 2026-11-17)

Built: area maps (`/localities/<slug>`, `/projects/area/<slug>`) have Map / Satellite (Google's embed of the map box, zoom
fitted, frame made on the first tap); guides without a drawn map get "<Area> from above" at a hand-set centre
(`frontend/lib/site/areaCentres.ts`, OSM points from Nominatim, Lohegaon from `area_bounds`). Shared embed code:
`frontend/components/site/mapsEmbed.tsx`. Taps are recorded as site events `satellite_open` / `streetview_open` on the visit
(they used to post to `/t/feature`, which never existed, so project pages' taps had never been kept). Invisible until
`NEXT_PUBLIC_MAPS_EMBED_KEY` is in the image build.


- On the area's map: **Map / Satellite**, as on project pages. Satellite is Google's embed of the area's map box
  (`maptype=satellite`, zoom to fit), created on the first tap. Same caption rule: "Google's satellite picture. It can be
  months or years old."
- A view of the whole area is allowed here (satellite-view.md forbids one at an area's centre for a *project* page, where it
  would show somebody else's land as the project's; an area page claims nothing about a plot).
- **Owner**: the `NEXT_PUBLIC_MAPS_EMBED_KEY` from satellite-view.md step 2. Once set, project pages and area pages both get
  the switch.

### 3. "How <area> grew": the same ground in 2017 and today (BUILT 2026-11-17; pictures wait for the owner's run)

Built: area stats carry `registered` (projects registered with MahaRERA per year, empty years 0); the guide shows "How <area>
grew" after the MahaRERA records, a server-rendered bar chart with a hidden table of the same numbers (left out under 3
years). `backend/scripts/area_from_above.py <slug> [--years 2017 2026] [--box s,w,n,e] [--dry-run]` picks the least cloudy
Feb to Apr Sentinel-2 L2A pass per year from the catalogue (tile cloud under 10%), asks the Process API
(`sh.dataspace.copernicus.eu/process/v1`, per its OpenAPI file read 2026-11-17) for that day, refuses a picture that is cloudy or
does not cover the box, and writes `frontend/public/areas/<slug>-<year>.webp` with `<slug>.json`. With two years there, the
guide shows the oldest and newest with month captions, the credit and `ImageObject` data, and uses the newest as its link
preview. No real Copernicus call has been made yet (no credentials on the build machine).


- Sentinel-2 (Copernicus, public, free, ours to keep with its credit) is too coarse for one project (10 m a pixel; that is
  why satellite-view.md step 3 is only a trial), but **an area is 3 to 6 km across**: fields turning into towers over eight
  years show plainly at that scale.
- The page shows two pictures side by side, "Kharadi, March 2017" and "Kharadi, March 2026", the same box, the least cloudy
  dry-season pass of each year, with "Contains modified Copernicus Sentinel data 2017, 2026". Under them, from our own
  register: **projects registered with MahaRERA per year** in the area, a small bar chart (2017 to today), so the picture and
  the count tell the same story. No sentence about the picture is written by a model.
- It is **the area's image** we have been missing: we may keep it, so it can be the area page's social card (link previews)
  and an `ImageObject` in the page's data, which an embed can never be.
- Built as a script first (`backend/scripts/area_from_above.py <area>`) writing `frontend/public/areas/<slug>-<year>.webp`;
  re-run once a year (a loop is not needed).
- **Owner**: create a free Copernicus Data Space account and give the script its client id and secret (`deploy/gcp/keys.ps1`);
  look at the Kharadi and Wagholi pairs and say yes or no before the rest are made. If they are a blur: mark this step
  DROPPED here, nothing on the site changes.

### 4. Photos of the place (BUILT 2026-11-17: own and free-licensed photos through Studio; Street View on tap as a component)

Built: Studio → More → Area photos. Agents and the team upload their own photos, or free-licensed ones entered by hand with
author, CC licence (CC0, CC BY, CC BY-SA, 2.0 to 4.0) and https source link; each needs a caption, date taken and credit.
A photo waits until the owner publishes it; the owner can hide and reorder. Stored upright, EXIF removed (no phone GPS on a
public page), as WebP 1600 and 640 px (`platform.media.keep_photo`); module `areaphotos` owns `area_photos`. The guide shows
up to 8 live photos after the intro, credited, any licence linked, with `ImageObject` data. `StreetViewOnTap.tsx` is ready,
not yet placed on a page.


A real photo of the main road, the metro, the IT park is what buyers expect at the top of the page. Three ways, best first:

| Source | Trust | Cost | Owner's part |
|---|---|---|---|
| **Our own**: the team or local agents shoot 5 to 8 photos per area (main road, metro or bus stop, office park, market, a new tower cluster); uploaded in Studio with who took it and the date | highest: ours, dated, can show what is true today | an afternoon per area | decide who shoots; we add the Studio upload (code, 1 day) |
| **Wikimedia Commons** free-licensed photos (CC BY / CC BY-SA), each with author, licence and link under it | good, if recent; many are old | free | say yes to licensed photos; the 10-29 rule removed *unlicensed* copies |
| **Street View on tap** at 2 or 3 landmark spots, Google's embed (not stored) | good, dated by Google only | free with the step 2 key | nothing beyond step 2 |

Not doing: AI-made "area pictures", stock photos of other cities, photos taken from portals or builders' sites without a
licence.

## What the owner does

1. Nothing for step 1.
2. Step 2: the Maps Embed browser key (already asked for by satellite-view.md).
3. Step 3: a free Copernicus account; then look at two picture pairs and say yes or no.
4. Step 4: choose the photo source (own, Commons, Street View, or a mix).

## How we judge it (four weeks after step 1 is live)

- Search Console: area guides' impressions for searches with "metro", "near", "IT park", "hospital" plus the area's name.
- Studio visits: taps on landmarks and on Satellite; enquiries from area-page visits against before.
- No fall in the pages' Core Web Vitals.

## Not doing

- Travel times ("15 minutes to EON"): the guides say why; road distance may come later from OSRM, said as distance.
- Drawing planned metro or ring-road routes on the map before an official alignment we can cite; the trackers cover them.
- A boundary for an area: nobody agrees on one (area-maps.md).
