# Area maps: "Most active projects in <area>" on a street map

Owner, 2026-10-23: on the Upper Kharadi page, show a map of the area with only its most active projects on it.

## What a buyer sees (LIVE: Upper Kharadi; Wagholi and Kharadi as their pins come in)

- On the area's buyer guide (`/localities/<area>`, right after the intro) and on its project list (`/projects/area/<area>`, in place
  of the plain "Most active" list): a street map with up to 10 numbered pins, the picked project's card (photo, price from,
  MahaRERA date, homes booked, "See project", "Directions in Google Maps") and the same projects as a numbered list.
- Pins: the number matches the list; colour is the stage by dates (gold new launch, blue being built, white ring nearly ready);
  a gold ring means a local agent lists it. A name label sits beside a pin only where it fits; in a cluster the list says the name.
- Server-rendered with the first project picked, so it reads in full without JavaScript; picking a pin and lighting a pin from
  its row are extras. The list is the content (links Google and screen readers follow); the picture is `alt=""`.
- Under the map: "Map data © OpenStreetMap contributors", and how many active projects are not on the map yet.

## Rules

- **Only checked positions**, in this order: a pin checked by hand (`areastats/areamap.py`, `MAPS[area].pins`, each with how it
  was checked); a pin the daily round found by the name the project is sold under (`map_pin`, `auto` or `approved`); the
  project's own Google place from enrichment (`geo.located_from == "google"`, places check passed). Never the locality's centre
  (28 of 39 Upper Kharadi records sat on that one point), never a sales gallery or office, never a `doubtful` pin.
- One pin per name sold: phases and towers are one pin with their homes added up (Pristine O2 World Part 1 to 4).
- Ranking is "most active" as on every page (`hubs.active`: doctor's link slots, hot score, Google impressions). Homes only.
- No prices on pins, no area boundary (nobody agrees on one), no embedded Google map (fees per view, slower, every portal's look).

## How it is made

- Street map: `backend/scripts/build_area_map.py <area>` draws the streets, river and parks inside the area's box from
  OpenStreetMap (Overpass) into `frontend/public/maps/<area slug>.svg` (~180 KB, much less gzipped) in the site's colours, with
  the roads buyers know labelled (`LABELS`) and the area's spine drawn wide (`SPINE`). Run once per area; again only if the box
  or the streets change a lot.
- Data: `GET /api/v1/public/register/map?area=` (`areamap.public`), 404 for an area without a drawn map.
- Page: `components/site/AreaMap.tsx` (section) + `AreaMapView.tsx` (pins, card, list; `placeLabels` decides the labels).

## Pins by themselves (LIVE)

`areastats/mappins.py`, once a day inside the enrichment loop (registered through wiring.py: `enrich.add_daily`):
- takes the 25 most active projects of each mapped area that have no checked position, and asks Google Places for the names they
  are sold under (`names_for`: owner's override, group name, search name, marketed name, each also without its "Phase 8" /
  "Tower 5"; a name with nothing distinctive left, like "Kharadi New Project", is never searched); at most 40 searches a day;
- `auto` when Google's place carries every distinctive word of a sold-under name, is inside the map and is not a gallery, office
  or shop; `doubtful` when it shares a distinctive word (not the builder's) but not all; else nothing, tried again in 90 days;
- doubtful pins wait in Studio > Admin > **Map pins to check** with a Google Maps link: Yes puts the pin on the map at once; No
  puts the place on the project's `refused` list and the next round looks for another.

## Areas by place (LIVE)

Decided 2026-10-23 (owner asked "Ekaanta shows on the Kharadi map but is in Viman Nagar"; left the call to us): a project whose
position was checked belongs to the area it is IN, on the maps AND on the area pages, lists and counts. The pincode only decides
for projects without a checked position. Why: 411014 is Kharadi, Viman Nagar and Wadgaon Sheri; 27 of 67 pinned "Kharadi"
projects were elsewhere by Google's own address.

- Boundaries: `app/core/area_bounds.py`, one polygon per area (Kharadi, Upper Kharadi, Wagholi, Lohegaon), drawn over the pinned
  projects coloured by Google's neighbourhood. They overlap on purpose where both names are used (Upper Kharadi with Kharadi's
  east edge and Wagholi's west). Areas without one (Hinjawadi, Wakad, Baner) stay by pincode.
- `areastats/placement.py`, daily: keeps a project's area when its pin is inside that boundary or within 500 m (an edge is not a
  wall); else the boundary that holds it; else out of our areas, its Pune place from Google's address (Viman Nagar ...). Hand
  placements (`pune_places.VERIFIED`) never move. `also_areas`: other boundaries within 500 m, so it shows on those maps too.
- The register sweep keeps a position-placed area (`locality_from: "position"`); a hand placement still wins.
- First run moved 20 projects out of Kharadi (12 Wadgaon Sheri, 6 Viman Nagar, 2 Kalyani Nagar), Ekaanta among them; nothing
  else moved. Kharadi's map was re-centred on its boundary.

## Areas

| Area | Map | Pins |
|---|---|---|
| Upper Kharadi | LIVE | 10 by hand, the rest by the daily round |
| Wagholi | LIVE (drawn 2026-10-23) | daily round + Studio |
| Kharadi | LIVE (drawn 2026-10-23) | daily round + Studio |
| Lohegaon | TARGET: Overpass was at capacity on 2026-10-23; run the script when it answers | |

A map shows on the area's pages once it has 3 pins (`showsMap`); until then the page keeps its plain list.

## Next (TARGET)

- Lodha Kharadi New Project Towers 5/6/9 are named "Lodha Camelot" on their page (search name) though the owner kept them out of
  Camelot (2026-10-13): not pinned until that is settled.
