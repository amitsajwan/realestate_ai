# Area maps: "Most active projects in <area>" on a street map

Owner, 2026-10-23: on the Upper Kharadi page, show a map of the area with only its most active projects on it.

## What a buyer sees (LIVE for Upper Kharadi)

- On the area's buyer guide (`/localities/<area>`, right after the intro) and on its project list (`/projects/area/<area>`, in place
  of the plain "Most active" list): a street map with up to 10 numbered pins, the picked project's card (photo, price from,
  MahaRERA date, homes booked, "See project", "Directions in Google Maps") and the same projects as a numbered list.
- Pins: the number matches the list; colour is the stage by dates (gold new launch, blue being built, white ring nearly ready);
  a gold ring means a local agent lists it. A name label sits beside a pin only where it fits; in a cluster the list says the name.
- Server-rendered with the first project picked, so it reads in full without JavaScript; picking a pin and lighting a pin from
  its row are extras. The list is the content (links Google and screen readers follow); the picture is `alt=""`.
- Under the map: "Map data © OpenStreetMap contributors", and how many active projects are not on the map yet.

## Rules

- **Only checked positions.** A pin is a Google Maps place found for the name the project is sold under and checked by hand
  against the builder's or the listings' address (`areastats/areamap.py`, `MAPS[area].pins`, each with how it was checked), or
  the project's own Google place from enrichment (`geo.located_from == "google"`, places check passed). Never the locality's
  centre (28 of 39 Upper Kharadi records sat on that one point) and never a sales gallery.
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

## Next (TARGET)

- Kharadi, Wagholi, Lohegaon: draw the map, then check pins for their active projects (Google place by marketed name, by hand).
- A pin step in enrichment that searches the marketed name (`marketed_name_override`, group name) instead of MahaRERA's working
  name ("Kharadi Pune Phase I"), so hand checks are only for the doubtful ones.
- Lodha Kharadi New Project Towers 5/6/9 are named "Lodha Camelot" on their page (search name) though the owner kept them out of
  Camelot (2026-10-13): not pinned until that is settled.
