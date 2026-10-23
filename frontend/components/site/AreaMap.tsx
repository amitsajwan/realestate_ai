import React from 'react'
import Link from 'next/link'
import type { AreaMapData } from '@/lib/site/hubs'
import AreaMapView, { type Shown } from './AreaMapView'

/** "Most active projects in <area>" on the area's street map (backend areastats/areamap.py; docs/plan/area-maps.md). Only projects
 *  whose position was checked are pinned; the rest are counted under the map. An agent-listed project links its shared page
 *  directly (its register page 301s there) and wears a gold ring. The page fetches the map (getAreaMap) and the listed slugs
 *  (getListedSlugs) with its other data; with no map, or fewer than MIN pins (`showsMap`), it shows its plain list instead. */
const MIN = 3

/** Whether an area has a map worth showing (the page then leaves out its plain "Most active" list). */
export function showsMap(data: AreaMapData | null): data is AreaMapData {
  return Boolean(data && data.items.length >= MIN)
}

export default function AreaMap({ data, listed, allHref, className = 'mt-9' }:
  { data: AreaMapData; listed: Map<string, string>; allHref?: string; className?: string }) {
  const items: Shown[] = data.items.map((p) => {
    const own = p.regnos.map((r) => listed.get(r)).find(Boolean)
    return { ...p, href: `/projects/${own ?? p.slug}`, listed: Boolean(own) }
  })
  return (
    <section className={className} aria-labelledby="area-map-title" data-testid="area-map">
      <h2 id="area-map-title" className="text-xl font-semibold text-slate-900">Most active projects in {data.name}</h2>
      <p className="mt-1 max-w-3xl text-sm text-slate-700">
        Ranked by homes booked lately and new launches on MahaRERA. Each pin is the project&apos;s own place on Google Maps, checked
        against the builder&apos;s address. Pick a pin or a project for its possession date, homes booked and price.
      </p>
      <AreaMapView data={data} items={items} />
      {(data.left_out > 0 || allHref) && (
        <p className="mt-3 text-sm text-slate-700">
          {data.left_out > 0 && <>{data.left_out} more active {data.left_out === 1 ? 'project is' : 'projects are'} not on the map yet: we have not checked {data.left_out === 1 ? 'its' : 'their'} location. </>}
          {allHref && <Link href={allHref} className="font-semibold text-[#0f2340] underline underline-offset-2">All projects in {data.name} →</Link>}
        </p>
      )}
    </section>
  )
}
