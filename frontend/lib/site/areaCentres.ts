/** Where "<area> from above" (components/site/AreaFromAbove.tsx) centres Google's satellite view, for the area guides that have
 *  no drawn street map yet (backend areastats/areamap.py MAPS has Kharadi, Upper Kharadi and Wagholi; those take the centre of
 *  their map's box instead). docs/plan/area-pictures.md step 2.
 *
 *  Set by hand on 2026-11-17, none guessed. Each centre is either OpenStreetMap's own point for the area (Nominatim search
 *  "<area>, Pune", the result of type place=suburb, then reverse-looked-up to confirm it falls in that area) or, where
 *  OpenStreetMap has no point for the area, the middle of the boundary we drew over the area's projects with checked positions
 *  (backend app/core/area_bounds.py). Zoom 14 shows about 3 km across on a laptop: Nominatim's box for a suburb point is a fixed
 *  default, not the area's extent, so it cannot size the view.
 *
 *  A view at an area's middle is allowed on an area page: satellite-view.md forbids one at an area's centre for a PROJECT page,
 *  where it would show somebody else's land as the project's. An area page claims nothing about a plot. */
export interface AreaCentre { lat: number; lon: number; zoom: number; how: string }

export const AREA_CENTRES: Record<string, AreaCentre> = {
  // OSM has no suburb point for Lohegaon (the search finds the airport and a bus stop); our boundary spans 18.583 to 18.625 N,
  // 73.895 to 73.958 E, and its middle reverse-looks-up to pincode 411047, Lohegaon's
  lohegaon: { lat: 18.604, lon: 73.9265, zoom: 14, how: 'middle of our drawn Lohegaon boundary (area_bounds.py), 2026-11-17' },
  'keshav-nagar': { lat: 18.53227, lon: 73.93838, zoom: 14, how: 'OpenStreetMap place=suburb "Keshav Nagar", Nominatim 2026-11-17' },
  hinjawadi: { lat: 18.59275, lon: 73.73822, zoom: 14, how: 'OpenStreetMap place=suburb "Hinjawadi" (reverse: Hinjawadi Phase 1), Nominatim 2026-11-17' },
  wakad: { lat: 18.60225, lon: 73.76445, zoom: 14, how: 'OpenStreetMap place=suburb "Wakad", Nominatim 2026-11-17' },
  baner: { lat: 18.55899, lon: 73.78452, zoom: 14, how: 'OpenStreetMap place=suburb "Baner" (reverse: Baner Gaon), Nominatim 2026-11-17' },
}
