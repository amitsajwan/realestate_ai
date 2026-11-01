# Location checks: every source we read confirms (or corrects) where a project is

Owner, 2026-11-01, on avasetu.in/projects/96-arrcade-kharadi: "is this kharadi.. i doubt". "We need to confirm location at
various cycles: say you got it from MahaRERA, next you found the project on NoBroker while enriching, and we found a mismatch,
we need to fix it. Enrichment can take time. For now create a plan, and fix the pages."

## What went wrong (96 Arrcade)

- MahaRERA's card says pincode **411014** (Kharadi's). The register set `locality: kharadi, locality_from: pincode` from that alone.
- MahaRERA's own address says "Sr No 96/1B/F/G, Plot 3 & 4, **Chovisawadi**, village Pimpri Chinchawad (M Corp.)". We never read
  it: the general-details API we use has no address, and the address endpoint is not known yet (L1).
- 14 Oct, Google pin search: the best match was at pincode **412105** (Charholi). `propertyfacts.pin.pick` refused it as a
  different pincode and the note was stored ("not found on Google Maps (pincode 412105, MahaRERA says 411014)"). Nothing read
  the note.
- 21 and 26 Oct, web facts, prices and profile: all five sites read were for "Siddhhidata 96 Arrcade, Chovisawadi / Charholi
  Budruk" (their URLs say so). We took their prices, floors and highlights and ignored where they said it is.
- The places step put the project at Kharadi's centre (`geo.located_from: locality`), found it "within 15 km of the pincode",
  passed, and the page said **Position checked** with a map and "World Trade Center 0.9 km". None of it was measured from the
  project.
- `areastats/placement.py` (Areas by place) only moves a project that has a checked position, so it never looked at this one.

Same pattern, found the same day (2026-11-01): 19 pages filed under 411014 that every source puts in Charholi (2), Mundhwa (4) or
Wadgaon Sheri (13), and one Wagholi project sold as Upper Kharadi (343 Crest). A wider sweep flagged 50. Most of the rest were
right, for example Lohegaon projects filed with Google's 411032 (Kalwad / Khese Park, the same Lohegaon) and Kesnand inside
Wagholi. Left for a closer look (L6): Godrej Greens P52100000985 (412207, but every site found is Godrej Greens Undri),
Bramha Skycity Phase 3 (Google 411015, Dhanori), Shubh Nirvana Wing K L M and The Altira (Lohegaon village, sold as Viman Nagar).

## Fixed now (BUILT 2026-11-01)

- `pune_places.VERIFIED` takes a place outside our areas, and `newsroom.register.locality_of` then gives `None`: the project
  leaves the area lists and its page stays under the real place (`pune_place`). The 20 projects above are placed by hand, each
  with its evidence in a comment.
- A page whose place word was wrong gets a new address ("96-arrcade-charholi"). The old one stays in `old_slugs`,
  `pages.project_page` finds it, and the frontend sends it on with a 301.
- Each moved record loses what was built on the wrong place: `geo` and the `places` step (map, "Position checked", the work-hub
  distances), the written summary and sections ("in Kharadi"), the page doctor's description, the gathered `property_facts`
  sheet (nearby list) and the stored Google search. Those still in our areas or on a watch list are written again by the next
  enrichment round. The rest keep the facts that do not depend on the place (MahaRERA, prices, highlights) and the code's own
  paragraph.

## The rule (TARGET)

A project's place is a **claim with readings**, like every other fact (`property_facts`): each source we read gives a reading,
and the place shown is the one the readings agree on.

| Reading | Where it comes from | Weight |
|---|---|---|
| MahaRERA address / village | MahaRERA project view (L1) | official: what the agreement says |
| MahaRERA pincode | register sweep (LIVE) | official but often wrong: builders type the office's or a neighbour's pincode |
| Google pin and its address | `propertyfacts.pin` (LIVE), including a candidate refused only for its pincode (L2) | measured |
| Each listing site's area | the web facts / prices / profile reads (LIVE reads; the area is not kept yet, L3) | one vote per site |
| Builder's own site | the same reads, when `official` | strong |
| Agent's listing | the listing form | strong, the agent's word |
| Owner / Studio | hand placement (`VERIFIED`, later a Studio button, L6) | final |

Decision, run after every step that adds a reading (register sweep, pin search, web read, listing saved), never on a timer:

1. A hand placement wins.
2. MahaRERA's village, when we have it, and it names one of `pune_places` → that place.
3. Else a checked position inside an area boundary → that area (the LIVE "Areas by place" rule).
4. Else the pincode's area, **unless** two or more independent readings (Google's address, separate listing sites, the builder)
   agree on another place and none says the pincode's area: then that place.
5. Readings that disagree with no majority: keep the pincode's place but mark `place_doubt`. The page shows no map, no distances
   and no "checked" tag, and the record goes to the Studio review list.

When the decision changes a record's place, the same clean-up as the fix above runs: new slug + old slug kept, clear `geo` /
`places` / nearby / written text, then enrich again if it is still ours.

## Steps

| Step | What | Where | Status |
|---|---|---|---|
| L0 | Fix the 20 wrong pages (above) | `pune_places.VERIFIED`, `register.locality_of`, `pages.project_page` | BUILT 2026-11-01 |
| L1 | Read MahaRERA's address and village. The view page is a micro-frontend: find the endpoint its project-details screen calls (the general-details answer has none; guessed `getProjectLandAddressDetails` etc. answer 401). Store `address`, `village` on the register record, once per record, with the monthly details read | `agentprojects/maharera.py`, `areastats/refresh.details` | TARGET |
| L2 | Keep Google's best candidate even when refused for its pincode: `{place_id, address, pincode, lat, lon}` as a reading, not as the pin | `propertyfacts/pin.py` | TARGET |
| L3 | Keep each read listing site's own area (URL words, the page's address line), as `place_readings` | `areastats/webfacts`, `prices`, `profile` | TARGET |
| L4 | `place_check(doc)`: the decision above, run at the end of each step that added a reading, with the clean-up when the place moves | `areastats/placement.py` (it already writes `locality`, `pune_place`, `position`) | TARGET |
| L5 | "Position checked" only for a position measured on the project (Google pin, map pin, hand pin). A locality or pincode centre shows the map search with "Position not checked", and no work-hub distances | `enrich.check_places`, `pages.view` (`map`), `RegisterProjectPage` | TARGET (affects every page placed from its area's centre) |
| L6 | Studio: "Place in doubt" list with the readings side by side, and a one-tap "it is in X" that writes the hand placement to the database (not code) | Studio, `areastats` | TARGET |
| L7 | Weekly sweep for old records that never get enriched again: Google's stored refusal notes + stored search results vs the pincode place, the same check as the 2026-11-01 one-off | `areastats/placement.refresh` | TARGET |

Order: L5 first (it stops the false "checked" claim on every page at once), then L2 + L3 (cheap: the reads already happen), L4,
then L1 (needs finding the endpoint), L6, L7.
