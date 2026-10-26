import React from 'react'
import Link from 'next/link'
import { readableName } from '@/lib/site/format'
import type { AreaMapData, ListedProject } from '@/lib/site/hubs'
import AreaMapView, { type Shown } from './AreaMapView'

/** "Most active projects in <area>" on the area's street map (backend areastats/areamap.py; docs/plan/area-maps.md). Only projects
 *  whose position was checked are pinned; the rest are counted under the map. An agent-listed project links its shared page
 *  directly (its register page 301s there) and wears a gold ring. The page fetches the map (getAreaMap) and the listed slugs
 *  (getListed) with its other data; with no map, or fewer than MIN pins (`showsMap`), it shows its plain list instead. */
const MIN = 3

/** Whether an area has a map worth showing (the page then leaves out its plain "Most active" list). */
export function showsMap(data: AreaMapData | null): data is AreaMapData {
  return Boolean(data && data.items.length >= MIN)
}

export default function AreaMap({ data, listed, allHref, className = 'mt-9' }:
  { data: AreaMapData; listed: Map<string, ListedProject>; allHref?: string; className?: string }) {
  const items: Shown[] = data.items.map((raw) => {
    // MahaRERA's names in capitals ("See ZEN ELITE", "RION BUILDTECH PRIVATE LIMITED") read as shouting next to the cards
    const p = { ...raw, name: readableName(raw.name), page_name: raw.page_name && readableName(raw.page_name), builder: raw.builder && readableName(raw.builder) }
    const own = p.regnos.map((r) => listed.get(r)).find(Boolean)
    return own ? { ...p, href: `/projects/${own.slug}`, listed: true, price_from: own.price_min ?? p.price_from }
      : { ...p, href: `/projects/${p.slug}`, listed: false }
  })
  return (
    <section className={className} aria-labelledby="area-map-title" data-testid="area-map">
      {/* not "Top": the area page's Top row ranks by share booked among projects you can still buy, this by recent bookings and
          launches, and two different number ones on one page read as a contradiction (owner review 2026-10-26) */}
      <h2 id="area-map-title" className="text-xl font-semibold text-slate-900">Busy lately in {data.name}, on the map</h2>
      <p className="mt-1 max-w-3xl text-sm text-slate-700">
        Numbered by homes booked lately and new launches on MahaRERA, not by share of homes booked as the Top list is. Each pin is the project&apos;s own place on Google Maps, checked
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
